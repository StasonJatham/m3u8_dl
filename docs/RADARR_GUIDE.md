# Radarr Upload Tool - Usage Guide

## Overview

The Radarr Upload Tool automatically imports movie files into your Radarr library with proper metadata from TMDB.

## Features

- **Automatic TMDB Lookup**: Searches The Movie Database for metadata
- **Smart Filename Parsing**: Extracts title and year from filenames
- **Library Integration**: Adds movies to Radarr if not already present
- **Organized Import**: Properly structures files in Radarr's folder format
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
export RADARR_URL=http://localhost:7878
export RADARR_API_KEY=your_api_key_here
```

To find your API key:
1. Open Radarr web interface
2. Go to Settings → General → Security
3. Copy the API Key

### Method 2: Command Line Flags

```bash
python radarr_upload.py --url http://localhost:7878 --api-key your_api_key movie.mp4
```

## Usage Examples

### Basic Upload (Auto-detect from filename)

```bash
python radarr_upload.py "The Matrix 1999.mp4"
```

This will:
1. Extract title "The Matrix" and year 1999 from filename
2. Search TMDB for the movie
3. Add to Radarr library if not present
4. Copy file to Radarr's organized folder structure
5. Trigger import

### Specify Title and Year Manually

```bash
python radarr_upload.py movie.mp4 --title "The Matrix" --year 1999
```

### Move Instead of Copy

```bash
python radarr_upload.py movie.mp4 --move
```

### Use Custom Quality Profile

```bash
# First, list available profiles
python radarr_upload.py --list-profiles

# Then use the desired profile ID
python radarr_upload.py movie.mp4 --quality-profile 2
```

### List Root Folders

```bash
python radarr_upload.py --list-folders
```

## Workflow Integration

### Complete Download and Upload

```bash
# Step 1: Download video
python -m m3u8_dl https://example.com/watch/1590407 -n "The Matrix 1999"

# Step 2: Upload to Radarr
python radarr_upload.py "The Matrix 1999.mp4"
```

### Batch Upload

```bash
# Upload all videos in a directory
for file in *.mp4; do
    python radarr_upload.py "$file"
done
```

## Python API Usage

```python
from m3u8_dl import RadarrUploader

# Initialize uploader
uploader = RadarrUploader(
    api_url="http://localhost:7878",
    api_key="your_api_key"
)

# Upload and import a file
result = uploader.upload_and_import(
    file_path="The Matrix 1999.mp4",
    title="The Matrix",  # Optional, auto-detected if not provided
    year=1999,           # Optional, auto-detected if not provided
    copy_files=True,     # False to move instead of copy
    quality_profile_id=1
)

print(f"Imported: {result['movie']['title']}")
print(f"Location: {result['file_path']}")
```

## Filename Auto-Detection

The tool automatically extracts title and year from filenames:

| Filename | Detected Title | Detected Year |
|----------|---------------|---------------|
| `The.Matrix.1999.1080p.BluRay.mp4` | The Matrix | 1999 |
| `Inception (2010) [1080p].mp4` | Inception | 2010 |
| `The_Dark_Knight_2008_WEB-DL.mkv` | The Dark Knight | 2008 |

## Troubleshooting

### "No results found for [title]"

- Try specifying title and year manually with `--title` and `--year`
- Check TMDB to ensure the movie exists
- Make sure the spelling is correct

### "No root folders configured in Radarr"

- Open Radarr web interface
- Go to Settings → Media Management → Root Folders
- Add at least one root folder

### "API key required"

- Make sure you've set `RADARR_API_KEY` environment variable
- Or use `--api-key` flag
- Verify the API key is correct in Radarr settings

### File Already Exists

- The tool will skip if the file already exists in the target location
- Use `--move` flag if you want to remove the source file

## Advanced Options

### Custom Search

If auto-detection fails, you can search manually:

```python
uploader = RadarrUploader(api_url, api_key)

# Search TMDB
results = uploader.search_movie("The Matrix", 1999)
for movie in results:
    print(f"{movie['title']} ({movie.get('year')})")
```

### Check Library

```python
# Get all movies in library
movies = uploader.get_movies()

# Find specific movie
movie = uploader.find_movie_by_title("The Matrix", 1999)
if movie:
    print(f"Found: {movie['title']} (ID: {movie['id']})")
```

## Notes

- The tool requires an active Radarr instance
- Files are copied by default (use `--move` to move instead)
- Automatic TMDB lookup requires internet connection
- Quality profile 1 is used by default unless specified
