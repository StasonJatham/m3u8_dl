"""
Command-line interface for HLS downloader
"""

import asyncio
import sys
from .downloader import download_video


def main():
    """Main CLI entry point"""
    if len(sys.argv) < 2 or sys.argv[1] in ['--help', '-h']:
        print("HLS Stream Downloader")
        print("\nUsage: python -m m3u8_dl <video_id_or_url>")
        print("\nExamples:")
        print("  python -m m3u8_dl 1590407")
        print("  python -m m3u8_dl https://example.com/watch/1590407")
        print("\nOptions:")
        print("  --help, -h    Show this help message")
        sys.exit(0 if len(sys.argv) > 1 else 1)
    
    url_or_id = sys.argv[1]
    success = asyncio.run(download_video(url_or_id))
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
