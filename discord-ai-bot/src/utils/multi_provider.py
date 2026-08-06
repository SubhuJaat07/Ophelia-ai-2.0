"""
🚀 Multi-Provider AI Router - LiteLLM-Style Fallback System!
==========================================================

PROVIDERS (in priority order):
1. **Google Gemini** (Primary) - Generous free tier, high RPM/TPM
2. **Groq** (Speed) - Llama 3.1 for quick responses  
3. **NVIDIA NIM** (Power) - Heavy models for reasoning
4. **Cerebras/HuggingFace** (Backup) - Last resort

FEATURES:
✅ Automatic fallback on 429/500 errors
✅ Provider health tracking
✅ Rate limit awareness
✅ Cost optimization (free tier first!)
✅ Structured logging

Author: Production-Grade Implementation
"""
import os
import json
import time
import logging
import asyncio
from typing import Dict, List, Optional, Any, AsyncIterator
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

import httpx

logger = logging.getLogger("MultiProvider")


# ==========================================
# 📊 Provider Configuration
# ==========================================

class Provider(Enum):
    """Available AI providers"""
    GEMINI = "gemini"
    GROQ = "groq" 
    NVIDIA = "nvidia"
    CEREBRAS = "cerebras"
    OPENROUTER = "openrouter"


@dataclass
class ProviderConfig:
    """Configuration for a single provider"""
    name: str
    api_key_env: str  # Environment variable name
    base_url: str
    models: List[str]  # Available models (first is default)
    max_tokens: int = 4096
    free_tier_rpm: int = 60  # Requests per minute (free tier)
    supports_tools: bool = True
    supports_streaming: bool = True
    
    @property
    def api_key(self) -> Optional[str]:
        return os.getenv(self.api_key_env, "")
    
    @property
    def is_configured(self) -> bool:
        return len(self.api_key or "") > 10


# ==========================================
# 🔧 Default Provider Configurations
# ==========================================

DEFAULT_PROVIDERS: Dict[Provider, ProviderConfig] = {
    Provider.GEMINI: ProviderConfig(
        name="Google Gemini",
        api_key_env="GEMINI_API_KEY",
        base_url="https://generativelanguage.googleapis.com/v1beta",
        models=["gemini-2.0-flash", "gemini-1.5-flash", "gemini-1.5-pro"],
        max_tokens=8192,
        free_tier_rpm=1500,  # VERY generous!
        supports_tools=True,
        supports_streaming=True,
    ),
    
    Provider.GROQ: ProviderConfig(
        name="Groq",
        api_key_env="GROQ_API_KEYS",  # Can be comma-separated
        base_url="https://api.groq.com/openai/v1",
        models=["llama-3.3-70b-versatile", "llama-3.1-70b-versatile", "mixtral-8x7b-32768"],
        max_tokens=4096,
        free_tier_rpm=30,  # Lower but FAST
        supports_tools=True,
        supports_streaming=True,
    ),
    
    Provider.NVIDIA: ProviderConfig(
        name="NVIDIA NIM",
        api_key_env="NVIDIA_API_KEY",
        base_url="https://integrate.api.nvidia.com/v1",
        models=["meta/llama-3.1-70b-instruct", "meta/llama-3.1-405b-instruct", "deepseek-ai/deepseek-v3"],
        max_tokens=4096,
        free_tier_rpm=50,
        supports_tools=False,  # Limited tool support
        supports_streaming=True,
    ),
    
    Provider.CEREBRAS: ProviderConfig(
        name="Cerebras",
        api_key_env="CEREBRAS_API_KEY",
        base_url="https://api.cerebras.ai/v1",
        models=["llama-3.3-70b"],
        max_tokens=4096,
        free_tier_rpm=60,
        supports_tools=False,
        supports_streaming=True,
    ),
    
    Provider.OPENROUTER: ProviderConfig(
        name="OpenRouter",
        api_key_env="OPENROUTER_API_KEY",
        base_url="https://openrouter.ai/api/v1",
        models=["meta-llama/llama-3.1-70b-instruct:free", "google/gemma-2-9b-it:free"],
        max_tokens=4096,
        free_tier_rpm=20,
        supports_tools=False,
        supports_streaming=True,
    ),
}


