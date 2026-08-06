"""
Production-Grade Permission System for Ophelia MCP Server
==========================================================

Hierarchical Permission Levels:
    OWNER > ADMIN > MODERATOR > TRUSTED_BOT > AI_AGENT > MEMBER > READ_ONLY

Every tool MUST declare:
    - required_permission: Minimum permission level
    - required_discord_permission: Discord permission (e.g., ban_members)
    - guild_only: Can this run in DMs?
    - dm_allowed: Can this run in DMs?
    - owner_only: Only bot owners?
    - dangerous: Is this destructive?
    - confirmation_required: Needs user confirmation?
    - human_approval_required: Needs human-in-loop?
    - rate_limit: Max uses per minute
    - cooldown: Seconds between uses

Author: Production-Grade Implementation
"""
import time
import logging
from enum import IntEnum
from typing import Dict, Any, List, Optional, Set, Callable
from dataclasses import dataclass, field
from functools import wraps
from discord import Member, Guild, Permissions

logger = logging.getLogger("Permissions")


class PermissionLevel(IntEnum):
    """
    Hierarchical permission levels.
    Higher value = More permissions.
    """
    READ_ONLY = 0       # Can only read info
    MEMBER = 1          # Basic user
    AI_AGENT = 2        # AI agent with elevated access
    TRUSTED_BOT = 3     # Trusted bot/service account
    MODERATOR = 4       # Server moderator
    ADMIN = 5           # Server administrator
    OWNER = 6           # Bot/Guild owner (FULL ACCESS)


# Permission level names for display
LEVEL_NAMES = {
    PermissionLevel.READ_ONLY: "Read Only",
    PermissionLevel.MEMBER: "Member",
    PermissionLevel.AI_AGENT: "AI Agent",
    PermissionLevel.TRUSTED_BOT: "Trusted Bot",
    PermissionLevel.MODERATOR: "Moderator",
    PermissionLevel.ADMIN: "Administrator",
    PermissionLevel.OWNER: "Owner",
}

# Owner IDs from config (will be set during init)
OWNER_IDS: Set[int] = set()


def set_owner_ids(ids: Set[int]):
    """Set the bot owner IDs globally"""
    global OWNER_IDS
    OWNER_IDS = ids
    logger.info(f"👑 Owner IDs configured: {len(OWNER_IDS)} owners")


def is_bot_owner(user_id: int) -> bool:
    """Check if user is a bot owner"""
    return user_id in OWNER_IDS


@dataclass
class ToolPermission:
    """
    Complete permission definition for a tool.
    
    Every MCP tool must have one of these.
    """
    # Core permissions
    required_permission: PermissionLevel = PermissionLevel.MEMBER
    required_discord_permissions: List[str] = field(default_factory=list)
    
    # Context restrictions
    guild_only: bool = False      # Must be in a server (not DM)
    dm_allowed: bool = True       # Allowed in DMs
    
    # Access control
    owner_only: bool = False      # Only bot owners can use
    
    # Safety flags
    dangerous: bool = False       # Destructive action (ban, kick, delete)
    confirmation_required: bool = False  # Needs explicit user confirmation
    human_approval_required: bool = False  # Needs human-in-loop approval
    
    # Rate limiting
    rate_limit: int = 10          # Uses per minute (0 = unlimited)
    cooldown: float = 0.0         # Seconds between uses (0 = none)
    
    # Metadata
    category: str = "general"     # Tool category
    description: str = ""         # Human-readable description
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "required_permission": self.required_permission.name,
            "required_discord_permissions": self.required_discord_permissions,
            "guild_only": self.guild_only,
            "dm_allowed": self.dm_allowed,
            "owner_only": self.owner_only,
            "dangerous": self.dangerous,
            "confirmation_required": self.confirmation_required,
            "human_approval_required": self.human_approval_required,
            "rate_limit": self.rate_limit,
            "cooldown": self.cooldown,
            "category": self.category,
        }


