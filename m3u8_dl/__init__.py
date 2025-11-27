"""HLS Stream Downloader - Download HLS video streams."""

from .downloader import download_video
from .integrations.radarr import RadarrUploader
from .integrations.sonarr import SonarrUploader

__version__ = "1.0.0"
__all__ = ["download_video", "RadarrUploader", "SonarrUploader"]
