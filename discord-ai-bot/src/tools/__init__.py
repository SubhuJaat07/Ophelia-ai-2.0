"""
🛠️ Ophelia AI Tools - MCP-Style Function Calling Layer
=============================================

This module provides Discord operation tools that the AI can invoke!
Makes Ophelia a TRUE functional bot - not just chat!

Tools Categories:
🔍 Search & Read: Find messages, read channels
💬 Messaging: Send, reply, react  
👥 Members: Lookup users, get info
🏠 Server: Info, channels list
⚡ ACTIONS: Create channel, kick, timeout (REAL Discord API!)

Usage:
    from src.tools import get_tool_executor
    executor = get_tool_executor()
    result = await executor.execute_tool("search_messages", {"query": "gaming"})
"""

from .tool_executor import ToolExecutor, get_tool_executor
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
    CreateChannelTool,      # 🆕 REAL Channel Creation!
    KickUserTool,          # 🆕 REAL Kick Action!
    TimeoutUserTool        # 🆕 REAL Timeout Action!
)

__all__ = [
    'ToolExecutor',
    'get_tool_executor',
    'DiscordTool',
    'SearchMessagesTool',
    'ReadChannelTool',
    'SendMessageTool',
    'AddReactionTool',
    'GetMemberTool',
    'GetServerInfoTool',
    'ListChannelsTool',
    'GetChannelInfoTool',
    'CreateChannelTool',      # 🆕
    'KickUserTool',          # 🆕
    'TimeoutUserTool'        # 🆕
]
