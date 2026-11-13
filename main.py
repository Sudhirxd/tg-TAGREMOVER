
import os
import re
import sys
import html
import asyncio
import logging
import tempfile
import pathlib
from typing import Dict, Any, Optional

import aiohttp
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, F
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import Command, CommandStart
from aiogram.types import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery,
    FSInputFile,
)
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.exceptions import TelegramRetryAfter, TelegramBadRequest, TelegramNetworkError

# --- Environment & Configuration ---
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
PROXY = os.getenv("PROXY", "").strip() or None

# --- Rebranding Constants ---
TARGET_CHANNEL_LINK = "t.me/xdro1d"
TARGET_USERNAME = "@Sudhirxd"
TARGET_USER_LINK = "t.me/Sudhirxd"

# --- Logging Setup ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(levelname)s] - %(name)s - %(message)s",
)
logger = logging.getLogger("TagRemoverBot")

# --- Small Caps Font Transformer ---
SMALL_CAPS_MAP = str.maketrans(
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ",
    "ᴀʙᴄᴅᴇғɢʜɪᴊᴋʟᴍɴᴏᴘǫʀsᴛᴜᴠᴡxʏᴢᴀʙᴄᴅᴇғɢʜɪᴊᴋʟᴍɴᴏᴘǫʀsᴛᴜᴠᴡxʏᴢ",
)


def sc(text: str) -> str:
    return text.translate(SMALL_CAPS_MAP)


def sc_html(text: str) -> str:
    """Transform text into small-caps mini block font while preserving HTML tags."""
    parts = re.split(r"(<[^>]+>)", text)
    return "".join(
        p if p.startswith("<") and p.endswith(">") else p.translate(SMALL_CAPS_MAP)
        for p in parts
    )


# Common small-caps status tags
TXT_PROGRESS = sc("progress")
TXT_SUCCESS = sc("success")
TXT_ERROR = sc("error")

# --- Premium Emoji Definitions (from Catalog) ---
EMOJI_FIRE = "5424972470023104089"      # 🔥
EMOJI_STAR = "5372849966689566579"      # ⭐
EMOJI_ROCKET = "5359664288241829619"    # 🚀
EMOJI_CROWN = "6237927637906364256"     # 👑
EMOJI_SHIELD = "6235476345451716705"    # 🛡
EMOJI_CHECK = "5206607081334906820"     # ✅
EMOJI_CROSS = "5210952531676504517"     # ❌
EMOJI_WARNING = "5447644880824181073"   # ⚠️
EMOJI_LOCK = "4956719506027185156"      # 🔒
EMOJI_GEAR = "5116414868357907335"      # ⚙️
EMOJI_ZAP = "5224607267797606837"       # ⚡
EMOJI_DIAMOND = "5427009714745517609"   # 💎
EMOJI_PIN = "5397782960512444700"       # 📌
EMOJI_TERMINAL = "5424972470023104089"  # 💻
EMOJI_TAG = "5271604874419647061"       # 🏷
EMOJI_BELL = "5458603043203327669"      # 🔔
EMOJI_ANNOUNCE = "5424818078833715060"  # 📢

# User Curated Pack
EMOJI_AUDIO = "5388632425314140043"     # 🔈
EMOJI_TV = "5355012477883004708"        # 📺
EMOJI_MOBILE = "5231302331538104275"    # 📱
EMOJI_DEV = "6195190028956602330"       # 👨‍💻
EMOJI_PHONE = "5850292279503228917"     # 📱
EMOJI_NETFLIX = "5332726004253212527"   # 🎬
EMOJI_TICK = "5206607081334906820"      # ✔️
EMOJI_SCREEN = "4985813751929242386"    # 📺
EMOJI_PRIME = "5327807841497537073"     # 🆕


def pe(emoji_id: str, fallback: str) -> str:
    """Format Telegram Custom/Premium Emoji tag for Telegram client animated rendering."""
    if emoji_id:
        return f'<tg-emoji emoji-id="{emoji_id}">{fallback}</tg-emoji>'
    return fallback


