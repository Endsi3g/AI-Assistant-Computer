import yt_dlp
from typing import Dict, Any, Optional
import os

class YouTubeTool:
    def __init__(self, download_path: str = "downloads"):
        self.download_path = download_path
        if not os.path.exists(download_path):
            os.makedirs(download_path)

    def get_metadata(self, url: str) -> Dict[str, Any]:
        """Fetch video metadata."""
        ydl_opts = {'quiet': True, 'no_warnings': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return {
                'title': info.get('title'),
                'channel': info.get('uploader'),
                'views': info.get('view_count'),
                'duration': info.get('duration'),
                'description': info.get('description'),
            }

    def get_transcript(self, url: str, lang: str = 'en') -> str:
        """Download transcript/subtitles."""
        # Note: yt-dlp downloads subs as files. We need to read them back.
        # This is a bit tricky to return directly as text without file I/O.
        # Capability: Download auto-subs, convert to text.
        
        ydl_opts = {
            'skip_download': True,
            'writeautomaticsub': True,
            'writesubtitles': True,
            'subtitleslangs': [lang],
            'outtmpl': os.path.join(self.download_path, '%(id)s.%(ext)s'),
            'quiet': True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            video_id = info['id']
            ydl.download([url])
            
            # Check for vtt file
            potential_files = [
                f"{video_id}.{lang}.vtt",
                f"{video_id}.en.vtt" # Fallback
            ]
            
            content = "Transcript not found."
            for fname in potential_files:
                fpath = os.path.join(self.download_path, fname)
                if os.path.exists(fpath):
                    with open(fpath, 'r', encoding='utf-8') as f:
                        # Simple cleanup of VTT
                        lines = f.readlines()
                        # basic filter for timestamps and headers
                        content = " ".join([l.strip() for l in lines if '-->' not in l and l.strip() and not l.startswith('WEBVTT')])
                    break
            
            return content

    def download_video(self, url: str, resolution: str = "720") -> str:
        """Download video file."""
        ydl_opts = {
            'format': f'bestvideo[height<={resolution}]+bestaudio/best[height<={resolution}]',
            'outtmpl': os.path.join(self.download_path, '%(title)s.%(ext)s'),
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            return ydl.prepare_filename(info)

def run_youtube_task(action: str, url: str, **kwargs) -> str:
    tool = YouTubeTool()
    if action == "metadata":
        return str(tool.get_metadata(url))
    elif action == "transcript":
        return tool.get_transcript(url, kwargs.get('lang', 'en'))
    elif action == "download":
        return tool.download_video(url)
    else:
        return "Unknown action. Use: metadata, transcript, download"
