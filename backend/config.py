"""
Jarvis Configuration - Multi-Provider AI Support
"""
import os
from typing import Optional, Literal
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings with multi-provider AI support"""
    
    # AI Provider Selection
    ai_provider: Literal["ollama", "groq", "openai", "perplexity"] = Field(default="groq")
    
    # Ollama Configuration
    ollama_base_url: str = Field(default="http://localhost:11434")
    ollama_model: str = Field(default="llama3.2")
    
    # Groq Configuration
    groq_api_key: Optional[str] = Field(default=None)
    groq_model: str = Field(default="llama-3.3-70b-versatile")
    
    # OpenAI Configuration
    openai_api_key: Optional[str] = Field(default=None)
    openai_model: str = Field(default="gpt-4o")
    
    # Perplexity Configuration
    perplexity_api_key: Optional[str] = Field(default=None)
    perplexity_model: str = Field(default="sonar-pro")

    # SerpApi Configuration (Mark-X)
    serpapi_api_key: Optional[str] = Field(default=None)
    
    # Supabase Configuration
    supabase_url: Optional[str] = Field(default=None)
    supabase_key: Optional[str] = Field(default=None)
    
    # Local Storage
    local_storage_path: str = Field(default="./data")
    
    # TTS Settings
    tts_voice: str = Field(default="en-GB-RyanNeural")
    tts_rate: str = Field(default="+5%")
    tts_pitch: str = Field(default="+0Hz")
    
    # Agent Settings
    max_agent_steps: int = Field(default=50)
    agent_timeout: int = Field(default=300)
    token_budget: int = Field(default=100000)
    max_tokens: int = Field(default=4000)
    
    # Sandbox Settings
    enable_docker_sandbox: bool = Field(default=False)
    docker_memory_limit: str = Field(default="512m")
    docker_cpu_limit: int = Field(default=1)
    sandbox_timeout: int = Field(default=60)
    
    # Server Settings
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8000)
    debug: bool = Field(default=True)
    cors_origins: str = Field(default="http://localhost:5173,http://localhost:3000")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"
    
    def get_cors_origins_list(self) -> list:
        """Parse CORS origins string to list"""
        return [origin.strip() for origin in self.cors_origins.split(",")]
    
    def get_active_provider_config(self) -> dict:
        """Get configuration for the active AI provider"""
        if self.ai_provider == "ollama":
            return {
                "provider": "ollama",
                "base_url": self.ollama_base_url,
                "model": self.ollama_model,
            }
        elif self.ai_provider == "groq":
            return {
                "provider": "groq",
                "api_key": self.groq_api_key,
                "model": self.groq_model,
            }
        elif self.ai_provider == "openai":
            return {
                "provider": "openai",
                "api_key": self.openai_api_key,
                "model": self.openai_model,
            }
        else:  # perplexity
            return {
                "provider": "perplexity",
                "api_key": self.perplexity_api_key,
                "model": self.perplexity_model,
            }


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get the global settings instance"""
    return settings
