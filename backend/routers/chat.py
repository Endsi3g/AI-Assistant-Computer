"""
Chat Router
HTTP endpoints for chat functionality
"""
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import Optional

from services.ai_engine import AIEngine
from services.memory import MemoryService
from services.tts import TTSService


router = APIRouter()

# Singleton instances
ai_engine = AIEngine()
memory_service = MemoryService()
tts_service = TTSService()


class ChatRequest(BaseModel):
    """Chat message request"""
    message: str
    include_audio: bool = True
    

class TitleRequest(BaseModel):
    """Request to generate a title"""
    message: str

class ChatResponse(BaseModel):
    """Chat response with optional audio"""
    message: str
    audio_base64: Optional[str] = None
    tools_used: list = []
    

@router.post("/", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Send a chat message and get AI response"""
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")
    
    # Get AI response
    result = await ai_engine.chat(request.message)
    
    # Store conversation in memory
    await memory_service.store_conversation(
        user_message=request.message,
        assistant_message=result["text"]
    )
    
    # Generate audio if requested
    audio_base64 = None
    if request.include_audio:
        audio_base64 = await tts_service.synthesize_to_base64(result["text"])
    
    return ChatResponse(
        message=result["text"],
        audio_base64=audio_base64,
        tools_used=result.get("tools_used", [])
    )


@router.get("/history")
async def get_history(limit: int = 20):
    """Get recent conversation history"""
    conversations = await memory_service.get_recent_conversations(limit=limit)
    return {"conversations": conversations}


@router.delete("/history")
async def clear_history():
    """Clear conversation history and reset AI context"""
    ai_engine.reset_conversation()
    return {"status": "cleared", "message": "Conversation history cleared, sir."}


@router.post("/reset")
async def reset_context():
    """Reset AI conversation context without clearing memory"""
    ai_engine.reset_conversation()
    return {"status": "reset", "message": "Context reset. Ready for new conversation, sir."}


@router.post("/title")
async def generate_title(request: TitleRequest):
    """Generate a title for a chat session"""
    title = await ai_engine.generate_title(request.message)
    return {"title": title}
