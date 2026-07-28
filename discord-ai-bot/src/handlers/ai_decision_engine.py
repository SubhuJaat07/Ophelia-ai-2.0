"""
🧠 AI Decision Engine v1.0 - Ophelia THINKS and DECIDES!

Instead of pattern-matching commands, Ophelia's AI:
1. Understands user INTENT (in ANY language)
2. Knows her CAPABILITIES (what she can do)
3. Has access to DATA (profiles, context, memories)
4. DECIDES what action to take naturally

This makes her work in Hindi, English, Hinglish, or any language!
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

logger = logging.getLogger("AIDecisionEngine")


class AIDecisionEngine:
    """
    AI-powered decision engine that replaces pattern-matched commands.
    
    Instead of:
        if "kick" in message.lower(): do_kick()
    
    We now:
        1. AI analyzes: "User wants to remove someone"
        2. AI decides: "I should use kick command"
        3. Execute with context
    """
    
    # ==================== CAPABILITIES MANIFEST ====================
    # This tells AI what she CAN DO
    CAPABILITIES_MANIFEST = """
📋 **OPHELIA'S CAPABILITIES** (Ye sab kar sakti hu!)

**👥 USER COMMANDS (Moderation - OWNERS ONLY):**
• **Kick** - Kisi ko server se bahar karo (need: @mention or name)
• **Ban** - Kisi ko permanently block karo (need: @mention or name)  
• **Mute** - Kisi ko chup karao (need: @mention or name)
• **Warn** - Warning do kisi ko (need: @mention + reason)
• **Timeout** - Kisi ko time-out do (need: @mention + duration)

**📊 INFO & DATA COMMANDS:**
• **Show Profile** - User ka profile dikhao (relationship, mood, topics)
• **Channel Context** - Recent channel messages dikhao (kya ho rha)
• **My Stats** - Apna data dikhao (msg count, level, etc)
• **Server Info** - Server ki info dikhao
• **👑 Owners List** - Bot owners kaun hai (names + IDs)!

**💬 CHAT & PERSONALITY:**
• **Normal Chat** - Natural conversation (mood-based replies)
• **Jokes/Memes** - Fun responses when appropriate
• **Advice** - Help users with problems
• **Roleplay** - Stay in character as Delhi girl

**🧠 MEMORY & CONTEXT:**
• **Remember** - Save important info about users
• **Recall** - Recall past conversations
• **Mood Detection** - Understand user emotions
• **Context Awareness** - Know what's happening in channel

**⚙️ SETTINGS (Owner Only):**
• **Change Settings** - Modify bot behavior
• **Set Personality** - Adjust response style
• **Manage Memory** - Control what's remembered

**👑 OWNER INFO (When asked "owners kaun hai"):**
• I KNOW who my owners are! (Names + IDs available)
• Owners have FULL ACCESS to all commands
• When someone asks about owners, show the list PROUDLY!
• Example response: "👑 Mere owners hain: **Subhu**, **Aryan**, **Kavya** - Inko sab power hai!"
"""
    
    # ==================== AVAILABLE DATA MANIFEST ====================
    # This tells AI what DATA she has access to
    AVAILABLE_DATA = """
📦 **DATA I HAVE ACCESS TO:**

**👤 PER-USER DATA:**
• user_profile: {{user_profile}} (relationship level, msg count, topics, moods)
• user_id, username, display_name
• message_count: How many times they've talked to me
• relationship_level: new → casual → friend → bestie
• topics_discussed: What they like talking about
• mood_history: Their recent emotional states
• inside_jokes: Shared moments between us

**👑 OWNER DATA (IMPORTANT!):**
• owners_list: Complete list of bot owners with NAMES + IDs!
• Owners have FULL ACCESS - kick/ban/settings everything!
• I can show this when asked "owners kaun hai" or "who are owners"

**📺 CHANNEL DATA:**
• recent_messages: Last 50 messages from this channel
• channel_id, channel_name
• Active discussions happening right now
• Who said what recently

**🤖 BOT DATA:**
• My personality settings
• My capabilities (see above)
• Current guild/server settings
• Available models for responses

**⏰ TEMPORAL DATA:**
• Current time: {{current_time}}
• When user was first seen
• Last interaction timestamp
"""
    
    # ==================== INTENT TEMPLATES ====================
    # These help AI understand WHAT user wants (not patterns!)
    INTENT_EXAMPLES = """
🎯 **HOW TO UNDERSTAND USER INTENT:**

**Examples of same intent in different languages:**

*Moderation - Kick:*
• "kick @user" (English)
• "@user ko kick karo" (Hindi)
• "iska kick maro isko bahar karo" (Hinglish)
• "remove this person" (English)
• "ye nikalo server se" (Hindi)

*Info - Profile:*
• "my profile" (English)
• "mera profile dikhao" (Hindi)
• "mere baare me kya jaanti ho" (Hinglish)
• "what do you know about me" (English)

*Info - Channel Context:*
• "kya chal rha" (Hindi)
• "what happened here" (English)
• "discussion kya thi" (Hindi)
• "recent messages dikhao" (Hinglish)

*Info - Owners:*
• "owners kaun hai" (Hindi)
• "who are the owners" (English)
• "malik kaun hai" (Hindi)
• "who made this bot" (English)
• "kon hai jo sab control karta" (Hinglish)

