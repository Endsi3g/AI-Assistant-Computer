"""
Ollama Provider - Self-hosted LLM support
"""
import httpx
from typing import Optional, AsyncGenerator
import json


class OllamaProvider:
    """Ollama API client for self-hosted LLMs"""
    
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama3.2"):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.client = httpx.AsyncClient(timeout=10.0)
    
    async def check_connection(self) -> bool:
        """Check if Ollama is running"""
        try:
            response = await self.client.get(f"{self.base_url}/api/tags")
            return response.status_code == 200
        except Exception:
            return False
    
    async def list_models(self) -> list:
        """List available models"""
        try:
            response = await self.client.get(f"{self.base_url}/api/tags")
            if response.status_code == 200:
                data = response.json()
                return [m["name"] for m in data.get("models", [])]
            return []
        except Exception:
            return []
    
    async def chat(
        self,
        messages: list,
        tools: Optional[list] = None,
        stream: bool = False
    ) -> dict:
        """Send chat completion request"""
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": stream,
        }
        
        # Add tools if supported (Ollama 0.4+)
        if tools:
            payload["tools"] = tools
        
        try:
            response = await self.client.post(
                f"{self.base_url}/api/chat",
                json=payload
            )
            
            if response.status_code == 200:
                data = response.json()
                return self._format_response(data)
            else:
                return {
                    "content": f"Ollama error: {response.status_code}",
                    "tool_calls": None,
                    "error": True
                }
        except Exception as e:
            return {
                "content": f"Ollama connection error: {str(e)}",
                "tool_calls": None,
                "error": True
            }
    
    async def chat_stream(
        self,
        messages: list,
        tools: Optional[list] = None
    ) -> AsyncGenerator[dict, None]:
        """Stream chat completion"""
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": True,
        }
        
        if tools:
            payload["tools"] = tools
        
        try:
            async with self.client.stream(
                "POST",
                f"{self.base_url}/api/chat",
                json=payload
            ) as response:
                async for line in response.aiter_lines():
                    if line:
                        try:
                            data = json.loads(line)
                            yield self._format_stream_chunk(data)
                        except json.JSONDecodeError:
                            continue
        except Exception as e:
            yield {"error": str(e), "done": True}
    
    def _format_response(self, data: dict) -> dict:
        """Format Ollama response to standard format"""
        message = data.get("message", {})
        return {
            "content": message.get("content", ""),
            "tool_calls": message.get("tool_calls"),
            "model": data.get("model", self.model),
            "done": data.get("done", True),
            "total_duration": data.get("total_duration"),
            "eval_count": data.get("eval_count", 0),
        }
    
    def _format_stream_chunk(self, data: dict) -> dict:
        """Format streaming chunk"""
        message = data.get("message", {})
        return {
            "content": message.get("content", ""),
            "tool_calls": message.get("tool_calls"),
            "done": data.get("done", False),
        }
    
    async def close(self):
        """Close client connection"""
        await self.client.aclose()
