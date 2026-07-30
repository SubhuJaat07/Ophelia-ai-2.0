"""
🔧 Discord Tools - Actual Discord Operations for AI to Use!
========================================================

Each tool represents a Discord capability that Ophelia can invoke:
- Search messages across server
- Read channel history
- Send messages/replies
- Add reactions
- Get member info
- Server info & channel listing

All tools inherit from DiscordTool base class.
"""

import discord
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from .base_tool import DiscordTool, ToolResult, ToolParameter, ToolPermissionLevel
import logging

logger = logging.getLogger("DiscordTools")


# ============================================================
# 🔍 SEARCH MESSAGES TOOL
# ============================================================
class SearchMessagesTool(DiscordTool):
    """
    Search messages in server/channel - POWERFUL context finder!
    
    Lets AI find old conversations, specific topics, user messages.
    """
    
    name = "search_messages"
    description = """Search for messages in Discord server or channel. 
Can find messages by content, author, date range, or keywords.
Perfect for finding past discussions, context, or specific information.
Supports filtering by: content (text search), author_id, channel_id, 
limit (max results), and days_ago (how far back to search)."""
    
    parameters = [
        ToolParameter(
            name="query",
            param_type="string",
            description="Text/keywords to search for in messages",
            required=True
        ),
        ToolParameter(
            name="channel_id",
            param_type="string", 
            description="Specific channel ID to search (optional, searches all if omitted)",
            required=False,
            default=None
        ),
        ToolParameter(
            name="author_id",
            param_type="string",
            description="Only search messages from this user ID",
            required=False,
            default=None
        ),
        ToolParameter(
            name="limit",
            param_type="integer",
            description="Maximum number of results (default: 10, max: 50)",
            required=False,
            default=10
        ),
        ToolParameter(
            name="days_ago",
            param_type="integer",
            description="How many days back to search (default: 30, max: 365)",
            required=False,
            default=30
        )
    ]
    
    permission_level = ToolPermissionLevel.EVERYONE
    
    async def execute(self, args: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        try:
            query = args["query"].lower()
            channel_id = args.get("channel_id")
            author_id = args.get("author_id")
            limit = min(args.get("limit", 10), 50)
            days_ago = min(args.get("days_ago", 30), 365)
            
            guild = context.get("guild")
            if not guild:
                return ToolResult(success=False, content="❌ No guild/server available in context")
            
            # Calculate date threshold
            since_date = datetime.utcnow() - timedelta(days=days_ago)
            results = []
            
            # Determine channels to search
            if channel_id:
                channel = guild.get_channel(int(channel_id))
                if not channel:
                    return ToolResult(success=False, content=f"❌ Channel {channel_id} not found")
                channels_to_search = [channel] if hasattr(channel, 'history') else []
            else:
                # Search all text channels bot can see
                channels_to_search = [
                    ch for ch in guild.text_channels 
                    if ch.permissions_for(guild.me).read_message_history
                ]
            
            # Search through channels
            for channel in channels_to_search[:20]:  # Limit channels to search
                try:
                    async for message in channel.history(limit=100, after=since_date):
                        # Apply filters
                        if query and query not in message.content.lower():
                            continue
                        if author_id and str(message.author.id) != str(author_id):
                            continue
                        if message.author.bot:  # Skip bot messages
                            continue
                            
                        results.append({
                            "content": message.content[:300],
                            "author": f"{message.author.display_name}",
                            "author_id": str(message.author.id),
                            "channel": f"#{message.channel.name}",
                            "channel_id": str(message.channel.id),
                            "message_id": str(message.id),
                            "created_at": message.created_at.isoformat(),
                            "jump_url": message.jump_url
                        })
                        
                        if len(results) >= limit:
                            break
                    
                    if len(results) >= limit:
                        break
                        
                except Exception as e:
                    logger.debug(f"Cannot search channel {channel}: {e}")
                    continue
            
            if not results:
                return ToolResult(
                    success=True,
                    content=f"😔 No messages found matching '{query}' in the last {days_ago} days.",
                    data={"count": 0, "results": []}
                )
            
            # Format results for AI
            result_lines = [f"🔍 **Found {len(results)} message(s) about '{query}':**\n"]
            for i, msg in enumerate(results[:10], 1):  # Show max 10 in summary
                result_lines.append(
                    f"{i}. **{msg['author']}** in {msg['channel']} ({msg['created_at'][:10]}):\n"
                    f"   > {msg['content'][:200]}\n"
                )
            
            return ToolResult(
                success=True,
                content="\n".join(result_lines),
                data={"count": len(results), "results": results}
            )
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return ToolResult(success=False, content=f"❌ Search error: {str(e)[:150]}")


# ============================================================
# 📖 READ CHANNEL TOOL  
# ============================================================
class ReadChannelTool(DiscordTool):
    """
    Read recent messages from a channel - Context gathering!
    
    AI can use this to understand what's happening in any channel.
    """
    
    name = "read_channel_messages"
    description = """Read recent messages from a Discord channel.
Useful for understanding current discussions, getting context, or catching up on conversations.
Returns messages with author, timestamp, and content."""
    
    parameters = [
        ToolParameter(
            name="channel_id",
            param_type="string",
            description="ID of the channel to read from",
            required=True
        ),
        ToolParameter(
            name="limit",
            param_type="integer",
            description="Number of messages to fetch (default: 20, max: 100)",
            required=False,
            default=20
        ),
        ToolParameter(
            name="before_message_id",
            param_type="string",
            description="Get messages before this message ID (for pagination)",
            required=False,
            default=None
        )
    ]
    
    permission_level = ToolPermissionLevel.EVERYONE
    
    async def execute(self, args: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        try:
            channel_id = args["channel_id"]
            limit = min(args.get("limit", 20), 100)
            before_id = args.get("before_message_id")
            
            guild = context.get("guild")
            if not guild:
                return ToolResult(success=False, content="❌ No guild available")
            
            channel = guild.get_channel(int(channel_id))
            if not channel:
                return ToolResult(success=False, content=f"❌ Channel {channel_id} not found or not accessible")
            
            if not hasattr(channel, 'history'):
                return ToolResult(success=False, content=f"❌ Cannot read from this channel type")
            
            # Check permissions
            if not channel.permissions_for(guild.me).read_message_history:
                return ToolResult(success=False, content="❌ No permission to read this channel's history")
            
            # Fetch messages
            kwargs = {"limit": limit}
            if before_id:
                kwargs["before"] = discord.Object(id=int(before_id))
            
            messages = []
            async for msg in channel.history(**kwargs):
                messages.append(msg)
            
            if not messages:
                return ToolResult(success=True, content=f"📭 No messages found in #{channel.name}", data=[])
            
            messages.reverse()  # Chronological order
            
            # Format for AI
            lines = [f"📖 **Recent messages from #{channel.name}** ({len(messages)} messages):\n"]
            for msg in messages[-30:]:  # Max 30 in output
                is_bot = "🤖 " if msg.author.bot else ""
                lines.append(
                    f"[{msg.created_at.strftime('%H:%M')}] {is_bot}**{msg.author.display_name}:** {msg.content[:250]}"
                )
            
            return ToolResult(
                success=True,
                content="\n".join(lines),
                data={
                    "count": len(messages),
                    "channel_name": channel.name,
                    "messages": [{
                        "author": m.author.display_name,
                        "content": m.content,
                        "timestamp": m.created_at.isoformat()
                    } for m in messages]
                }
            )
            
        except Exception as e:
            logger.error(f"Read channel failed: {e}")
            return ToolResult(success=False, content=f"❌ Error reading channel: {str(e)[:150]}")


# ============================================================
# 💬 SEND MESSAGE TOOL
# ============================================================
class SendMessageTool(DiscordTool):
    """
    Send a message to any channel - Proactive messaging!
    
    AI can use this to send announcements, replies, etc.
    """
    
    name = "send_message"
    description = """Send a message to a Discord channel.
Use for sending announcements, responding in other channels, or proactive messaging.
Can optionally reply to an existing message."""
    
    parameters = [
        ToolParameter(
            name="channel_id",
            param_type="string",
            description="ID of the channel to send message to",
            required=True
        ),
        ToolParameter(
            name="message",
            param_type="string",
            description="Content of the message to send",
            required=True
        ),
        ToolParameter(
            name="reply_to_message_id",
            param_type="string",
            description="Optional: Message ID to reply to",
            required=False,
            default=None
        )
    ]
    
    permission_level = ToolPermissionLevel.MODERATOR  # Require mod for safety
    
    async def execute(self, args: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        try:
            channel_id = args["channel_id"]
            content = args["message"][:1900]  # Discord limit
            reply_to_id = args.get("reply_to_message_id")
            
            guild = context.get("guild")
            if not guild:
                return ToolResult(success=False, content="❌ No guild available")
            
            channel = guild.get_channel(int(channel_id))
            if not channel:
                return ToolResult(success=False, content=f"❌ Channel {channel_id} not found")
            
            # Check permissions
            if not channel.permissions_for(guild.me).send_messages:
                return ToolResult(success=False, content="❌ No permission to send messages here")
            
            # Send message
            kwargs = {}
            if reply_to_id:
                try:
                    reply_msg = await channel.fetch_message(int(reply_to_id))
                    kwargs["reference"] = reply_msg.to_reference()
                except:
                    pass  # Continue without reply if message not found
            
            sent_msg = await channel.send(content=content, **kwargs)
            
            return ToolResult(
                success=True,
                content=f"✅ Message sent to #{channel.name}! (ID: {sent_msg.id})",
                data={"message_id": str(sent_msg.id), "channel": channel.name}
            )
            
        except discord.Forbidden:
            return ToolResult(success=False, content="❌ Forbidden: Missing permissions to send message")
        except Exception as e:
            logger.error(f"Send message failed: {e}")
            return ToolResult(success=False, content=f"❌ Error sending: {str(e)[:150]}")


# ============================================================
# 😂 ADD REACTION TOOL
# ============================================================
class AddReactionTool(DiscordTool):
    """
    Add emoji reactions to messages - Quick feedback!
    
    AI can react to messages for quick responses.
    """
    
    name = "add_reaction"
    description = """Add an emoji reaction to a message.
Great for quick feedback, voting, or expressing emotions without typing."""
    
    parameters = [
        ToolParameter(
            name="channel_id",
            param_type="string",
            description="Channel ID where the message is",
            required=True
        ),
        ToolParameter(
            name="message_id",
            param_type="string",
            description="ID of the message to react to",
            required=True
        ),
        ToolParameter(
            name="emoji",
            param_type="string",
            description="Emoji to add (e.g., 👍, 🔥, ❤️, 😂)",
            required=True
        )
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
                return ToolResult(success=False, content=f"❌ Channel not found")
            
            message = await channel.fetch_message(int(message_id))
            
            # Check permissions
            if not channel.permissions_for(guild.me).add_reactions:
                return ToolResult(success=False, content="❌ No permission to add reactions")
            
            await message.add_reaction(emoji)
            
            return ToolResult(
                success=True,
                content=f"✅ Added reaction {emoji} to message!"
            )
            
        except discord.NotFound:
            return ToolResult(success=False, content="❌ Message not found")
        except discord.HTTPException as e:
            if "unknown_emoji" in str(e).lower():
                return ToolResult(success=False, content=f"❌ Unknown emoji: {emoji}")
            return ToolResult(success=False, content=f"❌ Could not add reaction: {str(e)[:100]}")
        except Exception as e:
            logger.error(f"Reaction failed: {e}")
            return ToolResult(success=False, content=f"❌ Error: {str(e)[:150]}")


# ============================================================
# 👥 GET MEMBER INFO TOOL
# ============================================================
class GetMemberTool(DiscordTool):
    """
    Get detailed info about a server member - User lookup!
    
    AI can look up users by ID or mention.
    """
    
    name = "get_member_info"
    description = """Get detailed information about a Discord server member.
Returns username, display name, roles, join date, status, and more.
Use for looking up users, verifying members, or getting user context."""
    
    parameters = [
        ToolParameter(
            name="user_id",
            param_type="string",
            description="The user's Discord ID to look up",
            required=True
        ),
        ToolParameter(
            name="guild_id",
            param_type="string",
            description="Guild ID (uses current guild if omitted)",
            required=False,
            default=None
        )
    ]
    
    permission_level = ToolPermissionLevel.EVERYONE
    
    async def execute(self, args: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        try:
            user_id = args["user_id"]
            
            guild = context.get("guild")
            if not guild:
                return ToolResult(success=False, content="❌ No guild available")
            
            # Try to get member
            member = None
            try:
                member = await guild.fetch_member(int(user_id))
            except discord.NotFound:
                # Try get_member (cache only)
                member = guild.get_member(int(user_id))
            
            if not member:
                return ToolResult(success=False, content=f"❌ User {user_id} not found in this server")
            
            # Gather member info
            roles = [role.name for role in member.roles if role.name != "@everyone"]
            joined_at = member.joined_at.strftime("%Y-%m-%d") if member.joined_at else "Unknown"
            created_at = member.created_at.strftime("%Y-%m-%d %H:%M") if member.created_at else "Unknown"
            
            # Status info
            status = "🟢 Online" if member.status == discord.Status.online else \
                     "🌙 Idle" if member.status == discord.Status.idle else \
                     "🔴 DND" if member.status == discord.Status.dnd else \
                     "⚫ Offline"
            
            # Activity info
            activity_str = ""
            if member.activity:
                activity_str = f"\n🎮 Activity: {member.activity.name}" if member.activity.name else ""
            
            info = f"""👤 **Member Info:** {member.display_name}

**Basic Info:**
• Username: `{member.name}`
• ID: `{member.id}`
• Bot: {'✅ Yes' if member.bot else '❌ No'}
• Account Created: {created_at}

**Server Info:**
• Nickname: {member.nick or 'None'}
• Joined Server: {joined_at}
• Status: {status}{activity_str}
• Roles ({len(roles)}): {', '.join(roles[:10]) if roles else 'None'}

**Avatar URL:** {member.avatar.url if member.avatar else 'Default'}"""
            
            return ToolResult(
                success=True,
                content=info,
                data={
                    "username": member.name,
                    "display_name": member.display_name,
                    "id": str(member.id),
                    "roles": roles,
                    "joined_at": joined_at,
                    "is_bot": member.bot,
                    "status": str(member.status)
                }
            )
            
        except Exception as e:
            logger.error(f"Get member failed: {e}")
            return ToolResult(success=False, content=f"❌ Error: {str(e)[:150]}")


# ============================================================
# 🏠 GET SERVER INFO TOOL
# ============================================================
class GetServerInfoTool(DiscordTool):
    """
    Get comprehensive server/guild information - Server awareness!
    
    AI can learn about the server it's in.
    """
    
    name = "get_server_info"
    description = """Get detailed information about the Discord server/guild.
Returns server name, member count, channel count, features, creation date, and more.
Helps AI understand the server context."""
    
    parameters = [
        ToolParameter(
            name="guild_id",
            param_type="string",
            description="Guild ID (uses current guild if omitted)",
            required=False,
            default=None
        )
    ]
    
    permission_level = ToolPermissionLevel.EVERYONE
    
    async def execute(self, args: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        try:
            guild = context.get("guild")
            if not guild:
                return ToolResult(success=False, content="❌ No guild available")
            
            # Gather server stats
            text_channels = len(guild.text_channels)
            voice_channels = len(guild.voice_channels)
            categories = len(guild.categories)
            roles = len(guild.roles)
            emojis = len(guild.emojis)
            
            # Member counts
            online = sum(1 for m in guild.members if m.status == discord.Status.online)
            bots = sum(1 for m in guild.members if m.bot)
            humans = guild.member_count - bots
            
            # Features list
            features = ", ".join(guild.features[:8]) if guild.features else "None"
            
            info = f"""🏠 **Server Information**

**Name:** {guild.name}
**ID:** `{guild.id}`
**Owner:** {guild.owner.display_name if guild.owner else 'Unknown'} (`{guild.owner_id}`)

**Statistics:**
• Members: {guild.member_count} total ({humans} humans, {bots} bots)
• Online Now: ~{online}
• Channels: {text_channels} text + {voice_channels} voice (in {categories} categories)
• Roles: {roles}
• Emojis: {emojis}
• Stickers: {len(guild.stickers)}

**Details:**
• Created: {guild.created_at.strftime('%Y-%m-%d')} ({(datetime.utcnow() - guild.created_at).days} days ago)
• Verification Level: {str(guild.verification_level)}
• Content Filter: {str(guild.explicit_content_filter)}
• Features: {features}

**Bot Permissions Here:**
{self._format_permissions(guild.me.guild_permissions)}"""
            
            return ToolResult(
                success=True,
                content=info,
                data={
                    "name": guild.name,
                    "id": str(guild.id),
                    "member_count": guild.member_count,
                    "channel_count": text_channels + voice_channels,
                    "owner": guild.owner.display_name if guild.owner else None
                }
            )
            
        except Exception as e:
            logger.error(f"Get server info failed: {e}")
            return ToolResult(success=False, content=f"❌ Error: {str(e)[:150]}")
    
    def _format_permissions(self, perms) -> str:
        perm_list = []
        if perms.administrator: perm_list.append("✅ Administrator (FULL ACCESS)")
        if perms.manage_guild: perm_list.append("✅ Manage Server")
        if perms.manage_roles: perm_list.append("✅ Manage Roles")
        if perms.manage_channels: perm_list.append("✅ Manage Channels")
        if perms.kick_members: perm_list.append("✅ Kick Members")
        if perms.ban_members: perm_list.append("✅ Ban Members")
        if perms.moderate_members: perm_list.append("✅ Timeout Members")
        if perms.manage_messages: perm_list.append("✅ Manage Messages")
        if perms.add_reactions: perm_list.append("✅ Add Reactions")
        
        return "\n".join(perm_list) if perm_list else "Limited permissions"


# ============================================================
# 📁 LIST CHANNELS TOOL
# ============================================================
class ListChannelsTool(DiscordTool):
    """
    List all channels in server - Navigation helper!
    
    AI can discover what channels exist.
    """
    
    name = "list_channels"
    description = """List all channels in the Discord server.
Shows channel names, types, IDs, and categories.
Helps AI navigate and understand server structure."""
    
    parameters = [
        ToolParameter(
            name="type_filter",
            param_type="string",
            description="Filter by type: 'text', 'voice', 'all' (default: 'all')",
            required=False,
            default="all",
            enum=["text", "voice", "all"]
        )
    ]
    
    permission_level = ToolPermissionLevel.EVERYONE
    
    async def execute(self, args: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        try:
            type_filter = args.get("type_filter", "all")
            
            guild = context.get("guild")
            if not guild:
                return ToolResult(success=False, content="❌ No guild available")
            
            channels_data = []
            lines = [f"📁 **Channels in {guild.name}:**\n"]
            
            # Group by category
            categories = {None: []}  # None for uncategorized
            for cat in guild.categories:
                categories[cat] = []
            
            for channel in guild.channels:
                if type_filter == "text" and not isinstance(channel, discord.TextChannel):
                    continue
                if type_filter == "voice" and not isinstance(channel, discord.VoiceChannel):
                    continue
                
                cat = channel.category
                if cat not in categories:
                    categories[cat] = []
                categories[cat].append(channel)
            
            # Format output
            for category, channels in categories.items():
                if category:
                    lines.append(f"\n**📂 {category.name}**:")
                else:
                    lines.append("\n**📂 Uncategorized**:")
                
                for ch in channels[:15]:  # Limit per category
                    icon = "💬" if isinstance(ch, discord.TextChannel) else "🔊"
                    nsfw_tag = " 🔞" if getattr(ch, 'nsfw', False) else ""
                    lines.append(f"  {icon} {ch.name} (`{ch.id}`){nsfw_tag}")
                    channels_data.append({
                        "name": ch.name,
                        "id": str(ch.id),
                        "type": "text" if isinstance(ch, discord.TextChannel) else "voice"
                    })
            
            total = sum(len(chs) for chs in categories.values())
            lines.append(f"\n**Total: {total} channels**")
            
            return ToolResult(
                success=True,
                content="\n".join(lines),
                data={"count": total, "channels": channels_data}
            )
            
        except Exception as e:
            logger.error(f"List channels failed: {e}")
            return ToolResult(success=False, content=f"❌ Error: {str(e)[:150]}")


# ============================================================
# 📺 GET CHANNEL INFO TOOL
# ============================================================
class GetChannelInfoTool(DiscordTool):
    """
    Get detailed info about a specific channel - Channel awareness!
    """
    
    name = "get_channel_info"
    description = """Get detailed information about a specific Discord channel.
Returns channel name, type, topic, member count, permissions, and more."""
    
    parameters = [
        ToolParameter(
            name="channel_id",
            param_type="string",
            description="ID of the channel to inspect",
            required=True
        )
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
            
            # Basic info
            ch_type = {
                discord.ChannelType.text: "💬 Text",
                discord.ChannelType.voice: "🔊 Voice",
                discord.ChannelType.category: "📁 Category",
                discord.ChannelType.forum: "📋 Forum",
                discord.ChannelType.stage_voice: "🎤 Stage"
            }.get(channel.type, f"Unknown ({channel.type})")
            
            info = f"""📺 **Channel Information**

**Name:** {channel.name}
**Type:** {ch_type}
**ID:** `{channel.id}`
**Category:** {channel.category.name if channel.category else 'Uncategorized'}"""

            # Text channel specifics
            if isinstance(channel, discord.TextChannel):
                topic = channel.topic or "No topic set"
                nsfw = "🔞 Yes" if channel.nsfw else "No"
                slowmode = channel.slowmode_delay
                
                info += f"""
**Topic:** {topic[:200]}
**NSFW:** {nsfw}
**Slowmode:** {slowmode} seconds
**Position:** {channel.position}"""

            # Voice channel specifics
            elif isinstance(channel, discord.VoiceChannel):
                bitrate = channel.bitrate // 1000  # Convert to kbps
                user_limit = channel.user_limit or "No limit"
                
                info += f"""
**Bitrate:** {bitrate} kbps
**User Limit:** {user_limit}
**Current Users:** {len(channel.members)}"""

            # Forum specifics
            elif isinstance(channel, discord.ForumChannel):
                info += f"""
**Available Tags:** {len(channel.tags)}
**Requires Tag:** {channel.require_tag}"""

            return ToolResult(
                success=True,
                content=info,
                data={
                    "name": channel.name,
                    "id": str(channel.id),
                    "type": str(channel.type)
                }
            )
            
        except Exception as e:
            logger.error(f"Get channel info failed: {e}")
            return ToolResult(success=False, content=f"❌ Error: {str(e)[:150]}")


# ============================================================
# 🆕 CREATE CHANNEL TOOL - ACTUALLY CREATES CHANNELS!
# ============================================================
class CreateChannelTool(DiscordTool):
    """
    Create a new text or voice channel in the server!
    This is a REAL action - not fake! 🛠️
    """
    
    name = "create_channel"
    description = """Create a new channel in the Discord server.
Can create text channels or voice channels. Requires appropriate permissions.
This ACTUALLY creates the channel - it's not fake!"""
    
    parameters = [
        ToolParameter(
            name="name",
            param_type="string",
            description="Name of the channel to create (e.g., 'peace', 'gaming', 'memes')",
            required=True
        ),
        ToolParameter(
            name="channel_type",
            param_type="string",
            description="Type of channel to create",
            required=False,
            default="text",
            enum=["text", "voice"]
        ),
        ToolParameter(
            name="category_id",
            param_type="string",
            description="Category ID to put channel in (optional)",
            required=False,
            default=None
        ),
        ToolParameter(
            name="topic",
            param_type="string",
            description="Topic/description for text channels (optional)",
            required=False,
            default=None
        )
    ]
    
    permission_level = ToolPermissionLevel.MODERATOR  # Mods+ can create channels
    
    async def execute(self, args: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        try:
            name = args["name"].strip().lower().replace(" ", "-")
            channel_type = args.get("channel_type", "text")
            category_id = args.get("category_id")
            topic = args.get("topic")
            
            guild = context.get("guild")
            if not guild:
                return ToolResult(success=False, content="❌ No guild available")
            
            # Check bot permissions
            me = guild.me
            if not me.guild_permissions.manage_channels:
                return ToolResult(
                    success=False, 
                    content="❌ Mere paas channel banane ka permission nahi hai! 😅"
                )
            
            # Get category if specified
            category = None
            if category_id:
                category = guild.get_channel(int(category_id))
            
            # Create the channel based on type
            if channel_type == "voice":
                channel = await guild.create_voice_channel(
                    name=name,
                    category=category
                )
            else:
                channel = await guild.create_text_channel(
                    name=name,
                    topic=topic,
                    category=category
                )
            
            # SUCCESS! Return REAL info
            return ToolResult(
                success=True,
                content=f"✅ **Channel '{channel.name}' successfully created!**\n"
                        f"📺 Type: {channel_type}\n"
                        f"🆔 ID: `{channel.id}`\n"
                        f"🔗 {channel.mention}",
                data={
                    "channel_id": str(channel.id),
                    "channel_name": channel.name,
                    "channel_type": channel_type,
                    "mention": channel.mention
                }
            )
            
        except discord.Forbidden:
            return ToolResult(
                success=False,
                content="❌ Permission denied! Server owner/mod se permission le lo pehle!"
            )
        except Exception as e:
            logger.error(f"Create channel failed: {e}")
            return ToolResult(success=False, content=f"❌ Channel creation failed: {str(e)[:150]}")


# ============================================================
# 🆕 KICK USER TOOL - ACTUALLY KICKS USERS!
# ============================================================
class KickUserTool(DiscordTool):
    """
    Kick a user from the server - REAL moderation action!
    Only owners and moderators can use this.
    """
    
    name = "kick_user"
    description = """Kick a member from the Discord server.
This is a REAL moderation action - the user will be removed from the server.
Only use when explicitly asked by an owner or moderator."""
    
    parameters = [
        ToolParameter(
            name="user_id",
            param_type="string",
            description="ID of the user to kick",
            required=True
        ),
        ToolParameter(
            name="reason",
            param_type="string",
            description="Reason for kick (shown in audit log)",
            required=False,
            default="Kicked by Ophelia"
        )
    ]
    
    permission_level = ToolPermissionLevel.MODERATOR  # Mods+ only
    
    async def execute(self, args: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        try:
            user_id = args["user_id"]
            reason = args.get("reason", "Kicked by Ophelia")
            
            guild = context.get("guild")
            if not guild:
                return ToolResult(success=False, content="❌ No guild available")
            
            # Get member
            member = guild.get_member(int(user_id))
            if not member:
                return ToolResult(success=False, content=f"❌ User `{user_id}` not found in server")
            
            # Check if trying to kick owner/higher role
            if member.id == guild.owner_id:
                return ToolResult(success=False, content="❌ Owner ko kick nahi kar sakte bhai! 😂")
            
            if member.top_role >= guild.me.top_role:
                return ToolResult(
                    success=False, 
                    content=f"❌ {member.display_name} ki role meri se equal/higher hai, kick nahi kar sakti!"
                )
            
            # Actually kick!
            await member.kick(reason=reason)
            
            return ToolResult(
                success=True,
                content=f"✅ **{member.display_name}** ko kick kar diya!\n"
                        f"📝 Reason: {reason}",
                data={"kicked_user": member.display_name, "user_id": user_id}
            )
            
        except discord.Forbidden:
            return ToolResult(
                success=False,
                content="❌ Permission denied! Kick permission chahiye!"
            )
        except Exception as e:
            logger.error(f"Kick failed: {e}")
            return ToolResult(success=False, content=f"❌ Kick failed: {str(e)[:150]}")


# ============================================================
# 🆕 TIMEOUT USER TOOL - ACTUALLY TIMEOUT USERS!
# ============================================================
class TimeoutUserTool(DiscordTool):
    """
    Timeout (mute) a user - REAL moderation action!
    """
    
    name = "timeout_user"
    description = """Timeout/mute a member in the Discord server for a specific duration.
The user won't be able to send messages until timeout expires.
Duration is in minutes (max 1 week = 10080 minutes)."""
    
    parameters = [
        ToolParameter(
            name="user_id",
            param_type="string",
            description="ID of the user to timeout",
            required=True
        ),
        ToolParameter(
            name="duration_minutes",
            param_type="integer",
            description="Timeout duration in minutes (1-10080, default=10)",
            required=False,
            default=10
        ),
        ToolParameter(
            name="reason",
            param_type="string",
            description="Reason for timeout",
            required=False,
            default="Timed out by Ophelia"
        )
    ]
    
    permission_level = ToolPermissionLevel.MODERATOR
    
    async def execute(self, args: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        try:
            user_id = args["user_id"]
            duration = min(max(args.get("duration_minutes", 10), 1), 10080)  # Clamp 1-10080 mins
            reason = args.get("reason", "Timed out by Ophelia")
            
            guild = context.get("guild")
            if not guild:
                return ToolResult(success=False, content="❌ No guild available")
            
            member = guild.get_member(int(user_id))
            if not member:
                return ToolResult(success=False, content=f"❌ User `{user_id}` not found in server")
            
            if member.id == guild.owner_id:
                return ToolResult(success=False, content="❌ Owner ko timeout nahi kar sakte!")
            
            # Calculate timeout datetime
            timeout_until = datetime.utcnow() + timedelta(minutes=duration)
            
            # Apply timeout
            await member.timeout(timeout_until, reason=reason)
            
            duration_text = f"{duration} min" if duration < 60 else f"{duration//60} hours"
            
            return ToolResult(
                success=True,
                content=f"⏰ **{member.display_name}** ko {duration_text} ke liye timeout diya!\n"
                        f"📝 Reason: {reason}",
                data={
                    "timed_out_user": member.display_name,
                    "duration_minutes": duration,
                    "until": timeout_until.isoformat()
                }
            )
            
        except discord.Forbidden:
            return ToolResult(
                success=False,
                content="❌ Permission denied! Timeout/Moderate permission chahiye!"
            )
        except Exception as e:
            logger.error(f"Timeout failed: {e}")
            return ToolResult(success=False, content=f"❌ Timeout failed: {str(e)[:150]}")


# ============================================================
# 📋 EXPORT ALL TOOLS LIST
# ============================================================

ALL_DISCORD_TOOLS = [
    SearchMessagesTool,
    ReadChannelTool,
    SendMessageTool,
    AddReactionTool,
    GetMemberTool,
    GetServerInfoTool,
    ListChannelsTool,
    GetChannelInfoTool,
    CreateChannelTool,      # 🆕 Actually CREATE channels!
    KickUserTool,          # 🆕 Actually KICK users!
    TimeoutUserTool,       # 🆕 Actually TIMEOUT users!
]

def get_all_tools(bot=None) -> List[DiscordTool]:
    """Instantiate all tools with optional bot reference"""
    return [tool_cls(bot=bot) for tool_cls in ALL_DISCORD_TOOLS]
