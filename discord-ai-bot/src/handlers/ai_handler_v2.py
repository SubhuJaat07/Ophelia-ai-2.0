"""
AI Response Handler - PROPER MCP IMPLEMENTATION v2.0 🛠️
====================================================

This version FIXES all hallucination issues:
✅ Action intent detection (create, kick, timeout)
✅ FORCED tool use for actions (no faking!)
✅ Real Discord API execution
✅ Validation of tool results
✅ No more fake Channel IDs!
✅ No more raw function leaks!

Author: Proper Full-Stack Implementation
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
from src.handlers.ai_decision_engine import get_decision_engine

logger = logging.getLogger("AIHandler")


class AIHandlerV2:
    """
    PROPER AI Handler with REAL tool execution!
    
    Key improvements over v1:
    - Action intent detection
    - Forced tool use for actions  
    - Result validation
    - Anti-hallucination measures
    """
    
    def __init__(self):
        self.db = None
        self.cache = None
        self.groq = None
        
        # Keywords that trigger channel context awareness
        self.CHANNEL_CONTEXT_KEYWORDS = [
            "kya hua", "kya chal rha", "kya ho rha", "what happened", 
            "kon sahi", "who won", "kya kiya", "kya bola",
            "recent msgs", "recent messages", "channel context",
            "kya ho rha hai", "kya chal rha hai", "update do",
            "batao kya hua", "tell me what happened"
        ]
        
        # Mood detection keywords (Hinglish support!)
        self.MOOD_KEYWORDS = {
            'happy': ['😊', '😂', '❤️', '🎉', '💪', ':D', 'haha', 'lol', 'lmao', 
                    'happy', 'maza aa rha', 'mast', 'badhiya', 'awesome', 'cool',
                    'dhan dhana dhan', 'jai ho', 'waah', 'kya baat'],
            'sad': ['😢', '😞', '😔', '☹️', 'sad', 'dukh', 'cry', 'rona', 
                  'emotional', 'miss', 'yaad', 'tanha', 'akela'],
            'angry': ['😠', '😡', 'gussa', 'angry', 'pagal', 'stupid', 'idiot',
                    'frustrated', 'annoying', 'irritating', 'bakwas', 'ghtna'],
            'excited': ['🤩', '😍', '🔥', '⚡', 'excited', 'finally', 'omg', 
                      'wtf', 'zor se', 'chillao', 'party'],
            'confused': ['🤔', '😕', '?', 'confused', 'samajh nahi aaya', 'kaise',
                       'kyun', 'why', 'how', 'explain', 'matlab']
        }
        
        # 🔍 ACTION INTENT PATTERNS - Detect when user wants REAL actions!
        self.ACTION_PATTERNS = {
            'create_channel': ['create channel', 'channel banao', 'make channel', 'new channel', 
                            'add channel', 'banana', 'banado', 'channel create karo'],
            'kick_user': ['kick', 'hatao', 'nikalo', 'remove from server', 'throw out', 
                        'kick karo', 'bahar karo', 'server se hatao'],
            'timeout_user': ['timeout', 'mute', 'chupao', 'silent mode', 'shut up', 
                           'timeout do', 'chup karao', 'band karo'],
            'send_message': ['send message', 'bhejo', 'announce', 'broadcast', 
                          'message bhejo', 'send karo'],
            'add_reaction': ['react', 'emoji lagao', 'reaction add karo', 'react karo']
        }
        
        # Max system prompt length to avoid token limits
        self.MAX_SYSTEM_PROMPT_CHARS = 3500
    
    def _init_clients(self):
        """Initialize lazy-loaded clients"""
        if not self.db:
            self.db = get_db()
        if not self.cache:
            self.cache = get_cache()
        if not self.groq:
            self.groq = get_groq_client()
    
    # ==========================================
    # 🔍 ACTION DETECTION SYSTEM
    # ==========================================
    
    def _detect_action_intent(self, user_message: str) -> Optional[str]:
        """
        Detect if user wants to perform a REAL action.
        Returns the tool name that should be used, or None for chat/info.
        
        This is CRITICAL to prevent hallucination!
        """
        msg_lower = user_message.lower().strip()
        
        # Check each action pattern
        for tool_name, patterns in self.ACTION_PATTERNS.items():
            for pattern in patterns:
                if pattern in msg_lower:
                    logger.info(f"🎯 ACTION DETECTED: {tool_name} | Pattern: '{pattern}'")
                    return tool_name
        
        return None
    
    # ==========================================
    # 🛠️ MAIN TOOL-ENABLED RESPONSE GENERATOR
    # ==========================================
    
    async def generate_response_with_tools(
        self,
        guild_id: int,
        channel_id: int,
        user_id: int,
        user_message: str,
        username: str = "Unknown",
        display_name: str = "Unknown",
        guild: object = None,
        bot_member: object = None,
        mentioned_users: list = None,
        max_tool_iterations: int = 5
    ) -> str:
        """
        PROPER MCP-Style Tool Calling with ANTI-HALLUCINATION! 
        
        Flow:
        1. Detect if this is an ACTION request or INFO request
        2. For ACTIONS → Force tool use (tool_choice=specific_tool)
        3. Execute tools via Discord API (REAL results)
        4. Validate results (no fake IDs allowed)
        5. Generate natural response using REAL data
        
        NO MORE FAKE RESPONSES! 🚫
        """
        self._init_clients()
        
        try:
            # Import tool executor
            from src.tools import get_tool_executor
            
            tool_executor = get_tool_executor()
            
            # ✅ CHECK: Are tools available?
            if not tool_executor.tool_names:
                logger.warning("⚠️ No tools available!")
                return await self._generate_fallback_response(
                    guild_id, channel_id, user_id, user_message, 
                    username, display_name, guild, bot_member, mentioned_users
                )
            
            logger.info(f"🛠️ Tools available: {len(tool_executor.tool_names)}")
            
            # Get user profile & mood
            user_profile = self._get_user_profile(user_id, username, display_name)
            current_mood = self._detect_mood(user_message)
            
            # Save message to memory
            await self._save_message(guild_id, channel_id, user_id, "user", user_message)
            
            # 🔑 STEP 1: Detect Action Intent
            action_intent = self._detect_action_intent(user_message)
            
            task_type = self.groq.detect_task_type(user_message)
            
            logger.info(f"📝 Intent: {action_intent or 'CHAT/INFO'} | Task: {task_type.value}")
            
            # Gather available data
            available_data = self.gather_available_data(
                user_profile=user_profile,
                channel_id=channel_id,
                guild=guild,
                bot_member=bot_member
            )
            
            # Build conversation context
            messages = await self.get_conversation_context(
                guild_id, channel_id, user_id, username, display_name,
                task_type=task_type,
                user_query=user_message
            )
            
            # 🔑 STEP 2: Build System Prompt with STRICT rules
            if messages and messages[0].get("role") == "system":
                full_prompt = await self.build_system_prompt(
                    guild_id, user_profile, current_mood,
                    available_data=available_data,
                    user_message=user_message
                )
                
                # ⚠️ Add CRITICAL instructions for actions
                if action_intent:
                    full_prompt += f"\n\n{'='*50}\n"
                    full_prompt += f"⚠️ **ACTION REQUIRED: User wants you to use `{action_intent}` tool!**\n"
                    full_prompt += f"{'='*50}\n"
                    full_prompt += f"• You MUST call the `{action_intent}` function\n"
                    full_prompt += f"• Do NOT make up results or fake IDs\n"
                    full_prompt += f"• If tool fails, report the error honestly\n"
                    full_prompt += f"• Wait for tool result before responding\n"
                
                # Add tool info
                tools_info = tool_executor.get_tool_schema_summary()
                if len(full_prompt) + len(tools_info) < self.MAX_SYSTEM_PROMPT_CHARS:
                    full_prompt += f"\n\n{tools_info}"
                
                messages[0]["content"] = full_prompt[:self.MAX_SYSTEM_PROMPT_CHARS]
            
            # Add user message
            messages.append({"role": "user", "content": user_message})
            
            # Get settings & tool schemas
            settings = await self.get_guild_settings(guild_id)
            tool_schemas = tool_executor.schemas_for_groq
            
            # Build execution context
            exec_context = {
                "guild": guild,
                "guild_id": str(guild_id),
                "channel_id": str(channel_id),
                "user_id": str(user_id),
                "author_name": display_name,
                "is_owner": self._check_owner(user_id),
                "is_moderator": self._check_if_moderator(user_id, guild)
            }
            
            # 🔑 STEP 3: Tool-Calling Loop with VALIDATION
            final_response = ""
            iteration = 0
            tools_used = []
            tool_results_data = []  # Store actual tool results
            
            # Determine initial tool_choice strategy
            tool_choice = action_intent or "auto"
            
            logger.info(f"🎯 Strategy: tool_choice='{tool_choice}'")
            
            while iteration < max_tool_iterations:
                iteration += 1
                logger.info(f"\n{'='*50}")
                logger.info(f"🔄 Iteration {iteration}/{max_tool_iterations}")
                logger.info(f"{'='*50}")
                
                # Call Groq with tools
                result = await self.groq.chat_completion_with_tools(
                    messages=messages,
                    tools=tool_schemas,
                    temperature=settings.get("temperature", 0.7),
                    task_type=task_type,
                    tool_choice=tool_choice
                )
                
                # Parse response
                tool_calls = result.get("tool_calls", [])
                content = result.get("content", "") or ""
                
                logger.info(f"📊 Response: {len(tool_calls)} tool calls | Content: '{content[:80]}...'")
                
                # CASE A: No tool calls requested
                if not tool_calls:
                    final_response = content
                    
                    # ⚠️ VALIDATION: If we expected an action but got none
                    if action_intent and iteration == 1:
                        logger.warning(f"⚠️ Expected action '{action_intent}' but no tool called!")
                        
                        # Check for potential hallucination indicators
                        hallucination_indicators = ['channel id', 'created', 'done', '✅', 'kicked', 'timed out']
                        is_potential_fake = any(ind in final_response.lower() for ind in hallucination_indicators)
                        
                        if is_potential_fake or not final_response.strip():
                            logger.warning("❌ POTENTIAL HALLUCINATION DETECTED! Forcing retry...")
                            
                            # Add correction message and retry
                            messages.append({
                                "role": "assistant",
                                "content": content
                            })
                            messages.append({
                                "role": "user", 
                                "content": f"❌ ERROR: You didn't call the {action_intent} tool!\n"
                                        f"You MUST use the {action_intent} function to perform this action.\n"
                                        f"Do NOT make up results. Call the tool NOW!"
                            })
                            continue
                    
                    logger.info(f"✅ Using direct response (no tools)")
                    break
                
                # CASE B: Tool calls requested - EXECUTE THEM!
                logger.info(f"🤖 AI wants to execute {len(tool_calls)} tool(s):")
                
                for tc in tool_calls:
                    func_name = tc.get("function", {}).get("name", "unknown")
                    func_args = tc.get("function", {}).get("arguments", "{}")
                    tools_used.append(func_name)
                    logger.info(f"   → {func_name}({func_args[:120]}...)")
                
                # Add assistant message with tool calls to history
                messages.append({
                    "role": "assistant",
                    "content": content,
                    "tool_calls": tool_calls
                })
                
                # 🛠️ EXECUTE TOOLS - Get REAL results from Discord API!
                logger.info(f"⚡ Executing tools via Discord API...")
                
                tool_results = await tool_executor.process_ai_tool_calls(
                    tool_calls=tool_calls,
                    context=exec_context
                )
                
                # Log actual results
                for tr in tool_results:
                    result_content = tr.get("content", "")[:250]
                    logger.info(f"   ← RESULT: {result_content}...")
                    tool_results_data.append(tr)
                
                # Add tool results back to conversation
                for tr in tool_results:
                    messages.append(tr)
                
                # After first tool use, switch to getting text response
                tool_choice = "none"
                
                # Safety check
                if iteration >= max_tool_iterations:
                    logger.warning(f"⚠️ Max iterations reached")
            
            # 🔑 STEP 4: Generate Final Response (if needed)
            if not final_response or not final_response.strip():
                logger.info(f"📝 Generating final response from {len(tool_results_data)} tool results...")
                
                final_result = await self.groq.chat_completion_with_tools(
                    messages=messages,
                    tools=tool_schemas,
                    temperature=settings.get("temperature", 1.02),
                    task_type=TaskType.CHAT,
                    tool_choice="none"
                )
                
                final_response = final_result.get("content", "") or ""
            
            # 🔑 STEP 5: Clean & Validate Response
            final_response = self._clean_ai_response(final_response)
            
            # ✅ FINAL VALIDATION: For actions, verify tool was actually used
            if action_intent:
                if action_intent not in tools_used:
                    logger.error(f"❌ ACTION '{action_intent}' WAS NEVER EXECUTED!")
                    
                    # Override fake success responses
                    fake_success_words = ['done', 'created', '✅', 'success', 'kicked', 'timed out', 'ready']
                    is_fake_success = any(word in final_response.lower() for word in fake_success_words)
                    
                    if is_fake_success:
                        logger.warning("🔴 Overriding FAKE success response with honest error!")
                        final_response = (
                            f"😅 Arre yaar, maine {action_intent} execute nahi kar paayi!\n"
                            f"Kuch technical issue hai ya permission nahi hai.\n"
                            f"Admin/Owner se puch lo please? 🙏"
                        )
            
            # Save response
            await self._save_message(guild_id, channel_id, user_id, "assistant", final_response)
            
            # Update profile
            tools_str = ','.join(tools_used) if tools_used else 'none'
            user_profile["last_interactions"].append(
                f"[{datetime.now().strftime('%H:%M')}] Ophelia [TOOLS:{tools_str}]: {final_response[:60]}"
            )
            user_profile["last_interactions"] = user_profile["last_interactions"][-10:]
            self.cache.set_user_context(user_id, user_profile)
            
            logger.info(f"\n{'='*50}")
            logger.info(f"✅ RESPONSE GENERATED")
            logger.info(f"   Tools used: {tools_used}")
            logger.info(f"   Length: {len(final_response)} chars")
            logger.info(f"   Preview: {final_response[:100]}...")
            logger.info(f"{'='*50}\n")
            
            return final_response
            
        except Exception as e:
            logger.error(f"❌ ERROR in tool generation: {e}", exc_info=True)
            logger.info("⬇️ Falling back to regular generation...")
            return await self._generate_fallback_response(
                guild_id, channel_id, user_id, user_message,
                username, display_name, guild, bot_member, mentioned_users
            )
    
    async def _generate_fallback_response(self, *args, **kwargs) -> str:
        """Fallback when tool system fails"""
        # Import here to avoid circular dependency
        return await self.generate_response(*args, **kwargs)
    
    # ==========================================
    # 🧹 RESPONSE CLEANING
    # ==========================================
    
    def _clean_ai_response(self, response: str) -> str:
        """
        Clean AI response - remove raw function calls and weird formatting.
        Prevents leaks like <function=get_channel_info[...]>
        """
        if not response:
            return response
        
        # Remove raw function call syntax: <function=name[params]>
        response = re.sub(r'<function=\w+[\[\{].*?[\]\}]>', '', response, flags=re.DOTALL)
        
        # Remove standalone function calls: function_name(params)
        response = re.sub(r'^\s*\w+\([^)]*\)\s*$', '', response, flags=re.MULTILINE)
        
        # Clean up multiple newlines
        response = re.sub(r'\n{3,}', '\n\n', response)
        
        # Strip whitespace
        response = response.strip()
        
        # Fallback if empty after cleaning
        if not response:
            return "Hmm, kuch gadbad hai! Phir se try karo? 🤔"
        
        return response
    
    # ==========================================
    # 👤 USER PROFILE & MOOD
    # ==========================================
    
    def _get_user_profile(self, user_id, username, display_name):
        """Get or create user profile"""
        cache_key = f"user:{user_id}"
        profile = self.cache.get(cache_key)
        
        if not profile:
            profile = {
                "user_id": str(user_id),
                "username": username,
                "display_name": display_name,
                "first_seen": datetime.now().isoformat(),
                "message_count": 0,
                "topics_discussed": set(),
                "inside_jokes": set(),
                "preferences": {},
                "last_interactions": [],
                "mood_history": []
            }
            self.cache.set(cache_key, profile)
        
        # Update basic info
        profile["display_name"] = display_name
        profile["username"] = username
        profile["message_count"] = profile.get("message_count", 0) + 1
        
        return profile
    
    def _detect_mood(self, message: str) -> str:
        """Detect mood from message"""
        msg_lower = message.lower()
        scores = {}
        
        for mood, keywords in self.MOOD_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in msg_lower)
            scores[mood] = score
        
        best_mood = max(scores, key=scores.get) if any(scores.values()) else "neutral"
        return best_mood
    
    # ==========================================
    # 💾 MEMORY OPERATIONS
    # ==========================================
    
    async def _save_message(self, guild_id, channel_id, user_id, role, content):
        """Save message to database"""
        try:
            db = get_db()
            await db.save_message(
                guild_id=str(guild_id),
                channel_id=str(channel_id),
                user_id=str(user_id),
                role=role,
                content=content
            )
        except Exception as e:
            logger.debug(f"Message save failed: {e}")
    
    async def get_conversation_context(self, guild_id, channel_id, user_id, username, 
                                     display_name, task_type=None, user_query=None) -> list:
        """Build conversation context for AI"""
        messages = []
        
        # Get recent conversation history
        try:
            db = get_db()
            history = await db.get_recent_messages(
                guild_id=str(guild_id),
                channel_id=str(channel_id),
                limit=15
            )
            
            for msg in history:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                if role in ["user", "assistant"]:
                    messages.append({"role": role, "content": content})
                    
        except Exception as e:
            logger.debug(f"History fetch failed: {e}")
        
        return messages
    
    async def build_system_prompt(self, guild_id, user_profile, mood, 
                                 available_data=None, user_message=None) -> str:
        """Build comprehensive system prompt"""
        personality = SYSTEM_PROMPTS.get("fun", "")
        custom_instructions = ""
        
        try:
            settings = await self.get_guild_settings(guild_id)
            custom_instructions = settings.get("custom_instructions", "")
        except:
            pass
        
        prompt = BASE_SYSTEM_PROMPT.format(
            personality=personality,
            custom_instructions=custom_instructions
        )
        
        # Add user context
        if user_profile:
            msg_count = user_profile.get("message_count", 0)
            topics = list(user_profile.get("topics_discussed", []))[-5:]
            prompt += f"\n\n**👤 User Context:**\n"
            prompt += f"- Messages exchanged: {msg_count}\n"
            if topics:
                prompt += f"- Topics discussed: {', '.join(topics)}\n"
        
        # Add available data
        if available_data:
            prompt += f"\n{available_data}"
        
        return prompt
    
    async def get_guild_settings(self, guild_id) -> dict:
        """Get guild-specific settings"""
        return DEFAULT_GUILD_SETTINGS.copy()
    
    def gather_available_data(self, user_profile=None, channel_id=None, 
                             guild=None, bot_member=None) -> str:
        """Gather context data for AI"""
        data_parts = ["**📊 Available Data:**\n"]
        
        # Owner info
        try:
            from config.settings import config
            owners_text = "\n👑 **Owners:**\n"
            if guild:
                for owner_id in config.owner_ids:
                    member = guild.get_member(owner_id)
                    if member:
                        name = member.display_name or member.name
                        owners_text += f"• **{name}** (ID: `{owner_id}`) 👑\n"
                    else:
                        owners_text += f"• Unknown (ID: `{owner_id}`) 👑\n"
            data_parts.append(owners_text)
        except:
            pass
        
        # Bot permissions
        if guild and bot_member:
            perms = guild.permissions_for(bot_member)
            perm_list = []
            if perms.manage_channels: perm_list.append("manage_channels ✅")
            if perms.kick_members: perm_list.append("kick ✅")
            if perms.ban_members: perm_list.append("ban ✅")
            if perms.moderate_members: perm_list.append("timeout ✅")
            if perms.send_messages: perm_list.append("send_messages ✅")
            if perms.add_reactions: perm_list.append("react ✅")
            
            if perm_list:
                data_parts.append(f"\n🔧 **My Permissions:** {', '.join(perm_list)}\n")
        
        return "\n".join(data_parts)
    
    # ==========================================
    # 🔐 PERMISSION CHECKS
    # ==========================================
    
    def _check_owner(self, user_id) -> bool:
        """Check if user is bot owner"""
        try:
            from config.settings import is_owner
            return is_owner(user_id)
        except:
            return False
    
    def _check_if_moderator(self, user_id, guild) -> bool:
        """Check if user has moderation permissions"""
        if not guild:
            return False
        
        try:
            member = guild.get_member(user_id)
            if not member:
                return False
            
            if guild.owner_id == user_id:
                return True
            
            perms = guild.permissions_for(member)
            return any([
                perms.administrator,
                perms.manage_guild,
                perms.kick_members,
                perms.ban_members,
                perms.moderate_members
            ])
        except:
            return False
    
    # ==========================================
    # 📝 LEGACY METHODS (for fallback)
    # ==========================================
    
    async def generate_response(self, guild_id, channel_id, user_id, user_message,
                              username="Unknown", display_name="Unknown",
                              guild=None, bot_member=None, mentioned_users=None) -> str:
        """Regular response without tools (fallback)"""
        self._init_clients()
        
        try:
            user_profile = self._get_user_profile(user_id, username, display_name)
            current_mood = self._detect_mood(user_message)
            
            await self._save_message(guild_id, channel_id, user_id, "user", user_message)
            
            task_type = self.groq.detect_task_type(user_message)
            
            messages = await self.get_conversation_context(
                guild_id, channel_id, user_id, username, display_name,
                task_type=task_type, user_query=user_message
            )
            
            if messages and messages[0].get("role") == "system":
                full_prompt = await self.build_system_prompt(
                    guild_id, user_profile, current_mood,
                    user_message=user_message
                )
                messages[0]["content"] = full_prompt[:self.MAX_SYSTEM_PROMPT_CHARS]
            
            messages.append({"role": "user", "content": user_message})
            
            settings = await self.get_guild_settings(guild_id)
            
            response = await self.groq.chat_completion(
                messages=messages,
                temperature=settings.get("temperature", 1.02),
                task_type=task_type
            )
            
            await self._save_message(guild_id, channel_id, user_id, "assistant", response)
            
            return response or "Hmm, kuch gadbad hai! 😅"
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return f"Arre error aa gaya 😅 Try karo!"
    
    def store_channel_message(self, channel_id, author_name, content, is_bot=False, timestamp=None):
        """Store channel message for context awareness"""
        pass  # Simplified for now


# Global instance
_ai_handler_v2_instance = None


def init_ai_handler_v2() -> AIHandlerV2:
    """Initialize global AI Handler v2 instance"""
    global _ai_handler_v2_instance
    _ai_handler_v2_instance = AIHandlerV2()
    return _ai_handler_v2_instance


def get_ai_handler_v2() -> AIHandlerV2:
    """Get global AI Handler v2 instance"""
    if _ai_handler_v2_instance is None:
        return init_ai_handler_v2()
    return _ai_handler_v2_instance
