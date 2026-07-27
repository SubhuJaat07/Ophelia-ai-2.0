"""
Ophelia AI 2.0 Settings Command - /ai setting
Owner & Mod-only command with dropdown menus for server configuration
"""
import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional
import logging

from config.settings import DEFAULT_GUILD_SETTINGS, SYSTEM_PROMPTS, is_owner, config
from src.utils.database import get_db
from src.utils.cache import get_cache
from src.handlers.ai_handler import get_ai_handler

logger = logging.getLogger("Settings")


def check_is_mod():
    """Check if user has moderation permissions OR is owner"""
    async def predicate(interaction: discord.Interaction) -> bool:
        if not interaction.guild:
            await interaction.response.send_message(
                "❌ Ye command sirf servers me kaam karegi!", ephemeral=True
            )
            return False
        
        user = interaction.user
        
        # Owners always have access!
        if is_owner(user.id):
            return True
        
        # Check mod permissions
        is_admin = interaction.guild.owner_id == user.id
        has_mod_perms = user.guild_permissions.manage_guild or user.guild_permissions.administrator
        
        if not (is_admin or has_mod_perms):
            await interaction.response.send_message(
                "❌ Sirf Mods/Admins/Owners hi settings change kar sakte hain!", ephemeral=True
            )
            return False
        
        return True
    
    return app_commands.check(predicate)


