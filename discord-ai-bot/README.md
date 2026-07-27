# 🤖✨ Ophelia AI 2.0 - Advanced Discord Bot

**Sabse OP Discord AI Bot with Natural Language Commands! Direct bolo, samajh jaati hoon!**

![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python)
![Discord](https://img.shields.io/badge/Discord.py-2.4+-purple?logo=discord)
![Groq](https://img.shields.io/badge/Groq-API-orange)
![Natural Language](https://img.shields.io/badge/Natural_Language-🧠-green)

## ✨ NEW in 2.0 - Natural Language Commands!

**No more `/cmd` syntax! Just TALK to the bot naturally! 🗣️**

| You Say | Bot Does |
|---------|----------|
| `"iska avatar dikhao"` | Shows user's profile picture |
| `"isko timeout do 10 min"` | Times out the user |
| `"server info dikhao"` | Displays server statistics |
| `"status set karo playing Minecraft"` | Changes bot status |
| `"channel banao memes"` | Creates new channel |
| `"kick karo isko"` | Kicks user from server |
| `"roles dikhao"` | Shows user's roles |
| `"join date kab hai?"` | Shows when user joined |

---

## 👑 OWNER SYSTEM

**3 Owners with FULL CONTROL:**
- **User ID:** `1169492860278669312` (You) 👑
- **GF ID 1:** `1463113729959919801` 💕
- **GF ID 2:** `1443836576802013316` 💕

Owners can:
- ✅ Use ALL commands without restrictions
- ✅ Kick/Ban/Timeout/Mute anyone
- ✅ Create channels & roles
- ✅ Change bot status, nickname
- ✅ Full Discord API access!
- ✅ No need for @mention in servers

---

## 🔥 Features Overview

### 🤖 Smart AI Chat
- **Llama 3.3 70B** via Groq API (Fast & Free!)
- Multi-key fallback support
- Long-term memory system
- Custom personalities (Fun/Professional/Casual)

### 🗣️ Natural Language Commands
- **NO SYNTAX REQUIRED** - Just talk normally!
- Understands Hindi + English + Hinglish
- Context-aware responses
- Auto-detects commands from chat

### ⚙️ Server Settings (`/ai setting`)
- Interactive dropdown menus (Mods/Owners only)
- Temperature control
- Custom instructions
- AI channels (auto-reply without ping)
- Personality selection
- Memory toggle
- And much more!

### 🎯 Discord API Power
- **Avatar Display** - Show any user's profile pic
- **User Info** - Detailed user profiles
- **Server Stats** - Member count, channels, roles
- **Timeout/Kick/Ban** - Full moderation
- **Channel/Role Creation** - Manage server
- **Status Control** - Playing/Listening/Watching
- **Reactions** - Add emojis to messages

### 💾 Persistent Storage
- **Supabase Database** - Settings, memories, conversations
- **In-Memory Cache** - Fast access with auto-sync
- **Auto Warm-up** - Loads data on bot restart

---

## 🚀 Quick Setup

### 1. Prerequisites
- Python 3.10+
- Discord Bot Token ([Discord Developer Portal](https://discord.com/developers/applications))
- Groq API Key ([console.groq.com](https://console.groq.com))
- Supabase Project ([supabase.com](https://supabase.com))

### 2. Install & Configure
```bash
# Clone or download
cd Ophelia-AI-2.0

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt

# Setup environment
cp .env.example .env
# Edit .env with your credentials
```

### 3. Environment Variables (.env)
```env
DISCORD_TOKEN=your_discord_bot_token_here

# Multiple API keys supported (comma-separated)!
GROQ_API_KEYS=gsk_key1,gsk_key2,gsk_key3

SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_service_role_key_here

# Owners are automatically set, but you can customize:
OWNER_IDS=1169492860278669312,1463113729959919801,1443836576802013316
```

### 4. Database Setup
1. Go to [Supabase Dashboard](https://supabase.com) → SQL Editor
2. Run contents of `data/schema.sql`
3. Creates: guild_settings, conversations, memories, command_log tables

### 5. Discord Bot Configuration
1. [Discord Developer Portal](https://discord.com/developers/applications)
2. **Bot Tab:**
   - ✅ Message Content Intent
   - ✅ Server Members Intent
   - ✅ Presence Intent
   - ✅ Moderation Intent (for timeout/kick/ban)
3. **OAuth2 → URL Generator:**
   - Scopes: `bot`, `applications.commands`
   - Permissions: Administrator (recommended)

### 6. RUN!
```bash
python bot.py
```

---

## 📖 Usage Guide

### Basic Chatting (Everyone)
Just **@mention** the bot OR talk directly if you're an owner:

```
@Ophelia Hi bhai! Kya haal hai?
@Ophelia Make me a joke 😂
@Ophelia Code ek simple calculator bana do
```

### Natural Language Commands (The MAGIC!)

#### Info Commands (Anyone can use):
```
@Ophelia avatar dikhao @user          # Show avatar
@Ophelia iske baare me batao           # User info  
@Ophelia server info dikhao            # Server stats
@Ophelia meri info                     # Your own info
@Ophelia roles dikhao                  # User's roles
@Ophelia join date kab hai?            # When they joined
```

#### Moderation Commands (Mods/Owners):
```
@Ophelia isko timeout do 10 min        # Timeout user
@Ophelia kick karo isko                # Kick user
@Ophelia ban kar do                   # Ban user
@Ophelia mute karo                    # Mute user
@Ophelia 50 messages delete karo      # Clear chat
```

#### Bot Control (Owners Only):
```
@Ophelia status set karo playing Minecraft    # Change status
@Ophelia nickname change karo CoolBot         # Rename bot
@Ophelia channel banao memes                 # New channel
@Ophelia role banao VIP gold                 # New role
@Ophelia #general me bhejo "Hello everyone"  # Send message
@Ophelia embed banao "Title" "Description"   # Rich embed
```

### Settings Command (Mods/Owners)
Type `/ai setting` to open interactive settings panel:

![Settings Panel](https://via.placeholder.com/400x200?text=Interactive+Settings+with+Dropdowns)

**Available Settings:**
- 🤖 AI Toggle (On/Off)
- 🌡️ Temperature (0.0 = serious, 2.0 = crazy)
- 📝 Custom Instructions
- 🔔 Ping Reply (@mention response)
- 📢 Everyone Ping Response
- 💬 AI Channels (auto-reply without mention)
- 😄 Personality (Fun/Professional/Casual)
- 🧠 Memory System
- ⚡ Natural Language Commands
- 🔒 Mention Requirement

### Other Useful Commands
- `/ai help` - Show all commands
- `/ai status` - Check bot status
- `/ai ping` - Test latency
- `/ai owners` - Show who owns this bot
- `/ai clear_memory` - Clear conversation history (Mods)
- `/ai personalities` - View personality options

---

## 🧠 How Memory Works

Bot automatically remembers:
1. **User Preferences** - "Mujhe pasand hai..." type messages
2. **Personal Info** - Names, birthdays, locations
3. **Conversation Summaries** - Important discussions
4. **Server Facts** - Server-specific information

**Memory Flow:**
```
User Message → AI Response → Extract Info → Save to Supabase → Cache for Speed
     ↓                                                              ↓
   Next Chat ← Load Memories ← Check Cache ← Bot Restart/Cache Miss
```

**Memories persist FOREVER** (or until you clear them)! Even after months, bot will remember users! 🧠✨

---

## 🔑 Multi-Key API System

Multiple Groq API keys with automatic fallback:

```env
# Single key
GROQ_API_KEYS=gsk_abc123...

# Multiple keys (auto-rotate on failure!)
GROQ_API_KEYS=gsk_key1,gsk_key2,gsk_key3,gsk_key4
```

**How it works:**
1. Tries Key 1 first
2. If fails (rate limit, error), rotates to Key 2
3. Continues until success or all keys exhausted
4. Auto-recovers from temporary issues!

---

## 📁 Project Structure

```
Ophelia-AI-2.0/
├── bot.py                      # Main entry point
├── .env.example                # Config template
├── requirements.txt            # Dependencies
├── start.sh                    # Startup script
├── README.md                   # This file!
│
├── config/
│   └── settings.py             # Configuration & owner IDs
│
├── src/
│   ├── commands/
│   │   ├── settings.py         # /ai setting command
│   │   └── utility.py          # /ai help, info, ping etc.
│   │
│   ├── handlers/
│   │   ├── ai_handler.py       # AI response + memory
│   │   └── message_handler.py  # Message processing
│   │
│   └── utils/
│       ├── database.py         # Supabase operations
│       ├── cache.py            # In-memory cache
│       ├── groq_client.py      # Multi-key API client
│       ├── natural_commands.py # 🗣️ NATURAL LANGUAGE PARSER!
│       └── meta_commands.py    # Legacy /cmd support
│
└── data/
    └── schema.sql              # Database schema
```

---

## 🎨 Personality Modes

### 😄 Fun Mode (Default)
Hasi-mazaak, roasting, Hinglish mix, emojis - perfect for friend groups!

> **User:** Bhai suno  
> **Ophelia:** Sun rahi hoon bolo kya hua? 😏 Tumse koi baat nahi sunni bas mazaaak karna hai na? 💀

### 💼 Professional Mode
Helpful, formal, proper formatting - for work servers!

> **User:** Can you explain how this works?  
> **Ophelia:** Certainly! Here's a detailed explanation of the functionality...

### 🙂 Casual Mode
Relaxed friendly vibes - balanced approach!

> **User:** Kya haal hai?  
> **Ophelia:** Sab badhiya bhai! Aap sunao, kuch kaam tha kya? 🙂

---

## ❓ Troubleshooting

### Bot not responding?
1. Check `/ai status` - Is AI enabled?
2. Are you @mentioning correctly?
3. Look at console logs for errors
4. Verify owners have full access

### API errors?
1. Check Groq API keys are valid
2. Try multiple keys for fallback
3. Verify quota remaining at console.groq.com

### Database issues?
1. Ensure you ran `schema.sql` in Supabase
2. Check SUPABASE_URL and SUPABASE_KEY
3. Use SERVICE ROLE key (not anon key!)

### Natural commands not working?
1. Check if enabled in `/ai setting`
2. Make sure you're using correct phrases
3. Owners don't need @mention!

---

## 🤝 Contributing

Issues and PRs welcome! Main areas:
- More natural language patterns
- Additional Discord API integrations
- Voice channel support
- Image generation integration

---

## 📜 License

MIT License - Use freely, give credits! 😊

---

## 🌟 Star History

If this bot helped your server, give it a star! ⭐

---

**Made with ❤️ by an AI enthusiast**  
**For my GFs and all Discord communities!** 💕

*Remember: Is bot ka main target insaanon ke saath mazaaak karna hai! Entertainment first!* 😂🔥💀

---

## 🆘 Need Help?

- Check `/ai help` in Discord
- Read this README thoroughly
- Open an issue on GitHub
- DM the owners!

**Happy Chatting with Ophelia AI 2.0!** 🚀✨
