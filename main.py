"""HLS Stream Downloader - Standalone script.

For better organization, use the m3u8_dl package instead:
    python -m m3u8_dl <video_url>
"""

import asyncio
import sys

from m3u8_dl import download_video


async def main() -> None:
    """Main entry point for standalone script."""
    if len(sys.argv) < 2:
        print("Usage: python main.py <video_url>")
        print("\nExample:")
        print("  python main.py https://example.com/watch/1590407")
        print("\nFor more options, use: python -m m3u8_dl --help")
        sys.exit(1)
    
    url = sys.argv[1]
    success = await download_video(url)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
