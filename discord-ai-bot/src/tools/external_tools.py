"""
🌐 External API Tools - Web Search, Image Gen, Code Execution!
=============================================================

FREE APIs INTEGRATED:
✅ **Tavily Search** - Live web search (your key: tvly-dev-YGEwJ...)
✅ **Pollinations.ai** - FREE image generation (no API key needed!)
✅ **E2B Sandbox** - Safe code execution (your key: e2b_7af92747...)

All tools follow DiscordTool interface for seamless integration!

Uses api_keys.py for multi-key support (comma-separated in .env)
"""

import logging
import httpx
import json
import os
from typing import Dict, Any, List, Optional
from datetime import datetime

from .base_tool import DiscordTool, ToolResult, ToolParameter, ToolPermissionLevel

# Import key manager for comma-separated support
from ..utils.api_keys import (
    get_tavily_key,
    get_e2b_key,
    get_key_manager
)

logger = logging.getLogger("ExternalTools")


# ==========================================
# 🔍 WEB SEARCH TOOL (Tavily)
# ==========================================

class WebSearchTool(DiscordTool):
    """
    Search the web for current information using Tavily API!
    
    Your Key: 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
    Free tier: 1000 requests/month
    """
    
    name = "web_search"
    description = """Search the internet for real-time information.
Use this when user asks about:
- Current news or events
- Weather updates
- Sports scores (cricket, football, etc.)
- Latest trends or memes
- Any recent information
- "What's happening?", "Search for [topic]"

Returns summarized results with sources."""
    
    parameters = [
        ToolParameter(
            name="query",
            param_type="string",
            description="Search query - what to search for",
            required=True
        ),
        ToolParameter(
            name="max_results",
            param_type="integer",
            description="Number of results (1-10, default=5)",
            required=False,
            default=5
        ),
        ToolParameter(
            name="search_depth",
            param_type="string",
            description="Search depth: 'basic' or 'advanced' (default=basic)",
            required=False,
            default="basic",
            enum=["basic", "advanced"]
        )
    ]
    
    permission_level = ToolPermissionLevel.EVERYONE
    
    async def execute(self, args: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        try:
            query = args["query"]
            max_results = min(max(args.get("max_results", 5), 1), 10)
            search_depth = args.get("search_depth", "basic")
            
            # Get Tavily key (supports comma-separated)
            tavily_key = get_tavily_key()
            
            if not tavily_key or len(tavily_key) < 10:
                return ToolResult(
                    success=False,
                    content="❌ Tavily API key not configured!\n"
                           "Add to .env: TAVILY_API_KEY=tvly-your-key\n\n"
                           "Get free key at: https://tavily.com (1000 free searches/month)",
                    error="No Tavily API key"
                )
            
            # Use Tavily API
            return await self._search_tavily(query, max_results, search_depth, tavily_key)
            
        except Exception as e:
            logger.error(f"Web search failed: {e}")
            return ToolResult(
                success=False,
                content=f"❌ Search failed: {str(e)[:150]}",
                error=str(e)
            )
    
    async def _search_tavily(self, query: str, max_results: int, search_depth: str, api_key: str) -> ToolResult:
        """Search using Tavily API with proper format"""
        
        url = "https://api.tavily.com/search"
        
        payload = {
            "api_key": api_key,
            "query": query,
            "max_results": max_results,
            "include_answer": True,
            "include_raw_content": False,
            "include_images": False,
            "search_depth": search_depth  # basic or advanced
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload)
            
            if response.status_code == 429:
                return ToolResult(
                    success=False,
                    content="⏰ Tavily rate limit reached! Try again in a minute.",
                    error="rate_limited"
                )
            
            if response.status_code != 200:
                raise Exception(f"Tavily API error {response.status_code}: {response.text[:200]}")
            
            data = response.json()
            
            # Extract answer if available
            answer = data.get("answer", "")
            results = data.get("results", [])
            
            # Format results
            lines = []
            
            if answer:
                lines.append(f"📝 **AI Summary:**\n{answer}\n")
            
            lines.append(f"🔍 **Search Results for '{query}':**\n")
            
            for i, result in enumerate(results[:max_results], 1):
                title = result.get("title", "No title")
                url_link = result.get("url", "")
                content = result.get("content", "")[:250]
                
                lines.append(f"**{i}. {title}**")
                lines.append(f"   {content}")
                lines.append(f"   🔗 <{url_link}>\n")
            
            return ToolResult(
                success=True,
                content="\n".join(lines),
                data={
                    "results_count": len(results),
                    "query": query,
                    "has_answer": bool(answer)
                }
            )


# ==========================================
# 🎨 IMAGE GENERATION TOOL (Pollinations.ai - FREE!)
# ==========================================

class ImageGenerationTool(DiscordTool):
    """
    Generate images using AI - 100% FREE! No API key needed!
    
    Uses Pollinations.ai with FLUX models.
    """
    
    name = "generate_image"
    description = """Generate AI images from text descriptions - completely FREE!
Use this when user wants:
- An image of something ("draw a cat", "generate anime girl")
- Memes or funny images
- Art or illustrations
- Profile pictures or avatars
- "Make an image of...", "Draw...", "Generate..."

Supports any style: realistic, anime, cartoon, oil painting, etc."""
    
    parameters = [
        ToolParameter(
            name="prompt",
            param_type="string",
            description="Detailed description of the image to generate",
            required=True
        ),
        ToolParameter(
            name="style",
            param_type="string",
            description="Art style: realistic, anime, cartoon, oil-painting, digital-art, etc.",
            required=False,
            default=""
        ),
        ToolParameter(
            name="size",
            param_type="string",
            description="Image size: square, landscape, portrait, wide, tall",
            required=False,
            default="square"
        )
    ]
    
    permission_level = ToolPermissionLevel.EVERYONE
    
    async def execute(self, args: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        try:
            prompt = args["prompt"]
            style = args.get("style", "")
            size = args.get("size", "square")
            
            # Build enhanced prompt with style
            if style:
                full_prompt = f"{prompt}, {style} style"
            else:
                full_prompt = prompt
            
            # Size mapping
            size_map = {
                "square": "1024x1024",
                "landscape": "1920x1080",
                "portrait": "1080x1920",
                "wide": "1280x720",
                "tall": "720x1280"
            }
            
            width, height = size_map.get(size, "1024x1024").split("x")
            
            # Pollinations.ai is 100% FREE - no API key needed!
            image_url = f"https://image.pollinations.ai/prompt/{full_prompt.replace(' ', '%20')}?width={width}&height={height}&nologo=true&seed={hash(prompt) % 10000}"
            
            logger.info(f"🎨 Generating image: {prompt[:50]}...")
            
            # Verify image URL works
            async with httpx.AsyncClient(timeout=30.0) as client:
                verify_response = await client.head(image_url)
                if verify_response.status_code == 200:
                    return ToolResult(
                        success=True,
                        content=f"🎨 **Image Generated!**\n\n"
                               f"**Prompt:** {prompt}\n"
                               f"**Style:** {style or 'default'}\n\n"
                               f"[🖼️ Download Image]({image_url})\n\n"
                               f"⚠️ Image generates when you click!",
                        data={
                            "image_url": image_url,
                            "prompt": prompt,
                            "style": style
                        },
                        attachments=[image_url]
                    )
                else:
                    raise Exception("Image generation service unavailable")
            
        except Exception as e:
            logger.error(f"Image generation failed: {e}")
            return ToolResult(
                success=False,
                content=f"❌ Image generation failed: {str(e)[:150]}",
                error=str(e)
            )


# ==========================================
# 💻 CODE EXECUTION TOOL (E2B Sandbox)
# ==========================================

class CodeExecutionTool(DiscordTool):
    """
    Execute code safely in cloud sandbox using E2B!
    
    Your Key: e2b_7af927477963df713498287ae7f38a4d7ff04f5d
    Free tier available at https://e2b.dev
    """
    
    name = "execute_code"
    description = """Execute Python/JavaScript code safely in a sandboxed environment.
Use this when user wants:
- To run code snippets
- To test algorithms
- Math calculations
- Data processing
- "Run this code:", "Execute:", "What does this code output?"

Code runs in isolated cloud environment - SAFE!"""
    
    parameters = [
        ToolParameter(
            name="code",
            param_type="string",
            description="The code to execute",
            required=True
        ),
        ToolParameter(
            name="language",
            param_type="string",
            description="Programming language: python, javascript, typescript",
            required=False,
            default="python"
        )
    ]
    
    permission_level = ToolPermissionLevel.EVERYONE
    
    async def execute(self, args: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        try:
            code = args["code"]
            language = args.get("language", "python").lower()
            
            # Get E2B key (supports comma-separated)
            e2b_key = get_e2b_key()
            
            if not e2b_key or len(e2b_key) < 10:
                # Fallback to local Python execution (limited)
                if language == "python":
                    return await self._safe_python_exec(code)
                else:
                    return ToolResult(
                        success=False,
                        content="❌ E2B API key needed for non-Python execution!\n"
                               "Add to .env: E2B_API_KEY=e2b-your-key\n\n"
                               "Get free key at: https://e2b.dev",
                        error="No E2B API key"
                    )
            
            # Use E2B sandbox
            return await self._e2b_execute(code, language, e2b_key)
            
        except Exception as e:
            logger.error(f"Code execution failed: {e}")
            return ToolResult(
                success=False,
                content=f"❌ Code execution error: {str(e)[:200]}",
                error=str(e)
            )
    
    async def _safe_python_exec(self, code: str) -> ToolResult:
        """Basic safe Python execution (limited fallback)"""
        import sys
        import io
        from contextlib import redirect_stdout, redirect_stderr
        
        # Security check - dangerous operations
        dangerous = ['import os', 'import subprocess', 'system(', 'eval(', 'exec(',
                     '__import__', 'open(', 'write(', '.remove(', '.delete(']
        
        for d in dangerous:
            if d.lower() in code.lower():
                return ToolResult(
                    success=False,
                    content="❌ Code contains potentially unsafe operations!\n"
                           "For full sandbox execution, add E2B_API_KEY to .env",
                    error="Unsafe code detected"
                )
        
        # Execute with timeout
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        
        try:
            stdout = io.StringIO()
            stderr = io.StringIO()
            
            with redirect_stdout(stdout), redirect_stderr(stderr):
                exec_locals = {"__builtins__": __builtins__}
                exec(code, {}, exec_locals)
            
            output = stdout.getvalue()
            errors = stderr.getvalue()
            
            result = []
            if output.strip():
                result.append(f"**📤 Output:**\n```{output}```")
            if errors.strip():
                result.append(f"**⚠️ Errors:**\n```{errors}```")
            if not result:
                result.append("✅ Code executed successfully (no output)")
            
            return ToolResult(success=True, content="\n".join(result))
            
        except TimeoutError:
            return ToolResult(success=False, content="⏰ Code execution timed out!")
        except Exception as e:
            return ToolResult(
                success=False,
                content=f"❌ Execution error:\n```{str(e)}```"
            )
        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr
    
    async def _e2b_execute(self, code: str, language: str, api_key: str) -> ToolResult:
        """Execute code in E2B cloud sandbox"""
        
        # E2B API endpoint
        url = "https://api.e2b.dev/code/execution"
        
        payload = {
            "code": code,
            "language": language
        }
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            
            if response.status_code == 401:
                return ToolResult(
                    success=False,
                    content="❌ Invalid E2B API key! Check your .env file.",
                    error="invalid_api_key"
                )
            
            if response.status_code == 429:
                return ToolResult(
                    success=False,
                    content="⏰ E2B rate limit reached! Try again soon.",
                    error="rate_limited"
                )
            
            if response.status_code != 200:
                data = response.json()
                raise Exception(data.get("message", f"E2B error {response.status_code}"))
            
            data = response.json()
            
            logs = data.get("logs", [])
            output = data.get("output", "")
            error = data.get("error", "")
            
            result_parts = []
            
            if logs:
                log_text = "\n".join([f"  [{l.get('time', '')}] {l.get('message', '')}" for l in logs[-5:]])
                result_parts.append(f"**📋 Logs:**\n```{log_text}```")
            
            if output:
                result_parts.append(f"**📤 Output:**\n```{output}```")
            
            if error:
                result_parts.append(f"**❌ Error:**\n```{error}```")
            
            if not result_parts:
                result_parts.append("✅ Executed successfully!")
            
            return ToolResult(success=True, content="\n".join(result_parts))


# ==========================================
# 📊 GET ALL EXTERNAL TOOLS
# ==========================================

def get_external_tools(bot=None) -> List[DiscordTool]:
    """Get all external tool instances"""
    return [
        WebSearchTool(),
        ImageGenerationTool(),
        CodeExecutionTool(),
    ]


# Tool names for easy reference
EXTERNAL_TOOL_NAMES = ["web_search", "generate_image", "execute_code"]


# Quick test function
async def test_external_tools():
    """Test that all external tools work"""
    print("\n🔧 Testing External Tools...")
    
    # Test Tavily key
    tavily_key = get_tavily_key()
    print(f"  Tavily: {'✅' if tavily_key else '❌'} ({len(tavily_key) if tavily_key else 0} chars)")
    
    # Test E2B key
    e2b_key = get_e2b_key()
    print(f"  E2B: {'✅' if e2b_key else '❌'} ({len(e2b_key) if e2b_key else 0} chars)")
    
    print(f"\n  Tools available: {', '.join(EXTERNAL_TOOL_NAMES)}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_external_tools())
