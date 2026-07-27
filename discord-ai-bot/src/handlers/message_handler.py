"""
Message Handler - Processes incoming messages and triggers AI responses
Handles ping detection, AI channels, reply mode, etc.
"""
import discord
from discord.ext import commands
import logging
import asyncio
from typing import Optional

from config.settings import DEFAULT_GUILD_SETTINGS
from src.handlers.ai_handler import get_ai_handler
from src.utils.cache import get_cache

logger = logging.getLogger("MessageHandler")


class MessageHandler:
    """Handles all incoming message processing"""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.processing_messages = set()  # Track messages being processed to avoid duplicates
    
    async def should_respond(self, message: discord.Message) -> tuple[bool, str]:
        """
        Determine if bot should respond to this message.
        Returns (should_respond, reason)
        """
        # Ignore bot messages (including our own)
        if message.author.bot:
            return False, "bot_message"
        
        # Only respond in guilds (servers), not DMs for now
        if not message.guild:
            return False, "dm_message"
        
        ai = get_ai_handler()
        settings = await ai.get_guild_settings(message.guild.id)
        
        # Check if AI is enabled for this guild
        if not settings.get("enabled", True):
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
            # Bot was mentioned - check if ping reply enabled
            if settings.get("ping_reply_enabled", True):
                return True, "mention"
            else:
                return False, "ping_reply_disabled"
        
        # Check for @everyone or @here mentions
        if settings.get("everyone_ping_reply", False):
            if "@everyone" in message.content or "@here" in message.content:
                return True, "everyone_ping"
        
        # If mention required but no mention, don't respond
        if require_mention and not is_mentioned:
            return False, "no_mention_required"
        
        return False, "no_trigger"
    
    async def handle_message(self, message: discord.Message):
        """Main message handler - processes and responds if needed"""
        try:
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
                f"Processing message from {message.author} in #{message.channel.name} "
                f"(reason: {reason})"
            )
            
            # Show typing indicator
            async with message.channel.typing():
                # Generate AI response
                ai = get_ai_handler()
                
                response = await ai.generate_response(
                    guild_id=message.guild.id,
                    channel_id=message.channel.id,
                    user_id=message.author.id,
                    user_message=self._clean_message_content(message),
                    username=str(message.author)
                )
                
                # Send response with proper formatting
                await self._send_response(message, response)
            
            # Remove from processing set after a delay
            self.processing_messages.discard(msg_key)
            
        except Exception as e:
            logger.error(f"Error handling message: {e}")
            
            # Try to send error message
            try:
                if msg_key in self.processing_messages:
                    self.processing_messages.discard(msg_key)
                await message.reply(f"😅 Arre bhai, kuch error aa gaya! Try again karo.")
            except:
                pass
    
    def _clean_message_content(self, message: discord.Message) -> str:
        """
        Clean message content by removing bot mention.
        Keeps emojis, mentions of others intact.
        """
        content = message.content
        
        # Remove bot mention from content so it's not sent to API
        if self.bot.user.mentioned_in(message):
            # Remove the mention but keep everything else
            for mention in message.mentions:
                if mention.id == self.bot.user.id:
                    content = content.replace(mention.mention, "").strip()
                    content = content.replace(f"<@!{mention.id}>", "").strip()
        
        # Clean up extra whitespace
        while "  " in content:
            content = content.replace("  ", " ")
        
        return content.strip() or "hi"  # Default to hi if empty
    
    async def _send_response(self, original_message: discord.Message, response: str):
        """
        Send AI response using Discord's reply feature.
        Handles long messages, embeds when needed, etc.
        """
        max_length = 1900  # Leave some room for safety
        
        # Check if response should be in embed (contains code blocks, etc.)
        should_embed = self._should_use_embed(response)
        
        if len(response) <= max_length:
            # Single message response
            if should_embed:
                embed = discord.Embed(
                    description=response,
                    color=discord.Color.blurple()
                )
                embed.set_footer(text=f"🤖 AI Response • Replying to {original_message.author.display_name}")
                await original_message.reply(embed=embed, mention_author=False)
            else:
                # Normal text reply - THIS IS THE KEY PART!
                # Using reply=True makes Discord show it as a reply to the specific user
                await original_message.reply(response, mention_author=False)
        else:
            # Long response - split into chunks
            chunks = self._split_response(response, max_length)
            
            for i, chunk in enumerate(chunks):
                if i == 0:
                    # First chunk as reply
                    if should_embed:
                        embed = discord.Embed(description=chunk, color=discord.Color.blurple())
                        embed.set_footer(text=f"🤖 AI Response ({i+1}/{len(chunks)})")
                        await original_message.reply(embed=embed, mention_author=False)
                    else:
                        await original_message.reply(chunk, mention_author=False)
                else:
                    # Subsequent chunks as normal messages
                    if should_embed:
                        embed = discord.Embed(description=chunk, color=discord.Color.blurple())
                        embed.set_footer(text=f"🤖 AI Response ({i+1}/{len(chunks)})")
                        await original_message.channel.send(embed=embed)
                    else:
                        await original_message.channel.send(chunk)
                
                # Small delay between chunks
                if i < len(chunks) - 1:
                    await asyncio.sleep(0.5)
    
    def _should_use_embed(self, response: str) -> bool:
        """Determine if response should be sent as embed"""
        # Use embed if contains code blocks
        if "```" in response:
            return True
        
        # Use embed if very long single line
        lines = response.split("\n")
        if any(len(line) > 100 for line in lines):
            return True
        
        return False
    
    def _split_response(self, response: str, max_length: int) -> list[str]:
        """Split long response into chunks at appropriate boundaries"""
        chunks = []
        current_chunk = ""
        
        # Split by newlines first to preserve formatting
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


# Global message handler instance
message_handler: Optional[MessageHandler] = None


def init_message_handler(bot: commands.Bot) -> MessageHandler:
    """Initialize the global message handler"""
    global message_handler
    message_handler = MessageHandler(bot)
    return message_handler


def get_message_handler() -> MessageHandler:
    """Get the global message handler instance"""
    if message_handler is None:
        raise RuntimeError("Message handler not initialized!")
    return message_handler
