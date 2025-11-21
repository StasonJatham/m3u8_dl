#!/usr/bin/env python3
"""CLI tool for uploading TV shows to Sonarr."""

import argparse
import os
import sys
from pathlib import Path

from .sonarr_uploader import SonarrUploader


def create_parser() -> argparse.ArgumentParser:
    """Create and configure argument parser."""
    parser = argparse.ArgumentParser(
        prog='sonarr-upload',
        description='Upload and import TV episodes to Sonarr with automatic metadata',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Upload with auto-detection
  sonarr-upload "Show.Name.S01E01.mp4"

  # Specify series, season, and episode
  sonarr-upload episode.mp4 --title "Breaking Bad" --season 1 --episode 1

  # Move instead of copy
  sonarr-upload episode.mp4 --move

  # Use environment variables for API credentials
  export SONARR_URL=http://localhost:8989
  export SONARR_API_KEY=your_api_key
  sonarr-upload episode.mp4
        """
    )

    parser.add_argument(
        'file',
        metavar='FILE',
        help='path to episode file to upload'
    )

    parser.add_argument(
        '--url',
        metavar='URL',
        help='Sonarr API URL (default: $SONARR_URL or http://localhost:8989)',
        default=None
    )

    parser.add_argument(
        '--api-key',
        metavar='KEY',
        help='Sonarr API key (default: $SONARR_API_KEY)',
        default=None
    )

    parser.add_argument(
        '-t', '--title',
        metavar='TITLE',
        help='series title (auto-detected from filename if not specified)',
        default=None
    )

    parser.add_argument(
        '-s', '--season',
        metavar='NUM',
        type=int,
        help='season number (auto-detected from filename if not specified)',
        default=None
    )

    parser.add_argument(
        '-e', '--episode',
        metavar='NUM',
        type=int,
        help='episode number (auto-detected from filename if not specified)',
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
        help='do not automatically search TVDB if series not in library'
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

    parser.add_argument(
        '--parse',
        action='store_true',
        help='parse filename and show detected info without uploading'
    )

    return parser


def get_api_credentials(args: argparse.Namespace) -> tuple[str, str]:
    """Get API URL and key from args or environment."""
    api_url = args.url or os.getenv('SONARR_URL', 'http://localhost:8989')
    api_key = args.api_key or os.getenv('SONARR_API_KEY')

    if not api_key:
        print("Error: Sonarr API key required", file=sys.stderr)
        print("Provide via --api-key or SONARR_API_KEY environment variable", file=sys.stderr)
        sys.exit(1)

    return api_url, api_key


def main() -> None:
    """Main CLI entry point."""
    parser = create_parser()
    args = parser.parse_args()

    if args.parse:
        file_path = Path(args.file)
        if not file_path.exists():
            print(f"Error: File not found: {file_path}", file=sys.stderr)
            sys.exit(1)
        
        parsed = SonarrUploader._parse_episode_filename(file_path.name)
        print(f"Filename: {file_path.name}")
        print(f"Detected Series: {parsed['title'] or 'N/A'}")
        print(f"Detected Season: {parsed['season'] or 'N/A'}")
        print(f"Detected Episode: {parsed['episode'] or 'N/A'}")
        return

    api_url, api_key = get_api_credentials(args)
    uploader = SonarrUploader(api_url, api_key)

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
            season=args.season,
            episode=args.episode,
            auto_search=not args.no_auto_search,
            copy_files=not args.move,
            quality_profile_id=args.quality_profile
        )

        print(f"\n✓ Success!")
        print(f"Series: {result['series']['title']}")
        print(f"Episode: S{result['season']:02d}E{result['episode']:02d}")
        print(f"Location: {result['file_path']}")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
