"""
🎮 NVIDIA NIM MODELS COMPLETE REFERENCE (29+ Models)
====================================================

IMPORTANT: EK HI API KEY SE SAB MODELS KAM KARTE HAIN!
====================================================
- Base URL: https://integrate.api.nvidia.com/v1/chat/completions
- Authorization: Bearer YOUR_NVIDIA_API_KEY
- Sirf "model" field change karo har model ke liye

YOUR 30 API KEYS (already in multi_provider.py):
===============================================
All keys work for ALL models! Auto-rotation enabled.

QUICK START:
===========
import httpx
import asyncio

async def chat_with_nvidia(prompt, model="nvidia/nemotron-3-ultra-550b-a55b"):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://integrate.api.nvidia.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {NVIDIA_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.7,
                "max_tokens": 1024
            }
        )
        return response.json()
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum


class ModelCategory(Enum):
    """Model categories for easy selection"""
    ULTRA_POWERFUL = "ultra"          # Best reasoning
    FAST_CHAT = "fast"                 # Quick responses
    REASONING = "reasoning"           # Complex logic
    LARGE_LANGUAGE = "large"          # Big context
    VISION = "vision"                 # Image understanding
    EFFICIENT = "efficient"           # Low cost/fast
    SPECIALTY = "specialty"           # Unique capabilities
    EMBEDDING = "embedding"           # Vector embeddings


@dataclass
class NvidiaModel:
    """Complete NVIDIA Model Information"""
    name: str                          # Model ID for API
    display_name: str                  # Human readable name
    category: ModelCategory
    description: str                   # What it does
    use_cases: List[str]               # When to use it
    max_tokens: int                    # Max output tokens
    supports_tools: bool              # Function calling support
    supports_streaming: bool          # Stream response
    supports_vision: bool             # Image input
    context_window: int               # Input context size
    best_for: str                     # One-line recommendation
    api_key_index: int                # Which key (0-29) optimized for
    
    def get_api_call_example(self) -> str:
        """Generate example API call code"""
        return f'''
# {self.display_name}
model = "{self.name}"
# Max tokens: {self.max_tokens}
# Context: {self.context_window:,} tokens
# Tools: {"✅" if self.supports_tools else "❌"}
# Vision: {"✅" if self.supports_vision else "❌"}
# Streaming: {"✅" if self.supports_streaming else "❌"}

response = await client.post(
    "https://integrate.api.nvidia.com/v1/chat/completions",
    headers={{"Authorization": "Bearer $NVIDIA_API_KEY"}},
    json={{
        "model": "{self.name}",
        "messages": [{{"role": "user", "content": "Your prompt here"}}],
        "max_tokens": {min(self.max_tokens, 4096)},
        "temperature": 0.7
    }}
)
'''


# ============================================================
# 📚 COMPLETE NVIDIA MODEL CATALOG (29+ Models)
# ============================================================

NVIDIA_MODEL_CATALOG: Dict[str, NvidiaModel] = {

    # ==========================================
    # ⭐ ULTRA POWERFUL MODELS (Best Performance)
    # ==========================================
    
    "nvidia/nemotron-3-ultra-550b-a55b": NvidiaModel(
        name="nvidia/nemotron-3-ultra-550b-a55b",
        display_name="⭐ Nemotron Ultra 550B",
        category=ModelCategory.ULTRA_POWERFUL,
        description="NVIDIA's MOST POWERFUL model! 550 billion parameters with MoE architecture. Only 55B active params per token - blazing fast AND super smart!",
        use_cases=[
            "Complex multi-step reasoning",
            "Advanced code generation & debugging",
            "Mathematical proofs & analysis",
            "Long-form content creation",
            "Strategic planning & analysis",
            "Scientific research assistance"
        ],
        max_tokens=16384,
        supports_tools=True,
        supports_streaming=True,
        supports_vision=False,
        context_window=131072,
        best_for="🏆 BEST OVERALL - Use for everything important!",
        api_key_index=4  # Key 5: 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
    ),
    
    # ==========================================
    # 🧠 REASONING MODELS (Complex Logic)
    # ==========================================
    
    "nvidia/nemotron-3-super-120b-a12b": NvidiaModel(
        name="nvidia/nemotron-3-super-120b-a12b",
        display_name="🧠 Nemotron Super 120B",
        category=ModelCategory.REASONING,
        description="Heavy-duty reasoning beast! 120B params with efficient MoE. Perfect for complex logical problems.",
        use_cases=[
            "Complex logical reasoning",
            "Multi-step problem solving",
            "Code architecture design",
            "Data analysis & insights",
            "Technical documentation",
            "System design discussions"
        ],
        max_tokens=16384,
        supports_tools=False,
        supports_streaming=True,
        supports_vision=False,
        context_window=131072,
        best_for="Heavy reasoning tasks when you need deep analysis",
        api_key_index=1  # Key 2
    ),
    
    "deepseek-ai/deepseek-v4-pro": NvidiaModel(
        name="deepseek-ai/deepseek-v4-pro",
        display_name="🔬 DeepSeek V4 Pro",
        category=ModelCategory.REASONING,
        description="DeepSeek's latest pro model with advanced reasoning capabilities. Excellent for STEM tasks.",
        use_cases=[
            "Advanced mathematics",
            "Scientific calculations",
            "Research paper analysis",
            "Algorithm design",
            "Competitive programming",
            "Physics/Chemistry problems"
        ],
        max_tokens=16384,
        supports_tools=False,
        supports_streaming=False,
        supports_vision=False,
        context_window=65536,
        best_for="STEM & scientific reasoning tasks",
        api_key_index=21  # Key 22
    ),
    
    "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning": NvidiaModel(
        name="nvidia/nemotron-3-nano-omni-30b-a3b-reasoning",
        display_name="🤖 Omni Reasoning 30B",
        category=ModelCategory.REASONING,
        description="Multimodal reasoning model - understands text AND images with strong logic!",
        use_cases=[
            "Visual reasoning tasks",
            "Chart/graph analysis",
            "Document understanding",
            "Multi-modal problem solving",
            "Image-based Q&A",
            "Diagram interpretation"
        ],
        max_tokens=65536,
        supports_tools=False,
        supports_streaming=False,
        supports_vision=True,
        context_window=131072,
        best_for="When you need to reason about images",
        api_key_index=22  # Key 23
    ),
    
    "nvidia/llama-3.3-nemotron-super-49b-v1": NvidiaModel(
        name="nvidia/llama-3.3-nemotron-super-49b-v1",
        display_name="🏆 Nemotron Super 49B v1",
        category=ModelCategory.REASONING,
        description="NVIDIA's tuned Llama 3.3 - optimized for instruction following and reasoning.",
        use_cases=[
            "Instruction following",
            "Structured output generation",
            "Reasoning tasks",
            "Chat applications",
            "Content moderation",
            "Format conversion"
        ],
        max_tokens=4096,
        supports_tools=False,
        supports_streaming=False,
        supports_vision=False,
        context_window=131072,
        best_for="Reliable reasoning with Llama foundation",
        api_key_index=22  # Key 23
    ),
    
    "nvidia/llama-3.3-nemotron-super-49b-v1.5": NvidiaModel(
        name="nvidia/llama-3.3-nemotron-super-49b-v1.5",
        display_name="🏆 Nemotron Super 49B v1.5",
        category=ModelCategory.REASONING,
        description="Improved version of Nemotron Super 49B with better performance and larger output.",
        use_cases=[
            "Extended conversations",
            "Long-form reasoning",
            "Detailed explanations",
            "Document generation",
            "Complex instructions",
            "Analysis reports"
        ],
        max_tokens=65536,
        supports_tools=False,
        supports_streaming=False,
        supports_vision=False,
        context_window=131072,
        best_for="When you need longer outputs from reasoning model",
        api_key_index=23  # Key 24
    ),
    
    # ==========================================
    # ⚡ FAST CHAT MODELS (Quick Responses)
    # ==========================================
    
    "meta/llama-3.3-70b-instruct": NvidiaModel(
        name="meta/llama-3.3-70b-instruct",
        display_name="⚡ Llama 3.3 70B",
        category=ModelCategory.FAST_CHAT,
        description="Meta's Llama 3.3 - Perfect balance of speed and intelligence! Great for general chat.",
        use_cases=[
            "General conversation",
            "Quick Q&A",
            "Content summarization",
            "Creative writing",
            "Translation tasks",
            "Casual chat"
        ],
        max_tokens=4096,
        supports_tools=True,
        supports_streaming=True,
        supports_vision=False,
        context_window=131072,
        best_for="Daily driver - fast, smart, reliable!",
        api_key_index=0  # Key 1
    ),
    
    "meta/llama-3.1-8b-instruct": NvidiaModel(
        name="meta/llama-3.1-8b-instruct",
        display_name="🚀 Llama 3.1 8B",
        category=ModelCategory.FAST_CHAT,
        description="Super fast lightweight model! Instant responses for simple tasks.",
        use_cases=[
            "Ultra-fast responses",
            "Simple Q&A",
            "Classification tasks",
            "Short form generation",
            "Real-time chat",
            "High-volume requests"
        ],
        max_tokens=1024,
        supports_tools=True,
        supports_streaming=True,
        supports_vision=False,
        context_window=131072,
        best_for="Speed demon - when you need instant replies",
        api_key_index=6  # Key 7
    ),
    
    "stepfun-ai/step-3.5-flash": NvidiaModel(
        name="stepfun-ai/step-3.5-flash",
        display_name="⚡ Step 3.5 Flash",
        category=ModelCategory.FAST_CHAT,
        description="Step AI's flash model - built for BLAZING fast inference!",
        use_cases=[
            "Real-time responses",
            "Quick completions",
            "Auto-complete suggestions",
            "Instant translations",
            "Fast categorization",
            "Low-latency apps"
        ],
        max_tokens=16384,
        supports_tools=False,
        supports_streaming=False,
        supports_vision=False,
        context_window=131072,
        best_for="Ultra-low latency requirements",
        api_key_index=17  # Key 18
    ),
    
    "mistralai/ministral-14b-instruct-2512": NvidiaModel(
        name="mistralai/ministral-14b-instruct-2512",
        display_name="🇫🇷 MiniStral 14B",
        category=ModelCategory.FAST_CHAT,
        description="Mistral's lightweight model - efficient and capable for edge deployment.",
        use_cases=[
            "Lightweight chat",
            "Resource-constrained env",
            "Quick tasks",
            "Simple reasoning",
            "Edge computing",
            "Mobile-friendly"
        ],
        max_tokens=2048,
        supports_tools=False,
        supports_streaming=False,
        supports_vision=False,
        context_window=131072,
        best_for="Efficient & lightweight operations",
        api_key_index=24  # Key 25
    ),
    
    # ==========================================
    # 💬 LARGE LANGUAGE MODELS (Big Context)
    # ==========================================
    
    "openai/gpt-oss-120b": NvidiaModel(
        name="openai/gpt-oss-120b",
        display_name="💬 GPT OSS 120B",
        category=ModelCategory.LARGE_LANGUAGE,
        description="Open source GPT-class model with 120B parameters. Powerful generalist!",
        use_cases=[
            "General purpose AI",
            "Long conversations",
            "Knowledge-intensive tasks",
            "Essay writing",
            "Story generation",
            "Comprehensive answers"
        ],
        max_tokens=4096,
        supports_tools=False,
        supports_streaming=False,
        supports_vision=False,
        context_window=131072,
        best_for="Open-source GPT alternative",
        api_key_index=2  # Key 3
    ),
    
    "openai/gpt-oss-20b": NvidiaModel(
        name="openai/gpt-oss-20b",
        display_name="📝 GPT OSS 20B",
        category=ModelCategory.LARGE_LANGUAGE,
        description="Smaller GPT OSS variant - faster but still very capable!",
        use_cases=[
            "Medium complexity tasks",
            "Balanced speed/intelligence",
            "Draft generation",
            "Note taking",
            "Email composition",
            "Report writing"
        ],
        max_tokens=4096,
        supports_tools=False,
        supports_streaming=False,
        supports_vision=False,
        context_window=131072,
        best_for="Smaller but capable GPT alternative",
        api_key_index=13  # Key 14
    ),
    
    "qwen/qwen3-next-80b-a3b-instruct": NvidiaModel(
        name="qwen/qwen3-next-80b-a3b-instruct",
        display_name="🌟 Qwen Next 80B",
        category=ModelCategory.LARGE_LANGUAGE,
        description="Alibaba's next-gen Qwen with MoE architecture. Excellent multilingual support!",
        use_cases=[
            "Multilingual tasks",
            "Chinese/English mixed",
            "Code generation",
            "Cultural context",
            "Asian language focus",
            "Next-gen features"
        ],
        max_tokens=4096,
        supports_tools=False,
        supports_streaming=False,
        supports_vision=False,
        context_window=131072,
        best_for="Multilingual & Chinese-optimized tasks",
        api_key_index=3  # Key 4
    ),
    
    "qwen/qwen3.5-397b-a17b": NvidiaModel(
        name="qwen/qwen3.5-397b-a17b",
        display_name="🔥 Qwen 3.5 397B",
        category=ModelCategory.LARGE_LANGUAGE,
        description="MASSIVE 397B parameter model! One of the largest available on NVIDIA NIM.",
        use_cases=[
            "Massive knowledge retrieval",
            "Encyclopedia-like answers",
            "Complex narratives",
            "World knowledge",
            "Historical analysis",
            "Comprehensive research"
        ],
        max_tokens=16384,
        supports_tools=False,
        supports_streaming=False,
        supports_vision=False,
        context_window=131072,
        best_for="When you need MAXIMUM knowledge",
        api_key_index=9  # Key 10
    ),
    
    "qwen/qwen3.5-122b-a10b": NvidiaModel(
        name="qwen/qwen3.5-122b-a10b",
        display_name="📊 Qwen 3.5 122B",
        category=ModelCategory.LARGE_LANGUAGE,
        description="Balanced large model from Qwen - great for production workloads.",
        use_cases=[
            "Production chatbots",
            "Balanced performance",
            "Cost-effective large model",
            "API services",
            "Batch processing",
            "Reliable outputs"
        ],
        max_tokens=16384,
        supports_tools=False,
        supports_streaming=False,
        supports_vision=False,
        context_window=131072,
        best_for="Balanced large model for production",
        api_key_index=11  # Key 12
    ),
    
    # ==========================================
    # 👁️ VISION MODELS (Image Understanding)
    # ==========================================
    
    "nvidia/llama-3.1-nemotron-nano-vl-8b-v1": NvidiaModel(
        name="nvidia/llama-3.1-nemotron-nano-vl-8b-v1",
        display_name="👁️ Nemotron Nano VL 8B",
        category=ModelCategory.VISION,
        description="Vision-Language model that can SEE images and TALK about them!",
        use_cases=[
            "Image description",
            "Screenshot analysis",
            "Meme understanding",
            "Photo Q&A",
            "Visual content mod",
            "OCR + understanding"
        ],
        max_tokens=1024,
        supports_tools=False,
        supports_streaming=False,
        supports_vision=True,
        context_window=131072,
        best_for="Basic image understanding tasks",
        api_key_index=14  # Key 15
    ),
    
    "nvidia/nemotron-nano-12b-v2-vl": NvidiaModel(
        name="nvidia/nemotron-nano-12b-v2-vl",
        display_name="👁️ Nemotron Nano VL 12B v2",
        category=ModelCategory.VISION,
        description="Improved vision model with better image comprehension!",
        use_cases=[
            "Advanced image analysis",
            "Medical imaging",
            "Technical diagrams",
            "Artwork description",
            "Visual search",
            "Image captioning"
        ],
        max_tokens=4096,
        supports_tools=False,
        supports_streaming=False,
        supports_vision=True,
        context_window=131072,
        best_for="Better image understanding than 8B VL",
        api_key_index=29  # Key 30
    ),
    
    # ==========================================
    # 🎭 SPECIALTY MODELS (Unique Capabilities)
    # ==========================================
    
    "meta/llama-4-maverick-17b-128e-instruct": NvidiaModel(
        name="meta/llama-4-maverick-17b-128e-instruct",
        display_name="🤠 Llama 4 Maverick",
        category=ModelCategory.SPECIALTY,
        description="Llama 4 with unique personality! 128 expert MoE architecture.",
        use_cases=[
            "Creative writing",
            "Roleplay characters",
            "Unique perspectives",
            "Entertainment",
            "Storytelling",
            "Personality-driven tasks"
        ],
        max_tokens=512,
        supports_tools=False,
        supports_streaming=False,
        supports_vision=False,
        context_window=131072,
        best_for="Creative & personality-driven content",
        api_key_index=7  # Key 8
    ),
    
    "moonshotai/kimi-k2.6": NvidiaModel(
        name="moonshotai/kimi-k2.6",
        display_name="🌙 Kimi K2.6",
        category=ModelCategory.SPECIALTY,
        description="Moonshot's long-context specialist! Great for reading long documents.",
        use_cases=[
            "Long document analysis",
            "Book summarization",
            "Codebase understanding",
            "Legal document review",
            "Research paper reading",
            "Extended context"
        ],
        max_tokens=16384,
        supports_tools=False,
        supports_streaming=True,
        supports_vision=False,
        context_window=200000,  # 200K context!
        best_for="LONG documents - 200K context window!",
        api_key_index=15  # Key 16
    ),
    
    "z-ai/glm-5.1": NvidiaModel(
        name="z-ai/glm-5.1",
        display_name="🇨🇳 GLM 5.1",
        category=ModelCategory.SPECIALTY,
        description="Z-AI's GLM model - optimized for Chinese language understanding!",
        use_cases=[
            "Chinese language tasks",
            "Hindi translation",
            "Asian languages",
            "Cultural nuance",
            "Regional content",
            "Localization"
        ],
        max_tokens=16384,
        supports_tools=False,
        supports_streaming=True,
        supports_vision=False,
        context_window=131072,
        best_for="Chinese/Hindi optimized tasks",
        api_key_index=5  # Key 6
    ),
    
    "google/gemma-3n-e4b-it": NvidiaModel(
        name="google/gemma-3n-e4b-it",
        display_name="💎 Gemma 3N",
        category=ModelCategory.EFFICIENT,
        description="Google's ultra-efficient model! Tiny but mighty - only 4B parameters!",
        use_cases=[
            "Lightweight tasks",
            "Edge deployment",
            "Quick classifications",
            "Simple patterns",
            "Low-resource needs",
            "Batch processing"
        ],
        max_tokens=512,
        supports_tools=False,
        supports_streaming=False,
        supports_vision=False,
        context_window=32768,
        best_for="Ultra-efficient tiny model",
        api_key_index=26  # Key 27
    ),
    
    "minimaxai/minimax-m2.7": NvidiaModel(
        name="minimaxai/minimax-m2.7",
        display_name="🎯 MiniMax M2.7",
        category=ModelCategory.SPECIALTY,
        description="MiniMax's targeted model - excels at specific focused tasks!",
        use_cases=[
            "Targeted generation",
            "Focused Q&A",
            "Specific domains",
            "Structured output",
            "Format following",
            "Precise tasks"
        ],
        max_tokens=8192,
        supports_tools=False,
        supports_streaming=False,
        supports_vision=False,
        context_window=131072,
        best_for="Focused, targeted tasks",
        api_key_index=8  # Key 9
    ),
    
    "nvidia/nemotron-3-nano-30b-a3b": NvidiaModel(
        name="nvidia/nemotron-3-nano-30b-a3b",
        display_name="🔹 Nemotron Nano 30B",
        category=ModelCategory.SPECIALTY,
        description="Compact yet powerful Nemotron variant - great balance of size and capability!",
        use_cases=[
            "Balanced performance",
            "Cost-effective",
            "General tasks",
            "Reliable output",
            "Production ready",
            "Versatile use"
        ],
        max_tokens=16384,
        supports_tools=False,
        supports_streaming=True,
        supports_vision=False,
        context_window=131072,
        best_for="Good all-rounder with streaming",
        api_key_index=16  # Key 17
    ),
    
    # ==========================================
    # 🇫🇷 MISTRAL MODELS (French Excellence)
    # ==========================================
    
    "mistralai/mistral-small-4-119b-2603": NvidiaModel(
        name="mistralai/mistral-small-4-119b-2603",
        display_name="🇫🇷 Mistral Small 4",
        category=ModelCategory.LARGE_LANGUAGE,
        description="Mistral's efficient 119B model - great performance-to-cost ratio!",
        use_cases=[
            "Efficient large model",
            "Production workloads",
            "Cost-effective scaling",
            "Reliable performance",
            "Enterprise ready",
            "API services"
        ],
        max_tokens=16384,
        supports_tools=False,
        supports_streaming=True,
        supports_vision=False,
        context_window=131072,
        best_for="Efficient Mistral for production",
        api_key_index=19  # Key 20
    ),
    
    "mistralai/mistral-medium-3.5-128b": NvidiaModel(
        name="mistralai/mistral-medium-3.5-128b",
        display_name="🇫🇷 Mistral Medium 3.5",
        category=ModelCategory.LARGE_LANGUAGE,
        description="Mistral's heavy-duty 128B model - maximum Mistral power!",
        use_cases=[
            "Heavy-duty tasks",
            "Maximum quality",
            "Complex generation",
            "Premium experiences",
            "Important outputs",
            "Critical applications"
        ],
        max_tokens=16384,
        supports_tools=False,
        supports_streaming=True,
        supports_vision=False,
        context_window=131072,
        best_for="Maximum Mistral power",
        api_key_index=28  # Key 29
    ),
}


# ============================================================
# 📊 EMBEDDING MODELS (Vector Search / Memory)
# ============================================================

EMBEDDING_MODELS_CATALOG: Dict[str, NvidiaModel] = {
    
    "nvidia/nv-embedqa-e5-v5": NvidiaModel(
        name="nvidia/nv-embedqa-e5-v5",
        display_name="🔍 NV-EmbedQA E5 v5",
        category=ModelCategory.EMBEDDING,
        description="Best embedding model for Q&A and semantic search! Based on E5 architecture.",
        use_cases=[
            "Semantic search",
            "Q&A retrieval",
            "Document similarity",
            "Memory systems",
            "RAG pipelines",
            "Vector databases"
        ],
        max_tokens=512,
        supports_tools=False,
        supports_streaming=False,
        supports_vision=False,
        context_window=512,
        best_for="Best overall embedding model",
        api_key_index=12  # Key 13
    ),
    
    "nvidia/nv-embed-v1": NvidiaModel(
        name="nvidia/nv-embed-v1",
        display_name="📊 NV-Embed v1",
        category=ModelCategory.EMBEDDING,
        description="NVIDIA's foundational embedding model - reliable and versatile.",
        use_cases=[
            "General embeddings",
            "Text vectorization",
            "Clustering",
            "Classification support",
            "Similarity matching",
            "Feature extraction"
        ],
        max_tokens=512,
        supports_tools=False,
        supports_streaming=False,
        supports_vision=False,
        context_window=512,
        best_for="General-purpose embeddings",
        api_key_index=25  # Key 26
    ),
    
    "nvidia/llama-nemotron-embed-vl-1b-v2": NvidiaModel(
        name="nvidia/llama-nemotron-embed-vl-1b-v2",
        display_name="👁️ Nemotron Embed VL",
        category=ModelCategory.EMBEDDING,
        description="Vision-Language embedding model - can embed BOTH text AND images!",
        use_cases=[
            "Multi-modal search",
            "Image-text similarity",
            "Visual retrieval",
            "Cross-modal search",
            "Image clustering",
            "Mixed content indexing"
        ],
        max_tokens=512,
        supports_tools=False,
        supports_streaming=False,
        supports_vision=True,
        context_window=512,
        best_for="When you need image + text embeddings",
        api_key_index=18  # Key 19
    ),
    
    "nvidia/llama-nemotron-embed-1b-v2": NvidiaModel(
        name="nvidia/llama-nemotron-embed-1b-v2",
        display_name="📝 Nemotron Embed 1B",
        category=ModelCategory.EMBEDDING,
        description="Lightweight text-only embedding model - fast and efficient!",
        use_cases=[
            "Fast embeddings",
            "Lightweight search",
            "Real-time vectorization",
            "High-volume processing",
            "Quick similarity",
            "Cache-friendly"
        ],
        max_tokens=512,
        supports_tools=False,
        supports_streaming=False,
        supports_vision=False,
        context_window=512,
        best_for="Fast, lightweight text embeddings",
        api_key_index=27  # Key 28
    ),
}


# ============================================================
# 🎯 MODEL RECOMMENDATION ENGINE
# ============================================================

def get_model_by_use_case(task_type: str) -> List[NvidiaModel]:
    """
    Get recommended models for specific task types.
    
    Args:
        task_type: Type of task (see options below)
        
    Returns:
        List of recommended models (best first)
    """
    recommendations = {
        "chat": [
            NVIDIA_MODEL_CATALOG["meta/llama-3.3-70b-instruct"],
            NVIDIA_MODEL_CATALOG["nvidia/nemotron-3-ultra-550b-a55b"],
            NVIDIA_MODEL_CATALOG["nvidia/nemotron-3-nano-30b-a3b"],
        ],
        "reasoning": [
            NVIDIA_MODEL_CATALOG["nvidia/nemotron-3-ultra-550b-a55b"],
            NVIDIA_MODEL_CATALOG["nvidia/nemotron-3-super-120b-a12b"],
            NVIDIA_MODEL_CATALOG["deepseek-ai/deepseek-v4-pro"],
        ],
        "fast": [
            NVIDIA_MODEL_CATALOG["meta/llama-3.1-8b-instruct"],
            NVIDIA_MODEL_CATALOG["stepfun-ai/step-3.5-flash"],
            NVIDIA_MODEL_CATALOG["mistralai/ministral-14b-instruct-2512"],
        ],
        "code": [
            NVIDIA_MODEL_CATALOG["nvidia/nemotron-3-ultra-550b-a55b"],
            NVIDIA_MODEL_CATALOG["meta/llama-3.3-70b-instruct"],
            NVIDIA_MODEL_CATALOG["qwen/qwen3-next-80b-a3b-instruct"],
        ],
        "creative": [
            NVIDIA_MODEL_CATALOG["meta/llama-4-maverick-17b-128e-instruct"],
            NVIDIA_MODEL_CATALOG["nvidia/nemotron-3-ultra-550b-a55b"],
            NVIDIA_MODEL_CATALOG["moonshotai/kimi-k2.6"],
        ],
        "vision": [
            NVIDIA_MODEL_CATALOG["nvidia/nemotron-3-nano-omni-30b-a3b-reasoning"],
            NVIDIA_MODEL_CATALOG["nvidia/nemotron-nano-12b-v2-vl"],
            NVIDIA_MODEL_CATALOG["nvidia/llama-3.1-nemotron-nano-vl-8b-v1"],
        ],
        "long_context": [
            NVIDIA_MODEL_CATALOG["moonshotai/kimi-k2.6"],  # 200K context!
            NVIDIA_MODEL_CATALOG["nvidia/nemotron-3-ultra-550b-a55b"],
            NVIDIA_MODEL_CATALOG["qwen/qwen3.5-397b-a17b"],
        ],
        "chinese": [
            NVIDIA_MODEL_CATALOG["z-ai/glm-5.1"],
            NVIDIA_MODEL_CATALOG["qwen/qwen3-next-80b-a3b-instruct"],
            NVIDIA_MODEL_CATALOG["qwen/qwen3.5-397b-a17b"],
        ],
        "embedding": [
            EMBEDDING_MODELS_CATALOG["nvidia/nv-embedqa-e5-v5"],
            EMBEDDING_MODELS_CATALOG["nvidia/nv-embed-v1"],
        ],
    }
    
    return recommendations.get(task_type, [NVIDIA_MODEL_CATALOG["nvidia/nemotron-3-ultra-550b-a55b"]])


def get_best_model() -> NvidiaModel:
    """Get the absolute best model for general use"""
    return NVIDIA_MODEL_CATALOG["nvidia/nemotron-3-ultra-550b-a55b"]


def get_fastest_model() -> NvidiaModel:
    """Get the fastest model"""
    return NVIDIA_MODEL_CATALOG["meta/llama-3.1-8b-instruct"]


def list_all_models() -> Dict[str, List[NvidiaModel]]:
    """List all models organized by category"""
    categories = {}
    
    for model in NVIDIA_MODEL_CATALOG.values():
        cat = model.category.value
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(model)
    
    return categories


def print_model_catalog():
    """Print pretty catalog of all models"""
    print("\n" + "="*70)
    print("🎮 NVIDIA NIM MODELS CATALOG - 29+ Models, 1 API KEY!")
    print("="*70)
    print("\n⚡  IMPORTANT: Ek hi API key se sab models kaam karte hain!")
    print("   Base URL: https://integrate.api.nvidia.com/v1/chat/completions")
    print("   Sirf 'model' field change karo!\n")
    
    categories = list_all_models()
    
    category_emojis = {
        "ultra": "⭐ ULTRA POWERFUL",
        "fast": "⚡ FAST CHAT",
        "reasoning": "🧠 REASONING",
        "large": "💬 LARGE LANGUAGE",
        "vision": "👁️ VISION",
        "efficient": "💎 EFFICIENT",
        "specialty": "🎭 SPECIALTY",
    }
    
    for cat, models in categories.items():
        print(f"\n{'─'*70}")
        print(f"  {category_emojis.get(cat, cat.upper())}")
        print(f"{'─'*70}")
        
        for m in sorted(models, key=lambda x: x.max_tokens, reverse=True):
            tools = "🔧" if m.supports_tools else "  "
            vision = "👁️" if m.supports_vision else "  "
            stream = "📡" if m.supports_streaming else "  "
            
            print(f"\n  📦 {m.display_name}")
            print(f"     Model: {m.name}")
            print(f"     Context: {m.context_window:,} tokens | Output: {m.max_tokens:,} tokens")
            print(f"     Features: {tools} Tools {vision} Vision {stream} Streaming")
            print(f"     ✨ Best for: {m.best_for}")
            print(f"     💡 Use cases: {', '.join(m.use_cases[:3])}...")
    
    print(f"\n{'='*70}")
    print("📊 EMBEDDING MODELS (for Vector Search/Memory)")
    print(f"{'='*70}")
    
    for model in EMBEDDING_MODELS_CATALOG.values():
        vision = "👁️" if model.supports_vision else "  "
        print(f"\n  📦 {model.display_name}")
        print(f"     Model: {model.name}")
        print(f"     Features: {vision} Multi-modal")
        print(f"     ✨ Best for: {model.best_for}")
    
    print(f"\n{'='*70}")
    print("🔑 API KEYS: You have 30 keys - auto-rotation enabled!")
    print("📖 Full details: See multi_provider.py")
    print("="*70 + "\n")


# Quick test function
async def test_nvidia_connection(api_key: str) -> Dict[str, Any]:
    """
    Test NVIDIA API connection with any model.
    
    Usage:
        result = await test_nvidia_connection("nvapi-your-key")
        print(result)
    """
    import httpx
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://integrate.api.nvidia.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "meta/llama-3.1-8b-instruct",  # Fast model for testing
                    "messages": [{"role": "user", "content": "Say 'Hello!' in one word."}],
                    "max_tokens": 10
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "success": True,
                    "message": "✅ NVIDIA API connection successful!",
                    "response": data.get("choices", [{}])[0].get("message", {}).get("content"),
                    "model_used": "meta/llama-3.1-8b-instruct"
                }
            else:
                return {
                    "success": False,
                    "message": f"❌ Error {response.status_code}",
                    "error": response.text[:200]
                }
                
    except Exception as e:
        return {
            "success": False,
            "message": f"❌ Connection failed: {str(e)}"
        }


# Run this file directly to see the catalog
if __name__ == "__main__":
    print_model_catalog()
