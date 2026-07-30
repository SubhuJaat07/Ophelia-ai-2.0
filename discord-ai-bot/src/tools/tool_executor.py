"""
🔧 Tool Executor - Handles AI Tool Calls & Executes Discord Operations
================================================================

This is the BRIDGE between AI (Groq) and Discord operations!

When AI decides to use a tool:
1. Groq returns: {name: "search_messages", arguments: {...}}
2. This executor finds the right tool
3. Validates parameters
4. Checks permissions  
5. Executes the operation
6. Returns result back to AI

AI then uses this info in its response!
"""

import logging
import json
from typing import Dict, Any, List, Optional, Callable
from .discord_tools import get_all_tools, ALL_DISCORD_TOOLS
from .base_tool import ToolResult, DiscordTool

logger = logging.getLogger("ToolExecutor")


class ToolExecutor:
    """
    Central executor for all AI tool calls.
    
    Manages tool registry, execution, and error handling.
    """
    
    def __init__(self, bot=None):
        self.bot = bot
        self._tools: Dict[str, DiscordTool] = {}
        self._tool_schemas: List[Dict] = []
        
        # Initialize tools
        self._register_all_tools()
    
    def _register_all_tools(self):
        """Register all available Discord tools"""
        tools = get_all_tools(bot=self.bot)
        
        for tool in tools:
            self._tools[tool.name] = tool
            self._tool_schemas.append(tool.schema)
            logger.debug(f"📦 Registered tool: {tool.name}")
        
        logger.info(f"🛠️ Tool Executor ready with {len(self._tools)} tools")
    
    @property
    def tool_names(self) -> List[str]:
        """List of all registered tool names"""
        return list(self._tools.keys())
    
    @property
    def schemas_for_groq(self) -> List[Dict]:
        """Get tool schemas formatted for Groq function calling"""
        return self._tool_schemas
    
    def get_tool_schema_summary(self) -> str:
        """Get human-readable summary of all tools (for system prompt)"""
        lines = ["🛠️ **AVAILABLE TOOLS I CAN USE:**\n"]
        
        for name, tool in self._tools.items():
            params = ", ".join([f"`{p.name}`" for p in tool.parameters if p.required])
            lines.append(f"• **{name}**({params}) - {tool.description[:100]}...\n")
        
        return "\n".join(lines)
    
    async def execute_tool_call(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        context: Dict[str, Any] = None
    ) -> ToolResult:
        """
        Execute a specific tool call from AI.
        
        Args:
            tool_name: Name of the tool to execute
            arguments: Parameters from AI (JSON object)
            context: Execution context (guild, channel, user, etc.)
        
        Returns:
            ToolResult with execution results
        """
        # Find tool
        if tool_name not in self._tools:
            logger.warning(f"❌ Unknown tool requested: {tool_name}")
            return ToolResult(
                success=False,
                content=f"❌ Unknown tool: '{tool_name}'. Available: {', '.join(self.tool_names)}",
                error=f"Tool not found: {tool_name}"
            )
        
        tool = self._tools[tool_name]
        
        # Parse arguments if string
        if isinstance(arguments, str):
            try:
                arguments = json.loads(arguments)
            except json.JSONDecodeError:
                return ToolResult(
                    success=False,
                    content=f"❌ Invalid arguments format for {tool_name}",
                    error="JSON parse error"
                )
        
        # Execute with context
        try:
            result = await tool.run(arguments, context or {})
            
            logger.info(
                f"{'✅' if result.success else '❌'} Tool {tool_name}: "
                f"{result.content[:80]}..."
            )
            
            return result
            
        except Exception as e:
            logger.error(f"💥 Tool execution crashed: {e}", exc_info=True)
            return ToolResult(
                success=False,
                content=f"❌ Tool execution failed: {str(e)[:200]}",
                error=str(e)
            )
    
    async def process_ai_tool_calls(
        self,
        tool_calls: List[Dict[str, Any]],
        context: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """
        Process multiple tool calls from AI response.
        
        Args:
            tool_calls: List of {id, type, function: {name, arguments}}
            context: Execution context
        
        Returns:
            List of {tool_call_id, result} for API response
        """
        results = []
        
        for call in tool_calls:
            try:
                func_info = call.get("function", {})
                tool_name = func_info.get("name", "")
                arguments_str = func_info.get("arguments", "{}")
                
                # Parse arguments
                try:
                    arguments = json.loads(arguments_str)
                except:
                    arguments = {"raw": arguments_str}
                
                # Execute
                result = await self.execute_tool_call(tool_name, arguments, context)
                
                # Format for Groq API response
                results.append({
                    "tool_call_id": call.get("id", ""),
                    "role": "tool",
                    "content": json.dumps(result.to_dict())
                })
                
            except Exception as e:
                logger.error(f"Failed to process tool call: {e}")
                results.append({
                    "tool_call_id": call.get("id", ""),
                    "role": "tool",
                    "content": json.dumps({
                        "success": False,
                        "error": str(e)[:200]
                    })
                })
        
        return results
    
    def build_context_from_message(self, message) -> Dict[str, Any]:
        """Build execution context from a Discord message"""
        ctx = {
            "message": message,
            "channel_id": str(message.channel.id),
            "author_id": str(message.author.id),
            "author_name": message.author.display_name,
        }
        
        if message.guild:
            ctx["guild"] = message.guild
            ctx["guild_id"] = str(message.guild.id)
            ctx["is_owner"] = self._check_if_owner(message.author.id)
            ctx["is_moderator"] = self._check_if_moderator(message.author, message.guild)
        
        return ctx
    
    def _check_if_owner(self, user_id) -> bool:
        """Check if user is bot owner"""
        try:
            from config.settings import is_owner
            return is_owner(user_id)
        except:
            return False
    
    def _check_if_moderator(self, member, guild) -> bool:
        """Check if user has moderation permissions"""
        if not member or not guild:
            return False
        
        # Check roles or permissions
        if guild.owner_id == member.id:
            return True
        
        perms = guild.permissions_for(member)
        return any([
            perms.administrator,
            perms.manage_guild,
            perms.kick_members,
            perms.ban_members,
            perms.moderate_members
        ])
    
    def __repr__(self) -> str:
        return f"<ToolExecutor(tools={len(self._tools)})>"


# Singleton instance
_executor_instance: Optional[ToolExecutor] = None


def get_tool_executor(bot=None) -> ToolExecutor:
    """Get singleton ToolExecutor instance"""
    global _executor_instance
    
    if _executor_instance is None or (_executor_instance.bot is None and bot is not None):
        _executor_instance = ToolExecutor(bot=bot)
    
    return _executor_instance


def reset_executor():
    """Reset singleton (for testing/reinit)"""
    global _executor_instance
    _executor_instance = None
