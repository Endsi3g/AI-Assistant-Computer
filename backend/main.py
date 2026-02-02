"""
JARVIS AI Assistant - Backend Server
FastAPI with WebSocket support, multi-provider AI, and ReAct agent
"""
import os
import sys
import json
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, List

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

from config import settings
from routers import chat, voice, tasks
from services.memory import MemoryService
from services.automation import AutomationService
from services.providers.router import AIRouter, initialize_ai_router
from services.react_agent import ReActAgent


# Request/Response Models
class ChatRequest(BaseModel):
    message: str
    provider: Optional[str] = None
    model: Optional[str] = None
    session_id: Optional[str] = None


class SettingsUpdate(BaseModel):
    provider: Optional[str] = None
    model: Optional[str] = None
    voice: Optional[str] = None


# Lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize and cleanup services"""
    # Initialize services
    app.state.memory = MemoryService()
    app.state.automation = AutomationService()
    
    # Initialize AI Router
    app.state.ai_router = await initialize_ai_router(
        primary_provider=settings.ai_provider,
        ollama_url=settings.ollama_base_url,
        ollama_model=settings.ollama_model,
        groq_api_key=settings.groq_api_key,
        groq_model=settings.groq_model,
        openai_api_key=settings.openai_api_key,
        openai_model=settings.openai_model,
        perplexity_api_key=settings.perplexity_api_key,
        perplexity_model=settings.perplexity_model,
    )
    
    # Initialize Scheduler (Proactive Core)
    from services.scheduler import SchedulerService
    app.state.scheduler = SchedulerService(
        automation_service=app.state.automation,
        memory_service=app.state.memory
    )
    app.state.scheduler.start()
    
    print("[INFO] Jarvis Backend initialized")
    print(f"   Provider: {app.state.ai_router.active_provider}")
    print(f"   Model: {app.state.ai_router.get_provider().model if app.state.ai_router.get_provider() else 'None'}")
    
    yield
    
    # Cleanup
    if hasattr(app.state, 'scheduler') and app.state.scheduler:
        app.state.scheduler.shutdown()
    if hasattr(app.state, 'ai_router') and app.state.ai_router:
        await app.state.ai_router.close()
    if hasattr(app.state, 'automation') and app.state.automation:
        app.state.automation.shutdown()
    
    print("[INFO] Jarvis Backend shutdown")


# Create FastAPI app
app = FastAPI(
    title="Jarvis AI Assistant",
    description="Autonomous AI assistant with multi-provider support and ReAct agent",
    version="2.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins_list(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(chat.router, prefix="/api/chat", tags=["Chat"])
app.include_router(voice.router, prefix="/api/voice", tags=["Voice"])
app.include_router(tasks.router, prefix="/api/tasks", tags=["Tasks"])


# Health check
@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    router = app.state.ai_router
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "ai_provider": router.active_provider if router else None,
        "ai_model": router.get_provider().model if router and router.get_provider() else None,
    }


# Get status
@app.get("/api/status")
async def get_status():
    """Get detailed system status"""
    router = app.state.ai_router
    return {
        "backend": "online",
        "version": "2.0.0",
        "ai": router.get_status() if router else None,
        "memory": "local" if not settings.supabase_url else "supabase",
        "features": {
            "react_agent": True,
            "multi_provider": True,
            "voice": True,
            "automation": True,
            "docker_sandbox": settings.enable_docker_sandbox,
        }
    }


# Switch provider
@app.post("/api/settings/provider")
async def switch_provider(update: SettingsUpdate):
    """Switch AI provider or model"""
    router = app.state.ai_router
    
    if update.provider:
        if update.provider not in ["ollama", "groq", "openai", "perplexity"]:
            raise HTTPException(400, "Invalid provider")
        router.set_provider(update.provider, update.model)
    
    return {"status": "ok", "active": router.get_status()}


# List models
@app.get("/api/models")
async def list_models():
    """List available AI models"""
    router = app.state.ai_router
    if not router:
        return {"models": []}
        
    try:
        provider = router.get_provider()
        if provider:
            models = await provider.list_models()
            return {"models": models}
    except Exception as e:
        print(f"Error listing models: {e}")
        
    return {"models": []}


# WebSocket for real-time chat
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket for real-time chat with step streaming"""
    await websocket.accept()
    
    try:
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            if message_data.get("type") == "message":
                content = message_data.get("content", "")
                msg_settings = message_data.get("settings", {})
                mode = msg_settings.get("mode", "standard")
                
                # Get or create router
                router = app.state.ai_router
                
                # Update provider if specified
                if msg_settings.get("provider"):
                    router.set_provider(
                        msg_settings["provider"],
                        msg_settings.get("model")
                    )
                
                # Create ReAct agent
                agent = ReActAgent(
                    router=router,
                    max_steps=settings.max_agent_steps,
                    token_budget=settings.token_budget,
                    memory_service=app.state.memory,
                    automation_service=app.state.automation
                )
                
                # Run agent and stream steps
                final_response = ""
                all_steps = []
                
                try:
                    async for step in agent.run(content, mode=mode):
                        # Send step to client
                        await websocket.send_json({
                            "type": "step",
                            "step": {
                                "id": step.id,
                                "type": step.type.value,
                                "content": step.content,
                                "tool_name": step.tool_name,
                                "tool_args": step.tool_args,
                                "duration_ms": step.duration_ms,
                            }
                        })
                        all_steps.append({
                            "id": step.id,
                            "type": step.type.value,
                            "content": step.content[:200],
                            "tool_name": step.tool_name,
                            "duration_ms": step.duration_ms,
                        })
                        
                        if step.type.value in ["response", "error"]:
                            final_response = step.content
                    
                    # Send final response
                    await websocket.send_json({
                        "type": "response",
                        "content": final_response,
                        "steps": all_steps,
                        "summary": agent.get_summary()
                    })
                    
                    # Store in memory
                    await app.state.memory.store_conversation(
                        user_message=content,
                        assistant_response=final_response
                    )
                except Exception as e:
                     await websocket.send_json({
                        "type": "error",
                        "content": f"I apologize, sir. An error occurred: {str(e)}"
                    })
            
            elif message_data.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
    
    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"WebSocket error: {e}")
        try:
            await websocket.send_json({
                "type": "error",
                "message": str(e)
            })
        except:
            pass


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "Jarvis AI Assistant",
        "version": "2.0.0",
        "status": "online",
        "docs": "/docs"
    }


# Run server
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )
