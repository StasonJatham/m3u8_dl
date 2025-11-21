"""Video download module using yt-dlp."""

from typing import Any, Dict

import yt_dlp


def download_m3u8(url: str, filename: str) -> None:
    """Download video from m3u8 URL using yt-dlp.
    
    Args:
        url: M3U8 stream URL with authentication token
        filename: Output filename without extension
        
    Raises:
        Exception: If download fails
    """
    ydl_opts: Dict[str, Any] = {
        'format': 'best',
        'outtmpl': {'default': f'{filename}.%(ext)s'},
        'restrictfilenames': False,
        'windowsfilenames': False,
        'noprogress': True,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.extract_info(url, download=True)
        print(f"✓ Downloaded: {filename}")
    except Exception as e:
        print(f"✗ Download failed: {e}")
        raise
