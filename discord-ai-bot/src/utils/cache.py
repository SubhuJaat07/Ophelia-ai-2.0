"""
Cache Manager for Discord AI Bot
Provides fast in-memory caching with Supabase persistence
"""
import json
import time
import logging
import asyncio
from typing import Dict, List, Optional, Any
from threading import Lock
from cachetools import TTLCache

logger = logging.getLogger("Cache")


class CacheManager:
    """Thread-safe cache manager with TTL support and database sync"""
    
    def __init__(self, default_ttl: int = 3600, max_size: int = 1000):
        self.default_ttl = default_ttl
        
        # Separate caches for different data types
        self.guild_settings_cache: TTLCache = TTLCache(
            maxsize=max_size,
            ttl=default_ttl
        )
        
        self.conversation_cache: TTLCache = TTLCache(
            maxsize=max_size * 10,
            ttl=default_ttl * 2  # Conversations stay longer
        )
        
        self.memory_cache: TTLCache = TTLCache(
            maxsize=max_size * 5,
            ttl=default_ttl * 24  # Memories stay for 24 hours
        )
        
        self.user_context_cache: TTLCache = TTLCache(
            maxsize=max_size * 20,
            ttl=1800  # 30 minutes for user context
        )
        
        self._lock = Lock()
    
    def get_guild_settings(self, guild_id: int) -> Optional[Dict]:
        """Get cached guild settings"""
        key = f"guild:{guild_id}"
        with self._lock:
            return self.guild_settings_cache.get(key)
    
    def set_guild_settings(self, guild_id: int, settings: Dict):
        """Cache guild settings"""
        key = f"guild:{guild_id}"
        with self._lock:
            self.guild_settings_cache[key] = settings
    
    def invalidate_guild(self, guild_id: int):
        """Invalidate guild cache (after settings update)"""
        key = f"guild:{guild_id}"
        with self._lock:
            if key in self.guild_settings_cache:
                del self.guild_settings_cache[key]
    
    def get_conversation(self, channel_id: int) -> Optional[List[Dict]]:
        """Get cached conversation history"""
        key = f"conv:{channel_id}"
        with self._lock:
            return self.conversation_cache.get(key)
    
    def set_conversation(self, channel_id: int, messages: List[Dict]):
        """Cache conversation history"""
        key = f"conv:{channel_id}"
        with self._lock:
            self.conversation_cache[key] = messages
    
    def add_to_conversation(self, channel_id: int, message: Dict, max_length: int = 50):
        """Add message to cached conversation"""
        key = f"conv:{channel_id}"
        with self._lock:
            messages = self.conversation_cache.get(key, [])
            messages.append(message)
            # Keep only last max_length messages
            if len(messages) > max_length:
                messages = messages[-max_length:]
            self.conversation_cache[key] = messages
    
    def clear_conversation(self, channel_id: int):
        """Clear conversation cache"""
        key = f"conv:{channel_id}"
        with self._lock:
            if key in self.conversation_cache:
                del self.conversation_cache[key]
    
    def get_memories(self, guild_id: int, user_id: Optional[int] = None) -> Optional[List[Dict]]:
        """Get cached memories"""
        key = f"mem:{guild_id}:{user_id or 'all'}"
        with self._lock:
            return self.memory_cache.get(key)
    
    def set_memories(self, guild_id: int, user_id: Optional[int], memories: List[Dict]):
        """Cache memories"""
        key = f"mem:{guild_id}:{user_id or 'all'}"
        with self._lock:
            self.memory_cache[key] = memories
    
    def get_user_context(self, user_id: int) -> Optional[Dict]:
        """Get cached user context (name, preferences, etc.)"""
        key = f"user:{user_id}"
        with self._lock:
            return self.user_context_cache.get(key)
    
    def set_user_context(self, user_id: int, context: Dict):
        """Cache user context"""
        key = f"user:{user_id}"
        with self._lock:
            self.user_context_cache[key] = context
    
    async def warmup_from_database(self, db_manager):
        """Load all data from database into cache on startup"""
        logger.info("🔥 Warming up cache from database...")
        start_time = time.time()
        
        try:
            # Load all guild settings
            all_settings = await db_manager.get_all_guild_settings()
            for guild_id, settings in all_settings.items():
                self.set_guild_settings(guild_id, settings)
            
            elapsed = time.time() - start_time
            logger.info(f"✅ Cache warmed up! Loaded {len(all_settings)} guild settings in {elapsed:.2f}s")
            
        except Exception as e:
            logger.error(f"❌ Error warming up cache: {e}")
    
    async def sync_guild_to_db(self, guild_id: int, settings: Dict, db_manager):
        """Sync guild settings to both cache and database"""
        # Update cache
        self.set_guild_settings(guild_id, settings)
        
        # Update database asynchronously
        try:
            await db_manager.upsert_guild_settings(guild_id, settings)
            logger.debug(f"Synced guild {guild_id} settings to database")
        except Exception as e:
            logger.error(f"Failed to sync guild {guild_id} to DB: {e}")
    
    def get_stats(self) -> Dict[str, int]:
        """Get cache statistics"""
        with self._lock:
            return {
                "guild_settings": len(self.guild_settings_cache),
                "conversations": len(self.conversation_cache),
                "memories": len(self.memory_cache),
                "user_contexts": len(self.user_context_cache)
            }


# Global cache instance
cache: Optional[CacheManager] = None


def init_cache(ttl: int = 3600, max_size: int = 1000) -> CacheManager:
    """Initialize the global cache instance"""
    global cache
    cache = CacheManager(default_ttl=ttl, max_size=max_size)
    return cache


def get_cache() -> CacheManager:
    """Get the global cache instance"""
    if cache is None:
        raise RuntimeError("Cache not initialized! Call init_cache() first.")
    return cache