def strip_tg_emoji(text: str) -> str:
    """Strip <tg-emoji> tags to raw fallback emoji while preserving <b>, <code>, etc."""
    return re.sub(r"<tg-emoji[^>]*>(.*?)</tg-emoji>", r"\1", text)


E_FIRE = pe(EMOJI_FIRE, "🔥")
E_STAR = pe(EMOJI_STAR, "⭐")
E_ROCKET = pe(EMOJI_ROCKET, "🚀")
E_CROWN = pe(EMOJI_CROWN, "👑")
E_SHIELD = pe(EMOJI_SHIELD, "🛡")
E_CHECK = pe(EMOJI_CHECK, "✅")
E_CROSS = pe(EMOJI_CROSS, "❌")
E_WARNING = pe(EMOJI_WARNING, "⚠️")
E_LOCK = pe(EMOJI_LOCK, "🔒")
E_GEAR = pe(EMOJI_GEAR, "⚙️")
E_ZAP = pe(EMOJI_ZAP, "⚡")
E_DIAMOND = pe(EMOJI_DIAMOND, "💎")
E_PIN = pe(EMOJI_PIN, "📌")
E_TERMINAL = pe(EMOJI_TERMINAL, "💻")
E_TAG = pe(EMOJI_TAG, "🏷")
E_BELL = pe(EMOJI_BELL, "🔔")
E_AUDIO = pe(EMOJI_AUDIO, "🔈")
E_TV = pe(EMOJI_TV, "📺")
E_MOBILE = pe(EMOJI_MOBILE, "📱")
E_DEV = pe(EMOJI_DEV, "👨‍💻")
E_NETFLIX = pe(EMOJI_NETFLIX, "🎬")
E_TICK = pe(EMOJI_TICK, "✔️")
E_PRIME = pe(EMOJI_PRIME, "🆕")

EMOJI_UPGRADE_MAP = {
    "🚀": E_ROCKET,
    "⚡": E_ZAP,
    "⚡️": E_ZAP,
    "👨‍💻": E_DEV,
    "💻": E_DEV,
    "🛡": E_SHIELD,
    "🛡️": E_SHIELD,
    "⚙️": E_GEAR,
    "⚙": E_GEAR,
    "🏷": E_TAG,
    "🏷️": E_TAG,
    "🎬": E_NETFLIX,
    "📺": E_TV,
    "🔈": E_AUDIO,
    "📱": E_MOBILE,
    "✔️": E_TICK,
    "✅": E_TICK,
    "🆕": E_PRIME,
    "💎": E_DIAMOND,
    "👑": E_CROWN,
    "🔥": E_FIRE,
    "📌": E_PIN,
}


def upgrade_emojis_to_premium(text: str) -> str:
    """Upgrade raw unicode emojis into <tg-emoji> tags for Telegram Premium rendering."""
    for raw_symbol, tag in EMOJI_UPGRADE_MAP.items():
        if tag != raw_symbol and raw_symbol in text:
            pattern = re.compile(rf"(?<!>){re.escape(raw_symbol)}(?!</tg-emoji>)")
            text = pattern.sub(tag, text)
    return text

# --- In-Memory State Stores ---
user_pending: Dict[int, Dict[str, Any]] = {}
user_waiting_caption: Dict[int, bool] = {}
user_waiting_filename: Dict[int, bool] = {}


# --- Gemini API Engine ---
async def call_gemini(prompt: str) -> Optional[str]:
    """Call Google Gemini 1.5 Flash via REST endpoint."""
    if not GEMINI_API_KEY:
        logger.warning("GEMINI_API_KEY is not set.")
        return None

    endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.4,
            "maxOutputTokens": 2000,
            "thinkingConfig": {"thinkingBudget": 0},
        },
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                endpoint, json=payload, timeout=aiohttp.ClientTimeout(total=20)
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    candidates = data.get("candidates", [])
                    if candidates:
                        return candidates[0]["content"]["parts"][0]["text"].strip()
                else:
                    err = await resp.text()
                    logger.error(f"Gemini API error ({resp.status}): {err}")
    except Exception as exc:
        logger.error(f"Gemini call failed: {exc}")
    return None


