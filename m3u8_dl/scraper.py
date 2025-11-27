"""Web scraper for capturing m3u8 URLs and metadata from video streaming sites."""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

from patchright.async_api import async_playwright, Browser, BrowserContext

logger = logging.getLogger(__name__)

async def capture_data(
    url: str, 
    browser: Optional[Browser] = None
) -> Tuple[Dict[str, Any], List[str], Optional[Dict[str, Any]]]:
    """Capture m3u8 URLs, watch links, and metadata from a video page.
    
    Args:
        url: Video watch page URL
        browser: Optional existing Playwright Browser instance
        
    Returns:
        Tuple of (m3u8_urls, watch_links, metadata)
    """
    m3u8_urls: Dict[str, Any] = {}
    master_urls: List[str] = []
    watch_links: List[str] = []
    metadata: Optional[Dict[str, Any]] = None
    
    should_close_browser = False
    playwright = None
    
    try:
        if not browser:
            playwright = await async_playwright().start()
            browser = await playwright.chromium.launch(headless=True, channel="chrome")
            should_close_browser = True
            
        context = await browser.new_context()
        page = await context.new_page()
        
        found_data_event = asyncio.Event()
        
        async def handle_request(request: Any) -> None:
            request_url = request.url
            if '.m3u8' in request_url:
                if 'index.m3u8' in request_url:
                    m3u8_urls['index'] = request_url
                    logger.debug(f"Found index m3u8: {request_url}")
                elif 'master.m3u8' in request_url and request_url not in master_urls:
                    master_urls.append(request_url)
                    logger.debug(f"Found master m3u8: {request_url}")
                
                if metadata and (m3u8_urls.get('index') or master_urls):
                    found_data_event.set()
        
        async def handle_response(response: Any) -> None:
            nonlocal metadata
            if '/api/v1/watch/' in response.url and response.status == 200:
                try:
                    metadata = await response.json()
                    logger.debug(f"Found metadata: {metadata.get('title', 'Unknown')}")
                    if (m3u8_urls.get('index') or master_urls):
                        found_data_event.set()
                except Exception as e:
                    logger.warning(f"Failed to parse metadata: {e}")
        
        page.on('request', handle_request)
        page.on('response', handle_response)
        
        try:
            logger.info(f"Navigating to {url}")
            await page.goto(url, wait_until='domcontentloaded', timeout=30000)
        except Exception as e:
            logger.error(f"Navigation error: {e}")
            # Continue anyway, maybe requests were already captured
        
        # Wait for data or timeout
        try:
            await asyncio.wait_for(found_data_event.wait(), timeout=10.0)
        except asyncio.TimeoutError:
            logger.debug("Timeout waiting for m3u8/metadata, proceeding with what we have")
        
        if not m3u8_urls:
            logger.info("No m3u8 found yet, looking for watch links...")
            try:
                # Wait for potential dynamic content
                await page.wait_for_load_state('networkidle', timeout=5000)
                
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
            except Exception as e:
                logger.warning(f"Error scraping watch links: {e}")
        
        await context.close()
        
    except Exception as e:
        logger.error(f"Scraper error: {e}")
    finally:
        if should_close_browser and browser:
            await browser.close()
        if should_close_browser and playwright:
            await playwright.stop()
    
    if master_urls:
        m3u8_urls['master'] = master_urls if len(master_urls) > 1 else master_urls[0]
    
    return m3u8_urls, watch_links, metadata

