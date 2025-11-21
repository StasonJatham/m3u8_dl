#!/usr/bin/env python3
"""CLI tool for uploading movies to Radarr."""

import argparse
import os
import sys
from pathlib import Path

from .radarr_uploader import RadarrUploader


def create_parser() -> argparse.ArgumentParser:
    """Create and configure argument parser."""
    parser = argparse.ArgumentParser(
        prog='radarr-upload',
        description='Upload and import movies to Radarr with automatic metadata',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Upload with auto-detection
  radarr-upload movie.mp4

  # Specify title and year
  radarr-upload movie.mp4 --title "The Matrix" --year 1999

  # Move instead of copy
  radarr-upload movie.mp4 --move

  # Use environment variables for API credentials
  export RADARR_URL=http://localhost:7878
  export RADARR_API_KEY=your_api_key
  radarr-upload movie.mp4
        """
    )

    parser.add_argument(
        'file',
        metavar='FILE',
        help='path to movie file to upload'
    )

    parser.add_argument(
        '--url',
        metavar='URL',
        help='Radarr API URL (default: $RADARR_URL or http://localhost:7878)',
        default=None
    )

    parser.add_argument(
        '--api-key',
        metavar='KEY',
        help='Radarr API key (default: $RADARR_API_KEY)',
        default=None
    )

    parser.add_argument(
        '-t', '--title',
        metavar='TITLE',
        help='movie title (auto-detected from filename if not specified)',
        default=None
    )

    parser.add_argument(
        '-y', '--year',
        metavar='YEAR',
        type=int,
        help='movie year (auto-detected from filename if not specified)',
        default=None
    )

    parser.add_argument(
        '-q', '--quality-profile',
        metavar='ID',
        type=int,
        help='quality profile ID (default: 1)',
        default=1
    )

    parser.add_argument(
        '--move',
        action='store_true',
        help='move file instead of copying'
    )

    parser.add_argument(
        '--no-auto-search',
        action='store_true',
        help='do not automatically search TMDB if movie not in library'
    )

    parser.add_argument(
        '--list-profiles',
        action='store_true',
        help='list available quality profiles and exit'
    )

    parser.add_argument(
        '--list-folders',
        action='store_true',
        help='list root folders and exit'
    )

    return parser


def get_api_credentials(args: argparse.Namespace) -> tuple[str, str]:
    """Get API URL and key from args or environment."""
    api_url = args.url or os.getenv('RADARR_URL', 'http://localhost:7878')
    api_key = args.api_key or os.getenv('RADARR_API_KEY')

    if not api_key:
        print("Error: Radarr API key required", file=sys.stderr)
        print("Provide via --api-key or RADARR_API_KEY environment variable", file=sys.stderr)
        sys.exit(1)

    return api_url, api_key


def main() -> None:
    """Main CLI entry point."""
    parser = create_parser()
    args = parser.parse_args()

    api_url, api_key = get_api_credentials(args)
    uploader = RadarrUploader(api_url, api_key)

    try:
        if args.list_profiles:
            print("Quality Profiles:")
            profiles = uploader.get_quality_profiles()
            for profile in profiles:
                print(f"  ID {profile['id']}: {profile['name']}")
            return

        if args.list_folders:
            print("Root Folders:")
            folders = uploader.get_root_folders()
            for folder in folders:
                print(f"  {folder['path']} (Free: {folder.get('freeSpace', 'N/A')})")
            return

        file_path = Path(args.file)
        if not file_path.exists():
            print(f"Error: File not found: {file_path}", file=sys.stderr)
            sys.exit(1)

        result = uploader.upload_and_import(
            str(file_path),
            title=args.title,
            year=args.year,
            auto_search=not args.no_auto_search,
            copy_files=not args.move,
            quality_profile_id=args.quality_profile
        )

        print(f"\n✓ Success!")
        print(f"Movie: {result['movie']['title']} ({result['movie'].get('year', 'N/A')})")
        print(f"Location: {result['file_path']}")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