def ensure_caption_limit(caption: str, max_limit: int = 1000) -> str:
    """Ensure media caption never exceeds Telegram's strict 1024-character ceiling."""
    if not caption or len(caption) <= max_limit:
        return caption
    return caption[:max_limit].rsplit("\n", 1)[0]


async def generate_telegram_caption(
    file_name: str, raw_caption: str, code_content: Optional[str] = None
) -> str:
    """Prompt Gemini to read the full code and construct a compact Telegram caption styled with premium emojis."""
    if code_content:
        prompt = (
            f"You are a professional software engineer and top Telegram channel curator.\n"
            f"Analyze this source code and write a COMPACT, HIGH-ENGAGEMENT Telegram post caption styled with PREMIUM EMOJIS.\n\n"
            f"Filename: {file_name}\n"
            f"--- SOURCE CODE CONTENT ---\n"
            f"{code_content[:20000]}\n"
            f"--- END SOURCE CODE ---\n\n"
            f"STRICT FORMATTING REQUIREMENTS:\n"
            f"1. LENGTH: Very concise and punchy (under 350 characters total).\n"
            f"2. Headline: Bold title with a premium emoji (e.g. ⚡ <b>Tool Name</b>, 🚀 <b>Script Name</b>, or 💎 <b>Project</b>).\n"
            f"3. Exactly 2-3 short bullet points explaining key features/what it does, each starting with a premium emoji (e.g. ⚡, 🛡️, ⚙️, 📌, 🔹). Do NOT use <ul>, <ol>, or <li> tags.\n"
            f"4. Run command: 💻 <code>python {file_name}</code> (or appropriate execution command).\n"
            f"5. 2-3 hashtags prefixed with 🏷️ or 🎯 (e.g. #Python #Dev #Tool).\n"
            f"6. Do NOT add channel or developer credit footers in the caption.\n"
            f"7. Use ONLY valid HTML tags: <b>, <i>, <code>. No markdown backticks or quotes."
        )
    else:
        prompt = (
            f"You are a top Telegram channel curator. Write a SHORT, punchy Telegram post caption styled with PREMIUM EMOJIS.\n"
            f"Filename: {file_name}\n"
            f"Existing description: {raw_caption}\n\n"
            f"STRICT FORMATTING REQUIREMENTS:\n"
            f"1. Under 300 characters total.\n"
            f"2. Bold title with a premium emoji (e.g. 🚀 <b>Title</b> or 💎 <b>Title</b>).\n"
            f"3. Exactly 2 short bullet points with premium emojis (e.g. ⚡, 📌, 🛡️).\n"
            f"4. 2-3 relevant hashtags prefixed with 🏷️.\n"
            f"5. Do NOT add channel or developer credit footers in the caption.\n"
            f"6. Use ONLY <b>, <i>, <code> tags."
        )

    res = await call_gemini(prompt)
    if res:
        res = re.sub(r"^```html\s*|^```\s*|```$", "", res, flags=re.MULTILINE).strip()
        res = re.sub(r"<\/?(?:ul|ol|p)>", "", res)
        res = re.sub(r"<li>\s*", "⚡ ", res)
        res = re.sub(r"<\/li>", "", res)
        res = re.sub(r"`([^`]+)`", r"<code>\1</code>", res)
        res = re.sub(r"^([•\-*])\s*", "⚡ ", res, flags=re.MULTILINE)
        res = upgrade_emojis_to_premium(res)
        formatted = sc_html(res.strip())
        return ensure_caption_limit(formatted)

    base = raw_caption or file_name
    return ensure_caption_limit(
        sc_html(f"{E_ROCKET} <b>{base}</b>\n\n{E_ZAP} {sc('clean unbranded media')}\n{E_SHIELD} {sc('verified')}")
    )


# --- Code & Text Credit Scrubber ---
CODE_EXTENSIONS = {
    ".py", ".js", ".ts", ".html", ".css", ".php", ".sh", ".bash",
    ".json", ".txt", ".md", ".cpp", ".c", ".h", ".cs", ".java",
    ".lua", ".go", ".rs", ".rb", ".xml", ".yaml", ".yml",
}


