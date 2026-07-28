"""
🚀 Message Handler for Ophelia AI 2.0 - AI-FIRST Architecture!

NEW FLOW (v4.0):
1. User sends message
2. AI analyzes intent with FULL context (mentions, channel, history)
3. AI decides: Command? Chat? Question?
4. Execute action OR respond naturally

NO MORE PATTERN MATCHING - AI IS THE BRAIN NOW! 🧠
"""
import discord
from discord.ext import commands
import logging
import asyncio
from typing import Optional

from config.settings import DEFAULT_GUILD_SETTINGS, is_owner
from src.handlers.ai_handler import get_ai_handler
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
        Returns (should_respond, reason)
        """
        # Ignore bot messages (including our own)
        if message.author.bot:
            return False, "bot_message"
        
        # DMs - always respond (owners get full power)
        if not message.guild:
            return True, "dm_message"
        
        ai = get_ai_handler()
        settings = await ai.get_guild_settings(message.guild.id)
        
        # Check if AI is enabled for this guild
        if not settings.get("enabled", True):
            # But owners can always use it!
            if not is_owner(message.author.id):
                return False, "ai_disabled"
        
        # Check if message is in an AI channel (auto-reply without ping)
        ai_channel_ids = settings.get("ai_channel_ids", [])
        if message.channel.id in ai_channel_ids:
            return True, "ai_channel"
        
        # Check if pinging is required
        require_mention = settings.get("require_mention", True)
        
        # Check for bot mention
        is_mentioned = self.bot.user in message.mentions
        
        if is_mentioned:
            if settings.get("ping_reply_enabled", True):
                return True, "mention"
            else:
                return False, "ping_reply_disabled"
        
        # Check for @everyone or @here mentions
        if settings.get("everyone_ping_reply", False):
            if "@everyone" in message.content or "@here" in message.content:
                return True, "everyone_ping"
        
        # Owners don't need mention in servers where bot is active
        if is_owner(message.author.id) and settings.get("enabled", True):
            return True, "owner_command"
        
        if require_mention and not is_mentioned:
            return False, "no_mention_required"
        
        return False, "no_trigger"
    
    async def handle_message(self, message: discord.Message):
        """Main message handler with natural command processing"""
        try:
            # 🆕 STORE CHANNEL MESSAGE FOR CONTEXT AWARENESS!
            # This lets Ophelia know what's happening in the server!
            try:
                ai_handler_instance = get_ai_handler()
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
            msg_key = f"{message.channel.id}-{message.id}"
            if msg_key in self.processing_messages:
                return
            
            self.processing_messages.add(msg_key)
            
            logger.info(
                f"📩 Processing from {message.author} in #{getattr(message.channel, 'name', 'DM')} "
                f"(reason: {reason})"
            )
            
            # Show typing indicator
            async with message.channel.typing():
                # 🚀 NEW AI-FIRST APPROACH: AI decides everything!
                ai = get_ai_handler()
                
                # Get user info for USER RECOGNITION! 👤
                username = str(message.author.name)
                display_name = message.author.display_name if message.guild else str(message.author)
                
                # 🆕 EXTRACT MENTIONS - So AI knows WHO to kick/ban/etc!
                mentioned_users = []
                if message.mentioned_users:
                    mentioned_users = [
                        {"id": str(u.id), "name": u.display_name, "mention": u.mention}
                        for u in message.mentioned_users
                        if u.id != self.bot.user.id  # Exclude bot itself
                    ]
                elif message.mentions:
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
                
                # 🧠 SEND TO AI WITH FULL CONTEXT!
                response = await ai.generate_response(
                    guild_id=message.guild.id if message.guild else 0,
                    channel_id=message.channel.id,
                    user_id=message.author.id,
                    user_message=clean_message + context_info,
                    username=username,
                    display_name=display_name,
                    guild=message.guild,
                    bot_member=message.guild.me if message.guild else None,
                    mentioned_users=mentioned_users  # 🆕 Pass who was mentioned!
                )
                
                # Send response
                await self._send_response(message, response)
            
            # Remove from processing set
            self.processing_messages.discard(msg_key)
            
        except Exception as e:
            logger.error(f"❌ Error handling message: {e}")
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
            for mention in message.mentions:
                if mention.id == self.bot.user.id:
                    content = content.replace(mention.mention, "").strip()
                    content = content.replace(f"<@!{mention.id}>", "").strip()
        
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
