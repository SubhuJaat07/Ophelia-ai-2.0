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
🌐 EXTERNAL: Web search, Image generation, Code execution!

NEW IN v3.1:
✅ Multi-Provider AI Fallback (Gemini + Groq + NVIDIA)
✅ External Tools (Tavily Search, Pollinations Images, E2B Code)
✅ Real Discord Actions (no more fake responses!)

Usage:
    from src.tools import get_tool_executor, get_registry
    executor = get_tool_executor()
    result = await executor.execute_tool("search_messages", {"query": "gaming"})
    
    # External tools:
    result = await executor.execute_tool("web_search", {"query": "cricket score"})
    result = await executor.execute_tool("generate_image", {"prompt": "cute cat"})
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

# 🆕 External Tools (Web Search, Image Gen, Code Execution)
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
    
    # 🆕 External Tools
    'WebSearchTool',
    'ImageGenerationTool',
    'CodeExecutionTool',
    'get_external_tools',
    'EXTERNAL_TOOL_NAMES',
    
    # New Production Grade
    'BaseTool',
    'ToolRegistry',
    'ToolMetadata',
    'ToolResult',
    'init_registry',
    'get_registry',
]
