import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    # Server settings
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", "8000"))
    
    # Radarr settings
    RADARR_URL = os.getenv("RADARR_URL", "http://localhost:7878")
    RADARR_API_KEY = os.getenv("RADARR_API_KEY", "")
    RADARR_QUALITY_PROFILE_ID = int(os.getenv("RADARR_QUALITY_PROFILE_ID", "1"))
    
    # Sonarr settings
    SONARR_URL = os.getenv("SONARR_URL", "http://localhost:8989")
    SONARR_API_KEY = os.getenv("SONARR_API_KEY", "")
    SONARR_QUALITY_PROFILE_ID = int(os.getenv("SONARR_QUALITY_PROFILE_ID", "1"))
    
    # Download settings
    DOWNLOAD_DIR = os.getenv("DOWNLOAD_DIR", "./downloads")
    
    # Browser settings
    HEADLESS = os.getenv("HEADLESS", "true").lower() == "true"

config = Config()
