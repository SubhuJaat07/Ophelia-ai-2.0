"""
Safety System for Ophelia MCP Server
=====================================

Handles:
- Dangerous action detection & blocking
- Confirmation token generation & validation
- Human-in-loop approval workflow
- Audit logging for all actions
- Rollback support for reversible actions

SAFETY PRINCIPLES:
1. Destructive actions MUST have explicit confirmation
2. Critical actions (ban) need human approval
3. All actions are logged for audit
4. Reversible actions support rollback
5. Rate limiting prevents abuse

Author: Production-Grade Implementation
"""
import time
import hashlib
import json
import logging
import asyncio
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timezone

logger = logging.getLogger("SafetySystem")


class DangerLevel(Enum):
    """How dangerous an action is"""
    SAFE = "safe"                    # No side effects (read info)
    LOW = "low"                      # Minor effects (send message)
    MEDIUM = "medium"                # Reversible effects (timeout, mute)
    HIGH = "high"                    # Destructive but recoverable (kick, delete channel)
    CRITICAL = "critical"            # Permanent/irreversible (ban, delete role)


class ActionStatus(Enum):
    """Status of an executed action"""
    PENDING = "pending"
    EXECUTING = "executing"
    SUCCESS = "success"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"
    REJECTED = "rejected"            # Blocked by safety system


@dataclass
class SafetyMetadata:
    """Complete safety information for a tool action"""
    danger_level: DangerLevel = DangerLevel.SAFE  # Fixed: was "DangerLevel SAFE"
    requires_confirmation: bool = False
    requires_human_approval: bool = False
    reversible: bool = False
    rollback_function: Optional[str] = None  # Name of rollback function if reversible
    reason_required: bool = True  # Must provide reason for action
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "danger_level": self.danger_level.value,
            "requires_confirmation": self.requires_confirmation,
            "requires_human_approval": self.requires_human_approval,
            "reversible": self.reversible,
            "rollback_function": self.rollback_function,
            "reason_required": self.reason_required,
        }


@dataclass 
class AuditLogEntry:
    """Single audit log entry"""
    timestamp: str
    action_id: str
    tool_name: str
    executor_id: int  # User who initiated
    executor_name: str
    guild_id: Optional[int]
    guild_name: Optional[str]
    target_id: Optional[int]  # User/channel being acted upon
    target_type: str  # "user", "channel", "role", etc.
    action_description: str
    arguments: Dict[str, Any]
    status: ActionStatus
    result: Optional[str] = None
    error: Optional[str] = None
    duration_ms: float = 0.0
    confirmation_token: Optional[str] = None
    approval_id: Optional[str] = None
    rollback_action_id: Optional[str] = None  # If this was rolled back
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "action_id": self.action_id,
            "tool_name": self.tool_name,
            "executor_id": self.executor_id,
            "executor_name": self.executor_name,
            "guild_id": self.guild_id,
            "guild_name": self.guild_name,
            "target_id": self.target_id,
            "target_type": self.target_type,
            "action_description": self.action_description,
            "arguments": self.arguments,
            "status": self.status.value,
            "result": self.result,
            "error": self.error,
            "duration_ms": self.duration_ms,
            "confirmation_token": self.confirmation_token,
            "approval_id": self.approval_id,
            "rollback_action_id": self.rollback_action_id,
        }


class SafetySystem:
    """
    Central safety system for all tool executions.
    
    Flow for dangerous actions:
    1. Pre-execution check → May require confirmation/approval
    2. Execution with full logging
    3. Post-execution validation
    4. Rollback if needed
    """
    
    def __init__(self, storage_path: str = "./data/safety"):
        self.storage_path = storage_path
        
        # Pending confirmations
        self._confirmations: Dict[str, Dict[str, Any]] = {}
        
        # Approval queue
        self._approvals: Dict[str, Dict[str, Any]] = {}
        
        # Audit log (in-memory + file)
        self._audit_log: List[AuditLogEntry] = []
        
        # Rollback registry: {tool_name: rollback_function}
        self._rollback_registry: Dict[str, Callable] = {}
        
        # Action history for potential rollback
        self._action_history: Dict[str, AuditLogEntry] = {}
        
        # Ensure storage directory exists
        import os
        os.makedirs(storage_path, exist_ok=True)
        
        logger.info(f"🛡️ Safety System initialized | Storage: {storage_path}")
    
    def get_danger_level(self, tool_name: str) -> DangerLevel:
        """
        Determine danger level for a tool.
        
        Mapping based on tool category/name.
        """
        dangerous_tools = {
            # CRITICAL - Permanent damage
            "ban_user": DangerLevel.CRITICAL,
            "delete_role_permanently": DangerLevel.CRITICAL,
            
            # HIGH - Destructive but potentially recoverable
            "kick_user": DangerLevel.HIGH,
            "delete_channel": DangerLevel.HIGH,
            "delete_role": DangerLevel.HIGH,
            "mass_delete_messages": DangerLevel.HIGH,
            "remove_all_roles": DangerLevel.HIGH,
            
            # MEDIUM - Reversible effects
            "timeout_user": DangerLevel.MEDIUM,
            "mute_user": DangerLevel.MEDIUM,
            "add_role": DangerLevel.MEDIUM,
            "remove_role": DangerLevel.MEDIUM,
            "create_channel": DangerLevel.MEDIUM,
            "create_role": DangerLevel.MEDIUM,
            "modify_permissions": DangerLevel.MEDIUM,
            
            # LOW - Minor effects
            "send_message": DangerLevel.LOW,
            "add_reaction": DangerLevel.LOW,
            "pin_message": DangerLevel.LOW,
            "unpin_message": DangerLevel.LOW,
            
            # SAFE - Read-only
            "search_messages": DangerLevel.SAFE,
            "get_channel_info": DangerLevel.SAFE,
            "get_member_info": DangerLevel.SAFE,
            "get_server_info": DangerLevel.SAFE,
            "list_channels": DangerLevel.SAFE,
            "list_members": DangerLevel.SAFE,
            "read_audit_log": DangerLevel.SAFE,
        }
        
        return dangerous_tools.get(tool_name, DangerLevel.LOW)
    
    def get_safety_metadata(self, tool_name: str) -> SafetyMetadata:
        """
        Get complete safety metadata for a tool.
        """
        danger = self.get_danger_level(tool_name)
        
        metadata = SafetyMetadata(
            danger_level=danger,
            requires_confirmation=danger.value in ["medium", "high", "critical"],
            requires_human_approval=(danger == DangerLevel.CRITICAL),
            reversible=danger.value in ["medium"],  # Timeouts/mutes can be undone
            reason_required=danger.value != "safe",
        )
        
        # Register rollback functions for reversible actions
        if tool_name == "timeout_user":
            metadata.rollback_function = "remove_timeout"
            metadata.reversible = True
        elif tool_name == "mute_user":
            metadata.rollback_function = "unmute_user"
            metadata.reversible = True
        
        return metadata
    
    async def pre_execution_check(
        self,
        tool_name: str,
        user_id: int,
        arguments: Dict[str, Any],
        context: Dict[str, Any] = None
    ) -> tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
        """
        Check if action is allowed before execution.
        
        Returns:
            (allowed, block_reason, safety_info)
        """
        metadata = self.get_safety_metadata(tool_name)
        safety_info = metadata.to_dict()
        safety_info["tool_name"] = tool_name
        
        # SAFE and LOW danger levels auto-pass
        if metadata.danger_level in [DangerLevel.SAFE, DangerLevel.LOW]:
            return True, None, safety_info
        
        # MEDIUM and above need confirmation
        if metadata.requires_confirmation:
            # Check if already confirmed
            token = arguments.get("confirmation_token")
            if token:
                is_valid, msg = self.validate_confirmation(token, user_id)
                if not is_valid:
                    return False, f"Invalid confirmation: {msg}", safety_info
            else:
                # Generate new confirmation token
                new_token = self.generate_confirmation(
                    tool_name=tool_name,
                    user_id=user_id,
                    arguments=arguments,
                    context=context
                )
                safety_info["confirmation_required"] = True
                safety_info["confirmation_token"] = new_token
                return (
                    False, 
                    f"⚠️ This action requires confirmation.\n"
                    f"Use this token to confirm: `{new_token}`\n"
                    f"Reply with: `confirm {new_token}`",
                    safety_info
                )
        
        # CRITICAL needs human approval
        if metadata.requires_human_approval:
            approval_id = self.request_approval(
                tool_name=tool_name,
                user_id=user_id,
                arguments=arguments,
                context=context
            )
            safety_info["approval_required"] = True
            safety_info["approval_id"] = approval_id
            return (
                False,
                f"🚨 This action requires owner approval.\n"
                f"Approval ID: `{approval_id}`\n"
                f"Waiting for owner review...",
                safety_info
            )
        
        return True, None, safety_info
    
    def generate_confirmation(
        self,
        tool_name: str,
        user_id: int,
        arguments: Dict[str, Any],
        context: Dict[str, Any] = None,
        ttl: int = 300  # 5 minutes
    ) -> str:
        """Generate a confirmation token for an action"""
        import secrets
        
        raw = f"{tool_name}:{user_id}:{time.time()}:{secrets.token_hex(16)}"
        token = hashlib.sha256(raw.encode()).hexdigest()[:16]
        
        self._confirmations[token] = {
            "tool_name": tool_name,
            "user_id": user_id,
            "arguments": arguments,
            "context": context or {},
            "created_at": time.time(),
            "expires_at": time.time() + ttl,
            "used": False,
        }
        
        logger.info(f"🔐 Generated confirmation: {token} for {tool_name} by {user_id}")
        return token
    
    def validate_confirmation(self, token: str, user_id: int) -> tuple[bool, str]:
        """Validate a confirmation token"""
        if token not in self._confirmations:
            return False, "Token not found."
        
        conf = self._confirmations[token]
        
        # Check user
        if conf["user_id"] != user_id:
            return False, "Token issued to different user."
        
        # Check expiry
        if time.time() > conf["expires_at"]:
            del self._confirmations[token]
            return False, "Token expired."
        
        # Check if already used
        if conf["used"]:
            return False, "Token already used."
        
        # Mark as used
        conf["used"] = True
        logger.info(f"✅ Confirmation validated: {token}")
        return True, "Confirmed."
    
    def request_approval(
        self,
        tool_name: str,
        user_id: int,
        arguments: Dict[str, Any],
        context: Dict[str, Any] = None
    ) -> str:
        """Request human approval for critical action"""
        import secrets
        
        approval_id = hashlib.sha256(
            f"approve:{tool_name}:{user_id}:{time.time()}:{secrets.token_hex(8)}".encode()
        ).hexdigest()[:16]
        
        self._approvals[approval_id] = {
            "tool_name": tool_name,
            "requester_id": user_id,
            "arguments": arguments,
            "context": context or {},
            "requested_at": time.time(),
            "status": "pending",
            "reviewed_by": None,
            "reviewed_at": None,
            "reason": None,
        }
        
        logger.warning(f"🔔 APPROVAL REQUESTED: {approval_id} | Tool: {tool_name} | By: {user_id}")
        return approval_id
    
    def review_approval(
        self,
        approval_id: str,
        reviewer_id: int,
        approved: bool,
        reason: str = ""
    ) -> tuple[bool, str]:
        """Review an approval request"""
        from src.core.permissions import is_bot_owner
        
        if approval_id not in self._approvals:
            return False, "Approval not found."
        
        approval = self._approvals[approval_id]
        
        if approval["status"] != "pending":
            return False, "Already reviewed."
        
        # Only owners can review
        if not is_bot_owner(reviewer_id):
            return False, "Only owners can approve."
        
        approval["status"] = "approved" if approved else "rejected"
        approval["reviewed_by"] = reviewer_id
        approval["reviewed_at"] = time.time()
        approval["reason"] = reason
        
        status = "✅ APPROVED" if approved else "❌ REJECTED"
        logger.info(f"📋 Approval {approval_id}: {status} by {reviewer_id}")
        
        return True, status
    
    def create_audit_entry(
        self,
        tool_name: str,
        executor_id: int,
        executor_name: str,
        guild_id: Optional[int],
        guild_name: Optional[str],
        target_id: Optional[int],
        target_type: str,
        action_description: str,
        arguments: Dict[str, Any],
        status: ActionStatus = ActionStatus.PENDING,
        **kwargs
    ) -> AuditLogEntry:
        """Create a new audit log entry"""
        action_id = hashlib.sha256(
            f"{tool_name}:{executor_id}:{time.time()}".encode()
        ).hexdigest()[:12]
        
        entry = AuditLogEntry(
            timestamp=datetime.now(timezone.utc).isoformat(),
            action_id=action_id,
            tool_name=tool_name,
            executor_id=executor_id,
            executor_name=executor_name,
            guild_id=guild_id,
            guild_name=guild_name,
            target_id=target_id,
            target_type=target_type,
            action_description=action_description,
            arguments=arguments,
            status=status,
            confirmation_token=kwargs.get("confirmation_token"),
            approval_id=kwargs.get("approval_id"),
        )
        
        self._audit_log.append(entry)
        self._action_history[action_id] = entry
        
        # Persist to file
        self._persist_audit_log()
        
        logger.info(f"📝 Audit: [{status.value}] {tool_name} by {executor_name} ({action_id})")
        return entry
    
    def update_audit_entry(
        self,
        action_id: str,
        status: ActionStatus,
        result: str = None,
        error: str = None,
        duration_ms: float = 0.0
    ):
        """Update an existing audit entry after execution"""
        if action_id in self._action_history:
            entry = self._action_history[action_id]
            entry.status = status
            entry.result = result
            entry.error = error
            entry.duration_ms = duration_ms
            
            self._persist_audit_log()
            logger.info(f"📝 Updated Audit: {action_id} → {status.value}")
    
    def register_rollback(self, tool_name: str, func: Callable):
        """Register a rollback function for a tool"""
        self._rollback_registry[tool_name] = func
        logger.info(f"🔄 Registered rollback: {tool_name}")
    
    async def execute_rollback(self, action_id: str, initiator_id: int) -> tuple[bool, str]:
        """Execute rollback for a previous action"""
        if action_id not in self._action_history:
            return False, "Action not found."
        
        entry = self._action_history[action_id]
        
        # Check if reversible
        if entry.tool_name not in self._rollback_registry:
            return False, f"No rollback available for {entry.tool_name}."
        
        # Verify initiator has permission (owner or original executor)
        from src.core.permissions import is_bot_owner
        if not is_bot_owner(initiator_id) and initiator_id != entry.executor_id:
            return False, "Only owners or original executor can rollback."
        
        try:
            rollback_func = self._rollback_registry[entry.tool_name]
            result = await rollback_func(entry.arguments, entry)
            
            # Create audit entry for rollback
            self.create_audit_entry(
                tool_name=f"rollback_{entry.tool_name}",
                executor_id=initiator_id,
                executor_name="System",
                guild_id=entry.guild_id,
                guild_name=entry.guild_name,
                target_id=entry.target_id,
                target_type=entry.target_type,
                action_description=f"Rollback of {entry.action_id}",
                arguments={"original_action_id": action_id},
                status=ActionStatus.SUCCESS
            )
            
            # Update original entry
            entry.rollback_action_id = action_id
            entry.status = ActionStatus.ROLLED_BACK
            
            logger.info(f"↩️ Rolled back action: {action_id}")
            return True, f"Rolled back successfully: {result}"
            
        except Exception as e:
            logger.error(f"❌ Rollback failed for {action_id}: {e}")
            return False, f"Rollback failed: {str(e)}"
    
    def _persist_audit_log(self):
        """Save audit log to disk"""
        try:
            filepath = f"{self.storage_path}/audit_log.json"
            data = [entry.to_dict() for entry in self._audit_log[-1000:]]  # Keep last 1000
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2, default=str)
                
        except Exception as e:
            logger.error(f"Failed to persist audit log: {e}")
    
    def get_audit_log(
        self,
        tool_name: str = None,
        user_id: int = None,
        guild_id: int = None,
        limit: int = 50
    ) -> List[AuditLogEntry]:
        """Query audit log with filters"""
        results = self._audit_log
        
        if tool_name:
            results = [e for e in results if e.tool_name == tool_name]
        if user_id:
            results = [e for e in results if e.executor_id == user_id]
        if guild_id:
            results = [e for e in results if e.guild_id == guild_id]
        
        return results[-limit:]
    
    def get_pending_confirmations(self, user_id: int = None) -> List[Dict]:
        """Get pending confirmations"""
        now = time.time()
        results = []
        
        for token, conf in list(self._confirmations.items()):
            # Clean expired
            if now > conf["expires_at"]:
                del self._confirmations[token]
                continue
                
            if conf["used"]:
                continue
                
            if user_id and conf["user_id"] != user_id:
                continue
                
            results.append({**conf, "token": token})
        
        return results
    
    def get_pending_approvals(self) -> List[Dict]:
        """Get pending human approvals"""
        return [
            {**v, "id": k}
            for k, v in self._approvals.items()
            if v["status"] == "pending"
        ]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get safety system statistics"""
        total_actions = len(self._audit_log)
        successful = sum(1 for e in self._audit_log if e.status == ActionStatus.SUCCESS)
        failed = sum(1 for e in self._audit_log if e.status == ActionStatus.FAILED)
        rolled_back = sum(1 for e in self._audit_log if e.status == ActionStatus.ROLLED_BACK)
        
        by_danger = {}
        for level in DangerLevel:
            by_danger[level.value] = sum(
                1 for e in self._audit_log 
                if self.get_danger_level(e.tool_name) == level
            )
        
        return {
            "total_actions": total_actions,
            "successful": successful,
            "failed": failed,
            "rolled_back": rolled_back,
            "success_rate": (successful / total_actions * 100) if total_actions else 0,
            "pending_confirmations": len(self.get_pending_confirmations()),
            "pending_approvals": len(self.get_pending_approvals()),
            "by_danger_level": by_danger,
        }


# Global safety system instance
_safety_system: Optional[SafetySystem] = None


def init_safety_system(storage_path: str = "./data/safety") -> SafetySystem:
    """Initialize global safety system"""
    global _safety_system
    _safety_system = SafetySystem(storage_path=storage_path)
    return _safety_system


def get_safety_system() -> SafetySystem:
    """Get global safety system instance"""
    global _safety_system
    if _safety_system is None:
        _safety_system = SafetySystem()
    return _safety_system