class SettingsView(discord.ui.View):
    """Interactive settings view with dropdowns and buttons - Ophelia AI 2.0"""
    
    def __init__(self, guild_id: int, original_response: discord.Message = None):
        super().__init__(timeout=300)  # 5 minute timeout
        self.guild_id = guild_id
        self.original_response = original_response
    
    async def _get_settings(self) -> dict:
        """Get current guild settings"""
        ai = get_ai_handler()
        return await ai.get_guild_settings(self.guild_id)
    
    async def _save_settings(self, **updates):
        """Save updated settings to cache and database"""
        ai = get_ai_handler()
        db = get_db()
        cache = get_cache()
        
        current = await self._get_settings()
        current.update(updates)
        
        # Update both cache and DB
        cache.set_guild_settings(self.guild_id, current)
        await db.upsert_guild_settings(self.guild_id, current)
    
    @discord.ui.select(
        placeholder="🎛️ Select Setting to Change...",
        min_values=1,
        max_values=1,
        options=[
            discord.SelectOption(
                label="🤖 AI Toggle",
                description="AI on/off karo",
                value="toggle_ai"
            ),
            discord.SelectOption(
                label="🌡️ Temperature",
                description="Response creativity (0.0 - 2.0)",
                value="temperature"
            ),
            discord.SelectOption(
                label="📝 Custom Instructions",
                description="Custom system prompt add karo",
                value="instructions"
            ),
            discord.SelectOption(
                label="🔔 Ping Reply",
                description="@mention pe reply on/off",
                value="ping_reply"
            ),
            discord.SelectOption(
                label="📢 Everyone Ping Reply",
                description="@everyone/@here pe reply on/off",
                value="everyone_ping"
            ),
            discord.SelectOption(
                label="💬 AI Channel",
                description="Bina ping ke AI reply channel set karo",
                value="ai_channel"
            ),
            discord.SelectOption(
                label="😄 Personality",
                description="Bot personality change karo (fun/professional/casual)",
                value="personality"
            ),
            discord.SelectOption(
                label="🧠 Memory",
                description="Long-term memory on/off",
                value="memory"
            ),
            discord.SelectOption(
                label="⚡ Natural Commands",
                description="Natural language commands on/off",
                value="natural_commands"
            ),
            discord.SelectOption(
                label="🔒 Require Mention",
                description="Mention zaroori hai ya nahi",
                value="require_mention"
            ),
        ]
    )
    async def settings_select_callback(self, interaction: discord.Interaction, select: discord.ui.Select):
        """Handle setting selection from dropdown"""
        selected = select.values[0]
        settings = await self._get_settings()
        
        if selected == "toggle_ai":
            new_val = not settings.get("enabled", True)
            await self._save_settings(enabled=new_val)
            
            embed = self._create_settings_embed(await self._get_settings())
            embed.add_field(
                name="✅ AI Toggled!",
                value=f"AI ab {'**ON** 🟢' if new_val else '**OFF** 🔴'} hai!",
                inline=False
            )
            await interaction.response.edit_message(embed=embed, view=self)
        
        elif selected == "temperature":
            modal = TemperatureModal(self.guild_id, self)
            await interaction.response.send_modal(modal)
        
        elif selected == "instructions":
            modal = InstructionsModal(self.guild_id, self)
            await interaction.response.send_modal(modal)
        
        elif selected == "ping_reply":
            new_val = not settings.get("ping_reply_enabled", True)
            await self._save_settings(ping_reply_enabled=new_val)
            
            embed = self._create_settings_embed(await self._get_settings())
            status = "**ON** ✅" if new_val else "**OFF** ❌"
            embed.add_field(
                name="🔔 Ping Reply Updated",
                value=f"@mention pe reply ab {status}",
                inline=False
            )
            await interaction.response.edit_message(embed=embed, view=self)
        
        elif selected == "everyone_ping":
            new_val = not settings.get("everyone_ping_reply", False)
            await self._save_settings(everyone_ping_reply=new_val)
            
            embed = self._create_settings_embed(await self._get_settings())
            status = "**ON** 📢" if new_val else "**OFF** 🔕"
            embed.add_field(
                name="📢 Everyone Ping Updated",
                value=f"@everyone/@here pe reply ab {status}",
                inline=False
            )
            await interaction.response.edit_message(embed=embed, view=self)
        
        elif selected == "ai_channel":
            modal = AIChannelModal(self.guild_id, self)
            await interaction.response.send_modal(modal)
        
        elif selected == "personality":
            select_view = PersonalitySelect(self.guild_id, self)
            embed = self._create_settings_embed(await self._get_settings())
            embed.add_field(
                name="😄 Select Personality",
                value="Niche se personality choose karo:",
                inline=False
            )
            await interaction.response.edit_message(embed=embed, view=select_view)
        
        elif selected == "memory":
            new_val = not settings.get("memory_enabled", True)
            await self._save_settings(memory_enabled=new_val)
            
            embed = self._create_settings_embed(await self._get_settings())
            status = "**ON** 🧠" if new_val else "**OFF** 🧹"
            embed.add_field(
                name="🧠 Memory Updated",
                value=f"Long-term memory ab {status}",
                inline=False
            )
            await interaction.response.edit_message(embed=embed, view=self)
        
        elif selected == "natural_commands":
            new_val = not settings.get("natural_language_commands", True)
            await self._save_settings(natural_language_commands=new_val)
            
            embed = self._create_settings_embed(await self._get_settings())
            status = "**ON** 🗣️" if new_val else "**OFF** 🔕"
            embed.add_field(
                name="⚡ Natural Commands Updated",
                value=f"Natural language commands ab {status}",
                inline=False
            )
            await interaction.response.edit_message(embed=embed, view=self)
        
        elif selected == "require_mention":
            new_val = not settings.get("require_mention", True)
            await self._save_settings(require_mention=new_val)
            
            embed = self._create_settings_embed(await self._get_settings())
            status = "**ON** ✅" if new_val else "**OFF** ❌"
            embed.add_field(
                name="🔒 Mention Requirement Updated",
                value=f"Mention ab {'zaroori' if new_val else 'zaroori NAHI'} hai (owners ko hamesha kaam karega!)",
                inline=False
            )
            await interaction.response.edit_message(embed=embed, view=self)
    
    def _create_settings_embed(self, settings: dict) -> discord.Embed:
        """Create embed showing all current settings"""
        enabled_emoji = "🟢 ON" if settings.get("enabled", True) else "🔴 OFF"
        ping_emoji = "✅" if settings.get("ping_reply_enabled", True) else "❌"
        everyone_emoji = "✅" if settings.get("everyone_ping_reply", False) else "❌"
        memory_emoji = "🟢" if settings.get("memory_enabled", True) else "🔴"
        natural_emoji = "✅" if settings.get("natural_language_commands", True) else "❌"
        mention_emoji = "✅" if settings.get("require_mention", True) else "❌"
        
        ai_channels = settings.get("ai_channel_ids", [])
        channel_list = "\n".join([f"<#{cid}>" for cid in ai_channels]) if ai_channels else "*None*"
        
        personality = settings.get("personality", "fun")
        personality_emojis = {"fun": "😄", "professional": "💼", "casual": "🙂"}
        
        embed = discord.Embed(
            title="⚙️ Ophelia AI 2.0 - Server Settings",
            color=discord.Color.blurple(),
            description=f"**Server ID:** `{self.guild_id}`\n👑 **Owners**: <@1169492860278669312>, <@1463113729959919801>, <@1443836576802013316>\n\nDropdown se setting choose karo!"
        )
        
        embed.add_field(
            name=f"🤖 AI Status: {enabled_emoji}",
            value="Bot active hai ya nahi",
            inline=True
        )
        embed.add_field(
            name=f"🌡️ Temperature: {settings.get('temperature', 1.02)}",
            value="Response creativity level",
            inline=True
        )
        embed.add_field(
            name=f"😄 Personality: {personality_emojis.get(personality, '😄')} {personality.title()}",
            value="Bot ka style",
            inline=True
        )
        
        embed.add_field(
            name=f"🔔 Ping Reply: {ping_emoji}",
            value="@mention pe respond karega",
            inline=True
        )
        embed.add_field(
            name=f"📢 Everyone Ping: {everyone_emoji}",
            value="@everyone/@here pe respond karega",
            inline=True
        )
        embed.add_field(
            name=f"🧠 Memory: {memory_emoji}",
            value="Long-term yaad rakhega",
            inline=True
        )
        
        embed.add_field(
            name=f"⚡ Natural Commands: {natural_emoji}",
            value="'Avatar dikhao' jaise commands samjhega",
            inline=True
        )
        embed.add_field(
            name=f"🔒 Require Mention: {mention_emoji}",
            value="Mention zaroori? (Owners ko nahi!)",
            inline=True
        )
        embed.add_field(
            name="💬 AI Channels",
            value=channel_list,
            inline=False
        )
        
        instructions = settings.get("custom_instructions", "")
        if instructions:
            preview = instructions[:200] + "..." if len(instructions) > 200 else instructions
            embed.add_field(
                name="📝 Custom Instructions",
                value=f"```{preview}```",
                inline=False
            )
        
        embed.set_footer(text="Settings automatically save ho jaati hain! • Owners ko full access!")
        embed.set_thumbnail(url="https://cdn.discordapp.com/embed/avatars/0.png")
        
        return embed


