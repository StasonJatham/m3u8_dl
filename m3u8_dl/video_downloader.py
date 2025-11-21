"""
Video download module using yt-dlp
"""

import yt_dlp


def download_m3u8(url: str, filename: str) -> None:
    """
    Downloads video from m3u8 URL using yt-dlp.
    
    Args:
        url: The m3u8 stream URL (with token)
        filename: Output filename (without extension)
        
    Raises:
        Exception: If download fails
    """
    ydl_opts = {
        'format': 'best',
        'outtmpl': {'default': filename + '.%(ext)s'},
        'restrictfilenames': False,
        'windowsfilenames': False,
        'quiet': True,
        'no_warnings': True,
        'progress_hooks': [lambda d: print(f"\r{d.get('_percent_str', '0%')} of {d.get('_total_bytes_str', '?')} at {d.get('_speed_str', '?')}", end='') if d['status'] == 'downloading' else None],
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.extract_info(url, download=True)
        print(f"\n✓ Downloaded: {filename}")
    except Exception as e:
        print(f"\n✗ Download failed: {e}")
        raise