def sanitize_code_credits(content: str) -> str:
    """Strip external Telegram channels and author credits, inject target credits."""
    # 1. Replace all external t.me and telegram.me links
    content = re.sub(
        r"https?://(?:t\.me|telegram\.me)/(?!xdro1d\b|Sudhirxd\b)[a-zA-Z0-9_]+",
        f"https://{TARGET_CHANNEL_LINK}",
        content,
    )
    content = re.sub(
        r"(?:t\.me|telegram\.me)/(?!xdro1d\b|Sudhirxd\b)[a-zA-Z0-9_]+",
        TARGET_CHANNEL_LINK,
        content,
    )

    # 2. Replace other author @handles in comments or credits
    content = re.sub(
        r"@(?!Sudhirxd\b|xdro1d\b)[a-zA-Z0-9_]{4,}",
        TARGET_USERNAME,
        content,
    )

    # 3. Replace common credit lines
    content = re.sub(
        r"(?i)(credit[s]?\s*[:=]\s*)(?!.*Sudhirxd).*$",
        rf"\1{TARGET_USERNAME} ({TARGET_CHANNEL_LINK})",
        content,
        flags=re.MULTILINE,
    )
    return content


def sanitize_filename(name: str) -> str:
    """Remove foreign channel watermarks from filenames."""
    # Remove [@channel] or [channel_name]
    name = re.sub(r"\[.*?\]", "", name)
    # Remove @usernames
    name = re.sub(r"@[a-zA-Z0-9_]+", "", name)
    # Clean leading/trailing symbols
    name = re.sub(r"^[-_.\s]+|[-_.\s]+$", "", name)
    return name.strip() or "file"


# --- Keyboards with Native Server Styles (No Button Emojis) ---
def build_file_action_keyboard(has_gemini: bool) -> InlineKeyboardMarkup:
    """Produces [ ᴀɪ ᴄᴀᴘᴛɪᴏɴ ] [ ᴇᴅɪᴛ ᴄᴀᴘᴛɪᴏɴ ] [ ᴇᴅɪᴛ ғɪʟᴇɴᴀᴍᴇ ] [ sᴇɴᴅ ] buttons."""
    buttons = []
    first_row = []

    if has_gemini:
        first_row.append(
            InlineKeyboardButton(
                text=sc("ai caption"),
                callback_data="btn_ai_caption",
                style="primary",
            )
        )

    first_row.append(
        InlineKeyboardButton(
            text=sc("edit caption"),
            callback_data="btn_edit_caption",
            style="primary",
        )
    )
    buttons.append(first_row)

    buttons.append(
        [
            InlineKeyboardButton(
                text=sc("edit filename"),
                callback_data="btn_edit_filename",
                style="primary",
            )
        ]
    )

    buttons.append(
        [
            InlineKeyboardButton(
                text=sc("send"),
                callback_data="btn_send",
                style="success",
            )
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def build_cancel_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=sc("cancel"),
                    callback_data="btn_cancel_caption",
                    style="danger",
                )
            ]
        ]
    )


# --- Dispatcher Setup ---
dp = Dispatcher()


# --- Handlers: Commands ---
@dp.message(CommandStart())
async def cmd_start(msg: Message):
    text = (
        f"{E_CROWN} <b>tag remover and rebrander</b> {E_FIRE}\n\n"
        f"<b>{TXT_PROGRESS}</b>: forward any file to begin\n\n"
        f"• {E_STAR} <b>ai caption:</b> generates ready-to-post channel captions.\n"
        f"• {E_ROCKET} <b>instant clone:</b> zero tag, zero latency."
    )
    formatted = sc_html(text)
    try:
        await msg.answer(text=formatted)
    except TelegramBadRequest as ex:
        if "custom_emoji" in str(ex).lower() or "can't parse entities" in str(ex).lower():
            clean = strip_tg_emoji(formatted)
            await msg.answer(text=clean)
        else:
            raise