class TemperatureModal(discord.ui.Modal, title="🌡️ Set Temperature"):
    """Modal for setting temperature value"""
    
    def __init__(self, guild_id: int, parent_view: SettingsView):
        super().__init__()
        self.guild_id = guild_id
        self.parent_view = parent_view
    
    temp_input = discord.ui.TextInput(
        label="Temperature (0.0 - 2.0)",
        placeholder="1.02 = normal, 2.0 = crazy creative, 0.0 = serious",
        default="1.02",
        min_length=1,
        max_length=4,
        required=True
    )
    
    async def on_submit(self, interaction: discord.Interaction):
        try:
            temp = float(self.temp_input.value)
            temp = max(0.0, min(2.0, temp))  # Clamp between 0-2
            
            ai = get_ai_handler()
            db = get_db()
            cache = get_cache()
            
            settings = await ai.get_guild_settings(self.guild_id)
            settings["temperature"] = temp
            
            cache.set_guild_settings(self.guild_id, settings)
            await db.upsert_guild_settings(self.guild_id, settings)
            
            embed = self.parent_view._create_settings_embed(settings)
            embed.add_field(
                name="✅ Temperature Updated!",
                value=f"Ab temperature **{temp}** hai!",
                inline=False
            )
            await interaction.response.edit_message(embed=embed, view=self.parent_view)
            
        except ValueError:
            await interaction.response.send_message(
                "❌ Valid number daalo bhai! (0.0 se 2.0 ke beech)",
                ephemeral=True
            )


