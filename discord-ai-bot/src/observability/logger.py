"""
Observability Package - Structured Logging & Monitoring for Ophelia MCP Server
=============================================================================

Features:
- Structured JSON logging
- Error tracking with context
- Performance metrics
- Tool execution history
- Permission failure logs
- Discord API error tracking
- Retry history

Author: Production-Grade Implementation
"""
import json
import time
import logging
import traceback
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path

logger = logging.getLogger("Observability")


class LogLevel(Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class EventType(Enum):
    """Types of events we track"""
    # Tool events
    TOOL_EXECUTION_START = "tool_execution_start"
    TOOL_EXECUTION_END = "tool_execution_end"
    TOOL_EXECUTION_ERROR = "tool_execution_error"
    
    # Permission events
    PERMISSION_CHECK = "permission_check"
    PERMISSION_DENIED = "permission_denied"
    PERMISSION_GRANTED = "permission_granted"
    
    # Safety events
    SAFETY_CONFIRMATION_REQUESTED = "safety_confirmation_requested"
    SAFETY_CONFIRMATION_VALIDATED = "safety_confirmation_validated"
    SAFETY_APPROVAL_REQUESTED = "safety_approval_requested"
    SAFETY_APPROVAL_GRANTED = "safety_approval_granted"
    SAFETY_APPROVAL_DENIED = "safety_approval_denied"
    
    # Discord API events
    DISCORD_API_CALL = "discord_api_call"
    DISCORD_API_ERROR = "discord_api_error"
    DISCORD_RATE_LIMITED = "discord_rate_limited"
    
    # AI events
    AI_REQUEST_START = "ai_request_start"
    AI_REQUEST_END = "ai_request_end"
    AI_TOOL_CALL = "ai_tool_call"
    AI_RESPONSE_GENERATED = "ai_response_generated"
    AI_ERROR = "ai_error"
    
    # System events
    SYSTEM_STARTUP = "system_startup"
    SYSTEM_SHUTDOWN = "system_shutdown"
    SYSTEM_ERROR = "system_error"
    
    # Message events
    MESSAGE_RECEIVED = "message_received"
    MESSAGE_PROCESSED = "message_processed"
    MESSAGE_ERROR = "message_error"


@dataclass
class StructuredLogEntry:
    """A structured log entry with full context"""
    timestamp: str
    event_type: str
    level: str
    message: str
    
    # Context fields
    guild_id: Optional[int] = None
    channel_id: Optional[int] = None
    user_id: Optional[int] = None
    
    # Additional context
    context: Dict[str, Any] = field(default_factory=dict)
    
    # Metrics
    duration_ms: Optional[float] = None
    success: Optional[bool] = None
    
    # Error info
    error: Optional[str] = None
    error_traceback: Optional[str] = None
    
    # Request tracing
    trace_id: Optional[str] = None
    request_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ToolExecutionRecord:
    """Record of a single tool execution"""
    tool_name: str
    start_time: float
    end_time: Optional[float] = None
    duration_ms: Optional[float] = None
    success: Optional[bool] = None
    caller_user_id: Optional[int] = None
    arguments: Dict[str, Any] = field(default_factory=dict)
    result_summary: Optional[str] = None
    error_message: Optional[str] = None
    trace_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass 
class MetricPoint:
    """A single metric data point"""
    name: str
    value: float
    timestamp: float
    tags: Dict[str, str] = field(default_factory=dict)


class ObservabilityManager:
    """
    Central observability manager.
    
    Provides:
    - Structured logging to file and console
    - Tool execution tracking
    - Error aggregation
    - Performance metrics
    """
    
    def __init__(
        self,
        log_dir: str = "./data/logs",
        enable_file_logging: bool = True,
        enable_console_logging: bool = True,
        retain_logs_days: int = 7
    ):
        self.log_dir = Path(log_dir)
        self.enable_file_logging = enable_file_logging
        self.enable_console_logging = enable_console_logging
        self.retain_logs_days = retain_logs_days
        
        # In-memory log storage (for querying)
        self._log_entries: List[StructuredLogEntry] = []
        self._max_in_memory_entries = 10000
        
        # Tool execution records
        self._tool_executions: List[ToolExecutionRecord] = []
        
        # Metrics storage
        self._metrics: List[MetricPoint] = []
        
        # Error tracker (for aggregation)
        self._errors: List[Dict[str, Any]] = []
        
        # Ensure directory exists
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Current log file path
        self._current_log_file = self.log_dir / f"ophelia_{datetime.now().strftime('%Y%m%d')}.jsonl"
        
        logger.info(f"📊 Observability initialized | Log dir: {log_dir}")
    
    def log(
        self,
        event_type: EventType,
        message: str,
        level: LogLevel = LogLevel.INFO,
        **context
    ) -> StructuredLogEntry:
        """
        Create a structured log entry.
        
        Args:
            event_type: Type of event
            message: Human-readable message
            level: Log level
            **context: Additional context fields
        """
        entry = StructuredLogEntry(
            timestamp=datetime.now(timezone.utc).isoformat(),
            event_type=event_type.value,
            level=level.value,
            message=message,
            **{k: v for k, v in context.items() if k in [
                'guild_id', 'channel_id', 'user_id', 'duration_ms', 
                'success', 'error', 'error_traceback', 'trace_id', 'request_id'
            ]}
        )
        
        # Add extra context
        extra_context = {k: v for k, v in context.items() if k not in entry.__dataclass_fields__}
        if extra_context:
            entry.context = extra_context
        
        # Store in memory
        self._log_entries.append(entry)
        if len(self._log_entries) > self._max_in_memory_entries:
            self._log_entries = self._log_entries[-self._max_in_memory_entries:]
        
        # Write to file
        if self.enable_file_logging:
            self._write_to_file(entry)
        
        # Console output (for errors and warnings)
        if self.enable_console_logging and level.value in ["WARNING", "ERROR", "CRITICAL"]:
            print(f"[{level.value}] [{event_type.value}] {message}")
            if entry.error_traceback:
                print(entry.error_traceback[:500])
        
        return entry
    
    def log_tool_start(
        self,
        tool_name: str,
        user_id: int,
        arguments: Dict[str, Any],
        trace_id: str = None
    ) -> ToolExecutionRecord:
        """Log the start of a tool execution"""
        record = ToolExecutionRecord(
            tool_name=tool_name,
            start_time=time.time(),
            caller_user_id=user_id,
            arguments=arguments,
            trace_id=trace_id
        )
        
        self._tool_executions.append(record)
        
        self.log(
            EventType.TOOL_EXECUTION_START,
            f"Tool execution started: {tool_name}",
            level=LogLevel.INFO,
            tool_name=tool_name,
            user_id=user_id,
            trace_id=trace_id
        )
        
        return record
    
    def log_tool_end(
        self,
        record: ToolExecutionRecord,
        success: bool,
        result_summary: str = None,
        error: str = None
    ):
        """Log the end of a tool execution"""
        record.end_time = time.time()
        record.duration_ms = (record.end_time - record.start_time) * 1000
        record.success = success
        record.result_summary = result_summary
        record.error_message = error
        
        self.log(
            EventType.TOOL_EXECUTION_END if success else EventType.TOOL_EXECUTION_ERROR,
            f"Tool {'completed' if else 'failed'}: {record.tool_name} ({record.duration_ms:.0f}ms)",
            level=LogLevel.INFO if success else LogLevel.ERROR,
            tool_name=record.tool_name,
            duration_ms=record.duration_ms,
            success=success,
            error=error,
            trace_id=record.trace_id
        )
        
        if not success:
            self._track_error(record.tool_name, error, "tool_execution")
    
    def log_permission_check(
        self,
        tool_name: str,
        user_id: int,
        granted: bool,
        reason: str = None,
        required_level: str = None,
        user_level: str = None
    ):
        """Log a permission check result"""
        event_type = EventType.PERMISSION_GRANTED if granted else EventType.PERMISSION_DENIED
        level = LogLevel.DEBUG if granted else LogLevel.WARNING
        
        self.log(
            event_type,
            f"Permission {'granted' if granted else 'denied'} for {tool_name}",
            level=level,
            tool_name=tool_name,
            user_id=user_id,
            success=granted,
            context={
                "reason": reason,
                "required_level": required_level,
                "user_level": user_level
            }
        )
    
    def log_api_error(
        self,
        endpoint: str,
        error: str,
        status_code: int = None,
        retry_count: int = 0
    ):
        """Log a Discord API error"""
        self.log(
            EventType.DISCORD_API_ERROR,
            f"Discord API error: {endpoint}",
            level=LogLevel.ERROR,
            error=error,
            context={
                "endpoint": endpoint,
                "status_code": status_code,
                "retry_count": retry_count
            }
        )
        
        self._track_error(endpoint, error, "discord_api")
    
    def log_ai_event(
        self,
        event_type: EventType,
        model: str = None,
        tokens_used: int = None,
        tool_calls: int = None,
        duration_ms: float = None,
        error: str = None
    ):
        """Log an AI-related event"""
        self.log(
            event_type,
            f"AI Event: {event_type.value}",
            level=LogLevel.ERROR if error else LogLevel.DEBUG,
            context={
                "model": model,
                "tokens_used": tokens_used,
                "tool_calls": tool_calls,
                "duration_ms": duration_ms,
            },
            error=error
        )
    
    def _track_error(self, source: str, error: str, error_type: str):
        """Track an error for aggregation"""
        self._errors.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "source": source,
            "error": error[:500],
            "type": error_type,
        })
        
        # Keep only last 1000 errors
        if len(self._errors) > 1000:
            self._errors = self._errors[-1000:]
    
    def _write_to_file(self, entry: StructuredLogEntry):
        """Append log entry to current log file"""
        try:
            with open(self._current_log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(entry.to_dict(), default=str) + '\n')
        except Exception as e:
            print(f"Failed to write log: {e}")
    
    def query_logs(
        self,
        event_type: EventType = None,
        level: LogLevel = None,
        user_id: int = None,
        guild_id: int = None,
        start_time: datetime = None,
        end_time: datetime = None,
        limit: int = 100
    ) -> List[StructuredLogEntry]:
        """Query log entries with filters"""
        results = self._log_entries
        
        if event_type:
            results = [e for e in results if e.event_type == event_type.value]
        if level:
            results = [e for e in results if e.level == level.value]
        if user_id:
            results = [e for e in results if e.user_id == user_id]
        if guild_id:
            results = [e for e in results if e.guild_id == guild_id]
        if start_time:
            results = [e for e in results if e.timestamp >= start_time.isoformat()]
        if end_time:
            results = [e for e in results if e.timestamp <= end_time.isoformat()]
        
        return results[-limit:]
    
    def get_tool_stats(self) -> Dict[str, Any]:
        """Get statistics about tool executions"""
        if not self._tool_executions:
            return {"total_executions": 0}
        
        completed = [t for t in self._tool_executions if t.end_time is not None]
        
        by_tool = {}
        for t in completed:
            if t.tool_name not in by_tool:
                by_tool[t.tool_name] = {"count": 0, "success": 0, "total_ms": 0}
            by_tool[t.tool_name]["count"] += 1
            by_tool[t.tool_name]["total_ms"] += t.duration_ms or 0
            if t.success:
                by_tool[t.tool_name]["success"] += 1
        
        # Calculate averages
        for tool, stats in by_tool.items():
            stats["avg_ms"] = stats["total_ms"] / stats["count"] if stats["count"] > 0 else 0
            stats["success_rate"] = (stats["success"] / stats["count"] * 100) if stats["count"] > 0 else 0
            del stats["total_ms"]
        
        total_success = sum(1 for t in completed if t.success)
        
        return {
            "total_executions": len(completed),
            "successful": total_success,
            "failed": len(completed) - total_success,
            "success_rate": (total_success / len(completed) * 100) if completed > 0 else 0,
            "by_tool": by_tool,
        }
    
    def get_recent_errors(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent errors"""
        return self._errors[-limit:]
    
    def get_error_summary(self) -> Dict[str, Any]:
        """Get aggregated error information"""
        if not self._errors:
            return {"total_errors": 0}
        
        by_source = {}
        by_type = {}
        
        for e in self._errors:
            source = e["source"]
            etype = e["type"]
            
            by_source[source] = by_source.get(source, 0) + 1
            by_type[etype] = by_type.get(etype, 0) + 1
        
        # Last hour errors
        one_hour_ago = time.time() - 3600
        recent_errors = [e for e in self._errors if 
                        datetime.fromisoformat(e["timestamp"]).timestamp() > one_hour_ago]
        
        return {
            "total_errors": len(self._errors),
            "last_hour": len(recent_errors),
            "by_source": by_source,
            "by_type": by_type,
        }


# Global observability instance
_observability: Optional[ObservabilityManager] = None


def init_observability(
    log_dir: str = "./data/logs",
    **kwargs
) -> ObservabilityManager:
    """Initialize global observability manager"""
    global _observability
    _observability = ObservabilityManager(log_dir=log_dir, **kwargs)
    return _observability


def get_observability() -> ObservabilityManager:
    """Get global observability instance"""
    global _observability
    if _observability is None:
        _observability = ObservabilityManager()
    return _observability


# Convenience functions for quick logging
def log_event(event_type: EventType, message: str, **kwargs):
    """Quick logging function"""
    obs = get_observability()
    return obs.log(event_type, message, **kwargs)


def log_tool_execution(tool_name: str, success: bool, duration_ms: float, **kwargs):
    """Quick tool execution logging"""
    obs = get_observability()
    obs.log(
        EventType.TOOL_EXECUTION_END if success else EventType.TOOL_EXECUTION_ERROR,
        f"Tool {'completed' if success else 'failed'}: {tool_name}",
        level=LogLevel.INFO if success else LogLevel.ERROR,
        tool_name=tool_name,
        duration_ms=duration_ms,
        success=success,
        **kwargs
    )
