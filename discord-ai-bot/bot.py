"""
Main Discord AI Bot
Complete Discord bot with Groq API integration, memory, and server settings
"""
import discord
from discord.ext import commands
import logging
import asyncio
import sys
import os

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import config
from src.utils.database import init_database, get_db
from src.utils.cache import init_cache, get_cache
from src.utils.groq_client import init_groq_client, get_groq_client
from src.handlers.ai_handler import init_ai_handler, get_ai_handler
from src.handlers.message_handler import init_message_handler, get_message_handler
from src.utils.meta_commands import init_meta_commands

# Configure logging
logging.basicConfig(
    level=getattr(logging, config.log_level.upper()),
    format='%(asctime)s | %(name)s | %(levelname)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("Bot")


class AIBot(commands.Bot):
    """Main AI Bot class with enhanced functionality"""
    
    def __init__(self):
        # Set up intents - we need all of them for full functionality
        intents = discord.Intents.default()
        intents.message_content = True  # Read message content
        intents.members = True  # Track members for memory
        intents.reactions = True  # Handle reactions
        intents.presences = True  # User presence (optional)
        
        super().__init__(
            command_prefix="!",  # Legacy prefix (mainly using slash commands)
            intents=intents,
            help_command=None,  # We'll create custom help
            activity=discord.Activity(
                type=discord.ActivityType.playing,
                name="AI Chat | /ai help"
            )
        )
        
        self.initialized = False
    
    async def setup_hook(self):
        """Called when bot is starting up - initialize all components"""
        logger.info("🚀 Bot starting up...")
        
        try:
            # Validate configuration
            if not config.token:
                logger.error("❌ No Discord token provided! Check .env file")
                return
            
            if not config.has_valid_groq_keys:
                logger.error("❌ No valid Groq API keys provided!")
                return
            
            # Initialize database connection
            logger.info("📦 Connecting to Supabase...")
            db = init_database(config.supabase_url, config.supabase_key)
            
            # Initialize cache
            logger.info("⚡ Initializing cache...")
            cache = init_cache(ttl=config.cache_ttl)
            
            # Warm up cache from database
            await cache.warmup_from_database(db)
            
            # Initialize Groq client with multi-key support
            logger.info(f"🔑 Initializing Groq client ({len(config.groq_api_keys)} keys)...")
            groq = init_groq_client(config.groq_api_keys)
            
            # Test API connection
            connected, msg = await groq.test_connection()
            if connected:
                logger.info(f"✅ {msg}")
            else:
                logger.warning(f"⚠️ {msg}")
            
            # Initialize AI handler
            ai = init_ai_handler()
            
            # Initialize message handler
            msg_handler = init_message_handler(self)
            
            # Initialize meta-command system
            meta = init_meta_commands(self)
            
            # Load cogs/commands
            logger.info("📦 Loading commands...")
            await self.load_extension("src.commands.settings")
            await self.load_extension("src.commands.utility")
            
            self.initialized = True
            logger.info("✅ All systems initialized!")
            
        except Exception as e:
            logger.error(f"❌ Error during startup: {e}")
            import traceback
            traceback.print_exc()
    
    async def on_ready(self):
        """Called when bot is ready and connected"""
        if not self.initialized:
            logger.error("❌ Bot not properly initialized!")
            return
        
        logger.info("=" * 50)
        logger.info(f"🤖 {self.user.name} is online!")
        logger.info(f"📊 Serving {len(self.guilds)} servers")
        logger.info(f"🆔 Bot ID: {self.user.id}")
        logger.info("=" * 50)
        
        # Update presence
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.playing,
                name="AI Chat | @me ya /ai help"
            )
        )
    
    async def on_message(self, message: discord.Message):
        """
        Main message handler.
        Processes incoming messages and triggers AI responses when appropriate.
        """
        # Don't process until fully initialized
        if not self.initialized:
            return
        
        # Process regular commands first (prefix commands like !help)
        await self.process_commands(message)
        
        # Then handle AI message processing
        try:
            handler = get_message_handler()
            await handler.handle_message(message)
        except Exception as e:
            logger.error(f"Error in message handler: {e}")
    
    async def on_guild_join(self, guild: discord.Guild):
        """Called when bot joins a new server"""
        logger.info(f"🎉 Joined new server: {guild.name} ({guild.id})")
        
        # Create default settings for this guild
        try:
            db = get_db()
            from config.settings import DEFAULT_GUILD_SETTINGS
            await db.upsert_guild_settings(guild.id, DEFAULT_GUILD_SETTINGS.copy())
            
            # Try to send welcome message to system channel or first text channel
            channel = guild.system_channel or next(
                (ch for ch in guild.text_channels if ch.permissions_for(guild.me).send_messages),
                None
            )
            
            if channel:
                embed = discord.Embed(
                    title="🤖 Hello! Main aa gaya!",
                    description=(
                        "Main **AI Bot** hoon!\n\n"
                        "**Kaise use karo:**\n"
                        "• Mere ko **@mention** karo reply ke liye\n"
                        "• `/ai setting` se settings change karo (Mods only)\n"
                        "• `/ai status` se current status dekho\n\n"
                        "**Features:**\n"
                        "• Long-term memory 🧠\n"
                        "• Custom personality 😄\n"
                        "• Meta-commands ⚡\n"
                        "• Server-specific settings ⚙️\n\n"
                        "Mazaa aayega! 😎"
                    ),
                    color=discord.Color.blurple()
                )
                embed.set_footer(text="Use /ai setting to configure me!")
                await channel.send(embed=embed)
                
        except Exception as e:
            logger.error(f"Error welcoming guild {guild.id}: {e}")
    
    async def on_command_error(self, ctx, error):
        """Handle command errors gracefully"""
        if isinstance(error, commands.CommandNotFound):
            pass  # Ignore unknown commands
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ Tere paas permission nahi hai bhai!", ephemeral=True)
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"❌ Missing argument: `{error.param.name}`", ephemeral=True)
        else:
            logger.error(f"Command error: {error}")
            await ctx.send(f"❌ Error: {str(error)}", ephemeral=True)


async def main():
    """Main entry point"""
    # Create and run bot
    bot = AIBot()
    
    try:
        await bot.start(config.token)
    except KeyboardInterrupt:
        logger.info("🛑 Shutting down...")
        await bot.close()
    except discord.LoginFailure:
        logger.error("❌ Invalid Discord token! Check your .env file")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        raise


if __name__ == "__main__":
    # Run the bot
    asyncio.run(main())