class InstructionsModal(discord.ui.Modal, title="📝 Set Custom Instructions"):
    """Modal for setting custom instructions"""
    
    def __init__(self, guild_id: int, parent_view: SettingsView):
        super().__init__()
        self.guild_id = guild_id
        self.parent_view = parent_view
    
    instructions_input = discord.ui.TextInput(
        label="Custom Instructions",
        placeholder="E.g.: Always respond in Hindi, be very sarcastic, talk like a pirate...",
        style=discord.TextStyle.paragraph,
        default="",
        min_length=0,
        max_length=1000,
        required=False
    )
    
    async def on_submit(self, interaction: discord.Interaction):
        instructions = self.instructions_input.value
        
        ai = get_ai_handler()
        db = get_db()
        cache = get_cache()
        
        settings = await ai.get_guild_settings(self.guild_id)
        settings["custom_instructions"] = instructions
        
        cache.set_guild_settings(self.guild_id, settings)
        await db.upsert_guild_settings(self.guild_id, settings)
        
        embed = self.parent_view._create_settings_embed(settings)
        if instructions:
            embed.add_field(
                name="✅ Instructions Updated!",
                value="Custom instructions save ho gayi!",
                inline=False
            )
        else:
            embed.add_field(
                name="🗑️ Instructions Cleared!",
                value="Custom instructions hata di!",
                inline=False
            )
        await interaction.response.edit_message(embed=embed, view=self.parent_view)


class AIChannelModal(discord.ui.Modal, title="💬 Set AI Channel"):
    """Modal for setting AI auto-reply channels"""
    
    def __init__(self, guild_id: int, parent_view: SettingsView):
        super().__init__()
        self.guild_id = guild_id
        self.parent_view = parent_view
    
    channel_input = discord.ui.TextInput(
        label="Channel IDs (comma separated)",
        placeholder="123456789, 987654321\n(Channels jahan bina ping ke bot reply kare)",
        style=discord.TextStyle.paragraph,
        default="",
        min_length=0,
        max_length=500,
        required=False
    )
    
    async def on_submit(self, interaction: discord.Interaction):
        raw = self.channel_input.value.strip()
        
        if raw:
            channel_ids = [int(cid.strip()) for cid in raw.split(",") if cid.strip().isdigit()]
        else:
            channel_ids = []
        
        ai = get_ai_handler()
        db = get_db()
        cache = get_cache()
        
        settings = await ai.get_guild_settings(self.guild_id)
        settings["ai_channel_ids"] = channel_ids
        
        cache.set_guild_settings(self.guild_id, settings)
        await db.upsert_guild_settings(self.guild_id, settings)
        
        embed = self.parent_view._create_settings_embed(settings)
        if channel_ids:
            embed.add_field(
                name="✅ AI Channels Updated!",
                value=f"{len(channel_ids)} channels set kiye!",
                inline=False
            )
        else:
            embed.add_field(
                name="🗑️ AI Channels Cleared!",
                value="Ab koi AI channel nahi hai",
                inline=False
            )
        await interaction.response.edit_message(embed=embed, view=self.parent_view)


