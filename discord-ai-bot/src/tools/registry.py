"""
Enhanced Tool Registry for Ophelia MCP Server
==============================================

Production-grade tool management:
- Auto-registration of tools
- Complete metadata (name, description, category, permissions)
- Schema generation for AI function calling
- Integration with Permission System
- Integration with Safety System
- Plugin support

Tool Categories:
- info: Read-only information retrieval
- communication: Send messages, react
- moderation: Kick, ban, timeout, mute
- admin: Server configuration, roles
- system: Bot administration

Author: Production-Grade Implementation
"""
import time
import importlib
import inspect
import logging
from typing import Dict, Any, List, Optional, Type, Callable
from dataclasses import dataclass, field
from pathlib import Path
from abc import ABC, abstractmethod

from ..core.permissions import (
    ToolPermission,
    PermissionLevel,
    PERMISSION_TEMPLATES,
    get_permission_checker
)
from ..safety.system import SafetySystem, get_safety_system, DangerLevel
from ..observability.logger import (
    ObservabilityManager, 
    get_observability,
    EventType,
    LogLevel
)

logger = logging.getLogger("ToolRegistry")


@dataclass
class ToolMetadata:
    """
    Complete metadata for a registered tool.
    
    Every tool in the registry has this.
    """
    # Identity
    name: str
    description: str
    
    # Categorization
    category: str = "general"
    tags: List[str] = field(default_factory=list)
    
    # Versioning
    version: str = "1.0.0"
    
    # Permissions (from core.permissions.ToolPermission)
    permission: ToolPermission = None
    
    # Safety (auto-derived from safety system)
    danger_level: DangerLevel = DangerLevel.LOW
    requires_confirmation: bool = False
    reversible: bool = False
    
    # Execution
    enabled: bool = True
    deprecated: bool = False
    deprecation_message: str = ""
    
    # Examples for AI to understand usage
    examples: List[Dict[str, Any]] = field(default_factory=list)
    # Format: [{"user_input": "...", "tool_call": {...}, "explanation": "..."}]
    
    # Transport support
    supported_transports: List[str] = field(default_factory=lambda: ["stdio", "http"])
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary"""
        return {
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "tags": self.tags,
            "version": self.version,
            "permission": self.permission.to_dict() if self.permission else None,
            "danger_level": self.danger_level.value,
            "requires_confirmation": self.requires_confirmation,
            "reversible": self.reversible,
            "enabled": self.enabled,
            "deprecated": self.deprecated,
            "examples": self.examples,
        }


@dataclass 
class ToolResult:
    """Standardized result from tool execution"""
    success: bool
    content: str  # Human-readable result for AI
    data: Optional[Dict[str, Any]] = None  # Structured data
    error: Optional[str] = None
    action_id: Optional[str] = None  # For audit tracking
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "content": self.content,
            "data": self.data,
            "error": self.error,
            "action_id": self.action_id,
        }


class BaseTool(ABC):
    """
    Abstract base class for all MCP tools.
    
    All tools MUST:
    1. Define metadata (name, description, category)
    2. Define parameters schema
    3. Implement execute() method
    4. Handle errors gracefully
    """
    
    # Must be defined by subclasses
    name: str = ""
    description: str = ""
    category: str = "general"
    parameters: List[Dict[str, Any]] = []
    
    # Permission template key from PERMISSION_TEMPLATES
    permission_template: str = "read_info"
    
    # Is this tool enabled?
    enabled: bool = True
    
    def __init__(self, bot=None):
        self.bot = bot
        self._metadata: Optional[ToolMetadata] = None
        
        # Initialize systems on first use
        self._perm_checker = None
        self._safety_system = None
        self._observability = None
    
    @property
    def metadata(self) -> ToolMetadata:
        """Get or create tool metadata"""
        if not self._metadata:
            # Get safety info
            safety = get_safety_system()
            danger = safety.get_danger_level(self.name)
            
            self._metadata = ToolMetadata(
                name=self.name,
                description=self.description,
                category=self.category,
                permission=PERMISSION_TEMPLATES.get(
                    self.permission_template, 
                    PERMISSION_TEMPLATES["read_info"]
                ),
                danger_level=danger,
                requires_confirmation=danger.value in ["medium", "high", "critical"],
                reversible=danger == DangerLevel.MEDIUM,
            )
        
        return self._metadata
    
    @property
    def schema(self) -> Dict[str, Any]:
        """Generate JSON schema for AI function calling"""
        properties = {}
        required = []
        
        for param in self.parameters:
            prop_def = {
                "type": param.get("type", "string"),
                "description": param.get("description", ""),
            }
            
            if "enum" in param:
                prop_def["enum"] = param["enum"]
            
            if param.get("default") is not None:
                prop_def["default"] = param["default"]
            
            properties[param["name"]] = prop_def
            
            if param.get("required", False):
                required.append(param["name"])
        
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required,
                },
            },
        }
    
    async def run(
        self, 
        args: Dict[str, Any], 
        context: Dict[str, Any] = None
    ) -> ToolResult:
        """
        Main entry point - validates permissions, executes, logs.
        
        This is called by the ToolExecutor.
        """
        start_time = time.time()
        obs = get_observability()
        
        # Get context values
        user_id = int(context.get("user_id", 0)) if context else 0
        guild_id = int(context.get("guild_id", 0)) if context else 0
        
        try:
            # 1. Check if tool is enabled
            if not self.enabled:
                return ToolResult(
                    success=False,
                    content=f"Tool '{self.name}' is currently disabled.",
                    error="TOOL_DISABLED"
                )
            
            # 2. Validate parameters
            is_valid, error_msg = self._validate_args(args)
            if not is_valid:
                obs.log(EventType.TOOL_EXECUTION_ERROR, f"Validation failed: {error_name}",
                            tool_name=self.name, user_id=user_id, error=error_msg)
                return ToolResult(
                    success=False,
                    content=f"Parameter error: {error_msg}",
                    error="VALIDATION_ERROR"
                )
            
            # 3. Check permissions
            perm_ok, perm_error, perm_meta = await self._check_permissions(context)
            if not perm_ok:
                obs.log_permission_check(self.name, user_id, granted=False, reason=perm_error)
                return ToolResult(
                    success=False,
                    content=f"Permission denied: {perm_error}",
                    error="PERMISSION_DENIED"
                )
            
            obs.log_permission_check(self.name, user_id, granted=True)
            
            # 4. Safety check (for dangerous actions)
            safety = get_safety_system()
            safety_ok, safety_block, safety_info = await safety.pre_execution_check(
                tool_name=self.name,
                user_id=user_id,
                arguments=args,
                context=context
            )
            
            if not safety_ok:
                obs.log(EventType.SAFETY_CONFIRMATION_REQUESTED,
                            f"Safety block for {self.name}",
                            level=LogLevel.WARNING,
                            tool_name=self.name, user_id=user_id)
                
                return ToolResult(
                    success=False,
                    content=safety_block,
                    error="SAFETY_BLOCK",
                    data={"safety_info": safety_info}
                )
            
            # 5. Create audit entry
            audit_entry = safety.create_audit_entry(
                tool_name=self.name,
                executor_id=user_id,
                executor_name=context.get("author_name", "Unknown"),
                guild_id=guild_id or None,
                guild_name=context.get("guild", {}).name if context.get("guild") else None,
                target_id=args.get("target_user_id") or args.get("target_id"),
                target_type=self._get_target_type(),
                action_description=f"Execute {self.name}",
                arguments=args,
            )
            
            # 6. Execute the tool
            logger.info(f"🔧 Executing tool: {self.name} | User: {user_id}")
            
            result = await self.execute(args, context or {})
            
            duration_ms = (time.time() - start_time) * 1000
            
            # Normalize result
            if isinstance(result, str):
                result = ToolResult(success=True, content=result)
            elif isinstance(result, dict):
                result = ToolResult(**result)
            elif not isinstance(result, ToolResult):
                result = ToolResult(success=True, content=str(result))
            
            # Set audit ID
            result.action_id = audit_entry.action_id
            
            # 7. Update audit log
            status = "success" if result.success else "failed"
            safety.update_audit_entry(
                audit_entry.action_id,
                status=status,
                result=result.content[:500],
                error=result.error,
                duration_ms=duration_ms
            )
            
            # 8. Log completion
            obs.log_tool_end(
                obs.log_tool_start(self.name, user_id, args),
                success=result.success,
                result_summary=result.content[:200],
                error=result.error
            )
            
            return result
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            logger.error(f"❌ Tool {self.name} crashed: {e}", exc_info=True)
            
            obs.log(
                EventType.TOOL_EXECUTION_ERROR,
                f"Tool crashed: {self.name}",
                level=LogLevel.ERROR,
                tool_name=self.name,
                user_id=user_id,
                error=str(e)[:500],
                duration_ms=duration_ms
            )
            
            return ToolResult(
                success=False,
                content=f"Error executing {self.name}: {str(e)[:300]}",
                error=str(e)
            )
    
    def _validate_args(self, args: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """Validate arguments against parameter schema"""
        if not args:
            # Check if any params are required
            required = [p["name"] for p in self.parameters if p.get("required")]
            if required:
                return False, f"Missing required parameters: {', '.join(required)}"
            return True, None
        
        for param in self.parameters:
            pname = param["name"]
            
            # Required check
            if param.get("required") and pname not in args:
                return False, f"Missing required parameter: {pname}"
            
            # Type check (basic)
            if pname in args:
                expected = param.get("type", "string")
                value = args[pname]
                
                # Flexible type conversion
                if expected == "integer":
                    try:
                        args[pname] = int(value)
                    except (ValueError, TypeError):
                        return False, f"Parameter '{pname}' must be an integer"
                elif expected == "boolean":
                    if isinstance(value, str):
                        args[pname] = value.lower() in ('true', '1', 'yes')
                elif expected == "array":
                    if not isinstance(value, list):
                        return False, f"Parameter '{pname}' must be an array"
        
        return True, None
    
    async def _check_permissions(self, context: Dict[str, Any]) -> tuple[bool, Optional[str], Optional[Dict]]:
        """Check permissions using the permission system"""
        checker = get_permission_checker()
        
        user_id = int(context.get("user_id", 0)) if context else 0
        
        # Get member/guild from context if available
        member = context.get("member")
        guild = context.get("guild")
        is_dm = not guild
        
        return await checker.check_permission(
            tool_perm=self.metadata.permission,
            user_id=user_id,
            member=member,
            guild=guild,
            is_dm=is_dm
        )
    
    def _get_target_type(self) -> str:
        """Determine target type based on category"""
        type_map = {
            "moderation": "user",
            "admin": "server",
            "communication": "channel",
            "info": "various",
        }
        return type_map.get(self.category, "unknown")
    
    @abstractmethod
    async def execute(self, args: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        """
        Execute the tool logic.
        
        Must be implemented by all tools.
        
        Args:
            args: Validated parameters
            context: Execution context (guild, channel, user, etc.)
        
        Returns:
            ToolResult with execution results
        """
        pass


class ToolRegistry:
    """
    Central tool registry with auto-registration.
    
    Features:
    - Register tools by class or instance
    - Query tools by category/permission/name
    - Generate schemas for AI
    - Enable/disable tools
    - Plugin loading
    """
    
    def __init__(self, bot=None):
        self.bot = bot
        self._tools: Dict[str, BaseTool] = {}
        self._categories: Dict[str, List[str]] = {}
        
        logger.info("📦 Tool Registry initialized")
    
    def register(self, tool_class: Type[BaseTool], **kwargs) -> BaseTool:
        """
        Register a tool class.
        
        Args:
            tool_class: Class that extends BaseTool
            **kwargs: Arguments to pass to constructor
        
        Returns:
            Instantiated tool
        """
        instance = tool_class(bot=self.bot, **kwargs)
        
        # Skip if already registered
        if instance.name in self._tools:
            logger.debug(f"Tool {instance.name} already registered, updating...")
        
        self._tools[instance.name] = instance
        
        # Track category
        cat = instance.category
        if cat not in self._categories:
            self._categories[cat] = []
        if instance.name not in self._categories[cat]:
            self._categories[cat].append(instance.name)
        
        logger.info(f"✅ Registered tool: {instance.name} ({cat})")
        return instance
    
    def register_instance(self, tool: BaseTool) -> BaseTool:
        """Register an existing tool instance"""
        self._tools[tool.name] = tool
        
        cat = tool.category
        if cat not in self._categories:
            self._categories[cat] = []
        if tool.name not in self._categories[cat]:
            self._categories[cat].append(tool.name)
        
        logger.info(f"✅ Registered tool instance: {tool.name} ({cat})")
        return tool
    
    def get(self, name: str) -> Optional[BaseTool]:
        """Get a tool by name"""
        return self._tools.get(name)
    
    def get_all(self) -> Dict[str, BaseTool]:
        """Get all registered tools"""
        return dict(self._tools)
    
    def get_by_category(self, category: str) -> List[BaseTool]:
        """Get all tools in a category"""
        names = self._categories.get(category, [])
        return [self._tools[n] for n in names if n in self._tools]
    
    def get_enabled(self) -> List[BaseTool]:
        """Get all enabled tools"""
        return [t for t in self._tools.values() if t.enabled]
    
    def get_schemas_for_ai(self) -> List[Dict[str, Any]]:
        """Get schemas of all enabled tools for AI function calling"""
        return [t.schema for t in self.get_enabled()]
    
    def get_tools_for_permission(
        self, 
        permission_level: PermissionLevel
    ) -> List[BaseTool]:
        """Get tools usable at a given permission level"""
        return [
            t for t in self.get_enabled()
            if t.metadata.permission.required_permission <= permission_level
        ]
    
    def enable(self, name: str) -> bool:
        """Enable a tool"""
        if name in self._tools:
            self._tools[name].enabled = True
            logger.info(f"🔓 Enabled tool: {name}")
            return True
        return False
    
    def disable(self, name: str) -> bool:
        """Disable a tool"""
        if name in self._tools:
            self._tools[name].enabled = False
            logger.info(f"🔒 Disabled tool: {name}")
            return True
        return False
    
    def load_plugins(self, plugin_dir: str = "./plugins"):
        """
        Load external plugins from directory.
        
        Plugins are Python files that define tool classes.
        """
        plugin_path = Path(plugin_dir)
        
        if not plugin_path.exists():
            logger.info(f"Plugin directory not found: {plugin_dir}")
            return []
        
        loaded = []
        
        for py_file in plugin_path.glob("*.py"):
            if py_file.name.startswith("_"):
                continue
            
            try:
                # Import module
                spec = importlib.util.spec_from_file_location(
                    f"plugin_{py_file.stem}", 
                    str(py_file)
                )
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                # Find and register tool classes
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    
                    if (inspect.isclass(attr) and 
                        issubclass(attr, BaseTool) and 
                        attr != BaseTool and
                        hasattr(attr, 'name') and attr.name):
                        
                        self.register(attr)
                        loaded.append(attr.name)
                        
            except Exception as e:
                logger.error(f"Failed to load plugin {py_file}: {e}")
        
        if loaded:
            logger.info(f"🔌 Loaded {len(loaded)} plugins: {', '.join(loaded)}")
        
        return loaded
    
    @property
    def tool_names(self) -> List[str]:
        """List of all tool names"""
        return list(self._tools.keys())
    
    @property
    def categories(self) -> List[str]:
        """List of all categories"""
        return list(self._categories.keys())
    
    def get_registry_info(self) -> Dict[str, Any]:
        """Get complete registry information"""
        return {
            "total_tools": len(self._tools),
            "enabled_tools": len(self.get_enabled()),
            "categories": {
                cat: len(tools) 
                for cat, tools in self._categories.items()
            },
            "tools": [
                {
                    "name": t.name,
                    "category": t.category,
                    "enabled": t.enabled,
                    "danger": t.metadata.danger_level.value,
                }
                for t in self._tools.values()
            ]
        }
    
    def __len__(self):
        return len(self._tools)
    
    def __contains__(self, name: str):
        return name in self._tools


# Global registry instance
_registry: Optional[ToolRegistry] = None


def init_registry(bot=None) -> ToolRegistry:
    """Initialize global tool registry"""
    global _registry
    _registry = ToolRegistry(bot=bot)
    return _registry


def get_registry() -> ToolRegistry:
    """Get global tool registry"""
    global _registry
    if _registry is None:
        _registry = ToolRegistry()
    return _registry
