"""
Groq API Client with MULTI-MODEL Support & Smart Task Routing
Different models for different tasks - Making Ophelia UNIQUE!
"""
import asyncio
import logging
from typing import AsyncGenerator, Optional, List, Dict, Any
from enum import Enum
from groq import Groq, AsyncGroq
from config.settings import config

logger = logging.getLogger("GroqClient")


class TaskType(Enum):
    """Types of tasks for model selection"""
    CHAT = "chat"                    # Normal conversation - Fun & engaging
    COMMAND = "command"              # Execute actions - Fast & accurate
    REASONING = "reasoning"          # Complex logic - Smart thinking
    CREATIVE = "creative"            # Stories, jokes, roleplay - Imaginative
    ANALYSIS = "analysis"            # Data, code, technical - Precise


# 🎯 MODEL CONFIGURATION - Each task gets the BEST model!
MODELS = {
    # 💬 Chat & Conversation - FUN & NATURAL
    TaskType.CHAT: {
        "primary": "llama-3.3-70b-versatile",      # Best overall conversationalist
        "fallback": "qwen/qwen3.6-27b",           # Great backup
        "temperature": 1.02,                       # Creative but coherent
        "max_tokens": 1024,                        # Good length for chat
        "description": "Fun & friendly chat"
    },
    
    # ⚡ Commands & Actions - FAST & PRECISE
    TaskType.COMMAND: {
        "primary": "llama-3.1-8b-instant",         # Lightning fast!
        "fallback": "groq/compound-mini",           # Quick backup
        "temperature": 0.3,                         # Low creativity = accurate execution
        "max_tokens": 512,                          # Short & sweet
        "description": "Quick command execution"
    },
    
    # 🧠 Complex Reasoning - SMART & DEEP
    TaskType.REASONING: {
        "primary": "qwen/qwen3.6-27b",             # Best reasoning model!
        "fallback": "llama-3.3-70b-versatile",      # Strong backup
        "temperature": 0.7,                         # Balanced
        "max_tokens": 2048,                         # Longer thoughts
        "description": "Deep thinking & analysis"
    },
    
    # 🎨 Creative & Fun - IMAGINATIVE & UNIQUE
    TaskType.CREATIVE: {
        "primary": "qwen/qwen3.6-27b",             # Great at creative writing
        "fallback": "llama-3.3-70b-versatile",
        "temperature": 1.3,                         # Very creative!
        "max_tokens": 1536,                         # Space for creativity
        "description": "Stories, jokes, roleplay"
    },
    
    # 🔬 Analysis & Technical - PRECISE & ACCURATE
    TaskType.ANALYSIS: {
        "primary": "qwen/qwen3.6-27b",             # Excellent at analysis
        "fallback": "llama-3.3-70b-versatile",
        "temperature": 0.5,                         # Focused & precise
        "max_tokens": 1536,
        "description": "Code, data, technical stuff"
    }
}


