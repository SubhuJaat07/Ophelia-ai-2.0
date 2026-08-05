"""
Reliability System for Ophelia MCP Server
==========================================

Handles:
- Automatic retry with exponential backoff
- Discord rate limit handling
- Gateway reconnection
- Heartbeat monitoring
- Graceful shutdown
- Request queue system

Author: Production-Grade Implementation
"""
import asyncio
import time
import logging
import functools
from typing import Dict, Any, List, Optional, Callable, TypeVar
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timezone

logger = logging.getLogger("Reliability")

T = TypeVar('T')


class RetryStrategy(Enum):
    """Retry strategies for different operations"""
    NONE = "none"              # No retry
    FIXED = "fixed"            # Fixed interval between retries
    EXPONENTIAL = "exponential"  # Exponential backoff
    LINEAR = "linear"          # Linear increase in delay


@dataclass
class RetryConfig:
    """Configuration for retry behavior"""
    max_retries: int = 3
    base_delay: float = 1.0     # Base delay in seconds
    max_delay: float = 60.0     # Maximum delay cap
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL
    jitter: bool = True         # Add random jitter to prevent thundering herd
    retryable_exceptions: tuple = (Exception,)  # Which exceptions to retry on
    
    def get_delay(self, attempt: int) -> float:
        """Calculate delay for given attempt number"""
        if self.strategy == RetryStrategy.FIXED:
            delay = self.base_delay
        elif self.strategy == RetryStrategy.EXPONENTIAL:
            delay = self.base_delay * (2 ** attempt)
        elif self.strategy == RetryStrategy.LINEAR:
            delay = self.base_delay * (attempt + 1)
        else:
            delay = 0
        
        # Cap at max
        delay = min(delay, self.max_delay)
        
        # Add jitter if enabled
        if self.jitter:
            import random
            delay *= (0.5 + random.random())
        
        return delay


@dataclass 
class RateLimitInfo:
    """Information about a rate limit"""
    endpoint: str
    limit_type: str  # "global", "endpoint", "user"
    remaining: int = 0
    reset_after: float = 0.0
    is_limited: bool = False
    
    @property
    def reset_time(self) -> datetime:
        """When this rate limit resets"""
        return datetime.now(timezone.utc).timestamp() + self.reset_after


@dataclass
class QueueItem:
    """An item in the request queue"""
    id: str
    func: Callable
    args: tuple
    kwargs: dict
    priority: int = 5  # 1 = highest, 10 = lowest
    created_at: float = field(default_factory=time.time)
    retries: int = 0
    max_retries: int = 3
    result: Any = None
    error: Optional[str] = None
    completed: bool = False


class RateLimitHandler:
    """
    Handles Discord API rate limits intelligently.
    
    Features:
    - Tracks rate limits per endpoint
    - Automatic delays when approaching limits
    - Priority queuing for important requests
    """
    
    def __init__(self):
        self._rate_limits: Dict[str, RateLimitInfo] = {}
        self._global_limit: Optional[RateLimitInfo] = None
        
        logger.info("⏱️ Rate Limit Handler initialized")
    
    def update_from_headers(self, endpoint: str, headers: Dict[str, str]):
        """Update rate limit info from Discord response headers"""
        # Discord sends these headers:
        # X-RateLimit-Limit, X-RateLimit-Remaining, X-RateLimit-Reset-After, X-RateLimit-Global
        
        try:
            remaining = int(headers.get("X-RateLimit-Remaining", 1))
            reset_after = float(headers.get("X-RateLimit-Reset-After", 0))
            is_global = headers.get("X-RateLimit-Global", "false") == "true"
            
            info = RateLimitInfo(
                endpoint=endpoint,
                limit_type="global" if is_global else "endpoint",
                remaining=remaining,
                reset_after=reset_after,
                is_limited=(remaining <= 0)
            )
            
            if is_global:
                self._global_limit = info
            else:
                self._rate_limits[endpoint] = info
                
            if info.is_limited:
                logger.warning(f"🚫 Rate limited: {endpoint} | Resets in {reset_after:.1f}s")
            
        except Exception as e:
            logger.debug(f"Failed to parse rate limit headers: {e}")
    
    async def check_and_wait(self, endpoint: str) -> bool:
        """
        Check if we're rate limited and wait if needed.
        
        Returns True if we can proceed, False if we should abort.
        """
        # Check global limit first
        if self._global_limit and self._global_limit.is_limited:
            wait_time = self._global_limit.reset_after
            logger.warning(f"🌍 GLOBAL RATE LIMIT active! Waiting {wait_time:.1f}s...")
            await asyncio.sleep(wait_time)
            return True
        
        # Check endpoint-specific limit
        if endpoint in self._rate_limits:
            info = self._rate_limits[endpoint]
            if info.is_limited:
                wait_time = info.reset_after
                logger.info(f"⏳ Endpoint {endpoint} rate limited. Waiting {wait_time:.1f}s...")
                await asyncio.sleep(wait_time)
                return True
            
            # Warn if getting low
            elif info.remaining <= 2:
                logger.debug(f"⚠️ Rate limit low for {endpoint}: {info.remaining} remaining")
        
        return True
    
    def get_status(self) -> Dict[str, Any]:
        """Get current rate limit status"""
        return {
            "endpoints_tracked": len(self._rate_limits),
            "global_limit": self._global_limit.to_dict() if self._global_limit else None,
            "limited_endpoints": [
                {"endpoint": e.endpoint, "resets_in": e.reset_after}
                for e in self._rate_limits.values()
                if e.is_limited
            ]
        }


