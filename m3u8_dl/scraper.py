"""Web scraper for capturing m3u8 URLs and metadata from video streaming sites."""

import asyncio
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

from patchright.async_api import async_playwright


async def capture_data(url: str) -> Tuple[Dict[str, Any], List[str], Optional[Dict[str, Any]]]:
    """Capture m3u8 URLs, watch links, and metadata from a video page.
    
    Args:
        url: Video watch page URL
        
    Returns:
        Tuple of (m3u8_urls, watch_links, metadata)
    """
    m3u8_urls: Dict[str, Any] = {}
    master_urls: List[str] = []
    watch_links: List[str] = []
    metadata: Optional[Dict[str, Any]] = None
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, channel="chrome")
        context = await browser.new_context()
        page = await context.new_page()
        
        async def handle_request(request: Any) -> None:
            request_url = request.url
            if '.m3u8' in request_url:
                if 'index.m3u8' in request_url:
                    m3u8_urls['index'] = request_url
                elif 'master.m3u8' in request_url and request_url not in master_urls:
                    master_urls.append(request_url)
        
        async def handle_response(response: Any) -> None:
            nonlocal metadata
            if '/api/v1/watch/' in response.url and response.status == 200:
                try:
                    metadata = await response.json()
                except Exception:
                    pass
        
        page.on('request', handle_request)
        page.on('response', handle_response)
        
        try:
            await page.goto(url, wait_until='domcontentloaded', timeout=15000)
        except Exception as e:
            print(f"Navigation error: {e}")
        
        for _ in range(16):
            await asyncio.sleep(0.5)
            if metadata and m3u8_urls:
                break
        
        if not m3u8_urls:
            try:
                elements = await page.locator('xpath=//*[@id="root"]/div[2]/div/div[2]/div/div//a').all()
                for element in elements:
                    href = await element.get_attribute('href')
                    if href and '/watch/' in href:
                        if href.startswith('/'):
                            parsed = urlparse(url)
                            full_url = f"{parsed.scheme}://{parsed.netloc}{href}"
                        else:
                            full_url = href
                        if full_url not in watch_links:
                            watch_links.append(full_url)
            except Exception:
                pass
        
        await browser.close()
    
    if master_urls:
        m3u8_urls['master'] = master_urls if len(master_urls) > 1 else master_urls[0]
    
    return m3u8_urls, watch_links, metadata
