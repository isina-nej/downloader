"""File storage management with streaming support."""

import os
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Tuple
import aiofiles
import aiofiles.os
from src.config import config
from src.database import SessionLocal, FileRecord


class StorageManager:
    """Manages file storage operations."""

    def __init__(self):
        """Initialize storage manager."""
        self.storage_path = config.STORAGE_PATH
        self.storage_path.mkdir(parents=True, exist_ok=True)

    def generate_file_id(self) -> str:
        """Generate a unique file ID."""
        return str(uuid.uuid4())

    def get_file_path(self, file_id: str) -> Path:
        """Get the file path for a given file ID."""
        return self.storage_path / file_id

    async def save_file_stream(
        self,
        telegram_file_id: str,
        filename: str,
        file_stream,
        user_id: int,
    ) -> Tuple[str, int]:
        """
        Save a file from stream to storage.

        Args:
            telegram_file_id: Original file ID from Telegram
            filename: Original filename
            file_stream: File content stream (bytes)
            user_id: Telegram user ID

        Returns:
            Tuple of (generated_file_id, file_size)

        Raises:
            ValueError: If file size exceeds limit
        """
        file_id = self.generate_file_id()
        file_path = self.get_file_path(file_id)
        file_size = 0

        try:
            async with aiofiles.open(file_path, "wb") as f:
                async for chunk in file_stream:
                    file_size += len(chunk)
                    if file_size > config.MAX_FILE_SIZE:
                        # Delete the incomplete file
                        await aiofiles.os.remove(file_path)
                        raise ValueError(
                            f"File size exceeds maximum limit of {config.MAX_FILE_SIZE / (1024**3):.2f} GB"
                        )
                    await f.write(chunk)

            # Save file record to database
            db = SessionLocal()
            try:
                file_record = FileRecord(
                    id=file_id,
                    telegram_file_id=telegram_file_id,
                    original_filename=filename,
                    file_size=file_size,
                    file_path=str(file_path),
                    telegram_user_id=user_id,
                )
                db.add(file_record)
                db.commit()
            finally:
                db.close()

            return file_id, file_size

        except Exception as e:
            # Clean up file if it exists
            if file_path.exists():
                await aiofiles.os.remove(file_path)
            raise

    async def get_file(self, file_id: str) -> Optional[Tuple[Path, str]]:
        """
        Retrieve file information and increment download count.

        Args:
            file_id: The file ID to retrieve

        Returns:
            Tuple of (file_path, original_filename) or None if not found
        """
        db = SessionLocal()
        try:
            file_record = db.query(FileRecord).filter(FileRecord.id == file_id).first()
            if not file_record:
                return None

            # Update last accessed and download count
            file_record.last_accessed = datetime.utcnow()
            file_record.download_count += 1
            db.commit()

            file_path = Path(file_record.file_path)
            if not file_path.exists():
                return None

            return file_path, file_record.original_filename

        finally:
            db.close()

    async def delete_file(self, file_id: str) -> bool:
        """Delete a file and its record."""
        db = SessionLocal()
        try:
            file_record = db.query(FileRecord).filter(FileRecord.id == file_id).first()
            if not file_record:
                return False

            file_path = Path(file_record.file_path)
            if file_path.exists():
                await aiofiles.os.remove(file_path)

            db.delete(file_record)
            db.commit()
            return True

        finally:
            db.close()

    async def cleanup_old_files(self) -> int:
        """Delete files older than retention period."""
        db = SessionLocal()
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=config.FILE_RETENTION_DAYS)
            old_files = db.query(FileRecord).filter(FileRecord.created_at < cutoff_date).all()

            deleted_count = 0
            for file_record in old_files:
                try:
                    file_path = Path(file_record.file_path)
                    if file_path.exists():
                        await aiofiles.os.remove(file_path)
                    db.delete(file_record)
                    deleted_count += 1
                except Exception:
                    pass  # Continue with other files

            db.commit()
            return deleted_count

        finally:
            db.close()

    async def get_storage_info(self) -> dict:
        """Get storage statistics."""
        db = SessionLocal()
        try:
            total_files = db.query(FileRecord).count()
            total_size = 0
            for file_record in db.query(FileRecord).all():
                try:
                    total_size += file_record.file_size
                except Exception:
                    pass

            return {
                "total_files": total_files,
                "total_size_gb": total_size / (1024**3),
                "available_space_gb": self._get_available_space() / (1024**3),
            }

        finally:
            db.close()

    def _get_available_space(self) -> int:
        """Get available disk space in bytes."""
        try:
            stat = os.statvfs(self.storage_path)
            return stat.f_bavail * stat.f_frsize
        except Exception:
            return 0


storage_manager = StorageManager()
