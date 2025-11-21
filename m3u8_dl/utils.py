"""Utility functions for parsing and formatting."""

import re
from typing import Dict, Any, Optional, Tuple


def parse_input(input_str: str) -> Tuple[str, str]:
    """Parse input URL and extract video ID.
    
    Args:
        input_str: Full video URL
        
    Returns:
        Tuple of (url, video_id)
        
    Raises:
        ValueError: If input format is invalid
    """
    input_str = input_str.strip()
    
    if not input_str.startswith(('http://', 'https://')):
        raise ValueError(f"Invalid input: {input_str}. Expected a full URL starting with http:// or https://")
    
    url = input_str
    if '/watch/' in input_str:
        video_id = url.split('/watch/')[-1].split('?')[0]
    else:
        video_id = url.rstrip('/').split('/')[-1].split('?')[0]
    
    return url, video_id


def generate_filename(metadata: Optional[Dict[str, Any]]) -> str:
    """Generate clean filename from video metadata.
    
    Args:
        metadata: Metadata dict from API response
        
    Returns:
        Sanitized filename string
    """
    if not metadata:
        return "video"
    
    try:
        title_name = metadata.get('title', {}).get('name', 'Unknown')
        episode = metadata.get('episode')
        
        if episode:
            season_num = episode.get('season_number', 0)
            episode_num = episode.get('episode_number', 0)
            episode_name = episode.get('name', '')
            
            if episode_name:
                filename = f"{title_name} - S{season_num:02d}E{episode_num:02d} - {episode_name}"
            else:
                filename = f"{title_name} - S{season_num:02d}E{episode_num:02d}"
        else:
            filename = title_name
        
        return re.sub(r'[<>:"/\\|?*]', '', filename)
    except Exception as e:
        print(f"Error generating filename: {e}")
        return "video"
