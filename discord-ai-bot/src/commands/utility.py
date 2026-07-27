"""
Utility Commands - Help, Info, and other useful commands
"""
import discord
from discord import app_commands
from discord.ext import commands
import logging
import platform
from datetime import datetime

from config.settings import config, SYSTEM_PROMPTS
from src.utils.groq_client import get_groq_client

logger = logging.getLogger("Commands")


@app_commands.guild_only()
class UtilityCog(commands.GroupCog, group_name="ai"):
    """AI Utility commands"""
    
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="help", description="📚 Help commands dekho")
    async def ai_help(self, interaction: discord.Interaction):
        """Show help embed with all available commands"""
        
        embed = discord.Embed(
            title="🤖 AI Bot Help",
            color=discord.Color.blurple(),
            description="Sab commands jo tum use kar sakte ho!"
        )
        
        # Basic Usage Section
        embed.add_field(
            name="💬 Basic Chatting",
            value=(
                "Sirf **@mention** karo aur baat shuru!\n"
                "`@BotName Hi!`\n"
                "`@BotName Make me a joke`\n"
                "`@BotName Code bana do`"
            ),
            inline=False
        )
        
        # Settings Section
        embed.add_field(
            name="⚙️ Settings (Mods Only)",
            value=(
                "`/ai setting` - Full settings panel\n"
                "`/ai status` - Current status dekho\n"
                "Dropdowns se sab change karo!"
            ),
            inline=False
        )
        
        # Meta Commands Section
        embed.add_field(
            name="⚡ Meta Commands (AI Power)",
            value=(
                "AI ko commands execute karwa sakte ho:\n"
                "`/cmd say [channel] \"msg\"`\n"
                "`/cmd embed \"title\" \"desc\"`\n"
                "`/cmd clear [count]`\n"
                "`/cmd kick/ban @user` (mods)"
            ),
            inline=False
        )
        
        # Tips Section
        embed.add_field(
            name="💡 Pro Tips",
            value=(
                "• **AI Channel** set karo for auto-reply\n"
                "• **Memory** on rakho for better convos\n"
                "• **Personality** change karo as per mood\n"
                "• Multiple **API keys** use karo for backup"
            ),
            inline=False
        )
        
        embed.set_footer(text="Mazaa aayega! 😎 • Made with ❤️")
        embed.set_thumbnail(url=self.bot.user.avatar.url if self.bot.user.avatar else None)
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @app_commands.command(name="info", description="ℹ️ Bot info dekho")
    async def ai_info(self, interaction: discord.Interaction):
        """Show bot information"""
        
        try:
            groq = get_groq_client()
            api_status = f"✅ {groq.available_keys_count} keys loaded"
        except:
            api_status = "❌ Not initialized"
        
        uptime = datetime.utcnow() - self.bot.start_time if hasattr(self.bot, 'start_time') else "Unknown"
        
        embed = discord.Embed(
            title="🤖 Bot Information",
            color=discord.Color.green(),
            description="Bot ke baare me sab kuch!"
        )
        
        embed.add_field(name="🆔 Bot ID", value=f"`{self.bot.user.id}`", inline=True)
        embed.add_field(name="📊 Servers", value=f"`{len(self.bot.guilds)}`", inline=True)
        embed.add_field(name="👥 Users", value=f"`{sum(g.member_count for g in self.bot.guilds)}`", inline=True)
        embed.add_field(name="🔑 API Status", value=api_status, inline=True)
        embed.add_field(name="🐍 Python", value=f"`{platform.python_version()}`", inline=True)
        embed.add_field(name="📦 discord.py", value=f"`{discord.__version__}`", inline=True)
        
        embed.add_field(
            name="🤖 Model",
            value=f"`{config.default_model}`",
            inline=True
        )
        
        embed.set_footer(text="Made with Groq API + Supabase + 💖")
        embed.set_thumbnail(url=self.bot.user.avatar.url if self.bot.user.avatar else None)
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @app_commands.command(name="ping", description="🏓 Bot latency check karo")
    async def ai_ping(self, interaction: discord.Interaction):
        """Check bot latency"""
        
        # Measure real latency
        start = datetime.timestamp(datetime.now())
        await interaction.response.defer(ephemeral=True)
        end = datetime.timestamp(datetime.now())
        latency_ms = int((end - start) * 1000)
        
        # WebSocket latency
        ws_latency = int(self.bot.latency * 1000)
        
        embed = discord.Embed(
            title="🏓 Pong!",
            color=discord.Color.green() if latency_ms < 500 else discord.Color.orange()
        )
        
        embed.add_field(name="⏱️ Response Time", value=f"`{latency_ms}ms`", inline=True)
        embed.add_field(name="🌐 WebSocket", value=f"`{ws_latency}ms`", inline=True)
        
        # Status based on latency
        if latency_ms < 200:
            status = "⚡ Super Fast!"
        elif latency_ms < 500:
            status = "✅ Good!"
        else:
            status = "😅 A bit slow..."
        
        embed.description = status
        
        await interaction.followup.send(embed=embed, ephemeral=True)
    
    @app_commands.command(
        name="clear_memory", 
        description="🧹 Conversation memory clear karo (Mods only)"
    )
    async def clear_memory(
        self, 
        interaction: discord.Interaction,
        confirm: bool = False
    ):
        """Clear conversation history for current channel"""
        
        # Check mod permissions
        user = interaction.user
        is_mod = (
            interaction.guild.owner_id == user.id or
            user.guild_permissions.manage_guild or
            user.guild_permissions.administrator
        )
        
        if not is_mod:
            await interaction.response.send_message(
                "❌ Sirf mods memory clear kar sakte hain!",
                ephemeral=True
            )
            return
        
        if not confirm:
            embed = discord.Embed(
                title="⚠️ Confirm Memory Clear",
                description=(
                    "Kya tum sure ho ki is channel ki conversation memory clear karni hai?\n\n"
                    "Ye action **undo nahi** ho sakta!\n\n"
                    "Confirm karne ke liye `confirm: True` select karo."
                ),
                color=discord.Color.orange()
            )
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        try:
            from src.utils.database import get_db
            from src.utils.cache import get_cache
            
            db = get_db()
            cache = get_cache()
            
            # Clear from database
            success = await db.clear_conversation_history(
                interaction.guild.id,
                interaction.channel.id
            )
            
            # Clear from cache
            cache.clear_conversation(interaction.channel.id)
            
            if success:
                embed = discord.Embed(
                    title="✅ Memory Cleared!",
                    description=f"#{interaction.channel.name} ki conversation memory clear ho gayi!",
                    color=discord.Color.green()
                )
            else:
                embed = discord.Embed(
                    title="⚠️ Partial Success",
                    description="Cache to clear ho gaya but database me issue aa sakti hai.",
                    color=discord.Color.orange()
                )
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error clearing memory: {e}")
            await interaction.response.send_message(
                f"❌ Error clearing memory: {str(e)}",
                ephemeral=True
            )
    
    @app_commands.command(name="personalities", description="😄 Available personalities dekho")
    async def show_personalities(self, interaction: discord.Interaction):
        """Show all available personality options with previews"""
        
        embed = discord.Embed(
            title="😄 Available Personalities",
            color=discord.Color.purple(),
            description="Change karo `/ai setting` → Personality se!"
        )
        
        for key, prompt in SYSTEM_PROMPTS.items():
            # Get first 150 chars of personality as preview
            preview = prompt[:200].replace("\n", " ") + "..."
            
            emojis = {"fun": "😄", "professional": "💼", "casual": "🙂"}
            
            embed.add_field(
                name=f"{emojis.get(key, '🤖')} {key.title()}",
                value=f"```{preview}```",
                inline=False
            )
        
        embed.set_footer(text="Use /ai setting → Personality to change!")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot):
    """Setup function to add the cog to bot"""
    await bot.add_cog(UtilityCog(bot))
    logger.info("✅ Utility Cog loaded!")
