"""Database models and session management."""

from datetime import datetime
from typing import Optional
from sqlalchemy import Column, String, Integer, DateTime, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from src.config import config

Base = declarative_base()


class FileRecord(Base):
    """Database model for tracking downloaded files."""

    __tablename__ = "files"

    id = Column(String(36), primary_key=True)  # UUID
    telegram_file_id = Column(String(255), nullable=False, unique=True)
    original_filename = Column(String(255), nullable=False)
    file_size = Column(Integer, nullable=False)
    file_path = Column(String(512), nullable=False)
    telegram_user_id = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_accessed = Column(DateTime, default=datetime.utcnow)
    download_count = Column(Integer, default=0)

    def to_dict(self) -> dict:
        """Convert model to dictionary."""
        return {
            "id": self.id,
            "filename": self.original_filename,
            "size": self.file_size,
            "created_at": self.created_at.isoformat(),
            "downloads": self.download_count,
        }


# Database setup
engine = create_engine(config.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """Dependency for getting database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database tables."""
    Base.metadata.create_all(bind=engine)
