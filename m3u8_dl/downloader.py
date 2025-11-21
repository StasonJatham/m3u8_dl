"""
Main downloader orchestration module
"""

from .scraper import capture_data
from .utils import parse_input, generate_filename
from .video_downloader import download_m3u8


async def download_video(url_or_id: str, verbose: bool = True) -> bool:
    """
    Downloads a video given a URL or video ID.
    If m3u8 is not found on the initial URL, tries all alternative /watch/* links.
    
    Args:
        url_or_id: Either a full video URL or just a video ID
        verbose: Whether to print detailed progress information
        
    Returns:
        True if successful, False otherwise
        
    Example:
        >>> import asyncio
        >>> from m3u8_dl import download_video
        >>> 
        >>> # Download by ID
        >>> asyncio.run(download_video("1590407"))
        >>> 
        >>> # Download by URL
        >>> asyncio.run(download_video("https://example.com/watch/1590407"))
    """
    try:
        url, video_id = parse_input(url_or_id)
        
        if verbose:
            print(f"Fetching video {video_id}...")
        
        # Build list of all mirrors to try (starting with the initial URL)
        all_mirrors = [url]
        
        # Capture m3u8 URLs, related links, and metadata from initial URL
        m3u8_urls, watch_links, metadata = await capture_data(url)
        
        # Add alternative mirrors to the list
        if watch_links:
            all_mirrors.extend(watch_links)
        
        # If no streams found on initial URL, show we're trying alternatives
        if not m3u8_urls and watch_links:
            if verbose:
                print(f"Trying {len(watch_links)} alternative mirrors...")
        
        # Try each mirror in order
        for mirror_idx, mirror_url in enumerate(all_mirrors):
            # Skip initial capture if this is the first mirror (already captured)
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
                            print(f"  No streams found")
                        continue
                    
                    if verbose and mirror_idx > 0:
                        print(f"  ✓ Found streams")
                except Exception:
                    if verbose:
                        print(f"  Mirror error")
                    continue
            
            # Skip if no streams found on this mirror
            if not current_m3u8_urls:
                continue
            
            # Prepare URLs in priority order: index first, then all masters
            urls_to_try = []
            if 'index' in current_m3u8_urls:
                urls_to_try.append(('index', current_m3u8_urls['index']))
            if 'master' in current_m3u8_urls:
                master_urls = current_m3u8_urls['master']
                if isinstance(master_urls, list):
                    for master_url in master_urls:
                        urls_to_try.append(('master', master_url))
                else:
                    urls_to_try.append(('master', master_urls))
            
            # Debug: Show all found m3u8 URLs
            if verbose:
                print(f"  Found {len(urls_to_try)} unique m3u8 URL(s):")
                for stream_type, stream_url in urls_to_try:
                    # Truncate URL for cleaner display
                    display_url = stream_url if len(stream_url) <= 80 else stream_url[:77] + "..."
                    print(f"    - {stream_type}.m3u8: {display_url}")
            
            # Try all streams from this mirror
            filename = generate_filename(current_metadata or metadata)
            
            for stream_idx, (stream_type, stream_url) in enumerate(urls_to_try):
                try:
                    if verbose:
                        if len(urls_to_try) > 1:
                            print(f"  Trying {stream_type}.m3u8 ({stream_idx + 1}/{len(urls_to_try)})...", end=' ')
                        else:
                            print(f"  Downloading ({stream_type}.m3u8)...", end=' ')
                    download_m3u8(stream_url, filename)
                    if verbose:
                        print(f"✓ Success!")
                    return True
                except Exception as e:
                    if verbose:
                        print(f"Failed")
                    continue
        
        # All mirrors and streams exhausted
        if verbose:
            print("❌ All download attempts failed")
        return False
            
    except Exception as e:
        print(f"Error: {e}")
        return False
