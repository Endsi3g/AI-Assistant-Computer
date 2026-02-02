"""
Voice Router
HTTP endpoints for voice synthesis and voice list
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
from typing import Optional

from services.tts import TTSService, JARVIS_VOICES


router = APIRouter()
tts_service = TTSService()


class SynthesizeRequest(BaseModel):
    """Text-to-speech request"""
    text: str
    voice: Optional[str] = None
    rate: Optional[str] = None
    pitch: Optional[str] = None


class VoiceSettings(BaseModel):
    """Voice settings update"""
    voice: Optional[str] = None
    rate: Optional[str] = None
    pitch: Optional[str] = None


@router.post("/synthesize")
async def synthesize_speech(request: SynthesizeRequest):
    """Convert text to speech and return audio as base64"""
    if not request.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")
    
    # Apply temporary settings if provided
    original_voice = tts_service.voice
    original_rate = tts_service.rate
    original_pitch = tts_service.pitch
    
    try:
        if request.voice:
            tts_service.set_voice(request.voice)
        if request.rate:
            tts_service.set_rate(request.rate)
        if request.pitch:
            tts_service.set_pitch(request.pitch)
        
        audio_base64 = await tts_service.synthesize_to_base64(request.text)
        
        return {
            "audio_base64": audio_base64,
            "voice": tts_service.voice,
            "text_length": len(request.text)
        }
    finally:
        # Restore original settings
        tts_service.voice = original_voice
        tts_service.rate = original_rate
        tts_service.pitch = original_pitch


@router.post("/synthesize/raw")
async def synthesize_speech_raw(request: SynthesizeRequest):
    """Convert text to speech and return raw MP3 audio"""
    if not request.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")
    
    audio_bytes = await tts_service.synthesize(request.text)
    
    return Response(
        content=audio_bytes,
        media_type="audio/mpeg",
        headers={
            "Content-Disposition": "inline; filename=jarvis_speech.mp3"
        }
    )


@router.get("/voices")
async def list_voices():
    """Get list of available TTS voices"""
    all_voices = await tts_service.get_available_voices()
    
    return {
        "recommended": JARVIS_VOICES,
        "current": tts_service.voice,
        "all_voices": all_voices
    }


@router.put("/settings")
async def update_voice_settings(settings: VoiceSettings):
    """Update default voice settings"""
    if settings.voice:
        tts_service.set_voice(settings.voice)
    if settings.rate:
        tts_service.set_rate(settings.rate)
    if settings.pitch:
        tts_service.set_pitch(settings.pitch)
    
    return {
        "status": "updated",
        "current_settings": {
            "voice": tts_service.voice,
            "rate": tts_service.rate,
            "pitch": tts_service.pitch
        }
    }


@router.get("/settings")
async def get_voice_settings():
    """Get current voice settings"""
    return {
        "voice": tts_service.voice,
        "rate": tts_service.rate,
        "pitch": tts_service.pitch,
        "recommended_voices": JARVIS_VOICES
    }
