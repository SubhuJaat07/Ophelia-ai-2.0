"""
Persistent Cache Manager with FILE-BASED BACKUP
Memory survives restarts! 💾
"""
import json
import time
import os
import logging
import asyncio
from typing import Dict, List, Optional, Any
from threading import Lock
from cachetools import TTLCache
from pathlib import Path

logger = logging.getLogger("Cache")

# Storage directory for persistent data
STORAGE_DIR = Path("/app/data") if os.path.exists("/app") else Path("./data")
CONVERSATIONS_FILE = STORAGE_DIR / "conversations.json"
MEMORIES_FILE = STORAGE_DIR / "memories.json"
USER_PREFERENCES_FILE = STORAGE_DIR / "user_preferences.json"


class PersistentCacheManager:
    """
    ENHANCED Cache Manager with:
    ✅ In-memory cache for speed
    ✅ File-based persistence for survival across restarts
    ✅ Auto-save on important updates
    ✅ Load from files on startup
    """
    
    def __init__(self, default_ttl: int = 3600, max_size: int = 1000):
        self.default_ttl = default_ttl
        
        # Ensure storage directory exists
        STORAGE_DIR.mkdir(parents=True, exist_ok=True)
        
        # Separate caches for different data types
        self.guild_settings_cache: TTLCache = TTLCache(
            maxsize=max_size,
            ttl=default_ttl
        )
        
        self.conversation_cache: TTLCache = TTLCache(
            maxsize=max_size * 10,
            ttl=default_ttl * 24 * 7  # Conversations stay for 1 week!
        )
        
        self.memory_cache: TTLCache = TTLCache(
            maxsize=max_size * 5,
            ttl=default_ttl * 24 * 30  # Memories stay for 30 days!
        )
        
        self.user_context_cache: TTLCache = TTLCache(
            maxsize=max_size * 20,
            ttl=default_ttl * 24 * 7  # User context stays 1 week
        )
        
        # Persistent storage (loaded from files)
        self._persistent_conversations: Dict[str, List[Dict]] = {}
        self._persistent_memories: Dict[str, List[Dict]] = {}
        self._persistent_user_prefs: Dict[str, Dict] = {}
        
        self._lock = Lock()
        
        # Load persistent data from files on startup
        self._load_persistent_data()
        
        logger.info(f"💾 Persistent cache initialized | Storage: {STORAGE_DIR}")
    
    def _load_persistent_data(self):
        """Load data from JSON files on startup - THIS IS THE MAGIC! ✨"""
        try:
            # Load conversations
            if CONVERSATIONS_FILE.exists():
                with open(CONVERSATIONS_FILE, 'r', encoding='utf-8') as f:
                    self._persistent_conversations = json.load(f)
                logger.info(f"📂 Loaded {len(self._persistent_conversations)} conversation histories from disk")
            
            # Load memories
            if MEMORIES_FILE.exists():
                with open(MEMORIES_FILE, 'r', encoding='utf-8') as f:
                    self._persistent_memories = json.load(f)
                logger.info(f"🧠 Loaded {len(self._persistent_memories)} memory sets from disk")
            
            # Load user preferences
            if USER_PREFERENCES_FILE.exists():
                with open(USER_PREFERENCES_FILE, 'r', encoding='utf-8') as f:
                    self._persistent_user_prefs = json.load(f)
                logger.info(f"👤 Loaded {len(self._persistent_user_prefs)} user preferences from disk")
                
        except Exception as e:
            logger.error(f"❌ Error loading persistent data: {e}")
    
    def _save_conversations_to_disk(self):
        """Save conversations to JSON file"""
        try:
            # Merge in-memory + persistent data
            all_conv = dict(self._persistent_conversations)
            for key in self.conversation_cache:
                all_conv[key] = self.conversation_cache[key]
            
            with open(CONVERSATIONS_FILE, 'w', encoding='utf-8') as f:
                json.dump(all_conv, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Error saving conversations: {e}")
    
    def _save_memories_to_disk(self):
        """Save memories to JSON file"""
        try:
            all_mem = dict(self._persistent_memories)
            for key in self.memory_cache:
                all_mem[key] = self.memory_cache[key]
            
            with open(MEMORIES_FILE, 'w', encoding='utf-8') as f:
                json.dump(all_mem, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Error saving memories: {e}")
    
    def _save_user_prefs_to_disk(self):
        """Save user preferences to JSON file"""
        try:
            all_prefs = dict(self._persistent_user_prefs)
            for key in self.user_context_cache:
                all_prefs[key] = self.user_context_cache[key]
            
            with open(USER_PREFERENCES_FILE, 'w', encoding='utf-8') as f:
                json.dump(all_prefs, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Error saving user prefs: {e}")
    
    # ==================== GUILD SETTINGS ====================
    
    def get_guild_settings(self, guild_id: int) -> Optional[Dict]:
        key = f"guild:{guild_id}"
        with self._lock:
            return self.guild_settings_cache.get(key)
    
    def set_guild_settings(self, guild_id: int, settings: Dict):
        key = f"guild:{guild_id}"
        with self._lock:
            self.guild_settings_cache[key] = settings
    
    def invalidate_guild(self, guild_id: int):
        key = f"guild:{guild_id}"
        with self._lock:
            if key in self.guild_settings_cache:
                del self.guild_settings_cache[key]
    
    # ==================== CONVERSATION HISTORY (PERSISTENT!) ====================
    
    def get_conversation(self, channel_id: int) -> Optional[List[Dict]]:
        """
        Get conversation history - checks both cache AND persistent storage!
        This is how memory survives restarts! 🔄
        """
        key = str(channel_id)
        
        # First check in-memory cache (faster)
        with self._lock:
            cached = self.conversation_cache.get(key)
            if cached:
                return cached
            
            # Then check persistent storage (survives restarts!)
            if key in self._persistent_conversations:
                return self._persistent_conversations[key]
        
        return None
    
    def set_conversation(self, channel_id: int, messages: List[Dict]):
        """Set conversation in both cache and persistent storage"""
        key = str(channel_id)
        with self._lock:
            # Update in-memory cache
            self.conversation_cache[key] = messages
            # Update persistent storage
            self._persistent_conversations[key] = messages
        
        # Save to disk asynchronously
        asyncio.create_task(self._async_save(self._save_conversations_to_disk))
    
    def add_to_conversation(self, channel_id: int, message: Dict, max_length: int = 50):
        """Add message to conversation - PERSISTS TO DISK!"""
        key = str(channel_id)
        with self._lock:
            # Get existing or create new
            messages = self.conversation_cache.get(key) or \
                      self._persistent_conversations.get(key, []) or []
            
            messages.append(message)
            
            # Keep only last max_length messages
            if len(messages) > max_length:
                messages = messages[-max_length:]
            
            # Update both storages
            self.conversation_cache[key] = messages
            self._persistent_conversations[key] = messages
        
        # Save to disk
        asyncio.create_task(self._async_save(self._save_conversations_to_disk))
    
    def clear_conversation(self, channel_id: int):
        """Clear conversation from both cache and disk"""
        key = str(channel_id)
        with self._lock:
            if key in self.conversation_cache:
                del self.conversation_cache[key]
            if key in self._persistent_conversations:
                del self._persistent_conversations[key]
        
        asyncio.create_task(self._async_save(self._save_conversations_to_disk))
    
    # ==================== MEMORIES (PERSISTENT!) ====================
    
    def get_memories(self, guild_id: int, user_id: Optional[int] = None) -> Optional[List[Dict]]:
        """Get memories - checks cache then persistent storage"""
        key = f"{guild_id}:{user_id or 'all'}"
        
        with self._lock:
            cached = self.memory_cache.get(key)
            if cached:
                return cached
            
            if key in self._persistent_memories:
                return self._persistent_memories[key]
        
        return None
    
    def set_memories(self, guild_id: int, user_id: Optional[int], memories: List[Dict]):
        """Set memories - saves to disk!"""
        key = f"{guild_id}:{user_id or 'all'}"
        with self._lock:
            self.memory_cache[key] = memories
            self._persistent_memories[key] = memories
        
        asyncio.create_task(self._async_save(self._save_memories_to_disk))
    
    # ==================== USER CONTEXT (PERSISTENT!) ====================
    
    def get_user_context(self, user_id: int) -> Optional[Dict]:
        """Get user context/preferences"""
        key = str(user_id)
        with self._lock:
            cached = self.user_context_cache.get(key)
            if cached:
                return cached
            
            if key in self._persistent_user_prefs:
                return self._persistent_user_prefs[key]
        
        return None
    
    def set_user_context(self, user_id: int, context: Dict):
        """Set user context - saves to disk!"""
        key = str(user_id)
        with self._lock:
            self.user_context_cache[key] = context
            self._persistent_user_prefs[key] = context
        
        asyncio.create_task(self._async_save(self._save_user_prefs_to_disk))
    
    async def _async_save(self, save_func):
        """Async wrapper for saving to disk"""
        try:
            save_func()
        except Exception as e:
            logger.error(f"Async save error: {e}")
    
    async def warmup_from_database(self, db_manager):
        """Load data from database into cache (if available)"""
        logger.info("🔥 Warming up cache from database...")
        start_time = time.time()
        
        try:
            all_settings = await db_manager.get_all_guild_settings()
            for guild_id, settings in all_settings.items():
                self.set_guild_settings(guild_id, settings)
            
            elapsed = time.time() - start_time
            logger.info(f"✅ Cache warmed up! Loaded {len(all_settings)} guild settings in {elapsed:.2f}s")
            
        except Exception as e:
            logger.warning(f"⚠️ Database warmup failed (using file storage instead): {e}")
    
    async def sync_guild_to_db(self, guild_id: int, settings: Dict, db_manager):
        """Sync guild settings to cache and database"""
        self.set_guild_settings(guild_id, settings)
        
        try:
            await db_manager.upsert_guild_settings(guild_id, settings)
        except Exception as e:
            logger.warning(f"DB sync failed (settings still in cache): {e}")
    
    def get_stats(self) -> Dict[str, int]:
        """Get cache statistics including persistent storage"""
        with self._lock:
            return {
                "guild_settings": len(self.guild_settings_cache),
                "conversations_memory": len(self.conversation_cache),
                "conversations_disk": len(self._persistent_conversations),
                "memories_memory": len(self.memory_cache),
                "memories_disk": len(self._persistent_memories),
                "user_contexts_memory": len(self.user_context_cache),
                "user_contexts_disk": len(self._persistent_user_prefs)
            }
    
    def get_persistent_stats(self) -> str:
        """Get human-readable stats about persistent storage"""
        stats = self.get_stats()
        return (
            f"💾 **Persistent Memory Stats:**\n"
            f"📂 Conversations on disk: {stats['conversations_disk']}\n"
            f"🧠 Memories on disk: {stats['memories_disk']}\n"
            f"👤 User prefs on disk: {stats['user_contexts_disk']}\n"
            f"⚡ In-memory cache: {stats['conversations_memory']} convs, {stats['memories_memory']} mems\n"
            f"📁 Storage location: `{STORAGE_DIR}`"
        )


# Global cache instance
cache: Optional[PersistentCacheManager] = None


def init_cache(ttl: int = 3600, max_size: int = 1000) -> PersistentCacheManager:
    """Initialize global cache with PERSISTENCE!"""
    global cache
    cache = PersistentCacheManager(default_ttl=ttl, max_size=max_size)
    return cache


def get_cache() -> PersistentCacheManager:
    """Get global cache instance"""
    if cache is None:
        raise RuntimeError("Cache not initialized! Call init_cache() first.")
    return cache
