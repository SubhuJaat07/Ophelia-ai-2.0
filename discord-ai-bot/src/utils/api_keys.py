"""
🔑 API Keys Manager - Multi-Key Support with Auto-Rotation
==========================================================

Supports comma-separated API keys in .env files:
- GROQ_API_KEYS=key1,key2,key3
- TAVILY_API_KEY=key1 (single)
- E2B_API_KEY=key1 (single)

Features:
✅ Parse comma-separated keys from env
✅ Auto-rotation on failure
✅ Health tracking per key
✅ Fallback support
"""

import os
import logging
import random
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger("APIKeysManager")


class KeyStatus(Enum):
    """API Key health status"""
    HEALTHY = "healthy"
    RATE_LIMITED = "rate_limited"
    ERROR = "error"
    DISABLED = "disabled"


@dataclass
class KeyInfo:
    """Information about an API key"""
    key: str
    status: KeyStatus = KeyStatus.HEALTHY
    success_count: int = 0
    error_count: int = 0
    last_used: Optional[float] = None
    rate_limited_until: float = 0
    
    @property
    def is_available(self) -> bool:
        import time
        if self.status == KeyStatus.DISABLED:
            return False
        if self.status == KeyStatus.RATE_LIMITED:
            return time.time() > self.rate_limited_until
        return True


class MultiKeyManager:
    """
    Manages multiple API keys with auto-rotation.
    
    Usage:
        manager = MultiKeyManager("GROQ_API_KEYS")
        key = manager.get_next_key()
        # Use key...
        manager.report_success(key)
        
        # On error:
        manager.report_failure(key)
    """
    
    def __init__(self, env_var_name: str, default: str = None):
        """
        Initialize key manager from environment variable.
        
        Args:
            env_var_name: Name of environment variable (e.g., "GROQ_API_KEYS")
            default: Default value if env not set
        """
        self.env_var_name = env_var_name
        self.keys: Dict[str, KeyInfo] = {}
        self.key_order: List[str] = []
        self.current_index = 0
        
        # Load keys from environment
        raw_value = os.getenv(env_var_name, default or "")
        keys_list = self._parse_keys(raw_value)
        
        for key in keys_list:
            self.keys[key] = KeyInfo(key=key)
            self.key_order.append(key)
        
        logger.info(f"🔑 {env_var_name}: {len(self.keys)} key(s) loaded")
    
    def _parse_keys(self, raw_value: str) -> List[str]:
        """Parse comma-separated keys from string"""
        if not raw_value or not raw_value.strip():
            return []
        
        # Split by comma and clean up
        keys = [k.strip() for k in raw_value.split(",") if k.strip()]
        return keys
    
    @property
    def has_keys(self) -> bool:
        """Check if any keys are available"""
        return len(self.keys) > 0
    
    @property
    def available_count(self) -> int:
        """Count of available (healthy) keys"""
        return sum(1 for k in self.keys.values() if k.is_available)
    
    @property
    def total_count(self) -> int:
        """Total number of keys"""
        return len(self.keys)
    
    def get_next_key(self) -> Optional[str]:
        """
        Get next available key using round-robin with health awareness.
        
        Returns:
            Next healthy key, or None if no keys available
        """
        if not self.has_keys:
            logger.warning(f"⚠️ No keys configured for {self.env_var_name}")
            return None
        
        import time
        
        # Try to find next healthy key starting from current index
        attempts = 0
        while attempts < len(self.key_order):
            key = self.key_order[self.current_index % len(self.key_order)]
            self.current_index += 1
            
            key_info = self.keys.get(key)
            if key_info and key_info.is_available:
                key_info.last_used = time.time()
                return key
            
            attempts += 1
        
        # All keys unhealthy - try random one anyway (last resort)
        available = [k for k, v in self.items() if v.status != KeyStatus.DISABLED]
        if available:
            key = random.choice(available)
            self.keys[key].last_used = time.time()
            logger.warning(f"⚠️ All keys unhealthy for {self.env_var_name}, using fallback")
            return key
        
        logger.error(f"❌ No available keys for {self.env_var_name}")
        return None
    
    def report_success(self, key: str):
        """Report successful API call with this key"""
        if key in self.keys:
            info = self.keys[key]
            info.success_count += 1
            info.error_count = max(0, info.error_count - 1)  # Decay errors
            if info.status == KeyStatus.ERROR:
                info.status = KeyStatus.HEALTHY
            logger.debug(f"✅ Success reported for {self.env_var_name} key (total: {info.success_count})")
    
    def report_failure(self, key: str, is_rate_limit: bool = False):
        """Report failed API call with this key"""
        import time
        
        if key in self.keys:
            info = self.keys[key]
            info.error_count += 1
            
            if is_rate_limit:
                info.status = KeyStatus.RATE_LIMITED
                info.rate_limited_until = time.time() + 60  # 1 minute cooldown
                logger.warning(f"⏰ Rate limited on {self.env_var_name} key, cooling down...")
            elif info.error_count >= 3:
                info.status = KeyStatus.ERROR
                logger.warning(f"❌ Multiple failures on {self.env_var_name} key, marking as error")
            
            logger.debug(f"❌ Failure reported for {self.env_var_name} key (errors: {info.error_count})")
    
    def get_status_report(self) -> Dict[str, Any]:
        """Get status report of all keys"""
        import time
        
        report = {
            "env_var": self.env_var_name,
            "total_keys": self.total_count,
            "available_keys": self.available_count,
            "keys": []
        }
        
        for key, info in self.items():
            report["keys"].append({
                "key_preview": f"{key[:8]}...{key[-4:]}" if len(key) > 12 else key,
                "status": info.status.value,
                "successes": info.success_count,
                "errors": info.error_count,
                "is_available": info.is_available
            })
        
        return report
    
    def items(self):
        """Iterate over key items"""
        return self.keys.items()


