# 🚀 Telegram Forward Tag Remover & Code Rebrander Bot

A high-performance Telegram bot built on **aiogram 3.x** and **Google Gemini 2.5 Flash**. Instantly strips forwarded channel headers, analyzes source code to generate structured Telegram channel post captions, and scrubs foreign author credits from code files.

---

## ✨ Features

- **⚡ Zero-Bandwidth Forward Stripper:**
  Uses Telegram's server-side cloning to strip forwarded tags from any media type (videos, documents, audios, photos, voice notes, stickers, GIFs) up to 2GB with zero local bandwidth.

- **🤖 Deep AI Code Analysis (Gemini 2.5 Flash):**
  Reads the actual source code of forwarded scripts to generate a structured, ready-to-post Telegram caption detailing what the code does, libraries used, execution commands, and hashtags.

- **🛡 In-Code Credit Scrubber & Rebrander (< 20MB):**
  Automatically detects code/script files (`.py`, `.js`, `.ts`, `.html`, `.php`, `.sh`, `.cpp`, etc.), scrubs foreign channel links (`t.me/...`) and usernames, and injects your branding:
  - Channel: `t.me/xdro1d`
  - Developer: `@Sudhirxd`

- **🎨 Native Server-Side Styled Buttons:**
  Uses Telegram's native button styles (`success` = green, `danger` = red, `primary` = accent) without button emojis.

- **🔤 Mini Block Small-Caps Typography:**
  All user-facing text, status indicators, and AI caption prose are rendered in clean small-caps typography (`ᴀʙᴄᴅᴇғɢʜɪᴊᴋʟᴍɴᴏᴘǫʀsᴛᴜᴠᴡxʏᴢ`).

- **🔄 Auto-Reconnect Engine:**
  Gracefully catches DNS and network drops on Windows/Linux with automatic reconnection.

---

## 📋 Requirements

- Python 3.10+ (Fully compatible with Python 3.12, 3.13, and 3.14)
- Telegram Bot Token from [@BotFather](https://t.me/BotFather)
- Google Gemini API Key from [Google AI Studio](https://aistudio.google.com/)

---

## 🚀 Installation & Setup

### 1. Clone or Open Workspace
```powershell
cd "tag remover"
```

### 2. Install Dependencies
```powershell
pip install -r requirements.txt
```

### 3. Configure `.env`
Create or edit `.env` in the project root:
```env
# Telegram Bot Token from @BotFather
BOT_TOKEN=your_telegram_bot_token_here

# Google Gemini API Key from Google AI Studio
GEMINI_API_KEY=your_gemini_api_key_here

# Optional: HTTP or SOCKS5 Proxy (leave empty if not needed)
PROXY=
```

---

## ▶️ Running the Bot

```powershell
python main.py
```

---

## 🕹 Usage Workflow

1. Forward any file, video, or script into the bot's private chat.
2. The bot catches the file and presents action buttons:
   - **`[ ᴀɪ ᴄᴀᴘᴛɪᴏɴ ]`** — Reads the code and generates an analytical Telegram post caption.
   - **`[ ᴇᴅɪᴛ ᴄᴀᴘᴛɪᴏɴ ]`** — Enter your own custom caption manually.
   - **`[ ᴇᴅɪᴛ ғɪʟᴇɴᴀᴍᴇ ]`** — Change the document or script filename (< 20MB).
   - **`[ sᴇɴᴅ ]`** — Delivers the cleaned, tag-free media immediately.

---

## 👤 Developer & Channel

- **Channel:** [t.me/xdro1d](https://t.me/xdro1d)
- **Developer:** [@Sudhirxd](https://t.me/Sudhirxd)

