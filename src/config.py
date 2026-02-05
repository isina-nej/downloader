"""Configuration management for Telegram File Downloader."""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config:
    """Application configuration class."""

    # Telegram
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_CHAT_ID: int = int(os.getenv("TELEGRAM_CHAT_ID", "0"))

    # Server
    STORAGE_PATH: Path = Path(os.getenv("STORAGE_PATH", "./storage"))
    MAX_FILE_SIZE: int = int(os.getenv("MAX_FILE_SIZE", "2147483648"))  # 2GB
    DOWNLOAD_URL_BASE: str = os.getenv("DOWNLOAD_URL_BASE", "https://yourdomain.com")
    SERVER_HOST: str = os.getenv("SERVER_HOST", "0.0.0.0")
    SERVER_PORT: int = int(os.getenv("SERVER_PORT", "8000"))

    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./telegram_downloader.db")

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = int(os.getenv("RATE_LIMIT_PER_MINUTE", "10"))

    # File Retention
    FILE_RETENTION_DAYS: int = int(os.getenv("FILE_RETENTION_DAYS", "30"))

    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    def __init__(self):
        """Validate configuration on initialization."""
        if not self.TELEGRAM_BOT_TOKEN:
            raise ValueError("TELEGRAM_BOT_TOKEN environment variable is required")
        
        # Create storage directory if it doesn't exist
        self.STORAGE_PATH.mkdir(parents=True, exist_ok=True)


config = Config()
