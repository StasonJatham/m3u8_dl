"""Radarr uploader for automatic movie import and indexing."""

import os
import re
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests


class RadarrUploader:
    """Upload and import movies to Radarr."""

    def __init__(self, api_url: str, api_key: str) -> None:
        """Initialize Radarr uploader.
        
        Args:
            api_url: Radarr API URL (e.g., http://localhost:7878)
            api_key: Radarr API key
        """
        self.api_url = api_url.rstrip('/')
        self.api_key = api_key
        self.headers = {
            'X-Api-Key': api_key,
            'Content-Type': 'application/json'
        }

    def _get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """Make GET request to Radarr API."""
        url = f"{self.api_url}/api/v3/{endpoint}"
        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        return response.json()

    def _post(self, endpoint: str, data: Dict[str, Any]) -> Any:
        """Make POST request to Radarr API."""
        url = f"{self.api_url}/api/v3/{endpoint}"
        response = requests.post(url, headers=self.headers, json=data)
        response.raise_for_status()
        return response.json()

    def search_movie(self, title: str, year: Optional[int] = None) -> List[Dict[str, Any]]:
        """Search for a movie in Radarr's lookup.
        
        Args:
            title: Movie title to search for
            year: Optional year to narrow search
            
        Returns:
            List of matching movies from TMDB
        """
        query = f"{title} {year}" if year else title
        return self._get('movie/lookup', params={'term': query})

    def get_root_folders(self) -> List[Dict[str, Any]]:
        """Get configured root folders in Radarr."""
        return self._get('rootfolder')

    def get_quality_profiles(self) -> List[Dict[str, Any]]:
        """Get quality profiles configured in Radarr."""
        return self._get('qualityprofile')

    def add_movie(
        self,
        tmdb_id: int,
        title: str,
        year: int,
        root_folder_path: str,
        quality_profile_id: int = 1,
        monitored: bool = True,
        search_for_movie: bool = False
    ) -> Dict[str, Any]:
        """Add a movie to Radarr library.
        
        Args:
            tmdb_id: TMDB ID of the movie
            title: Movie title
            year: Movie year
            root_folder_path: Root folder path for the movie
            quality_profile_id: Quality profile ID (default: 1)
            monitored: Whether to monitor the movie
            search_for_movie: Whether to search for the movie after adding
            
        Returns:
            Added movie data
        """
        data = {
            'tmdbId': tmdb_id,
            'title': title,
            'year': year,
            'rootFolderPath': root_folder_path,
            'qualityProfileId': quality_profile_id,
            'monitored': monitored,
            'addOptions': {
                'searchForMovie': search_for_movie
            }
        }
        return self._post('movie', data)

    def get_movies(self) -> List[Dict[str, Any]]:
        """Get all movies in Radarr library."""
        return self._get('movie')

    def find_movie_by_title(self, title: str, year: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """Find a movie in Radarr library by title.
        
        Args:
            title: Movie title to search for
            year: Optional year to narrow search
            
        Returns:
            Movie data if found, None otherwise
        """
        movies = self.get_movies()
        for movie in movies:
            if movie['title'].lower() == title.lower():
                if year is None or movie.get('year') == year:
                    return movie
        return None

    def trigger_manual_import(
        self,
        folder_path: str,
        movie_id: Optional[int] = None,
        quality_profile_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Trigger manual import scan for a folder.
        
        Args:
            folder_path: Path to folder containing movie file
            movie_id: Optional movie ID to associate with
            quality_profile_id: Optional quality profile ID
            
        Returns:
            List of importable files found
        """
        params = {
            'folder': folder_path,
            'filterExistingFiles': True
        }
        if movie_id:
            params['movieId'] = movie_id
        
        return self._get('manualimport', params=params)

    def import_movie(
        self,
        file_path: str,
        movie_id: int,
        quality_profile_id: int = 1,
        copy_files: bool = True
    ) -> Dict[str, Any]:
        """Import a movie file into Radarr.
        
        Args:
            file_path: Path to the movie file
            movie_id: Movie ID to import to
            quality_profile_id: Quality profile ID
            copy_files: Whether to copy (True) or move (False) files
            
        Returns:
            Import result
        """
        files = self.trigger_manual_import(str(Path(file_path).parent), movie_id, quality_profile_id)
        
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
                'movieId': movie_id,
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

    ) -> Dict[str, Any]:
        """Upload a movie file and automatically import it to Radarr.
        
        Handles the full workflow: search TMDB, add to library, copy file, trigger import.
        
        Args:
            file_path: Path to the movie file
            title: Movie title (auto-detected from filename if None)
            year: Movie year (auto-detected from filename if None)
            auto_search: Whether to auto-search TMDB if not in library
            copy_files: Whether to copy (True) or move (False) files
            quality_profile_id: Quality profile ID to use
            
        Returns:
            Import result with movie and import details
        \"\"\"\n        file_path = Path(file_path).resolve()
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        if title is None:
            title = self._extract_title_from_filename(file_path.name)
        
        if year is None:
            year = self._extract_year_from_filename(file_path.name)
        
        print(f"Processing: {title} ({year or 'unknown year'})")
        
        movie = self.find_movie_by_title(title, year)
        
        if not movie and auto_search:
            print(f"Searching TMDB for: {title}")
            results = self.search_movie(title, year)
            
            if not results:
                raise ValueError(f"No results found for {title}")
            
            best_match = results[0]
            print(f"Found: {best_match['title']} ({best_match.get('year', 'N/A')})")
            
            root_folders = self.get_root_folders()
            if not root_folders:
                raise ValueError("No root folders configured in Radarr")
            
            root_folder = root_folders[0]['path']
            
            print(f"Adding to Radarr library...")
            movie = self.add_movie(
                tmdb_id=best_match['tmdbId'],
                title=best_match['title'],
                year=best_match.get('year', 0),
                root_folder_path=root_folder,
                quality_profile_id=quality_profile_id,
                monitored=True,
                search_for_movie=False
            )
        
        if not movie:
            raise ValueError(f"Movie not found in library and auto_search is disabled")
        
        print(f"Movie in library: {movie['title']} (ID: {movie['id']})")
        
        movie_folder = Path(movie['path'])
        movie_folder.mkdir(parents=True, exist_ok=True)
        
        dest_file = movie_folder / file_path.name
        print(f"Copying to: {dest_file}")
        
        if copy_files:
            shutil.copy2(file_path, dest_file)
        else:
            shutil.move(str(file_path), dest_file)
        
        print("Triggering import...")
        result = self.import_movie(
            str(dest_file),
            movie['id'],
            quality_profile_id,
            copy_files=False
        )
        
        print("✓ Import completed successfully!")
        
        return {
            'movie': movie,
            'import_result': result,
            'file_path': str(dest_file)
        }

    @staticmethod
    def _extract_title_from_filename(filename: str) -> str:
        """Extract movie title from filename."""
        name = Path(filename).stem
        name = name.replace('.', ' ').replace('_', ' ')
        
        year_match = re.search(r'\b(19|20)\d{2}\b', name)
        if year_match:
            name = name[:year_match.start()].strip()
        
        quality_patterns = [
            r'\b(1080p|720p|2160p|4k|BluRay|WEB-DL|WEBRip|HDRip)\b',
            r'\[.*?\]',
            r'\(.*?\)'
        ]
        for pattern in quality_patterns:
            name = re.sub(pattern, '', name, flags=re.IGNORECASE)
        
        return name.strip()

    @staticmethod
    def _extract_year_from_filename(filename: str) -> Optional[int]:
        """Extract year from filename."""
        year_match = re.search(r'\b(19|20)\d{2}\b', filename)
        if year_match:
            return int(year_match.group())
        return None
