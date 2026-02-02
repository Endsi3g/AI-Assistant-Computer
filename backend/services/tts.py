"""
Text-to-Speech Service
Edge-TTS integration for natural voice output
"""
import io
import asyncio
import edge_tts
from config import get_settings
import base64


class TTSService:
    """Text-to-Speech service using Edge-TTS"""
    
    def __init__(self):
        self.settings = get_settings()
        self.voice = self.settings.tts_voice
        self.rate = self.settings.tts_rate
        self.pitch = self.settings.tts_pitch
    
    async def synthesize(self, text: str) -> bytes:
        """Convert text to speech and return audio bytes"""
        if not text.strip():
            return b""
        
        # Normalize text for better speech
        text = self._normalize_text(text)
        
        communicate = edge_tts.Communicate(
            text,
            self.voice,
            pitch=self.pitch,
            rate=self.rate
        )
        
        audio_buffer = bytearray()
        
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_buffer.extend(chunk["data"])
        
        return bytes(audio_buffer)
    
    async def synthesize_to_base64(self, text: str) -> str:
        """Convert text to speech and return base64 encoded audio"""
        audio_bytes = await self.synthesize(text)
        return base64.b64encode(audio_bytes).decode('utf-8')
    
    def _normalize_text(self, text: str) -> str:
        """Normalize text for better speech synthesis"""
        import re
        
        # Replace multiple periods with single pause
        text = re.sub(r'\.{2,}', '.', text)
        
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Handle common abbreviations
        abbreviations = {
            "AI": "A.I.",
            "API": "A.P.I.",
            "URL": "U.R.L.",
            "HTTP": "H.T.T.P.",
            "HTTPS": "H.T.T.P.S.",
            "CPU": "C.P.U.",
            "RAM": "ram",
            "GB": "gigabytes",
            "MB": "megabytes",
            "KB": "kilobytes",
        }
        
        for abbr, replacement in abbreviations.items():
            text = re.sub(rf'\b{abbr}\b', replacement, text)
        
        return text.strip()
    
    async def get_available_voices(self) -> list:
        """Get list of available TTS voices"""
        voices = await edge_tts.list_voices()
        return [
            {
                "name": v["Name"],
                "short_name": v["ShortName"],
                "gender": v["Gender"],
                "locale": v["Locale"]
            }
            for v in voices
        ]
    
    def set_voice(self, voice: str):
        """Change the TTS voice"""
        self.voice = voice
    
    def set_rate(self, rate: str):
        """Change speaking rate (e.g., '+10%', '-5%')"""
        self.rate = rate
    
    def set_pitch(self, pitch: str):
        """Change voice pitch (e.g., '+5Hz', '-3Hz')"""
        self.pitch = pitch


# Recommended voices for Jarvis
JARVIS_VOICES = {
    "british_male": "en-GB-RyanNeural",      # Default Jarvis voice
    "british_female": "en-GB-SoniaNeural",
    "american_male": "en-US-GuyNeural",
    "american_female": "en-US-JennyNeural",
    "australian_male": "en-AU-WilliamNeural",
    "multilingual": "en-GB-OllieMultilingualNeural"  # Can speak multiple languages
}