class PermissionChecker:
    """
    Centralized permission checking system.
    
    Validates:
    - User permission level
    - Discord permissions
    - Guild/DM context
    - Owner status
    - Rate limits
    - Cooldowns
    - Dangerous action approvals
    """
    
    def __init__(self):
        # Rate limiting storage: {tool_name: {user_id: [timestamps]}}
        self._rate_limit_tracker: Dict[str, Dict[int, List[float]]] = {}
        
        # Cooldown storage: {tool_name: {user_id: last_use_time}}
        self._cooldown_tracker: Dict[str, Dict[int, float]] = {}
        
        # Pending confirmations: {confirmation_token: {tool, user, args, expires}}
        self._pending_confirmations: Dict[str, Dict[str, Any]] = {}
        
        # Human approval queue: {approval_id: {tool, user, args, status}}
        self._approval_queue: Dict[str, Dict[str, Any]] = {}
        
        logger.info("🔒 Permission Checker initialized")
    
    def get_user_permission_level(
        self, 
        user_id: int, 
        member: Optional[Member] = None,
        guild: Optional[Guild] = None
    ) -> PermissionLevel:
        """
        Determine user's permission level.
        
        Hierarchy:
        1. Bot Owners → OWNER level always
        2. Guild Owner → OWNER level in that guild
        3. Admin perms → ADMIN level
        4. Mod perms → MODERATOR level
        5. Everyone else → MEMBER
        """
        # Check bot owner first (global)
        if is_bot_owner(user_id):
            return PermissionLevel.OWNER
        
        # Need member/guild for Discord-based checks
        if not member or not guild:
            return PermissionLevel.MEMBER  # Default for DMs
        
        # Guild owner
        if guild.owner_id == user_id:
            return PermissionLevel.OWNER
        
        # Check Discord permissions
        perms: Permissions = guild.permissions_for(member)
        
        if perms.administrator:
            return PermissionLevel.ADMIN
        
        # Check for moderation permissions
        mod_perms = [
            perms.manage_guild,
            perms.kick_members,
            perms.ban_members,
            perms.moderate_members,
            perms.manage_channels,
            perms.manage_roles,
        ]
        
        if any(mod_perms):
            return PermissionLevel.MODERATOR
        
        return PermissionLevel.MEMBER
    
    async def check_permission(
        self,
        tool_perm: ToolPermission,
        user_id: int,
        member: Optional[Member] = None,
        guild: Optional[Guild] = None,
        is_dm: bool = False
    ) -> tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
        """
        Comprehensive permission check.
        
        Returns:
            (allowed, denial_reason, metadata)
            
        Metadata includes:
            - level: User's permission level
            - requirements: What was checked
            - approval_info: If approval needed
        """
        user_level = self.get_user_permission_level(user_id, member, guild)
        metadata = {
            "level": user_level.name,
            "required": tool_perm.required_permission.name,
            "user_id": user_id,
        }
        
        # 1. Owner-only check
        if tool_perm.owner_only and not is_bot_owner(user_id):
            return False, "This action is restricted to bot owners only.", metadata
        
        # 2. Guild-only check
        if tool_perm.guild_only and (is_dm or not guild):
            return False, "This action can only be used within a server.", metadata
        
        # 3. DM allowed check
        if is_dm and not tool_perm.dm_allowed:
            return False, "This action cannot be used in direct messages.", metadata
        
        # 4. Permission level check
        if user_level < tool_perm.required_permission:
            return (
                False, 
                f"Insufficient permissions. Required: {LEVEL_NAMES.get(tool_perm.required_permission, 'Unknown')}, "
                f"Your level: {LEVEL_NAMES.get(user_level, 'Unknown')}",
                metadata
            )
        
        # 5. Discord permissions check
        if member and guild and tool_perm.required_discord_permissions:
            perms: Permissions = guild.permissions_for(member)
            missing_perms = []
            
            for perm_name in tool_perm.required_discord_permissions:
                if not getattr(perms, perm_name, False):
                    missing_perms.append(perm_name)
            
            if missing_perms:
                return (
                    False,
                    f"Missing Discord permissions: {', '.join(missing_perms)}",
                    metadata
                )
        
        # 6. Rate limit check
        rate_ok, rate_msg = self._check_rate_limit(tool_perm, user_id)
        if not rate_ok:
            return False, rate_msg, metadata
        
        # 7. Cooldown check
        cd_ok, cd_msg = self._check_cooldown(tool_perm, user_id)
        if not cd_ok:
            return False, cd_msg, metadata
        
        # 8. Dangerous action checks
        if tool_perm.dangerous:
            metadata["dangerous"] = True
            metadata["confirmation_required"] = tool_perm.confirmation_required
            metadata["human_approval_required"] = tool_perm.human_approval_required
            
            # If confirmation required and not yet confirmed
            if tool_perm.confirmation_required:
                token = self._generate_confirmation_token(user_id, tool_perm)
                metadata["confirmation_token"] = token
                # Don't deny, just flag it
                logger.info(f"⚠️ Dangerous action requires confirmation: {token}")
        
        return True, None, metadata
    
    def _check_rate_limit(self, tool_perm: ToolPermission, user_id: int) -> tuple[bool, Optional[str]]:
        """Check if user has exceeded rate limit"""
        if tool_perm.rate_limit <= 0:
            return True, None  # No rate limit
        
        # This would need a proper tool name - using category as proxy
        tool_key = tool_perm.category
        
        now = time.time()
        window_start = now - 60.0  # 1 minute window
        
        if tool_key not in self._rate_limit_tracker:
            self._rate_limit_tracker[tool_key] = {}
        
        if user_id not in self._rate_limit_tracker[tool_key]:
            self._rate_limit_tracker[tool_key][user_id] = []
        
        # Clean old entries
        self._rate_limit_tracker[tool_key][user_id] = [
            t for t in self._rate_limit_tracker[tool_key][user_id]
            if t > window_start
        ]
        
        usage_count = len(self._rate_limit_tracker[tool_key][user_id])
        
        if usage_count >= tool_perm.rate_limit:
            return False, f"Rate limit exceeded ({tool_perm.rate_limit}/minute). Try again soon."
        
        # Record this use
        self._rate_limit_tracker[tool_key][user_id].append(now)
        return True, None
    
    def _check_cooldown(self, tool_perm: ToolPermission, user_id: int) -> tuple[bool, Optional[str]]:
        """Check if user is on cooldown"""
        if tool_perm.cooldown <= 0:
            return True, None  # No cooldown
        
        tool_key = tool_perm.category
        now = time.time()
        
        if tool_key not in self._cooldown_tracker:
            self._cooldown_tracker[tool_key] = {}
        
        if user_id in self._cooldown_tracker[tool_key]:
            last_use = self._cooldown_tracker[tool_key][user_id]
            elapsed = now - last_use
            
            if elapsed < tool_perm.cooldown:
                remaining = tool_perm.cooldown - elapsed
                return False, f"Cooldown active. Please wait {remaining:.1f} seconds."
        
        # Update last use time
        self._cooldown_tracker[tool_key][user_id] = now
        return True, None
    
    def _generate_confirmation_token(self, user_id: int, tool_perm: ToolPermission) -> str:
        """Generate a confirmation token for dangerous actions"""
        import hashlib
        import secrets
        
        raw = f"{user_id}:{tool_perm.category}:{time.time()}:{secrets.token_hex(8)}"
        token = hashlib.sha256(raw.encode()).hexdigest()[:16]
        
        # Store pending confirmation
        self._pending_confirmations[token] = {
            "user_id": user_id,
            "tool_category": tool_perm.category,
            "created_at": time.time(),
            "expires_at": time.time() + 300.0,  # 5 minutes
            "confirmed": False,
        }
        
        return token
    
    def confirm_action(self, token: str, user_id: int) -> tuple[bool, str]:
        """Confirm a pending dangerous action"""
        if token not in self._pending_confirmations:
            return False, "Invalid or expired confirmation token."
        
        conf = self._pending_confirmations[token]
        
        # Verify user
        if conf["user_id"] != user_id:
            return False, "This confirmation was issued to a different user."
        
        # Check expiry
        if time.time() > conf["expires_at"]:
            del self._pending_confirmations[token]
            return False, "Confirmation token has expired."
        
        # Confirm
        conf["confirmed"] = True
        logger.info(f"✅ Action confirmed by user {user_id}: {token}")
        return True, "Action confirmed."
    
    def request_human_approval(
        self,
        tool_name: str,
        user_id: int,
        action_description: str,
        context: Dict[str, Any] = None
    ) -> str:
        """
        Request human approval for critical actions.
        
        Returns approval ID for tracking.
        """
        import hashlib
        import secrets
        
        approval_id = hashlib.sha256(
            f"approval:{user_id}:{tool_name}:{time.time()}:{secrets.token_hex(8)}".encode()
        ).hexdigest()[:16]
        
        self._approval_queue[approval_id] = {
            "tool_name": tool_name,
            "requester_id": user_id,
            "action_description": action_description,
            "context": context or {},
            "requested_at": time.time(),
            "status": "pending",  # pending, approved, rejected
            "reviewed_by": None,
            "reviewed_at": None,
        }
        
        logger.warning(f"🔔 Human approval requested: {approval_id} | {action_description}")
        return approval_id
    
    def review_approval(
        self,
        approval_id: str,
        reviewer_id: int,
        approved: bool,
        reason: str = ""
    ) -> tuple[bool, str]:
        """Review (approve/reject) a pending human approval request"""
        if approval_id not in self._approval_queue:
            return False, "Approval request not found."
        
        approval = self._approval_queue[approval_id]
        
        if approval["status"] != "pending":
            return False, "This request has already been reviewed."
        
        # Reviewer must be owner or admin
        if not is_bot_owner(reviewer_id):
            return False, "Only bot owners can review approval requests."
        
        approval["status"] = "approved" if approved else "rejected"
        approval["reviewed_by"] = reviewer_id
        approval["reviewed_at"] = time.time()
        approval["review_reason"] = reason
        
        status = "APPROVED" if approved else "REJECTED"
        logger.info(f"📋 Approval {approval_id}: {status} by {reviewer_id}")
        
        return True, f"Request {status}."
    
    def get_pending_approvals(self) -> List[Dict[str, Any]]:
        """Get all pending human approval requests"""
        return [
            {**v, "id": k}
            for k, v in self._approval_queue.items()
            if v["status"] == "pending"
        ]
    
    def record_tool_usage(self, tool_name: str, user_id: int, success: bool, duration_ms: float):
        """Record tool execution for audit log"""
        # This feeds into the audit logging system
        logger.info(
            f"📊 Tool Usage: {tool_name} | User: {user_id} | "
            f"Success: {success} | Duration: {duration_ms:.0f}ms"
        )


