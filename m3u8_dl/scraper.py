"""
Web scraper module for capturing m3u8 URLs and metadata from video streaming sites
"""

import asyncio
from patchright.async_api import async_playwright
from typing import Dict, List, Optional, Tuple


async def capture_data(url: str) -> Tuple[Dict[str, any], List[str], Optional[dict]]:
    """
    Captures all index.m3u8 and master.m3u8 URLs (with full tokens),
    extracts /watch/* links from the page, and captures metadata from API call.
    
    Args:
        url: The video watch page URL
        
    Returns:
        Tuple containing:
        - m3u8_urls: Dict with 'index' (str) and/or 'master' (str or list) keys
        - watch_links: List of related /watch/* URLs found on the page
        - metadata: JSON metadata from the API response
    """
    m3u8_urls = {}
    master_urls = []  # Store all master.m3u8 URLs
    watch_links = []
    metadata = None
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, channel="chrome")
        context = await browser.new_context()
        page = await context.new_page()
        
        # Listen to network requests for m3u8 files
        async def handle_request(request):
            url = request.url
            if '.m3u8' in url:
                if 'index.m3u8' in url:
                    m3u8_urls['index'] = url
                elif 'master.m3u8' in url and url not in master_urls:
                    master_urls.append(url)
        
        # Listen to API responses for metadata
        async def handle_response(response):
            nonlocal metadata
            if '/api/v1/watch/' in response.url and response.status == 200:
                try:
                    data = await response.json()
                    metadata = data
                except Exception:
                    pass
        
        page.on('request', handle_request)
        page.on('response', handle_response)
        
        # Navigate to the page
        try:
            await page.goto(url, wait_until='domcontentloaded', timeout=15000)
        except Exception as e:
            print(f"Navigation error: {e}")
        
        # Wait for metadata and m3u8 files
        max_wait = 8
        for i in range(max_wait * 2):
            await asyncio.sleep(0.5)
            if metadata and m3u8_urls:
                break
        
        # Extract related /watch/* links from the page (only if m3u8 not found)
        if not m3u8_urls:
            try:
                elements = await page.locator('xpath=//*[@id="root"]/div[2]/div/div[2]/div/div//a').all()
                for element in elements:
                    href = await element.get_attribute('href')
                    if href and '/watch/' in href:
                        if href.startswith('/'):
                            # Extract domain from the current URL
                            from urllib.parse import urlparse
                            parsed = urlparse(url)
                            base_url = f"{parsed.scheme}://{parsed.netloc}"
                            full_url = f"{base_url}{href}"
                        else:
                            full_url = href
                        if full_url not in watch_links:
                            watch_links.append(full_url)
            except Exception:
                pass
        
        await browser.close()
    
    # Store master URLs as list if multiple found, single string if only one
    if master_urls:
        m3u8_urls['master'] = master_urls if len(master_urls) > 1 else master_urls[0]
    
    return m3u8_urls, watch_links, metadata
