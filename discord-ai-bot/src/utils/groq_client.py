"""
Groq API Client with Multi-Key Fallback Support
Handles streaming, retries, and automatic key rotation
"""
import asyncio
import logging
from typing import AsyncGenerator, Optional, List, Dict, Any
from groq import Groq, AsyncGroq
from config.settings import config

logger = logging.getLogger("GroqClient")


class GroqClient:
    """Enhanced Groq client with multi-key fallback and streaming support"""
    
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
    
    def _get_client(self) -> tuple[AsyncGroq, int]:
        """Get current client with fallback support"""
        if not self.clients:
            raise RuntimeError("No available API clients!")
        
        # Try current index first
        client = self.clients[self.current_key_index]
        return client, self.current_key_index
    
    def _rotate_key(self):
        """Rotate to next available API key"""
        self.current_key_index = (self.current_key_index + 1) % len(self.clients)
        logger.info(f"🔄 Rotated to API key #{self.current_key_index + 1}")
    
    async def chat_completion_stream(
        self,
        messages: List[Dict[str, str]],
        model: str = None,
        temperature: float = 1.02,
        max_tokens: int = 32768,
        top_p: float = 1.0,
        max_retries: int = 3
    ) -> AsyncGenerator[str, None]:
        """
        Stream chat completion with automatic retry on failure.
        Yields content chunks as they arrive.
        """
        model = model or config.default_model
        
        last_error = None
        
        for attempt in range(max_retries):
            try:
                client, key_idx = self._get_client()
                
                logger.debug(f"Attempting stream with key #{key_idx + 1} (attempt {attempt + 1})")
                
                stream = await client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    max_completion_tokens=max_tokens,
                    top_p=top_p,
                    stream=True
                )
                
                async for chunk in stream:
                    content = chunk.choices[0].delta.content
                    if content:
                        yield content
                
                # Success - return normally
                return
                
            except Exception as e:
                last_error = e
                logger.warning(f"Key #{self.current_key_index + 1} failed: {e}")
                
                # Rotate to next key for retry
                self._rotate_key()
                
                # Small delay before retry
                await asyncio.sleep(0.5 * (attempt + 1))
        
        # All retries exhausted
        logger.error(f"All {max_retries} attempts failed. Last error: {last_error}")
        raise RuntimeError(f"Groq API request failed after {max_retries} attempts: {last_error}")
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: str = None,
        temperature: float = 1.02,
        max_tokens: int = 32768,
        top_p: float = 1.0,
        max_retries: int = 3
    ) -> str:
        """
        Non-streaming chat completion with automatic retry.
        Returns complete response text.
        """
        model = model or config.default_model
        
        last_error = None
        
        for attempt in range(max_retries):
            try:
                client, key_idx = self._get_client()
                
                response = await client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    max_completion_tokens=max_tokens,
                    top_p=top_p,
                    stream=False
                )
                
                return response.choices[0].message.content or ""
                
            except Exception as e:
                last_error = e
                logger.warning(f"Key #{self.current_key_index + 1} failed: {e}")
                self._rotate_key()
                await asyncio.sleep(0.5 * (attempt + 1))
        
        raise RuntimeError(f"Groq API request failed after {max_retries} attempts: {last_error}")
    
    async def test_connection(self) -> tuple[bool, str]:
        """Test if the API connection works"""
        try:
            client, _ = self._get_client()
            response = await client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": "Hi"}],
                max_completion_tokens=5
            )
            return True, f"Connected! Model: {response.model}"
        except Exception as e:
            return False, f"Connection failed: {str(e)}"
    
    @property
    def available_keys_count(self) -> int:
        """Return number of available API keys"""
        return len(self.clients)


# Global Groq client instance
groq_client: Optional[GroqClient] = None


def init_groq_client(api_keys: List[str]) -> GroqClient:
    """Initialize the global Groq client"""
    global groq_client
    groq_client = GroqClient(api_keys)
    return groq_client


def get_groq_client() -> GroqClient:
    """Get the global Groq client instance"""
    if groq_client is None:
        raise RuntimeError("Groq client not initialized! Call init_groq_client() first.")
    return groq_client