@dp.message(Command("help"))
async def cmd_help(msg: Message):
    text = (
        f"{E_SHIELD} <b>usage guide</b>\n\n"
        f"1. forward any file or code document.\n"
        f"2. click <b>ai caption</b> to let gemini craft the post.\n"
        f"3. click <b>send</b> to output clean media with your branding."
    )
    formatted = sc_html(text)
    try:
        await msg.answer(text=formatted)
    except TelegramBadRequest as ex:
        if "custom_emoji" in str(ex).lower() or "can't parse entities" in str(ex).lower():
            clean = strip_tg_emoji(formatted)
            await msg.answer(text=clean)
        else:
            raise


# --- Handlers: Callbacks ---
@dp.callback_query(F.data == "btn_ai_caption")
async def on_ai_caption(query: CallbackQuery, bot: Bot):
    user_id = query.from_user.id
    data = user_pending.get(user_id)
    if not data:
        await query.answer(sc("no file found"), show_alert=True)
        return

    await query.answer(sc("analyzing code..."))
    status_msg = await query.message.edit_text(
        f"<b>{TXT_PROGRESS}</b>: {sc('reading code and generating caption')}..."
    )

    file_name = data.get("file_name", "media")
    raw_caption = data.get("caption", "")
    file_id = data.get("file_id")
    file_size = data.get("file_size", 0)
    ext = pathlib.Path(file_name).suffix.lower()

    code_content = None
    # If code/text document under 20MB: download and read actual code
    if file_id and (ext in CODE_EXTENSIONS or file_size <= 2 * 1024 * 1024):
        try:
            file_info = await bot.get_file(file_id)
            temp_dir = tempfile.gettempdir()
            dest_path = os.path.join(temp_dir, f"analyze_{data['message_id']}_{file_name}")
            await bot.download_file(file_info.file_path, dest_path)
            try:
                with open(dest_path, "r", encoding="utf-8", errors="ignore") as f:
                    code_content = f.read(50000)
            finally:
                if os.path.exists(dest_path):
                    os.remove(dest_path)
        except Exception as read_err:
            logger.warning(f"Could not read code content: {read_err}")

    new_caption = await generate_telegram_caption(file_name, raw_caption, code_content=code_content)
    data["caption"] = new_caption

    try:
        await status_msg.edit_text(
            f"<b>{TXT_SUCCESS}</b>: {sc('ai caption ready')}\n\n{new_caption}",
            reply_markup=build_file_action_keyboard(has_gemini=bool(GEMINI_API_KEY)),
        )
    except TelegramBadRequest as ex:
        err = str(ex).lower()
        if "custom_emoji" in err or "can't parse entities" in err:
            clean_cap = strip_tg_emoji(new_caption)
            await status_msg.edit_text(
                f"<b>{TXT_SUCCESS}</b>: {sc('ai caption ready')}\n\n{clean_cap}",
                reply_markup=build_file_action_keyboard(has_gemini=bool(GEMINI_API_KEY)),
            )
        else:
            raise


