from typing import Optional
from pathlib import Path
from fastapi import APIRouter, Request, Depends, Form, BackgroundTasks
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from ..database import get_db, Download, Settings
from ..services.download_service import process_download, DownloadRequest, manager

router = APIRouter()

# Setup templates
templates_dir = Path(__file__).parent.parent / "templates"
templates = Jinja2Templates(directory=str(templates_dir))

@router.get("/", response_class=HTMLResponse)
async def index(request: Request, db: Session = Depends(get_db)):
    """Main UI."""
    downloads = db.query(Download).order_by(Download.created_at.desc()).limit(20).all()
    settings = db.query(Settings).first()
    return templates.TemplateResponse("index.html", {
        "request": request, 
        "downloads": downloads,
        "settings": settings
    })

@router.post("/submit-form")
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
