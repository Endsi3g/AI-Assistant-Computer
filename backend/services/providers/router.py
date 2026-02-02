"""
AI Router - Smart routing between providers with fallback
"""
from typing import Optional, AsyncGenerator, Union
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from .ollama import OllamaProvider
from .groq import GroqProvider
from .openai_provider import OpenAIProvider
from .perplexity import PerplexityProvider


class AIRouter:
    """
    Smart AI router with multi-provider support and fallback.
    Automatically selects the best available provider.
    """
    
    def __init__(
        self,
        primary_provider: str = "groq",
        ollama_url: str = "http://localhost:11434",
        ollama_model: str = "llama3.2",
        groq_api_key: Optional[str] = None,
        groq_model: str = "llama-3.3-70b-versatile",
        openai_api_key: Optional[str] = None,
        openai_model: str = "gpt-4o",
        perplexity_api_key: Optional[str] = None,
        perplexity_model: str = "sonar-pro",
    ):
        self.primary_provider = primary_provider
        self.providers = {}
        self.active_provider = None
        
        # Initialize providers
        self.providers["ollama"] = OllamaProvider(ollama_url, ollama_model)
        
        if groq_api_key:
            self.providers["groq"] = GroqProvider(groq_api_key, groq_model)
        
        if openai_api_key:
            self.providers["openai"] = OpenAIProvider(openai_api_key, openai_model)
        
        if perplexity_api_key:
            self.providers["perplexity"] = PerplexityProvider(perplexity_api_key, perplexity_model)
    
    async def initialize(self) -> str:
        """Initialize router and find best available provider"""
        # Try primary provider first
        if self.primary_provider in self.providers:
            provider = self.providers[self.primary_provider]
            if await provider.check_connection():
                self.active_provider = self.primary_provider
                return f"[OK] Using {self.primary_provider}"
        
        # Fallback chain: groq -> perplexity -> openai -> ollama
        fallback_order = ["groq", "perplexity", "openai", "ollama"]
        for provider_name in fallback_order:
            if provider_name in self.providers and provider_name != self.primary_provider:
                provider = self.providers[provider_name]
                if await provider.check_connection():
                    self.active_provider = provider_name
                    return f"[WARN] Fallback to {provider_name}"
        
        return "[WARN] No AI provider available"
    
    def get_provider(self) -> Union[OllamaProvider, GroqProvider, OpenAIProvider, PerplexityProvider, None]:
        """Get the active provider instance"""
        if self.active_provider:
            return self.providers.get(self.active_provider)
        return None
    
    def set_provider(self, provider_name: str, model: Optional[str] = None) -> bool:
        """Manually set the active provider"""
        if provider_name in self.providers:
            self.active_provider = provider_name
            if model:
                self.providers[provider_name].model = model
            return True
        return False
    
    async def chat(
        self,
        messages: list,
        tools: Optional[list] = None,
        stream: bool = False
    ) -> dict:
        """Send chat request to active provider"""
        provider = self.get_provider()
        if not provider:
            return {
                "content": "No AI provider available. Please check your configuration.",
                "tool_calls": None,
                "error": True
            }
        
        return await provider.chat(messages, tools, stream)
    
    async def chat_stream(
        self,
        messages: list,
        tools: Optional[list] = None
    ) -> AsyncGenerator[dict, None]:
        """Stream chat from active provider"""
        provider = self.get_provider()
        if not provider:
            yield {
                "content": "No AI provider available.",
                "done": True,
                "error": True
            }
            return
        
        async for chunk in provider.chat_stream(messages, tools):
            yield chunk
    
    async def list_available_models(self) -> dict:
        """List models from all providers"""
        result = {}
        for name, provider in self.providers.items():
            try:
                models = await provider.list_models()
                result[name] = models
            except Exception:
                result[name] = []
        return result
    
    def get_status(self) -> dict:
        """Get router status"""
        return {
            "active_provider": self.active_provider,
            "active_model": self.providers[self.active_provider].model if self.active_provider else None,
            "available_providers": list(self.providers.keys()),
        }
    
    async def close(self):
        """Close all provider connections"""
        for provider in self.providers.values():
            await provider.close()


# Global router instance
_router: Optional[AIRouter] = None


def get_ai_router() -> Optional[AIRouter]:
    """Get the global AI router instance"""
    return _router


async def initialize_ai_router(
    primary_provider: str = "groq",
    ollama_url: str = "http://localhost:11434",
    ollama_model: str = "llama3.2",
    groq_api_key: Optional[str] = None,
    groq_model: str = "llama-3.3-70b-versatile",
    openai_api_key: Optional[str] = None,
    openai_model: str = "gpt-4o",
    perplexity_api_key: Optional[str] = None,
    perplexity_model: str = "sonar-pro",
) -> AIRouter:
    """Initialize the global AI router"""
    global _router
    _router = AIRouter(
        primary_provider=primary_provider,
        ollama_url=ollama_url,
        ollama_model=ollama_model,
        groq_api_key=groq_api_key,
        groq_model=groq_model,
        openai_api_key=openai_api_key,
        openai_model=openai_model,
        perplexity_api_key=perplexity_api_key,
        perplexity_model=perplexity_model,
    )
    status = await _router.initialize()
    print(status)
    return _router