@dataclass
class ProviderHealth:
    """Track provider health status"""
    provider: Provider
    is_healthy: bool = True
    last_error: Optional[str] = None
    last_success_time: Optional[float] = None
    error_count: int = 0
    success_count: int = 0
    last_request_time: Optional[float] = None
    rate_limited_until: float = 0  # Unix timestamp until which we skip this provider
    
    @property
    def is_rate_limited(self) -> bool:
        return time.time() < self.rate_limited_until
    
    @property
    def success_rate(self) -> float:
        total = self.success_count + self.error_count
        return self.success_count / total if total > 0 else 1.0


# ==========================================
# 🎯 Multi-Provider Router Class
# ==========================================

class MultiProviderRouter:
    """
    Intelligent AI request router with automatic fallback.
    
    Usage:
        router = MultiProviderRouter()
        response = await router.generate("Hello!", tools=[...])
        
    The router will:
    1. Try primary provider (Gemini)
    2. On failure, try next provider automatically
    3. Track health and avoid unhealthy providers
    4. Respect rate limits
    """
    
    def __init__(self):
        self.providers: Dict[Provider, ProviderConfig] = DEFAULT_PROVIDERS.copy()
        self.health: Dict[Provider, ProviderHealth] = {
            p: ProviderHealth(provider=p) for p in Provider
        }
        
        # Priority order for fallback
        self.provider_priority: List[Provider] = [
            Provider.GEMINI,   # Primary - most generous free tier
            Provider.GROQ,     # Speed - fast responses
            Provider.NVIDIA,   # Power - heavy reasoning
            Provider.CEREBRAS, # Backup
            Provider.OPENROUTER, # Last resort
        ]
        
        # HTTP client with timeout
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(30.0, connect=5.0),
            headers={"Content-Type": "application/json"}
        )
        
        # Track current Groq key index (for multi-key rotation)
        self._groq_key_index = 0
        self._groq_keys: List[str] = []
        
        logger.info(f"🚀 MultiProvider Router initialized with {len(self.providers)} providers")
    
    async def close(self):
        """Clean up HTTP client"""
        await self.client.aclose()
    
    def _get_groq_keys(self) -> List[str]:
        """Get all available Groq keys"""
        if not self._groq_keys:
            keys_str = os.getenv("GROQ_API_KEYS", "")
            self._groq_keys = [k.strip() for k in keys_str.split(",") if len(k.strip()) > 10]
        return self._groq_keys
    
    def _get_next_groq_key(self) -> Optional[str]:
        """Rotate through Groq keys"""
        keys = self._get_groq_keys()
        if not keys:
            return None
        
        key = keys[self._groq_key_index % len(keys)]
        self._groq_key_index += 1
        return key
    
    def _get_api_key(self, provider: Provider) -> Optional[str]:
        """Get API key for provider"""
        config = self.providers.get(provider)
        if not config:
            return None
        
        # Special handling for Groq (multi-key support)
        if provider == Provider.GROQ:
            groq_key = self._get_next_groq_key()
            if groq_key:
                return groq_key
            # Fallback to single key from env
            return os.getenv("GROQ_API_KEY", "")
        
        return config.api_key
    
    def get_available_providers(self) -> List[Provider]:
        """Get list of configured and healthy providers"""
        available = []
        for p in self.provider_priority:
            config = self.providers.get(p)
            health = self.health.get(p)
            
            if config and config.is_configured:
                if health and health.is_healthy and not health.is_rate_limited:
                    available.append(p)
                elif health is None:
                    available.append(p)
        
        return available
    
    async def generate(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict]] = None,
        temperature: float = 1.02,
        max_tokens: int = 1024,
        preferred_provider: Optional[Provider] = None,
    ) -> Dict[str, Any]:
        """
        Generate AI response with automatic fallback.
        
        Args:
            messages: Chat messages in OpenAI format
            tools: Tool definitions (OpenAI function calling format)
            temperature: Generation temperature
            max_tokens: Max tokens to generate
            preferred_provider: Force specific provider (optional)
        
        Returns:
            Dict with 'content', 'tool_calls', 'provider', 'model' keys
        """
        # Determine which providers to try
        if preferred_provider:
            providers_to_try = [preferred_provider]
        else:
            providers_to_try = self.get_available_providers()
        
        if not providers_to_try:
            logger.error("❌ No providers available!")
            return {
                "content": "😅 Sorry bhai, saare AI providers down hain! Thoda der baad try karo.",
                "tool_calls": None,
                "provider": None,
                "model": None,
                "error": "No providers available"
            }
        
        last_error = None
        
        for provider in providers_to_try:
            try:
                result = await self._try_provider(
                    provider=provider,
                    messages=messages,
                    tools=tools,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                
                if result:
                    # Update health tracking
                    health = self.health[provider]
                    health.is_healthy = True
                    health.last_success_time = time.time()
                    health.success_count += 1
                    health.last_request_time = time.time()
                    
                    logger.info(f"✅ {provider.value} responded successfully")
                    return result
                
            except RateLimitError as e:
                logger.warning(f"⏳ {provider.value} rate limited: {e}")
                health = self.health[provider]
                health.rate_limited_until = time.time() + 60  # Skip for 60 seconds
                health.error_count += 1
                last_error = e
                
            except ProviderError as e:
                logger.warning(f"❌ {provider.value} failed: {e}")
                health = self.health[provider]
                health.is_healthy = False
                health.last_error = str(e)
                health.error_count += 1
                last_error = e
            
            except Exception as e:
                logger.error(f"💥 Unexpected error from {provider.value}: {e}")
                last_error = e
        
        # All providers failed
        logger.error(f"❌ ALL providers failed! Last error: {last_error}")
        return {
            "content": "😅 Arre yaar, sab AI providers problem kar rahe hain! Thoda der baad try karo na?",
            "tool_calls": None,
            "provider": None,
            "model": None,
            "error": str(last_error)
        }
    
    async def _try_provider(
        self,
        provider: Provider,
        messages: List[Dict],
        tools: Optional[List[Dict]],
        temperature: float,
        max_tokens: int,
    ) -> Optional[Dict]:
        """Try a single provider and return result or raise exception"""
        config = self.providers[provider]
        api_key = self._get_api_key(provider)
        
        if not api_key or len(api_key) < 10:
            raise ProviderError(f"No API key for {config.name}")
        
        model = config.models[0]  # Use default model
        
        logger.debug(f"🔄 Trying {config.name} ({model})...")
        
        if provider == Provider.GEMINI:
            return await self._call_gemini(config, api_key, model, messages, tools, temperature, max_tokens)
        elif provider == Provider.GROQ:
            return await self._call_openai_compat(config, api_key, model, messages, tools, temperature, max_tokens)
        elif provider == Provider.NVIDIA:
            return await self._call_openai_compat(config, api_key, model, messages, tools, temperature, max_tokens)
        elif provider in [Provider.CEREBRAS, Provider.OPENROUTER]:
            return await self._call_openai_compat(config, api_key, model, messages, tools, temperature, max_tokens)
        
        raise ProviderError(f"Unknown provider: {provider}")
    
    async def _call_gemini(
        self,
        config: ProviderConfig,
        api_key: str,
        model: str,
        messages: List[Dict],
        tools: Optional[List[Dict]],
        temperature: float,
        max_tokens: int,
    ) -> Dict:
        """Call Google Gemini API"""
        url = f"{config.base_url}/models/{model}:generateContent?key={api_key}"
        
        # Convert OpenAI format to Gemini format
        contents = []
        system_instruction = ""
        
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            
            if role == "system":
                system_instruction = content
            else:
                gemini_role = "model" if role == "assistant" else "user"
                contents.append({
                    "role": gemini_role,
                    "parts": [{"text": content}]
                })
        
        payload = {
            "contents": contents,
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
                "topP": 1.0,
            }
        }
        
        if system_instruction:
            payload["systemInstruction"] = {"parts": [{"text": system_instruction}]}
        
        # Convert tools to Gemini format if provided
        if tools:
            gemini_functions = []
            for tool in tools:
                if "function" in tool:
                    func = tool["function"]
                    gemini_functions.append({
                        "name": func.get("name", ""),
                        "description": func.get("description", ""),
                        "parameters": func.get("parameters", {})
                    })
            if gemini_functions:
                payload["tools"] = [{"functionDeclarations": gemini_functions}]
        
        response = await self.client.post(url, json=payload)
        
        if response.status_code == 429:
            raise RateLimitError(f"Gemini rate limit exceeded")
        elif response.status_code != 200:
            raise ProviderError(f"Gemini API error {response.status_code}: {response.text[:200]}")
        
        data = response.json()
        
        # Parse Gemini response
        candidate = data.get("candidates", [{}])[0]
        content_data = candidate.get("content", {})
        parts = content_data.get("parts", [{}])
        
        text_content = ""
        tool_calls = None
        
        for part in parts:
            if "text" in part:
                text_content += part["text"]
            elif "functionCall" in part:
                if tool_calls is None:
                    tool_calls = []
                fc = part["functionCall"]
                tool_calls.append({
                    "id": fc.get("name", ""),
                    "type": "function",
                    "function": {
                        "name": fc.get("name", ""),
                        "arguments": json.dumps(fc.get("args", {}))
                    }
                })
        
        return {
            "content": text_content or None,
            "tool_calls": tool_calls,
            "provider": Provider.GEMINI,
            "model": model,
            "usage": data.get("usageMetadata", {})
        }
    
    async def _call_openai_compat(
        self,
        config: ProviderConfig,
        api_key: str,
        model: str,
        messages: List[Dict],
        tools: Optional[List[Dict]],
        temperature: float,
        max_tokens: int,
    ) -> Dict:
        """Call OpenAI-compatible API (Groq, NVIDIA, Cerebras, etc.)"""
        url = f"{config.base_url}/chat/completions"
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        # NVIDIA needs special header
        if config.name == "NVIDIA NIM":
            headers["Accept"] = "application/json"
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "top_p": 1.0,
        }
        
        if tools and config.supports_tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"
        
        response = await self.client.post(url, json=payload, headers=headers)
        
        if response.status_code == 429:
            raise RateLimitError(f"{config.name} rate limit exceeded")
        elif response.status_code == 500 or response.status_code == 502:
            raise ProviderError(f"{config.name} server error")
        elif response.status_code != 200:
            raise ProviderError(f"{config.name} API error {response.status_code}: {response.text[:200]}")
        
        data = response.json()
        choice = data.get("choices", [{}])[0]
        message = choice.get("message", {})
        
        return {
            "content": message.get("content"),
            "tool_calls": message.get("tool_calls"),
            "provider": config.name.lower().replace(" ", "_").replace("-", "_"),
            "model": data.get("model", model),
            "usage": data.get("usage", {})
        }
    
    async def generate_stream(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> AsyncIterator[str]:
        """Generate streaming response (for future use)"""
        # For now, just yield non-streaming result
        result = await self.generate(messages, **kwargs)
        if result.get("content"):
            yield result["content"]
    
    def get_status(self) -> Dict[str, Any]:
        """Get status of all providers"""
        status = {}
        for p, health in self.health.items():
            config = self.providers.get(p)
            status[p.value] = {
                "configured": config.is_configured if config else False,
                "healthy": health.is_healthy,
                "success_rate": f"{health.success_rate:.1%}",
                "rate_limited": health.is_rate_limited,
                "last_error": health.last_error,
            }
        return status


# ==========================================
# ❌ Custom Exceptions
# ==========================================

class ProviderError(Exception):
    """Provider returned an error"""
    pass


class RateLimitError(ProviderError):
    """Provider rate limited us"""
    pass


# ==========================================
# 🌍 Global Instance
# ==========================================

_router: Optional[MultiProviderRouter] = None


def init_multi_provider() -> MultiProviderRouter:
    """Initialize global multi-provider router"""
    global _router
    _router = MultiProviderRouter()
    
    # Log which providers are configured
    for p in _router.provider_priority:
        config = _router.providers[p]
        status = "✅" if config.is_configured else "❌"
        logger.info(f"   {status} {config.name}: {'configured' if config.is_configured else 'missing API key'}")
    
    return _router


def get_multi_provider() -> MultiProviderRouter:
    """Get global multi-provider router instance"""
    if _router is None:
        return init_multi_provider()
    return _router
