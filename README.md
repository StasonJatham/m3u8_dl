<div align="center">

<img src="docs/pirate-python-whiteweb.webp" alt="HLS Downloader" width="400">

# M3U8 Downloader

**Professional HLS Stream Downloader for Educational Research**

[![Python 3.4+](https://img.shields.io/badge/python-3.14+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-Educational%20Use-orange.svg)](#legal-notice)

[Features](#features) • [Quick Start](#quick-start) • [Usage](#usage) • [Radarr](#radarr-upload-tool) • [Sonarr](#sonarr-upload-tool) • [Docker](#docker)

</div>

---

## ⚠️ Legal Notice

> **FOR EDUCATIONAL AND RESEARCH PURPOSES ONLY**
>
> This software is provided as-is for academic research and educational purposes. Users are solely responsible for compliance with copyright laws and terms of service. The authors accept no liability for misuse. Unauthorized downloading of copyrighted content is illegal in most jurisdictions.

---

## Features

### HLS Downloader

- 🎯 **Automated Stream Capture** - Intercepts HLS streams with authentication tokens
- 📝 **Smart Metadata Extraction** - Generates proper filenames from API metadata
- 🔄 **Resilient Fallback System** - Tries multiple mirrors and stream variants automatically
- 🐳 **Docker Ready** - Pre-configured container with all dependencies
- 🛠️ **Dual Interface** - Use as CLI tool or Python library
- ⚡ **Optimized Performance** - Concurrent mirror scanning and intelligent retry logic

### Radarr Uploader

- 🎬 **Automatic TMDB Lookup** - Searches and matches movies automatically
- 📚 **Library Integration** - Seamlessly adds movies to your Radarr library
- 🏷️ **Smart Filename Parsing** - Extracts title and year from filenames
- 📁 **Organized Import** - Properly structures files in Radarr's format
- ⚙️ **Flexible Configuration** - Supports custom quality profiles and root folders

### Sonarr Uploader

- 📺 **Automatic TVDB Lookup** - Searches and matches TV series automatically
- 📚 **Library Integration** - Seamlessly adds shows to your Sonarr library
- 🏷️ **Smart Episode Parsing** - Extracts series/season/episode from filenames (S01E01, 1x01, 101)
- 📁 **Season Organization** - Properly structures episodes in season folders
- ⚙️ **Flexible Configuration** - Supports custom quality profiles and root folders

## Quick Start

### Local Installation

```bash
# Install dependencies
pip install patchright yt-dlp

# Install browser (required for patchright)
patchright install chromium

# Download a video
python -m m3u8_dl https://example.com/watch/1590407
```

### Docker

```bash
# Build image
docker build -t m3u8-dl .

# Run container
docker run -v $(pwd)/downloads:/app/downloads m3u8-dl https://example.com/watch/1590407
```

## Usage

### Command Line

**Basic download:**
```bash
python -m m3u8_dl https://example.com/watch/1590407
```

**With custom filename:**
```bash
python -m m3u8_dl https://example.com/watch/1590407 --name my_video
```

**Save to specific directory:**
```bash
python -m m3u8_dl https://example.com/watch/1590407 -o ~/Downloads
```

**Quiet mode:**
```bash
python -m m3u8_dl https://example.com/watch/1590407 --quiet
```

### Python Library

```python
import asyncio
from m3u8_dl import download_video

async def main():
    await download_video("https://example.com/watch/1590407")  # Basic
    await download_video("https://example.com/watch/1590407", verbose=False)  # Quiet mode
    await download_video("https://example.com/watch/1590407", custom_filename="my_video")  # Custom name

asyncio.run(main())
```

## Radarr Upload Tool

Upload and automatically import downloaded movies into Radarr with proper metadata.

> **📖 See [RADARR_GUIDE.md](docs/RADARR_GUIDE.md) for detailed documentation and advanced usage.**

### Setup

```bash
# Set environment variables (recommended)
export RADARR_URL=http://localhost:7878
export RADARR_API_KEY=your_api_key_here

# Or use command line flags
python radarr_upload.py --url http://localhost:7878 --api-key your_api_key movie.mp4
```

### Usage

**Auto-detect title and year from filename:**
```bash
python radarr_upload.py "The Matrix 1999.mp4"
```

**Specify title and year manually:**
```bash
python radarr_upload.py movie.mp4 --title "The Matrix" --year 1999
```

**Move file instead of copy:**
```bash
python radarr_upload.py movie.mp4 --move
```

**List quality profiles:**
```bash
python radarr_upload.py --list-profiles
```

**List root folders:**
```bash
python radarr_upload.py --list-folders
```

**Complete workflow example:**
```bash
# Download video
python -m m3u8_dl https://example.com/watch/1590407 -n "The Matrix 1999"

# Upload to Radarr
python radarr_upload.py "The Matrix 1999.mp4"
```

## Sonarr Upload Tool

Upload and automatically import downloaded TV episodes into Sonarr with proper metadata.

> **📖 See [SONARR_GUIDE.md](docs/SONARR_GUIDE.md) for detailed documentation and advanced usage.**

### Setup

```bash
# Set environment variables (recommended)
export SONARR_URL=http://localhost:8989
export SONARR_API_KEY=your_api_key_here

# Or use command line flags
python sonarr_upload.py --url http://localhost:8989 --api-key your_api_key episode.mp4
```

### Usage

**Auto-detect from filename:**
```bash
python sonarr_upload.py "Breaking.Bad.S01E01.mp4"
```

**Specify series, season, and episode manually:**
```bash
python sonarr_upload.py episode.mp4 --title "Breaking Bad" --season 1 --episode 1
```

**Parse filename without uploading:**
```bash
python sonarr_upload.py "Show.Name.S02E05.mp4" --parse
```

**Move instead of copy:**
```bash
python sonarr_upload.py episode.mp4 --move
```

**Complete workflow example:**
```bash
# Download episode
python -m m3u8_dl https://example.com/watch/1590407 -n "Breaking Bad S01E01"

# Upload to Sonarr
python sonarr_upload.py "Breaking Bad S01E01.mp4"
```

## How It Works

### HLS Downloader

1. **Browser Automation** - Launches headless Chrome via patchright to execute JavaScript
2. **Network Interception** - Captures authenticated .m3u8 HLS stream URLs
3. **Metadata Extraction** - Parses API responses for title, season, episode information
4. **Intelligent Fallback** - Tries multiple mirrors and stream variants on failure
5. **Stream Download** - Downloads via yt-dlp with proper authentication tokens

### Output Filenames

- **TV Series**: `Show Title - S01E01 - Episode Name.mp4`
- **Movies**: `Movie Title.mp4`

## Docker

The included Dockerfile provides a fully configured environment with all dependencies pre-installed.

### Building

```bash
docker build -t m3u8-dl .
```

### Running

```bash
# Download to current directory
docker run -v $(pwd)/downloads:/app/downloads m3u8-dl <VIDEO_URL>

# Example
docker run -v $(pwd)/downloads:/app/downloads m3u8-dl https://example.com/watch/1590407
```

### Environment Variables

```bash
docker run -e VERBOSE=false -v $(pwd)/downloads:/app/downloads m3u8-dl https://example.com/watch/1590407
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Browser not found | Install Chrome or use Docker |
| No streams found | Video may be unavailable or region-locked |
| Download fails (502) | Tool automatically retries with alternative mirrors |
| yt-dlp errors | Update: `pip install -U yt-dlp` |

## Project Structure

```
m3u8-dl/
├── m3u8_dl/              # Main package
│   ├── scraper.py          # Browser automation & network interception
│   ├── downloader.py       # Orchestration & fallback logic
│   ├── video_downloader.py # yt-dlp wrapper
│   ├── utils.py            # Helper functions
│   └── cli.py              # CLI interface
├── Dockerfile              # Docker configuration
├── requirements.txt        # Python dependencies
└── README.md              # Documentation
```

## API Reference

### `download_video(url_or_id: str, verbose: bool = True) -> bool`

Main download function. Accepts video ID or full URL.

**Returns:** `True` if successful, `False` otherwise

---

<div align="center">

### Legal Disclaimer

**This software is provided "AS IS" without warranty of any kind.**

Users are solely responsible for compliance with all applicable laws, including but not limited to copyright laws, terms of service agreements, and data protection regulations. The authors and contributors accept no liability for misuse, legal consequences, or damages arising from the use of this software.

**Unauthorized downloading of copyrighted content is illegal.**

Use at your own risk and responsibility.

---

Made with ❤️ for educational purposes

</div>
