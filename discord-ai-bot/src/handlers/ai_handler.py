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
    
    async def get_conversation_context(
        self,
        guild_id: int,
        channel_id: int,
        user_id: int,
        max_messages: int = 30
    ) -> List[Dict[str, str]]:
        """
        Build conversation context including recent messages and relevant memories.
        Returns list of message dicts for the API.
        """
        self._init_clients()
        
        messages = []
        
        # Add system prompt
        system_prompt = await self.build_system_prompt(guild_id)
        messages.append({"role": "system", "content": system_prompt})
        
        # Get relevant memories if enabled
        settings = await self.get_guild_settings(guild_id)
        if settings.get("memory_enabled", True):
            memories = await self._get_relevant_memories(guild_id, user_id)
            if memories:
                memory_context = self._format_memories(memories)
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
            # Add conversation history (respecting max_tokens roughly)
            messages.extend(conv_history[-max_messages:])
        
        return messages
    
    async def _get_relevant_memories(
        self,
        guild_id: int,
        user_id: int,
        limit: int = 10
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
        """Format memories for inclusion in prompt"""
        formatted = []
        for mem in memories[:10]:  # Limit to avoid token overflow
            content = mem.get("content", "")[:200]  # Truncate long memories
            mem_type = mem.get("memory_type", "general")
            formatted.append(f"- [{mem_type}] {content}")
        
        return "\n".join(formatted) if formatted else "No significant memories yet."
    
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
