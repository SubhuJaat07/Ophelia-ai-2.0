"""
Advanced Natural Language Command System for Ophelia AI 2.0
AI understands DIRECT commands like "avatar dikhao", "timeout do", etc.
NO /cmd syntax needed - just talk naturally!
"""
import discord
from discord.ext import commands
import logging
import re
import asyncio
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime, timedelta

from config.settings import config, is_owner

logger = logging.getLogger("NaturalCommands")


class NaturalCommandParser:
    """
    Advanced command parser that understands NATURAL LANGUAGE!
    User says: "iska avatar dikhao"
    Bot understands: SHOW_AVATAR command with target user
    """
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    async def process_message(
        self,
        message: str,
        guild: discord.Guild,
        channel: discord.TextChannel,
        author: discord.Member,
        referenced_message: Optional[discord.Message] = None
    ) -> Tuple[str, bool, Optional[discord.Embed]]:
        """
        Process user message for natural language commands.
        Returns (response_text, was_command_executed, optional_embed)
        """
        
        msg_lower = message.lower().strip()
        
        # Check if this looks like a command (action-oriented)
        command_result = await self._detect_and_execute(
            msg_lower, message, guild, channel, author, referenced_message
        )
        
        if command_result:
            return command_result
        
        return None, False, None
    
    async def _detect_and_execute(
        self,
        msg_lower: str,
        original_msg: str,
        guild: discord.Guild,
        channel: discord.TextChannel,
        author: discord.Member,
        referenced_msg: Optional[discord.Message] = None
    ) -> Optional[Tuple[str, bool, Optional[discord.Embed]]]:
        """Detect and execute natural language commands"""
        
        # Get target user (from mention or referenced message)
        target_user = self._extract_target_user(original_msg, channel, referenced_msg)
        
        # ===== AVATAR & INFO COMMANDS (Everyone can use) =====
        
        if self._matches_patterns(msg_lower, ["avatar", "dp", "profile pic", "photo", "display picture", "pfp"]):
            return await self._cmd_show_avatar(target_user or author, original_msg)
        
        if self._matches_patterns(msg_lower, ["info", "baare me", "about", "details", "profile", "who is"]):
            return await self._cmd_show_user_info(target_user or author)
        
        if self._matches_patterns(msg_lower, ["server info", "server details", "server stats", "kitne members", "member count"]):
            return await self._cmd_show_server_info(guild)
        
        if self._matches_patterns(msg_lower, ["my info", "mera info", "mera profile"]):
            return await self._cmd_show_user_info(author)
        
        if self._matches_patterns(msg_lower, ["roles", "konse roles", "what roles"]):
            target = target_user or author
            return await self._cmd_show_roles(target)
        
        if self._matches_patterns(msg_lower, ["join date", "kab join hua", "when joined"]):
            target = target_user or author
            return await self._cmd_show_join_date(target)
        
        # ===== MODERATION COMMANDS (Owner/Mod Only) =====
        
        if self._matches_patterns(msg_lower, ["timeout", "mute temporarily", "silent mode"]):
            if not self._check_owner(author):
                return ("❌ Sirf owners timeout kar sakte hain!", False, None)
            duration = self._extract_duration(original_msg)
            reason = self._extract_reason(original_msg)
            if target_user:
                return await self._cmd_timeout(target_user, duration, reason, author, guild)
            return ("❌ Batao kis user ko timeout karna hai? (@mention karo)", False, None)
        
        if self._matches_patterns(msg_lower, ["kick", "hatao", "remove", "throw out", "nikalo"]):
            if not self._check_mod(author, guild):
                return ("❌ Sirf mods kick kar sakte hain!", False, None)
            reason = self._extract_reason(original_msg)
            if target_user:
                return await self._cmd_kick(target_user, reason, author, guild)
            return ("❌ Batao kis user ko kick karna hai?", False, None)
        
        if self._matches_patterns(msg_lower, ["ban", "permanent ban", "block", "paka band"]):
            if not self._check_mod(author, guild):
                return ("❌ Sirf mods ban kar sakte hain!", False, None)
            reason = self._extract_reason(original_msg)
            if target_user:
                return await self._cmd_ban(target_user, reason, author, guild)
            return ("❌ Batao kis user ko ban karna hai?", False, None)
        
        if self._matches_patterns(msg_lower, ["mute", "chupao", "silence", "shut up"]):
            if not self._check_mod(author, guild):
                return ("❌ Sirf mods mute kar sakte hain!", False, None)
            if target_user:
                return await self._cmd_mute(target_user, author, guild)
            return ("❌ Batao kis user ko mute karna hai?", False, None)
        
        # ===== BOT CONTROL COMMANDS (Owner Only) =====
        
        if self._matches_patterns(msg_lower, ["status", "set status", "playing", "listening", "watching", "streaming"]):
            if not self._check_owner(author):
                return ("❌ Sirf owners status change kar sakte hain!", False, None)
            activity_data = self._extract_activity(original_msg)
            return await self._cmd_set_status(activity_data)
        
        if self._matches_patterns(msg_lower, ["nickname", "name change", "naam badlo", "call me", "bolte ho"]):
            if not self._check_owner(author):
                return ("❌ Sirf owners nickname change kar sakte hain!", False, None)
            new_name = self._extract_nickname(original_msg)
            if new_name:
                return await self._cmd_set_nickname(new_name, guild)
            return ("❌ Naya naam batao?", False, None)
        
        if self._matches_patterns(msg_lower, ["channel banao", "make channel", "new channel", "naya channel", "create channel"]):
            if not self._check_owner(author):
                return ("❌ Sirf channels bana sakte hain owners!", False, None)
            channel_info = self._extract_channel_info(original_msg)
            return await self._cmd_create_channel(channel_info, guild)
        
        if self._matches_patterns(msg_lower, ["role banao", "make role", "new role", "naya role", "create role"]):
            if not self._check_owner(author):
                return ("❌ Sirf roles bana sakte hain owners!", False, None)
            role_info = self._extract_role_info(original_msg)
            return await self._cmd_create_role(role_info, guild)
        
        # ===== MESSAGING COMMANDS =====
        
        if self._matches_patterns(msg_lower, ["bhejo", "send to", "message in", "channel me bhejo", "announce"]):
            if not self._check_mod(author, guild) and "announce" in msg_lower:
                pass  # Allow announces for mods
            send_info = self._extract_send_info(original_msg, guild)
            if send_info:
                return await self._cmd_send_message(send_info, author)
            return ("❌ Kya bhejna hai aur kahan? Specify karo!", False, None)
        
        if self._matches_patterns(msg_lower, ["embed", "rich embed", "fancy message", "beautiful message"]):
            embed_info = self._extract_embed_info(original_msg)
            if embed_info:
                return await self._cmd_send_embed(embed_info, channel)
            return ("❌ Embed ke liye title aur description do!", False, None)
        
        # ===== REACTION COMMANDS =====
        
        if self._matches_patterns(msg_lower, ["react", "emoji lagao", "reaction do", "emoji do"]):
            emoji = self._extract_emoji(original_msg)
            target_msg = referenced_msg
            if emoji and target_msg:
                return await self._cmd_add_reaction(emoji, target_msg)
            return ("❌ Emoji batao aur message pe reply karke bol!", False, None)
        
        # ===== UTILITY COMMANDS =====
        
        if self._matches_patterns(msg_lower, ["clear", "delete messages", "messages delete", "chat clean"]):
            if not self._check_mod(author, guild):
                return ("❌ Sirf mods messages delete kar sakte hain!", False, None)
            count = self._extract_number(original_msg) or 10
            return await self._cmd_clear_messages(count, channel)
        
        if self._matches_patterns(msg_lower, ["help", "commands", "kya kar sakti hai", "features"]):
            return await self._cmd_show_help(author)
        
        return None
    
    def _matches_patterns(self, text: str, patterns: List[str]) -> bool:
        """Check if text matches any of the given patterns"""
        for pattern in patterns:
            if pattern.lower() in text:
                return True
        return False
    
    def _extract_target_user(
        self, 
        message: str, 
        channel: discord.TextChannel, 
        referenced_msg: Optional[discord.Message] = None
    ) -> Optional[discord.Member]:
        """Extract target user from mentions or referenced message"""
        # First check for mentions in message
        mention_pattern = r'<@!?(\d{17,19})>'
        match = re.search(mention_pattern, message)
        if match:
            user_id = int(match.group(1))
            return channel.guild.get_member(user_id)
        
        # Then check referenced message (reply)
        if referenced_msg:
            return channel.guild.get_member(referenced_msg.author.id)
        
        return None
    
    def _extract_duration(self, message: str) -> int:
        """Extract timeout duration from message in minutes"""
        # Look for duration patterns
        patterns = [
            r'(\d+)\s*min',      # 10 min, 5min
            r'(\d+)\s*minute',   # 10 minute
            r'(\d+)\s*hour',     # 1 hour
            r'(\d+)\s*hr',       # 1hr
            r'(\d+)\s*day',      # 1 day
        ]
        
        for pattern in patterns:
            match = re.search(pattern, message.lower())
            if match:
                num = int(match.group(1))
                if 'hour' in pattern or 'hr' in pattern:
                    return num * 60
                elif 'day' in pattern:
                    return num * 1440
                return num
        
        return 10  # Default 10 minutes
    
    def _extract_reason(self, message: str) -> str:
        """Extract reason from message"""
        # Remove common prefixes to get reason
        reason = message
        for prefix in ['timeout', 'kick', 'ban', 'mute', 'do', 'kar', 'karo']:
            reason = re.sub(prefix, '', reason, flags=re.IGNORECASE)
        
        # Remove mentions and numbers (duration)
        reason = re.sub(r'<@!?\d+>', '', reason)
        reason = re.sub(r'\d+\s*(min|hour|hr|day|minute)?', '', reason, flags=re.IGNORECASE)
        
        return reason.strip() or "No reason provided"
    
    def _extract_activity(self, message: str) -> Dict[str, str]:
        """Extract activity type and name from message"""
        activity_type = "playing"  # Default
        
        if any(word in message.lower() for word in ['listening']):
            activity_type = "listening"
        elif any(word in message.lower() for word in ['watching']):
            activity_type = "watching"
        elif any(word in message.lower() for word in ['streaming']):
            activity_type = "streaming"
        
        # Extract what they're doing
        name_match = re.search(r'(?:playing|listening||watching|streaming|status)\s+(.+)', message, re.IGNORECASE)
        name = name_match.group(1).strip() if name_match else "with Ophelia AI"
        
        return {"type": activity_type, "name": name}
    
    def _extract_nickname(self, message: str) -> Optional[str]:
        """Extract new nickname from message"""
        # Look for quoted string or after keywords
        quote_match = re.search(r'"([^"]+)"', message)
        if quote_match:
            return quote_match.group(1)
        
        # Try extracting after keywords
        patterns = [
            r'(?:nickname|name|naam|bolte)\s+(?:to|as|)?\s*(.+)',
            r'(?:call me|bulao|bolo)\s*(.+)',
        ]
        for pattern in patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                return match.group(1).strip()[:32]  # Discord max 32 chars
        
        return None
    
    def _extract_channel_info(self, message: str) -> Dict[str, str]:
        """Extract channel creation info"""
        name_match = re.search(r'(?:channel)?\s*["\']?(\w[\w\s-]*)["\']?', message, re.IGNORECASE)
        name = name_match.group(1).strip().lower().replace(" ", "-") if name_match else "general"
        
        ch_type = "text"
        if 'voice' in message.lower():
            ch_type = "voice"
        elif 'stage' in message.lower():
            ch_type = "stage"
        
        return {"name": name, "type": ch_type}
    
    def _extract_role_info(self, message: str) -> Dict[str, str]:
        """Extract role creation info"""
        name_match = re.search(r'(?:role)?\s*["\']?(\w[\w\s]*)["\']?', message, re.IGNORECASE)
        name = name_match.group(1).strip() if name_match else "New Role"
        
        colors = {
            'red': discord.Color.red(),
            'blue': discord.Color.blue(),
            'green': discord.Color.green(),
            'yellow': discord.Color.gold(),
            'purple': discord.Color.purple(),
            'pink': discord.Color.pink(),
            'orange': discord.Color.orange(),
            'white': discord.Color.white(),
            'black': discord.Color.default(),
            'blurple': discord.Color.blurple(),
            'gold': discord.Color.gold(),
        }
        
        color = discord.Color.blue()  # Default
        for color_name, color_val in colors.items():
            if color_name in message.lower():
                color = color_val
                break
        
        return {"name": name, "color": color}
    
    def _extract_send_info(self, message: str, guild: discord.Guild) -> Optional[Dict]:
        """Extract message sending info"""
        # Find channel
        channel_match = re.search(r'<#(\d{17,19})>|(?:channel|#)(?:\s+me)?\s*(\w+)', message, re.IGNORECASE)
        
        target_channel = None
        if channel_match:
            if channel_match.group(1):  # Channel mention
                target_channel = guild.get_channel(int(channel_match.group(1)))
            else:  # Channel name
                ch_name = channel_match.group(2).lower()
                target_channel = discord.utils.get(guild.text_channels, name=ch_name)
        
        # Extract message content
        content_match = re.search(r'["\'](.+)["\']|bhejo\s+(.+)|send\s+(.+)|announce\s+(.+)', message, re.IGNORECASE)
        content = content_match.group(1) or content_match.group(2) or content_match.group(3) or content_match.group(4)
        
        if target_channel and content:
            return {"channel": target_channel, "content": content.strip()}
        
        return None
    
    def _extract_embed_info(self, message: str) -> Optional[Dict]:
        """Extract embed creation info"""
        # Look for title and description
        matches = re.findall(r'"([^"]+)"', message)
        if len(matches) >= 2:
            return {"title": matches[0], "description": matches[1]}
        elif len(matches) == 1:
            return {"title": "Announcement", "description": matches[0]}
        return None
    
    def _extract_emoji(self, message: str) -> Optional[str]:
        """Extract emoji from message"""
        # Custom emoji format
        custom_emoji = re.search(r'<a?:\w+:(\d+)>', message)
        if custom_emoji:
            return custom_emoji.group(0)
        
        # Common emojis - just return first emoji-like character found
        emoji_chars = ['😂', '❤️', '🔥', '💀', '✨', '🎉', '👍', '👎', '😢', '😡', '🤔', '💯', '⭐', '🎮', '🎵']
        for emoji in emoji_chars:
            if emoji in message:
                return emoji
        
        return None
    
    def _extract_number(self, message: str) -> Optional[int]:
        """Extract number from message"""
        match = re.search(r'\d+', message)
        return int(match.group()) if match else None
    
    def _check_owner(self, user: discord.Member) -> bool:
        """Check if user is bot owner"""
        return is_owner(user.id)
    
    def _check_mod(self, user: discord.Member, guild: discord.Guild) -> bool:
        """Check if user is mod or owner"""
        if is_owner(user.id):
            return True
        return user.guild_permissions.manage_guild or user.guild_permissions.administrator
    
    # ==================== COMMAND EXECUTORS ====================
    
    async def _cmd_show_avatar(self, user: discord.Member, original_msg: str) -> Tuple[str, bool, Optional[discord.Embed]]:
        """Show user's avatar"""
        avatar_url = user.avatar.url if user.avatar else user.default_avatar.url
        
        embed = discord.Embed(
            title=f"📸 {user.display_name}'s Avatar",
            color=user.color or discord.Color.blurple()
        )
        embed.set_image(url=avatar_url)
        embed.add_field(name="User", value=f"<@{user.id}>", inline=True)
        embed.add_field(name="Avatar URL", value=f"[Click here]({avatar_url})", inline=True)
        
        return f"✅ Yeh raha {user.mention} ka avatar:", True, embed
    
    async def _cmd_show_user_info(self, user: discord.Member) -> Tuple[str, bool, Optional[discord.Embed]]:
        """Show detailed user information"""
        embed = discord.Embed(
            title=f"👤 {user.display_name}'s Info",
            color=user.color or discord.Color.blurple()
        )
        embed.set_thumbnail(url=user.avatar.url if user.avatar else user.default_avatar.url)
        
        embed.add_field(name="Username", value=str(user), inline=True)
        embed.add_field(name="Display Name", value=user.display_name, inline=True)
        embed.add_field(name="User ID", value=f"`{user.id}`", inline=True)
        embed.add_field(name="Bot?", value="✅ Yes" if user.bot else "❌ No", inline=True)
        embed.add_field(name="Account Created", value=format(user.created_at, "%d %b %Y"), inline=True)
        embed.add_field(name="Server Join Date", value=format(user.joined_at, "%d %b %Y") if user.joined_at else "Unknown", inline=True)
        
        # Roles
        roles = [role.name for role in user.roles[1:]]  # Skip @everyone
        if roles:
            embed.add_field(name=f"Roles ({len(roles)})", value=", ".join(roles[:10]), inline=False)
            if len(roles) > 10:
                embed.add_field(name="", value=f"*...and {len(roles)-10} more*", inline=False)
        
        # Top role
        if user.top_role and user.top_role.name != "@everyone":
            embed.add_field(name="Top Role", value=f"<@&{user.top_role.id}>", inline=True)
        
        # Owner badge
        if is_owner(user.id):
            embed.add_field(name="👑 Status", value="**BOT OWNER**", inline=False)
        
        return f"✅ Yeh raha {user.mention} ki puri info:", True, embed
    
    async def _cmd_show_server_info(self, guild: discord.Guild) -> Tuple[str, bool, Optional[discord.Embed]]:
        """Show server information"""
        embed = discord.Embed(
            title=f"📊 {guild.name} Server Info",
            color=discord.Color.blurple(),
            timestamp=datetime.now()
        )
        
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        
        embed.add_field(name="Server ID", value=f"`{guild.id}`", inline=True)
        embed.add_field(name="Owner", value=f"<@{guild.owner_id}>", inline=True)
        embed.add_field(name="Created", value=format(guild.created_at, "%d %b %Y"), inline=True)
        
        embed.add_field(name="Members", value=guild.member_count, inline=True)
        embed.add_field(name="Text Channels", value=len(guild.text_channels), inline=True)
        embed.add_field(name="Voice Channels", value=len(guild.voice_channels), inline=True)
        embed.add_field(name="Roles", value=len(guild.roles), inline=True)
        embed.add_field(name="Emojis", value=len(guild.emojis), inline=True)
        embed.add_field(name="Boost Level", value=str(guild.premium_tier), inline=True)
        
        features = []
        if guild.features:
            feature_names = {
                'COMMUNITY': 'Community',
                'PARTNERED': 'Partnered',
                'VERIFIED': 'Verified',
                'DISCOVERABLE': 'Discoverable',
                'ANIMATED_ICON': 'Animated Icon',
                'BANNER': 'Banner',
                'VIP_REGIONS': 'VIP Regions',
            }
            for f in guild.features:
                if f in feature_names:
                    features.append(feature_names[f])
        
        if features:
            embed.add_field(name="Features", value=", ".join(features), inline=False)
        
        return f"✅ Server ki full info:", True, embed
    
    async def _cmd_show_roles(self, user: discord.Member) -> Tuple[str, bool, Optional[discord.Embed]]:
        """Show user's roles"""
        roles = [role for role in user.roles if role.name != "@everyone"]
        
        if not roles:
            return f"{user.mention} ke paas koi special role nahi hai 😅", True, None
        
        embed = discord.Embed(
            title=f"🎭 {user.display_name}'s Roles",
            color=user.color or discord.Color.blurple(),
            description=f"Total **{len(roles)} roles**"
        )
        
        role_list = []
        for i, role in enumerate(sorted(roles, key=lambda r: r.position, reverse=True)):
            role_list.append(f"`{i+1}.` <@&{role.id}>")
        
        embed.description += "\n".join(role_list[:20])
        
        return f"✅ Yeh hain {user.mention} ke roles:", True, embed
    
    async def _cmd_show_join_date(self, user: discord.Member) -> Tuple[str, bool, Optional[discord.Embed]]:
        """Show when user joined server"""
        if not user.joined_at:
            return f"❌ Join date available nahi hai", True, None
        
        days_since = (datetime.now(user.joined_at.tzinfo) - user.joined_at).days
        
        embed = discord.Embed(
            title="📅 Join Date",
            color=discord.Color.green()
        )
        embed.add_field(name="User", value=user.mention, inline=True)
        embed.add_field(name="Join Date", value=format(user.joined_at, "%d %B %Y at %I:%M %p"), inline=True)
        embed.add_field(name="Days in Server", value=f"**{days_since} days**", inline=True)
        
        return f"✅ {user.mention} ko server join hua:", True, embed
    
    async def _cmd_timeout(
        self, 
        user: discord.Member, 
        duration_minutes: int, 
        reason: str,
        moderator: discord.Member,
        guild: discord.Guild
    ) -> Tuple[str, bool, Optional[discord.Embed]]:
        """Timeout a user"""
        try:
            duration = timedelta(minutes=duration_minutes)
            await user.timeout(duration, reason=f"Via AI by {moderator}: {reason}")
            
            embed = discord.Embed(
                title="⏰ User Timed Out!",
                color=discord.Color.orange()
            )
            embed.add_field(name="User", value=user.mention, inline=True)
            embed.add_field(name="Duration", value=f"**{duration_minutes} minutes**", inline=True)
            embed.add_field(name="Reason", value=reason, inline=True)
            embed.add_field(name="By", value=moderator.mention, inline=True)
            embed.set_footer(text="Timeout automatically expires!")
            
            return f"✅ {user.mention} ko **{duration_minutes} minutes** ke liye timeout kar diya!", True, embed
            
        except Exception as e:
            return f"❌ Timeout nahi ho paya: `{e}`", True, None
    
    async def _cmd_kick(
        self, 
        user: discord.Member, 
        reason: str,
        moderator: discord.Member,
        guild: discord.Guild
    ) -> Tuple[str, bool, Optional[discord.Embed]]:
        """Kick a user"""
        try:
            await user.kick(reason=f"Via AI by {moderator}: {reason}")
            
            embed = discord.Embed(
                title="👢 User Kicked!",
                color=discord.Color.red()
            )
            embed.add_field(name="User", value=user.mention, inline=True)
            embed.add_field(name="Reason", value=reason, inline=True)
            embed.add_field(name="Kicked By", value=moderator.mention, inline=True)
            
            return f"✅ {user.mention} ko kick kar diya!", True, embed
            
        except Exception as e:
            return f"❌ Kick nahi ho paya: `{e}`", True, None
    
    async def _cmd_ban(
        self, 
        user: discord.Member, 
        reason: str,
        moderator: discord.Member,
        guild: discord.Guild
    ) -> Tuple[str, bool, Optional[discord.Embed]]:
        """Ban a user"""
        try:
            await user.ban(reason=f"Via AI by {moderator}: {reason}", delete_message_days=0)
            
            embed = discord.Embed(
                title="🚫 User Banned!",
                color=discord.Color.dark_red()
            )
            embed.add_field(name="User", value=user.mention, inline=True)
            embed.add_field(name="Reason", value=reason, inline=True)
            embed.add_field(name="Banned By", value=moderator.mention, inline=True)
            
            return f"✅ {user.mention} ko permanently ban kar diya!", True, embed
            
        except Exception as e:
            return f"❌ Ban nahi ho paya: `{e}`", True, None
    
    async def _cmd_mute(
        self, 
        user: discord.Member, 
        moderator: discord.Member,
        guild: discord.Guild
    ) -> Tuple[str, bool, Optional[discord.Embed]]:
        """Mute a user (using timeout for 5 min or mute role)"""
        try:
            # Use timeout for 5 minutes as mute
            await user.timeout(timedelta(minutes=5), reason=f"Muted via AI by {moderator}")
            
            embed = discord.Embed(
                title="🔇 User Muted!",
                color=discord.Color.orange()
            )
            embed.add_field(name="User", value=user.mention, inline=True)
            embed.add_field(name="Duration", value="5 minutes", inline=True)
            embed.add_field(name="Muted By", value=moderator.mention, inline=True)
            
            return f"✅ {user.mention} ko mute kar diya (5 min)!", True, embed
            
        except Exception as e:
            return f"❌ Mute nahi ho paya: `{e}`", True, None
    
    async def _cmd_set_status(self, activity: Dict[str, str]) -> Tuple[str, bool, Optional[discord.Embed]]:
        """Set bot status/activity"""
        try:
            type_map = {
                "playing": discord.ActivityType.playing,
                "listening": discord.ActivityType.listening,
                "watching": discord.ActivityType.watching,
                "streaming": discord.ActivityType.streaming
            }
            
            activity_type = type_map.get(activity["type"], discord.ActivityType.playing)
            act = discord.Activity(type=activity_type, name=activity["name"])
            await self.bot.change_presence(activity=act)
            
            return f"✅ Status set: **{activity['type']}** *{activity['name']}*", True, None
            
        except Exception as e:
            return f"❌ Status set nahi ho paya: `{e}`", True, None
    
    async def _cmd_set_nickname(self, new_name: str, guild: discord.Guild) -> Tuple[str, bool, Optional[discord.Embed]]:
        """Change bot's nickname in server"""
        try:
            await guild.me.edit(nickname=new_name)
            return f"✅ Mera ab naam **{new_name}** hai! 😊", True, None
        except Exception as e:
            return f"❌ Nickname change nahi ho paya: `{e}`", True, None
    
    async def _cmd_create_channel(self, info: Dict[str, str], guild: discord.Guild) -> Tuple[str, bool, Optional[discord.Embed]]:
        """Create a new channel"""
        try:
            type_map = {
                "text": discord.ChannelType.text,
                "voice": discord.ChannelType.voice,
                "stage": discord.ChannelType.stage
            }
            
            ch_type = type_map.get(info["type"], discord.ChannelType.text)
            new_channel = await guild.create_channel(name=info["name"], type=ch_type)
            
            embed = discord.Embed(
                title="✅ Channel Created!",
                color=discord.Color.green()
            )
            embed.add_field(name="Name", value=f"#{new_channel.name}", inline=True)
            embed.add_field(name="Type", value=info["type"].title(), inline=True)
            embed.add_field(name="ID", value=f"`{new_channel.id}`", inline=True)
            
            return f"✅ Channel **#{new_channel.name}** bana diya!", True, embed
            
        except Exception as e:
            return f"❌ Channel nahi bana: `{e}`", True, None
    
    async def _cmd_create_role(self, info: Dict[str, str], guild: discord.Guild) -> Tuple[str, bool, Optional[discord.Embed]]:
        """Create a new role"""
        try:
            new_role = await guild.create_role(name=info["name"], color=info["color"])
            
            embed = discord.Embed(
                title="✅ Role Created!",
                color=info["color"]
            )
            embed.add_field(name="Name", value=f"@{new_role.name}", inline=True)
            embed.add_field(name="Color", value=info["color"].value if hasattr(info['color'], 'value') else "Default", inline=True)
            embed.add_field(name="ID", value=f"`{new_role.id}`", inline=True)
            
            return f"✅ Role **@{new_role.name}** bana diya!", True, embed
            
        except Exception as e:
            return f"❌ Role nahi bana: `{e}`", True, None
    
    async def _cmd_send_message(self, info: Dict, author: discord.Member) -> Tuple[str, bool, Optional[discord.Embed]]:
        """Send message to a channel"""
        try:
            channel = info["channel"]
            content = info["content"]
            
            sent_msg = await channel.send(content)
            
            embed = discord.Embed(
                title="✅ Message Sent!",
                color=discord.Color.green()
            )
            embed.add_field(name="Channel", value=f"<#{channel.id}>", inline=True)
            embed.add_field(name="Content", value=content[:100] + ("..." if len(content) > 100 else ""), inline=False)
            
            return f"✅ Message <#{channel.id}> me bhej diya!", True, embed
            
        except Exception as e:
            return f"❌ Message nahi bhej paya: `{e}`", True, None
    
    async def _cmd_send_embed(self, info: Dict, channel: discord.TextChannel) -> Tuple[str, bool, Optional[discord.Embed]]:
        """Send an embed message"""
        try:
            embed = discord.Embed(
                title=info["title"],
                description=info["description"],
                color=discord.Color.blurple(),
                timestamp=datetime.now()
            )
            embed.set_footer(text="🤖 Generated by Ophelia AI 2.0")
            
            await channel.send(embed=embed)
            
            return f"✅ Embed bhej diya!", True, None
            
        except Exception as e:
            return f"❌ Embed nahi bhej paya: `{e}`", True, None
    
    async def _cmd_add_reaction(self, emoji: str, message: discord.Message) -> Tuple[str, bool, Optional[discord.Embed]]:
        """Add reaction to a message"""
        try:
            await message.add_reaction(emoji)
            return f"✅ Reaction {emoji} add kar diya!", True, None
        except Exception as e:
            return f"❌ Reaction add nahi ho paya: `{e}`", True, None
    
    async def _cmd_clear_messages(self, count: int, channel: discord.TextChannel) -> Tuple[str, bool, Optional[discord.Embed]]:
        """Delete messages from channel"""
        try:
            count = min(count, 100)  # Max 100
            deleted = await channel.purge(limit=count)
            
            embed = discord.Embed(
                title="🧹 Messages Deleted!",
                color=discord.Color.orange()
            )
            embed.add_field(name="Count", value=f"**{len(deleted)} messages**", inline=True)
            embed.add_field(name="Channel", value=f"<#{channel.id}>", inline=True)
            
            return f"✅ **{len(deleted)} messages** delete kiye!", True, embed
            
        except Exception as e:
            return f"❌ Messages delete nahi ho paye: `{e}`", True, None
    
    async def _cmd_show_help(self, user: discord.Member) -> Tuple[str, bool, Optional[discord.Embed]]:
        """Show help for natural language commands"""
        owner_mode = is_owner(user.id)
        
        embed = discord.Embed(
            title="🤖 Ophelia AI 2.0 - Natural Commands",
            description="Sirf **bolna** hai, samajh jaati hoon! 🧠",
            color=discord.Color.blurple()
        )
        
        # Everyone can use these
        embed.add_field(
            name="👀 Info Commands (Sab use karein)",
            value=(
                "`avatar dikhao` / `dp dikhao`\n"
                "`iske baare me batao`\n"
                "`server info dikhao`\n"
                "`mera info`\n"
                "`roles dikhao`\n"
                "`join date kab hai?`"
            ),
            inline=False
        )
        
        if owner_mode:
            embed.add_field(
                name="👑 Owner Commands (Full Power)",
                value=(
                    "`isko timeout do [time]`\n"
                    "`isko kick/ban/mute karo`\n"
                    "`status set karo playing [game]`\n"
                    "`nickname change karo [name]`\n"
                    "`channel/role banao [name]`\n"
                    "`#channel me [msg] bhejo`\n"
                    "`embed banao [title] [desc]`\n"
                    "`[count] messages delete karo`"
                ),
                inline=False
            )
        else:
            embed.add_field(
                name="⚡ Mod Commands",
                value=(
                    "`isko timeout/kick/ban karo`\n"
                    "`messages delete karo`"
                ),
                inline=False
            )
        
        embed.set_footer(text="Directly bolo, koi /cmd syntax nahi chahiye! 😊")
        
        return "✅ Yeh rahi meri command list:", True, embed


# Global instance
natural_parser: Optional[NaturalCommandParser] = None


def init_natural_commands(bot: commands.Bot) -> NaturalCommandParser:
    """Initialize natural command system"""
    global natural_parser
    natural_parser = NaturalCommandParser(bot)
    return natural_parser


def get_natural_parser() -> NaturalCommandParser:
    """Get natural command parser instance"""
    if natural_parser is None:
        raise RuntimeError("Natural command parser not initialized!")
    return natural_parser