@dp.callback_query(F.data == "btn_send")
async def on_send_click(query: CallbackQuery, bot: Bot):
    user_id = query.from_user.id
    data = user_pending.get(user_id)

    if not data:
        await query.answer(sc("no file found"), show_alert=True)
        return

    msg_id = data.get("message_id")
    target_caption = data.get("caption")
    file_id = data.get("file_id")
    file_name = data.get("file_name", "")
    file_size = data.get("file_size", 0)
    custom_filename = data.get("custom_filename")
    ext = pathlib.Path(file_name).suffix.lower()

    # If code/text file under 20MB or explicit rename requested
    is_code_file = ext in CODE_EXTENSIONS and file_size <= 20 * 1024 * 1024
    needs_download = bool(custom_filename or is_code_file)

    try:
        if needs_download and file_id:
            if file_size > 20 * 1024 * 1024:
                await query.message.edit_text(
                    f"{E_WARNING} <b>{TXT_ERROR}</b>: {sc('files over 20mb cannot be renamed directly. sending via server clone')}..."
                )
                safe_caption = ensure_caption_limit(target_caption) if target_caption else None
                if safe_caption is not None:
                    await bot.copy_message(
                        chat_id=user_id,
                        from_chat_id=user_id,
                        message_id=msg_id,
                        caption=safe_caption,
                        parse_mode=ParseMode.HTML,
                    )
                else:
                    await bot.copy_message(
                        chat_id=user_id,
                        from_chat_id=user_id,
                        message_id=msg_id,
                    )
            else:
                final_name = custom_filename or sanitize_filename(file_name)
                await query.message.edit_text(
                    f"<b>{TXT_PROGRESS}</b>: {sc('downloading and processing rename')}..."
                )

                file_info = await bot.get_file(file_id)
                temp_dir = tempfile.gettempdir()
                dest_path = os.path.join(temp_dir, final_name)

                await bot.download_file(file_info.file_path, dest_path)

                try:
                    if is_code_file:
                        try:
                            with open(dest_path, "r", encoding="utf-8", errors="ignore") as f:
                                content = f.read()
                            cleaned_content = sanitize_code_credits(content)
                            with open(dest_path, "w", encoding="utf-8") as f:
                                f.write(cleaned_content)
                        except Exception as scrub_err:
                            logger.warning(f"Scrub error: {scrub_err}")

                    safe_caption = ensure_caption_limit(target_caption) if target_caption else None
                    try:
                        await bot.send_document(
                            chat_id=user_id,
                            document=FSInputFile(dest_path, filename=final_name),
                            caption=safe_caption,
                            parse_mode=ParseMode.HTML,
                        )
                    except TelegramBadRequest as ex:
                        err = str(ex).lower()
                        if "custom_emoji" in err or "can't parse entities" in err:
                            clean_cap = strip_tg_emoji(safe_caption) if safe_caption else None
                            try:
                                await bot.send_document(
                                    chat_id=user_id,
                                    document=FSInputFile(dest_path, filename=final_name),
                                    caption=clean_cap,
                                    parse_mode=ParseMode.HTML,
                                )
                            except TelegramBadRequest:
                                plain_cap = re.sub(r"<[^>]+>", "", clean_cap) if clean_cap else None
                                await bot.send_document(
                                    chat_id=user_id,
                                    document=FSInputFile(dest_path, filename=final_name),
                                    caption=plain_cap,
                                    parse_mode=None,
                                )
                        else:
                            raise
                finally:
                    if os.path.exists(dest_path):
                        os.remove(dest_path)

        else:
            # Server-side clone (zero-bandwidth, strips forward header)
            safe_caption = ensure_caption_limit(target_caption) if target_caption else None
            if safe_caption is not None:
                try:
                    await bot.copy_message(
                        chat_id=user_id,
                        from_chat_id=user_id,
                        message_id=msg_id,
                        caption=safe_caption,
                        parse_mode=ParseMode.HTML,
                    )
                except TelegramBadRequest as ex:
                    err = str(ex).lower()
                    if "custom_emoji" in err or "can't parse entities" in err:
                        clean_cap = strip_tg_emoji(safe_caption)
                        try:
                            await bot.copy_message(
                                chat_id=user_id,
                                from_chat_id=user_id,
                                message_id=msg_id,
                                caption=clean_cap,
                                parse_mode=ParseMode.HTML,
                            )
                        except TelegramBadRequest:
                            plain_cap = re.sub(r"<[^>]+>", "", clean_cap)
                            await bot.copy_message(
                                chat_id=user_id,
                                from_chat_id=user_id,
                                message_id=msg_id,
                                caption=plain_cap,
                                parse_mode=None,
                            )
                    else:
                        raise
            else:
                await bot.copy_message(
                    chat_id=user_id,
                    from_chat_id=user_id,
                    message_id=msg_id,
                )

        await query.message.delete()
        await query.answer(sc("delivered"))

    except TelegramRetryAfter as tra:
        logger.warning(f"Rate limited: retry after {tra.retry_after}s")
        await asyncio.sleep(tra.retry_after)
        await bot.copy_message(chat_id=user_id, from_chat_id=user_id, message_id=msg_id)
        await query.message.delete()

    except TelegramBadRequest as tbr:
        err_msg = str(tbr).lower()
        logger.error(f"TelegramBadRequest: {tbr}")
        if "chat_forwards_restricted" in err_msg or "protected" in err_msg:
            await query.message.edit_text(
                f"{E_LOCK} <b>{TXT_ERROR}</b>: {sc('content is copy-protected by source channel')}",
            )
        else:
            await query.message.edit_text(
                f"{E_CROSS} <b>{TXT_ERROR}</b>: <code>{html.escape(str(tbr))}</code>",
            )

    except Exception as exc:
        logger.error(f"Delivery failed: {exc}")
        await query.message.edit_text(
            f"{E_CROSS} <b>{TXT_ERROR}</b>: <code>{html.escape(str(exc))}</code>",
        )


