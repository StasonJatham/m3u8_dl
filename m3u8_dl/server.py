import asyncio
import logging
import json
from typing import Optional, List
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, BackgroundTasks, HTTPException, Request, Form, WebSocket, WebSocketDisconnect, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from sqlalchemy.orm import Session

from .config import config
from .downloader import download_video
from .radarr_uploader import RadarrUploader
from .sonarr_uploader import SonarrUploader
from .logging_config import setup_logging
from .database import init_db, get_db, Download, Settings

# Setup logging
logger = setup_logging(verbose=True)

# WebSocket Connection Manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                pass

manager = ConnectionManager()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Server starting up...")
    init_db()
    yield
    # Shutdown
    logger.info("Server shutting down...")

app = FastAPI(title="m3u8-dl Server", lifespan=lifespan)

class DownloadRequest(BaseModel):
    url: str
    type: str  # 'movie' or 'series'
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
    from .database import SessionLocal
    db = SessionLocal()
    
    try:
        # Get settings
        settings = db.query(Settings).first()
        
        # Initialize uploaders with DB settings
        radarr = RadarrUploader(settings.radarr_url, settings.radarr_api_key)
        sonarr = SonarrUploader(settings.sonarr_url, settings.sonarr_api_key)
        
        await update_status(db, download_id, "downloading", "0%", "Starting download...")
        
        temp_filename = f"download_{req.type}_{req.tmdbId or req.tvdbId or 'unknown'}_{download_id}"
        
        import os
        import glob
        
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

@app.post("/api/download")
async def queue_download(req: DownloadRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Queue a download task."""
    # Create DB entry
    db_download = Download(
        url=req.url,
        type=req.type,
        title=req.title or "Unknown",
        year=req.year,
        season=req.season,
        episode=req.episode,
        status="queued"
    )
    db.add(db_download)
    db.commit()
    db.refresh(db_download)
    
    background_tasks.add_task(process_download, req, db_download.id)
    
    # Broadcast new download
    await manager.broadcast({
        "type": "new",
        "download": {
            "id": db_download.id,
            "title": db_download.title,
            "status": db_download.status,
            "type": db_download.type,
            "progress": "0%",
            "task": "Queued"
        }
    })
    
    return {"status": "queued", "id": db_download.id}

@app.get("/api/history")
async def get_history(db: Session = Depends(get_db)):
    downloads = db.query(Download).order_by(Download.created_at.desc()).limit(50).all()
    return downloads

@app.get("/api/settings")
async def get_settings(db: Session = Depends(get_db)):
    return db.query(Settings).first()

@app.post("/api/settings")
async def update_settings(settings: dict, db: Session = Depends(get_db)):
    db_settings = db.query(Settings).first()
    for key, value in settings.items():
        if hasattr(db_settings, key):
            setattr(db_settings, key, value)
    db.commit()
    return {"status": "updated"}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

import os
from pathlib import Path

# Setup templates
templates_dir = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=str(templates_dir))

@app.get("/", response_class=HTMLResponse)
async def index(request: Request, db: Session = Depends(get_db)):
    """Main UI."""
    downloads = db.query(Download).order_by(Download.created_at.desc()).limit(20).all()
    settings = db.query(Settings).first()
    return templates.TemplateResponse("index.html", {
        "request": request, 
        "downloads": downloads,
        "settings": settings
    })

@app.post("/submit-form")
async def submit_form(
    request: Request,
    background_tasks: BackgroundTasks,
    url: str = Form(...),
    type: str = Form(...),
    title: Optional[str] = Form(None),
    year: Optional[int] = Form(None),
    season: Optional[int] = Form(None),
    episode: Optional[int] = Form(None),
    db: Session = Depends(get_db)
):
    req = DownloadRequest(
        url=url,
        type=type,
        title=title,
        year=year,
        season=season,
        episode=episode
    )
    
    # Create DB entry
    db_download = Download(
        url=req.url,
        type=req.type,
        title=req.title or "Unknown",
        year=req.year,
        season=req.season,
        episode=req.episode,
        status="queued"
    )
    db.add(db_download)
    db.commit()
    db.refresh(db_download)
    
    background_tasks.add_task(process_download, req, db_download.id)
    
    # Broadcast new download
    await manager.broadcast({
        "type": "new",
        "download": {
            "id": db_download.id,
            "title": db_download.title,
            "status": db_download.status,
            "type": db_download.type,
            "progress": "0%",
            "task": "Queued"
        }
    })
    
    # Redirect back to home
    downloads = db.query(Download).order_by(Download.created_at.desc()).limit(20).all()
    settings = db.query(Settings).first()
    return templates.TemplateResponse("index.html", {
        "request": request,
        "message": f"Download queued for {title or url}",
        "downloads": downloads,
        "settings": settings
    })

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=config.HOST, port=config.PORT)
