"""
HLS Stream Downloader - Standalone script
For better organization, use the m3u8_dl package instead.
"""

import asyncio
import sys
from m3u8_dl import download_video


async def main():
    """Main entry point for standalone script"""
    if len(sys.argv) < 2:
        print("Usage: python main.py <video_id_or_url>")
        print("\nExamples:")
        print("  python main.py 1590407")
        print("  python main.py https://example.com/watch/1590407")
        print("\nTip: For better organization, use: python -m m3u8_dl <video_id_or_url>")
        sys.exit(1)
    
    url_or_id = sys.argv[1]
    success = await download_video(url_or_id)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
