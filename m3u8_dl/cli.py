"""Command-line interface for HLS downloader."""

import argparse
import asyncio
import os
import sys
from typing import Optional

from .downloader import download_video


def create_parser() -> argparse.ArgumentParser:
    """Create and configure argument parser."""
    parser = argparse.ArgumentParser(
        prog='m3u8_dl',
        description='Professional HLS Stream Downloader for Educational Research',
        epilog='For educational and research purposes only. Users are responsible for compliance with copyright laws.',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        'video',
        metavar='VIDEO_URL',
        help='full video URL to download (e.g., https://example.com/watch/1590407)'
    )
    
    parser.add_argument(
        '-o', '--output',
        metavar='DIR',
        help='output directory for downloaded videos (default: current directory)',
        default=None
    )
    
    parser.add_argument(
        '-n', '--name',
        metavar='FILENAME',
        help='custom output filename without extension (e.g., "my_video")',
        default=None
    )
    
    parser.add_argument(
        '-q', '--quiet',
        action='store_true',
        help='suppress all output except errors'
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='enable verbose output with detailed progress information (default)'
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version='%(prog)s 1.0.0'
    )
    
    return parser


def main() -> None:
    """Main CLI entry point."""
    parser = create_parser()
    
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)
    
    args = parser.parse_args()
    verbose = not args.quiet
    
    if args.output:
        os.makedirs(args.output, exist_ok=True)
        original_dir = os.getcwd()
        os.chdir(args.output)
        try:
            success = asyncio.run(download_video(args.video, verbose=verbose, custom_filename=args.name))
        finally:
            os.chdir(original_dir)
    else:
        success = asyncio.run(download_video(args.video, verbose=verbose, custom_filename=args.name))
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