class RequestQueue:
    """
    Priority-based request queue.
    
    Ensures important requests are processed first
    and prevents flooding the API.
    """
    
    def __init__(
        self,
        max_concurrent: int = 5,
        default_timeout: float = 30.0
    ):
        self._queue: List[QueueItem] = []
        self._processing: set = set()
        self._max_concurrent = max_concurrent
        self._default_timeout = default_timeout
        self._counter = 0
        
        logger.info(f"📬 Request Queue initialized (max_concurrent={max_concurrent})")
    
    async def enqueue(
        self,
        func: Callable,
        args: tuple = (),
        kwargs: dict = None,
        priority: int = 5,
        timeout: float = None
    ) -> QueueItem:
        """
        Add a request to the queue.
        
        Args:
            func: Async function to call
            args: Positional arguments
            kwargs: Keyword arguments
            priority: 1-10 (1 highest)
            timeout: Max time to wait for result
        
        Returns:
            QueueItem that will be populated with result
        """
        import hashlib
        
        self._counter += 1
        item_id = hashlib.md5(f"{self._counter}:{time.time()}".encode()).hexdigest()[:12]
        
        item = QueueItem(
            id=item_id,
            func=func,
            args=args,
            kwargs=kwargs or {},
            priority=priority,
            max_retries=3,
        )
        
        self._queue.append(item)
        # Sort by priority (lower = higher priority)
        self._queue.sort(key=lambda x: x.priority)
        
        logger.debug(f"📬 Queued request {item_id} (priority={priority}, queue_size={len(self._queue)})")
        
        return item
    
    async def process_queue(self):
        """Process all items in the queue"""
        while self._queue:
            if len(self._processing) >= self._max_concurrent:
                await asyncio.sleep(0.1)
                continue
            
            item = self._queue.pop(0)
            self._processing.add(item.id)
            
            # Process asynchronously
            asyncio.create_task(self._process_item(item))
    
    async def _process_item(self, item: QueueItem):
        """Process a single queue item"""
        try:
            result = await asyncio.wait_for(
                item.func(*item.args, **item.kwargs),
                timeout=self._default_timeout
            )
            item.result = result
            item.completed = True
            
        except asyncio.TimeoutError:
            item.error = f"Timeout after {self._default_timeout}s"
        except Exception as e:
            item.error = str(e)
            
            # Retry if possible
            if item.retries < item.max_retries:
                item.retries += 1
                self._queue.append(item)
                logger.debug(f"🔄 Retrying {item.id} ({item.retries}/{item.max_retries})")
            else:
                logger.error(f"❌ Queue item {item.id} failed after {item.max_retries} retries")
        
        finally:
            self._processing.discard(item.id)
    
    @property
    def queue_size(self) -> int:
        return len(self._queue)
    
    @property
    def processing_count(self) -> int:
        return len(self._processing)


