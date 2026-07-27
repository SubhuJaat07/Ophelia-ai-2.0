"""
Ophelia AI 2.0 - Advanced Discord Bot
Natural Language Commands • Full Discord API • Owner System
"""
import discord
from discord.ext import commands
import logging
import asyncio
import sys
import os

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import config, is_owner, get_owners
from src.utils.database import init_database, get_db
from src.utils.cache import init_cache, get_cache
from src.utils.groq_client import init_groq_client, get_groq_client
from src.handlers.ai_handler import init_ai_handler, get_ai_handler
from src.handlers.message_handler import init_message_handler, get_message_handler
from src.utils.meta_commands import init_meta_commands
from src.utils.natural_commands import init_natural_commands

# Configure logging
logging.basicConfig(
    level=getattr(logging, config.log_level.upper()),
    format='%(asctime)s | %(name)s | %(levelname)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("OpheliaAI")


class OpheliaBot(commands.Bot):
    """Ophelia AI 2.0 - Advanced Discord Bot with Natural Language Commands"""
    
    def __init__(self):
        # Set up intents - we need ALL of them for full functionality!
        intents = discord.Intents.default()
        intents.message_content = True      # Read message content (CRITICAL for natural language)
        intents.members = True              # Track members for memory & info
        intents.reactions = True            # Handle reactions
        intents.presences = True            # User presence info
        intents.moderation = True           # For timeout/kick/ban actions
        
        super().__init__(
            command_prefix="!",            # Legacy prefix (mainly using slash commands)
            intents=intents,
            help_command=None,              # Custom help command
            activity=discord.Activity(
                type=discord.ActivityType.playing,
                name="Natural Commands | @me bolna!"
            ),
            owner_ids=config.owner_ids      # Set owners for bot.owner_id checks
        )
        
        self.initialized = False
        self.start_time = None
    
    async def setup_hook(self):
        """Called when bot is starting up - initialize all components"""
        logger.info("🚀 Ophelia AI 2.0 starting up...")
        self.start_time = datetime.utcnow()
        
        try:
            # Validate configuration
            if not config.token:
                logger.error("❌ No Discord token provided! Check .env file")
                return
            
            if not config.has_valid_groq_keys:
                logger.error("❌ No valid Groq API keys provided!")
                return
            
            # Log owner IDs
            logger.info(f"👑 Owners: {config.owner_ids}")
            
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
            
            # Initialize message handler (with natural command support!)
            msg_handler = init_message_handler(self)
            
            # Initialize meta-command system (legacy /cmd support)
            meta = init_meta_commands(self)
            
            # Initialize NATURAL LANGUAGE COMMAND SYSTEM! 🧠
            logger.info("🗣️ Initializing natural language command parser...")
            natural = init_natural_commands(self)
            
            # Load cogs/commands
            logger.info("📦 Loading commands...")
            await self.load_extension("src.commands.settings")
            await self.load_extension("src.commands.utility")
            
            self.initialized = True
            logger.info("=" * 50)
            logger.info("✅ Ophelia AI 2.0 FULLY INITIALIZED!")
            logger.info("=" * 50)
            
        except Exception as e:
            logger.error(f"❌ Error during startup: {e}")
            import traceback
            traceback.print_exc()
    
    async def on_ready(self):
        """Called when bot is ready and connected"""
        if not self.initialized:
            logger.error("❌ Bot not properly initialized!")
            return
        
        logger.info("=" * 60)
        logger.info(f"🤖 **OPHELIA AI 2.0** IS ONLINE!")
        logger.info(f"📊 Serving {len(self.guilds)} servers")
        logger.info(f"🆔 Bot ID: {self.user.id}")
        logger.info(f"👑 Owners: {len(config.owner_ids)} users with FULL ACCESS")
        logger.info(f"🗣️ Natural Language Commands: ENABLED")
        logger.info("=" * 60)
        
        # Update presence with cool status
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.playing,
                name="Bolo 'avatar dikhao' ya 'timeout do' | @me"
            )
        )
    
    async def on_message(self, message: discord.Message):
        """
        Main message handler.
        Processes incoming messages and triggers AI responses when appropriate.
        Supports natural language commands!
        """
        # Don't process until fully initialized
        if not self.initialized:
            return
        
        # Ignore bots (including ourselves)
        if message.author.bot:
            return
        
        # Process regular commands first (prefix commands like !help)
        await self.process_commands(message)
        
        # Then handle AI message processing (includes natural commands!)
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
                    title="🤖✨ OPHELIA AI 2.0 AA GAYI! ✨",
                    description=(
                        "Main **Ophelia AI 2.0** hoon - sabse advanced Discord AI!\n\n"
                        "**🔥 Kaise use karo:**\n"
                        "• Mere ko **@mention** karo ya seedha bolo\n"
                        "• **Natural Language Commands** - koi syntax nahi!\n"
                        "  `Avatar dikhao` | `Timeout do` | `Server info dikhao`\n\n"
                        "**⚙️ Settings (Mods/Owners):**\n"
                        "• `/ai setting` - Full settings panel\n"
                        "• `/ai status` - Current status\n\n"
                        "**👑 OWNER POWERS:**\n"
                        "• Kick/Ban/Timeout/Mute users\n"
                        "• Create channels & roles\n"
                        "• Change bot status/nickname\n"
                        "• Full Discord API access!\n\n"
                        "**💡 Examples:**\n"
                        "`@Ophelia avatar dikhao @user`\n"
                        "`@Ophelia isko timeout do 10 min`\n"
                        "`@Ophelia status set karo playing Minecraft`\n"
                        "`@Ophelia channel banao memes`\n\n"
                        "Mazaa aayega! 😎🔥"
                    ),
                    color=discord.Color.magenta()  # Ophelia's color!
                )
                
                embed.add_field(
                    name="⚡ Natural Commands",
                    value="Koi `/cmd` nahi - seedha **bol do** aur main samajh jaati hoon!",
                    inline=False
                )
                
                embed.set_footer(text="Made with ❤️ | Use /ai help for more info")
                embed.set_thumbnail(url=self.user.avatar.url if self.user.avatar else None)
                
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
        elif isinstance(error, commands.NotOwner):
            await ctx.send("❌ Sirf owners ye command use kar sakte hain!", ephemeral=True)
        else:
            logger.error(f"Command error: {error}")
            await ctx.send(f"❌ Error: {str(error)}", ephemeral=True)


async def main():
    """Main entry point"""
    # Create and run bot
    bot = OpheliaBot()
    
    try:
        await bot.start(config.token)
    except KeyboardInterrupt:
        logger.info("🛑 Shutting down Ophelia AI 2.0...")
        await bot.close()
    except discord.LoginFailure:
        logger.error("❌ Invalid Discord token! Check your .env file")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        raise


if __name__ == "__main__":
    # Run the bot
    asyncio.run(main())


# Import datetime for start_time
from datetime import datetime