@dp.callback_query(F.data == "btn_edit_caption")
async def on_edit_caption_click(query: CallbackQuery):
    user_id = query.from_user.id
    if user_id not in user_pending:
        await query.answer(sc("no file found"), show_alert=True)
        return

    user_waiting_caption[user_id] = True
    user_waiting_filename[user_id] = False
    await query.message.edit_text(
        f"<b>{TXT_PROGRESS}</b>: {sc('send the new caption in chat below')}",
        reply_markup=build_cancel_keyboard(),
    )
    await query.answer()


@dp.callback_query(F.data == "btn_edit_filename")
async def on_edit_filename_click(query: CallbackQuery):
    user_id = query.from_user.id
    if user_id not in user_pending:
        await query.answer(sc("no file found"), show_alert=True)
        return

    user_waiting_filename[user_id] = True
    user_waiting_caption[user_id] = False
    await query.message.edit_text(
        f"<b>{TXT_PROGRESS}</b>: {sc('send the new filename with extension below (e.g. script.py)')}",
        reply_markup=build_cancel_keyboard(),
    )
    await query.answer()


@dp.callback_query(F.data == "btn_cancel_caption")
async def on_cancel_caption_click(query: CallbackQuery):
    user_id = query.from_user.id
    user_waiting_caption[user_id] = False
    user_waiting_filename[user_id] = False
    data = user_pending.get(user_id, {})
    file_name = data.get("file_name", "media")
    caption = data.get("caption", "")
    caption_preview = f"\n\n<b>{sc('caption')}</b>: <code>{html.escape(caption)}</code>" if caption else ""
    name_preview = f"\n<b>{sc('file')}</b>: <code>{html.escape(file_name)}</code>" if file_name != "media" else ""

    await query.message.edit_text(
        f"<b>{TXT_PROGRESS}</b>: {sc('file ready')}{name_preview}{caption_preview}",
        reply_markup=build_file_action_keyboard(has_gemini=bool(GEMINI_API_KEY)),
    )
    await query.answer()