class GroqClient:
    """
    ENHANCED Groq client with:
    ✅ Multi-model support (different models for different tasks)
    ✅ Smart task detection & routing
    ✅ Multi-key fallback
    ✅ Streaming support
    """
    
    def __init__(self, api_keys: List[str]):
        self.api_keys = api_keys
        self.current_key_index = 0
        self.clients: List[AsyncGroq] = []
        
        # Initialize async clients for all keys
        for key in api_keys:
            try:
                client = AsyncGroq(api_key=key)
                self.clients.append(client)
            except Exception as e:
                logger.warning(f"Failed to initialize client for key {key[:10]}...: {e}")
        
        if not self.clients:
            raise RuntimeError("No valid Groq API keys provided!")
        
        logger.info(f"🔑 Initialized {len(self.clients)} Groq API client(s)")
        logger.info(f"🤖 Multi-model system ready:")
        for task_type, cfg in MODELS.items():
            logger.info(f"   • {task_type.value}: {cfg['primary']} ({cfg['description']})")
    
    def _get_client(self) -> tuple[AsyncGroq, int]:
        """Get current client with fallback support"""
        if not self.clients:
            raise RuntimeError("No available API clients!")
        
        client = self.clients[self.current_key_index]
        return client, self.current_key_index
    
    def _rotate_key(self):
        """Rotate to next available API key"""
        self.current_key_index = (self.current_key_index + 1) % len(self.clients)
        logger.info(f"🔄 Rotated to API key #{self.current_key_index + 1}")
    
    def detect_task_type(self, message: str) -> TaskType:
        """
        Automatically detect what TYPE of task this is.
        This makes Ophelia SMART - she knows which model to use!
        """
        msg_lower = message.lower().strip()
        
        # Command patterns - ACTION words
        command_words = ['kick', 'ban', 'timeout', 'mute', 'clear', 'delete', 
                        'create', 'set status', 'nickname', 'send', 'announce',
                        'embed', 'react', 'role banao', 'channel banao']
        if any(word in msg_lower for word in command_words):
            return TaskType.COMMAND
        
        # Creative patterns - FUN/IMAGINATION words
        creative_words = ['story', 'joke', 'roast', 'meme', 'rap', 'poem', 
                         'shayari', 'imagine', 'roleplay', 'act like', 
                         'pretend', 'funny', 'entertain', 'dance', 'sing']
        if any(word in msg_lower for word in creative_words):
            return TaskType.CREATIVE
        
        # Analysis patterns - TECHNICAL words
        analysis_words = ['code', 'debug', 'explain', 'analyze', 'how does', 
                         'what is the difference', 'compare', 'calculate',
                         'math', 'programming', 'api', 'function', 'algorithm']
        if any(word in msg_lower for word in analysis_words):
            return TaskType.ANALYSIS
        
        # Reasoning patterns - COMPLEX THINKING
        reasoning_words = ['why', 'how come', 'what if', 'should i', 'would you',
                          'opinion', 'think about', 'consider', 'pros and cons',
                          'debate', 'argue', 'philosophy', 'meaning of life']
        if any(word in msg_lower for word in reasoning_words):
            return TaskType.REASONING
        
        # Default to CHAT for normal conversation
        return TaskType.CHAT
    
    async def chat_completion_stream(
        self,
        messages: List[Dict[str, str]],
        model: str = None,
        temperature: float = None,
        max_tokens: int = None,
        top_p: float = 1.0,
        max_retries: int = 3,
        task_type: TaskType = None
    ) -> AsyncGenerator[str, None]:
        """
        Stream chat completion with SMART MODEL SELECTION!
        Automatically picks best model based on task type.
        """
        # Auto-detect task type if not provided
        if task_type is None and messages:
            last_user_msg = ""
            for msg in reversed(messages):
                if msg.get("role") == "user":
                    last_user_msg = msg.get("content", "")
                    break
            task_type = self.detect_task_type(last_user_msg)
        
        # Get model config for this task type
        task_config = MODELS.get(task_type or TaskType.CHAT, MODELS[TaskType.CHAT])
        
        # Use provided values or fall back to task defaults
        final_model = model or task_config["primary"]
        final_temp = temperature if temperature is not None else task_config["temperature"]
        final_max_tokens = max_tokens if max_tokens is not None else task_config["max_tokens"]
        
        logger.info(f"🎯 Task: {task_type.value if task_type else 'unknown'} | Model: {final_model} | Temp: {final_temp}")
        
        last_error = None
        
        for attempt in range(max_retries):
            try:
                client, key_idx = self._get_client()
                
                stream = await client.chat.completions.create(
                    model=final_model,
                    messages=messages,
                    temperature=final_temp,
                    max_completion_tokens=final_max_tokens,
                    top_p=top_p,
                    stream=True
                )
                
                async for chunk in stream:
                    content = chunk.choices[0].delta.content
                    if content:
                        yield content
                
                return
                
            except Exception as e:
                last_error = e
                logger.warning(f"Key #{self.current_key_index + 1} failed: {e}")
                
                # Try fallback model on first retry
                if attempt == 0 and "fallback" in task_config:
                    final_model = task_config["fallback"]
                    logger.info(f"🔄 Trying fallback model: {final_model}")
                
                self._rotate_key()
                await asyncio.sleep(0.5 * (attempt + 1))
        
        logger.error(f"All {max_retries} attempts failed. Last error: {last_error}")
        raise RuntimeError(f"Groq API request failed after {max_retries} attempts: {last_error}")
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: str = None,
        temperature: float = None,
        max_tokens: int = None,
        top_p: float = 1.0,
        max_retries: int = 3,
        task_type: TaskType = None
    ) -> str:
        """Non-streaming completion with smart model selection"""
        if task_type is None and messages:
            last_user_msg = ""
            for msg in reversed(messages):
                if msg.get("role") == "user":
                    last_user_msg = msg.get("content", "")
                    break
            task_type = self.detect_task_type(last_user_msg)
        
        task_config = MODELS.get(task_type or TaskType.CHAT, MODELS[TaskType.CHAT])
        
        final_model = model or task_config["primary"]
        final_temp = temperature if temperature is not None else task_config["temperature"]
        final_max_tokens = max_tokens if max_tokens is not None else task_config["max_tokens"]
        
        last_error = None
        
        for attempt in range(max_retries):
            try:
                client, key_idx = self._get_client()
                
                response = await client.chat.completions.create(
                    model=final_model,
                    messages=messages,
                    temperature=final_temp,
                    max_completion_tokens=final_max_tokens,
                    top_p=top_p,
                    stream=False
                )
                
                return response.choices[0].message.content or ""
                
            except Exception as e:
                last_error = e
                logger.warning(f"Key #{self.current_key_index + 1} failed: {e}")
                
                if attempt == 0 and "fallback" in task_config:
                    final_model = task_config["fallback"]
                
                self._rotate_key()
                await asyncio.sleep(0.5 * (attempt + 1))
        
        raise RuntimeError(f"Groq API request failed after {max_retries} attempts: {last_error}")
    
    async def test_connection(self) -> tuple[bool, str]:
        """Test if the API connection works"""
        try:
            client, _ = self._get_client()
            response = await client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": "Hi"}],
                max_completion_tokens=5
            )
            return True, f"Connected! Multi-model ready! 🚀"
        except Exception as e:
            return False, f"Connection failed: {str(e)}"
    
    @property
    def available_keys_count(self) -> int:
        return len(self.clients)
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get info about current model configuration"""
        return {
            "models": {k.value: v for k, v in MODELS.items()},
            "total_models": len(set(v["primary"] for v in MODELS.values())),
            "smart_routing": True
        }


# Global instance
groq_client: Optional[GroqClient] = None


def init_groq_client(api_keys: List[str]) -> GroqClient:
    """Initialize global Groq client with multi-model support"""
    global groq_client
    groq_client = GroqClient(api_keys)
    return groq_client


def get_groq_client() -> GroqClient:
    """Get global Groq client instance"""
    if groq_client is None:
        raise RuntimeError("Groq client not initialized! Call init_groq_client() first.")
    return groq_client
