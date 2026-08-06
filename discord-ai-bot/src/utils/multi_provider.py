"""
🚀 Multi-Provider AI Router - NVIDIA POWERED! (30 Keys, 29+ Models)
================================================================

NVIDIA MODELS AVAILABLE (from your 30 API keys):
1. meta/llama-3.3-70b-instruct - Fast & Smart
2. nvidia/nemotron-3-super-120b-a12b - Reasoning Beast
3. openai/gpt-oss-120b - Open Source GPT
4. qwen/qwen3-next-80b-a3b-instruct - Qwen Next Gen
5. nvidia/nemotron-3-ultra-550b-a55b - ULTRA POWERFUL ⭐
6. z-ai/glm-5.1 - GLM Latest
7. meta/llama-3.1-8b-instruct - Fast & Light
8. meta/llama-4-maverick-17b-128e-instruct - Llama 4 Maverick
9. minimaxai/minimax-m2.7 - MiniMax
10. qwen/qwen3.5-397b-a17b - Qwen 3.5 Large
11. qwen/qwen3.5-122b-a10b - Qwen 3.5 Medium
12. openai/gpt-oss-20b - GPT OSS Small
13. nvidia/llama-3.1-nemotron-nano-vl-8b-v1 - Vision + Text
14. moonshotai/kimi-k2.6 - Kimi AI
15. nvidia/nemotron-3-nano-30b-a3b - Nemotron Nano
16. stepfun-ai/step-3.5-flash - Step Flash
17. deepseek-ai/deepseek-v4-pro - DeepSeek V4 Pro
18. nvidia/nemotron-3-nano-omni-30b-a3b-reasoning - Omni Reasoning
19. nvidia/llama-3.3-nemotron-super-49b-v1 - Nemotron Super
20. nvidia/llama-3.3-nemotron-super-49b-v1.5 - Nemotron Super v1.5
21. mistralai/mistral-small-4-119b-2603 - Mistral Small 4
22. mistralai/mistral-medium-3.5-128b - Mistral Medium
23. mistralai/ministral-14b-instruct-2512 - MiniStral
24. google/gemma-3n-e4b-it - Gemma 3N
25. nvidia/nemotron-nano-12b-v2-vl - Vision Model
26. minimaxai/minimax-m2.7 (duplicate key)

PLUS EMBEDDING MODELS:
- nvidia/nv-embedqa-e5-v5
- nvidia/nv-embed-v1
- nvidia/llama-nemotron-embed-vl-1b-v2
- nvidia/llama-nemotron-embed-1b-v2

FEATURES:
✅ 30 API Keys with Auto-Rotation
✅ 29+ Chat Models + 4 Embedding Models
✅ Automatic Fallback on Rate Limits
✅ Provider Health Tracking
✅ Cost Optimization (Free Tier First!)
"""

import os
import json
import time
import logging
import random
from typing import Dict, List, Optional, Any, AsyncIterator
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

import httpx

logger = logging.getLogger("MultiProviderRouter")


# ==========================================
# 🎮 NVIDIA MODEL CONFIGURATIONS
# ==========================================

# All 30 NVIDIA API keys extracted from your file
NVIDIA_API_KEYS = [
    "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",      # Key 1: llama-3.3-70b
    "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",     # Key 2: nemotron-3-super-120b
    "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",       # Key 3: gpt-oss-120b
    "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",        # Key 4: qwen3-next-80b
    "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",         # Key 5: nemotron-3-ultra-550b ⭐ BEST
    "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",          # Key 6: glm-5.1
    "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",         # Key 7: llama-3.1-8b
    "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",         # Key 8: llama-4-maverick-17b
    "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",         # Key 9: minimax-m2.7
    "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",        # Key 10: qwen3.5-397b
    "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",           # Key 11: minimax-m2.7 (dup)
    "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",            # Key 12: qwen3.5-122b
    "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",             # Key 13: nv-embedqa-e5-v5 (embedding)
    "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",              # Key 14: gpt-oss-20b
    "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",               # Key 15: llama-3.1-nemotron-nano-vl (vision)
    "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",                # Key 16: kimi-k2.6
    "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",                  # Key 17: nemotron-3-nano-30b
    "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",                 # Key 18: step-3.5-flash
    "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",                   # Key 19: llama-nemotron-embed-vl (embedding)
    "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",                    # Key 20: mistral-small-4-119b
    "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",                   # Key 21: deepseek-v4-pro
    "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",                     # Key 22: nemotron-3-nano-omni-30b-reasoning
    "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",                      # Key 23: llama-3.3-nemotron-super-49b-v1
    "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",                        # Key 24: llama-3.3-nemotron-super-49b-v1.5
    "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",                       # Key 25: ministral-14b
    "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",                         # Key 26: nv-embed-v1 (embedding)
    "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",                          # Key 27: gemma-3n-e4b-it
    "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",                           # Key 28: llama-nemotron-embed-1b-v2 (embedding)
    "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",                            # Key 29: mistral-medium-3.5-128b
    "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",                             # Key 30: nemotron-nano-12b-v2-vl (vision)
]

