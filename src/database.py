"""Database models, session management, and utilities - Professional schema."""

from datetime import datetime, timedelta
from typing import Optional, List
from enum import Enum
import uuid

from sqlalchemy import (
    Column,
    String,
    Integer,
    DateTime,
    Boolean,
    Float,
    ForeignKey,
    Index,
    Text,
    create_engine,
    event,
    func,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.pool import StaticPool

from src.config import config
from src.logging_config import bot_logger

Base = declarative_base()


class FileStatus(str, Enum):
    """File status enumeration."""
    ACTIVE = "active"
    ARCHIVED = "archived"
    DELETED = "deleted"
    EXPIRED = "expired"


class TelegramUser(Base):
    """Telegram user model for tracking users."""

    __tablename__ = "telegram_users"
    __table_args__ = (Index("idx_user_telegram_id", "telegram_user_id"),)

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    telegram_user_id = Column(Integer, nullable=False, unique=True, index=True)
    username = Column(String(255), nullable=True, index=True)
    first_name = Column(String(255), nullable=True)
    last_name = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_activity = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    files = relationship("FileRecord", back_populates="user", cascade="all, delete-orphan")
    downloads = relationship("DownloadHistory", back_populates="user", cascade="all, delete-orphan")

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "telegram_user_id": self.telegram_user_id,
            "username": self.username,
            "name": f"{self.first_name or ''} {self.last_name or ''}".strip(),
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat(),
            "last_activity": self.last_activity.isoformat(),
        }


class FileRecord(Base):
    """Database model for tracking downloaded files - Professional schema."""

    __tablename__ = "files"
    __table_args__ = (
        Index("idx_file_telegram_id", "telegram_file_id"),
        Index("idx_file_user_id", "user_id"),
        Index("idx_file_status", "status"),
        Index("idx_file_created_at", "created_at"),
        Index("idx_file_expires_at", "expires_at"),
    )

    # Primary key
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # File information
    telegram_file_id = Column(String(512), nullable=False, unique=True, index=True)
    original_filename = Column(String(512), nullable=False)
    file_mime_type = Column(String(100), nullable=True)
    file_size = Column(Integer, nullable=False)  # In bytes
    file_path = Column(String(1024), nullable=False)
    
    # User information
    user_id = Column(String(36), ForeignKey("telegram_users.id"), nullable=False, index=True)
    user = relationship("TelegramUser", back_populates="files")
    
    # Status tracking
    status = Column(String(50), default=FileStatus.ACTIVE, nullable=False, index=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    last_accessed = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=True, index=True)  # For expiration logic
    
    # Statistics
    download_count = Column(Integer, default=0, nullable=False)
    total_download_size = Column(Integer, default=0, nullable=False)  # In bytes
    
    # Metadata
    is_public = Column(Boolean, default=False, nullable=False)
    checksum = Column(String(128), nullable=True)  # SHA256 hash for integrity
    
    # Relationships
    downloads = relationship("DownloadHistory", back_populates="file", cascade="all, delete-orphan")

    def to_dict(self) -> dict:
        """Convert model to dictionary."""
        return {
            "id": self.id,
            "filename": self.original_filename,
            "size_bytes": self.file_size,
            "size_mb": round(self.file_size / (1024 * 1024), 2),
            "mime_type": self.file_mime_type,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "last_accessed": self.last_accessed.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "download_count": self.download_count,
            "total_downloads_size_mb": round(self.total_download_size / (1024 * 1024), 2),
            "is_public": self.is_public,
        }

    def is_expired(self) -> bool:
        """Check if file has expired."""
        if self.expires_at:
            return datetime.utcnow() > self.expires_at
        return False

    def update_access(self):
        """Update last accessed timestamp."""
        self.last_accessed = datetime.utcnow()


class DownloadHistory(Base):
    """Download history for analytics."""

    __tablename__ = "download_history"
    __table_args__ = (
        Index("idx_download_file_id", "file_id"),
        Index("idx_download_user_id", "user_id"),
        Index("idx_download_created_at", "created_at"),
    )

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    file_id = Column(String(36), ForeignKey("files.id"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("telegram_users.id"), nullable=False, index=True)
    
    file = relationship("FileRecord", back_populates="downloads")
    user = relationship("TelegramUser", back_populates="downloads")
    
    downloaded_bytes = Column(Integer, nullable=False)  # Actual bytes downloaded
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    user_agent = Column(String(512), nullable=True)  # For tracking download sources
    ip_address = Column(String(45), nullable=True)  # IPv4 or IPv6

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "file_id": self.file_id,
            "user_id": self.user_id,
            "downloaded_bytes": self.downloaded_bytes,
            "created_at": self.created_at.isoformat(),
        }


class DatabaseStatistics(Base):
    """Cached statistics for performance."""

    __tablename__ = "statistics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    
    total_files = Column(Integer, default=0, nullable=False)
    total_size_bytes = Column(Integer, default=0, nullable=False)
    active_files = Column(Integer, default=0, nullable=False)
    total_downloads = Column(Integer, default=0, nullable=False)
    total_downloads_bytes = Column(Integer, default=0, nullable=False)
    unique_users = Column(Integer, default=0, nullable=False)
    
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "total_files": self.total_files,
            "total_size_gb": round(self.total_size_bytes / (1024 ** 3), 2),
            "active_files": self.active_files,
            "total_downloads": self.total_downloads,
            "total_downloads_gb": round(self.total_downloads_bytes / (1024 ** 3), 2),
            "unique_users": self.unique_users,
            "updated_at": self.updated_at.isoformat(),
        }


# Database setup
engine = create_engine(
    config.DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in config.DATABASE_URL else {},
    poolclass=StaticPool if "sqlite" in config.DATABASE_URL else None,
    echo=False,  # Set to True for SQL debugging
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """Dependency for getting database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database tables with proper setup."""
    try:
        Base.metadata.create_all(bind=engine)
        bot_logger.info("Database tables created/verified successfully")
        
        # Initialize statistics table if empty
        db = SessionLocal()
        try:
            stats = db.query(DatabaseStatistics).first()
            if not stats:
                stats = DatabaseStatistics()
                db.add(stats)
                db.commit()
                bot_logger.info("Statistics table initialized")
        finally:
            db.close()
            
    except Exception as e:
        bot_logger.error(f"Database initialization error: {e}")
        raise
