"""
🔧 Base Tool Class - Abstract foundation for all Discord tools
============================================================

All tools must inherit from DiscordTool and implement:
- name: Tool identifier
- description: What the tool does (for AI)
- parameters: JSON schema of accepted parameters
- execute(): Async method that runs the tool
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger("DiscordTools")


class ToolPermissionLevel(Enum):
    """Who can use this tool"""
    EVERYONE = "everyone"      # All users
    MODERATOR = "moderator"    # Mods and above
    OWNER = "owner"            # Only bot owners
    DISABLED = "disabled"      # Turned off


@dataclass
class ToolParameter:
    """Definition of a tool parameter"""
    name: str
    param_type: str  # "string", "integer", "boolean", "array"
    description: str
    required: bool = True
    default: Any = None
    enum: Optional[List[str]] = None  # For limited choices


@dataclass 
class ToolResult:
    """Result from tool execution"""
    success: bool
    content: str  # Human-readable result (for AI to use)
    data: Optional[Dict[str, Any]] = None  # Structured data if needed
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "content": self.content,
            "data": self.data,
            "error": self.error
        }


class DiscordTool(ABC):
    """
    Abstract base class for all Discord tools.
    
    Every tool must:
    1. Define its schema (name, description, parameters)
    2. Implement execute() method
    3. Handle errors gracefully
    4. Return ToolResult with useful info for AI
    """
    
    # Must be defined by subclasses
    name: str = ""
    description: str = ""
    parameters: List[ToolParameter] = []
    permission_level: ToolPermissionLevel = ToolPermissionLevel.EVERYONE
    
    def __init__(self, bot=None):
        self.bot = bot
    
    @property
    def schema(self) -> Dict[str, Any]:
        """Generate JSON schema for this tool (for Groq function calling)"""
        properties = {}
        required = []
        
        for param in self.parameters:
            prop_def = {
                "type": param.param_type,
                "description": param.description
            }
            
            if param.enum:
                prop_def["enum"] = param.enum
            
            if not param.required and param.default is not None:
                prop_def["default"] = param.default
            
            properties[param.name] = prop_def
            
            if param.required:
                required.append(param.name)
        
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required
                }
            }
        }
    
    def validate_parameters(self, args: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """Validate incoming parameters against schema"""
        if not args:
            if any(p.required for p in self.parameters):
                return False, f"Missing required parameters: {[p.name for p in self.parameters if p.required]}"
            return True, None
        
        for param in self.parameters:
            if param.required and param.name not in args:
                return False, f"Missing required parameter: {param.name}"
            
            if param.name in args:
                value = args[param.name]
                
                # Type checking
                type_map = {
                    "string": str,
                    "integer": int,
                    "boolean": bool,
                    "array": list,
                    "number": (int, float)
                }
                
                expected_type = type_map.get(param.param_type, str)
                if not isinstance(value, expected_type):
                    # Try conversion for flexible input
                    try:
                        if param.param_type == "integer":
                            args[param.name] = int(value)
                        elif param.param_type == "number":
                            args[param.name] = float(value)
                        elif param.param_type == "boolean":
                            if isinstance(value, str):
                                args[param.name] = value.lower() in ('true', '1', 'yes')
                    except (ValueError, TypeError):
                        return False, f"Parameter '{param.name}' should be {param.param_type}, got {type(value).__name__}"
                
                # Enum checking
                if param.enum and value not in param.enum:
                    return False, f"Parameter '{param.name}' must be one of: {param.enum}"
        
        return True, None
    
    async def run(self, args: Dict[str, Any], context: Dict[str, Any] = None) -> ToolResult:
        """
        Main entry point - validates then executes.
        
        Args:
            args: Parameters from AI/tool call
            context: Additional context (guild, channel, user, etc.)
        
        Returns:
            ToolResult with success/failure + content for AI
        """
        # Validate parameters
        is_valid, error_msg = self.validate_parameters(args)
        if not is_valid:
            return ToolResult(
                success=False,
                content=f"❌ Parameter Error: {error_msg}",
                error=error_msg
            )
        
        # Check permissions if context provided
        if context:
            has_perm, perm_error = await self._check_permissions(context)
            if not has_perm:
                return ToolResult(
                    success=False,
                    content=f"🔒 Permission Denied: {perm_error}",
                    error=perm_error
                )
        
        try:
            # Execute the tool (safe against None args)
            safe_args = args or {}
            logger.info(f"🔧 Executing tool: {self.name} with args: {list(safe_args.keys())}")
            result = await self.execute(args, context or {})
            
            if isinstance(result, ToolResult):
                return result
            elif isinstance(result, str):
                return ToolResult(success=True, content=result)
            else:
                return ToolResult(success=True, content=str(result))
                
        except Exception as e:
            logger.error(f"❌ Tool {self.name} failed: {e}", exc_info=True)
            return ToolResult(
                success=False,
                content=f"❌ Error executing {self.name}: {str(e)[:200]}",
                error=str(e)
            )
    
    async def _check_permissions(self, context: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """Check if user has permission to use this tool"""
        user_id = context.get("user_id")
        is_owner = context.get("is_owner", False)
        is_mod = context.get("is_moderator", False)
        
        if self.permission_level == ToolPermissionLevel.DISABLED:
            return False, "This tool is currently disabled"
        
        if self.permission_level == ToolPermissionLevel.OWNER and not is_owner:
            return False, "Only bot owners can use this tool"
        
        if self.permission_level == ToolPermissionLevel.MODERATOR and not (is_owner or is_mod):
            return False, "Only moderators and owners can use this tool"
        
        return True, None
    
    @abstractmethod
    async def execute(self, args: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        """
        Execute the tool logic. Must be implemented by subclasses.
        
        Args:
            args: Validated parameters
            context: Execution context (guild, channel, author, etc.)
        
        Returns:
            ToolResult with execution results
        """
        pass
    
    def __repr__(self) -> str:
        return f"<DiscordTool:{self.name}>"
