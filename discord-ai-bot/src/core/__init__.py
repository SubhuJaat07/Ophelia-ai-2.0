"""
Core Package - Production-grade infrastructure for Ophelia MCP Server

Components:
- permissions: Hierarchical permission system
- reliability: Retry, rate limiting, health monitoring
- registry: Tool registry with metadata (in tools package)
"""

from .permissions import (
    PermissionLevel,
    ToolPermission,
    PermissionChecker,
    init_permission_checker,
    get_permission_checker,
    is_bot_owner,
    set_owner_ids,
    PERMISSION_TEMPLATES,
    LEVEL_NAMES,
)

from .reliability import (
    RetryConfig,
    RetryStrategy,
    RateLimitHandler,
    RequestQueue,
    HealthMonitor,
    with_retry,
    get_rate_limit_handler,
    init_health_monitor,
    get_health_monitor,
)

__all__ = [
    # Permissions
    "PermissionLevel",
    "ToolPermission",
    "PermissionChecker",
    "init_permission_checker",
    "get_permission_checker",
    "is_bot_owner",
    "set_owner_ids",
    "PERMISSION_TEMPLATES",
    "LEVEL_NAMES",
    
    # Reliability
    "RetryConfig",
    "RetryStrategy",
    "RateLimitHandler",
    "RequestQueue",
    "HealthMonitor",
    "with_retry",
    "get_rate_limit_handler",
    "init_health_monitor",
    "get_health_monitor",
]
