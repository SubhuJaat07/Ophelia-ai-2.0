"""
AI Response Handler - UPGRADED with MULTI-MODEL SUPPORT
- Different models for different tasks
- Unique personality that makes Ophelia stand out!
- Persistent memory integration
"""
import logging
from typing import List, Dict, Optional, Any
from datetime import datetime

from config.settings import (
    DEFAULT_GUILD_SETTINGS,
    SYSTEM_PROMPTS,
    BASE_SYSTEM_PROMPT
)
from src.utils.database import get_db
from src.utils.cache import get_cache
from src.utils.groq_client import get_groq_client, TaskType

logger = logging.getLogger("AIHandler")


class AIHandler:
    """
    ENHANCED AI Handler with:
    ✅ Multi-model smart routing
    ✅ Unique personality system
    ✅ Persistent memory support
    """
    
    def __init__(self):
        self.db = None
        self.cache = None
        self.groq = None
    
    def _init_clients(self):
        """Lazy initialization of clients"""
        if not self.db:
            self.db = get_db()
        if not self.cache:
            self.cache = get_cache()
        if not self.groq:
            self.groq = get_groq_client()
    
    async def get_guild_settings(self, guild_id: int) -> Dict[str, Any]:
        """Get guild settings from cache or database"""
        self._init_clients()
        
        settings = self.cache.get_guild_settings(guild_id)
        if settings:
            return settings
        
        settings = await self.db.get_guild_settings(guild_id)
        if settings:
            self.cache.set_guild_settings(guild_id, settings)
            return settings
        
        return DEFAULT_GUILD_SETTINGS.copy()
    
    async def build_system_prompt(self, guild_id: int) -> str:
        """Build UNIQUE system prompt with personality"""
        settings = await self.get_guild_settings(guild_id)
        
        personality_key = settings.get("personality", "fun")
        personality_prompt = SYSTEM_PROMPTS.get(personality_key, SYSTEM_PROMPTS["fun"])
        
        custom_instructions = settings.get("custom_instructions", "")
        
        system_prompt = BASE_SYSTEM_PROMPT.format(
            personality=personality_prompt,
            custom_instructions=f"\n\n**Server-Specific Instructions:**\n{custom_instructions}" if custom_instructions else ""
        )
        
        return system_prompt
    
    # Token limits for Groq free tier
    MAX_TOTAL_CHARS = 6000  # ~2,000 tokens (safe for free tier)
    MAX_MESSAGES = 8
    MAX_MESSAGE_LENGTH = 800
    MAX_SYSTEM_PROMPT_CHARS = 1500
    
    async def get_conversation_context(
        self,
        guild_id: int,
        channel_id: int,
        user_id: int,
        max_messages: int = None,
        task_type: TaskType = TaskType.CHAT
    ) -> List[Dict[str, str]]:
        """
        Build conversation context with SMART MODEL SELECTION!
        Returns messages optimized for the specific task type.
        """
        self._init_clients()
        
        if max_messages is None:
            max_messages = self.MAX_MESSAGES
            
        messages = []
        
        # Add system prompt (shortened for token efficiency)
        system_prompt = await self.build_system_prompt(guild_id)
        system_prompt = system_prompt[:self.MAX_SYSTEM_PROMPT_CHARS]
        if len(system_prompt) == self.MAX_SYSTEM_PROMPT_CHARS:
            system_prompt += "... [truncated]"
        messages.append({"role": "system", "content": system_prompt})
        
        # Get relevant memories (if enabled) - from PERSISTENT storage!
        settings = await self.get_guild_settings(guild_id)
        if settings.get("memory_enabled", True):
            memories = await self._get_relevant_memories(guild_id, user_id, limit=5)
            if memories:
                memory_context = self._format_memories(memories)
                if len(memory_context) > 1000:
                    memory_context = memory_context[:1000] + "... [truncated]"
                messages.append({
                    "role": "system",
                    "content": f"**What you remember about this server/user:**\n{memory_context}"
                })
        
        # Get conversation history - FROM PERSISTENT STORAGE (survives restarts!)
        conv_history = self.cache.get_conversation(channel_id)
        
        if not conv_history:
            # Try database as fallback
            conv_history = await self.db.get_conversation_history(
                guild_id, channel_id, limit=max_messages
            )
            if conv_history:
                self.cache.set_conversation(channel_id, conv_history)
        
        if conv_history:
            recent_messages = conv_history[-max_messages:]
            for msg in recent_messages:
                content = msg.get("content", "")
                if len(content) > self.MAX_MESSAGE_LENGTH:
                    content = content[:self.MAX_MESSAGE_LENGTH] + "... [truncated]"
                messages.append({
                    "role": msg.get("role", "user"),
                    "content": content
                })
        
        # Ensure payload limit
        messages = self._ensure_payload_limit(messages)
        
        return messages
    
    def _ensure_payload_limit(self, messages: List[Dict], max_chars: int = None) -> List[Dict]:
        """Ensure total payload doesn't exceed Groq's limit"""
        if max_chars is None:
            max_chars = self.MAX_TOTAL_CHARS
        
        total_size = sum(len(m.get("content", "")) for m in messages)
        
        if total_size <= max_chars:
            return messages
        
        logger.warning(f"⚠️ Payload too large ({total_size} chars), trimming...")
        
        system_msgs = [m for m in messages if m.get("role") == "system"]
        other_msgs = [m for m in messages if m.get("role") != "system"]
        
        available_space = max_chars - sum(len(m.get("content", "")) for m in system_msgs)
        
        if available_space <= 0:
            logger.error("❌ System prompts too large, using minimal prompt")
            return [{"role": "system", "content": "You are Ophelia AI, a helpful Discord bot."}]
        
        trimmed_msgs = []
        current_size = 0
        
        for msg in reversed(other_msgs):
            content = msg.get("content", "")
            if current_size + len(content) <= available_space:
                trimmed_msgs.insert(0, msg)
                current_size += len(content)
            else:
                break
        
        final_messages = system_msgs + trimmed_msgs
        logger.info(f"✅ Trimmed payload from {total_size} to {sum(len(m.get('content','')) for m in final_messages)} chars")
        
        return final_messages
    
    async def _get_relevant_memories(
        self,
        guild_id: int,
        user_id: int,
        limit: int = 5
    ) -> List[Dict]:
        """Get relevant memories - checks persistent storage first!"""
        try:
            # Check cache/persistent storage first
            cached = self.cache.get_memories(guild_id, user_id)
            if cached:
                return cached
            
            # Fetch from database
            memories = await self.db.get_memories(guild_id, user_id, limit=limit)
            
            if memories:
                self.cache.set_memories(guild_id, user_id, memories)
            
            return memories or []
        except Exception as e:
            logger.debug(f"Memory fetch skipped: {e}")
            return []
    
    def _format_memories(self, memories: List[Dict]) -> str:
        """Format memories compactly"""
        formatted = []
        for mem in memories[:5]:
            content = mem.get("content", "")[:150]
            mem_type = mem.get("memory_type", "general")
            formatted.append(f"- [{mem_type}] {content}")
        
        return "\n".join(formatted) if formatted else ""
    
    async def generate_response(
        self,
        guild_id: int,
        channel_id: int,
        user_id: int,
        user_message: str,
        username: str,
        force_task_type: TaskType = None
    ) -> str:
        """
        Generate AI response with MULTI-MODEL SMART ROUTING!
        Automatically selects best model based on message type.
        """
        self._init_clients()
        
        try:
            # Save user message to PERSISTENT memory
            await self._save_message(guild_id, channel_id, user_id, "user", user_message)
            
            # Detect task type or use forced type
            if force_task_type:
                task_type = force_task_type
            else:
                task_type = self.groq.detect_task_type(user_message)
            
            # Build context
            messages = await self.get_conversation_context(
                guild_id, channel_id, user_id, task_type=task_type
            )
            
            # Add current user message
            messages.append({"role": "user", "content": user_message})
            
            # Get settings
            settings = await self.get_guild_settings(guild_id)
            
            # Get model config for this task type
            requested_max_tokens = min(settings.get("max_tokens", 1024), 1024)
            
            # Generate response with SMART MODEL SELECTION! 🎯
            response_parts = []
            async for chunk in self.groq.chat_completion_stream(
                messages=messages,
                temperature=settings.get("temperature", 1.02),
                max_tokens=requested_max_tokens,
                top_p=settings.get("top_p", 1.0),
                task_type=task_type  # THIS IS THE MAGIC! ✨
            ):
                response_parts.append(chunk)
            
            full_response = "".join(response_parts)
            
            # Save assistant response to PERSISTENT memory
            await self._save_message(guild_id, channel_id, user_id, "assistant", full_response)
            
            # Extract and save important info as memories
            await self._extract_and_save_memories(
                guild_id, user_id, user_message, full_response
            )
            
            return full_response
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            error_msg = str(e)
            
            # Ophelia-style error messages
            if "413" in error_msg or "too large" in error_msg.lower():
                return "Arre yaar, itna lamba message mat bhojo! 🤯 Meri processing power limit hai 😅 Thoda short karke do?"
            elif "403" in error_msg or "permission" in error_msg.lower():
                return "Bhai permission issue aa gaya 😐 Admin se puch ke dekh, mujhe block toh nahi kiya na? 🥺"
            elif "rate" in error_msg.lower() or "limit" in error_msg.lower():
                return "Thoda ruk ja bhai! ⏳ Bahut zyada requests aa rhi hain. 2-3 sec baar try kar! ⚡"
            elif "timeout" in error_msg.lower():
                return "Server thoda slow hai abhi 🐌 Dobara try kar? Quick hoga!"
            else:
                return f"Kuch technical issue aa gaya 😅 `{error_msg[:80]}` - Try again bro!"
    
    async def generate_response_stream(
        self,
        guild_id: int,
        channel_id: int,
        user_id: int,
        user_message: str,
        username: str
    ):
        """Generate streaming response with multi-model support"""
        self._init_clients()
        
        try:
            await self._save_message(guild_id, channel_id, user_id, "user", user_message)
            
            # Auto-detect task type
            task_type = self.groq.detect_task_type(user_message)
            
            messages = await self.get_conversation_context(
                guild_id, channel_id, user_id, task_type=task_type
            )
            messages.append({"role": "user", "content": user_message})
            
            settings = await self.get_guild_settings(guild_id)
            requested_max_tokens = min(settings.get("max_tokens", 1024), 1024)
            
            full_response = ""
            
            async for chunk in self.groq.chat_completion_stream(
                messages=messages,
                temperature=settings.get("temperature", 1.02),
                max_tokens=requested_max_tokens,
                top_p=settings.get("top_p", 1.0),
                task_type=task_type
            ):
                full_response += chunk
                yield chunk
            
            await self._save_message(guild_id, channel_id, user_id, "assistant", full_response)
            await self._extract_and_save_memories(guild_id, user_id, user_message, full_response)
            
        except Exception as e:
            logger.error(f"Error in stream generation: {e}")
            yield f"😅 Yaar kuch gadbad ho gayi: {str(e)[:60]}... Dobara try karo bro!"
    
    async def _save_message(
        self,
        guild_id: int,
        channel_id: int,
        user_id: int,
        role: str,
        content: str
    ):
        """Save message to BOTH cache AND disk (persistent!)"""
        self._init_clients()
        
        # Update cache (this also saves to disk!)
        self.cache.add_to_conversation(channel_id, {"role": role, "content": content})
        
        # Also save to database (async, don't wait - may fail gracefully)
        asyncio.create_task(
            self.db.save_message(guild_id, channel_id, user_id, role, content)
        )
    
    async def _extract_and_save_memories(
        self,
        guild_id: int,
        user_id: int,
        user_msg: str,
        ai_response: str
    ):
        """Extract and save important info as long-term memories"""
        try:
            memories_to_save = []
            
            # User preferences
            preference_keywords = ["i like", "i love", "i hate", "mujhe pasand", "mujhe pasand nahi"]
            msg_lower = user_msg.lower()
            for keyword in preference_keywords:
                if keyword in msg_lower:
                    memories_to_save.append({
                        "type": "user_preference",
                        "content": user_msg[:300],
                        "importance": 0.9
                    })
                    break
            
            # Personal info
            personal_keywords = ["mera naam", "my name is", "born on", "birthday", "live in"]
            for keyword in personal_keywords:
                if keyword in msg_lower:
                    memories_to_save.append({
                        "type": "user_info",
                        "content": user_msg[:300],
                        "importance": 1.0
                    })
                    break
            
            # Save to both database AND persistent storage
            for mem in memories_to_save:
                await self.db.save_memory(
                    guild_id=guild_id,
                    user_id=user_id,
                    memory_type=mem["type"],
                    content=mem["content"],
                    importance=mem["importance"]
                )
                
                # Also update cache (which saves to disk!)
                existing = self.cache.get_memories(guild_id, user_id) or []
                existing.append(mem)
                self.cache.set_memories(guild_id, user_id, existing)
            
            # Invalidate memory cache for refresh
            self.cache.set_memories(guild_id, user_id, [])
            
        except Exception as e:
            logger.debug(f"Memory extraction skipped: {e}")


# Global instance
ai_handler: Optional[AIHandler] = None


def init_ai_handler() -> AIHandler:
    """Initialize global AI handler"""
    global ai_handler
    ai_handler = AIHandler()
    return ai_handler


def get_ai_handler() -> AIHandler:
    """Get global AI handler instance"""
    if ai_handler is None:
        raise RuntimeError("AI handler not initialized! Call init_ai_handler() first.")
    return ai_handler


import asyncio
