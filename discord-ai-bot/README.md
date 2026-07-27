# 🤖 Discord AI Bot - OP Bot with Groq API

**Ek OP Discord bot jo mazaaake ke saath baat karega, yaad rakhega, aur server manage karega!**

![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python)
![Discord](https://img.shields.io/badge/Discord.py-2.4+-purple?logo=discord)
![Groq](https://img.shields.io/badge/Groq-API-orange)

## ✨ Features

| Feature | Description |
|---------|-------------|
| **🤖 Smart AI Chat** | Llama 3.3 70B via Groq API - fast & free! |
| **🔑 Multi-Key Fallback** | Comma-separated API keys - auto-rotate on failure |
| **⚙️ Server Settings** | `/ai setting` command (Mods only) with dropdowns |
| **🧠 Long-Term Memory** | Yaad rakhega users ko - even after months! |
| **💬 Reply Mode** | Reply to specific user using Discord's reply feature |
| **😄 Fun Personality** | Hasi-mazaak, roasting, memes - full entertainment! |
| **📢 Custom Channels** | Set channels where AI replies without @mention |
| **⚡ Meta Commands** | AI can execute commands like kick, ban, embeds! |
| **💾 Supabase + Cache** | Fast cache + persistent database storage |
| **🎛️ Full Control** | Temperature, personality, ping settings - sab customizable! |

## 🚀 Quick Setup

### 1. Prerequisites

- Python 3.10+
- Discord Bot Token ([Discord Developer Portal](https://discord.com/developers/applications))
- Groq API Key ([console.groq.com](https://console.groq.com))
- Supabase Project ([supabase.com](https://supabase.com))

### 2. Clone & Install

```bash
# Navigate to project
cd discord-ai-bot

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure Environment

```bash
# Copy example env file
cp .env.example .env

# Edit .env file with your credentials
```

**`.env` Configuration:**
```env
DISCORD_TOKEN=your_discord_bot_token_here
GROQ_API_KEYS=gsk_key1,gsk_key2,gsk_key3  # Multiple keys supported!
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_service_role_key_here
```

### 4. Setup Database

1. Go to your Supabase dashboard → SQL Editor
2. Run the contents of `data/schema.sql`
3. This creates all required tables (guild_settings, conversations, memories, etc.)

### 5. Configure Discord Bot

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Select your bot → **Bot** tab:
   - Enable "Message Content Intent"
   - Enable "Server Members Intent" 
   - Enable "Presence Intent"
3. Go to **OAuth2 → URL Generator**:
   - Scopes: `bot`, `applications.commands`
   - Permissions: Administrator (or customize as needed)
4. Invite bot to your server

### 6. Run the Bot!

```bash
python bot.py
```

## 📖 Usage Guide

### Basic Chatting

Just **@mention** the bot and start chatting!

```
@BotName Hi bhai! Kya haal hai?
@BotName Make me a joke 😂
@BotName Code ek simple calculator bana do
```

### Settings Command (Mods Only!)

Type `/ai setting` to open the interactive settings panel:

![Settings Dropdown](https://via.placeholder.com/400x200?text=Interactive+Settings+Panel+with+Dropdowns)

**Available Settings:**
- 🤖 **AI Toggle** - On/Off karo
- 🌡️ **Temperature** - Response creativity (0.0 = serious, 2.0 = crazy)
- 📝 **Custom Instructions** - Apna system prompt add karo
- 🔔 **Ping Reply** - @mention pe reply on/off
- 📢 **Everyone Ping** - @everyone/@here pe reply on/off
- 💬 **AI Channel** - Bina ping ke auto-reply channel set karo
- 😄 **Personality** - Fun/Professional/Casual mode
- 🧠 **Memory** - Long-term memory on/off
- ⚡ **Meta Commands** - AI ko commands use karne do

### Setting Up AI Channel

1. `/ai setting` karo
2. **"💬 AI Channel"** select karo
3. Channel IDs daalo (comma-separated)
4. Ab us channel me bina mention ke bhi bot reply dega!

**Channel ID kaise nikale?**
- Discord me **Developer Mode** on karo (Settings → Advanced)
- Channel pe right click → **Copy Channel ID**

### Meta Commands (AI Power!)

AI ko commands execute karwa sakte ho:

```
@BotName /cmd say 123456789 "Hello everyone!"
@BotName /cmd embed "Announcement" "Server update!" blue
@BotName /cmd clear 50
@BotName /cmd create_channel "memes"
```

**Available Commands:**
| Command | Description | Mod Only |
|---------|-------------|----------|
| `say` | Message bhejo kisi channel me | No |
| `embed` | Embed message bhejo | No |
| `react` | Reaction add karo | No |
| `status` | Bot status change karo | No |
| `clear` | Messages delete karo | No |
| `kick` | User kick karo | ✅ |
| `ban` | User ban karo | ✅ |
| `create_channel` | Naya channel banao | No |
| `create_role` | Naya role banao | No |
| `nickname` | Bot nickname change karo | No |

## 🧠 How Memory Works

Bot automatically remembers:

1. **User Preferences** - "Mujhe pasand hai..." type messages
2. **Personal Info** - Names, birthdays, locations
3. **Conversation Summaries** - Important discussions summarized
4. **Server Facts** - Server-specific information

**Memory Flow:**
```
User Message → AI Response → Extract Info → Save to Supabase → Cache for Speed
     ↓                                                              ↓
   Next Chat ← Load Memories ← Check Cache ← Bot Restart/Cache Miss
```

## 🔑 Multi-Key System

Multiple API keys support automatic fallback:

```env
# Single key (simple)
GROQ_API_KEYS=gsk_abc123...

# Multiple keys (fallback enabled)
GROQ_API_KEYS=gsk_key1,gsk_key2,gsk_key3
```

**How it works:**
1. Tries Key 1 first
2. If fails (rate limit, error), rotates to Key 2
3. Continues until success or all keys exhausted
4. Auto-recovers from temporary issues!

## 📁 Project Structure

```
discord-ai-bot/
├── bot.py                 # Main bot entry point
├── .env.example           # Environment template
├── requirements.txt       # Dependencies
├── config/
│   └── settings.py        # Configuration & defaults
├── src/
│   ├── commands/
│   │   └── settings.py    # /ai setting command
│   ├── handlers/
│   │   ├── ai_handler.py  # AI response generation
│   │   └── message_handler.py  # Message processing
│   └── utils/
│       ├── database.py    # Supabase operations
│       ├── cache.py       # In-memory caching
│       ├── groq_client.py # Groq API client
│       └── meta_commands.py  # Meta-command system
└── data/
    └── schema.sql         # Database schema
```

## 🎨 Personality Modes

### 😄 Fun Mode (Default)
- Hasi-mazaak, light roasting
- Hinglish mix
- Emojis, memes vibes
- Perfect for friend groups!

### 💼 Professional Mode
- Helpful & concise responses
- Proper formatting
- Good for work servers

### 🙂 Casual Mode
- Relaxed friendly vibe
- Easy-going conversations
- Balanced approach

## ❓ Troubleshooting

### Bot not responding?
1. Check if bot is online (`/ai status`)
2. Verify AI is enabled in settings
3. Check if you're @mentioning correctly
4. Look at console logs for errors

### API errors?
1. Verify Groq API key is valid
2. Check if you have remaining quota
3. Try multiple keys for fallback

### Database issues?
1. Ensure you ran `schema.sql` in Supabase
2. Check SUPABASE_URL and SUPABASE_KEY
3. Verify service role key (not anon key)

## 🤝 Contributing

Issues and PRs welcome! Main areas for improvement:
- More personality modes
- Additional meta-commands
- Voice chat integration
- Image generation support

## 📜 License

MIT License - Use freely, just give credits! 😊

---

**Made with ❤️ and lots of ☕ by an AI enthusiast**

*Remember: Is bot ka main target insaanon ke saath mazaaak karna hai! Entertainment first!* 😂🔥