# --- Handlers: Message & Media Intake ---
@dp.message(F.chat.type == "private")
async def handle_incoming(msg: Message):
    user_id = msg.from_user.id

    # Handle manual caption input
    if user_waiting_caption.get(user_id):
        if msg.text and not msg.text.startswith("/"):
            user_waiting_caption[user_id] = False
            if user_id in user_pending:
                user_pending[user_id]["caption"] = msg.text
                await msg.reply(
                    f"<b>{TXT_SUCCESS}</b>: {sc('caption updated')}\n\n"
                    f"<code>{html.escape(msg.text)}</code>",
                    reply_markup=build_file_action_keyboard(has_gemini=bool(GEMINI_API_KEY)),
                )
                return

    # Handle manual filename input
    if user_waiting_filename.get(user_id):
        if msg.text and not msg.text.startswith("/"):
            user_waiting_filename[user_id] = False
            clean_input = re.sub(r'[\\/*?:"<>|]', "", msg.text).strip()
            if user_id in user_pending and clean_input:
                user_pending[user_id]["custom_filename"] = clean_input
                user_pending[user_id]["file_name"] = clean_input
                caption = user_pending[user_id].get("caption", "")
                caption_prev = f"\n\n<b>{sc('caption')}</b>: <code>{html.escape(caption)}</code>" if caption else ""
                await msg.reply(
                    f"<b>{TXT_SUCCESS}</b>: {sc('filename updated')}\n\n"
                    f"<b>{sc('file')}</b>: <code>{html.escape(clean_input)}</code>{caption_prev}",
                    reply_markup=build_file_action_keyboard(has_gemini=bool(GEMINI_API_KEY)),
                )
                return

    # Skip commands
    if msg.text and msg.text.startswith("/"):
        return

    # Extract media metadata
    file_id = None
    file_name = "media"
    file_size = 0

    if msg.document:
        file_id = msg.document.file_id
        file_name = msg.document.file_name or "document"
        file_size = msg.document.file_size or 0
    elif msg.video:
        file_id = msg.video.file_id
        file_name = msg.video.file_name or "video.mp4"
        file_size = msg.video.file_size or 0
    elif msg.audio:
        file_id = msg.audio.file_id
        file_name = msg.audio.file_name or "audio.mp3"
        file_size = msg.audio.file_size or 0
    elif msg.photo:
        file_id = msg.photo[-1].file_id
        file_name = "photo.jpg"
        file_size = msg.photo[-1].file_size or 0

    has_payload = bool(
        file_id
        or msg.voice
        or msg.video_note
        or msg.animation
        or msg.forward_origin
        or msg.forward_date
        or msg.text
    )

    if not has_payload:
        return

    # Save pending payload
    user_pending[user_id] = {
        "message_id": msg.message_id,
        "caption": msg.caption,
        "file_id": file_id,
        "file_name": file_name,
        "file_size": file_size,
    }
    user_waiting_caption[user_id] = False

    caption_preview = f"\n\n<b>{sc('caption')}</b>: <code>{html.escape(msg.caption)}</code>" if msg.caption else ""
    name_preview = f"\n<b>{sc('file')}</b>: <code>{html.escape(file_name)}</code>" if file_name != "media" else ""

    # Choose icon based on file type
    ext = pathlib.Path(file_name).suffix.lower()
    if msg.video or ext in {".mp4", ".mkv", ".avi", ".mov", ".webm"}:
        type_icon = E_NETFLIX
    elif msg.audio or msg.voice or ext in {".mp3", ".wav", ".flac", ".aac", ".ogg", ".m4a"}:
        type_icon = E_AUDIO
    elif ext in {".apk", ".xapk", ".ipa"}:
        type_icon = E_MOBILE
    elif ext in CODE_EXTENSIONS:
        type_icon = E_DEV
    else:
        type_icon = E_ROCKET

    text = f"{type_icon} <b>{TXT_PROGRESS}</b>: {sc('file received')}{name_preview}{caption_preview}"
    reply_markup = build_file_action_keyboard(has_gemini=bool(GEMINI_API_KEY))

    try:
        await msg.reply(text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
    except TelegramBadRequest as ex:
        if "can't parse entities" in str(ex).lower():
            clean_text = re.sub(r"<[^>]+>", "", text)
            await msg.reply(clean_text, reply_markup=reply_markup, parse_mode=None)
        else:
            raise


# --- Application Runner ---
async def main():
    if not BOT_TOKEN:
        logger.critical("BOT_TOKEN is not set in .env! Exiting.")
        sys.exit(1)

    if not GEMINI_API_KEY:
        logger.warning("GEMINI_API_KEY is not set in .env. AI caption button disabled.")

    session = AiohttpSession(proxy=PROXY) if PROXY else None

    bot = Bot(
        token=BOT_TOKEN,
        session=session,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    logger.info("Starting Telegram Tag Remover Bot (Auto-Reconnect Enabled)...")

    while True:
        try:
            await dp.start_polling(bot)
            break
        except TelegramNetworkError as net_err:
            logger.warning(f"DNS / Network drop: {net_err}. Reconnecting in 4 seconds...")
            await asyncio.sleep(4)
        except Exception as exc:
            logger.error(f"Unexpected connection drop: {exc}. Retrying in 5 seconds...")
            await asyncio.sleep(5)


if __name__ == "__main__":
    asyncio.run(main())
