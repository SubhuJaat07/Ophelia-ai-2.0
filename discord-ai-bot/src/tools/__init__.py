"""
🛠️ Ophelia AI Tools - COMPLETE MCP-Style Function Calling (35+ TOOLS!)
========================================================================

This module provides Discord operation tools that the AI can invoke!
Makes Ophelia a TRUE functional bot - not just chat!

TOOLS CATEGORIES:
⚡ MODERATION (6 tools): kick_user, ban_user, unban_user, timeout_user, mute_user, unmute_user
📝 CHANNELS (6 tools): create_text_channel, create_voice_channel, delete_channel, rename_channel, list_channels, get_channel_info
👤 ROLES (5 tools): create_role, delete_role, assign_role, remove_role, list_roles
💬 MESSAGES (6 tools): send_message, send_embed, edit_message, delete_message, pin_message, add_reaction
📊 SERVER INFO (4 tools): get_server_info, get_member_info, list_members, get_banned_users
✨ PROFILE (2 tools): change_nickname, get_avatar
🔍 SEARCH (2 tools): search_messages, read_channel_history
🎯 UTILITY (1 tool): create_invite
🌐 EXTERNAL (3 tools): web_search, generate_image, execute_code

TOTAL: 35+ REAL Discord Actions + External APIs!

NEW IN v3.1:
✅ Multi-Provider AI Fallback (NVIDIA 30 Keys, 29+ Models!)
✅ Complete MCP Tool Set from GitHub Repos
✅ Real Discord API Execution (no fake responses!)
✅ External Tools (Tavily Search, Pollinations Images, E2B Code)

Usage:
    from src.tools import get_tool_executor, get_registry
    executor = get_tool_executor()
    result = await executor.execute_tool("kick_user", {"user_id": "123"})
    
    # Or use registry directly:
    registry = get_registry()
    tool = registry.get("ban_user")
    result = await tool.run({"user_id": "123"}, context)
"""

# Legacy exports (backward compatible)
from .tool_executor import ToolExecutor, get_tool_executor
from .base_tool import DiscordTool, ToolResult as LegacyToolResult, ToolParameter, ToolPermissionLevel
from .discord_tools import (
    DiscordTool,
    SearchMessagesTool,
    ReadChannelTool,
    SendMessageTool,
    AddReactionTool,
    GetMemberTool,
    GetServerInfoTool,
    ListChannelsTool,
    GetChannelInfoTool,
    CreateChannelTool,
    KickUserTool,
    TimeoutUserTool,
    get_all_tools,
    ALL_DISCORD_TOOLS,
)

# 🆕 COMPLETE MCP TOOLS (30 NEW TOOLS!)
from .complete_discord_tools import (
    # ⚡ Moderation
    BanUserTool,
    UnbanUserTool,
    MuteUserTool,
    UnmuteUserTool,
    
    # 📝 Channels
    CreateTextChannelTool,
    CreateVoiceChannelTool,
    DeleteChannelTool,
    RenameChannelTool,
    
    # 👤 Roles
    CreateRoleTool,
    DeleteRoleTool,
    AssignRoleTool,
    RemoveRoleTool,
    ListRolesTool,
    
    # 💬 Messages
    SendEmbedTool,
    EditMessageTool,
    DeleteMessageTool,
    PinMessageTool,
    
    # 📊 Server
    GetBannedUsersTool,
    ListMembersTool,
    
    # ✨ Profile
    ChangeNicknameTool,
    GetUserAvatarTool,
    
    # 🔍 Search & History
    
    # 🎯 Utility
    CreateInviteTool,
    
    # Helper functions
    get_all_complete_tools,
    COMPLETE_TOOL_NAMES,
)

# 🆕 EXTERNAL TOOLS (Web Search, Image Gen, Code Execution)
from .external_tools import (
    WebSearchTool,
    ImageGenerationTool,
    CodeExecutionTool,
    get_external_tools,
    EXTERNAL_TOOL_NAMES,
)

# New production-grade exports
from .registry import (
    BaseTool,
    ToolRegistry,
    ToolMetadata,
    ToolResult,
    init_registry,
    get_registry,
)

__all__ = [
    # Legacy
    'ToolExecutor',
    'get_tool_executor',
    'DiscordTool',
    'LegacyToolResult',
    'ToolParameter',
    'ToolPermissionLevel',
    'SearchMessagesTool',
    'ReadChannelTool',
    'SendMessageTool',
    'AddReactionTool',
    'GetMemberTool',
    'GetServerInfoTool',
    'ListChannelsTool',
    'GetChannelInfoTool',
    'CreateChannelTool',
    'KickUserTool',
    'TimeoutUserTool',
    'get_all_tools',
    'ALL_DISCORD_TOOLS',
    
    # ⚡ Complete Moderation Tools
    'BanUserTool',
    'UnbanUserTool',
    'MuteUserTool',
    'UnmuteUserTool',
    
    # 📝 Channel Management
    'CreateTextChannelTool',
    'CreateVoiceChannelTool',
    'DeleteChannelTool',
    'RenameChannelTool',
    
    # 👤 Role Management
    'CreateRoleTool',
    'DeleteRoleTool',
    'AssignRoleTool',
    'RemoveRoleTool',
    'ListRolesTool',
    
    # 💬 Message Operations
    'SendEmbedTool',
    'EditMessageTool',
    'DeleteMessageTool',
    'PinMessageTool',
    
    # 📊 Server Info
    'GetBannedUsersTool',
    'ListMembersTool',
    
    # ✨ Profile
    'ChangeNicknameTool',
    'GetUserAvatarTool',
    
    # 🎯 Utility
    'CreateInviteTool',
    
    # 🆕 External Tools
    'WebSearchTool',
    'ImageGenerationTool',
    'CodeExecutionTool',
    'get_external_tools',
    'EXTERNAL_TOOL_NAMES',
    
    # Complete Tools Helper
    'get_all_complete_tools',
    'COMPLETE_TOOL_NAMES',
    
    # Production Grade
    'BaseTool',
    'ToolRegistry',
    'ToolMetadata',
    'ToolResult',
    'init_registry',
    'get_registry',
]
