# Sonarr Upload Tool - Usage Guide

## Overview

The Sonarr Upload Tool automatically imports TV episode files into your Sonarr library with proper metadata from TVDB.

## Features

- **Automatic TVDB Lookup**: Searches The Movie Database for TV series metadata
- **Smart Filename Parsing**: Extracts series, season, and episode from filenames
- **Multiple Format Support**: S01E01, 1x01, 101 formats all supported
- **Library Integration**: Adds series to Sonarr if not already present
- **Season Organization**: Properly structures episodes in season folders
- **Flexible Options**: Support for custom quality profiles and manual overrides

## Installation

```bash
# Install dependencies
pip install -r requirements.txt
```

## Configuration

### Method 1: Environment Variables (Recommended)

Create a `.env` file or export variables:

```bash
export SONARR_URL=http://localhost:8989
export SONARR_API_KEY=your_api_key_here
```

To find your API key:
1. Open Sonarr web interface
2. Go to Settings → General → Security
3. Copy the API Key

### Method 2: Command Line Flags

```bash
python sonarr_upload.py --url http://localhost:8989 --api-key your_api_key episode.mp4
```

## Usage Examples

### Basic Upload (Auto-detect from filename)

```bash
python sonarr_upload.py "Breaking.Bad.S01E01.Pilot.mp4"
```

This will:
1. Extract series "Breaking Bad", season 1, episode 1 from filename
2. Search TVDB for the series
3. Add to Sonarr library if not present
4. Copy file to Sonarr's organized folder structure (e.g., `/Series/Breaking Bad/Season 01/`)
5. Trigger import

### Specify Series, Season, and Episode Manually

```bash
python sonarr_upload.py episode.mp4 --title "Breaking Bad" --season 1 --episode 1
```

### Parse Filename Without Uploading

```bash
python sonarr_upload.py "Game.of.Thrones.S05E09.mp4" --parse
```

Output:
```
Filename: Game.of.Thrones.S05E09.mp4
Detected Series: Game of Thrones
Detected Season: 5
Detected Episode: 9
```

### Move Instead of Copy

```bash
python sonarr_upload.py episode.mp4 --move
```

### Use Custom Quality Profile

```bash
# First, list available profiles
python sonarr_upload.py --list-profiles

# Then use the desired profile ID
python sonarr_upload.py episode.mp4 --quality-profile 2
```

### List Root Folders

```bash
python sonarr_upload.py --list-folders
```

## Workflow Integration

### Complete Download and Upload

```bash
# Step 1: Download episode
python -m m3u8_dl https://example.com/watch/1590407 -n "Breaking Bad S01E01"

# Step 2: Upload to Sonarr
python sonarr_upload.py "Breaking Bad S01E01.mp4"
```

### Batch Upload

```bash
# Upload all episodes in a directory
for file in *.mp4; do
    python sonarr_upload.py "$file"
done
```

## Python API Usage

```python
from m3u8_dl import SonarrUploader

# Initialize uploader
uploader = SonarrUploader(
    api_url="http://localhost:8989",
    api_key="your_api_key"
)

# Upload and import an episode
result = uploader.upload_and_import(
    file_path="Breaking.Bad.S01E01.mp4",
    title="Breaking Bad",  # Optional, auto-detected if not provided
    season=1,              # Optional, auto-detected if not provided
    episode=1,             # Optional, auto-detected if not provided
    copy_files=True,       # False to move instead of copy
    quality_profile_id=1
)

print(f"Imported: {result['series']['title']}")
print(f"Episode: S{result['season']:02d}E{result['episode']:02d}")
print(f"Location: {result['file_path']}")
```

## Filename Auto-Detection

The tool automatically extracts series, season, and episode from filenames:

| Filename | Detected Series | Season | Episode |
|----------|----------------|--------|---------|
| `Breaking.Bad.S01E01.Pilot.1080p.mp4` | Breaking Bad | 1 | 1 |
| `Game.of.Thrones.5x09.mp4` | Game of Thrones | 5 | 9 |
| `The.Office.203.720p.WEB-DL.mkv` | The Office | 2 | 3 |
| `Show.Name.s02e05.mp4` | Show Name | 2 | 5 |

### Supported Formats

1. **S01E01 Format** (most common)
   - `Show.Name.S01E01.mp4`
   - `Show.Name.s01e01.mp4`
   - Case insensitive

2. **1x01 Format** (alternative)
   - `Show.Name.1x01.mp4`
   - `Show.Name.5X09.mp4`
   - Case insensitive

3. **101 Format** (compact)
   - `Show.Name.101.mp4` → Season 1, Episode 1
   - `Show.Name.509.mp4` → Season 5, Episode 9
   - First digit = season, last two digits = episode

## Troubleshooting

### "No results found for [series]"

- Try specifying title manually with `--title`
- Check TVDB to ensure the series exists
- Make sure the spelling is correct

### "No root folders configured in Sonarr"

- Open Sonarr web interface
- Go to Settings → Media Management → Root Folders
- Add at least one root folder

### "API key required"

- Make sure you've set `SONARR_API_KEY` environment variable
- Or use `--api-key` flag
- Verify the API key is correct in Sonarr settings

### "Could not determine season/episode from filename"

- Use `--parse` flag to see what was detected
- Specify manually with `--season` and `--episode` flags
- Ensure filename follows one of the supported formats

### File Already Exists

- The tool will skip if the file already exists in the target location
- Use `--move` flag if you want to remove the source file

## Advanced Options

### Custom Search

If auto-detection fails, you can search manually:

```python
uploader = SonarrUploader(api_url, api_key)

# Search TVDB
results = uploader.search_series("Breaking Bad")
for series in results:
    print(f"{series['title']} ({series.get('year')})")
```

### Check Library

```python
# Get all series in library
all_series = uploader.get_series()

# Find specific series
series = uploader.find_series_by_title("Breaking Bad")
if series:
    print(f"Found: {series['title']} (ID: {series['id']})")
    
    # Get episodes for this series
    episodes = uploader.get_episodes(series['id'])
    for ep in episodes:
        print(f"S{ep['seasonNumber']:02d}E{ep['episodeNumber']:02d}: {ep['title']}")
```

### Manual Episode Import

```python
# For more control over the import process
series = uploader.find_series_by_title("Breaking Bad")

result = uploader.import_episode(
    file_path="/path/to/episode.mp4",
    series_id=series['id'],
    copy_files=True
)
```

## Season Folder Structure

Sonarr organizes episodes like this:

```
/TV Shows/
  Breaking Bad/
    Season 01/
      Breaking Bad - S01E01.mp4
      Breaking Bad - S01E02.mp4
    Season 02/
      Breaking Bad - S02E01.mp4
  Game of Thrones/
    Season 01/
      Game of Thrones - S01E01.mkv
```

The tool automatically:
- Creates the series folder if it doesn't exist
- Creates the season folder (Season 01, Season 02, etc.)
- Renames the file to match Sonarr's naming convention

## Notes

- The tool requires an active Sonarr instance
- Files are copied by default (use `--move` to move instead)
- Automatic TVDB lookup requires internet connection
- Quality profile 1 is used by default unless specified
- Season folders are created automatically if enabled in Sonarr settings
