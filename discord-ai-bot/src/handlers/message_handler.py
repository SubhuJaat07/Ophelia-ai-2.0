"""
🚀 Message Handler for Ophelia AI 3.0 - PRODUCTION GRADE!

CRITICAL RULES:
✅ SIRF @mention pe reply kare (owners exception)
✅ Tools ACTUALLY execute (no fake responses)
✅ Memory persists across restarts

FLOW:
1. Check if should respond (MENTION REQUIRED!)
2. Extract context (mentions, channel, history)
3. Send to AI with tools enabled
4. Execute REAL Discord actions
5. Return response

🔧 FIXED: Mention detection now works correctly!
"""
import discord
from discord.ext import commands
import logging
import asyncio
from typing import Optional

from config.settings import DEFAULT_GUILD_SETTINGS, is_owner
from src.handlers.ai_handler_v3 import get_ai_handler_v3  # 🚀 PRODUCTION GRADE v3!
from src.utils.cache import get_cache
from src.utils.natural_commands import get_natural_parser

logger = logging.getLogger("MessageHandler")


class MessageHandler:
    """Advanced message handler with natural command support"""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.processing_messages = set()  # Track messages being processed
    
    async def should_respond(self, message: discord.Message) -> tuple[bool, str]:
        """
        Determine if bot should respond to this message.
        
        ⚠️ CRITICAL: SIRF @mention pe reply kare! (except DMs/owners)
        Returns (should_respond, reason)
        """
        # Ignore bot messages (including our own)
        if message.author.bot:
            return False, "bot_message"
        
        # DMs - always respond
        if not message.guild:
            logger.info(f"✅ DM from {message.author.name} - will respond")
            return True, "dm_message"
        
        # ✅ CHECK 1: Is bot mentioned? (MOST IMPORTANT!)
        # Using mentioned_in() is more reliable than checking message.mentions
        is_mentioned = self.bot.user.mentioned_in(message)
        
        if is_mentioned:
            logger.info(f"✅✅ MENTION DETECTED from {message.author.name}! Content: {message.content[:50]}...")
            return True, "mention"
        
        # ✅ CHECK 2: Get settings safely (with fallback)
        try:
            ai = get_ai_handler_v3()
            settings = await ai.get_guild_settings(message.guild.id)
        except Exception as e:
            logger.warning(f"Settings fetch failed: {e}, using defaults")
            settings = {"enabled": True, "require_mention": True, "ai_channel_ids": [], "ping_reply_enabled": True}
        
        # Check if AI is disabled for this guild
        if not settings.get("enabled", True):
            if not is_owner(message.author.id):
                return False, "ai_disabled"
        
        # ✅ CHECK 3: Is this an AI channel? (auto-reply channels)
        ai_channel_ids = settings.get("ai_channel_ids", [])
        if message.channel.id in ai_channel_ids:
            return True, "ai_channel"
        
        # ✅ CHECK 4: Reply to @everyone/@here ONLY if enabled
        if settings.get("everyone_ping_reply", False):
            if "@everyone" in message.content or "@here" in message.content:
                return True, "everyone_ping"
        
        # ✅ CHECK 5: Owners can bypass mention (but log it!)
        if is_owner(message.author.id) and settings.get("enabled", True):
            logger.info(f"👑 Owner {message.author.name} used command without mention")
            return True, "owner_command"
        
        # ❌ NO MENTION = NO REPLY
        logger.debug(f"❌ No reply - no mention from {message.author.name} in #{message.channel.name}")
        return False, "no_mention"
    
    async def handle_message(self, message: discord.Message):
        """Main message handler with natural command processing"""
        msg_key = f"{message.channel.id}-{message.id}"
        
        try:
            # 🆕 STORE CHANNEL MESSAGE FOR CONTEXT AWARENESS!
            try:
                ai_handler_instance = get_ai_handler_v3()
                ai_handler_instance.store_channel_message(
                    channel_id=message.channel.id,
                    author_name=message.author.display_name or str(message.author.name),
                    content=self._clean_message_content(message)[:200],
                    is_bot=message.author.bot,
                    timestamp=message.created_at.isoformat()
                )
            except Exception as e:
                logger.debug(f"Channel context storage skipped: {e}")
            
            # Quick check if we should respond
            should_respond, reason = await self.should_respond(message)
            
            if not should_respond:
                return
            
            # Avoid processing same message multiple times
            if msg_key in self.processing_messages:
                logger.debug(f"⏭️ Already processing message {msg_key}")
                return
            
            self.processing_messages.add(msg_key)
            
            logger.info(
                f"📩 Processing from {message.author} in #{getattr(message.channel, 'name', 'DM')} "
                f"(reason: {reason})"
            )
            
            # Show typing indicator
            async with message.channel.typing():
                # 🚀 PRODUCTION-GRADE AI-FIRST APPROACH!
                ai = get_ai_handler_v3()
                
                # Get user info for USER RECOGNITION! 👤
                username = str(message.author.name)
                display_name = message.author.display_name if message.guild else str(message.author)
                
                # 🆕 EXTRACT MENTIONS - So AI knows WHO to kick/ban/etc!
                mentioned_users = []
                
                # discord.py uses `message.mentions` (not mentioned_users!)
                if message.mentions:
                    mentioned_users = [
                        {"id": str(u.id), "name": u.display_name, "mention": u.mention}
                        for u in message.mentions
                        if u.id != self.bot.user.id  # Exclude bot itself
                    ]
                
                # 🆕 Build context-rich message for AI
                clean_message = self._clean_message_content(message)
                
                # Add mention context to message if someone was mentioned
                if mentioned_users and not any(word in clean_message.lower() for word in ["kick", "ban", "mute", "timeout", "warn"]):
                    # Regular message with mention - AI will decide what to do
                    context_info = f"\n\n[Context: You can see {len(mentioned_users)} mentioned user(s): {', '.join([u['name'] for u in mentioned_users])}]"
                else:
                    context_info = ""
                
                # 🧠🛠️ SEND TO AI WITH TOOLS ENABLED!
                try:
                    # PRODUCTION: Use v3 handler with full integration
                    response = await ai.generate_response_with_tools(
                        guild_id=message.guild.id if message.guild else 0,
                        channel_id=message.channel.id,
                        user_id=message.author.id,
                        user_message=clean_message + context_info,
                        username=username,
                        display_name=display_name,
                        guild=message.guild,
                        bot_member=message.guild.me if message.guild else None,
                        mentioned_users=mentioned_users,
                        message=message  # Pass original message for context
                    )
                except Exception as tool_error:
                    logger.error(f"❌ Tool generation failed: {tool_error}", exc_info=True)
                    # Fallback: Simple response
                    response = "😅 Arre yaar, kuch technical issue aa gaya! Thoda der baad try karo."
                
                # Send response
                await self._send_response(message, response)
            
            # Remove from processing set
            self.processing_messages.discard(msg_key)
            
        except Exception as e:
            logger.error(f"❌ Error handling message: {e}", exc_info=True)
            import traceback
            traceback.print_exc()
            
            try:
                self.processing_messages.discard(msg_key)
                await message.reply(f"😅 Arre yaar, kuch error aa gaya! Try again karo.\n`{str(e)[:100]}`")
            except:
                pass
    
    def _clean_message_content(self, message: discord.Message) -> str:
        """
        Clean message content by removing bot mention.
        Keeps emojis, mentions of others intact.
        """
        content = message.content
        
        # Remove bot mention from content so it's not sent to API
        if message.guild and self.bot.user.mentioned_in(message):
            # Try both formats: <@ID> and <@!ID>
            bot_mention = self.bot.user.mention
            bot_mention_bang = f"<@!{self.bot.user.id}>"
            
            content = content.replace(bot_mention, "").strip()
            content = content.replace(bot_mention_bang, "").strip()
        
        # Clean up extra whitespace
        while "  " in content:
            content = content.replace("  ", " ")
        
        return content.strip() or "hi"
    
    async def _send_response(self, original_message: discord.Message, response: str):
        """
        Send AI response using Discord's reply feature.
        - Normal chat: PLAIN TEXT (no embeds)
        - Commands: Already handled with embeds by natural_commands
        """
        max_length = 1900
        
        # For NORMAL AI CHAT: Always use plain text (no embeds!)
        if len(response) <= max_length:
            await original_message.reply(response, mention_author=False)
        else:
            chunks = self._split_response(response, max_length)
            
            for i, chunk in enumerate(chunks):
                if i == 0:
                    await original_message.reply(chunk, mention_author=False)
                else:
                    await original_message.channel.send(chunk)
                
                if i < len(chunks) - 1:
                    await asyncio.sleep(0.5)
    
    def _should_use_embed(self, response: str) -> bool:
        """Always return False now - commands handle their own embeds, chat is plain text"""
        return False
    
    def _split_response(self, response: str, max_length: int) -> list[str]:
        """Split long response into chunks at appropriate boundaries"""
        chunks = []
        current_chunk = ""
        
        lines = response.split("\n")
        
        for line in lines:
            if len(current_chunk) + len(line) + 1 > max_length:
                if current_chunk:
                    chunks.append(current_chunk.rstrip())
                current_chunk = line + "\n"
            else:
                current_chunk += line + "\n"
        
        if current_chunk:
            chunks.append(current_chunk.rstrip())
        
        return chunks


# Global instance
message_handler: Optional[MessageHandler] = None


def init_message_handler(bot: commands.Bot) -> MessageHandler:
    """Initialize global message handler"""
    global message_handler
    message_handler = MessageHandler(bot)
    return message_handler


def get_message_handler() -> MessageHandler:
    """Get global message handler instance"""
    if message_handler is None:
        raise RuntimeError("Message handler not initialized!")
    return message_handler
