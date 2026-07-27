"""
Meta-Command System - Allows AI to use/execute Discord commands via chat
Users can ask AI to do things, and AI can use /cmd to execute actions
"""
import discord
from discord.ext import commands
import logging
import json
import re
from typing import Optional, Dict, Any

logger = logging.getLogger("MetaCommands")


class MetaCommandParser:
    """Parses and executes meta-commands from AI responses"""
    
    # Available commands that AI can use (FIXED: No more quote conflicts!)
    AVAILABLE_COMMANDS = {
        "say": {
            "description": "Kisi channel me message bhejo",
            "usage": "/cmd say [channel_id] 'message'",
            "example": "/cmd say 123456789 'Hello everyone!'",
            "permissions": ["manage_messages"]
        },
        "react": {
            "description": "Message pe reaction karo",
            "usage": "/cmd react [message_id] :emoji:",
            "example": "/cmd react 123456789 😂",
            "permissions": ["add_reactions"]
        },
        "embed": {
            "description": "Embed bhejo with title, description, color",
            "usage": "/cmd embed 'title' 'description' [color]",
            "example": "/cmd embed 'Announcement' 'Server update!' blue",
            "permissions": ["embed_links"]
        },
        "nickname": {
            "description": "Apna nickname change karo",
            "usage": "/cmd nickname 'new_nickname'",
            "example": "/cmd nickname 'Cool Bot'",
            "permissions": ["change_nickname"]
        },
        "status": {
            "description": "Bot status change karo (playing, listening, watching)",
            "usage": "/cmd status [type] 'text'",
            "example": "/cmd status playing 'Minecraft'",
            "permissions": []  # No special perms needed
        },
        "kick": {
            "description": "User kick karo (mod only)",
            "usage": "/cmd kick @user [reason]",
            "example": "/cmd kick @troll Spamming",
            "permissions": ["kick_members"],
            "mod_only": True
        },
        "ban": {
            "description": "User ban karo (admin only)",
            "usage": "/cmd ban @user [reason]",
            "example": "/cmd ban @hacker Hacking attempt",
            "permissions": ["ban_members"],
            "mod_only": True
        },
        "clear": {
            "description": "Messages delete karo",
            "usage": "/cmd clear [count]",
            "example": "/cmd clear 50",
            "permissions": ["manage_messages"]
        },
        "create_channel": {
            "description": "Naya channel banao",
            "usage": "/cmd create_channel 'name' [type]",
            "example": "/cmd create_channel 'general' text",
            "permissions": ["manage_channels"]
        },
        "create_role": {
            "description": "Naya role banao",
            "usage": "/cmd create_role 'name' [color]",
            "example": "/cmd create_role 'VIP' gold",
            "permissions": ["manage_roles"]
        }
    }
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    async def parse_and_execute(
        self,
        response: str,
        guild: discord.Guild,
        channel: discord.TextChannel,
        author: discord.Member
    ) -> tuple[str, bool]:
        """
        Parse AI response for meta-commands and execute them.
        Returns (cleaned_response, had_commands)
        """
        if "/cmd" not in response:
            return response, False
        
        # Check if meta commands are enabled for this guild
        from src.handlers.ai_handler import get_ai_handler
        ai = get_ai_handler()
        settings = await ai.get_guild_settings(guild.id)
        
        if not settings.get("meta_commands_enabled", True):
            # Remove commands from response but don't execute
            cleaned = re.sub(r'/cmd\s+\w+.*', '', response)
            return cleaned.strip(), True
        
        # Find all /cmd patterns
        cmd_pattern = r'/cmd\s+(\w+)\s*(.*?)(?=/cmd|$)'
        matches = re.findall(cmd_pattern, response, re.DOTALL)
        
        executed_commands = []
        
        for cmd_name, args in matches:
            cmd_name = cmd_name.lower().strip()
            args = args.strip()
            
            # Execute command
            result = await self._execute_command(
                cmd_name, args, guild, channel, author
            )
            
            executed_commands.append(f"[CMD] {cmd_name}: {result}")
        
        # Clean response by removing command syntax
        cleaned_response = re.sub(r'/cmd\s+\w+\s*.*?(?=/cmd|$)', '', response, flags=re.DOTALL).strip()
        
        # Add execution summary if there were results
        if executed_commands and len(executed_commands) <= 3:
            cleaned_response += "\n\n*✅ Commands execute ho gaye!*"
        
        return cleaned_response or "Done! ✅", len(executed_commands) > 0
    
    async def _execute_command(
        self,
        cmd_name: str,
        args: str,
        guild: discord.Guild,
        channel: discord.TextChannel,
        author: discord.Member
    ) -> str:
        """Execute a single meta-command"""
        
        # Check if command exists
        if cmd_name not in self.AVAILABLE_COMMANDS:
            return f"❌ Unknown command: {cmd_name}"
        
        cmd_info = self.AVAILABLE_COMMANDS[cmd_name]
        
        # Check permissions for mod-only commands
        if cmd_info.get("mod_only"):
            if not author.guild_permissions.manage_guild and guild.owner_id != author.id:
                return f"❌ Sirf mods '{cmd_name}' use kar sakte hain!"
        
        try:
            # Route to appropriate handler
            handler = getattr(self, f"_cmd_{cmd_name}", None)
            if handler:
                return await handler(args, guild, channel, author)
            else:
                return f"❌ Command '{cmd_name}' implemented nahi hai"
                
        except Exception as e:
            logger.error(f"Error executing command {cmd_name}: {e}")
            return f"❌ Error: {str(e)[:100]}"
    
    # ==================== COMMAND HANDLERS ====================
    
    async def _cmd_say(self, args: str, guild, channel, author) -> str:
        """Send message to a specific channel"""
        # Parse channel ID and message - support both quotes
        match = re.match(r"(\d+)\s+'(.*)'", args, re.DOTALL)
        if not match:
            match = re.match(r'(\d+)\s+"(.*)"', args, re.DOTALL)
        if not match:
            # Try without quotes
            parts = args.split(maxsplit=1)
            if len(parts) < 2:
                return "❌ Usage: /cmd say [channel_id] 'message'"
            channel_id = int(parts[0])
            message = parts[1]
        else:
            channel_id = int(match.group(1))
            message = match.group(2)
        
        target_channel = guild.get_channel(channel_id)
        if not target_channel:
            return f"❌ Channel {channel_id} nahi mila!"
        
        await target_channel.send(message)
        return f"✅ Message bhej diya #{target_channel.name} me!"
    
    async def _cmd_react(self, args: str, guild, channel, author) -> str:
        """Add reaction to a message"""
        parts = args.split(maxsplit=1)
        if len(parts) < 2:
            return "❌ Usage: /cmd react [message_id] :emoji:"
        
        message_id = int(parts[0])
        emoji = parts[1].strip()
        
        try:
            msg = await channel.fetch_message(message_id)
            await msg.add_reaction(emoji)
            return f"✅ Reaction {emoji} add kiya!"
        except Exception as e:
            return f"❌ Reaction add nahi ho paya: {e}"
    
    async def _cmd_embed(self, args: str, guild, channel, author) -> str:
        """Send an embedded message"""
        # Simple parsing for embed - support both quote types
        match = re.match(r"'(.*)'\s*'(.*)'(?:\s*(\w+))?", args)
        if not match:
            match = re.match(r'"(.*)"\s*"(.*)"(?:\s*(\w+))?', args)
        if not match:
            return "❌ Usage: /cmd embed 'title' 'description' [color]"
        
        title = match.group(1)
        description = match.group(2)
        color_name = match.group(3) or "blue"
        
        colors = {
            "blue": discord.Color.blue(),
            "red": discord.Color.red(),
            "green": discord.Color.green(),
            "purple": discord.Color.purple(),
            "gold": discord.Color.gold(),
            "blurple": discord.Color.blurple()
        }
        
        color = colors.get(color_name.lower(), discord.Color.blurple())
        
        embed = discord.Embed(title=title, description=description, color=color)
        embed.set_footer(text="🤖 AI Generated Embed")
        
        await channel.send(embed=embed)
        return "✅ Embed bhej diya!"
    
    async def _cmd_status(self, args: str, guild, channel, author) -> str:
        """Change bot status"""
        parts = args.split(maxsplit=1)
        activity_type = parts[0].lower() if parts else "playing"
        status_text = parts[1] if len(parts) > 1 else ""
        
        activity_map = {
            "playing": discord.ActivityType.playing,
            "listening": discord.ActivityType.listening,
            "watching": discord.ActivityType.watching,
            "streaming": discord.ActivityType.streaming
        }
        
        activity_type_enum = activity_map.get(activity_type, discord.ActivityType.playing)
        
        activity = discord.Activity(type=activity_type_enum, name=status_text)
        await self.bot.change_presence(activity=activity)
        
        return f"✅ Status set: {activity_type} {status_text}"
    
    async def _cmd_clear(self, args: str, guild, channel, author) -> str:
        """Delete messages"""
        count = int(args) if args.isdigit() else 10
        count = min(count, 100)  # Max 100 at once
        
        deleted = await channel.purge(limit=count)
        return f"✅ {len(deleted)} messages delete kiye!"
    
    async def _cmd_kick(self, args: str, guild, channel, author) -> str:
        """Kick a user"""
        # Extract user mention or ID
        user_match = re.search(r'<@!?(\d+)>|(\d{17,19})', args)
        if not user_match:
            return "❌ User mention karo ya ID do"
        
        user_id = int(user_match.group(1) or user_match.group(2))
        reason = re.sub(r'<@!?(\d+)>|(\d{17,19})', '', args).strip() or "No reason provided"
        
        try:
            member = guild.get_member(user_id) or await guild.fetch_member(user_id)
            await member.kick(reason=f"Via AI Command by {author}: {reason}")
            return f"✅ {member} ko kick kiya!"
        except Exception as e:
            return f"❌ Kick nahi ho paya: {e}"
    
    async def _cmd_ban(self, args: str, guild, channel, author) -> str:
        """Ban a user"""
        user_match = re.search(r'<@!?(\d+)>|(\d{17,19})', args)
        if not user_match:
            return "❌ User mention karo ya ID do"
        
        user_id = int(user_match.group(1) or user_match.group(2))
        reason = re.sub(r'<@!?(\d+)>|(\d{17,19})', '', args).strip() or "No reason provided"
        
        try:
            member = guild.get_member(user_id) or await guild.fetch_member(user_id)
            await member.ban(reason=f"Via AI Command by {author}: {reason}")
            return f"✅ {member} ko ban kiya!"
        except Exception as e:
            return f"❌ Ban nahi ho paya: {e}"
    
    async def _cmd_create_channel(self, args: str, guild, channel, author) -> str:
        """Create a new channel"""
        # Support both quote types
        match = re.match(r"'(.*)'(?:\s*(\w+))?", args)
        if not match:
            match = r'"(.*)"(?:\s*(\w+))?'
            match = re.match(match, args)
        if not match:
            return "❌ Usage: /cmd create_channel 'name' [type]"
        
        name = match.group(1).lower().replace(" ", "-")
        channel_type = (match.group(2) or "text").lower()
        
        channel_types = {
            "text": discord.ChannelType.text,
            "voice": discord.ChannelType.voice,
            "stage": discord.ChannelType.stage
        }
        
        ch_type = channel_types.get(channel_type, discord.ChannelType.text)
        
        new_channel = await guild.create_channel(name=name, type=ch_type)
        return f"✅ Channel #{new_channel.name} bana diya!"
    
    async def _cmd_create_role(self, args: str, guild, channel, author) -> str:
        """Create a new role"""
        # Support both quote types
        match = re.match(r"'(.*)'(?:\s*(\w+))?", args)
        if not match:
            match = re.match(r'"(.*)"(?:\s*(\w+))?', args)
        if not match:
            return "❌ Usage: /cmd create_role 'name' [color]"
        
        name = match.group(1)
        color_name = match.group(2) or "blue"
        
        colors = {
            "blue": discord.Color.blue(),
            "red": discord.Color.red(),
            "green": discord.Color.green(),
            "purple": discord.Color.purple(),
            "gold": discord.Color.gold(),
            "white": discord.Color.white(),
            "black": discord.Color.default()
        }
        
        color = colors.get(color_name.lower(), discord.Color.blue())
        
        new_role = await guild.create_role(name=name, color=color)
        return f"✅ Role @{new_role.name} bana diya!"
    
    def get_help_text(self) -> str:
        """Get help text listing all available commands"""
        help_lines = ["**📋 Available Meta-Commands:**\n"]
        
        for name, info in self.AVAILABLE_COMMANDS.items():
            mod_tag = " 🔒" if info.get("mod_only") else ""
            help_lines.append(f"`{info['usage']}`{mod_tag}")
            help_lines.append(f"   {info['description']}\n")
        
        return "\n".join(help_lines)


# Global instance
meta_command_parser: Optional[MetaCommandParser] = None


def init_meta_commands(bot: commands.Bot) -> MetaCommandParser:
    """Initialize meta-command system"""
    global meta_command_parser
    meta_command_parser = MetaCommandParser(bot)
    return meta_command_parser


def get_meta_parser() -> MetaCommandParser:
    """Get meta-command parser instance"""
    if meta_command_parser is None:
        raise RuntimeError("Meta-command parser not initialized!")
    return meta_command_parser
