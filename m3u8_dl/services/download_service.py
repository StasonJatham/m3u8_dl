import logging
import os
import glob
from typing import Optional
from sqlalchemy.orm import Session
from pydantic import BaseModel

from ..database import SessionLocal, Download, Settings
from ..radarr_uploader import RadarrUploader
from ..sonarr_uploader import SonarrUploader
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
            await update_status(db, download_id, "failed", error="Downloaded file not found")
            return
            
        downloaded_file = files[0]
        logger.info(f"File downloaded: {downloaded_file}")
        
        # Update DB with file path
        download = db.query(Download).filter(Download.id == download_id).first()
        if download:
            download.file_path = downloaded_file
            db.commit()

        await update_status(db, download_id, "importing", "80%", "Importing to library...")

        if req.type == 'movie':
            logger.info("Importing to Radarr...")
            radarr.upload_and_import(
                file_path=downloaded_file,
                title=req.title,
                year=req.year,
                quality_profile_id=settings.radarr_quality_profile_id
            )
        elif req.type == 'series':
            logger.info("Importing to Sonarr...")
            sonarr.upload_and_import(
                file_path=downloaded_file,
                title=req.title,
                season=req.season,
                episode=req.episode,
                quality_profile_id=settings.sonarr_quality_profile_id
            )
            
        await update_status(db, download_id, "completed", "100%", "Completed successfully")
            
    except Exception as e:
        logger.exception(f"Error processing download: {e}")
        await update_status(db, download_id, "failed", error=str(e))
    finally:
        db.close()
