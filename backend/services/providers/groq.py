"""
Groq Provider - Fast cloud LLM API
"""
from groq import AsyncGroq
from typing import Optional, AsyncGenerator
import json


class GroqProvider:
    """Groq API client for fast cloud inference"""
    
    def __init__(self, api_key: str, model: str = "llama-3.3-70b-versatile"):
        self.api_key = api_key
        self.model = model
        self.client = AsyncGroq(api_key=api_key)
    
    async def check_connection(self) -> bool:
        """Check if Groq API is accessible"""
        try:
            # Simple test request
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "test"}],
                max_tokens=1
            )
            return True
        except Exception:
            return False
    
    async def list_models(self) -> list:
        """List available models"""
        return [
            "llama-3.3-70b-versatile",
            "llama-3.1-8b-instant",
            "llama-3.1-70b-versatile",
            "mixtral-8x7b-32768",
            "gemma2-9b-it",
        ]
    
    async def chat(
        self,
        messages: list,
        tools: Optional[list] = None,
        stream: bool = False
    ) -> dict:
        """Send chat completion request"""
        try:
            kwargs = {
                "model": self.model,
                "messages": messages,
                "max_tokens": 4096,
            }
            
            if tools:
                kwargs["tools"] = tools
                kwargs["tool_choice"] = "auto"
            
            response = await self.client.chat.completions.create(**kwargs)
            
            return self._format_response(response)
        except Exception as e:
            return {
                "content": f"Groq error: {str(e)}",
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
            
            if tools:
                kwargs["tools"] = tools
                kwargs["tool_choice"] = "auto"
            
            stream = await self.client.chat.completions.create(**kwargs)
            
            async for chunk in stream:
                yield self._format_stream_chunk(chunk)
        except Exception as e:
            yield {"error": str(e), "done": True}
    
    def _format_response(self, response) -> dict:
        """Format Groq response to standard format"""
        choice = response.choices[0]
        message = choice.message
        
        tool_calls = None
        if message.tool_calls:
            tool_calls = [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments
                    }
                }
                for tc in message.tool_calls
            ]
        
        return {
            "content": message.content or "",
            "tool_calls": tool_calls,
            "model": response.model,
            "done": True,
            "usage": {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
            }
        }
    
    def _format_stream_chunk(self, chunk) -> dict:
        """Format streaming chunk"""
        if not chunk.choices:
            return {"content": "", "done": False}
        
        delta = chunk.choices[0].delta
        
        tool_calls = None
        if hasattr(delta, 'tool_calls') and delta.tool_calls:
            tool_calls = [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function.name if tc.function else None,
                        "arguments": tc.function.arguments if tc.function else ""
                    }
                }
                for tc in delta.tool_calls
            ]
        
        return {
            "content": delta.content or "",
            "tool_calls": tool_calls,
            "done": chunk.choices[0].finish_reason is not None,
        }
    
    async def close(self):
        """Close client connection"""
        await self.client.close()
