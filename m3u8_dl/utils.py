"""
Utility functions for parsing and formatting
"""

import re
from typing import Tuple, Optional


# Base domain - configure this for your target site
BASE_DOMAIN = "https://example.com"


def parse_input(input_str: str) -> Tuple[str, str]:
    """
    Parses input which can be a full URL or just a video ID.
    
    Args:
        input_str: Either a full video URL or just a video ID number
        
    Returns:
        Tuple of (full_url, video_id)
        
    Raises:
        ValueError: If input format is invalid
    """
    input_str = input_str.strip()
    
    # If it's just a number/ID
    if input_str.isdigit():
        video_id = input_str
        url = f"{BASE_DOMAIN}/watch/{video_id}"
    # If it's a full URL
    elif '/watch/' in input_str:
        url = input_str
        video_id = url.split('/watch/')[-1].split('?')[0]
    else:
        raise ValueError(f"Invalid input: {input_str}. Expected URL or video ID.")
    
    return url, video_id


def generate_filename(metadata: Optional[dict]) -> str:
    """
    Generates a clean filename from metadata.
    
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
            # For TV series episodes
            season_num = episode.get('season_number', 0)
            episode_num = episode.get('episode_number', 0)
            episode_name = episode.get('name', '')
            
            if episode_name:
                # Use episode name if available
                filename = f"{title_name} - S{season_num:02d}E{episode_num:02d} - {episode_name}"
            else:
                filename = f"{title_name} - S{season_num:02d}E{episode_num:02d}"
        else:
            # For movies - just use the title name
            filename = title_name
        
        # Clean filename by removing invalid characters
        filename = re.sub(r'[<>:"/\\|?*]', '', filename)
        
        return filename
    except Exception as e:
        print(f"Error generating filename: {e}")
        return "video"