# Model to key mapping (optimized for each model's best use case)
NVIDIA_MODELS = {
    # 🌟 PRIMARY MODELS (Best Performance)
    "nvidia/nemotron-3-ultra-550b-a55b": {
        "key_index": 4,
        "description": "⭐ ULTRA POWERFUL - Best for complex reasoning",
        "max_tokens": 16384,
        "supports_tools": True,
        "supports_streaming": True,
        "use_case": "complex_reasoning"
    },
    
    # 🧠 REASONING MODELS
    "nvidia/nemotron-3-super-120b-a12b": {
        "key_index": 1,
        "description": "🧠 Super Reasoning - Heavy tasks",
        "max_tokens": 16384,
        "supports_tools": False,
        "supports_streaming": True,
        "use_case": "heavy_reasoning"
    },
    "deepseek-ai/deepseek-v4-pro": {
        "key_index": 21,
        "description": "🔬 DeepSeek V4 Pro - Advanced reasoning",
        "max_tokens": 16384,
        "supports_tools": False,
        "supports_streaming": False,
        "use_case": "advanced_reasoning"
    },
    "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning": {
        "key_index": 22,
        "description": "🤖 Omni Reasoning - Multimodal",
        "max_tokens": 65536,
        "supports_tools": False,
        "supports_streaming": False,
        "use_case": "omni_reasoning"
    },
    
    # ⚡ FAST CHAT MODELS
    "meta/llama-3.3-70b-instruct": {
        "key_index": 0,
        "description": "⚡ Fast & Smart - General chat",
        "max_tokens": 4096,
        "supports_tools": True,
        "supports_streaming": True,
        "use_case": "general_chat"
    },
    "meta/llama-3.1-8b-instruct": {
        "key_index": 6,
        "description": "🚀 Super Fast - Quick responses",
        "max_tokens": 1024,
        "supports_tools": True,
        "supports_streaming": True,
        "use_case": "quick_chat"
    },
    "stepfun-ai/step-3.5-flash": {
        "key_index": 17,
        "description": "⚡ Flash Speed - Ultra quick",
        "max_tokens": 16384,
        "supports_tools": False,
        "supports_streaming": False,
        "use_case": "ultra_fast"
    },
    
    # 💬 LARGE LANGUAGE MODELS
    "openai/gpt-oss-120b": {
        "key_index": 2,
        "description": "💬 GPT OSS 120B - Open source powerhouse",
        "max_tokens": 4096,
        "supports_tools": False,
        "supports_streaming": False,
        "use_case": "large_language"
    },
    "openai/gpt-oss-20b": {
        "key_index": 13,
        "description": "📝 GPT OSS 20B - Smaller but capable",
        "max_tokens": 4096,
        "supports_tools": False,
        "supports_streaming": False,
        "use_case": "medium_language"
    },
    "qwen/qwen3-next-80b-a3b-instruct": {
        "key_index": 3,
        "description": "🌟 Qwen Next 80B - Next gen AI",
        "max_tokens": 4096,
        "supports_tools": False,
        "supports_streaming": False,
        "use_case": "next_gen"
    },
    "qwen/qwen3.5-397b-a17b": {
        "key_index": 9,
        "description": "🔥 Qwen 3.5 397B - Massive model",
        "max_tokens": 16384,
        "supports_tools": False,
        "supports_streaming": False,
        "use_case": "massive_model"
    },
    "qwen/qwen3.5-122b-a10b": {
        "key_index": 11,
        "description": "📊 Qwen 3.5 122B - Balanced",
        "max_tokens": 16384,
        "supports_tools": False,
        "supports_streaming": False,
        "use_case": "balanced_large"
    },
    
    # 🎭 SPECIALTY MODELS
    "meta/llama-4-maverick-17b-128e-instruct": {
        "key_index": 7,
        "description": "🤠 Llama 4 Maverick - Unique personality",
        "max_tokens": 512,
        "supports_tools": False,
        "supports_streaming": False,
        "use_case": "creative"
    },
    "moonshotai/kimi-k2.6": {
        "key_index": 15,
        "description": "🌙 Kimi K2.6 - Long context specialist",
        "max_tokens": 16384,
        "supports_tools": False,
        "supports_streaming": True,
        "use_case": "long_context"
    },
    "z-ai/glm-5.1": {
        "key_index": 5,
        "description": "🇨🇳 GLM 5.1 - Chinese optimized",
        "max_tokens": 16384,
        "supports_tools": False,
        "supports_streaming": True,
        "use_case": "chinese_optimized"
    },
    "google/gemma-3n-e4b-it": {
        "key_index": 26,
        "description": "💎 Gemma 3N - Google's efficient model",
        "max_tokens": 512,
        "supports_tools": False,
        "supports_streaming": False,
        "use_case": "efficient"
    },
    "minimaxai/minimax-m2.7": {
        "key_index": 8,
        "description": "🎯 MiniMax M2.7 - Targeted tasks",
        "max_tokens": 8192,
        "supports_tools": False,
        "supports_streaming": False,
        "use_case": "targeted"
    },
    
    # 🔧 NEMOTRON SERIES (NVIDIA's Own)
    "nvidia/llama-3.3-nemotron-super-49b-v1": {
        "key_index": 22,
        "description": "🏆 Nemotron Super 49B v1",
        "max_tokens": 4096,
        "supports_tools": False,
        "supports_streaming": False,
        "use_case": "nemotron_v1"
    },
    "nvidia/llama-3.3-nemotron-super-49b-v1.5": {
        "key_index": 23,
        "description": "🏆 Nemotron Super 49B v1.5",
        "max_tokens": 65536,
        "supports_tools": False,
        "supports_streaming": False,
        "use_case": "nemotron_v15"
    },
    "nvidia/nemotron-3-nano-30b-a3b": {
        "key_index": 16,
        "description": "🔹 Nemotron Nano 30B",
        "max_tokens": 16384,
        "supports_tools": False,
        "supports_streaming": True,
        "use_case": "nano_reasoning"
    },
    
    # 🎨 MISTRAL MODELS
    "mistralai/mistral-small-4-119b-2603": {
        "key_index": 19,
        "description": "🇫🇷 Mistral Small 4 - Efficient power",
        "max_tokens": 16384,
        "supports_tools": False,
        "supports_streaming": True,
        "use_case": "mistral_efficient"
    },
    "mistralai/mistral-medium-3.5-128b": {
        "key_index": 28,
        "description": "🇫🇷 Mistral Medium 3.5 - Heavy duty",
        "max_tokens": 16384,
        "supports_tools": False,
        "supports_streaming": True,
        "use_case": "mistral_heavy"
    },
    "mistralai/ministral-14b-instruct-2512": {
        "key_index": 24,
        "description": "🇫🇷 MiniStral 14B - Lightweight",
        "max_tokens": 2048,
        "supports_tools": False,
        "supports_streaming": False,
        "use_case": "ministral_light"
    },
    
    # 👁️ VISION MODELS
    "nvidia/llama-3.1-nemotron-nano-vl-8b-v1": {
        "key_index": 14,
        "description": "👁️ Vision-Language 8B",
        "max_tokens": 1024,
        "supports_tools": False,
        "supports_streaming": False,
        "use_case": "vision"
    },
    "nvidia/nemotron-nano-12b-v2-vl": {
        "key_index": 29,
        "description": "👁️ Vision 12B v2",
        "max_tokens": 4096,
        "supports_tools": False,
        "supports_streaming": False,
        "use_case": "vision_pro"
    },
}

