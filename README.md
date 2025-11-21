<div align="center">

<img src="docs/pirate-python-whiteweb.webp" alt="HLS Downloader" width="400">

# M3U8 Downloader

**Professional HLS Stream Downloader for Educational Research**

[![Python 3.4+](https://img.shields.io/badge/python-3.14+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-Educational%20Use-orange.svg)](#legal-notice)

[Features](#features) • [Quick Start](#quick-start) • [Usage](#usage) • [Docker](#docker) • [Legal Notice](#legal-notice)

</div>

---

## ⚠️ Legal Notice

> **FOR EDUCATIONAL AND RESEARCH PURPOSES ONLY**
>
> This software is provided as-is for academic research and educational purposes. Users are solely responsible for compliance with copyright laws and terms of service. The authors accept no liability for misuse. Unauthorized downloading of copyrighted content is illegal in most jurisdictions.

---

## Features

- 🎯 **Automated Stream Capture** - Intercepts HLS streams with authentication tokens
- 📝 **Smart Metadata Extraction** - Generates proper filenames from API metadata
- 🔄 **Resilient Fallback System** - Tries multiple mirrors and stream variants automatically
- 🐳 **Docker Ready** - Pre-configured container with all dependencies
- 🛠️ **Dual Interface** - Use as CLI tool or Python library
- ⚡ **Optimized Performance** - Concurrent mirror scanning and intelligent retry logic

## Quick Start

### Local Installation

```bash
# Install dependencies
pip install patchright yt-dlp

# Install browser (required for patchright)
patchright install chromium

# Download a video
python -m m3u8_dl 1590407
```

### Docker

```bash
# Build image
docker build -t m3u8-dl .

# Run container
docker run -v $(pwd)/downloads:/app/downloads m3u8-dl 1590407
```

## Usage

### Command Line

**By video ID:**
```bash
python -m m3u8_dl 1590407
```

**By URL:**
```bash
python -m m3u8_dl https://example.com/watch/1590407
```

### Python Library

```python
import asyncio
from m3u8_dl import download_video

async def main():
    await download_video("1590407")  # By ID
    await download_video("https://example.com/watch/1590407")  # By URL
    await download_video("1590407", verbose=False)  # Quiet mode

asyncio.run(main())
```

## How It Works

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
docker run -v $(pwd)/downloads:/app/downloads m3u8-dl <VIDEO_ID>

# Example
docker run -v $(pwd)/downloads:/app/downloads m3u8-dl 1590407
```

### Environment Variables

```bash
docker run -e VERBOSE=false -v $(pwd)/downloads:/app/downloads m3u8-dl 1590407
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
