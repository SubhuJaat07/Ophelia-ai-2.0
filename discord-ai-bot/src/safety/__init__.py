"""
Safety Package - Action safety, confirmations, audit logging

Components:
- system: Main safety system with confirmation/approval/audit
"""

from .system import (
    SafetySystem,
    DangerLevel,
    ActionStatus,
    SafetyMetadata,
    AuditLogEntry,
    init_safety_system,
    get_safety_system,
)

__all__ = [
    "SafetySystem",
    "DangerLevel",
    "ActionStatus",
    "SafetyMetadata",
    "AuditLogEntry",
    "init_safety_system",
    "get_safety_system",
]