class PersonalitySelect(discord.ui.View):
    """Sub-view for personality selection"""
    
    def __init__(self, guild_id: int, parent_view: SettingsView):
        super().__init__(timeout=60)
        self.guild_id = guild_id
        self.parent_view = parent_view
    
    @discord.ui.select(
        placeholder="😄 Choose Personality...",
        min_values=1,
        max_values=1,
        options=[
            discord.SelectOption(label="😄 Fun & Funny", description="Hasi-mazaak, roasting, memes!", value="fun"),
            discord.SelectOption(label="💼 Professional", description="Serious, helpful, formal", value="professional"),
            discord.SelectOption(label="🙂 Casual & Friendly", description="Relaxed, friendly vibes", value="casual"),
        ]
    )
    async def personality_select(self, interaction: discord.Interaction, select: discord.ui.Select):
        personality = select.values[0]
        
        ai = get_ai_handler()
        db = get_db()
        cache = get_cache()
        
        settings = await ai.get_guild_settings(self.guild_id)
        settings["personality"] = personality
        
        cache.set_guild_settings(self.guild_id, settings)
        await db.upsert_guild_settings(self.guild_id, settings)
        
        embed = self.parent_view._create_settings_embed(settings)
        embed.add_field(
            name="✅ Personality Changed!",
            value=f"Ab bot **{personality}** mode me hai!",
            inline=False
        )
        await interaction.response.edit_message(embed=embed, view=self.parent_view)


@app_commands.guild_only()
class SettingsCog(commands.GroupCog, group_name="ai"):
    """AI Settings commands group - Ophelia AI 2.0"""
    
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="setting", description="⚙️ AI Bot Settings (Mods/Owners only!)")
    @check_is_mod()
    async def ai_setting(self, interaction: discord.Interaction):
        """
        Main settings command - shows interactive settings panel.
        Only users with Manage Server permission or owners can use this.
        """
        logger.info(f"🎛️ {interaction.user} opened settings for guild {interaction.guild.id}")
        
        # Create initial embed with current settings
        ai = get_ai_handler()
        settings = await ai.get_guild_settings(interaction.guild.id)
        
        view = SettingsView(guild_id=interaction.guild.id)
        embed = view._create_settings_embed(settings)
        
        await interaction.response.send_message(
            embed=embed,
            view=view,
            ephemeral=False
        )
    
    @app_commands.command(name="status", description="📊 Current AI Status dekho")
    async def ai_status(self, interaction: discord.Interaction):
        """Quick status check for anyone"""
        ai = get_ai_handler()
        settings = await ai.get_guild_settings(interaction.guild.id)
        
        enabled = settings.get("enabled", True)
        status_emoji = "🟢 Online" if enabled else "🔴 Offline"
        personality = settings.get("personality", "fun")
        natural_on = settings.get("natural_language_commands", True)
        
        embed = discord.Embed(
            title=f"🤖 Ophelia AI 2.0 Status: {status_emoji}",
            color=discord.Color.green() if enabled else discord.Color.red()
        )
        
        embed.add_field(name="Personality", value=personality.title(), inline=True)
        embed.add_field(name="Temperature", value=str(settings.get('temperature', 1.02)), inline=True)
        embed.add_field(name="Memory", value="🟢 On" if settings.get('memory_enabled') else "🔴 Off", inline=True)
        embed.add_field(name="Natural Commands", value="✅ On" if natural_on else "❌ Off", inline=True)
        embed.add_field(name="You're Owner?", value="👑 YES!" if is_owner(interaction.user.id) else "❌ No", inline=True)
        
        embed.set_footer(text="Use /ai setting for more options | Natural commands: 'avatar dikhao' etc.")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @app_commands.command(name="owners", description="👑 Bot Owners dekho")
    async def show_owners(self, interaction: discord.Interaction):
        """Show who the bot owners are"""
        embed = discord.Embed(
            title="👑 Ophelia AI 2.0 Owners",
            description="Ye log is bot ke **SUPER OWNERS** hain - unko full power hai!",
            color=discord.Color.gold()
        )
        
        for owner_id in config.owner_ids:
            try:
                owner = await self.bot.fetch_user(owner_id)
                embed.add_field(
                    name=f"👑 {owner.name}#{owner.discriminator}",
                    value=f"`ID: {owner_id}`",
                    inline=True
                )
            except:
                embed.add_field(
                    name="👑 Unknown Owner",
                    value=f"`ID: {owner_id}`",
                    inline=True
                )
        
        embed.set_footer(text="Owners can do ANYTHING with this bot!")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot):
    """Setup function to add the cog to bot"""
    await bot.add_cog(SettingsCog(bot))
    logger.info("✅ Ophelia AI 2.0 Settings Cog loaded!")
