"""Video download module using yt-dlp."""

import asyncio
import logging
from typing import Any, Dict
from concurrent.futures import ThreadPoolExecutor

import yt_dlp

logger = logging.getLogger(__name__)

def _download_sync(url: str, filename: str) -> None:
    """Synchronous download function to be run in executor."""
    ydl_opts: Dict[str, Any] = {
        'format': 'best',
        'outtmpl': {'default': f'{filename}.%(ext)s'},
        'restrictfilenames': False,
        'windowsfilenames': False,
        'noprogress': False,
        'quiet': True,
        'no_warnings': True,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.extract_info(url, download=True)
        logger.info(f"✓ Downloaded: {filename}")
    except Exception as e:
        logger.error(f"✗ Download failed: {e}")
        raise

async def download_m3u8(url: str, filename: str) -> None:
    """Download video from m3u8 URL using yt-dlp asynchronously.
    
    Args:
        url: M3U8 stream URL with authentication token
        filename: Output filename without extension
        
    Raises:
        Exception: If download fails
    """
    loop = asyncio.get_running_loop()
    with ThreadPoolExecutor() as pool:
        await loop.run_in_executor(pool, _download_sync, url, filename)
