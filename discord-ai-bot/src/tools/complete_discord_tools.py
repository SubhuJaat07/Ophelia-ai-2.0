"""
🔧 COMPLETE Discord Tools - FULL SERVER CONTROL!
================================================

ALL Discord operations for AI to use - 30+ Tools!
Based on Discord MCP repos (iprashantraj, pasympa, etc.)

Categories:
📝 Messages: search, read, send, edit, delete, pin, embed
👥 Members: info, kick, ban, unban, timeout, nickname, roles
🔧 Channels: create, delete, rename, info, list, permissions, slowmode, topic
🎭 Roles: create, delete, assign, remove, list
🔗 Other: invites, emojis, threads, reactions, server info

All tools inherit from DiscordTool base class.
"""

import discord
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from .base_tool import DiscordTool, ToolResult, ToolParameter, ToolPermissionLevel
import logging

logger = logging.getLogger("CompleteDiscordTools")


# ============================================================
# 📝 MESSAGE TOOLS
# ============================================================

class SearchMessagesTool(DiscordTool):
    """Search messages in server/channel"""
    
    name = "search_messages"
    description = """Search for messages in Discord server or channel by content, author, or date."""
    
    parameters = [
        ToolParameter(name="query", param_type="string", description="Text to search for", required=True),
        ToolParameter(name="channel_id", param_type="string", description="Specific channel ID", required=False, default=None),
        ToolParameter(name="author_id", param_type="string", description="Author user ID", required=False, default=None),
        ToolParameter(name="limit", param_type="integer", description="Max results (default: 10)", required=False, default=10),
    ]
    
    permission_level = ToolPermissionLevel.EVERYONE
    
    async def execute(self, args: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        try:
            query = args["query"].lower()
            channel_id = args.get("channel_id")
            author_id = args.get("author_id")
            limit = min(args.get("limit", 10), 50)
            
            guild = context.get("guild")
            if not guild:
                return ToolResult(success=False, content="❌ No guild available")
            
            since_date = datetime.utcnow() - timedelta(days=30)
            results = []
            
            channels_to_search = []
            if channel_id:
                ch = guild.get_channel(int(channel_id))
                channels_to_search = [ch] if ch and hasattr(ch, 'history') else []
            else:
                channels_to_search = [ch for ch in guild.text_channels if ch.permissions_for(guild.me).read_message_history]
            
            for channel in channels_to_search[:20]:
                try:
                    async for message in channel.history(limit=100, after=since_date):
                        if query and query not in message.content.lower():
                            continue
                        if author_id and str(message.author.id) != str(author_id):
                            continue
                        if message.author.bot:
                            continue
                        results.append({
                            "content": message.content[:300],
                            "author": f"{message.author.display_name}",
                            "channel": f"#{message.channel.name}",
                            "message_id": str(message.id),
                            "jump_url": message.jump_url
                        })
                        if len(results) >= limit:
                            break
                    if len(results) >= limit:
                        break
                except Exception as e:
                    logger.debug(f"Cannot search channel {channel}: {e}")
            
            if not results:
                return ToolResult(success=True, content=f"😔 No messages found matching '{query}'", data={"count": 0})
            
            lines = [f"🔍 **Found {len(results)} message(s):**\n"]
            for i, msg in enumerate(results[:10], 1):
                lines.append(f"{i}. **{msg['author']}** in {msg['channel']}: {msg['content'][:200]}")
            
            return ToolResult(success=True, content="\n".join(lines), data={"count": len(results), "results": results})
        except Exception as e:
            return ToolResult(success=False, content=f"❌ Search error: {str(e)[:150]}")


class ReadChannelTool(DiscordTool):
    """Read recent messages from a channel"""
    
    name = "read_channel_messages"
    description = """Read recent messages from a Discord channel for context."""
    
    parameters = [
        ToolParameter(name="channel_id", param_type="string", description="Channel ID to read", required=True),
        ToolParameter(name="limit", param_type="integer", description="Number of messages (default: 20)", required=False, default=20),
    ]
    
    permission_level = ToolPermissionLevel.EVERYONE
    
    async def execute(self, args: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        try:
            channel_id = args["channel_id"]
            limit = min(args.get("limit", 20), 100)
            
            guild = context.get("guild")
            if not guild:
                return ToolResult(success=False, content="❌ No guild available")
            
            channel = guild.get_channel(int(channel_id))
            if not channel or not hasattr(channel, 'history'):
                return ToolResult(success=False, content=f"❌ Channel not found or cannot read")
            
            if not channel.permissions_for(guild.me).read_message_history:
                return ToolResult(success=False, content="❌ No permission to read history")
            
            messages = []
            async for msg in channel.history(limit=limit):
                messages.append(msg)
            
            if not messages:
                return ToolResult(success=True, content=f"📭 No messages in #{channel.name}")
            
            messages.reverse()
            lines = [f"📖 **#{channel.name}** ({len(messages)} messages):\n"]
            for msg in messages[-30:]:
                is_bot = "🤖 " if msg.author.bot else ""
                lines.append(f"[{msg.created_at.strftime('%H:%M')}] {is_bot}**{msg.author.display_name}:** {msg.content[:250]}")
            
            return ToolResult(success=True, content="\n".join(lines), data={"count": len(messages)})
        except Exception as e:
            return ToolResult(success=False, content=f"❌ Error: {str(e)[:150]}")


class SendMessageTool(DiscordTool):
    """Send a message to any channel"""
    
    name = "send_message"
    description = """Send a message to a Discord channel."""
    
    parameters = [
        ToolParameter(name="channel_id", param_type="string", description="Channel ID to send to", required=True),
        ToolParameter(name="message", param_type="string", description="Message content", required=True),
        ToolParameter(name="reply_to_message_id", param_type="string", description="Reply to message ID", required=False, default=None),
    ]
    
    permission_level = ToolPermissionLevel.MODERATOR
    
    async def execute(self, args: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        try:
            channel_id = args["channel_id"]
            content = args["message"][:1900]
            reply_to_id = args.get("reply_to_message_id")
            
            guild = context.get("guild")
            if not guild:
                return ToolResult(success=False, content="❌ No guild available")
            
            channel = guild.get_channel(int(channel_id))
            if not channel:
                return ToolResult(success=False, content=f"❌ Channel {channel_id} not found")
            
            if not channel.permissions_for(guild.me).send_messages:
                return ToolResult(success=False, content="❌ No permission to send messages")
            
            kwargs = {}
            if reply_to_id:
                try:
                    reply_msg = await channel.fetch_message(int(reply_to_id))
                    kwargs["reference"] = reply_msg.to_reference()
                except:
                    pass
            
            sent_msg = await channel.send(content=content, **kwargs)
            return ToolResult(success=True, content=f"✅ Message sent to #{channel.name}! (ID: {sent_msg.id})", data={"message_id": str(sent_msg.id)})
        except discord.Forbidden:
            return ToolResult(success=False, content="❌ Forbidden: Missing permissions")
        except Exception as e:
            return ToolResult(success=False, content=f"❌ Error: {str(e)[:150]}")


class EditMessageTool(DiscordTool):
    """Edit an existing message sent by bot"""
    
    name = "edit_message"
    description = """Edit a message that was sent by the bot."""
    
    parameters = [
        ToolParameter(name="channel_id", param_type="string", description="Channel ID", required=True),
        ToolParameter(name="message_id", param_type="string", description="Message ID to edit", required=True),
        ToolParameter(name="new_content", param_type="string", description="New message content", required=True),
    ]
    
    permission_level = ToolPermissionLevel.MODERATOR
    
    async def execute(self, args: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        try:
            channel_id = args["channel_id"]
            message_id = args["message_id"]
            new_content = args["new_content"][:1900]
            
            guild = context.get("guild")
            if not guild:
                return ToolResult(success=False, content="❌ No guild available")
            
            channel = guild.get_channel(int(channel_id))
            if not channel:
                return ToolResult(success=False, content="❌ Channel not found")
            
            message = await channel.fetch_message(int(message_id))
            if message.author.id != guild.me.id:
                return ToolResult(success=False, content="❌ Can only edit my own messages!")
            
            await message.edit(content=new_content)
            return ToolResult(success=True, content=f"✅ Message edited successfully!", data={"message_id": message_id})
        except Exception as e:
            return ToolResult(success=False, content=f"❌ Edit failed: {str(e)[:150]}")


class DeleteMessageTool(DiscordTool):
    """Delete a message (bot's own or with manage_messages)"""
    
    name = "delete_message"
    description = """Delete a message. Can delete bot's own messages or any message with manage_messages permission."""
    
    parameters = [
        ToolParameter(name="channel_id", param_type="string", description="Channel ID", required=True),
        ToolParameter(name="message_id", param_type="string", description="Message ID to delete", required=True),
        ToolParameter(name="reason", param_type="string", description="Reason for deletion", required=False, default="Deleted by Ophelia"),
    ]
    
    permission_level = ToolPermissionLevel.MODERATOR
    
    async def execute(self, args: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        try:
            channel_id = args["channel_id"]
            message_id = args["message_id"]
            reason = args.get("reason", "Deleted by Ophelia")
            
            guild = context.get("guild")
            if not guild:
                return ToolResult(success=False, content="❌ No guild available")
            
            channel = guild.get_channel(int(channel_id))
            if not channel:
                return ToolResult(success=False, content="❌ Channel not found")
            
            message = await channel.fetch_message(int(message_id))
            await message(reason=reason)
            return ToolResult(success=True, content=f"✅ Message deleted!", data={"deleted_message_id": message_id})
        except discord.Forbidden:
            return ToolResult(success=False, content="❌ Cannot delete this message (permission/age)")
        except Exception as e:
            return ToolResult(success=False, content=f"❌ Delete failed: {str(e)[:150]}")


class PinMessageTool(DiscordTool):
    """Pin a message to the channel"""
    
    name = "pin_message"
    description = """Pin a message in a channel so it's easily accessible."""
    
    parameters = [
        ToolParameter(name="channel_id", param_type="string", description="Channel ID", required=True),
        ToolParameter(name="message_id", param_type="string", description="Message ID to pin", required=True),
    ]
    
    permission_level = ToolPermissionLevel.MODERATOR
    
    async def execute(self, args: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        try:
            channel_id = args["channel_id"]
            message_id = args["message_id"]
            
            guild = context.get("guild")
            if not guild:
                return ToolResult(success=False, content="❌ No guild available")
            
            channel = guild.get_channel(int(channel_id))
            if not channel:
                return ToolResult(success=False, content="❌ Channel not found")
            
            message = await channel.fetch_message(int(message_id))
            await message.pin()
            return ToolResult(success=True, content=f"📌 Message pinned successfully!")
        except Exception as e:
            return ToolResult(success=False, content=f"❌ Pin failed: {str(e)[:150]}")


class UnpinMessageTool(DiscordTool):
    """Unpin a pinned message"""
    
    name = "unpin_message"
    description = """Remove a pin from a pinned message."""
    
    parameters = [
        ToolParameter(name="channel_id", param_type="string", description="Channel ID", required=True),
        ToolParameter(name="message_id", param_type="string", description="Message ID to unpin", required=True),
    ]
    
    permission_level = ToolPermissionLevel.MODERATOR
    
    async def execute(self, args: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        try:
            channel_id = args["channel_id"]
            message_id = args["message_id"]
            
            guild = context.get("guild")
            if not guild:
                return ToolResult(success=False, content="❌ No guild available")
            
            channel = guild.get_channel(int(channel_id))
            if not channel:
                return ToolResult(success=False, content="❌ Channel not found")
            
            message = await channel.fetch_message(int(message_id))
            await message.unpin()
            return ToolResult(success=True, content=f"📍 Message unpinned successfully!")
        except Exception as e:
            return ToolResult(success=False, content=f"❌ Unpin failed: {str(e)[:150]}")


class SendEmbedTool(DiscordTool):
    """Send a rich embed message"""
    
    name = "send_embed"
    description = """Send a beautiful embedded message with title, description, colors, fields, images, etc."""
    
    parameters = [
        ToolParameter(name="channel_id", param_type="string", description="Channel ID to send to", required=True),
        ToolParameter(name="title", param_type="string", description="Embed title", required=True),
        ToolParameter(name="description", param_type="string", description="Embed description/body", required=False, default=None),
        ToolParameter(name="color", param_type="string", description="Color (hex like 'FF0000' or name like 'red', 'blue', 'green')", required=False, default="0x5865F2"),
        ToolParameter(name="fields", param_type="string", description="Fields as JSON array: [{\"name\":\"Field\",\"value\":\"Value\"}]", required=False, default="[]"),
        ToolParameter(name="footer", param_type="string", description="Footer text", required=False, default=None),
        ToolParameter(name="thumbnail_url", param_type="string", description="Thumbnail image URL", required=False, default=None),
        ToolParameter(name="image_url", param_type="string", description="Main image URL", required=False, default=None),
        ToolParameter(name="author_name", param_type="string", description="Author name", required=False, default=None),
    ]
    
    permission_level = ToolPermissionLevel.MODERATOR
    
    async def execute(self, args: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        try:
            import json
            
            channel_id = args["channel_id"]
            title = args["title"][:256]
            description = args.get("description")
            color_str = args.get("color", "0x5865F2")
            fields_json = args.get("fields", "[]")
            footer = args.get("footer")
            thumbnail_url = args.get("thumbnail_url")
            image_url = args.get("image_url")
            author_name = args.get("author_name")
            
            # Parse color
            color_map = {
                "red": 0xFF0000, "green": 0x00FF00, "blue": 0x0000FF,
                "yellow": 0xFFFF00, "purple": 0x9900FF, "orange": 0xFF8800,
                "white": 0xFFFFFF, "black": 0x000000
            }
            if color_str.lower() in color_map:
                color = color_map[color_str.lower()]
            elif color_str.startswith("0x"):
                color = int(color_str, 16)
            elif color_str.startswith("#"):
                color = int(color_str[1:], 16)
            else:
                color = 0x5865F2  # Discord blurple
            
            # Build embed
            embed = discord.Embed(
                title=title,
                description=description,
                color=color,
                timestamp=datetime.utcnow()
            )
            
            # Parse and add fields
            try:
                fields = json.loads(fields_json)
                for field in fields[:25]:  # Max 25 fields
                    inline = field.get("inline", False)
                    embed.add_field(name=field["name"][:256], value=field["value"][:1024], inline=inline)
            except json.JSONDecodeError:
                pass
            
            if footer:
                embed.set_footer(text=footer[:2048])
            if thumbnail_url:
                embed.set_thumbnail(url=thumbnail_url)
            if image_url:
                embed.set_image(url=image_url)
            if author_name:
                embed.set_author(name=author_name[:256])
            
            guild = context.get("guild")
            if not guild:
                return ToolResult(success=False, content="❌ No guild available")
            
            channel = guild.get_channel(int(channel_id))
            if not channel:
                return ToolResult(success=False, content="❌ Channel not found")
            
            msg = await channel(embed=embed)
            return ToolResult(success=True, content=f"✅ Embed sent to #{channel.name}!", data={"message_id": str(msg.id)})
        except Exception as e:
            return ToolResult(success=False, content=f"❌ Embed failed: {str(e)[:200]}")


# ============================================================
# 👥 MEMBER TOOLS
# ============================================================

class GetMemberTool(DiscordTool):
    """Get detailed info about a server member"""
    
    name = "get_member_info"
    description = """Get detailed information about a Discord member."""
    
    parameters = [
        ToolParameter(name="user_id", param_type="string", description="User's Discord ID", required=True),
    ]
    
    permission_level = ToolPermissionLevel.EVERYONE
    
    async def execute(self, args: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        try:
            user_id = args["user_id"]
            guild = context.get("guild")
            if not guild:
                return ToolResult(success=False, content="❌ No guild available")
            
            member = None
            try:
                member = await guild.fetch_member(int(user_id))
            except discord.NotFound:
                member = guild.get_member(int(user_id))
            
            if not member:
                return ToolResult(success=False, content=f"❌ User {user_id} not found")
            
            roles = [role.name for role in member.roles if role.name != "@everyone"]
            joined_at = member.joined_at.strftime("%Y-%m-%d") if member.joined_at else "Unknown"
            created_at = member.created_at.strftime("%Y-%m-%d") if member.created_at else "Unknown"
            
            status = {"online": "🟢 Online", "idle": "🌙 Idle", "dnd": "🔴 DND", "offline": "⚫ Offline"}.get(str(member.status), "⚫ Offline")
            
            info = f"""👤 **{member.display_name}**
• Username: `{member.name}`
• ID: `{member.id}`
• Bot: {'Yes' if member.bot else 'No'}
• Created: {created_at}
• Joined: {joined_at}
• Status: {status}
• Roles ({len(roles)}): {', '.join(roles[:10]) or 'None'}"""
            
            return ToolResult(success=True, content=info, data={"username": member.name, "roles": roles, "id": str(member.id)})
        except Exception as e:
            return ToolResult(success=False, content=f"❌ Error: {str(e)[:150]}")


class KickUserTool(DiscordTool):
    """Kick a user from the server"""
    
    name = "kick_user"
    description = """Kick a member from the server. They can rejoin with invite."""
    
    parameters = [
        ToolParameter(name="user_id", param_type="string", description="User ID to kick", required=True),
        ToolParameter(name="reason", param_type="string", description="Reason for kick", required=False, default="Kicked by Ophelia"),
    ]
    
    permission_level = ToolPermissionLevel.MODERATOR
    
    async def execute(self, args: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        try:
            user_id = args["user_id"]
            reason = args.get("reason", "Kicked by Ophelia")
            
            guild = context.get("guild")
            if not guild:
                return ToolResult(success=False, content="❌ No guild available")
            
            member = guild.get_member(int(user_id))
            if not member:
                return ToolResult(success=False, content=f"❌ User not found")
            
            if member.id == guild.owner_id:
                return ToolResult(success=False, content="❌ Owner ko kick nahi kar sakte! 😂")
            
            if member.top_role >= guild.me.top_role:
                return ToolResult(success=False, content="❌ User ki role meri se equal/higher hai!")
            
            await member.kick(reason=reason)
            return ToolResult(success=True, content=f"✅ **{member.display_name}** ko kick diya!\nReason: {reason}", data={"kicked_user": member.display_name})
        except discord.Forbidden:
            return ToolResult(success=False, content="❌ Permission denied!")
        except Exception as e:
            return ToolResult(success=False, content=f"❌ Kick failed: {str(e)[:150]}")


class BanUserTool(DiscordTool):
    """Ban a user from the server"""
    
    name = "ban_user"
    description = """Ban a member from the server. They CANNOT rejoin unless unbanned."""
    
    parameters = [
        ToolParameter(name="user_id", param_type="string", description="User ID to ban", required=True),
        ToolParameter(name="reason", param_type="string", description="Reason for ban", required=False, default="Banned by Ophelia"),
        ToolParameter(name="delete_message_days", param_type="integer", description="Delete messages from last X days (0-7)", required=False, default=0),
    ]
    
    permission_level = ToolPermissionLevel.MODERATOR
    
    async def execute(self, args: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        try:
            user_id = args["user_id"]
            reason = args.get("reason", "Banned by Ophelia")
            delete_days = min(max(args.get("delete_message_days", 0), 0), 7)
            
            guild = context.get("guild")
            if not guild:
                return ToolResult(success=False, content="❌ No guild available")
            
            member = guild.get_member(int(user_id))
            
            # Check if trying to ban owner
            if member and member.id == guild.owner_id:
                return ToolResult(success=False, content="❌ Owner ko ban nahi kar sakte! 😂")
            
            # Check role hierarchy
            if member and member.top_role >= guild.me.top_role:
                return ToolResult(success=False, content="❌ User ki role meri se equal/higher hai!")
            
            # Ban the user (works even if user not in server)
            user = member or discord.Object(id=int(user_id))
            await guild.ban(user, reason=reason, delete_message_days=delete_days)
            
            display_name = member.display_name if member else f"User({user_id})"
            return ToolResult(success=True, content=f"🚫 **{display_name}** ko BAN kar diya!\nReason: {reason}", data={"banned_user": display_name})
        except discord.Forbidden:
            return ToolResult(success=False, content="❌ Permission denied! Ban permission chahiye!")
        except Exception as e:
            return ToolResult(success=False, content=f"❌ Ban failed: {str(e)[:150]}")


class UnbanUserTool(DiscordTool):
    """Unban a banned user"""
    
    name = "unban_user"
    description = """Unban a previously banned user so they can rejoin."""
    
    parameters = [
        ToolParameter(name="user_id", param_type="string", description="User ID to unban", required=True),
        ToolParameter(name="reason", param_type="string", description="Reason for unban", required=False, default="Unbanned by Ophelia"),
    ]
    
    permission_level = ToolPermissionLevel.MODERATOR
    
    async def execute(self, args: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        try:
            user_id = args["user_id"]
            reason = args.get("reason", "Unbanned by Ophelia")
            
            guild = context.get("guild")
            if not guild:
                return ToolResult(success=False, content="❌ No guild available")
            
            user = discord.Object(id=int(user_id))
            await guild.unban(user, reason=reason)
            
            return ToolResult(success=True, content=f"✅ User `{user_id}` ko UNBAN kar diya! Ab wo join kar sakte hain.", data={"unbanned_user_id": user_id})
        except discord.NotFound:
            return ToolResult(success=False, content="❌ Ye user ban list me nahi hai!")
        except discord.Forbidden:
            return ToolResult(success=False, content="❌ Permission denied!")
        except Exception as e:
            return ToolResult(success=False, content=f"❌ Unban failed: {str(e)[:150]}")


class TimeoutUserTool(DiscordTool):
    """Timeout/mute a user"""
    
    name = "timeout_user"
    description = """Timeout a user for specified duration. They can't send messages until timeout ends."""
    
    parameters = [
        ToolParameter(name="user_id", param_type="string", description="User ID to timeout", required=True),
        ToolParameter(name="duration_minutes", param_type="integer", description="Duration in minutes (1-10080)", required=False, default=10),
        ToolParameter(name="reason", param_type="string", description="Reason for timeout", required=False, default="Timed out by Ophelia"),
    ]
    
    permission_level = ToolPermissionLevel.MODERATOR
    
    async def execute(self, args: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        try:
            user_id = args["user_id"]
            duration = min(max(args.get("duration_minutes", 10), 1), 10080)
            reason = args.get("reason", "Timed out by Ophelia")
            
            guild = context.get("guild")
            if not guild:
                return ToolResult(success=False, content="❌ No guild available")
            
            member = guild.get_member(int(user_id))
            if not member:
                return ToolResult(success=False, content="❌ User not found")
            
            if member.id == guild.owner_id:
                return ToolResult(success=False, content="❌ Owner ko timeout nahi kar sakte!")
            
            timeout_until = datetime.utcnow() + timedelta(minutes=duration)
            await member.timeout(timeout_until, reason=reason)
            
            duration_text = f"{duration} min" if duration < 60 else f"{duration//60} hours"
            return ToolResult(success=True, content=f"⏰ **{member.display_name}** ko {duration_text} ke liye timeout diya!", data={"duration_minutes": duration})
        except discord.Forbidden:
            return ToolResult(success=False, content="❌ Permission denied!")
        except Exception as e:
            return ToolResult(success=False, content=f"❌ Timeout failed: {str(e)[:150]}")


class RemoveTimeoutTool(DiscordTool):
    """Remove timeout from a user"""
    
    name = "remove_timeout"
    description = """Remove active timeout from a user immediately."""
    
    parameters = [
        ToolParameter(name="user_id", param_type="string", description="User ID to remove timeout from", required=True),
        ToolParameter(name="reason", param_type="string", description="Reason", required=False, default="Timeout removed by Ophelia"),
    ]
    
    permission_level = ToolPermissionLevel.MODERATOR
    
    async def execute(self, args: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        try:
            user_id = args["user_id"]
            reason = args.get("reason", "Timeout removed by Ophelia")
            
            guild = context.get("guild")
            if not guild:
                return ToolResult(success=False, content="❌ No guild available")
            
            member = guild.get_member(int(user_id))
            if not member:
                return ToolResult(success=False, content="❌ User not found")
            
            await member.timeout(None, reason=reason)  # None removes timeout
            return ToolResult(success=True, content=f"✅ **{member.display_name}** ka timeout hataya!")
        except Exception as e:
            return ToolResult(success=False, content=f"❌ Remove timeout failed: {str(e)[:150]}")


class GetBannedUsersTool(DiscordTool):
    """List all banned users"""
    
    name = "get_banned_users"
    description = """Get list of all banned users in the server."""
    
    parameters = []  # No params needed
    
    permission_level = ToolPermissionLevel.MODERATOR
    
    async def execute(self, args: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        try:
            guild = context.get("guild")
            if not guild:
                return ToolResult(success=False, content="❌ No guild available")
            
            bans = [entry async for entry in guild.bans()]
            
            if not bans:
                return ToolResult(success=True, content="📋 Koi banned users nahi hain!")
            
            lines = [f"🚫 **Banned Users ({len(bans)}):**\n"]
            for entry in bans[:25]:  # Show max 25
                user = entry.user
                reason = entry.reason or "No reason"
                lines.append(f"• **{user.name}** (`{user.id}`) - Reason: {reason}")
            
            return ToolResult(success=True, content="\n".join(lines), data={"count": len(bans)})
        except discord.Forbidden:
            return ToolResult(success=False, content="❌ No permission to view bans!")
        except Exception as e:
            return ToolResult(success=False, content=f"❌ Error: {str(e)[:150]}")


class EditNicknameTool(DiscordTool):
    """Change a member's nickname"""
    
    name = "edit_nickname"
    description = """Change a member's nickname in the server."""
    
    parameters = [
        ToolParameter(name="user_id", param_type="string", description="User ID", required=True),
        ToolParameter(name="nickname", param_type="string", description="New nickname (empty to reset)", required=True),
    ]
    
    permission_level = ToolPermissionLevel.MODERATOR
    
    async def execute(self, args: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        try:
            user_id = args["user_id"]
            nickname = args["nickname"][:32] if args.get("nickname") else None
            
            guild = context.get("guild")
            if not guild:
                return ToolResult(success=False, content="❌ No guild available")
            
            member = guild.get_member(int(user_id))
            if not member:
                return ToolResult(success=False, content="❌ User not found")
            
            await member(nick=nickname)
            nick_display = nickname or "(reset)"
            return ToolResult(success=True, content=f"✅ **{member.name}** ka nickname change ho gaya: **{nick_display}**")
        except discord.Forbidden:
            return ToolResult(success=False, content="❌ Cannot change this nickname!")
        except Exception as e:
            return ToolResult(success=False, content=f"❌ Nickname change failed: {str(e)[:150]}")


# ============================================================
# 🔧 CHANNEL TOOLS
# ============================================================

class CreateChannelTool(DiscordTool):
    """Create a new text or voice channel"""
    
    name = "create_channel"
    description = """Create a new text or voice channel in the server."""
    
    parameters = [
        ToolParameter(name="name", param_type="string", description="Channel name", required=True),
        ToolParameter(name="channel_type", param_type="string", description="Type: 'text' or 'voice'", required=False, default="text", enum=["text", "voice"]),
        ToolParameter(name="category_id", param_type="string", description="Category ID (optional)", required=False, default=None),
        ToolParameter(name="topic", param_type="string", description="Topic for text channels", required=False, default=None),
    ]
    
    permission_level = ToolPermissionLevel.MODERATOR
    
    async def execute(self, args: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        try:
            name = args["name"].strip().lower().replace(" ", "-")[:100]
            channel_type = args.get("channel_type", "text")
            category_id = args.get("category_id")
            topic = args.get("topic")
            
            guild = context.get("guild")
            if not guild:
                return ToolResult(success=False, content="❌ No guild available")
            
            if not guild.me.guild_permissions.manage_channels:
                return ToolResult(success=False, content="❌ Mere paas manage_channels permission nahi hai!")
            
            category = None
            if category_id:
                category = guild.get_channel(int(category_id))
            
            if channel_type == "voice":
                channel = await guild.create_voice_channel(name=name, category=category)
            else:
                channel = await guild.create_text_channel(name=name, topic=topic, category=category)
            
            return ToolResult(success=True, content=f"✅ Channel '{channel.name}' bana diya! 🆔 `{channel.id}`", data={"channel_id": str(channel.id), "mention": channel.mention})
        except discord.Forbidden:
            return ToolResult(success=False, content="❌ Permission denied!")
        except Exception as e:
            return ToolResult(success=False, content=f"❌ Create failed: {str(e)[:150]}")


class DeleteChannelTool(DiscordTool):
    """Delete a channel"""
    
    name = "delete_channel"
    description = """Permanently delete a channel. This action CANNOT be undone!"""
    
    parameters = [
        ToolParameter(name="channel_id", param_type="string", description="Channel ID to delete", required=True),
        ToolParameter(name="reason", param_type="string", description="Reason for deletion", required=False, default="Deleted by Ophelia"),
    ]
    
    permission_level = ToolPermissionLevel.OWNER  # Owner only - dangerous!
    
    async def execute(self, args: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        try:
            channel_id = args["channel_id"]
            reason = args.get("reason", "Deleted by Ophelia")
            
            guild = context.get("guild")
            if not guild:
                return ToolResult(success=False, content="❌ No guild available")
            
            channel = guild.get_channel(int(channel_id))
            if not channel:
                return ToolResult(success=False, content="❌ Channel not found")
            
            channel_name = channel.name
            await channel(reason=reason)
            return ToolResult(success=True, content=f"🗑️ Channel '{channel_name}' delete ho gaya!", data={"deleted_channel": channel_name})
        except discord.Forbidden:
            return ToolResult(success=False, content="❌ Permission denied! Admin chahiye iske liye!")
        except Exception as e:
            return ToolResult(success=False, content=f"❌ Delete failed: {str(e)[:150]}")


class RenameChannelTool(DiscordTool):
    """Rename a channel"""
    
    name = "rename_channel"
    description = """Rename an existing channel."""
    
    parameters = [
        ToolParameter(name="channel_id", param_type="string", description="Channel ID to rename", required=True),
        ToolParameter(name="new_name", param_type="string", description="New channel name", required=True),
    ]
    
    permission_level = ToolPermissionLevel.MODERATOR
    
    async def execute(self, args: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        try:
            channel_id = args["channel_id"]
            new_name = args["new_name"].strip().lower().replace(" ", "-")[:100]
            
            guild = context.get("guild")
            if not guild:
                return ToolResult(success=False, content="❌ No guild available")
            
            channel = guild.get_channel(int(channel_id))
            if not channel:
                return ToolResult(success=False, content="❌ Channel not found")
            
            old_name = channel.name
            await channel(name=new_name)
            return ToolResult(success=True, content=f"✅ Channel rename: '{old_name}' → '**{new_name}**'")
        except discord.Forbidden:
            return ToolResult(success=False, content="❌ Permission denied!")
        except Exception as e:
            return ToolResult(success=False, content=f"❌ Rename failed: {str(e)[:150]}")


class ListChannelsTool(DiscordTool):
    """List all channels in server"""
    
    name = "list_channels"
    description = """List all channels in the Discord server."""
    
    parameters = [
        ToolParameter(name="type_filter", param_type="string", description="Filter: 'text', 'voice', 'all'", required=False, default="all", enum=["text", "voice", "all"]),
    ]
    
    permission_level = ToolPermissionLevel.EVERYONE
    
    async def execute(self, args: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        try:
            type_filter = args.get("type_filter", "all")
            guild = context.get("guild")
            if not guild:
                return ToolResult(success=False, content="❌ No guild available")
            
            lines = [f"📁 **Channels in {guild.name}:**\n"]
            count = 0
            
            for channel in guild.channels:
                if type_filter == "text" and not isinstance(channel, discord.TextChannel):
                    continue
                if type_filter == "voice" and not isinstance(channel, discord.VoiceChannel):
                    continue
                
                icon = "💬" if isinstance(channel, discord.TextChannel) else "🔊"
                cat = f" ({channel.category.name})" if channel.category else ""
                lines.append(f"  {icon} {channel.name}{cat} (`{channel.id}`)")
                count += 1
            
            lines.append(f"\n**Total: {count} channels**")
            return ToolResult(success=True, content="\n".join(lines), data={"count": count})
        except Exception as e:
            return ToolResult(success=False, content=f"❌ Error: {str(e)[:150]}")


class GetChannelInfoTool(DiscordTool):
    """Get detailed info about a specific channel"""
    
    name = "get_channel_info"
    description = """Get detailed information about a specific channel."""
    
    parameters = [
        ToolParameter(name="channel_id", param_type="string", description="Channel ID to inspect", required=True),
    ]
    
    permission_level = ToolPermissionLevel.EVERYONE
    
    async def execute(self, args: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        try:
            channel_id = args["channel_id"]
            guild = context.get("guild")
            if not guild:
                return ToolResult(success=False, content="❌ No guild available")
            
            channel = guild.get_channel(int(channel_id))
            if not channel:
                return ToolResult(success=False, content=f"❌ Channel {channel_id} not found")
            
            ch_type = {
                discord.ChannelType.text: "💬 Text",
                discord.ChannelType.voice: "🔊 Voice",
                discord.ChannelType.category: "📁 Category",
                discord.ChannelType.forum: "📋 Forum",
            }.get(channel.type, str(channel.type))
            
            info = f"📺 **{channel.name}**\nType: {ch_type}\nID: `{channel.id}`"
            
            if isinstance(channel, discord.TextChannel):
                info += f"\nTopic: {channel.topic or 'None'}\nNSFW: {'Yes' if channel.nsfw else 'No'}\nSlowmode: {channel.slowmode_delay}s"
            elif isinstance(channel, discord.VoiceChannel):
                info += f"\nBitrate: {channel.bitrate//1000}kbps\nLimit: {channel.user_limit or '∞'}\nUsers: {len(channel.members)}"
            
            return ToolResult(success=True, content=info, data={"name": channel.name, "id": str(channel.id)})
        except Exception as e:
            return ToolResult(success=False, content=f"❌ Error: {str(e)[:150]}")


class SetSlowmodeTool(DiscordTool):
    """Set slowmode on a channel"""
    
    name = "set_slowmode"
    description = """Set slowmode delay on a text channel (users must wait between messages)."""
    
    parameters = [
        ToolParameter(name="channel_id", param_type="string", description="Channel ID", required=True),
        ToolParameter(name="seconds", param_type="integer", description="Slowmode in seconds (0=off, max=21600)", required=True),
    ]
    
    permission_level = ToolPermissionLevel.MODERATOR
    
    async def execute(self, args: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        try:
            channel_id = args["channel_id"]
            seconds = min(max(args.get("seconds", 0), 0), 21600)
            
            guild = context.get("guild")
            if not guild:
                return ToolResult(success=False, content="❌ No guild available")
            
            channel = guild.get_channel(int(channel_id))
            if not channel or not isinstance(channel, discord.TextChannel):
                return ToolResult(success=False, content="❌ Text channel not found")
            
            await channel(slowmode_delay=seconds)
            display = "off" if seconds == 0 else f"{seconds}s"
            return ToolResult(success=True, content=f"⏱️ Slowmode set to **{display}** on #{channel.name}")
        except Exception as e:
            return ToolResult(success=False, content=f"❌ Failed: {str(e)[:150]}")


class SetTopicTool(DiscordTool):
    """Set topic on a text channel"""
    
    name = "set_topic"
    description = """Set or update the topic/description of a text channel."""
    
    parameters = [
        ToolParameter(name="channel_id", param_type="string", description="Channel ID", required=True),
        ToolParameter(name="topic", param_type="string", description="New topic (empty to clear)", required=True),
    ]
    
    permission_level = ToolPermissionLevel.MODERATOR
    
    async def execute(self, args: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        try:
            channel_id = args["channel_id"]
            topic = args.get("topic", "")[:1024] or None
            
            guild = context.get("guild")
            if not guild:
                return ToolResult(success=False, content="❌ No guild available")
            
            channel = guild.get_channel(int(channel_id))
            if not channel or not isinstance(channel, discord.TextChannel):
                return ToolResult(success=False, content="❌ Text channel not found")
            
            await channel(topic=topic)
            return ToolResult(success=True, content=f"📝 Topic updated on #{channel.name}!")
        except Exception as e:
            return ToolResult(success=False, content=f"❌ Failed: {str(e)[:150]}")


# ============================================================
# 🎭 ROLE TOOLS
# ============================================================

class CreateRoleTool(DiscordTool):
    """Create a new role"""
    
    name = "create_role"
    description = """Create a new role in the server with optional color and permissions."""
    
    parameters = [
        ToolParameter(name="name", param_type="string", description="Role name", required=True),
        ToolParameter(name="color", param_type="string", description="Color hex (e.g., 'FF5500') or name", required=False, default="0x99AAB5"),
        ToolParameter(name="hoist", param_type="boolean", description="Show separately in member list", required=False, default=False),
        ToolParameter(name="mentionable", param_type="boolean", description="Allow anyone to @mention", required=False, default=False),
        ToolParameter(name="permissions", param_type="string", description="Comma-separated permissions (e.g., 'manage_messages,kick_members')", required=False, default=""),
    ]
    
    permission_level = ToolPermissionLevel.MODERATOR
    
    async def execute(self, args: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        try:
            name = args["name"][:100]
            color_str = args.get("color", "0x99AAB5")
            hoist = args.get("hoist", False)
            mentionable = args.get("mentionable", False)
            perms_str = args.get("permissions", "")
            
            # Parse color
            color_map = {"red": 0xFF0000, "green": 0x00FF00, "blue": 0x0000FF, "yellow": 0xFFFF00, "purple": 0x9900FF}
            if color_str.lower() in color_map:
                color = color_map[color_str.lower()]
            elif color_str.startswith("0x"):
                color = int(color_str, 16)
            elif color_str.startswith("#"):
                color = int(color_str[1:], 16)
            else:
                color = 0x99AAB5
            
            # Parse permissions
            permissions = discord.Permissions.none()
            if perms_str:
                perm_list = [p.strip() for p in perms_str.split(",")]
                for perm in perm_list:
                    if hasattr(permissions, perm):
                        setattr(permissions, perm, True)
            
            guild = context.get("guild")
            if not guild:
                return ToolResult(success=False, content="❌ No guild available")
            
            role = await guild.create_role(
                name=name,
                color=color,
                hoist=hoist,
                mentionable=mentionable,
                permissions=permissions
            )
            
            return ToolResult(success=True, content=f"✅ Role '{role.name}' bana diya! 🆔 `{role.id}` - {role.mention}", data={"role_id": str(role.id), "mention": role.mention})
        except discord.Forbidden:
            return ToolResult(success=False, content="❌ Permission denied! Manage Roles chahiye!")
        except Exception as e:
            return ToolResult(success=False, content=f"❌ Create role failed: {str(e)[:150]}")


class DeleteRoleTool(DiscordTool):
    """Delete a role"""
    
    name = "delete_role"
    description = """Permanently delete a role. This CANNOT be undone!"""
    
    parameters = [
        ToolParameter(name="role_id", param_type="string", description="Role ID to delete", required=True),
        ToolParameter(name="reason", param_type="string", description="Reason for deletion", required=False, default="Deleted by Ophelia"),
    ]
    
    permission_level = ToolPermissionLevel.OWNER  # Owner only - dangerous!
    
    async def execute(self, args: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        try:
            role_id = args["role_id"]
            reason = args.get("reason", "Deleted by Ophelia")
            
            guild = context.get("guild")
            if not guild:
                return ToolResult(success=False, content="❌ No guild available")
            
            role = guild.get_role(int(role_id))
            if not role:
                return ToolResult(success=False, content="❌ Role not found")
            
            if role.is_default():
                return ToolResult(success=False, content="❌ @everyone role delete nahi kar sakte!")
            
            role_name = role.name
            await role(reason=reason)
            return ToolResult(success=True, content=f"🗑️ Role '{role_name}' delete ho gaya!")
        except discord.Forbidden:
            return ToolResult(success=False, content="❌ Permission denied! Admin chahiye!")
        except Exception as e:
            return ToolResult(success=False, content=f"❌ Delete failed: {str(e)[:150]}")


class AssignRoleTool(DiscordTool):
    """Assign a role to a member"""
    
    name = "assign_role"
    description = """Give/add a role to a member."""
    
    parameters = [
        ToolParameter(name="user_id", param_type="string", description="User ID", required=True),
        ToolParameter(name="role_id", param_type="string", description="Role ID to assign", required=True),
        ToolParameter(name="reason", param_type="string", description="Reason", required=False, default="Role assigned by Ophelia"),
    ]
    
    permission_level = ToolPermissionLevel.MODERATOR
    
    async def execute(self, args: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        try:
            user_id = args["user_id"]
            role_id = args["role_id"]
            reason = args.get("reason", "Role assigned by Ophelia")
            
            guild = context.get("guild")
            if not guild:
                return ToolResult(success=False, content="❌ No guild available")
            
            member = guild.get_member(int(user_id))
            role = guild.get_role(int(role_id))
            
            if not member:
                return ToolResult(success=False, content="❌ User not found")
            if not role:
                return ToolResult(success=False, content="❌ Role not found")
            
            if role >= guild.me.top_role:
                return ToolResult(success=False, content="❌ Ye role meri se higher hai, assign nahi kar sakti!")
            
            await member.add_roles(role, reason=reason)
            return ToolResult(success=True, content=f"✅ **{member.display_name}** ko role **{role.name}** mil gaya!")
        except discord.Forbidden:
            return ToolResult(success=False, content="❌ Permission denied!")
        except Exception as e:
            return ToolResult(success=False, content=f"❌ Assign failed: {str(e)[:150]}")


class RemoveRoleTool(DiscordTool):
    """Remove a role from a member"""
    
    name = "remove_role"
    description = """Remove a role from a member."""
    
    parameters = [
        ToolParameter(name="user_id", param_type="string", description="User ID", required=True),
        ToolParameter(name="role_id", param_type="string", description="Role ID to remove", required=True),
        ToolParameter(name="reason", param_type="string", description="Reason", required=False, default="Role removed by Ophelia"),
    ]
    
    permission_level = ToolPermissionLevel.MODERATOR
    
    async def execute(self, args: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        try:
            user_id = args["user_id"]
            role_id = args["role_id"]
            reason = args.get("reason", "Role removed by Ophelia")
            
            guild = context.get("guild")
            if not guild:
                return ToolResult(success=False, content="❌ No guild available")
            
            member = guild.get_member(int(user_id))
            role = guild.get_role(int(role_id))
            
            if not member:
                return ToolResult(success=False, content="❌ User not found")
            if not role:
                return ToolResult(success=False, content="❌ Role not found")
            
            if role >= guild.me.top_role:
                return ToolResult(success=False, content="❌ Ye role meri se higher hai, remove nahi kar sakti!")
            
            await member.remove_roles(role, reason=reason)
            return ToolResult(success=True, content=f"✅ **{member.display_name}** se role **{role.name}** hataya!")
        except discord.Forbidden:
            return ToolResult(success=False, content="❌ Permission denied!")
        except Exception as e:
            return ToolResult(success=False, content=f"❌ Remove failed: {str(e)[:150]}")


class ListRolesTool(DiscordTool):
    """List all roles in the server"""
    
    name = "list_roles"
    description = """List all roles in the server with their IDs and member counts."""
    
    parameters = []  # No params needed
    
    permission_level = ToolPermissionLevel.EVERYONE
    
    async def execute(self, args: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        try:
            guild = context.get("guild")
            if not guild:
                return ToolResult(success=False, content="❌ No guild available")
            
            lines = [f"🎭 **Roles in {guild.name}** ({len(guild.roles)} total):\n"]
            
            # Sort by position (highest first)
            sorted_roles = sorted(guild.roles, key=lambda r: r.position, reverse=True)
            
            for role in sorted_roles:
                member_count = len(role.members)
                color_hex = f"#{role.color.value:06X}" if role.color.value else "default"
                mention = "@" if role.mentionable else ""
                hoist = "📌 " if role.hoist else ""
                lines.append(f"  {hoist}{mention}**{role.name}** (`{role.id}`) - {color_hex} - {member_count} members")
            
            return ToolResult(success=True, content="\n".join(lines), data={"count": len(guild.roles)})
        except Exception as e:
            return ToolResult(success=False, content=f"❌ Error: {str(e)[:150]}")


# ============================================================
# 🔗 OTHER TOOLS
# ============================================================

class GetServerInfoTool(DiscordTool):
    """Get comprehensive server information"""
    
    name = "get_server_info"
    description = """Get detailed information about the Discord server."""
    
    parameters = []
    
    permission_level = ToolPermissionLevel.EVERYONE
    
    async def execute(self, args: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        try:
            guild = context.get("guild")
            if not guild:
                return ToolResult(success=False, content="❌ No guild available")
            
            online = sum(1 for m in guild.members if m.status == discord.Status.online)
            bots = sum(1 for m in guild.members if m.bot)
            humans = guild.member_count - bots
            
            info = f"""🏠 **{guild.name}**
🆔 `{guild.id}`
👑 Owner: {guild.owner.display_name if guild.owner else '?'} (`{guild.owner_id}`)

📊 **Stats:**
• Members: {guild.member_count} ({humans} 👥 + {bots} 🤖)
• Online: ~{online}
• Channels: {len(guild.text_channels)} 💬 + {len(guild.voice_channels)} 🔊
• Roles: {len(guild.roles)}
• Emojis: {len(guild.emojis)}

📅 Created: {guild.created_at.strftime('%Y-%m-%d')}
✅ Verification: {str(guild.verification_level)}"""
            
            return ToolResult(success=True, content=info, data={"name": guild.name, "id": str(guild.id), "members": guild.member_count})
        except Exception as e:
            return ToolResult(success=False, content=f"❌ Error: {str(e)[:150]}")


class AddReactionTool(DiscordTool):
    """Add emoji reaction to a message"""
    
    name = "add_reaction"
    description = """Add an emoji reaction to a message."""
    
    parameters = [
        ToolParameter(name="channel_id", param_type="string", description="Channel ID", required=True),
        ToolParameter(name="message_id", param_type="string", description="Message ID", required=True),
        ToolParameter(name="emoji", param_type="string", description="Emoji (e.g., 👍, 🔥, ❤️)", required=True),
    ]
    
    permission_level = ToolPermissionLevel.EVERYONE
    
    async def execute(self, args: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        try:
            channel_id = args["channel_id"]
            message_id = args["message_id"]
            emoji = args["emoji"]
            
            guild = context.get("guild")
            if not guild:
                return ToolResult(success=False, content="❌ No guild available")
            
            channel = guild.get_channel(int(channel_id))
            if not channel:
                return ToolResult(success=False, content="❌ Channel not found")
            
            message = await channel.fetch_message(int(message_id))
            await message.add_reaction(emoji)
            return ToolResult(success=True, content=f"✅ Added reaction {emoji}!")
        except discord.HTTPException as e:
            if "unknown_emoji" in str(e).lower():
                return ToolResult(success=False, content=f"❌ Unknown emoji: {emoji}")
            return ToolResult(success=False, content=f"❌ Could not react: {str(e)[:100]}")
        except Exception as e:
            return ToolResult(success=False, content=f"❌ Error: {str(e)[:150]}")


class CreateInviteTool(DiscordTool):
    """Create an invite link for a channel"""
    
    name = "create_invite"
    description = """Create an invite link for a channel."""
    
    parameters = [
        ToolParameter(name="channel_id", param_type="string", description="Channel ID", required=True),
        ToolParameter(name="max_uses", param_type="integer", description="Max uses (0=unlimited)", required=False, default=0),
        ToolParameter(name="max_age_minutes", param_type="integer", description="Expiry in minutes (0=never)", required=False, default=1440),
    ]
    
    permission_level = ToolPermissionLevel.MODERATOR
    
    async def execute(self, args: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        try:
            channel_id = args["channel_id"]
            max_uses = args.get("max_uses", 0) or 0
            max_age = (args.get("max_age_minutes", 1440) or 0) * 60  # Convert to seconds
            
            guild = context.get("guild")
            if not guild:
                return ToolResult(success=False, content="❌ No guild available")
            
            channel = guild.get_channel(int(channel_id))
            if not channel:
                return ToolResult(success=False, content="❌ Channel not found")
            
            invite = await channel.create_invite(max_uses=max_uses, max_age=max_age)
            return ToolResult(success=True, content=f"🔗 **Invite Link:** {invite.url}\nUses: {invite.uses}/{invite.max_uses}", data={"invite_url": invite.url})
        except discord.Forbidden:
            return ToolResult(success=False, content="❌ No permission to create invites!")
        except Exception as e:
            return ToolResult(success=False, content=f"❌ Invite failed: {str(e)[:150]}")


class CreateThreadTool(DiscordTool):
    """Create a thread in a channel"""
    
    name = "create_thread"
    description = """Create a new thread in a text channel."""
    
    parameters = [
        ToolParameter(name="channel_id", param_type="string", description="Parent channel ID", required=True),
        ToolParameter(name="name", param_type="string", description="Thread name", required=True),
        ToolParameter(name="message_id", param_type="string", description="Optional: Create from message", required=False, default=None),
    ]
    
    permission_level = ToolPermissionLevel.MODERATOR
    
    async def execute(self, args: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        try:
            channel_id = args["channel_id"]
            name = args["name"][:100]
            message_id = args.get("message_id")
            
            guild = context.get("guild")
            if not guild:
                return ToolResult(success=False, content="❌ No guild available")
            
            channel = guild.get_channel(int(channel_id))
            if not channel or not isinstance(channel, discord.TextChannel):
                return ToolResult(success=False, content="❌ Text channel not found")
            
            if message_id:
                message = await channel.fetch_message(int(message_id))
                thread = await message.create_thread(name=name)
            else:
                thread = await channel.create_thread(name=name, type=discord.ChannelType.public_thread)
            
            return ToolResult(success=True, content=f"🧵 Thread '{thread.name}' bana diya! 🆔 `{thread.id}`", data={"thread_id": str(thread.id)})
        except discord.Forbidden:
            return ToolResult(success=False, content="❌ Permission denied!")
        except Exception as e:
            return ToolResult(success=False, content=f"❌ Thread failed: {str(e)[:150]}")


class ListMembersTool(DiscordTool):
    """List members in the server"""
    
    name = "list_members"
    description = """List members in the server with filtering options."""
    
    parameters = [
        ToolParameter(name="limit", param_type="integer", description="Max members to show (default: 20)", required=False, default=20),
        ToolParameter(name="status_filter", param_type="string", description="Filter: 'online', 'idle', 'dnd', 'offline', 'all'", required=False, default="all"),
        ToolParameter(name="include_bots", param_type="boolean", description="Include bots in list", required=False, default=False),
    ]
    
    permission_level = ToolPermissionLevel.EVERYONE
    
    async def execute(self, args: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        try:
            limit = min(args.get("limit", 20), 50)
            status_filter = args.get("status_filter", "all")
            include_bots = args.get("include_bots", False)
            
            guild = context.get("guild")
            if not guild:
                return ToolResult(success=False, content="❌ No guild available")
            
            members = []
            for member in guild.members:
                if not include_bots and member.bot:
                    continue
                if status_filter != "all" and str(member.status) != status_filter:
                    continue
                members.append(member)
                if len(members) >= limit:
                    break
            
            lines = [f"👥 **Members** ({len(members)} shown):\n"]
            status_icons = {"online": "🟢", "idle": "🌙", "dnd": "🔴", "offline": "⚫"}
            
            for m in members:
                icon = status_icons.get(str(m.status), "⚫")
                bot_tag = " 🤖" if m.bot else ""
                roles = len(m.roles) - 1  # Exclude @everyone
                lines.append(f"  {icon} **{m.display_name}**`{m.id}`{bot_tag} - {roles} roles")
            
            return ToolResult(success=True, content="\n".join(lines), data={"count": len(members)})
        except Exception as e:
            return ToolResult(success=False, content=f"❌ Error: {str(e)[:150]}")


# ============================================================
# 📋 COMPLETE TOOL REGISTRY
# ============================================================

ALL_COMPLETE_DISCORD_TOOLS = [
    # 📝 Message Tools (9)
    SearchMessagesTool,
    ReadChannelTool,
    SendMessageTool,
    EditMessageTool,
    DeleteMessageTool,
    PinMessageTool,
    UnpinMessageTool,
    SendEmbedTool,
    AddReactionTool,
    
    # 👥 Member Tools (10)
    GetMemberTool,
    KickUserTool,
    BanUserTool,
    UnbanUserTool,
    TimeoutUserTool,
    RemoveTimeoutTool,
    GetBannedUsersTool,
    EditNicknameTool,
    ListMembersTool,
    
    # 🔧 Channel Tools (8)
    CreateChannelTool,
    DeleteChannelTool,
    RenameChannelTool,
    ListChannelsTool,
    GetChannelInfoTool,
    SetSlowmodeTool,
    SetTopicTool,
    CreateThreadTool,
    
    # 🎭 Role Tools (5)
    CreateRoleTool,
    DeleteRoleTool,
    AssignRoleTool,
    RemoveRoleTool,
    ListRolesTool,
    
    # 🔗 Other Tools (3)
    GetServerInfoTool,
    CreateInviteTool,
]

TOTAL_TOOLS_COUNT = len(ALL_COMPLETE_DISCORD_TOOLS)


def get_all_complete_tools(bot=None) -> List[DiscordTool]:
    """Instantiate all complete tools"""
    return [tool_cls(bot=bot) for tool_cls in ALL_COMPLETE_DISCORD_TOOLS]


def print_tool_summary():
    """Print summary of all available tools"""
    print("\n" + "="*70)
    print(f"🔧 COMPLETE DISCORD TOOLS - {TOTAL_TOOLS_COUNT} TOOLS AVAILABLE!")
    print("="*70)
    
    categories = {
        "📝 Messages": ["search_messages", "read_channel_messages", "send_message", "edit_message", 
                       "delete_message", "pin_message", "unpin_message", "send_embed", "add_reaction"],
        "👥 Members": ["get_member_info", "kick_user", "ban_user", "unban_user", "timeout_user",
                      "remove_timeout", "get_banned_users", "edit_nickname", "list_members"],
        "🔧 Channels": ["create_channel", "delete_channel", "rename_channel", "list_channels",
                       "get_channel_info", "set_slowmode", "set_topic", "create_thread"],
        "🎭 Roles": ["create_role", "delete_role", "assign_role", "remove_role", "list_roles"],
        "🔗 Other": ["get_server_info", "create_invite"],
    }
    
    for cat, tools in categories.items():
        print(f"\n{cat} ({len(tools)} tools):")
        for tool in tools:
            print(f"  • {tool}")
    
    print("\n" + "="*70)
    print("✅ All tools perform REAL Discord API actions!")
    print("="*70 + "\n")


if __name__ == "__main__":
    print_tool_summary()
