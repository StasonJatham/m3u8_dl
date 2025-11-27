"""Main downloader orchestration module."""

import logging
from typing import Any, Dict, List, Optional, Tuple

from .scraper import capture_data
from .utils import parse_input, generate_filename
from .video_downloader import download_m3u8

logger = logging.getLogger(__name__)

async def download_video(
    url_or_id: str,
    verbose: bool = True,
    custom_filename: Optional[str] = None
) -> bool:
    """Download video from URL with automatic fallback to alternative mirrors.
    
    Args:
        url_or_id: Full video URL
        verbose: Whether to print detailed progress information (deprecated, uses logging)
        custom_filename: Optional custom filename without extension
        
    Returns:
        True if successful, False otherwise
    """
    try:
        url, video_id = parse_input(url_or_id)
        
        logger.info(f"Fetching video {video_id}...")
        
        all_mirrors: List[str] = [url]
        m3u8_urls, watch_links, metadata = await capture_data(url)
        
        if watch_links:
            all_mirrors.extend(watch_links)
        
        if not m3u8_urls and watch_links:
            logger.info(f"Trying {len(watch_links)} alternative mirrors...")
        
        for mirror_idx, mirror_url in enumerate(all_mirrors):
            if mirror_idx == 0:
                current_m3u8_urls = m3u8_urls
                current_metadata = metadata
            else:
                try:
                    logger.info(f"Mirror {mirror_idx}/{len(all_mirrors) - 1}...")
                    current_m3u8_urls, _, current_metadata = await capture_data(mirror_url)
                    
                    if not current_m3u8_urls:
                        logger.debug("  No streams found")
                        continue
                    
                    logger.info("  ✓ Found streams")
                except Exception as e:
                    logger.warning(f"  Mirror error: {e}")
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
            
            logger.info(f"  Found {len(urls_to_try)} unique m3u8 URL(s)")
            for stream_type, stream_url in urls_to_try:
                logger.debug(f"    - {stream_type}.m3u8: {stream_url}")
            
            filename = custom_filename if custom_filename else generate_filename(current_metadata or metadata)
            
            for stream_idx, (stream_type, stream_url) in enumerate(urls_to_try):
                try:
                    logger.info(f"  Downloading ({stream_type}.m3u8)...")
                    await download_m3u8(stream_url, filename)
                    logger.info("✓ Success!")
                    return True
                except Exception as e:
                    logger.error(f"Failed to download stream: {e}")
                    continue
        
        logger.error("❌ All download attempts failed")
        return False
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        return False
