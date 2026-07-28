"""
AI Response Handler - SUPER SMART UPGRADE v3.0
🧠 Features:
- User Recognition (Knows WHO is talking!)
- User Profiling (Remembers preferences)
- Context Awareness (Follows conversation flow)
- Emotional Intelligence (Reads mood)
- Multi-model smart routing
- Persistent memory integration
"""
import logging
import re
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
    SUPER SMART AI Handler with:
    ✅ User Recognition (knows who's talking!)
    ✅ User Profiling (remembers each user)
    ✅ Context Awareness (follows flow)
    ✅ Emotional Intelligence (reads mood)
    ✅ Multi-model smart routing
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
    
    # ==================== USER RECOGNITION SYSTEM 🧠 ====================
    
    def _get_user_profile(self, user_id: int, username: str, display_name: str) -> Dict[str, Any]:
        """
        Get or create user profile - THIS IS THE MAGIC!
        Ophelia REMEMBERS who you are!
        """
        self._init_clients()
        
        # Try to get existing profile from cache/disk
        profile = self.cache.get_user_context(user_id)
        
        if not profile:
            # Create new profile for first-time users!
            profile = {
                "user_id": user_id,
                "username": username,
                "display_name": display_name,
                "first_seen": datetime.now().isoformat(),
                "message_count": 0,
                "preferences": {},
                "personality_notes": [],
                "mood_history": [],
                "last_interactions": [],
                "relationship_level": "new",  # new, casual, friend, bestie
                "nicknames_given": [],  # Names Ophelia calls this user
                "topics_discussed": [],
                "inside_jokes": []  # Shared jokes/moments
            }
            logger.info(f"🆕 New user profile created for {display_name} ({user_id})")
        else:
            # Update existing profile
            profile["username"] = username
            profile["display_name"] = display_name
            profile["message_count"] = profile.get("message_count", 0) + 1
            
            # Auto-upgrade relationship based on message count
            msg_count = profile["message_count"]
            if msg_count > 100 and profile["relationship_level"] != "bestie":
                profile["relationship_level"] = "bestie"
            elif msg_count > 30 and profile["relationship_level"] == "new":
                profile["relationship_level"] = "casual"
            elif msg_count > 60 and profile["relationship_level"] == "casual":
                profile["relationship_level"] = "friend"
        
        # Save updated profile
        self.cache.set_user_context(user_id, profile)
        
        return profile
    
    def _detect_mood(self, message: str) -> str:
        """
        Detect user's mood from message - EMOTIONAL INTELLIGENCE!
        Returns: happy, sad, angry, excited, bored, confused, neutral, sarcastic
        """
        msg_lower = message.lower()
        
        # Happy indicators
        happy_words = ["😂", "😁", "😄", "haha", "lol", "lmao", "nice", "great", "amazing", 
                      "love", "best", "fire", "lit", "awesome", "happy", "excited", "yay",
                      "❤️", "💕", "💖", "🔥", "✨", "🎉"]
        if any(word in msg_lower for word in happy_words):
            return "happy"
        
        # Sad indicators  
        sad_words = ["😢", "😞", "😔", "sad", "depressed", "cry", "crying", "hurt",
                    "pain", "alone", "lonely", "miss", "gone", "leave", "bye 😢"]
        if any(word in msg_lower for word in sad_words):
            return "sad"
        
        # Angry indicators
        angry_words = ["😡", "😠", "angry", "mad", "hate", "stupid", "dumb", "idiot",
                      "annoying", "frustrated", "wtf", "damn", "hell", "freaking"]
        if any(word in msg_lower for word in angry_words):
            return "angry"
        
        # Excited indicators
        excited_words = ["!!!", "???", "omg", "oh my god", "wow", "can't believe",
                        "finally", "let's go", "yesss", "yessss", "omggg"]
        if any(word in msg_lower for word in excited_words):
            return "excited"
        
        # Bored indicators
        bored_words = ["bored", "boring", "nothing to do", "meh", "whatever", "ok",
                      "fine", "k", "hmm", "sigh", "ugh"]
        if any(word in msg_lower for word in bored_words):
            return "bored"
        
        # Confused indicators
        confused_words = ["?", "what", "how", "why", "don't understand", "confused",
                        "explain", "help", "idk", "i don't know", "kaise", "kyun"]
        if any(word in msg_lower for word in confused_words):
            return "confused"
        
        # Sarcastic indicators (tricky!)
        sarcastic_patterns = [r"oh really", r"wow.*so.*interesting", r"great.*job",
                            r"thanks.*a lot", r"brilliant", r"sure.*jan", r"ha.*ha"]
        if any(re.search(pattern, msg_lower) for pattern in sarcastic_patterns):
            return "sarcastic"
        
        return "neutral"
    
    def _get_mood_response_style(self, mood: str) -> Dict[str, str]:
        """Get response style based on detected mood"""
        styles = {
            "happy": {"emoji": "😊", "tone": "match their energy!", "style": "enthusiastic"},
            "sad": {"emoji": "🤗", "tone": "be supportive and caring", "style": "comforting"},
            "angry": {"emoji": "😌", "tone": "stay calm, don't escalate", "style": "calming"},
            "excited": {"emoji": "🎉", "tone": "match excitement!", "style": "energetic"},
            "bored": {"emoji": "⚡", "tone": "suggest something fun", "style": "engaging"},
            "confused": {"emoji": "💡", "tone": "explain clearly, be helpful", "style": "helpful"},
            "sarcastic": {"emoji": "😏", "tone": "play along with sarcasm", "style": "witty"},
            "neutral": {"emoji": "✨", "tone": "normal friendly chat", "style": "casual"}
        }
        return styles.get(mood, styles["neutral"])
    
    def _format_user_context_for_ai(self, profile: Dict, mood: str) -> str:
        """
        Format user info for AI context injection.
        THIS IS WHAT MAKES OPHELIA KNOW WHO YOU ARE!
        """
        relationship = profile.get("relationship_level", "new")
        msg_count = profile.get("message_count", 0)
        display_name = profile.get("display_name", "Unknown")
        topics = profile.get("topics_discussed", [])[-5:]  # Last 5 topics
        nicknames = profile.get("nicknames_given", [])
        
        # Relationship-based greeting style
        relationship_styles = {
            "new": f"{display_name} is a NEW user - be welcoming but not overly familiar!",
            "casual": f"You know {display_name} casually - friendly but respectful!",
            "friend": f"{display_name} is your FRIEND - can be more personal and fun!",
            "bestie": f"{display_name} is your BESTIE - inside jokes, teasing, maximum personality!"
        }
        
        context = f"""
**👤 USER INFO (You know who this is!):**
- Name: {display_name}
- Messages from them: {msg_count}
- Relationship: {relationship} → {relationship_styles.get(relationship, '')}
- Current Mood: {mood} → Respond accordingly!

**📝 What you know about {display_name}:**
"""
        
        if topics:
            context += f"- Topics they like: {', '.join(topics)}\n"
        if nicknames:
            context += f"- You call them: {nicknames[-1]}\n"
        
        # Add recent interaction summary
        last_msgs = profile.get("last_interactions", [])[-3:]
        if last_msgs:
            context += "\n**Recent convos:**\n"
            for interaction in last_msgs:
                context += f"- {interaction}\n"
        
        return context
    
    async def build_system_prompt(self, guild_id: int, user_profile: Dict = None, mood: str = "neutral") -> str:
        """Build UNIQUE system prompt with personality + USER CONTEXT!"""
        settings = await self.get_guild_settings(guild_id)
        
        personality_key = settings.get("personality", "fun")
        personality_prompt = SYSTEM_PROMPTS.get(personality_key, SYSTEM_PROMPTS["fun"])
        
        custom_instructions = settings.get("custom_instructions", "")
        
        # Build user-aware system prompt
        system_prompt = BASE_SYSTEM_PROMPT.format(
            personality=personality_prompt,
            custom_instructions=f"\n\n**Server-Specific Instructions:**\n{custom_instructions}" if custom_instructions else ""
        )
        
        # ADD USER CONTEXT IF AVAILABLE - THIS IS THE SECRET SAUCE!
        if user_profile:
            user_context = self._format_user_context_for_ai(user_profile, mood)
            mood_style = self._get_mood_response_style(mood)
            
            system_prompt += f"""

**🧠 CURRENT USER CONTEXT (CRITICAL - Use This!):**
{user_context}

**😊 MOOD RESPONSE GUIDE:**
- User seems {mood} → {mood_style['emoji']} {mood_style['tone']}
- Style: {mood_style['style']}

**⚠️ IMPORTANT RULES FOR THIS USER:**
1. Remember their name - USE IT naturally in responses!
2. Reference past conversations if relevant ("Pehle bola tha na...")
3. Match their energy level
4. If bestie/friend level - can tease, use inside jokes
5. If new user - be welcoming, don't assume familiarity
"""
        
        return system_prompt
    
    # Token limits for Groq free tier
    MAX_TOTAL_CHARS = 6000  # ~2,000 tokens (safe for free tier)
    MAX_MESSAGES = 8
    MAX_MESSAGE_LENGTH = 800
    MAX_SYSTEM_PROMPT_CHARS = 1800  # Increased slightly for user context
    
    # Channel Context Settings
    MAX_CHANNEL_CONTEXT_MSGS = 50  # Last 50 messages from channel
    CHANNEL_CONTEXT_KEYWORDS = ["kya hua", "kya chal rha", "what happened", "context", 
                                "kon sahi", "who won", "fight", "ladai", "argument",
                                "discussion", "baat", "recent", "pichle msgs", "summary",
                                "batao kya hua", "update do", "kya ho rha", "tell me"]
    
    def store_channel_message(
        self,
        channel_id: int,
        author_name: str,
        content: str,
        is_bot: bool = False,
        timestamp: str = None
    ):
        """
        Store channel messages for CONTEXT AWARENESS!
        This lets Ophelia know what's happening in the server!
        """
        self._init_clients()
        
        if not timestamp:
            timestamp = datetime.now().isoformat()
        
        # Get existing channel history or create new
        cache_key = f"channel_history:{channel_id}"
        history = self.cache.get_user_context(channel_id)  # Reusing user_context for channel
        
        if not history:
            history = {
                "messages": [],
                "participants": set(),
                "topics": [],
                "conflict_detected": False
            }
        
        # Add new message
        msg_entry = {
            "author": author_name,
            "content": content[:200],  # Truncate long messages
            "is_bot": is_bot,
            "timestamp": timestamp
        }
        
        if isinstance(history, dict):
            history["messages"].append(msg_entry)
            
            # Keep only last MAX_CHANNEL_CONTEXT_MSGS messages
            if len(history["messages"]) > self.MAX_CHANNEL_CONTEXT_MSGS:
                history["messages"] = history["messages"][-self.MAX_CHANNEL_CONTEXT_MSGS:]
            
            # Track participants
            if not is_bot:
                history.setdefault("participants", set()).add(author_name)
            
            # Detect conflicts/fights automatically
            conflict_words = ["fight", "ladai", "stupid", "idiot", "hate", "shut up", 
                            "mad", "wrong", "sahi nahi", "galat hai", "😡", "😠"]
            if any(word in content.lower() for word in conflict_words):
                history["conflict_detected"] = True
            
            # Save to cache (persists to disk!)
            self.cache.set_user_context(channel_id, history)
    
    def get_channel_context_summary(self, channel_id: int, query: str = "") -> Optional[str]:
        """
        Get summary of what's happening in the channel.
        Returns formatted context string or None if no context available.
        """
        self._init_clients()
        
        cache_key = f"channel_history:{channel_id}"
        history = self.cache.get_user_context(channel_id)
        
        if not history or not isinstance(history, dict):
            return None
        
        messages = history.get("messages", [])
        
        if len(messages) < 5:  # Not enough context
            return None
        
        # Build context summary
        participants = list(history.get("participants", set()))[-10:]  # Last 10 participants
        conflict_detected = history.get("conflict_detected", False)
        
        # Get last 20 messages for detailed context
        recent_msgs = messages[-20:]
        
        summary = f"""
**📺 CHANNEL CONTEXT (What's been happening here):**

**👥 Active Participants:** {', '.join(participants[:8])}
**💬 Recent Messages ({len(recent_msgs)} of {len(messages)} total):**

"""
        
        # Format recent messages
        for msg in recent_msgs:
            prefix = "🤖" if msg.get("is_bot") else "👤"
            time_short = msg.get("timestamp", "")[11:16] if msg.get("timestamp") else ""
            summary += f"{time_short} {prefix} **{msg['author']}:** {msg['content']}\n"
        
        if conflict_detected:
            summary += "\n⚠️ **Note:** Some conflict/heated discussion detected recently!"
        
        return summary
    
    async def get_conversation_context(
        self,
        guild_id: int,
        channel_id: int,
        user_id: int,
        username: str = "Unknown",
        display_name: str = "Unknown",
        max_messages: int = None,
        task_type: TaskType = TaskType.CHAT,
        user_query: str = ""  # NEW: User's message to detect context requests!
    ) -> List[Dict[str, str]]:
        """
        Build conversation context with FULL AWARENESS!
        - User Recognition 👤
- Channel Context 📺
- Emotional Intelligence 😊
"""
        self._init_clients()
        
        if max_messages is None:
            max_messages = self.MAX_MESSAGES
            
        messages = []
        
        # Get/Update User Profile - USER RECOGNITION! 👤
        user_profile = self._get_user_profile(user_id, username, display_name)
        
        # Detect Mood - EMOTIONAL INTELLIGENCE! 😊
        # We'll detect mood from the latest message later
        
        # Add system prompt WITH USER CONTEXT
        system_prompt = await self.build_system_prompt(guild_id, user_profile, "neutral")
        system_prompt = system_prompt[:self.MAX_SYSTEM_PROMPT_CHARS]
        if len(system_prompt) == self.MAX_SYSTEM_PROMPT_CHARS:
            system_prompt += "... [truncated]"
        messages.append({"role": "system", "content": system_prompt})
        
        # 🆕 CHANNEL CONTEXT - Check if user wants to know about recent chat!
        should_include_channel_context = (
            user_query and 
            any(keyword in user_query.lower() for keyword in self.CHANNEL_CONTEXT_KEYWORDS)
        )
        
        if should_include_channel_context:
            channel_context = self.get_channel_context_summary(channel_id, user_query)
            if channel_context:
                messages.append({
                    "role": "system", 
                    "content": channel_context[:1500]  # Limit size
                })
                logger.info(f"📺 Included channel context for query: {user_query[:30]}...")
        
        # Get relevant memories (if enabled) - from PERSISTENT storage!
        settings = await self.get_guild_settings(guild_id)
        if settings.get("memory_enabled", True):
            memories = await self._get_relevant_memories(guild_id, user_id, limit=5)
            if memories:
                memory_context = self._format_memories(memories)
                if len(memory_context) > 800:
                    memory_context = memory_context[:800] + "... [truncated]"
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
            return [{"role": "system", "content": "You are Ophelia AI, a helpful Discord bot with personality."}]
        
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
        username: str = "Unknown",
        display_name: str = "Unknown",
        force_task_type: TaskType = None
    ) -> str:
        """
        Generate AI response with FULL USER AWARENESS!
        Now Ophelia knows WHO is talking and HOW they feel!
        """
        self._init_clients()
        
        try:
            # Get/Update User Profile
            user_profile = self._get_user_profile(user_id, username, display_name)
            
            # Detect Mood - EMOTIONAL INTELLIGENCE! 😊
            current_mood = self._detect_mood(user_message)
            logger.info(f"😊 Detected mood for {display_name}: {current_mood}")
            
            # Update mood history in profile
            user_profile.setdefault("mood_history", []).append({
                "mood": current_mood,
                "timestamp": datetime.now().isoformat(),
                "message_preview": user_message[:50]
            })
            # Keep only last 20 mood entries
            user_profile["mood_history"] = user_profile["mood_history"][-20:]
            
            # Save user message to PERSISTENT memory
            await self._save_message(guild_id, channel_id, user_id, "user", user_message)
            
            # Update last interactions
            user_profile.setdefault("last_interactions", []).append(
                f"[{datetime.now().strftime('%H:%M')}] {display_name}: {user_message[:50]}"
            )
            user_profile["last_interactions"] = user_profile["last_interactions"][-10:]
            
            # Extract topics discussed
            topics = self._extract_topics(user_message)
            for topic in topics:
                if topic not in user_profile.get("topics_discussed", []):
                    user_profile.setdefault("topics_discussed", []).append(topic)
            
            # Save updated profile
            self.cache.set_user_context(user_id, user_profile)
            
            # Detect task type or use forced type
            if force_task_type:
                task_type = force_task_type
            else:
                task_type = self.groq.detect_task_type(user_message)
            
            # Build context WITH USER PROFILE, MOOD & CHANNEL CONTEXT!
            messages = await self.get_conversation_context(
                guild_id, channel_id, user_id, username, display_name, 
                task_type=task_type,
                user_query=user_message  # 🆕 Pass query for channel context detection!
            )
            
            # Override the system prompt to include current mood
            if messages and messages[0].get("role") == "system":
                mood_aware_prompt = await self.build_system_prompt(guild_id, user_profile, current_mood)
                mood_aware_prompt = mood_aware_prompt[:self.MAX_SYSTEM_PROMPT_CHARS]
                messages[0]["content"] = mood_aware_prompt
            
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
                task_type=task_type
            ):
                response_parts.append(chunk)
            
            full_response = "".join(response_parts)
            
            # Save assistant response to PERSISTENT memory
            await self._save_message(guild_id, channel_id, user_id, "assistant", full_response)
            
            # Update interactions with bot response
            user_profile["last_interactions"].append(
                f"[{datetime.now().strftime('%H:%M')}] Ophelia: {full_response[:50]}"
            )
            user_profile["last_interactions"] = user_profile["last_interactions"][-10:]
            self.cache.set_user_context(user_id, user_profile)
            
            # Extract and save important info as memories
            await self._extract_and_save_memories(
                guild_id, user_id, user_message, full_response
            )
            
            logger.info(f"💬 Response for {display_name} | Mood: {current_mood} | Length: {len(full_response)}")
            
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
        username: str = "Unknown",
        display_name: str = "Unknown"
    ):
        """Generate streaming response with user awareness"""
        self._init_clients()
        
        try:
            # Get user profile
            user_profile = self._get_user_profile(user_id, username, display_name)
            
            # Detect mood
            current_mood = self._detect_mood(user_message)
            
            await self._save_message(guild_id, channel_id, user_id, "user", user_message)
            
            # Auto-detect task type
            task_type = self.groq.detect_task_type(user_message)
            
            messages = await self.get_conversation_context(
                guild_id, channel_id, user_id, username, display_name, task_type=task_type
            )
            
            # Add mood awareness
            if messages and messages[0].get("role") == "system":
                mood_aware_prompt = await self.build_system_prompt(guild_id, user_profile, current_mood)
                messages[0]["content"] = mood_aware_prompt[:self.MAX_SYSTEM_PROMPT_CHARS]
            
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
    
    def _extract_topics(self, message: str) -> List[str]:
        """Extract topics from message for user profiling"""
        common_topics = [
            "gaming", "code", "music", "movie", "anime", "meme", "study", "work",
            "love", "food", "sleep", "cricket", "football", "crypto", "stock",
            "python", "javascript", "discord", "youtube", "instagram"
        ]
        
        msg_lower = message.lower()
        found_topics = []
        
        for topic in common_topics:
            if topic in msg_lower:
                found_topics.append(topic)
        
        return found_topics[:3]  # Max 3 topics per message
    
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