# ============================================================
# 🌐 PRE-CONFIGURED KEY MANAGERS
# ============================================================

# Global instances (lazy initialized)
_managers: Dict[str, MultiKeyManager] = {}


def get_key_manager(env_var_name: str, default: str = None) -> MultiKeyManager:
    """
    Get or create a key manager for the given environment variable.
    
    Usage:
        groq_manager = get_key_manager("GROQ_API_KEYS")
        key = groq_manager.get_next_key()
    """
    global _managers
    
    if env_var_name not in _managers:
        _managers[env_var_name] = MultiKeyManager(env_var_name, default)
    
    return _managers[env_var_name]


def get_grok_keys() -> MultiKeyManager:
    """Get Groq API keys manager"""
    return get_key_manager("GROQ_API_KEYS")


def get_tavily_key() -> Optional[str]:
    """Get Tavily API key (single or first of multiple)"""
    raw = os.getenv("TAVILY_API_KEY", "")
    if raw:
        keys = [k.strip() for k in raw.split(",") if k.strip()]
        return keys[0] if keys else None
    return None


def get_e2b_key() -> Optional[str]:
    """Get E2B API key (single or first of multiple)"""
    raw = os.getenv("E2B_API_KEY", "")
    if raw:
        keys = [k.strip() for k in raw.split(",") if k.strip()]
        return keys[0] if keys else None
    return None


def get_nvidia_key() -> Optional[str]:
    """Get NVIDIA API key"""
    return os.getenv("NVIDIA_API_KEY")


def get_gemini_key() -> Optional[str]:
    """Get Gemini API key (single or first of multiple)"""
    raw = os.getenv("GEMINI_API_KEY", "")
    if raw:
        keys = [k.strip() for k in raw.split(",") if k.strip()]
        return keys[0] if keys else None
    return None


def get_openrouter_key() -> Optional[str]:
    """Get OpenRouter API key (single or first of multiple)"""
    raw = os.getenv("OPENROUTER_API_KEY", "")
    if raw:
        keys = [k.strip() for k in raw.split(",") if k.strip()]
        return keys[0] if keys else None
    return None


def get_supabase_config() -> Dict[str, str]:
    """Get Supabase configuration"""
    return {
        "url": os.getenv("SUPABASE_URL", ""),
        "key": os.getenv("SUPABASE_KEY", "")
    }


def print_all_key_status():
    """Print status of all configured API keys"""
    print("\n" + "="*60)
    print("🔑 API KEYS STATUS")
    print("="*60)
    
    providers = [
        ("GROQ_API_KEYS", "Groq AI"),
        ("TAVILY_API_KEY", "Tavily Search"),
        ("E2B_API_KEY", "E2B Sandbox"),
        ("NVIDIA_API_KEY", "NVIDIA NIM"),
        ("GEMINI_API_KEY", "Gemini AI"),
        ("OPENROUTER_API_KEY", "OpenRouter"),
        ("SUPABASE_URL", "Supabase DB"),
    ]
    
    for env_var, name in providers:
        value = os.getenv(env_var, "")
        if value:
            # Show preview only
            if "," in value:
                keys = [k.strip() for k in value.split(",")]
                print(f"  ✅ {name}: {len(keys)} key(s)")
            else:
                preview = f"{value[:8]}...{value[-4:]}" if len(value) > 12 else value
                print(f"  ✅ {name}: {preview}")
        else:
            print(f"  ❌ {name}: Not set")
    
    print("="*60 + "\n")


if __name__ == "__main__":
    # Test the key manager
    print_all_key_status()
    
    # Test multi-key parsing
    os.environ["TEST_KEYS"] = "key1,key2,key3,key4,key5"
    manager = MultiKeyManager("TEST_KEYS")
    
    print(f"Loaded {manager.total_count} keys")
    print(f"Available: {manager.available_count}")
    
    # Simulate rotation
    print("\nKey rotation test:")
    for i in range(7):
        key = manager.get_next_key()
        print(f"  {i+1}. {key}")