*Chat - Mood based:*
• "I'm sad" → Empathetic response
• "muskil hai yaar" → Supportive friend
• "bore ho rhi hu" → Entertaining response
"""
    
    def __init__(self):
        self.decision_cache = {}  # Cache recent decisions
    
    def build_decision_context(
        self,
        user_message: str,
        user_profile: Dict[str, Any],
        channel_context: Optional[List[Dict]] = None,
        current_mood: str = "neutral",
        is_owner: bool = False,
        is_admin: bool = False
    ) -> str:
        """
        Build complete context for AI to make decisions.
        
        This injects ALL available data so AI can decide intelligently!
        """
        
        # Format current time
        current_time = datetime.now().strftime("%I:%M %p (%d/%m/%Y)")
        
        # Build user profile summary
        profile_summary = self._format_user_profile(user_profile)
        
        # Build channel context summary  
        context_summary = self._format_channel_context(channel_context)
        
        # Complete decision context
        decision_context = f"""
{self.CAPABILITIES_MANIFEST}

{self.AVAILABLE_DATA.format(
    user_profile=profile_summary,
    current_time=current_time
)}

{self.INTENT_EXAMPLES}

---

📨 **CURRENT SITUATION:**

**User's Message:** "{user_message}"

**User State:**
- Mood: {current_mood}
- Is Owner: {is_owner}
- Is Admin: {is_admin}
- {profile_summary}

**Channel Activity:**
{context_summary if context_summary else "No recent activity"}

---

🎯 **YOUR TASK:**
1. Understand what user WANTS (intent detection)
2. Decide which capability to use (if any)
3. Formulate natural response in SAME language as user
4. Use available data to personalize response

**IMPORTANT:** 
- Respond in user's language (Hindi/English/Hinglish)
- Be natural, not robotic
- Use personality appropriately
- If moderation action needed, specify action clearly
"""
        
        return decision_context
    
    def _format_user_profile(self, profile: Dict[str, Any]) -> str:
        """Format user profile for AI consumption"""
        if not profile:
            return "New user - no profile yet"
        
        try:
            level = profile.get("relationship_level", "new")
            msg_count = profile.get("message_count", 0)
            topics = profile.get("topics_discussed", [])
            nicknames = profile.get("nicknames_given", [])
            
            # Relationship emoji
            level_emoji = {"new": "🆗", "casual": "😊", "friend": "😄", "bestie": "🔥"}
            
            summary = f"""Relationship: {level_emoji.get(level, '🆗')} {level} ({msg_count} messages)"""
            
            if topics:
                summary += f"\nLikes discussing: {', '.join(topics[:5])}"
            
            if nicknames:
                summary += f"\nI call them: {nicknames[-1]}"
            
            return summary
            
        except Exception as e:
            logger.error(f"Error formatting profile: {e}")
            return "Profile available but error reading"
    
    def _format_channel_context(self, context: Optional[List[Dict]]) -> str:
        """Format channel context for AI consumption"""
        if not context:
            return "No recent messages"
        
        try:
            # Get last 10 messages for summary
            recent = context[-10:] if len(context) > 10 else context
            
            lines = []
            for msg in recent:
                author = msg.get("author_name", "Unknown")
                content = msg.get("content", "")[:80]
                is_bot = msg.get("is_bot", False)
                bot_tag = "🤖" if is_bot else "👤"
                lines.append(f"{bot_tag} {author}: {content}")
            
            return "\n".join(lines)
            
        except Exception as e:
            logger.error(f"Error formatting context: {e}")
            return "Context available but error reading"
    
    def parse_ai_decision(self, ai_response: str) -> Dict[str, Any]:
        """
        Parse AI's decision from its response.
        
        AI can indicate actions in format:
        [ACTION: kick_user] @username reason
        [ACTION: show_profile]
        [ACTION: show_channel_context]
        etc.
        """
        import re
        
        decision = {
            "action": None,  # kick, ban, mute, show_profile, show_context, chat, etc.
            "target": None,  # username/user_id if applicable
            "reason": None,  # reason for moderation
            "response": ai_response,  # actual text to send
            "confidence": 0.5  # how sure AI is about this action
        }
        
        # Look for action markers
        action_pattern = r'\[ACTION:\s*(\w+)\](?:\s*(?:@?(\w+)\s*)?(.*))?'
        match = re.search(action_pattern, ai_response, re.IGNORECASE)
        
        if match:
            decision["action"] = match.group(1).lower()
            decision["target"] = match.group(2)
            decision["reason"] = match.group(3).strip() if match.group(3) else None
            decision["confidence"] = 0.9  # High confidence if explicitly marked
            # Remove action marker from response
            decision["response"] = re.sub(action_pattern, '', ai_response).strip()
        
        # Also detect implicit intents
        lower_response = ai_response.lower()
        
        # If asking about self/profile
        if any(word in lower_response for word in ["my profile", "mera profile", "about me", "mere baare me"]):
            if not decision["action"]:
                decision["action"] = "show_profile"
                decision["confidence"] = 0.7
        
        # If asking about channel
        if any(word in lower_response for word in ["kya chal rha", "what happened", "channel context", "recent msgs", "discussion"]):
            if not decision["action"]:
                decision["action"] = "show_channel_context"
                decision["confidence"] = 0.7
        
        return decision


# Singleton instance
_decision_engine_instance = None

def get_decision_engine() -> AIDecisionEngine:
    """Get singleton instance of decision engine"""
    global _decision_engine_instance
    if _decision_engine_instance is None:
        _decision_engine_instance = AIDecisionEngine()
    return _decision_engine_instance
