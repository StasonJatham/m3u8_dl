from datetime import datetime
from typing import Optional
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

SQLALCHEMY_DATABASE_URL = "sqlite:///./m3u8_dl.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class Settings(Base):
    __tablename__ = "settings"

    id = Column(Integer, primary_key=True, index=True)
    # Radarr
    radarr_url = Column(String, default="http://localhost:7878")
    radarr_api_key = Column(String, default="")
    radarr_quality_profile_id = Column(Integer, default=1)
    radarr_root_folder = Column(String, default="")
    
    # Sonarr
    sonarr_url = Column(String, default="http://localhost:8989")
    sonarr_api_key = Column(String, default="")
    sonarr_quality_profile_id = Column(Integer, default=1)
    sonarr_root_folder = Column(String, default="")
    
    # General
    download_dir = Column(String, default="./downloads")
    concurrent_downloads = Column(Integer, default=1)

class Download(Base):
    __tablename__ = "downloads"

    id = Column(Integer, primary_key=True, index=True)
    url = Column(String)
    type = Column(String) # movie or series
    title = Column(String, nullable=True)
    year = Column(Integer, nullable=True)
    season = Column(Integer, nullable=True)
    episode = Column(Integer, nullable=True)
    tmdb_id = Column(Integer, nullable=True)
    tvdb_id = Column(Integer, nullable=True)
    
    status = Column(String, default="queued") # queued, downloading, importing, completed, failed
    progress = Column(String, default="0%")
    current_task = Column(String, default="Queued")
    error_message = Column(Text, nullable=True)
    
    file_path = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

def init_db():
    Base.metadata.create_all(bind=engine)
    
    # Create default settings if not exists
    db = SessionLocal()
    if not db.query(Settings).first():
        default_settings = Settings()
        db.add(default_settings)
        db.commit()
    db.close()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