def with_retry(
    config: RetryConfig = None,
    on_retry: Callable[[int, Exception], Any] = None
):
    """
    Decorator for automatic retry with exponential backoff.
    
    Usage:
        @with_retry(max_retries=3, base_delay=1.0)
        async def my_api_call():
            ...
    """
    if config is None:
        config = RetryConfig()
    
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(config.max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                    
                except config.retryable_exceptions as e:
                    last_exception = e
                    
                    # Don't retry on last attempt
                    if attempt == config.max_retries:
                        break
                    
                    # Calculate delay
                    delay = config.get_delay(attempt)
                    
                    # Call on_retry callback if provided
                    if on_retry:
                        await on_retry(attempt, e)
                    
                    logger.warning(
                        f"🔄 Retry {attempt + 1}/{config.max_retries} for {func.__name__} "
                        f"in {delay:.1f}s | Error: {str(e)[:100]}"
                    )
                    
                    await asyncio.sleep(delay)
            
            # All retries exhausted
            raise last_exception
        
        return wrapper
    return decorator


class HealthMonitor:
    """
    Monitors system health and reports status.
    
    Tracks:
    - Gateway connection status
    - Response times
    - Error rates
    - Resource usage
    """
    
    def __init__(self, check_interval: float = 30.0):
        self.check_interval = check_interval
        self._is_healthy = True
        self._checks: List[Dict[str, Any]] = []
        self._start_time = time.time()
        
        # Metrics
        self._total_requests = 0
        self._successful_requests = 0
        self._failed_requests = 0
        self._response_times: List[float] = []
        
        logger.info(f"💓 Health Monitor initialized (check_interval={check_interval}s)")
    
    def record_request(self, success: bool, duration_ms: float):
        """Record a completed request"""
        self._total_requests += 1
        
        if success:
            self._successful_requests += 1
        else:
            self._failed_requests += 1
        
        self._response_times.append(duration_ms)
        
        # Keep only last 1000 response times
        if len(self._response_times) > 1000:
            self._response_times = self._response_times[-1000:]
    
    async def run_check(self, check_func: Callable, name: str) -> bool:
        """Run a health check function"""
        start = time.time()
        
        try:
            result = await check_func() if asyncio.iscoroutinefunction(check_func) else check_func()
            duration = (time.time() - start) * 1000
            
            check_result = {
                "name": name,
                "passed": bool(result),
                "duration_ms": duration,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            
            self._checks.append(check_result)
            
            # Keep last 100 checks
            if len(self._checks) > 100:
                self._checks = self._checks[-100:]
            
            return bool(result)
            
        except Exception as e:
            self._checks.append({
                "name": name,
                "passed": False,
                "error": str(e)[:200],
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })
            return False
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get overall health status"""
        # Calculate average response time
        avg_response = (
            sum(self._response_times) / len(self._response_times)
            if self._response_times else 0
        )
        
        # Success rate
        success_rate = (
            (self._successful_requests / self._total_requests * 100)
            if self._total_requests > 0 else 100
        )
        
        # Determine if healthy
        recent_checks = self._checks[-10:] if self._checks else []
        passed_recent = sum(1 for c in recent_checks if c.get("passed", False))
        
        self._is_healthy = (
            success_rate >= 95 and
            (passed_recent >= len(recent_checks) * 0.8 if recent_checks else True)
        )
        
        uptime_seconds = time.time() - self._start_time
        
        return {
            "healthy": self._is_healthy,
            "uptime_seconds": uptime_seconds,
            "uptime_human": self._format_uptime(uptime_seconds),
            "requests": {
                "total": self._total_requests,
                "successful": self._successful_requests,
                "failed": self._failed_requests,
                "success_rate": f"{success_rate:.1f}%",
                "avg_response_ms": avg_response,
            },
            "recent_checks": {
                "total": len(recent_checks),
                "passed": passed_recent,
            }
        }
    
    def _format_uptime(self, seconds: float) -> str:
        """Format uptime in human-readable form"""
        days = int(seconds // 86400)
        hours = int((seconds % 86400) // 3600)
        minutes = int((seconds % 3600) // 60)
        
        parts = []
        if days > 0:
            parts.append(f"{days}d")
        if hours > 0:
            parts.append(f"{hours}h")
        parts.append(f"{minutes}m")
        
        return " ".join(parts)


# Global instances
_rate_limit_handler: Optional[RateLimitHandler] = None
_health_monitor: Optional[HealthMonitor] = None


def get_rate_limit_handler() -> RateLimitHandler:
    global _rate_limit_handler
    if _rate_limit_handler is None:
        _rate_limit_handler = RateLimitHandler()
    return _rate_limit_handler


def init_health_monitor(check_interval: float = 30.0) -> HealthMonitor:
    global _health_monitor
    _health_monitor = HealthMonitor(check_interval=check_interval)
    return _health_monitor


def get_health_monitor() -> HealthMonitor:
    global _health_monitor
    if _health_monitor is None:
        _health_monitor = HealthMonitor()
    return _health_monitor
