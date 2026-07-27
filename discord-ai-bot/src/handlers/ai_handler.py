"""
AI Response Handler
Manages conversation context, memory integration, and response generation
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
from src.utils.groq_client import get_groq_client

logger = logging.getLogger("AIHandler")


class AIHandler:
    """Handles AI response generation with memory and context management"""
    
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
        
        # Try cache first
        settings = self.cache.get_guild_settings(guild_id)
        if settings:
            return settings
        
        # Fallback to database
        settings = await self.db.get_guild_settings(guild_id)
        if settings:
            self.cache.set_guild_settings(guild_id, settings)
            return settings
        
        # Return default settings
        return DEFAULT_GUILD_SETTINGS.copy()
    
    async def build_system_prompt(self, guild_id: int) -> str:
        """Build system prompt with personality and custom instructions"""
        settings = await self.get_guild_settings(guild_id)
        
        personality_key = settings.get("personality", "fun")
        personality_prompt = SYSTEM_PROMPTS.get(personality_key, SYSTEM_PROMPTS["fun"])
        
        custom_instructions = settings.get("custom_instructions", "")
        
        system_prompt = BASE_SYSTEM_PROMPT.format(
            personality=personality_prompt,
            custom_instructions=f"\n\n**Server-Specific Instructions:**\n{custom_instructions}" if custom_instructions else ""
        )
        
        return system_prompt
    
    # Groq API limits - stay well under the max!
    MAX_TOTAL_CHARS = 80000  # ~20k tokens (safe limit)
    MAX_MESSAGES = 15  # Reduced from 30 to prevent 413 errors
    MAX_MESSAGE_LENGTH = 2000  # Truncate individual long messages
    
    async def get_conversation_context(
        self,
        guild_id: int,
        channel_id: int,
        user_id: int,
        max_messages: int = None  # Use default from class
    ) -> List[Dict[str, str]]:
        """
        Build conversation context including recent messages and relevant memories.
        Includes smart truncation to prevent 413 (Request too large) errors.
        Returns list of message dicts for the API.
        """
        self._init_clients()
        
        if max_messages is None:
            max_messages = self.MAX_MESSAGES
            
        messages = []
        
        # Add system prompt (with length limit!)
        system_prompt = await self.build_system_prompt(guild_id)
        system_prompt = system_prompt[:self.MAX_MESSAGE_LENGTH]  # Truncate if too long
        messages.append({"role": "system", "content": system_prompt})
        
        # Get relevant memories if enabled (but limit them!)
        settings = await self.get_guild_settings(guild_id)
        if settings.get("memory_enabled", True):
            memories = await self._get_relevant_memories(guild_id, user_id, limit=5)  # Reduced from 10
            if memories:
                memory_context = self._format_memories(memories)
                # Limit memory context size
                if len(memory_context) > 1000:
                    memory_context = memory_context[:1000] + "... [truncated]"
                messages.append({
                    "role": "system",
                    "content": f"**What you remember about this server/user:**\n{memory_context}"
                })
        
        # Get recent conversation history
        conv_history = self.cache.get_conversation(channel_id)
        
        if not conv_history:
            # Try loading from database
            conv_history = await self.db.get_conversation_history(
                guild_id, channel_id, limit=max_messages
            )
            if conv_history:
                self.cache.set_conversation(channel_id, conv_history)
        
        if conv_history:
            # Take last N messages and truncate each if needed
            recent_messages = conv_history[-max_messages:]
            for msg in recent_messages:
                content = msg.get("content", "")
                # Truncate long messages
                if len(content) > self.MAX_MESSAGE_LENGTH:
                    content = content[:self.MAX_MESSAGE_LENGTH] + "... [truncated]"
                messages.append({
                    "role": msg.get("role", "user"),
                    "content": content
                })
        
        # FINAL SAFETY CHECK: Ensure total payload isn't too large
        messages = self._ensure_payload_limit(messages)
        
        return messages
    
    def _ensure_payload_limit(self, messages: List[Dict], max_chars: int = None) -> List[Dict]:
        """
        Ensure total message payload doesn't exceed Groq's limit.
        Aggressively trims if needed to prevent 413 errors.
        """
        if max_chars is None:
            max_chars = self.MAX_TOTAL_CHARS
        
        # Calculate current size
        total_size = sum(len(m.get("content", "")) for m in messages)
        
        # If within limit, return as-is
        if total_size <= max_chars:
            return messages
        
        # Need to trim! Keep system prompt, trim history
        logger.warning(f"⚠️ Payload too large ({total_size} chars), trimming...")
        
        system_msgs = [m for m in messages if m.get("role") == "system"]
        other_msgs = [m for m in messages if m.get("role") != "system"]
        
        available_space = max_chars - sum(len(m.get("content", "")) for m in system_msgs)
        
        if available_space <= 0:
            # Even system prompts are too big, truncate them
            logger.error("❌ System prompts too large, aggressive truncation needed!")
            return [{"role": "system", "content": "You are Ophelia AI, a helpful Discord bot."}]
        
        # Trim from the end (keep most recent)
        trimmed_msgs = []
        current_size = 0
        
        # Reverse to process oldest first, keep newest
        for msg in reversed(other_msgs):
            content = msg.get("content", "")
            if current_size + len(content) <= available_space:
                trimmed_msgs.insert(0, msg)  # Insert at beginning to maintain order
                current_size += len(content)
            else:
                break  # Stop when we'd exceed limit
        
        final_messages = system_msgs + trimmed_msgs
        logger.info(f"✅ Trimmed payload from {total_size} to {sum(len(m.get('content','')) for m in final_messages)} chars")
        
        return final_messages
    
    async def _get_relevant_memories(
        self,
        guild_id: int,
        user_id: int,
        limit: int = 5  # Reduced from 10 to save space
    ) -> List[Dict]:
        """Get relevant memories for context"""
        try:
            # Try cache first
            cached = self.cache.get_memories(guild_id, user_id)
            if cached:
                return cached
            
            # Fetch from database
            memories = await self.db.get_memories(guild_id, user_id, limit=limit)
            
            if memories:
                self.cache.set_memories(guild_id, user_id, memories)
            
            return memories or []
        except Exception as e:
            logger.error(f"Error fetching memories: {e}")
            return []
    
    def _format_memories(self, memories: List[Dict]) -> str:
        """Format memories for inclusion in prompt (compact!)"""
        formatted = []
        for mem in memories[:5]:  # Max 5 memories now
            content = mem.get("content", "")[:150]  # Shorter truncation
            mem_type = mem.get("memory_type", "general")
            formatted.append(f"- [{mem_type}] {content}")
        
        return "\n".join(formatted) if formatted else ""
    
    async def generate_response(
        self,
        guild_id: int,
        channel_id: int,
        user_id: int,
        user_message: str,
        username: str
    ) -> str:
        """
        Generate AI response to a user message.
        Handles streaming, memory storage, and error handling.
        """
        self._init_clients()
        
        try:
            # Save user message to history
            await self._save_message(guild_id, channel_id, user_id, "user", user_message)
            
            # Build conversation context
            messages = await self.get_conversation_context(
                guild_id, channel_id, user_id
            )
            
            # Add current user message
            messages.append({
                "role": "user",
                "content": user_message
            })
            
            # Get guild settings for generation parameters
            settings = await self.get_guild_settings(guild_id)
            
            # Generate streaming response
            response_parts = []
            async for chunk in self.groq.chat_completion_stream(
                messages=messages,
                temperature=settings.get("temperature", 1.02),
                max_tokens=settings.get("max_tokens", 32768),
                top_p=settings.get("top_p", 1.0)
            ):
                response_parts.append(chunk)
            
            full_response = "".join(response_parts)
            
            # Save assistant response to history
            await self._save_message(guild_id, channel_id, user_id, "assistant", full_response)
            
            # Extract and save any important information as memories
            await self._extract_and_save_memories(
                guild_id, user_id, user_message, full_response
            )
            
            return full_response
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return f"Arre yaar, kuch technical issue aa gaya 😅 Error: {str(e)[:100]}"
    
    async def generate_response_stream(
        self,
        guild_id: int,
        channel_id: int,
        user_id: int,
        user_message: str,
        username: str
    ):
        """
        Generate streaming AI response.
        Yields chunks for real-time display.
        """
        self._init_clients()
        
        try:
            # Save user message first
            await self._save_message(guild_id, channel_id, user_id, "user", user_message)
            
            # Build context
            messages = await self.get_conversation_context(
                guild_id, channel_id, user_id
            )
            messages.append({"role": "user", "content": user_message})
            
            settings = await self.get_guild_settings(guild_id)
            
            full_response = ""
            
            async for chunk in self.groq.chat_completion_stream(
                messages=messages,
                temperature=settings.get("temperature", 1.02),
                max_tokens=settings.get("max_tokens", 32768),
                top_p=settings.get("top_p", 1.0)
            ):
                full_response += chunk
                yield chunk
            
            # Save complete response
            await self._save_message(guild_id, channel_id, user_id, "assistant", full_response)
            
            # Memory extraction
            await self._extract_and_save_memories(
                guild_id, user_id, user_message, full_response
            )
            
        except Exception as e:
            logger.error(f"Error in stream generation: {e}")
            yield f"😅 Kuch gadbad ho gayi bhai: {str(e)[:100]}"
    
    async def _save_message(
        self,
        guild_id: int,
        channel_id: int,
        user_id: int,
        role: str,
        content: str
    ):
        """Save message to both cache and database"""
        self._init_clients()
        
        # Update cache
        self.cache.add_to_conversation(channel_id, {"role": role, "content": content})
        
        # Save to database (async, don't wait)
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
        """Extract important info from conversations and store as memories"""
        try:
            # Simple heuristic-based memory extraction
            # In production, this could use another LLM call
            
            memories_to_save = []
            
            # Detect user preferences (likes, dislikes)
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
            
            # Detect personal info sharing (name, birthday, etc.)
            personal_keywords = ["mera naam", "my name is", "born on", "birthday", "live in"]
            for keyword in personal_keywords:
                if keyword in msg_lower:
                    memories_to_save.append({
                        "type": "user_info",
                        "content": user_msg[:300],
                        "importance": 1.0
                    })
                    break
            
            # Save detected memories
            for mem in memories_to_save:
                await self.db.save_memory(
                    guild_id=guild_id,
                    user_id=user_id,
                    memory_type=mem["type"],
                    content=mem["content"],
                    importance=mem["importance"]
                )
                
            # Invalidate memory cache for this user
            self.cache.set_memories(guild_id, user_id, [])
            
        except Exception as e:
            logger.debug(f"Memory extraction skipped: {e}")


# Global AI handler instance
ai_handler: Optional[AIHandler] = None


def init_ai_handler() -> AIHandler:
    """Initialize the global AI handler"""
    global ai_handler
    ai_handler = AIHandler()
    return ai_handler


def get_ai_handler() -> AIHandler:
    """Get the global AI handler instance"""
    if ai_handler is None:
        raise RuntimeError("AI handler not initialized! Call init_ai_handler() first.")
    return ai_handler


# Import asyncio here to avoid circular dependency at module level
import asyncio
