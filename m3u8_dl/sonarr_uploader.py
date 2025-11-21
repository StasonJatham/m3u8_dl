"""Sonarr uploader for automatic TV show import and indexing."""

import re
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests


class SonarrUploader:
    """Upload and import TV shows to Sonarr."""

    def __init__(self, api_url: str, api_key: str) -> None:
        """Initialize Sonarr uploader.
        
        Args:
            api_url: Sonarr API URL (e.g., http://localhost:8989)
            api_key: Sonarr API key
        """
        self.api_url = api_url.rstrip('/')
        self.api_key = api_key
        self.headers = {
            'X-Api-Key': api_key,
            'Content-Type': 'application/json'
        }

    def _get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """Make GET request to Sonarr API."""
        url = f"{self.api_url}/api/v3/{endpoint}"
        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        return response.json()

    def _post(self, endpoint: str, data: Dict[str, Any]) -> Any:
        """Make POST request to Sonarr API."""
        url = f"{self.api_url}/api/v3/{endpoint}"
        response = requests.post(url, headers=self.headers, json=data)
        response.raise_for_status()
        return response.json()

    def search_series(self, title: str) -> List[Dict[str, Any]]:
        """Search for a TV series in Sonarr's lookup.
        
        Args:
            title: Series title to search for
            
        Returns:
            List of matching series from TVDB
        """
        return self._get('series/lookup', params={'term': title})

    def get_root_folders(self) -> List[Dict[str, Any]]:
        """Get configured root folders in Sonarr."""
        return self._get('rootfolder')

    def get_quality_profiles(self) -> List[Dict[str, Any]]:
        """Get quality profiles configured in Sonarr."""
        return self._get('qualityprofile')

    def add_series(
        self,
        tvdb_id: int,
        title: str,
        root_folder_path: str,
        quality_profile_id: int = 1,
        season_folder: bool = True,
        monitored: bool = True,
        search_for_missing: bool = False
    ) -> Dict[str, Any]:
        """Add a TV series to Sonarr library.
        
        Args:
            tvdb_id: TVDB ID of the series
            title: Series title
            root_folder_path: Root folder path for the series
            quality_profile_id: Quality profile ID (default: 1)
            season_folder: Whether to use season folders
            monitored: Whether to monitor the series
            search_for_missing: Whether to search for missing episodes
            
        Returns:
            Added series data
        """
        data = {
            'tvdbId': tvdb_id,
            'title': title,
            'rootFolderPath': root_folder_path,
            'qualityProfileId': quality_profile_id,
            'seasonFolder': season_folder,
            'monitored': monitored,
            'addOptions': {
                'searchForMissingEpisodes': search_for_missing
            }
        }
        return self._post('series', data)

    def get_series(self) -> List[Dict[str, Any]]:
        """Get all series in Sonarr library."""
        return self._get('series')

    def find_series_by_title(self, title: str) -> Optional[Dict[str, Any]]:
        """Find a series in Sonarr library by title.
        
        Args:
            title: Series title to search for
            
        Returns:
            Series data if found, None otherwise
        """
        all_series = self.get_series()
        title_lower = title.lower()
        for series in all_series:
            if series['title'].lower() == title_lower:
                return series
        return None

    def get_episodes(self, series_id: int) -> List[Dict[str, Any]]:
        """Get all episodes for a series.
        
        Args:
            series_id: Series ID
            
        Returns:
            List of episodes
        """
        return self._get('episode', params={'seriesId': series_id})

    def trigger_manual_import(
        self,
        folder_path: str,
        series_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Trigger manual import scan for a folder.
        
        Args:
            folder_path: Path to folder containing episode file
            series_id: Optional series ID to associate with
            
        Returns:
            List of importable files found
        """
        params = {
            'folder': folder_path,
            'filterExistingFiles': True
        }
        if series_id:
            params['seriesId'] = series_id
        
        return self._get('manualimport', params=params)

    def import_episode(
        self,
        file_path: str,
        series_id: int,
        copy_files: bool = True
    ) -> Dict[str, Any]:
        """Import an episode file into Sonarr.
        
        Args:
            file_path: Path to the episode file
            series_id: Series ID to import to
            copy_files: Whether to copy (True) or move (False) files
            
        Returns:
            Import result
        """
        files = self.trigger_manual_import(str(Path(file_path).parent), series_id)
        
        if not files:
            raise ValueError(f"No importable files found at {file_path}")
        
        target_file = None
        for file_info in files:
            if Path(file_info['path']).name == Path(file_path).name:
                target_file = file_info
                break
        
        if not target_file:
            raise ValueError(f"File {file_path} not found in import scan results")
        
        import_data = {
            'files': [{
                'path': target_file['path'],
                'folderName': str(Path(file_path).parent),
                'seriesId': series_id,
                'episodeIds': target_file.get('episodeIds', []),
                'quality': target_file.get('quality', {'quality': {'id': 0}}),
                'qualityWeight': 1
            }],
            'importMode': 'copy' if copy_files else 'move'
        }
        
        return self._post('command', {
            'name': 'ManualImport',
            'files': import_data['files'],
            'importMode': import_data['importMode']
        })

    def upload_and_import(
        self,
        file_path: str,
        title: Optional[str] = None,
        season: Optional[int] = None,
        episode: Optional[int] = None,
        auto_search: bool = True,
        copy_files: bool = True,
        quality_profile_id: int = 1
    ) -> Dict[str, Any]:
        """Upload an episode file and automatically import it to Sonarr.
        
        This handles the full workflow:
        1. Parse filename for series/season/episode info
        2. Search for series (or use existing in library)
        3. Add to library if not present
        4. Copy file to Sonarr's root folder with proper naming
        5. Trigger manual import
        
        Args:
            file_path: Path to the episode file
            title: Series title (if None, extracted from filename)
            season: Season number (if None, extracted from filename)
            episode: Episode number (if None, extracted from filename)
            auto_search: Whether to auto-search TVDB if not in library
            copy_files: Whether to copy (True) or move (False) files
            quality_profile_id: Quality profile ID to use
            
        Returns:
            Import result with series and import details
        """
        file_path = Path(file_path).resolve()
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        if title is None or season is None or episode is None:
            parsed = self._parse_episode_filename(file_path.name)
            if title is None:
                title = parsed['title']
            if season is None:
                season = parsed['season']
            if episode is None:
                episode = parsed['episode']
        
        if not title:
            raise ValueError("Could not determine series title from filename")
        if season is None or episode is None:
            raise ValueError("Could not determine season/episode from filename")
        
        print(f"Processing: {title} - S{season:02d}E{episode:02d}")
        
        series = self.find_series_by_title(title)
        
        if not series and auto_search:
            print(f"Searching TVDB for: {title}")
            results = self.search_series(title)
            
            if not results:
                raise ValueError(f"No results found for {title}")
            
            best_match = results[0]
            print(f"Found: {best_match['title']} ({best_match.get('year', 'N/A')})")
            
            root_folders = self.get_root_folders()
            if not root_folders:
                raise ValueError("No root folders configured in Sonarr")
            
            root_folder = root_folders[0]['path']
            
            print(f"Adding to Sonarr library...")
            series = self.add_series(
                tvdb_id=best_match['tvdbId'],
                title=best_match['title'],
                root_folder_path=root_folder,
                quality_profile_id=quality_profile_id,
                monitored=True,
                search_for_missing=False
            )
        
        if not series:
            raise ValueError(f"Series not found in library and auto_search is disabled")
        
        print(f"Series in library: {series['title']} (ID: {series['id']})")
        
        series_folder = Path(series['path'])
        if series.get('seasonFolder', True):
            season_folder = series_folder / f"Season {season:02d}"
        else:
            season_folder = series_folder
        
        season_folder.mkdir(parents=True, exist_ok=True)
        
        extension = file_path.suffix
        dest_filename = f"{series['title']} - S{season:02d}E{episode:02d}{extension}"
        dest_file = season_folder / dest_filename
        
        print(f"Copying to: {dest_file}")
        
        if copy_files:
            shutil.copy2(file_path, dest_file)
        else:
            shutil.move(str(file_path), dest_file)
        
        print("Triggering import...")
        result = self.import_episode(
            str(dest_file),
            series['id'],
            copy_files=False
        )
        
        print("✓ Import completed successfully!")
        
        return {
            'series': series,
            'season': season,
            'episode': episode,
            'import_result': result,
            'file_path': str(dest_file)
        }

    @staticmethod
    def _parse_episode_filename(filename: str) -> Dict[str, Any]:
        """Parse series title, season, and episode from filename.
        
        Supports formats:
        - S01E01 or s01e01
        - 1x01 or 1X01  
        - 101 (season 1, episode 1)
        """
        name = Path(filename).stem
        name_clean = name.replace('.', ' ').replace('_', ' ')
        
        season = None
        episode = None
        title = name_clean
        
        match = re.search(r'[Ss](\d{1,2})[Ee](\d{1,2})', name)
        if match:
            season = int(match.group(1))
            episode = int(match.group(2))
            title = name_clean[:match.start()].strip()
        
        if season is None:
            match = re.search(r'(\d{1,2})[xX](\d{1,2})', name)
            if match:
                season = int(match.group(1))
                episode = int(match.group(2))
                title = name_clean[:match.start()].strip()
        
        if season is None:
            match = re.search(r'\b(\d)(\d{2})\b', name)
            if match:
                season = int(match.group(1))
                episode = int(match.group(2))
                title = name_clean[:match.start()].strip()
        
        quality_patterns = [
            r'\b(1080p|720p|2160p|4k|BluRay|WEB-DL|WEBRip|HDRip|HDTV)\b',
            r'\[.*?\]',
            r'\(.*?\)'
        ]
        for pattern in quality_patterns:
            title = re.sub(pattern, '', title, flags=re.IGNORECASE)
        
        title = re.sub(r'\s+', ' ', title).strip()
        title = re.sub(r'[\s\-]+$', '', title)
        
        return {
            'title': title if title else None,
            'season': season,
            'episode': episode
        }