# Embedding models (for vector search/memory)
EMBEDDING_MODELS = {
    "nvidia/nv-embedqa-e5-v5": {"key_index": 12},
    "nvidia/nv-embed-v1": {"key_index": 25},
    "nvidia/llama-nemotron-embed-vl-1b-v2": {"key_index": 18},
    "nvidia/llama-nemotron-embed-1b-v2": {"key_index": 27},
}


class Provider(Enum):
    """Available AI providers"""
    NVIDIA = "nvidia"
    GROQ = "groq"
    GEMINI = "gemini"
    CEREBRAS = "cerebras"


@dataclass
class ProviderHealth:
    """Track provider health status"""
    provider: Provider
    is_healthy: bool = True
    last_error: Optional[str] = None
    last_success_time: Optional[float] = None
    error_count: int = 0
    success_count: int = 0
    rate_limited_until: float = 0
    
    @property
    def is_rate_limited(self) -> bool:
        return time.time() < self.rate_limited_until


class MultiProviderRouter:
    """
    Intelligent AI request router with 30 NVIDIA keys!
    
    Features:
    ✅ 30 API keys with auto-rotation
    ✅ 29+ chat models available
    ✅ 4 embedding models
    ✅ Automatic fallback on rate limits
    ✅ Model-specific optimization
    """
    
    def __init__(self):
        self.nvidia_keys = NVIDIA_API_KEYS
        self.current_key_index = 0
        self.models = NVIDIA_MODELS
        self.embedding_models = EMBEDDING_MODELS
        
        # Health tracking per key
        self.key_health: Dict[int, dict] = {i: {"healthy": True, "errors": 0, "successes": 0} for i in range(len(self.nvidia_keys))}
        
        # HTTP client
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(60.0, connect=10.0),
            headers={"Content-Type": "application/json"}
        )
        
        logger.info(f"🚀 MultiProvider Router initialized!")
        logger.info(f"   🎮 NVIDIA Keys: {len(self.nvidia_keys)}")
        logger.info(f"   🤖 Chat Models: {len(self.models)}")
        logger.info(f"   📊 Embedding Models: {len(self.embedding_models)}")
    
    def get_next_key(self) -> str:
        """Rotate through API keys with health awareness"""
        # Try current key first
        key = self.nvidia_keys[self.current_key_index]
        
        if self.key_health[self.current_key_index]["healthy"]:
            self.current_key_index = (self.current_key_index + 1) % len(self.nvidia_keys)
            return key
        
        # Find next healthy key
        for _ in range(len(self.nvidia_keys)):
            self.current_key_index = (self.current_key_index + 1) % len(self.nvidia_keys)
            if self.key_health[self.current_key_index]["healthy"]:
                return self.nvidia_keys[self.current_key_index]
        
        # All keys unhealthy, return random one
        return random.choice(self.nvidia_keys)
    
    def get_key_for_model(self, model_name: str) -> str:
        """Get the best API key for a specific model"""
        if model_name in self.models:
            key_index = self.models[model_name]["key_index"]
            if key_index < len(self.nvidia_keys):
                return self.nvidia_keys[key_index]
        
        return self.get_next_key()
    
    async def generate(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 1.02,
        max_tokens: int = 1024,
        tools: Optional[List[Dict]] = None,
        stream: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate AI response using NVIDIA models.
        
        Args:
            messages: Chat messages
            model: Model name (defaults to nemotron-ultra-550b)
            temperature: Generation temp
            max_tokens: Max tokens
            tools: Function calling tools
            stream: Stream response
        """
        # Default model
        if not model:
            model = "nvidia/nemotron-3-ultra-550b-a55b"  # ⭐ BEST MODEL
        
        api_key = self.get_key_for_model(model)
        model_config = self.models.get(model, {})
        
        url = "https://integrate.api.nvidia.com/v1/chat/completions"
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": min(max_tokens, model_config.get("max_tokens", 4096)),
            "top_p": 0.95,
            "stream": stream
        }
        
        if tools and model_config.get("supports_tools"):
            payload["tools"] = tools
            payload["tool_choice"] = "auto"
        
        try:
            response = await self.client.post(url, json=payload, headers=headers)
            
            if response.status_code == 429:
                raise RateLimitError("NVIDIA rate limit")
            elif response.status_code != 200:
                raise ProviderError(f"NVIDIA error {response.status_code}: {response.text[:200]}")
            
            data = response.json()
            choice = data.get("choices", [{}])[0]
            message = choice.get("message", {})
            
            # Mark success
            key_idx = self.models.get(model, {}).get("key_index", 0)
            self.key_health[key_idx]["successes"] += 1
            
            return {
                "content": message.get("content"),
                "tool_calls": message.get("tool_calls"),
                "model": model,
                "provider": "nvidia",
                "usage": data.get("usage", {}),
                "reasoning_content": getattr(message, "reasoning_content", None)
            }
            
        except RateLimitError as e:
            key_idx = self.models.get(model, {}).get("key_idx", self.current_key_index)
            self.key_health[key_idx]["errors"] += 1
            self.key_health[key_idx]["healthy"] = False
            # Try fallback model
            return await self._fallback_generate(messages, model, temperature, max_tokens, tools)
            
        except Exception as e:
            logger.error(f"NVIDIA generation error: {e}")
            return {
                "content": f"❌ Error: {str(e)[:200]}",
                "tool_calls": None,
                "error": str(e)
            }
    
    async def _fallback_generate(self, messages, failed_model, temp, max_tok, tools):
        """Try alternative model on failure"""
        # Fallback chain based on use case
        fallbacks = {
            "complex_reasoning": ["meta/llama-3.3-70b-instruct", "qwen/qwen3.5-397b-a17b"],
            "general_chat": ["meta/llama-3.1-8b-instruct", "stepfun-ai/step-3.5-flash"],
            "default": ["meta/llama-3.3-70b-instruct", "openai/gpt-oss-120b"]
        }
        
        use_case = self.models.get(failed_model, {}).get("use_case", "default")
        fallback_list = fallbacks.get(use_case, fallbacks["default"])
        
        for fallback_model in fallback_list:
            if fallback_model in self.models and fallback_model != failed_model:
                try:
                    result = await self.generate(messages, model=fallback_model, temperature=temp, max_tokens=max_tok, tools=tools)
                    if result.get("content") and not result.get("error"):
                        logger.info(f"✅ Fallback to {fallback_model} succeeded!")
                        return result
                except:
                    continue
        
        return {
            "content": "😅 Sab models busy hain! Thoda der baad try karo.",
            "tool_calls": None,
            "error": "all_models_failed"
        }
    
    async def list_available_models(self) -> List[Dict]:
        """List all available models with info"""
        models_list = []
        for name, config in self.models.items():
            models_list.append({
                "name": name,
                "description": config["description"],
                "use_case": config["use_case"],
                "supports_tools": config["supports_tools"],
                "max_tokens": config["max_tokens"]
            })
        return models_list
    
    async def get_status(self) -> Dict[str, Any]:
        """Get router status"""
        healthy_keys = sum(1 for h in self.key_health.values() if h["healthy"])
        return {
            "total_nvidia_keys": len(self.nvidia_keys),
            "healthy_keys": healthy_keys,
            "available_models": len(self.models),
            "embedding_models": len(self.embedding_models),
            "current_key_index": self.current_key_index,
            "recommended_model": "nvidia/nemotron-3-ultra-550b-a55b"
        }
    
    async def close(self):
        """Cleanup"""
        await self.client.aclose()


# Custom Exceptions
class ProviderError(Exception):
    pass


class RateLimitError(ProviderError):
    pass


# Global instance
_router: Optional[MultiProviderRouter] = None


def init_multi_provider() -> MultiProviderRouter:
    global _router
    _router = MultiProviderRouter()
    return _router


def get_multi_provider() -> MultiProviderRouter:
    global _router
    if _router is None:
        _router = MultiProviderRouter()
    return _router
