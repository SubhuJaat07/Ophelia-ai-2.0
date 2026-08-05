"""
🛠️ Ophelia AI Tools - MCP-Style Function Calling Layer (Production Grade)
========================================================================

This module provides Discord operation tools that the AI can invoke!
Makes Ophelia a TRUE functional bot - not just chat!

Tools Categories:
🔍 Search & Read: Find messages, read channels
💬 Messaging: Send, reply, react  
👥 Members: Lookup users, get info
🏠 Server: Info, channels list
⚡ ACTIONS: Create channel, kick, timeout (REAL Discord API!)

NEW IN PRODUCTION GRADE:
- Tool Registry with metadata
- Permission integration
- Safety system integration
- Structured logging
- Plugin support

Usage:
    from src.tools import get_tool_executor, get_registry
    executor = get_tool_executor()
    result = await executor.execute_tool("search_messages", {"query": "gaming"})
    
    # Or use registry directly:
    registry = get_registry()
    tool = registry.get("search_messages")
    result = await tool.run({"query": "gaming"}, context)
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
    
    # New Production Grade
    'BaseTool',
    'ToolRegistry',
    'ToolMetadata',
    'ToolResult',
    'init_registry',
    'get_registry',
]
