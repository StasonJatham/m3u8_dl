"""Main downloader orchestration module."""

from typing import Any, Dict, List, Optional, Tuple

from .scraper import capture_data
from .utils import parse_input, generate_filename
from .video_downloader import download_m3u8


async def download_video(
    url_or_id: str,
    verbose: bool = True,
    custom_filename: Optional[str] = None
) -> bool:
    """Download video from URL with automatic fallback to alternative mirrors.
    
    Args:
        url_or_id: Full video URL
        verbose: Whether to print detailed progress information
        custom_filename: Optional custom filename without extension
        
    Returns:
        True if successful, False otherwise
    """
    try:
        url, video_id = parse_input(url_or_id)
        
        if verbose:
            print(f"Fetching video {video_id}...")
        
        all_mirrors: List[str] = [url]
        m3u8_urls, watch_links, metadata = await capture_data(url)
        
        if watch_links:
            all_mirrors.extend(watch_links)
        
        if not m3u8_urls and watch_links and verbose:
            print(f"Trying {len(watch_links)} alternative mirrors...")
        
        for mirror_idx, mirror_url in enumerate(all_mirrors):
            if mirror_idx == 0:
                current_m3u8_urls = m3u8_urls
                current_metadata = metadata
            else:
                try:
                    if verbose:
                        print(f"Mirror {mirror_idx}/{len(all_mirrors) - 1}...")
                    current_m3u8_urls, _, current_metadata = await capture_data(mirror_url)
                    
                    if not current_m3u8_urls:
                        if verbose:
                            print("  No streams found")
                        continue
                    
                    if verbose:
                        print("  ✓ Found streams")
                except Exception:
                    if verbose:
                        print("  Mirror error")
                    continue
            
            if not current_m3u8_urls:
                continue
            
            urls_to_try: List[Tuple[str, str]] = []
            if 'index' in current_m3u8_urls:
                urls_to_try.append(('index', current_m3u8_urls['index']))
            if 'master' in current_m3u8_urls:
                master_urls = current_m3u8_urls['master']
                if isinstance(master_urls, list):
                    urls_to_try.extend([('master', url) for url in master_urls])
                else:
                    urls_to_try.append(('master', master_urls))
            
            if verbose:
                print(f"  Found {len(urls_to_try)} unique m3u8 URL(s):")
                for stream_type, stream_url in urls_to_try:
                    display_url = stream_url if len(stream_url) <= 80 else stream_url[:77] + "..."
                    print(f"    - {stream_type}.m3u8: {display_url}")
            
            filename = custom_filename if custom_filename else generate_filename(current_metadata or metadata)
            
            for stream_idx, (stream_type, stream_url) in enumerate(urls_to_try):
                try:
                    if verbose:
                        if len(urls_to_try) > 1:
                            print(f"  Trying {stream_type}.m3u8 ({stream_idx + 1}/{len(urls_to_try)})...", end=' ')
                        else:
                            print(f"  Downloading ({stream_type}.m3u8)...", end=' ')
                    download_m3u8(stream_url, filename)
                    if verbose:
                        print("✓ Success!")
                    return True
                except Exception:
                    if verbose:
                        print("Failed")
                    continue
        
        if verbose:
            print("❌ All download attempts failed")
        return False
            
    except Exception as e:
        print(f"Error: {e}")
        return False
