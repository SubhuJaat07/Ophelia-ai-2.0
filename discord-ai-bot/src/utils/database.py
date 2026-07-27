"""
Supabase Database Manager
Handles all database operations for guild settings, conversations, and memories
"""
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
from supabase import create_client, Client

logger = logging.getLogger("Database")


class DatabaseManager:
    """Manages all Supabase database operations"""
    
    def __init__(self, url: str, key: str):
        self.client: Client = create_client(url, key)
        self._ensure_tables_exist()
    
    def _ensure_tables_exist(self):
        """Ensure required tables exist (run SQL migrations if needed)"""
        # Note: Tables should be created via Supabase dashboard or migration
        # This is just a placeholder for initialization
        logger.info("Database connection established")
    
    # ==================== GUILD SETTINGS ====================
    
    async def get_guild_settings(self, guild_id: int) -> Dict[str, Any]:
        """Get settings for a specific guild (server)"""
        try:
            response = self.client.table("guild_settings")\
                .select("*")\
                .eq("guild_id", str(guild_id))\
                .execute()
            
            if response.data:
                settings = response.data[0]
                # Parse JSON fields
                if isinstance(settings.get("ai_channel_ids"), str):
                    settings["ai_channel_ids"] = json.loads(settings["ai_channel_ids"])
                return settings
            return None
        except Exception as e:
            logger.error(f"Error fetching guild {guild_id} settings: {e}")
            return None
    
    async def upsert_guild_settings(self, guild_id: int, settings: Dict[str, Any]) -> bool:
        """Insert or update guild settings"""
        try:
            data = {
                "guild_id": str(guild_id),
                **settings,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
            
            # Convert lists to JSON strings
            if "ai_channel_ids" in data and isinstance(data["ai_channel_ids"], list):
                data["ai_channel_ids"] = json.dumps(data["ai_channel_ids"])
            
            response = self.client.table("guild_settings")\
                .upsert(data, on_conflict="guild_id")\
                .execute()
            
            return len(response.data) > 0
        except Exception as e:
            logger.error(f"Error updating guild {guild_id} settings: {e}")
            return False
    
    async def get_all_guild_settings(self) -> Dict[int, Dict]:
        """Get all guild settings (for cache warm-up)"""
        try:
            response = self.client.table("guild_settings").select("*").execute()
            
            result = {}
            for item in response.data or []:
                gid = int(item.get("guild_id", 0))
                if isinstance(item.get("ai_channel_ids"), str):
                    item["ai_channel_ids"] = json.loads(item["ai_channel_ids"])
                result[gid] = item
            
            return result
        except Exception as e:
            logger.error(f"Error fetching all guild settings: {e}")
            return {}
    
    # ==================== CONVERSATION HISTORY ====================
    
    async def save_message(
        self,
        guild_id: int,
        channel_id: int,
        user_id: int,
        role: str,
        content: str
    ) -> bool:
        """Save a message to conversation history"""
        try:
            data = {
                "guild_id": str(guild_id),
                "channel_id": str(channel_id),
                "user_id": str(user_id),
                "role": role,  # "user", "assistant", "system"
                "content": content,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            
            response = self.client.table("conversations").insert(data).execute()
            return True
        except Exception as e:
            logger.error(f"Error saving message: {e}")
            return False
    
    async def get_conversation_history(
        self,
        guild_id: int,
        channel_id: int,
        limit: int = 50
    ) -> List[Dict]:
        """Get recent conversation history for a channel"""
        try:
            response = self.client.table("conversations")\
                .select("*")\
                .eq("guild_id", str(guild_id))\
                .eq("channel_id", str(channel_id))\
                .order("created_at", desc=True)\
                .limit(limit)\
                .execute()
            
            # Reverse to get chronological order
            messages = (response.data or [])[::-1]
            return [{"role": m["role"], "content": m["content"]} for m in messages]
        except Exception as e:
            logger.error(f"Error fetching conversation history: {e}")
            return []
    
    async def get_user_conversation_history(
        self,
        guild_id: int,
        user_id: int,
        limit: int = 30
    ) -> List[Dict]:
        """Get conversation history with a specific user"""
        try:
            response = self.client.table("conversations")\
                .select("*")\
                .eq("guild_id", str(guild_id))\
                .eq("user_id", str(user_id))\
                .order("created_at", desc=True)\
                .limit(limit)\
                .execute()
            
            messages = (response.data or [])[::-return [{"role": m["role"], "content": m["content"]} for m in messages]
        except Exception as e:
            logger.error(f"Error fetching user conversation history: {e}")
            return []
    
    async def clear_conversation_history(self, guild_id: int, channel_id: int) -> bool:
        """Clear conversation history for a channel"""
        try:
            self.client.table("conversations")\
                .delete()\
                .eq("guild_id", str(guild_id))\
                .eq("channel_id", str(channel_id))\
                .execute()
            return True
        except Exception as e:
            logger.error(f"Error clearing conversation history: {e}")
            return False
    
    # ==================== LONG-TERM MEMORIES ====================
    
    async def save_memory(
        self,
        guild_id: int,
        user_id: int,
        memory_type: str,
        content: str,
        importance: float = 1.0
    ) -> bool:
        """Save a long-term memory about a user or server"""
        try:
            data = {
                "guild_id": str(guild_id),
                "user_id": str(user_id),
                "memory_type": memory_type,  # "user_preference", "server_fact", "conversation_summary"
                "content": content,
                "importance": importance,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "last_accessed": datetime.now(timezone.utc).isoformat()
            }
            
            response = self.client.table("memories").insert(data).execute()
            return True
        except Exception as e:
            logger.error(f"Error saving memory: {e}")
            return False
    
    async def get_memories(
        self,
        guild_id: int,
        user_id: Optional[int] = None,
        limit: int = 20
    ) -> List[Dict]:
        """Get relevant memories for context"""
        try:
            query = self.client.table("memories")\
                .select("*")\
                .eq("guild_id", str(guild_id))\
                .order("importance", desc=True)\
                .order("last_accessed", desc=True)\
                .limit(limit)
            
            if user_id:
                query = query.or_(f"user_id.eq.{str(user_id)},user_id.eq.global")
            
            response = query.execute()
            return response.data or []
        except Exception as e:
            logger.error(f"Error fetching memories: {e}")
            return []
    
    async def update_memory_access(self, memory_id: str):
        """Update last accessed timestamp for a memory"""
        try:
            self.client.table("memories")\
                .update({"last_accessed": datetime.now(timezone.utc).isoformat()})\
                .eq("id", memory_id)\
                .execute()
        except Exception as e:
            logger.error(f"Error updating memory access: {e}")
    
    async def summarize_and_store_conversation(
        self,
        guild_id: int,
        channel_id: int,
        summary: str
    ):
        """Summarize old conversations and store as memory"""
        try:
            # Store summary as a memory
            await self.save_memory(
                guild_id=guild_id,
                user_id=0,  # Global/server-level memory
                memory_type="conversation_summary",
                content=f"[Channel {channel_id}] {summary}",
                importance=0.8
            )
            
            # Clear old individual messages but keep recent ones
            # This is a simplified version - implement pagination for production
            pass
        except Exception as e:
            logger.error(f"Error summarizing conversation: {e}")


# Global database instance
db: Optional[DatabaseManager] = None


def init_database(url: str, key: str) -> DatabaseManager:
    """Initialize the global database instance"""
    global db
    db = DatabaseManager(url, key)
    return db


def get_db() -> DatabaseManager:
    """Get the global database instance"""
    if db is None:
        raise RuntimeError("Database not initialized! Call init_database() first.")
    return db
