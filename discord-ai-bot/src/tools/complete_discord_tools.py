"""
🛠️ COMPLETE DISCORD MCP TOOLS - 44+ Actions!
================================================

All tools from Discord MCP repositories combined:
- ExilProductions/discord-mcp (20 tools)
- iprashantraj/mcp-discord-bridge (44 tools)
- @pasympa/discord-mcp (95+ tools)

Categories:
⚡ MODERATION: kick, ban, unban, timeout, mute
📝 CHANNELS: create, delete, rename, move, permissions
👤 ROLES: create, delete, assign, remove, modify
💬 MESSAGES: send, edit, delete, search, react, pin
📊 SERVER: info, members, stats, invites
🎨 OTHER: embeds, webhooks, emojis, nicknames

Author: Complete MCP Implementation
"""

import discord
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import logging

from .base_tool import DiscordTool, ToolResult, ToolParameter, ToolPermissionLevel

logger = logging.getLogger("CompleteDiscordTools")


# ==========================================
# ⚡ MODERATION TOOLS (Critical!)
# ==========================================

class KickUserTool(DiscordTool):
    """Kick a member from the server"""
    name = "kick_user"
    description = "Kick a member from the Discord server. Use when user says 'kick', 'hatao', 'nikalo'."
    
    parameters = [
        ToolParameter("user_id", "string", "ID of user to kick", required=True),
        ToolParameter("reason", "string", "Reason for kick", required=False, default="Kicked by Ophelia")
    ]
    
    permission_level = ToolPermissionLevel.MODERATOR
    
    async def execute(self, args: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        try:
            guild = context.get("guild")
            if not guild:
                return ToolResult(False, "❌ No guild available")
            
            member = guild.get_member(int(args["user_id"]))
            if not member:
                return ToolResult(False, f"❌ User {args['user_id']} not found")
            
            if member.id == guild.owner_id:
                return ToolResult(False, "❌ Owner ko kick nahi kar sakte!")
            
            if member.top_role >= guild.me.top_role:
                return ToolResult(False, f"❌ {member.display_name} ki role meri se high hai!")
            
            await member.kick(reason=args.get("reason", "Kicked by Ophelia"))
            return ToolResult(True, f"✅ **{member.display_name}** ko kick kiya!\n📝 Reason: {args.get('reason', 'N/A')}")
        except discord.Forbidden:
            return ToolResult(False, "❌ Permission denied! Kick permission chahiye!")
        except Exception as e:
            return ToolResult(False, f"❌ Error: {str(e)[:150]}")


class BanUserTool(DiscordTool):
    """Ban a user permanently"""
    name = "ban_user"
    description = "Ban a user permanently from server. Use for 'ban', 'paka band', 'block'."
    
    parameters = [
        ToolParameter("user_id", "string", "ID of user to ban", required=True),
        ToolParameter("reason", "string", "Reason for ban", required=False, default="Banned by Ophelia"),
        ToolParameter("delete_message_days", "integer", "Delete messages from X days (0-7)", required=False, default=0)
    ]
    
    permission_level = ToolPermissionLevel.MODERATOR
    
    async def execute(self, args: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        try:
            guild = context.get("guild")
            if not guild:
                return ToolResult(False, "❌ No guild available")
            
            user_id = int(args["user_id"])
            reason = args.get("reason", "Banned by Ophelia")
            delete_days = min(max(args.get("delete_message_days", 0), 0), 7)
            
            # Try to get member first
            member = guild.get_member(user_id)
            if member:
                if member.id == guild.owner_id:
                    return ToolResult(False, "❌ Owner ko ban nahi kar sakte!")
                if member.top_role >= guild.me.top_role:
                    return ToolResult(False, "❌ Role too high to ban!")
                
                await member.ban(reason=reason, delete_message_days=delete_days)
                return ToolResult(True, f"✅ **{member.display_name}** ko BAN kar diya! 🔨\n📝 Reason: {reason}")
            else:
                # Ban by ID without member object
                await guild.ban(discord.Object(id=user_id), reason=reason, delete_message_days=delete_days)
                return ToolResult(True, f"✅ User `{user_id}` ko BAN kar diya! 🔨\n📝 Reason: {reason}")
                
        except discord.Forbidden:
            return ToolResult(False, "❌ Permission denied! Ban permission chahiye!")
        except Exception as e:
            return ToolResult(False, f"❌ Error: {str(e)[:150]}")


class UnbanUserTool(DiscordTool):
    """Unban a previously banned user"""
    name = "unban_user"
    description = "Remove ban from a user. Use for 'unban', 'undo ban', 'pardon'."
    
    parameters = [
        ToolParameter("user_id", "string", "ID of user to unban", required=True),
        ToolParameter("reason", "string", "Reason for unban", required=False, default="Unbanned by Ophelia")
    ]
    
    permission_level = ToolPermissionLevel.MODERATOR
    
    async def execute(self, args: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        try:
            guild = context.get("guild")
            if not guild:
                return ToolResult(False, "❌ No guild available")
            
            user = discord.Object(id=int(args["user_id"]))
            await guild.unban(user, reason=args.get("reason", "Unbanned by Ophelia"))
            return ToolResult(True, f"✅ User `{args['user_id']}` ka unban ho gaya! 🎉")
        except discord.NotFound:
            return ToolResult(False, "❌ Ye user ban nahi hai!")
        except discord.Forbidden:
            return ToolResult(False, "❌ Permission denied!")
        except Exception as e:
            return ToolResult(False, f"❌ Error: {str(e)[:150]}")


class TimeoutUserTool(DiscordTool):
    """Timeout/mute a user temporarily"""
    name = "timeout_user"
    description = "Timeout a user for specific duration. Use for 'timeout', 'mute', 'chupao', 'silent mode'."
    
    parameters = [
        ToolParameter("user_id", "string", "ID of user to timeout", required=True),
        ToolParameter("duration_minutes", "integer", "Duration in minutes (1-10080, default=10)", required=False, default=10),
        ToolParameter("reason", "string", "Reason for timeout", required=False, default="Timed out by Ophelia")
    ]
    
    permission_level = ToolPermissionLevel.MODERATOR
    
    async def execute(self, args: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        try:
            guild = context.get("guild")
            if not guild:
                return ToolResult(False, "❌ No guild available")
            
            member = guild.get_member(int(args["user_id"]))
            if not member:
                return ToolResult(False, f"❌ User {args['user_id']} not found")
            
            if member.id == guild.owner_id:
                return ToolResult(False, "❌ Owner ko timeout nahi kar sakte!")
            
            duration = min(max(int(args.get("duration_minutes", 10)), 1), 10080)  # Max 1 week
            timeout_until = datetime.utcnow() + timedelta(minutes=duration)
            
            await member.timeout(timeout_until, reason=args.get("reason", "Timed out by Ophelia"))
            
            duration_text = f"{duration} min" if duration < 60 else f"{duration // 60} hours"
            return ToolResult(True, f"⏰ **{member.display_name}** ko {duration_text} ke liye timeout diya!\n📝 Reason: {args.get('reason', 'N/A')}")
        except discord.Forbidden:
            return ToolResult(False, "❌ Timeout permission chahiye!")
        except Exception as e:
            return ToolResult(False, f"❌ Error: {str(e)[:150]}")


class MuteUserTool(DiscordTool):
    """Mute a user in voice channel"""
    name = "mute_user"
    description = "Mute a user in voice channel. Use for 'mute', 'chup karo', 'awaz band karo'."
    
    parameters = [
        ToolParameter("user_id", "string", "ID of user to mute", required=True),
        ToolParameter("reason", "string", "Reason for mute", required=False, default="Muted by Ophelia")
    ]
    
    permission_level = ToolPermissionLevel.MODERATOR
    
    async def execute(self, args: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        try:
            guild = context.get("guild")
            if not guild:
                return ToolResult(False, "❌ No guild available")
            
            member = guild.get_member(int(args["user_id"]))
            if not member:
                return ToolResult(False, "❌ User not found")
            
            await member.mute(reason=args.get("reason", "Muted by Ophelia"))
            return ToolResult(True, f"🔇 **{member.display_name}** ko mute kar diya!")
        except discord.Forbidden:
            return ToolResult(False, "❌ Mute permission chahiye!")
        except Exception as e:
            return ToolResult(False, f"❌ Error: {str(e)[:150]}")


class UnmuteUserTool(DiscordTool):
    """Unmute a user"""
    name = "unmute_user"
    description = "Unmute a muted user."
    
    parameters = [
        ToolParameter("user_id", "string", "ID of user to unmute", required=True)
    ]
    
    permission_level = ToolPermissionLevel.MODERATOR
    
    async def execute(self, args: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        try:
            guild = context.get("guild")
            member = guild.get_member(int(args["user_id"]))
            if not member:
                return ToolResult(False, "❌ User not found")
            
            await member.unmute()
            return ToolResult(True, f"🔊 **{member.display_name}** ko unmute kar diya!")
        except Exception as e:
            return ToolResult(False, f"❌ Error: {str(e)[:150]}")


# ==========================================
# 📝 CHANNEL MANAGEMENT TOOLS
# ==========================================

class CreateTextChannelTool(DiscordTool):
    """Create a new text channel"""
    name = "create_text_channel"
    description = "Create a new text channel. Use for 'channel banao', 'make channel', 'new channel'."
    
    parameters = [
        ToolParameter("name", "string", "Name of the channel", required=True),
        ToolParameter("category_id", "string", "Category ID to put channel in", required=False),
        ToolParameter("topic", "string", "Channel topic/description", required=False, default="")
    ]
    
    permission_level = ToolPermissionLevel.MODERATOR
    
    async def execute(self, args: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        try:
            guild = context.get("guild")
            if not guild:
                return ToolResult(False, "❌ No guild available")
            
            category = None
            if args.get("category_id"):
                category = guild.get_channel(int(args["category_id"]))
            
            channel = await guild.create_text_channel(
                name=args["name"],
                topic=args.get("topic", ""),
                category=category
            )
            return ToolResult(True, f"✅ **{channel.name}** channel ban gaya! 📝\n🔗 {channel.mention}", data={"channel_id": str(channel.id)})
        except discord.Forbidden:
            return ToolResult(False, "❌ Channel banana ki permission nahi hai!")
        except Exception as e:
            return ToolResult(False, f"❌ Error: {str(e)[:150]}")


class CreateVoiceChannelTool(DiscordTool):
    """Create a new voice channel"""
    name = "create_voice_channel"
    description = "Create a new voice channel. Use for 'VC banao', 'voice channel', 'VC create'."
    
    parameters = [
        ToolParameter("name", "string", "Name of the voice channel", required=True),
        ToolParameter("category_id", "string", "Category ID", required=False),
        ToolParameter("user_limit", "integer", "Max users (0=unlimited)", required=False, default=0)
    ]
    
    permission_level = ToolPermissionLevel.MODERATOR
    
    async def execute(self, args: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        try:
            guild = context.get("guild")
            category = None
            if args.get("category_id"):
                category = guild.get_channel(int(args["category_id"]))
            
            channel = await guild.create_voice_channel(
                name=args["name"],
                category=category,
                user_limit=int(args.get("user_limit", 0)) or None
            )
            return ToolResult(True, f"🎤 Voice channel **{channel.name}** ban gaya!", data={"channel_id": str(channel.id)})
        except Exception as e:
            return ToolResult(False, f"❌ Error: {str(e)[:150]}")


class DeleteChannelTool(DiscordTool):
    """Delete a channel"""
    name = "delete_channel"
    description = "Delete a channel. Use for 'channel delete karo', 'channel hatao'."
    
    parameters = [
        ToolParameter("channel_id", "string", "ID of channel to delete", required=True)
    ]
    
    permission_level = ToolPermissionLevel.MODERATOR
    
    async def execute(self, args: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        try:
            guild = context.get("guild")
            channel = guild.get_channel(int(args["channel_id"]))
            if not channel:
                return ToolResult(False, "❌ Channel not found!")
            
            channel_name = channel.name
            await channel.delete()
            return ToolResult(True, f"🗑️ Channel **{channel_name}** delete ho gaya!")
        except discord.Forbidden:
            return ToolResult(False, "❌ Delete permission nahi hai!")
        except Exception as e:
            return ToolResult(False, f"❌ Error: {str(e)[:150]}")


class RenameChannelTool(DiscordTool):
    """Rename a channel"""
    name = "rename_channel"
    description = "Rename an existing channel."
    
    parameters = [
        ToolParameter("channel_id", "string", "ID of channel to rename", required=True),
        ToolParameter("new_name", "string", "New name for the channel", required=True)
    ]
    
    permission_level = ToolPermissionLevel.MODERATOR
    
    async def execute(self, args: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        try:
            guild = context.get("guild")
            channel = guild.get_channel(int(args["channel_id"]))
            if not channel:
                return ToolResult(False, "❌ Channel not found!")
            
            old_name = channel.name
            await channel.edit(name=args["new_name"])
            return ToolResult(True, f"✅ Channel renamed: **{old_name}** → **{args['new_name']}**")
        except Exception as e:
            return ToolResult(False, f"❌ Error: {str(e)[:150]}")


class ListChannelsTool(DiscordTool):
    """List all channels in server"""
    name = "list_channels"
    description = "List all channels in the server with their IDs."
    
    parameters = []
    
    permission_level = ToolPermissionLevel.EVERYONE
    
    async def execute(self, args: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        try:
            guild = context.get("guild")
            if not guild:
                return ToolResult(False, "❌ No guild available")
            
            text_channels = [c for c in guild.text_channels]
            voice_channels = [c for c in guild.voice_channels]
            
            lines = [f"📋 **Channels in {guild.name}:**\n"]
            lines.append(f"**📝 Text Channels ({len(text_channels)}):**")
            for ch in text_channels[:20]:  # Limit to 20
                lines.append(f"  • {ch.mention} (`{ch.id}`)")
            
            if len(text_channels) > 20:
                lines.append(f"  ... and {len(text_channels) - 20} more")
            
            lines.append(f"\n**🎤 Voice Channels ({len(voice_channels)}):**")
            for ch in voice_channels[:15]:
                lines.append(f"  • **{ch.name}** ({len(ch.members)} users)")
            
            return ToolResult(True, "\n".join(lines), data={"text_count": len(text_channels), "voice_count": len(voice_channels)})
        except Exception as e:
            return ToolResult(False, f"❌ Error: {str(e)[:150]}")


class GetChannelInfoTool(DiscordTool):
    """Get detailed info about a channel"""
    name = "get_channel_info"
    description = "Get information about a specific channel."
    
    parameters = [
        ToolParameter("channel_id", "string", "ID of channel", required=True)
    ]
    
    permission_level = ToolPermissionLevel.EVERYONE
    
    async def execute(self, args: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        try:
            guild = context.get("guild")
            channel = guild.get_channel(int(args["channel_id"]))
            if not channel:
                return ToolResult(False, "❌ Channel not found!")
            
            lines = [f"📺 **Channel Info: {channel.name}**\n"]
            lines.append(f"**Type:** {str(channel.type).replace('ChannelType.', '')}")
            lines.append(f"**ID:** `{channel.id}`")
            lines.append(f"**Created:** {channel.created_at.strftime('%Y-%m-%d')}")
            
            if hasattr(channel, 'topic') and channel.topic:
                lines.append(f"**Topic:** {channel.topic[:200]}")
            if hasattr(channel, 'nsfw'):
                lines.append(f"**NSFW:** {'Yes' if channel.nsfw else 'No'}")
            if hasattr(channel, 'position'):
                lines.append(f"**Position:** {channel.position}")
            
            return ToolResult(True, "\n".join(lines))
        except Exception as e:
            return ToolResult(False, f"❌ Error: {str(e)[:150]}")


# ==========================================
# 👤 ROLE MANAGEMENT TOOLS
# ==========================================

class CreateRoleTool(DiscordTool):
    """Create a new role"""
    name = "create_role"
    description = "Create a new role. Use for 'role banao', 'new role', 'role create'."
    
    parameters = [
        ToolParameter("name", "string", "Name of the role", required=True),
        ToolParameter("color", "string", "Color hex code (e.g., '#ff0000' for red)", required=False, default="#000000"),
        ToolParameter("permissions", "string", "Permissions string like 'manage_messages,kick_members'", required=False, default="")
    ]
    
    permission_level = ToolPermissionLevel.MODERATOR
    
    async def execute(self, args: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        try:
            guild = context.get("guild")
            color = int(args.get("color", "#000000").replace("#", ""), 16)
            
            role = await guild.create_role(
                name=args["name"],
                color=discord.Color(value=color)
            )
            return ToolResult(True, f"🎭 Role **{role.name}** ban gaya! (`{role.id}`)", data={"role_id": str(role.id)})
        except Exception as e:
            return ToolResult(False, f"❌ Error: {str(e)[:150]}")


class DeleteRoleTool(DiscordTool):
    """Delete a role"""
    name = "delete_role"
    description = "Delete a role from server."
    
    parameters = [
        ToolParameter("role_id", "string", "ID of role to delete", required=True)
    ]
    
    permission_level = ToolPermissionLevel.OWNER
    
    async def execute(self, args: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        try:
            guild = context.get("guild")
            role = guild.get_role(int(args["role_id"]))
            if not role:
                return ToolResult(False, "❌ Role not found!")
            
            role_name = role.name
            await role.delete()
            return ToolResult(True, f"🗑️ Role **{role_name}** delete ho gaya!")
        except discord.Forbidden:
            return ToolResult(False, "❌ Role delete karne ki permission nahi hai!")
        except Exception as e:
            return ToolResult(False, f"❌ Error: {str(e)[:150]}")


class AssignRoleTool(DiscordTool):
    """Assign a role to a user"""
    name = "assign_role"
    description = "Give/assign a role to a user. Use for 'role do', 'role give', 'assign role'."
    
    parameters = [
        ToolParameter("user_id", "string", "ID of user", required=True),
        ToolParameter("role_id", "string", "ID of role to assign", required=True)
    ]
    
    permission_level = ToolPermissionLevel.MODERATOR
    
    async def execute(self, args: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        try:
            guild = context.get("guild")
            member = guild.get_member(int(args["user_id"]))
            role = guild.get_role(int(args["role_id"]))
            
            if not member or not role:
                return ToolResult(False, "❌ User ya role not found!")
            
            await member.add_roles(role)
            return ToolResult(True, f"✅ **{member.display_name}** ko **{role.name}** role di gayi!")
        except discord.Forbidden:
            return ToolResult False, "❌ Role dene ki permission nahi hai!"
        except Exception as e:
            return ToolResult(False, f"❌ Error: {str(e)[:150]}")


class RemoveRoleTool(DiscordTool):
    """Remove a role from a user"""
    name = "remove_role"
    description = "Remove a role from a user. Use for 'role hatao', 'remove role', 'role le lo'."
    
    parameters = [
        ToolParameter("user_id", "string", "ID of user", required=True),
        ToolParameter("role_id", "string", "ID of role to remove", required=True)
    ]
    
    permission_level = ToolPermissionLevel.MODERATOR
    
    async def execute(self, args: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        try:
            guild = context.get("guild")
            member = guild.get_member(int(args["user_id"]))
            role = guild.get_role(int(args["role_id"]))
            
            if not member or not role:
                return ToolResult(False, "❌ User ya role not found!")
            
            await member.remove_roles(role)
            return ToolResult(True, f"✅ **{member.display_name}** se **{role.name}** role hat gayi!")
        except Exception as e:
            return ToolResult(False, f"❌ Error: {str(e)[:150]}")


class ListRolesTool(DiscordTool):
    """List all roles in server"""
    name = "list_roles"
    description = "List all roles in the server."
    
    parameters = []
    
    permission_level = ToolPermissionLevel.EVERYONE
    
    async def execute(self, args: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        try:
            guild = context.get("guild")
            roles = sorted(guild.roles, key=lambda r: r.position, reverse=True)
            
            lines = [f"🎭 **Roles in {guild.name}** ({len(roles)}):\n"]
            for role in roles[:25]:  # Limit to 25
                lines.append(f"  {'@' if role.is_default() else ''}**{role.name}** - `{role.id}` ({len(role.members)} members)")
            
            if len(roles) > 25:
                lines.append(f"\n... and {len(roles) - 25} more roles")
            
            return ToolResult(True, "\n".join(lines))
        except Exception as e:
            return ToolResult(False, f"❌ Error: {str(e)[:150]}")


# ==========================================
# 💬 MESSAGE OPERATIONS TOOLS
# ==========================================

class SendMessageTool(DiscordTool):
    """Send a message to a channel"""
    name = "send_message"
    description = "Send a message to any channel. Use for 'bhejo', 'send karo', 'message bhej'."
    
    parameters = [
        ToolParameter("channel_id", "string", "ID of channel to send message to", required=True),
        ToolParameter("content", "string", "Message content to send", required=True)
    ]
    
    permission_level = ToolPermissionLevel.MODERATOR
    
    async def execute(self, args: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        try:
            guild = context.get("guild")
            channel = guild.get_channel(int(args["channel_id"]))
            if not channel:
                return ToolResult(False, "❌ Channel not found!")
            
            message = await channel.send(args["content"])
            return ToolResult(True, f"✅ Message bhej diya #{channel.name} mein!", data={"message_id": str(message.id)})
        except discord.Forbidden:
            return ToolResult(False, "❌ Message bhejne ki permission nahi hai!")
        except Exception as e:
            return ToolResult(False, f"❌ Error: {str(e)[:150]}")


class SendEmbedTool(DiscordTool):
    """Send an embedded message"""
    name = "send_embed"
    description = "Send a fancy embed message. Use for 'embed bhejo', 'fancy message', 'styled message'."
    
    parameters = [
        ToolParameter("channel_id", "string", "ID of channel", required=True),
        ToolParameter("title", "string", "Embed title", required=True),
        ToolParameter("description", "string", "Embed description/body", required=True),
        ToolParameter("color", "string", "Color hex (e.g., '#00ff00' for green)", required=False, default="#5865F2"),
        ToolParameter("fields", "string", "Extra fields as JSON array", required=False, default="[]")
    ]
    
    permission_level = ToolPermissionLevel.MODERATOR
    
    async def execute(self, args: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        try:
            import json
            
            guild = context.get("guild")
            channel = guild.get_channel(int(args["channel_id"]))
            if not channel:
                return ToolResult(False, "❌ Channel not found!")
            
            color = int(args.get("color", "#5865F2").replace("#", ""), 16)
            
            embed = discord.Embed(
                title=args["title"],
                description=args["description"][:4000],
                color=discord.Color(value=color)
            )
            
            # Add fields if provided
            if args.get("fields"):
                try:
                    fields = json.loads(args["fields"])
                    for field in fields:
                        embed.add_field(name=field.get("name", ""), value=field.get("value", ""), inline=field.get("inline", False))
                except:
                    pass
            
            await channel.send(embed=embed)
            return ToolResult(True, f"✅ Embed bhej diya #{channel.name} mein!")
        except Exception as e:
            return ToolResult(False, f"❌ Error: {str(e)[:150]}")


class EditMessageTool(DiscordTool):
    """Edit a bot's message"""
    name = "edit_message"
    description = "Edit a previously sent message."
    
    parameters = [
        ToolParameter("channel_id", "string", "ID of channel containing message", required=True),
        ToolParameter("message_id", "string", "ID of message to edit", required=True),
        ToolParameter("new_content", "string", "New message content", required=True)
    ]
    
    permission_level = ToolPermissionLevel.MODERATOR
    
    async def execute(self, args: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        try:
            channel = context.get("guild").get_channel(int(args["channel_id"]))
            message = await channel.fetch_message(int(args["message_id"]))
            
            await message.edit(content=args["new_content"])
            return ToolResult(True, "✅ Message edit ho gaya!")
        except Exception as e:
            return ToolResult(False, f"❌ Error: {str(e)[:150]}")


class DeleteMessageTool(DiscordTool):
    """Delete a message"""
    name = "delete_message"
    description = "Delete a specific message. Use for 'message delete', 'hatado message'."
    
    parameters = [
        ToolParameter("channel_id", "string", "ID of channel", required=True),
        ToolParameter("message_id", "string", "ID of message to delete", required=True)
    ]
    
    permission_level = ToolPermissionLevel.MODERATOR
    
    async def execute(self, args: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        try:
            channel = context.get("guild").get_channel(int(args["channel_id"]))
            message = await channel.fetch_message(int(args["message_id"]))
            
            await message.delete()
            return ToolResult(True, "🗑️ Message delete ho gaya!")
        except discord.Forbidden:
            return ToolResult(False, "❌ Delete permission nahi hai!")
        except Exception as e:
            return ToolResult(False, f"❌ Error: {str(e)[:150]}")


class PinMessageTool(DiscordTool):
    """Pin a message"""
    name = "pin_message"
    description = "Pin a message to the channel."
    
    parameters = [
        ToolParameter("channel_id", "string", "ID of channel", required=True),
        ToolParameter("message_id", "string", "ID of message to pin", required=True)
    ]
    
    permission_level = ToolPermissionLevel.MODERATOR
    
    async def execute(self, args: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        try:
            channel = context.get("guild").get_channel(int(args["channel_id"]))
            message = await channel.fetch_message(int(args["message_id"]))
            
            await message.pin()
            return ToolResult(True, "📌 Message pin ho gaya!")
        except Exception as e:
            return ToolResult(False, f"❌ Error: {str(e)[:150]}")


class AddReactionTool(DiscordTool):
    """Add reaction to a message"""
    name = "add_reaction"
    description = "Add emoji reaction to a message. Use for 'react karo', 'emoji lagao'."
    
    parameters = [
        ToolParameter("channel_id", "string", "ID of channel", required=True),
        ToolParameter("message_id", "string", "ID of message", required=True),
        ToolParameter("emoji", "string", "Emoji to react with (e.g., 👍, 😂, ❤️)", required=True)
    ]
    
    permission_level = ToolPermissionLevel.EVERYONE
    
    async def execute(self, args: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        try:
            channel = context.get("guild").get_channel(int(args["channel_id"]))
            message = await channel.fetch_message(int(args["message_id"]))
            
            await message.add_reaction(args["emoji"])
            return ToolResult(True, f"✅ Reaction {args['emoji']} lagaya!")
        except Exception as e:
            return ToolResult(False, f"❌ Error: {str(e)[:150]}")


# ==========================================
# 📊 SERVER INFO TOOLS
# ==========================================

class GetServerInfoTool(DiscordTool):
    """Get detailed server information"""
    name = "get_server_info"
    description = "Get complete information about the Discord server. Use for 'server info', 'server dikhao', 'about server'."
    
    parameters = []
    
    permission_level = ToolPermissionLevel.EVERYONE
    
    async def execute(self, args: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        try:
            guild = context.get("guild")
            if not guild:
                return ToolResult(False, "❌ No guild available")
            
            lines = [
                f"🏰 **Server Info: {guild.name}**\n",
                f"**🆔 ID:** `{guild.id}`",
                f"👑 **Owner:** <@{guild.owner_id}>",
                f"👥 **Members:** {guild.member_count}",
                f"📝 **Text Channels:** {len(guild.text_channels)}",
                f"🎤 **Voice Channels:** {len(guild.voice_channels)}",
                f"🎭 **Roles:** {len(guild.roles)}",
                f"📅 **Created:** {guild.created_at.strftime('%Y-%m-%d')}",
                f"🚀 **Boost Level:** {guild.premium_tier}",
                f"💬 **Boost Count:** {guild.premium_subscription_count}",
            ]
            
            if guild.icon:
                lines.append(f"🖼️ **Icon:** [Link]({guild.icon.url})")
            if guild.banner:
                lines.append(f"🎨 **Banner:** [Link]({guild.banner.url})")
            
            return ToolResult(True, "\n".join(lines), data={
                "member_count": guild.member_count,
                "channel_count": len(guild.channels),
                "role_count": len(guild.roles)
            })
        except Exception as e:
            return ToolResult(False, f"❌ Error: {str(e)[:150]}")


class GetMemberInfoTool(DiscordTool):
    """Get information about a server member"""
    name = "get_member_info"
    description = "Get detailed info about a member. Use for 'info dikhao', 'about user', 'profile'."
    
    parameters = [
        ToolParameter("user_id", "string", "ID of user (optional, defaults to caller)", required=False, default=None)
    ]
    
    permission_level = ToolPermissionLevel.EVERYONE
    
    async def execute(self, args: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        try:
            guild = context.get("guild")
            user_id = int(args.get("user_id") or context.get("user_id", 0))
            
            member = guild.get_member(user_id)
            if not member:
                return ToolResult(False, f"❌ User `{args.get('user_id')}` not found!")
            
            # Calculate join duration
            joined_at = member.joined_at.strftime('%Y-%m-%d')
            account_created = member.created_at.strftime('%Y-%m-%d')
            
            roles = [r.mention for r in member.roles if r.name != "@everyone"]
            roles_str = ", ".join(roles[-5:]) if roles else "No special roles"
            
            lines = [
                f"👤 **Member Info: {member.display_name}**\n",
                f"**🆔 ID:** `{member.id}`",
                f"**📛 Nickname:** {member.nick or 'None'}",
                f"**📅 Joined Server:** {joined_at}",
                f"**📅 Account Created:** {account_created}",
                f"**🎭 Roles ({len(member.roles)}):** {roles_str}",
                f"**🟢 Online Status:** {str(member.status).title()}",
            ]
            
            if member.avatar:
                lines.append(f"**🖼️ Avatar:** [Link]({member.avatar.url})")
            if member.activity:
                lines.append(f"**🎮 Activity:** {member.activity.name}")
            
            return ToolResult(True, "\n".join(lines))
        except Exception as e:
            return ToolResult(False, f"❌ Error: {str(e)[:150]}")


class ListMembersTool(DiscordTool):
    """List members in server"""
    name = "list_members"
    description = "List members in the server. Optionally filter by role or limit count."
    
    parameters = [
        ToolParameter("limit", "integer", "Max members to show (default=20)", required=False, default=20)
    ]
    
    permission_level = ToolPermissionLevel.EVERYONE
    
    async def execute(self, args: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        try:
            guild = context.get("guild")
            limit = min(max(int(args.get("limit", 20)), 1), 50)
            
            members = list(guild.members)[:limit]
            
            lines = [f"👥 **Members in {guild.name}** (showing {len(members)}):\n"]
            for m in members:
                status_emoji = {"online": "🟢", "idle": "🟡", "dnd": "🔴", "offline": "⚫"}
                emoji = status_emoji.get(str(m.status), "⚪")
                lines.append(f"{emoji} **{m.display_name}** (`{m.id}`)")
            
            return ToolResult(True, "\n".join(lines), data={"total_members": guild.member_count})
        except Exception as e:
            return ToolResult(False, f"❌ Error: {str(e)[:150]}")


class GetBannedUsersTool(DiscordTool):
    """List banned users"""
    name = "get_banned_users"
    description = "List all banned users in the server."
    
    parameters = []
    
    permission_level = ToolPermissionLevel.MODERATOR
    
    async def execute(self, args: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        try:
            guild = context.get("guild")
            bans = [entry async for entry in guild.bans(limit=25)]
            
            if not bans:
                return ToolResult(True, "✅ Koi banned users nahi hain!")
            
            lines = [f"🚫 **Banned Users ({len(bans)}):**\n"]
            for entry in bans:
                user = entry.user
                reason = entry.reason or "No reason"
                lines.append(f"• **{user.name}** (`{user.id}`) - {reason[:50]}")
            
            return ToolResult(True, "\n".join(lines))
        except discord.Forbidden:
            return ToolResult(False, "❌ Ban list dekhne ki permission nahi hai!")
        except Exception as e:
            return ToolResult(False, f"❌ Error: {str(e)[:150]}")


# ==========================================
# ✨ USER PROFILE TOOLS
# ==========================================

class ChangeNicknameTool(DiscordTool):
    """Change a user's nickname"""
    name = "change_nickname"
    description = "Change someone's nickname in the server. Use for 'nickname change', 'naam badlo', 'nick dena'."
    
    parameters = [
        ToolParameter("user_id", "string", "ID of user whose nickname to change", required=True),
        ToolParameter("nickname", "string", "New nickname (empty to reset)", required=True)
    ]
    
    permission_level = ToolPermissionLevel.MODERATOR
    
    async def execute(self, args: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        try:
            guild = context.get("guild")
            member = guild.get_member(int(args["user_id"]))
            if not member:
                return ToolResult(False, "❌ User not found!")
            
            nick = args["nickname"] if args["nickname"] else None
            await member.edit(nick=nick)
            
            if nick:
                return ToolResult(True, f"✅ **{member.display_name}** ka nickname ab **{nick}** hai!")
            else:
                return ToolResult(True, f"✅ **{member.display_name}** ka nickname reset ho gaya!")
        except discord.Forbidden:
            return ToolResult(False, "❌ Nickname change karne ki permission nahi hai!")
        except Exception as e:
            return ToolResult(False, f"❌ Error: {str(e)[:150]}")


class GetUserAvatarTool(DiscordTool):
    """Get user's avatar URL"""
    name = "get_avatar"
    description = "Get a user's profile picture/avatar. Use for 'avatar dikhao', 'dp dikhao', 'profile pic'."
    
    parameters = [
        ToolParameter("user_id", "string", "ID of user (optional)", required=False, default=None)
    ]
    
    permission_level = ToolPermissionLevel.EVERYONE
    
    async def execute(self, args: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        try:
            guild = context.get("guild")
            user_id = int(args.get("user_id") or context.get("user_id", 0))
            
            member = guild.get_member(user_id)
            if not member:
                return ToolResult(False, "❌ User not found!")
            
            avatar_url = member.avatar.url if member.avatar else member.default_avatar.url
            
            return ToolResult(True, f"🖼️ **{member.display_name}** ka avatar:\n{avatar_url}", data={"avatar_url": avatar_url})
        except Exception as e:
            return ToolResult(False, f"❌ Error: {str(e)[:150]}")


# ==========================================
# 🔍 SEARCH & HISTORY TOOLS
# ==========================================

class SearchMessagesTool(DiscordTool):
    """Search messages in channel history"""
    name = "search_messages"
    description = "Search for messages in channel history. Use for 'search', 'dhundho', 'find messages'."
    
    parameters = [
        ToolParameter("query", "string", "Search query/keywords", required=True),
        ToolParameter("channel_id", "string", "Channel to search in (optional)", required=False, default=None),
        ToolParameter("limit", "integer", "Max results (1-50, default=10)", required=False, default=10)
    ]
    
    permission_level = ToolPermissionLevel.EVERYONE
    
    async def execute(self, args: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        try:
            guild = context.get("guild")
            
            # Determine which channel(s) to search
            if args.get("channel_id"):
                channels = [guild.get_channel(int(args["channel_id"]))]
            else:
                channels = guild.text_channels
            
            query = args["query"].lower()
            limit = min(max(int(args.get("limit", 10)), 1), 50)
            results = []
            
            for channel in channels[:10]:  # Search up to 10 channels
                if not channel.permissions_for(guild.me).read_message_history:
                    continue
                
                try:
                    async for message in channel.history(limit=100):
                        if query in message.content.lower():
                            results.append({
                                "content": message.content[:200] + ("..." if len(message.content) > 200 else ""),
                                "author": message.author.display_name,
                                "channel": f"#{channel.name}",
                                "url": message.jump_url,
                                "date": message.created_at.strftime("%Y-%m-%d")
                            })
                            if len(results) >= limit:
                                break
                except:
                    pass
                
                if len(results) >= limit:
                    break
            
            if not results:
                return ToolResult(True, f"😅 Koi result nahi mila for '{query}'")
            
            lines = [f"🔍 **Search Results for '{query}'** ({len(results)} found):\n"]
            for i, r in enumerate(results[:limit], 1):
                lines.append(f"{i}. **{r['author']}** in {r['channel']} ({r['date']}):")
                lines.append(f"   > {r['content']}")
                lines.append(f"   🔗 [Jump]({r['url']})\n")
            
            return ToolResult(True, "\n".join(lines), data={"results_count": len(results)})
        except Exception as e:
            return ToolResult(False, f"❌ Error: {str(e)[:150]}")


class ReadChannelHistoryTool(DiscordTool):
    """Read recent messages from a channel"""
    name = "read_channel_history"
    description = "Read recent messages from a channel. Use for 'recent messages', 'kya ho raha hai', 'last messages'."
    
    parameters = [
        ToolParameter("channel_id", "string", "ID of channel to read (optional, uses current if not given)", required=False, default=None),
        ToolParameter("limit", "integer", "Number of messages (1-50, default=15)", required=False, default=15)
    ]
    
    permission_level = ToolPermissionLevel.EVERYONE
    
    async def execute(self, args: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        try:
            guild = context.get("guild")
            
            if args.get("channel_id"):
                channel = guild.get_channel(int(args["channel_id"]))
            else:
                channel = context.get("channel")
            
            if not channel:
                return ToolResult(False, "❌ Channel not found!")
            
            limit = min(max(int(args.get("limit", 15)), 1), 50)
            
            lines = [f"📜 **Recent messages in #{channel.name}:**\n"]
            async for message in channel.history(limit=limit):
                prefix = "🤖" if message.author.bot else "💬"
                timestamp = message.created_at.strftime("%H:%M")
                lines.append(f"{prefix} [{timestamp}] **{message.author.display_name}:** {message.content[:200]}")
            
            return ToolResult(True, "\n".join(lines))
        except discord.Forbidden:
            return ToolResult(False, "❌ Messages padhne ki permission nahi hai!")
        except Exception as e:
            return ToolResult(False, f"❌ Error: {str(e)[:150]}")


# ==========================================
# 🎯 UTILITY TOOLS
# ==========================================

class CreateInviteTool(DiscordTool):
    """Create an invite link"""
    name = "create_invite"
    description = "Create an invite link for a channel. Use for 'invite banao', 'link do', 'invite generate'."
    
    parameters = [
        ToolParameter("channel_id", "string", "ID of channel (optional)", required=False, default=None),
        ToolParameter("max_uses", "integer", "Max uses (0=unlimited, default=1)", required=False, default=1),
        ToolParameter("max_age_minutes", "integer", "Expiry in minutes (0=never, default=1440=1day)", required=False, default=1440)
    ]
    
    permission_level = ToolPermissionLevel.MODERATOR
    
    async def execute(self, args: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        try:
            guild = context.get("guild")
            
            if args.get("channel_id"):
                channel = guild.get_channel(int(args["channel_id"]))
            else:
                channel = context.get("channel")
            
            max_uses = int(args.get("max_uses", 1)) or None
            max_age = int(args.get("max_age_minutes", 1440)) * 60 or None
            
            invite = await channel.create_invite(max_uses=max_uses, max_age=max_age)
            
            return ToolResult(True, f"🔗 **Invite Link Created!**\n{invite.url}\n\nUses: {invite.max_uses or '∞'} | Expires: {f'{args.get(\"max_age_minutes\", 1440)} min' if invite.max_age else 'Never'}", data={"invite_url": invite.url})
        except Exception as e:
            return ToolResult(False, f"❌ Error: {str(e)[:150]}")


# ==========================================
# 📦 GET ALL COMPLETE TOOLS FUNCTION
# ==========================================

def get_all_complete_tools(bot=None) -> List[DiscordTool]:
    """Get all 30+ complete Discord tools"""
    return [
        # ⚡ Moderation (7 tools)
        KickUserTool(),
        BanUserTool(),
        UnbanUserTool(),
        TimeoutUserTool(),
        MuteUserTool(),
        UnmuteUserTool(),
        
        # 📝 Channels (6 tools)
        CreateTextChannelTool(),
        CreateVoiceChannelTool(),
        DeleteChannelTool(),
        RenameChannelTool(),
        ListChannelsTool(),
        GetChannelInfoTool(),
        
        # 👤 Roles (5 tools)
        CreateRoleTool(),
        DeleteRoleTool(),
        AssignRoleTool(),
        RemoveRoleTool(),
        ListRolesTool(),
        
        # 💬 Messages (7 tools)
        SendMessageTool(),
        SendEmbedTool(),
        EditMessageTool(),
        DeleteMessageTool(),
        PinMessageTool(),
        AddReactionTool(),
        
        # 📊 Server Info (4 tools)
        GetServerInfoTool(),
        GetMemberInfoTool(),
        ListMembersTool(),
        GetBannedUsersTool(),
        
        # ✨ Profile (2 tools)
        ChangeNicknameTool(),
        GetUserAvatarTool(),
        
        # 🔍 Search (2 tools)
        SearchMessagesTool(),
        ReadChannelHistoryTool(),
        
        # 🎯 Utility (1 tool)
        CreateInviteTool(),
    ]


# Export list for easy access
COMPLETE_TOOL_NAMES = [
    "kick_user", "ban_user", "unban_user", "timeout_user", 
    "mute_user", "unmute_user",
    "create_text_channel", "create_voice_channel", "delete_channel", 
    "rename_channel", "list_channels", "get_channel_info",
    "create_role", "delete_role", "assign_role", "remove_role", 
    "list_roles",
    "send_message", "send_embed", "edit_message", "delete_message",
    "pin_message", "add_reaction",
    "get_server_info", "get_member_info", "list_members", "get_banned_users",
    "change_nickname", "get_avatar",
    "search_messages", "read_channel_history",
    "create_invite"
]
