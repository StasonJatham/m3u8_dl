from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles

from .logging_config import setup_logging
from .database import init_db, SessionLocal, Download
from .routers import api, views
from .services.websocket_manager import manager

# Setup logging
logger = setup_logging(verbose=True)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Server starting up...")
    init_db()
    
    # Reset interrupted downloads
    db = SessionLocal()
    try:
        interrupted = db.query(Download).filter(Download.status.in_(["downloading", "importing"])).all()
        for download in interrupted:
            logger.warning(f"Marking interrupted download {download.id} as failed")
            download.status = "failed"
            download.error_message = "Server restarted during processing"
        db.commit()
    except Exception as e:
        logger.error(f"Error resetting downloads: {e}")
    finally:
        db.close()
        
    yield
    # Shutdown
    logger.info("Server shutting down...")

app = FastAPI(title="m3u8-dl Server", lifespan=lifespan)

# Mount static files
static_dir = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Include routers
app.include_router(api.router)
app.include_router(views.router)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

if __name__ == "__main__":
    import asyncio
    import signal
    from hypercorn.config import Config
    from hypercorn.asyncio import serve
    from .config import config

    hyper_config = Config()
    hyper_config.bind = [f"{config.HOST}:{config.PORT}"]
    hyper_config.accesslog = "-"
    hyper_config.errorlog = "-"
    
    # Hypercorn supports HTTP/2 and WebSockets over HTTP/2 by default
    # No SSL configured as per request (h2c will be used if client supports it)
    
    # Setup graceful shutdown
    shutdown_event = asyncio.Event()
    
    def _signal_handler(*args):
        shutdown_event.set()

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.add_signal_handler(signal.SIGINT, _signal_handler)
    loop.add_signal_handler(signal.SIGTERM, _signal_handler)

    try:
        loop.run_until_complete(serve(app, hyper_config, shutdown_trigger=shutdown_event.wait))
    except KeyboardInterrupt:
        pass
    finally:
        loop.close()
