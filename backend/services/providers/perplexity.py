"""
Perplexity Provider - Search-enhanced AI with citations
Uses OpenAI-compatible API at https://api.perplexity.ai
"""
from openai import AsyncOpenAI
from typing import Optional, AsyncGenerator


class PerplexityProvider:
    """Perplexity API client for search-enhanced AI responses"""
    
    def __init__(self, api_key: str, model: str = "sonar-pro"):
        self.api_key = api_key
        self.model = model
        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url="https://api.perplexity.ai"
        )
    
    async def check_connection(self) -> bool:
        """Check if Perplexity API is accessible"""
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "test"}],
                max_tokens=1
            )
            return True
        except Exception:
            return False
    
    async def list_models(self) -> list:
        """List available Perplexity models"""
        return [
            "sonar-pro",
            "sonar",
            "sonar-reasoning-pro",
            "sonar-reasoning",
        ]
    
    async def chat(
        self,
        messages: list,
        tools: Optional[list] = None,
        stream: bool = False
    ) -> dict:
        """Send chat completion request with optional web search"""
        try:
            kwargs = {
                "model": self.model,
                "messages": messages,
                "max_tokens": 4096,
            }
            
            # Perplexity doesn't support tools in the same way
            # but has built-in search capabilities
            
            response = await self.client.chat.completions.create(**kwargs)
            
            return self._format_response(response)
        except Exception as e:
            return {
                "content": f"Perplexity error: {str(e)}",
                "tool_calls": None,
                "error": True
            }
    
    async def chat_stream(
        self,
        messages: list,
        tools: Optional[list] = None
    ) -> AsyncGenerator[dict, None]:
        """Stream chat completion"""
        try:
            kwargs = {
                "model": self.model,
                "messages": messages,
                "max_tokens": 4096,
                "stream": True,
            }
            
            stream = await self.client.chat.completions.create(**kwargs)
            
            async for chunk in stream:
                yield self._format_stream_chunk(chunk)
        except Exception as e:
            yield {"error": str(e), "done": True}
    
    def _format_response(self, response) -> dict:
        """Format Perplexity response to standard format"""
        choice = response.choices[0]
        message = choice.message
        
        # Extract citations if present (Perplexity includes these in responses)
        citations = []
        if hasattr(response, 'citations'):
            citations = response.citations
        
        return {
            "content": message.content or "",
            "tool_calls": None,  # Perplexity doesn't use tool calls
            "citations": citations,
            "model": response.model,
            "done": True,
            "usage": {
                "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                "total_tokens": response.usage.total_tokens if response.usage else 0,
            }
        }
    
    def _format_stream_chunk(self, chunk) -> dict:
        """Format streaming chunk"""
        if not chunk.choices:
            return {"content": "", "done": False}
        
        delta = chunk.choices[0].delta
        
        return {
            "content": delta.content or "",
            "tool_calls": None,
            "done": chunk.choices[0].finish_reason is not None,
        }
    
    async def close(self):
        """Close client connection"""
        await self.client.close()
