import logging
import os
import glob
from typing import Optional
from sqlalchemy.orm import Session
from pydantic import BaseModel

from ..database import SessionLocal, Download, Settings
from ..integrations.radarr import RadarrUploader
from ..integrations.sonarr import SonarrUploader
from ..downloader import download_video
from ..video_downloader import download_direct
from .websocket_manager import manager

logger = logging.getLogger(__name__)

class DownloadRequest(BaseModel):
    url: str
    type: str  # 'movie', 'series', or 'direct'
    title: Optional[str] = None
    year: Optional[int] = None
    season: Optional[int] = None
    episode: Optional[int] = None
    tmdbId: Optional[int] = None
    tvdbId: Optional[int] = None

async def update_status(db: Session, download_id: int, status: str, progress: str = None, task: str = None, error: str = None):
    download = db.query(Download).filter(Download.id == download_id).first()
    if download:
        download.status = status
        if progress: download.progress = progress
        if task: download.current_task = task
        if error: download.error_message = error
        db.commit()
        
        await manager.broadcast({
            "type": "update",
            "id": download.id,
            "status": status,
            "progress": download.progress,
            "task": download.current_task,
            "error": error
        })

async def process_download(req: DownloadRequest, download_id: int):
    """Background task to process the download and import."""
    logger.info(f"Processing download request: {req.url}")
    
    # Create a new DB session for this task
    db = SessionLocal()
    
    try:
        # Get settings
        settings = db.query(Settings).first()
        if not settings:
            # Fallback if settings are missing (shouldn't happen if init_db ran)
            logger.error("Settings not found in database")
            await update_status(db, download_id, "failed", error="Database settings missing")
            return

        # Initialize uploaders with DB settings
        radarr = RadarrUploader(settings.radarr_url, settings.radarr_api_key)
        sonarr = SonarrUploader(settings.sonarr_url, settings.sonarr_api_key)
        
        await update_status(db, download_id, "downloading", "0%", "Starting download...")
        
        if req.type == 'direct':
            download_dir = settings.download_dir
            os.makedirs(download_dir, exist_ok=True)
            
            await update_status(db, download_id, "downloading", "10%", "Downloading with yt-dlp...")
            
            # For direct download, we might want to pass a custom filename if title is provided
            # But download_direct currently takes output_dir. 
            # Let's stick to the existing logic for now.
            success = await download_direct(req.url, download_dir)
            
            if success:
                await update_status(db, download_id, "completed", "100%", "Download completed")
            else:
                await update_status(db, download_id, "failed", error="Download failed")
            return

        temp_filename = f"download_{req.type}_{req.tmdbId or req.tvdbId or 'unknown'}_{download_id}"
        
        download_dir = settings.download_dir
        os.makedirs(download_dir, exist_ok=True)
        output_path = f"{download_dir}/{temp_filename}"
        
        await update_status(db, download_id, "downloading", "10%", "Downloading video...")
        
        # We need to capture logs/progress from download_video if possible, 
        # but for now we just wait.
        success = await download_video(req.url, verbose=True, custom_filename=output_path)
        
        if not success:
            await update_status(db, download_id, "failed", error="Download failed")
            return

        files = glob.glob(f"{output_path}.*")
        if not files:
            await update_status(db, download_id, "failed", error="Output file not found")
            return
            
        final_path = files[0]
        
        # Update DB with file path
        download = db.query(Download).filter(Download.id == download_id).first()
        if download:
            download.file_path = final_path
            db.commit()
        
        await update_status(db, download_id, "completed", "100%", "Download completed")
        
        # Auto-index if configured (logic can be added here or triggered manually)
        # For now, we just leave it as completed.

    except Exception as e:
        logger.exception("Error processing download")
        await update_status(db, download_id, "failed", error=str(e))
    finally:
        db.close()

def delete_download_files(file_path: str):
    """Delete downloaded files."""
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"Deleted file: {file_path}")
    except Exception as e:
        logger.error(f"Error deleting file {file_path}: {e}")

async def index_download(download_id: int):
    """Index a completed download to Radarr/Sonarr."""
    db = SessionLocal()
    try:
        download = db.query(Download).filter(Download.id == download_id).first()
        settings = db.query(Settings).first()
        
        if not download or not download.file_path or not os.path.exists(download.file_path):
            await update_status(db, download_id, "failed", error="File not found for indexing")
            return
            
        await update_status(db, download_id, "importing", task="Indexing...")
        
        if download.type == 'movie':
            radarr = RadarrUploader(settings.radarr_url, settings.radarr_api_key)
            radarr.upload_and_import(
                download.file_path,
                title=download.title,
                year=download.year,
                quality_profile_id=settings.radarr_quality_profile_id,
                copy_files=True # Keep original for seeding/viewing
            )
        elif download.type == 'series':
            sonarr = SonarrUploader(settings.sonarr_url, settings.sonarr_api_key)
            sonarr.upload_and_import(
                download.file_path,
                title=download.title,
                season=download.season,
                episode=download.episode,
                quality_profile_id=settings.sonarr_quality_profile_id,
                copy_files=True
            )
            
        await update_status(db, download_id, "completed", task="Indexed successfully")
        
    except Exception as e:
        logger.exception("Error indexing download")
        await update_status(db, download_id, "completed", error=f"Indexing failed: {str(e)}") # Keep as completed, just log error
    finally:
        db.close()
