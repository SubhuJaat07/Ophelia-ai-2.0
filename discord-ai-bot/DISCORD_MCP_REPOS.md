# 🤖 Discord MCP Repositories - Complete Guide

## 📋 Top Discord MCP Servers (GitHub)

### 1️⃣ **ExilProductions/discord-mcp** ⭐ RECOMMENDED
**URL:** https://github.com/ExilProductions/discord-mcp

**Features:** Complete API surface for managing Discord via MCP

#### 🛠️ Available Actions/Tools:
| Category | Actions |
|----------|---------|
| **Moderation** | `timeout`, `kick`, `ban`, `enforce_role_policies` |
| **Channels** | `create_channel`, `delete_channel`, `rename_channel`, `move_channel` |
| **Roles** | `create_role`, `delete_role`, `assign_role`, `remove_role` |
| **Messages** | `send_message`, `edit_message`, `delete_message`, `read_messages` |
| **Server** | `get_server_info`, `get_member_list`, `get_bans` |
| **Permissions** | `set_permissions`, `manage_roles` |

---

### 2️⃣ **iprashantraj/mcp-discord-bridge** (44 TOOLS!)
**URL:** https://github.com/iprashantraj/mcp-discord-bridge

**Features:** AI assistant control - 44 tools, no cloning required!

#### 🛠️ All 44 Actions:
```
CHANNELS (8 tools):
├── create_channel
├── delete_channel
├── rename_channel
├── move_channel
├── list_channels
├── get_channel_info
├── create_category
└── set_channel_permissions

MEMBERS (10 tools):
├── kick_member
├── ban_member
├── unban_member
├── timeout_member
├── get_member_info
├── list_members
├── change_nickname
├── add_role_to_member
├── remove_role_from_member
└── get_member_avatar

MESSAGES (12 tools):
├── send_message
├── send_embed
├── edit_message
├── delete_message
├── pin_message
├── unpin_message
├── read_messages
├── search_messages
├── reply_to_message
├── add_reaction
├── remove_reaction
└── get_message_history

ROLES (6 tools):
├── create_role
├── delete_role
├── edit_role
├── list_roles
├── assign_role
└── remove_role

SERVER (5 tools):
├── get_server_info
├── get_server_icon
├── get_server_stats
├── create_webhook
├── manage_webhook

OTHER (3 tools):
├── get_user_info
├── create_invite
└── manage_emoji
```

---

### 3️⃣ **v-3/discordmcp**
**URL:** https://github.com/v-3/discordmcp

**Features:** Claude Integration focused

#### 🛠️ Actions:
- Send/read messages
- Channel management
- Member lookup
- Basic moderation

---

### 4️⃣ **SaseQ/discord-mcp** (Java/JDA)
**URL:** https://github.com/SaseQ/discord-mcp

**Features:** Uses JDA (Java Discord API)

#### 🛠️ Actions:
| Action | Description |
|--------|-------------|
| `kick_member` | Kicks a member from server |
| `ban_member` | Bans a user from server |
| `unban_member` | Removes ban from user |
| `get_bans` | Returns list of banned users |
| `send_message` | Send messages to channels |
| `read_messages` | Read channel history |

---

### 5️⃣ **@pasympa/discord-mcp** (95+ TOOLS!) 🚀
**URL:** https://www.npmjs.com/package/@pasympa/discord-mcp

**Features:** Multi-guild, 95+ tools, lightweight npm package

#### 🛠️ Categories:
- **Members:** kick, ban, unban, timeout, nickname, avatar
- **Channels:** CRUD operations, permissions, categories
- **Messages:** Send, edit, delete, pin, search, react
- **Roles:** Create, delete, modify, assign, remove
- **Server:** Info, stats, invites, emojis, webhooks
- **Threads:** Create, manage, archive
- **Voice:** Manage voice channels

---

## 🎯 Which One Should You Use?

| Repo | Tools Count | Language | Best For |
|------|-------------|----------|----------|
| **ExilProductions/discord-mcp** | ~20 | Python | Production, Complete API |
| **iprashantraj/mcp-discord-bridge** | **44** | Python | Maximum Features |
| **@pasympa/discord-mcp** | **95+** | Node.js | Enterprise, Multi-guild |
| **v-3/discordmcp** | ~10 | Python | Claude Desktop |
| **SaseQ/discord-mcp** | ~6 | Java | Java Ecosystem |

---

## 🔧 Recommended Setup for Ophelia Bot:

Based on your current setup, I recommend using **iprashantraj/mcp-discord-bridge** approach because:

1. ✅ **Python-based** (matches your discord.py bot)
2. ✅ **44 tools** - maximum functionality
3. ✅ **No cloning required** - easy integration
4. ✅ **Complete moderation** - kick/ban/timeout/all actions

### Next Steps:
1. Clone the repo you like best
2. Copy tool definitions to your `src/tools/`
3. Update `tool_executor.py` to register new tools
4. Test each action on Railway deployment

---

## 📊 Action Categories Summary:

```
MODERATION (Critical)
├── kick_user/member
├── ban_user/member  
├── unban_user/member
├── timeout_user/member
└── mute_user/member

CHANNEL MANAGEMENT
├── create_text_channel
├── create_voice_channel
├── delete_channel
├── rename_channel
├── move_channel
└── set_channel_permissions

ROLE MANAGEMENT
├── create_role
├── delete_role
├── assign_role
├── remove_role
└── modify_role

MESSAGE OPERATIONS
├── send_message
├── send_embed
├── edit_message
├── delete_message
├── search_messages
├── add_reaction
└── pin_message

SERVER INFO
├── get_server_info
├── list_channels
├── list_members
├── get_member_info
└── get_banned_users
```

---
*Generated: 2026-08-06*
*For Ophelia AI 3.1 Bot*
