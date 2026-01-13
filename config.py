"""
Configuration for Dependency Grapher
"""
import os
from pathlib import Path
from typing import Set

class Config:
    """Base configuration"""
    
    # Paths
    BASE_DIR = Path(__file__).parent
    TEMP_DIR = BASE_DIR / "temp"
    CACHE_DIR = BASE_DIR / "cache"
    
    # MongoDB
    MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
    DATABASE_NAME = os.getenv("DATABASE_NAME", "dependency_grapher")
    
    # Analysis settings
    MAX_FILE_SIZE = 1024 * 1024  # 1MB - קבצים גדולים יותר ידלגו
    SUPPORTED_EXTENSIONS = {".py"}
    
    # Directories to skip
    SKIP_DIRS: Set[str] = {
        "__pycache__",
        ".git",
        ".venv",
        "venv",
        "env",
        "node_modules",
        ".pytest_cache",
        ".mypy_cache",
        "htmlcov",
        "dist",
        "build",
        "*.egg-info"
    }
    
    # Files to skip
    SKIP_FILES: Set[str] = {
        "setup.py",
        "conftest.py"
    }
    
    # Graph settings
    MAX_DEPTH = 10  # עומק מקסימלי לחיפוש תלויות
    
    # Cache settings
    CACHE_TTL = 3600 * 24  # 24 hours
    
    # Analysis thresholds
    HIGH_RISK_THRESHOLD = 10  # מספר תלויות שמגדיר "סיכון גבוה"
    COMPLEX_FILE_LINES = 500  # קובץ נחשב מורכב מעל זה
    
    @classmethod
    def ensure_dirs(cls):
        """Create necessary directories"""
        cls.TEMP_DIR.mkdir(exist_ok=True)
        cls.CACHE_DIR.mkdir(exist_ok=True)


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    CACHE_TTL = 60  # 1 minute cache in dev


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB in production


# Current config
config = DevelopmentConfig if os.getenv("FLASK_ENV") == "development" else ProductionConfig