# Global permission checker instance
_permission_checker: Optional[PermissionChecker] = None


def init_permission_checker(owner_ids: Set[int] = None) -> PermissionChecker:
    """Initialize global permission checker"""
    global _permission_checker
    
    _permission_checker = PermissionChecker()
    
    if owner_ids:
        set_owner_ids(owner_ids)
    
    return _permission_checker


def get_permission_checker() -> PermissionChecker:
    """Get global permission checker instance"""
    global _permission_checker
    if _permission_checker is None:
        _permission_checker = PermissionChecker()
    return _permission_checker


# Pre-defined permission templates for common tool types
PERMISSION_TEMPLATES = {
    # Safe read operations
    "read_info": ToolPermission(
        required_permission=PermissionLevel.MEMBER,
        category="info",
        description="Read information"
    ),
    
    # Basic actions (send message, react)
    "basic_action": ToolPermission(
        required_permission=PermissionLevel.MEMBER,
        category="communication",
        description="Basic communication actions"
    ),
    
    # Channel management
    "channel_manage": ToolPermission(
        required_permission=PermissionLevel.MODERATOR,
        required_discord_permissions=["manage_channels"],
        guild_only=True,
        category="moderation",
        description="Channel management"
    ),
    
    # Role management
    "role_manage": ToolPermission(
        required_permission=PermissionLevel.ADMIN,
        required_discord_permissions=["manage_roles"],
        guild_only=True,
        dangerous=True,
        confirmation_required=True,
        category="admin",
        description="Role management"
    ),
    
    # User moderation (kick, timeout, mute)
    "moderation": ToolPermission(
        required_permission=PermissionLevel.MODERATOR,
        required_discord_permissions=["kick_members", "moderate_members"],
        guild_only=True,
        dangerous=True,
        confirmation_required=True,
        cooldown=30.0,  # 30 seconds between moderations
        category="moderation",
        description="User moderation actions"
    ),
    
    # Ban user (most severe)
    "ban": ToolPermission(
        required_permission=PermissionLevel.ADMIN,
        required_discord_permissions=["ban_members"],
        guild_only=True,
        dangerous=True,
        confirmation_required=True,
        human_approval_required=True,  # Bans need human approval!
        cooldown=60.0,
        category="admin",
        description="User ban (destructive)"
    ),
    
    # Delete content
    "delete_content": ToolPermission(
        required_permission=PermissionLevel.MODERATOR,
        required_discord_permissions=["manage_messages"],
        guild_only=True,
        dangerous=True,
        confirmation_required=True,
        cooldown=10.0,
        category="moderation",
        description="Content deletion"
    ),
    
    # Server configuration
    "server_config": ToolPermission(
        required_permission=PermissionLevel.ADMIN,
        required_discord_permissions=["manage_guild", "administrator"],
        guild_only=True,
        owner_only=False,  # Admins can config, but owners override
        dangerous=True,
        confirmation_required=True,
        category="admin",
        description="Server configuration"
    ),
    
    # Bot owner exclusive
    "bot_admin": ToolPermission(
        required_permission=PermissionLevel.OWNER,
        owner_only=True,
        category="system",
        description="Bot administration (owners only)"
    ),
}
