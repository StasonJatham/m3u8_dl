from typing import Optional
from fastapi import APIRouter, BackgroundTasks, Depends, Form, WebSocket, WebSocketDisconnect, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db, Download, Settings
from ..services.download_service import process_download, DownloadRequest, update_status
from ..services.websocket_manager import manager

router = APIRouter(prefix="/api")

@router.post("/download")
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
        tmdb_id=req.tmdbId,
        tvdb_id=req.tvdbId,
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

@router.get("/history")
async def get_history(db: Session = Depends(get_db)):
    downloads = db.query(Download).order_by(Download.created_at.desc()).limit(50).all()
    return downloads

@router.get("/settings")
async def get_settings(db: Session = Depends(get_db)):
    return db.query(Settings).first()

@router.post("/settings")
async def update_settings(settings: dict, db: Session = Depends(get_db)):
    db_settings = db.query(Settings).first()
    for key, value in settings.items():
        if hasattr(db_settings, key):
            setattr(db_settings, key, value)
    db.commit()
    return {"status": "updated"}

@router.post("/retry/{download_id}")
async def retry_download(download_id: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    download = db.query(Download).filter(Download.id == download_id).first()
    if not download:
        raise HTTPException(status_code=404, detail="Download not found")
    
    # Reset status
    download.status = "queued"
    download.progress = "0%"
    download.current_task = "Retrying..."
    download.error_message = None
    db.commit()
    
    # Re-create request object
    req = DownloadRequest(
        url=download.url,
        type=download.type,
        title=download.title,
        year=download.year,
        season=download.season,
        episode=download.episode
    )
    
    background_tasks.add_task(process_download, req, download.id)
    
    await manager.broadcast({
        "type": "update",
        "id": download.id,
        "status": "queued",
        "progress": "0%",
        "task": "Retrying...",
        "error": None
    })
    
    return {"status": "retrying"}

@router.post("/cancel/{download_id}")
async def cancel_download(download_id: int, db: Session = Depends(get_db)):
    # Note: This only updates the DB status. 
    # True cancellation of running threads/subprocesses is complex and not fully implemented here.
    download = db.query(Download).filter(Download.id == download_id).first()
    if not download:
        raise HTTPException(status_code=404, detail="Download not found")
        
    if download.status in ["completed", "failed"]:
        return {"status": "ignored", "message": "Download already finished"}

    download.status = "failed"
    download.error_message = "Cancelled by user"
    db.commit()
    
    await manager.broadcast({
        "type": "update",
        "id": download.id,
        "status": "failed",
        "progress": download.progress,
        "task": "Cancelled",
        "error": "Cancelled by user"
    })
    
    return {"status": "cancelled"}
