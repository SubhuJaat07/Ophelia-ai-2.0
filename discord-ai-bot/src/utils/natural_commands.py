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
        
        # Get target user (from mention, name, or referenced message) - IMPROVED!
        target_user = await self._extract_target_user(original_msg, channel, guild, referenced_msg)
        
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
        
        # ===== OWNER INFO COMMAND =====
        if self._matches_patterns(msg_lower, ["owner", "owners", "kon owner", "who is owner", "malik kaun hai"]):
            return await self._cmd_show_owners(guild)
        
        # ===== MODERATION COMMANDS (Owner/Mod Only) =====
        
        if self._matches_patterns(msg_lower, ["timeout", "mute temporarily", "silent mode"]):
            if not self._check_owner(author):
                return ("❌ Sirf owners timeout kar sakte hain!", False, None)
            duration = self._extract_duration(original_msg)
            reason = self._extract_reason(original_msg) or "Server rules violation"
            if target_user:
                return await self._cmd_timeout(target_user, duration, reason, author, guild)
            return ("❌ Batao kis user ko timeout karna hai? (@mention karo ya naam batao)", False, None)
        
        if self._matches_patterns(msg_lower, ["kick", "hatao", "remove", "throw out", "nikalo"]):
            if not self._check_mod(author, guild):
                return ("❌ Sirf mods kick kar sakte hain!", False, None)
            reason = self._extract_reason(original_msg) or "Server rules violation"
            if target_user:
                return await self._cmd_kick(target_user, reason, author, guild)
            return ("❌ Batao kis user ko kick karna hai? (@mention karo ya naam batao)", False, None)
        
        if self._matches_patterns(msg_lower, ["ban", "permanent ban", "block", "paka band"]):
            if not self._check_mod(author, guild):
                return ("❌ Sirf mods ban kar sakte hain!", False, None)
            reason = self._extract_reason(original_msg) or "Server rules violation"
            if target_user:
                return await self._cmd_ban(target_user, reason, author, guild)
            return ("❌ Batao kis user ko ban karna hai? (@mention karo ya naam batao)", False, None)
        
        if self._matches_patterns(msg_lower, ["mute", "chupao", "silence", "shut up"]):
            if not self._check_mod(author, guild):
                return ("❌ Sirf mods mute kar sakte hain!", False, None)
            if target_user:
                return await self._cmd_mute(target_user, author, guild)
            return ("❌ Batao kis user ko mute karna hai? (@mention karo ya naam batao)", False, None)
        
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
    
    async def _extract_target_user(
        self, 
        message: str, 
        channel: discord.TextChannel, 
        guild: discord.Guild,
        referenced_msg: Optional[discord.Message] = None
    ) -> Optional[discord.Member]:
        """Extract target user from mentions, username, or referenced message - IMPROVED!"""
        
        # First check for mentions in message (most reliable)
        mention_pattern = r'<@!?(\d{17,19})>'
        match = re.search(mention_pattern, message)
        if match:
            user_id = int(match.group(1))
            member = channel.guild.get_member(user_id)
            if member:
                return member
        
        # Then check referenced message (reply)
        if referenced_msg:
            return channel.guild.get_member(referenced_msg.author.id)
        
        # NEW: Try to find user by NAME/USERNAME from the message
        # Remove common words and try to match a username
        cleaned_msg = re.sub(r'<@!?\d+>', '', message)  # Remove mentions
        cleaned_msg = re.sub(r'(kick|ban|timeout|mute|isko|iska|usko|use|inhe|inhone|user|ko|ka|ke|liye|karo|kar|do|to|me|se|hai|please|hey|ophelia|@everyone|@here)', '', cleaned_msg, flags=re.IGNORECASE)
        cleaned_msg = cleaned_msg.strip()
        
        if cleaned_msg and len(cleaned_msg) > 2:
            # Search for member by display name or username
            for member in guild.members:
                if cleaned_msg.lower() in member.display_name.lower() or cleaned_msg.lower() in member.name.lower():
                    logger.info(f"🔍 Found user '{cleaned_msg}' → {member} ({member.id})")
                    return member
        
        return None
    
    def _extract_duration(self, message: str) -> int:
        """Extract timeout duration from message in minutes"""
        patterns = [
            r'(\d+)\s*min',
            r'(\d+)\s*minute',
            r'(\d+)\s*hour',
            r'(\d+)\s*hr',
            r'(\d+)\s*day',
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
    
    def _extract_reason(self, message: str) -> Optional[str]:
        """Extract reason from message - returns None if no clear reason"""
        reason = message
        for prefix in ['timeout', 'kick', 'ban', 'mute', 'do', 'kar', 'karo']:
            reason = re.sub(prefix, '', reason, flags=re.IGNORECASE)
        
        # Remove mentions and numbers (duration)
        reason = re.sub(r'<@!?\d+>', '', reason)
        reason = re.sub(r'\d+\s*(min|hour|hr|day|minute)?', '', reason, flags=re.IGNORECASE)
        
        reason = reason.strip()
        
        # Only return reason if it looks like actual content (not just random words)
        if len(reason) < 3 or reason.lower() in ['isco', 'iska', 'usko', 'use', 'inhe', 'ko', 'se']:
            return None  # No valid reason found
        
        return reason
    
    def _extract_activity(self, message: str) -> Dict[str, str]:
        """Extract activity type and name from message"""
        activity_type = "playing"  # Default
        
        if any(word in message.lower() for word in ['listening']):
            activity_type = "listening"
        elif any(word in message.lower() for word in ['watching']):
            activity_type = "watching"
        elif any(word in message.lower() for word in ['streaming']):
            activity_type = "streaming"
        
        name_match = re.search(r'(?:playing|listening||watching|streaming|status)\s+(.+)', message, re.IGNORECASE)
        name = name_match.group(1).strip() if name_match else "with Ophelia AI"
        
        return {"type": activity_type, "name": name}
    
    def _extract_nickname(self, message: str) -> Optional[str]:
        """Extract new nickname from message"""
        quote_match = re.search(r'"([^"]+)"', message)
        if quote_match:
            return quote_match.group(1)
        
        patterns = [
            r'(?:nickname|name|naam|bolte)\s+(?:to|as|)?\s*(.+)',
            r'(?:call me|bulao|bolo)\s*(.+)',
        ]
        for pattern in patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                return match.group(1).strip()[:32]
        
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
        
        color = discord.Color.blue()
        for color_name, color_val in colors.items():
            if color_name in message.lower():
                color = color_val
                break
        
        return {"name": name, "color": color}
    
    def _extract_send_info(self, message: str, guild: discord.Guild) -> Optional[Dict]:
        """Extract message sending info"""
        channel_match = re.search(r'<#(\d{17,19})>|(?:channel|#)(?:\s+me)?\s*(\w+)', message, re.IGNORECASE)
        
        target_channel = None
        if channel_match:
            if channel_match.group(1):
                target_channel = guild.get_channel(int(channel_match.group(1)))
            else:
                ch_name = channel_match.group(2).lower()
                target_channel = discord.utils.get(guild.text_channels, name=ch_name)
        
        content_match = re.search(r'["\'](.+)["\']|bhejo\s+(.+)|send\s+(.+)|announce\s+(.+)', message, re.IGNORECASE)
        content = content_match.group(1) or content_match.group(2) or content_match.group(3) or content_match.group(4)
        
        if target_channel and content:
            return {"channel": target_channel, "content": content.strip()}
        
        return None
    
    def _extract_embed_info(self, message: str) -> Optional[Dict]:
        """Extract embed creation info"""
        matches = re.findall(r'"([^"]+)"', message)
        if len(matches) >= 2:
            return {"title": matches[0], "description": matches[1]}
        elif len(matches) == 1:
            return {"title": "Announcement", "description": matches[0]}
        return None
    
    def _extract_emoji(self, message: str) -> Optional[str]:
        """Extract emoji from message"""
        custom_emoji = re.search(r'<a?:\w+:(\d+)>', message)
        if custom_emoji:
            return custom_emoji.group(0)
        
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
        """Show user's avatar - SEND AS PLAIN IMAGE, NOT EMBED!"""
        avatar_url = user.avatar.url if user.avatar else user.default_avatar.url
        
        # Return PLAIN TEXT with image URL - let Discord preview it naturally
        return f"📸 **{user.display_name}** ka avatar:\n{avatar_url}", True, None
    
    async def _cmd_show_user_info(self, user: discord.Member) -> Tuple[str, bool, Optional[discord.Embed]]:
        """Show detailed user information - NICE EMBED STYLE!"""
        embed = discord.Embed(
            title=f"╔══════════════════════════╗\n║  👤 USER INFORMATION     ║\n╚══════════════════════════╝",
            description=f"**{user.display_name}** ki puri jaankari:",
            color=user.color or discord.Color.blurple()
        )
        embed.set_thumbnail(url=user.avatar.url if user.avatar else user.default_avatar.url)
        
        embed.add_field(name="👤 Username", value=f"`{user}`", inline=True)
        embed.add_field(name="📛 Display Name", value=user.display_name, inline=True)
        embed.add_field(name="🆔 User ID", value=f"`{user.id}`", inline=True)
        embed.add_field(name="🤖 Bot?", value="✅ Yes" if user.bot else "❌ No", inline=True)
        embed.add_field(name="📅 Account Created", value=format(user.created_at, "%d %b %Y"), inline=True)
        embed.add_field(name="🏠 Server Join Date", value=format(user.joined_at, "%d %b %Y") if user.joined_at else "Unknown", inline=True)
        
        # Roles
        roles = [role.name for role in user.roles[1:]]
        if roles:
            embed.add_field(name=f"🎭 Roles ({len(roles)})", value=", ".join(roles[:10]), inline=False)
            if len(roles) > 10:
                embed.add_field(name="", value=f"*...and {len(roles)-10} more*", inline=False)
        
        # Top role
        if user.top_role and user.top_role.name != "@everyone":
            embed.add_field(name="⭐ Top Role", value=f"<@&{user.top_role.id}>", inline=True)
        
        # Owner badge
        if is_owner(user.id):
            embed.add_field(name="👑 Status", value="**BOT OWNER - FULL ACCESS**", inline=False)
        
        return f"", True, embed  # Empty text since embed has all info
    
    async def _cmd_show_server_info(self, guild: discord.Guild) -> Tuple[str, bool, Optional[discord.Embed]]:
        """Show server information - ANNOUNCEMENT STYLE!"""
        embed = discord.Embed(
            title="╔══════════════════════════════╗\n║  📊 SERVER INFORMATION      ║\n╚══════════════════════════════╝",
            description=f"**{guild.name}** server ki stats:",
            color=discord.Color.blurple(),
            timestamp=datetime.now()
        )
        
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        
        embed.add_field(name="🆔 Server ID", value=f"`{guild.id}`", inline=True)
        embed.add_field(name="👑 Owner", value=f"<@{guild.owner_id}>", inline=True)
        embed.add_field(name="📅 Created", value=format(guild.created_at, "%d %b %Y"), inline=True)
        
        embed.add_field(name="👥 Members", value=f"**{guild.member_count}**", inline=True)
        embed.add_field(name="💬 Text Channels", value=len(guild.text_channels), inline=True)
        embed.add_field(name="🎙️ Voice Channels", value=len(guild.voice_channels), inline=True)
        embed.add_field(name="🎭 Roles", value=len(guild.roles), inline=True)
        embed.add_field(name="😀 Emojis", value=len(guild.emojis), inline=True)
        embed.add_field(name="💎 Boost Level", value=str(guild.premium_tier), inline=True)
        
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
            embed.add_field(name="✨ Features", value=", ".join(features), inline=False)
        
        return f"", True, embed
    
    async def _cmd_show_owners(self, guild: discord.Guild) -> Tuple[str, bool, Optional[discord.Embed]]:
        """Show bot owners - IMPORTANT FIX!"""
        owner_ids = config.owner_ids
        
        embed = discord.Embed(
            title="╔══════════════════════════╗\n║  👑 BOT OWNERS           ║\n╚══════════════════════════╝",
            description="**Full access** to bot controls (kick/ban/settings/all)",
            color=discord.Color.gold()
        )
        
        owner_list = []
        for owner_id in owner_ids:
            member = guild.get_member(owner_id)
            if member:
                owner_list.append(f"👑 **{member.display_name}** (<@{owner_id}>)")
            else:
                owner_list.append(f"👑 Unknown Owner (`{owner_id}`)")
        
        embed.description += "\n\n" + "\n".join(owner_list)
        embed.set_footer(text="Only owners can use moderation & control commands")
        
        return f"", True, embed
    
    async def _cmd_show_roles(self, user: discord.Member) -> Tuple[str, bool, Optional[discord.Embed]]:
        """Show user's roles"""
        roles = [role for role in user.roles if role.name != "@everyone"]
        
        if not roles:
            return f"{user.mention} ke paas koi special role nahi hai 😅", True, None
        
        embed = discord.Embed(
            title=f"╔══════════════════════════╗\n║  🎭 {user.display_name.upper()}'S ROLES ║\n╚══════════════════════════╝",
            description=f"Total **{len(roles)} roles**",
            color=user.color or discord.Color.blurple()
        )
        
        role_list = []
        for i, role in enumerate(sorted(roles, key=lambda r: r.position, reverse=True)):
            role_list.append(f"`{i+1}.` <@&{role.id}>")
        
        embed.description += "\n" + "\n".join(role_list[:20])
        
        return f"", True, embed
    
    async def _cmd_show_join_date(self, user: discord.Member) -> Tuple[str, bool, Optional[discord.Embed]]:
        """Show when user joined server"""
        if not user.joined_at:
            return f"❌ Join date available nahi hai", True, None
        
        days_since = (datetime.now(user.joined_at.tzinfo) - user.joined_at).days
        
        embed = discord.Embed(
            title="╔══════════════════════════╗\n║  📅 JOIN DATE             ║\n╚══════════════════════════╝",
            color=discord.Color.green()
        )
        embed.add_field(name="User", value=user.mention, inline=True)
        embed.add_field(name="Join Date", value=format(user.joined_at, "%d %B %Y at %I:%M %p"), inline=True)
        embed.add_field(name="Days in Server", value=f"**{days_since} days**", inline=True)
        
        return f"", True, embed
    
    async def _cmd_timeout(
        self, 
        user: discord.Member, 
        duration_minutes: int, 
        reason: str,
        moderator: discord.Member,
        guild: discord.Guild
    ) -> Tuple[str, bool, Optional[discord.Embed]]:
        """Timeout a user - NICE EMBED STYLE!"""
        try:
            duration = timedelta(minutes=duration_minutes)
            await user.timeout(duration, reason=f"Via AI by {moderator}: {reason}")
            
            embed = discord.Embed(
                title="╔═════════════════════════════════╗\n║  ⏰  USER TIMED OUT!              ║\n╚═════════════════════════════════╝",
                description=f"**{user.display_name}** ko timeout kar diya gaya!",
                color=discord.Color.orange()
            )
            embed.add_field(name="👤 User", value=user.mention, inline=True)
            embed.add_field(name="⏱️ Duration", value=f"**{duration_minutes} minutes**", inline=True)
            embed.add_field(name="📝 Reason", value=reason or "Server rules violation", inline=True)
            embed.add_field(name="🔨 By Moderator", value=moderator.mention, inline=True)
            embed.set_footer(text="⚡ Timeout automatically expires after duration!")
            
            return f"", True, embed
            
        except Exception as e:
            return f"❌ Timeout nahi ho paya: `{e}`", True, None
    
    async def _cmd_kick(
        self, 
        user: discord.Member, 
        reason: str,
        moderator: discord.Member,
        guild: discord.Guild
    ) -> Tuple[str, bool, Optional[discord.Embed]]:
        """Kick a user - ANNOUNCEMENT STYLE EMBED!"""
        try:
            await user.kick(reason=f"Via AI by {moderator}: {reason}")
            
            embed = discord.Embed(
                title="╔═════════════════════════════════╗\n║  👢  USER KICKED!                 ║\n╚═════════════════════════════════╝",
                description=f"**{user.display_name}** ko server se kick kar diya gaya!",
                color=discord.Color.red()
            )
            embed.add_field(name="👤 Kicked User", value=f"{user.mention} (`{user.id}`)", inline=True)
            embed.add_field(name="📝 Reason", value=reason or "Server rules violation", inline=True)
            embed.add_field(name="🔨 Kicked By", value=moderator.mention, inline=True)
            embed.add_field(name="⏰ Time", value=datetime.now().strftime("%I:%M %p | %d %b %Y"), inline=True)
            embed.set_footer(text="🤖 Ophelia AI 2.0 • Moderation Action")
            
            return f"", True, embed
            
        except Exception as e:
            return f"❌ Kick nahi ho paya: `{e}`", True, None
    
    async def _cmd_ban(
        self, 
        user: discord.Member, 
        reason: str,
        moderator: discord.Member,
        guild: discord.Guild
    ) -> Tuple[str, bool, Optional[discord.Embed]]:
        """Ban a user - ANNOUNCEMENT STYLE EMBED!"""
        try:
            await user.ban(reason=f"Via AI by {moderator}: {reason}", delete_message_days=0)
            
            embed = discord.Embed(
                title="╔═════════════════════════════════╗\n║  🚫  USER BANNED!                 ║\n╚═════════════════════════════════╝",
                description=f"**{user.display_name}** ko permanently ban kar diya gaya!",
                color=discord.Color.dark_red()
            )
            embed.add_field(name="🚫 Banned User", value=f"{user.mention} (`{user.id}`)", inline=True)
            embed.add_field(name="📝 Reason", value=reason or "Server rules violation", inline=True)
            embed.add_field(name="🔨 Banned By", value=moderator.mention, inline=True)
            embed.add_field(name="⏰ Time", value=datetime.now().strftime("%I:%M %p | %d %b %Y"), inline=True)
            embed.set_footer(text="🤖 Ophelia AI 2.0 • Permanent Ban")
            
            return f"", True, embed
            
        except Exception as e:
            return f"❌ Ban nahi ho paya: `{e}`", True, None
    
    async def _cmd_mute(
        self, 
        user: discord.Member, 
        moderator: discord.Member,
        guild: discord.Guild
    ) -> Tuple[str, bool, Optional[discord.Embed]]:
        """Mute a user - NICE EMBED STYLE!"""
        try:
            await user.timeout(timedelta(minutes=5), reason=f"Muted via AI by {moderator}")
            
            embed = discord.Embed(
                title="╔═════════════════════════════════╗\n║  🔇  USER MUTED!                  ║\n╚═════════════════════════════════╝",
                description=f"**{user.display_name}** ko mute kar diya gaya!",
                color=discord.Color.orange()
            )
            embed.add_field(name="🔇 Muted User", value=user.mention, inline=True)
            embed.add_field(name="⏱️ Duration", value="5 minutes", inline=True)
            embed.add_field(name="🔨 Muted By", value=moderator.mention, inline=True)
            embed.set_footer(text="🤖 Auto-unmute after 5 minutes")
            
            return f"", True, embed
            
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
                title="╔═════════════════════════════════╗\n║  ✅  CHANNEL CREATED!              ║\n╚═════════════════════════════════╝",
                description=f"Naya channel **#{new_channel.name}** bana diya gaya!",
                color=discord.Color.green()
            )
            embed.add_field(name="📝 Name", value=f"#{new_channel.name}", inline=True)
            embed.add_field(name="📋 Type", value=info["type"].title(), inline=True)
            embed.add_field(name="🆔 ID", value=f"`{new_channel.id}`", inline=True)
            
            return f"", True, embed
            
        except Exception as e:
            return f"❌ Channel nahi bana: `{e}`", True, None
    
    async def _cmd_create_role(self, info: Dict[str, str], guild: discord.Guild) -> Tuple[str, bool, Optional[discord.Embed]]:
        """Create a new role"""
        try:
            new_role = await guild.create_role(name=info["name"], color=info["color"])
            
            embed = discord.Embed(
                title="╔═════════════════════════════════╗\n║  ✅  ROLE CREATED!                 ║\n╚═════════════════════════════════╝",
                description=f"Naya role **@{new_role.name}** bana diya gaya!",
                color=info["color"]
            )
            embed.add_field(name="📝 Name", value=f"@{new_role.name}", inline=True)
            embed.add_field(name="🎨 Color", value=str(info["color"]), inline=True)
            embed.add_field(name="🆔 ID", value=f"`{new_role.id}`", inline=True)
            
            return f"", True, embed
            
        except Exception as e:
            return f"❌ Role nahi bana: `{e}`", True, None
    
    async def _cmd_send_message(self, info: Dict, author: discord.Member) -> Tuple[str, bool, Optional[discord.Embed]]:
        """Send message to a channel"""
        try:
            channel = info["channel"]
            content = info["content"]
            
            sent_msg = await channel.send(content)
            
            embed = discord.Embed(
                title="╔═════════════════════════════════╗\n║  ✅  MESSAGE SENT!                 ║\n╚═════════════════════════════════╝",
                color=discord.Color.green()
            )
            embed.add_field(name="📍 Channel", value=f"<#{channel.id}>", inline=True)
            embed.add_field(name="Message Preview", value=content[:100] + ("..." if len(content) > 100 else ""), inline=False)
            embed.set_footer(text=f"Sent by {author.display_name}")
            
            return f"", True, embed
            
        except Exception as e:
            return f"❌ Message nahi bhej paya: `{e}`", True, None
    
    async def _cmd_send_embed(self, info: Dict, channel: discord.TextChannel) -> Tuple[str, bool, Optional[discord.Embed]]:
        """Send an embedded message"""
        colors = {
            "blue": discord.Color.blue(), "red": discord.Color.red(),
            "green": discord.Color.green(), "purple": discord.Color.purple(),
            "gold": discord.Color.gold(), "blurple": discord.Color.blurple()
        }
        color = discord.Color.blurple()
        
        embed = discord.Embed(
            title=info["title"],
            description=info["description"],
            color=color
        )
        embed.set_footer(text="🤖 Ophelia AI 2.0 • Embed Generated")
        
        await channel.send(embed=embed)
        
        return f"✅ Embed bhej diya #{channel.name} me!", True, None
    
    async def _cmd_add_reaction(self, emoji: str, message: discord.Message) -> Tuple[str, bool, Optional[discord.Embed]]:
        """Add reaction to a message"""
        try:
            await message.add_reaction(emoji)
            return f"✅ Reaction {emoji} add kar diya!", True, None
        except Exception as e:
            return f"❌ Reaction add nahi ho paya: `{e}`", True, None
    
    async def _cmd_clear_messages(self, count: int, channel: discord.TextChannel) -> Tuple[str, bool, Optional[discord.Embed]]:
        """Delete messages"""
        try:
            deleted = await channel.purge(limit=count)
            
            embed = discord.Embed(
                title="╔═════════════════════════════════╗\n║  🗑️  MESSAGES CLEARED!              ║\n╚═════════════════════════════════╝",
                description=f"**{len(deleted)}** messages delete kar diye!",
                color=discord.Color.dark_blue()
            )
            embed.add_field(name="🗑️ Deleted Count", value=f"**{len(deleted)}** messages", inline=True)
            embed.add_field(name="📍 Channel", value=f"<#{channel.id}>", inline=True)
            
            return f"", True, embed
            
        except Exception as e:
            return f"❌ Messages delete nahi hue: `{e}`", True, None
    
    async def _cmd_show_help(self, author: discord.Member) -> Tuple[str, bool, Optional[discord.Embed]]:
        """Show help with available commands"""
        is_own = is_owner(author.id)
        
        embed = discord.Embed(
            title="╔════════════════════════════════════════════════╗\n║  🤖 OPHELIA AI 2.0 - COMMAND LIST                   ║\n╚════════════════════════════════════════════════╝",
            description="**Natural Language Commands** — Sirf bolno, kaam ho jayega!",
            color=discord.Color.blurple()
        )
        
        # Everyone commands
        embed.add_field(
            name="👥 EVERYONE CAN USE",
            value=(
                "`avatar dikhao` — User's profile pic\n"
                "`info batao` — User/server info\n"
                "`server info` — Full server stats\n"
                "`owner kon hai` — Show bot owners\n"
                "`help` — Ye list dikhao"
            ),
            inline=False
        )
        
        # Mod/Owner commands
        if is_own or author.guild_permissions.manage_guild:
            embed.add_field(
                name="🔨 MODERATION (Owners/Mods)",
                value=(
                    "`isko kick karo` — Kick user\n"
                    "`iska ban kar do` — Ban user\n"
                    "`timeout do 10 min` — Timeout user\n"
                    "`mute karo` — Mute for 5 min\n"
                    "`50 clear karo` — Delete messages"
                ),
                inline=False
            )
        
        # Owner only
        if is_own:
            embed.add_field(
                name="👑 OWNER ONLY",
                value=(
                    "`status set karo playing X` — Bot status\n"
                    "`nickname change karo X` — Bot name\n"
                    "`channel banao X` — New channel\n"
                    "`role banao X` — New role\n"
                    "`#channel me bhejo X` — Send message"
                ),
                inline=False
            )
        
        embed.set_footer(text="💡 Tip: @Ophelia [command] — Natural language works!")
        
        return f"", True, embed


# Global instance
natural_command_parser: Optional[NaturalCommandParser] = None


def init_natural_commands(bot: commands.Bot) -> NaturalCommandParser:
    """Initialize global natural command parser"""
    global natural_command_parser
    natural_command_parser = NaturalCommandParser(bot)
    return natural_command_parser


# Alias for backwards compatibility
init_natural_parser = init_natural_commands


def get_natural_parser() -> NaturalCommandParser:
    """Get global parser instance"""
    if natural_command_parser is None:
        raise RuntimeError("Natural command parser not initialized!")
    return natural_command_parser


# Alias for consistency
get_natural_commands = get_natural_parser
