"""
Ophelia AI 3.0 - PRODUCTION GRADE Discord Bot
================================================

COMPLETE REWRITE with:
✅ Hierarchical Permission System (OWNER > ADMIN > MOD > MEMBER)
✅ Safety System (Confirmations, Audit Logging, Rollback)
✅ Structured Observability (Logging, Metrics, Error Tracking)
✅ Enhanced Tool Registry with Metadata
✅ Guaranteed Tool Execution (No more fake responses!)
✅ Memory Persistence across restarts
✅ Only replies on mention (configurable)

Architecture:
- src/core/permissions.py - Permission system
- src/safety/system.py - Safety & audit
- src/observability/logger.py - Structured logging
- src/tools/registry.py - Tool registry
- src/handlers/ai_handler_v3.py - Production AI handler
- src/handlers/message_handler.py - Message processing

Author: Production-Grade Implementation
"""
import discord
from discord.ext import commands
import logging
import asyncio
import sys
import os
from datetime import datetime

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import config, is_owner, get_owners
from src.utils.database import init_database, get_db
from src.utils.cache import init_cache, get_cache
from src.utils.groq_client import init_groq_client, get_groq_client

# NEW: Production-grade imports
from src.core.permissions import init_permission_checker, set_owner_ids
from src.safety.system import init_safety_system
from src.observability.logger import init_observability, get_observability, EventType
from src.tools import get_tool_executor, get_registry
from src.handlers.ai_handler_v3 import init_ai_handler_v3, get_ai_handler_v3  # 🚀 V3!
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
    """
    Ophelia AI 3.0 - PRODUCTION-GRADE Discord Bot
    
    Features:
    - Full Discord API access via MCP-style tools
    - Hierarchical permission system
    - Safety checks on dangerous actions
    - Complete audit trail
    - Memory persistence across restarts
    """
    
    def __init__(self):
        # Set up intents - we need ALL of them for full functionality!
        intents = discord.Intents.default()
        intents.message_content = True      # Read message content (CRITICAL!)
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
        """Called when bot is starting up - initialize ALL components"""
        logger.info("🚀 Ophelia AI 3.0 (Production Grade) starting up...")
        self.start_time = datetime.utcnow()
        
        try:
            # ==========================================
            # PHASE 1: Configuration Validation
            # ==========================================
            
            if not config.token:
                logger.error("❌ No Discord token provided! Check .env file")
                return
            
            if not config.has_valid_groq_keys:
                logger.error("❌ No valid Groq API keys provided!")
                return
            
            logger.info(f"👑 Owners: {config.owner_ids}")
            
            # ==========================================
            # PHASE 2: Core Infrastructure
            # ==========================================
            
            # Initialize database connection
            logger.info("📦 Connecting to Supabase...")
            db = init_database(config.supabase_url, config.supabase_key)
            
            # Initialize cache with persistence
            logger.info("⚡ Initializing persistent cache...")
            cache = init_cache(ttl=config.cache_ttl)
            
            # Warm up cache from database
            await cache.warmup_from_database(db)
            
            # ==========================================
            # PHASE 3: Production Systems (NEW!)
            # ==========================================
            
            # Initialize Permission System
            logger.info("🔒 Initializing permission system...")
            perm_checker = init_permission_checker(owner_ids=config.owner_ids)
            set_owner_ids(config.owner_ids)
            logger.info(f"   ✅ Permission levels: OWNER > ADMIN > MODERATOR > MEMBER")
            
            # Initialize Safety System
            logger.info("🛡️ Initializing safety system...")
            safety = init_safety_system(storage_path="./data/safety")
            logger.info(f"   ✅ Confirmations, audit logging, rollback ready")
            
            # Initialize Observability
            logger.info("📊 Initializing observability...")
            obs = init_observability(log_dir="./data/logs")
            obs.log_event(EventType.SYSTEM_STARTUP, "Ophelia AI 3.0 starting up")
            logger.info(f"   ✅ Structured logging enabled")
            
            # ==========================================
            # PHASE 4: AI & Tools
            # ==========================================
            
            # Initialize Groq client with multi-key support
            logger.info(f"🔑 Initializing Groq client ({len(config.groq_api_keys)} keys)...")
            groq = init_groq_client(config.groq_api_keys)
            
            # Test API connection
            connected, msg = await groq.test_connection()
            if connected:
                logger.info(f"✅ {msg}")
            else:
                logger.warning(f"⚠️ {msg}")
            
            # Initialize AI Handler V3 (PRODUCTION GRADE)
            logger.info("🧠 Initializing AI Handler V3...")
            ai_v3 = init_ai_handler_v3()
            logger.info(f"   ✅ Anti-hallucination enabled")
            logger.info(f"   ✅ Tool execution guaranteed")
            
            # Initialize message handler
            msg_handler = init_message_handler(self)
            
            # Initialize meta-command system (legacy /cmd support)
            meta = init_meta_commands(self)
            
            # Initialize natural language command parser
            logger.info("🗣️ Initializing natural language command parser...")
            natural = init_natural_commands(self)
            
            # Initialize Tool Executor with bot access
            logger.info("🛠️ Initializing MCP Tool System...")
            tool_exec = get_tool_executor(bot=self)
            logger.info(f"   ✅ {len(tool_exec.tool_names)} tools registered")
            logger.info(f"   ✅ Tools: {', '.join(tool_exec.tool_names[:6])}{'...' if len(tool_exec.tool_names) > 6 else ''}")
            
            # Load cogs/commands
            logger.info("📦 Loading commands...")
            await self.load_extension("src.commands.settings")
            
            # ==========================================
            # PHASE 5: Ready Check
            # ==========================================
            
            self.initialized = True
            
            logger.info("=" * 60)
            logger.info("✅ OPHELIA AI 3.0 FULLY INITIALIZED!")
            logger.info("=" * 60)
            logger.info("Systems loaded:")
            logger.info("  • Database (Supabase)")
            logger.info("  • Persistent Cache (File-based)")
            logger.info("  • Groq Multi-model Client")
            logger.info("  • Permission System (Hierarchical)")
            logger.info("  • Safety System (Audit + Confirmations)")
            logger.info("  • Observability (Structured Logging)")
            logger.info("  • Tool Registry (11+ tools)")
            logger.info("  • AI Handler V3 (Anti-hallucination)")
            logger.info("=" * 60)
            
        except Exception as e:
            logger.error(f"❌ Error during startup: {e}")
            import traceback
            traceback.print_exc()
    
    async def on_ready(self):
        """Called when bot is ready and connected"""
        if not self.initialized:
            logger.error("❌ Bot not properly initialized!")
            return
        
        obs = get_observability()
        
        logger.info("=" * 60)
        logger.info(f"🤖 **OPHELIA AI 3.0** IS ONLINE!")
        logger.info(f"📊 Serving {len(self.guilds)} servers")
        logger.info(f"🆔 Bot ID: {self.user.id}")
        logger.info(f"👑 Owners: {len(config.owner_ids)} users with FULL ACCESS")
        logger.info(f"🗣️ Natural Language Commands: ENABLED")
        logger.info(f"🛠️ MCP Tool Calling: ENABLED (Production Grade!)")
        logger.info(f"🔒 Permission System: ACTIVE")
        logger.info(f"🛡️ Safety System: ACTIVE")
        logger.info(f"📊 Observability: ACTIVE")
        logger.info("=" * 60)
        
        obs.log_event(
            EventType.SYSTEM_STARTUP,
            f"Bot online! Serving {len(self.guilds)} guilds",
            context={"guild_count": len(self.guilds), "bot_id": self.user.id}
        )
        
        # Update presence
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.playing,
                name="Bolo 'timeout do' ya 'channel banao' | @me only"
            )
        )
    
    async def on_message(self, message: discord.Message):
        """
        Main message handler.
        
        CRITICAL: Only responds when:
        1. User @mentions the bot, OR
        2. User is an owner, OR
        3. Message is in an AI channel, OR
        4. Message is a DM
        """
        # Don't process until fully initialized
        if not self.initialized:
            return
        
        # Ignore bots (including ourselves)
        if message.author.bot:
            return
        
        # Process regular commands first (prefix commands like !help)
        await self.process_commands(message)
        
        # Then handle AI message processing
        try:
            handler = get_message_handler()
            await handler.handle_message(message)
        except Exception as e:
            logger.error(f"Error in message handler: {e}", exc_info=True)
    
    async def on_guild_join(self, guild: discord.Guild):
        """Called when bot joins a new server"""
        logger.info(f"🎉 Joined new server: {guild.name} ({guild.id})")
        
        # Create default settings for this guild
        try:
            db = get_db()
            from config.settings import DEFAULT_GUILD_SETTINGS
            await db.upsert_guild_settings(guild.id, DEFAULT_GUILD_SETTINGS.copy())
            
            # Try to send welcome message
            channel = guild.system_channel or next(
                (ch for ch in guild.text_channels if ch.permissions_for(guild.me).send_messages),
                None
            )
            
            if channel:
                embed = discord.Embed(
                    title="🤖✨ OPHELIA AI 3.0 AA GAYI! ✨",
                    description=(
                        "Main **Ophelia AI 3.0** hoon - Production Grade Discord AI!\n\n"
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
                        "• Full Discord API access!\n\n"
                        "**🆕 v3 FEATURES:**\n"
                        "• ✅ Real tool execution (no fake replies!)\n"
                        "• 🔒 Permission system\n"
                        "• 🛡️ Safety confirmations\n"
                        "• 📊 Audit logging\n\n"
                        "**💡 Examples:**\n"
                        "`@Ophelia avatar dikhao @user`\n"
                        "`@Ophelia isko timeout do 10 min`\n"
                        "`@Ophelia channel banao memes`\n\n"
                        "Mazaa aayega! 😎🔥"
                    ),
                    color=discord.Color.magenta()
                )
                
                embed.add_field(
                    name="⚡ Natural Commands",
                    value="Koi `/cmd` nahi - seedha **bol do** aur main samajh jaati hoon!",
                    inline=False
                )
                
                embed.add_field(
                    name="🔒 Security",
                    value="Only mentions get replies | Owners have full access",
                    inline=False
                )
                
                embed.set_footer(text="Ophelia AI 3.0 | Production Grade | Made with ❤️")
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
    bot = OpheliaBot()
    
    try:
        await bot.start(config.token)
    except KeyboardInterrupt:
        logger.info("🛑 Shutting down Ophelia AI 3.0...")
        
        # Graceful shutdown - save any pending data
        obs = get_observability()
        obs.log_event(EventType.SYSTEM_SHUTDOWN, "Bot shutting down gracefully")
        
        await bot.close()
    except discord.LoginFailure:
        logger.error("❌ Invalid Discord token! Check your .env file")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        raise


if __name__ == "__main__":
    # Run the bot
    asyncio.run(main())
