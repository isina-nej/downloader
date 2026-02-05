"""File storage management with streaming support - Professional implementation."""

import os
import hashlib
import mimetypes
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Tuple
import aiofiles
import aiofiles.os
from sqlalchemy import func

from src.config import config
from src.database import SessionLocal, FileRecord, DownloadHistory, DatabaseStatistics, TelegramUser, FileStatus
from src.logging_config import bot_logger


class StorageManager:
    """Professional file storage manager with full tracking."""

    def __init__(self):
        """Initialize storage manager."""
        self.storage_path = config.STORAGE_PATH
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.logs_path = Path(config.STORAGE_PATH).parent / "logs"
        self.logs_path.mkdir(parents=True, exist_ok=True)

    def generate_file_id(self) -> str:
        """Generate a unique file ID using UUID."""
        import uuid
        return str(uuid.uuid4())

    def get_file_path(self, file_id: str) -> Path:
        """Get the file path for a given file ID."""
        return self.storage_path / file_id

    async def _calculate_checksum(self, file_path: Path, algorithm: str = "sha256") -> str:
        """Calculate file checksum for integrity verification."""
        hash_obj = hashlib.new(algorithm)
        async with aiofiles.open(file_path, "rb") as f:
            async for chunk in aiofiles.iter_chunked(f, 8192):
                hash_obj.update(chunk)
        return hash_obj.hexdigest()

    async def save_file_stream(
        self,
        telegram_file_id: str,
        filename: str,
        file_stream,
        user_id: int,
        mime_type: Optional[str] = None,
    ) -> Tuple[str, int]:
        """
        Save a file from stream to storage with full tracking.

        Args:
            telegram_file_id: Original file ID from Telegram
            filename: Original filename
            file_stream: File content stream (bytes)
            user_id: Telegram user ID
            mime_type: MIME type of file

        Returns:
            Tuple of (generated_file_id, file_size)

        Raises:
            ValueError: If file size exceeds limit
        """
        file_id = self.generate_file_id()
        file_path = self.get_file_path(file_id)
        file_size = 0

        try:
            # Save file to disk
            async with aiofiles.open(file_path, "wb") as f:
                async for chunk in file_stream:
                    file_size += len(chunk)
                    if file_size > config.MAX_FILE_SIZE:
                        await aiofiles.os.remove(file_path)
                        raise ValueError(
                            f"File size exceeds maximum limit of {config.MAX_FILE_SIZE / (1024**3):.2f} GB"
                        )
                    await f.write(chunk)

            # Calculate checksum for integrity
            checksum = await self._calculate_checksum(file_path)

            # Detect MIME type if not provided
            if not mime_type:
                mime_type, _ = mimetypes.guess_type(filename)
            if not mime_type:
                mime_type = "application/octet-stream"

            # Calculate expiration
            expires_at = datetime.utcnow() + timedelta(days=config.FILE_RETENTION_DAYS)

            # Save file record to database
            db = SessionLocal()
            try:
                # Get or create user
                user = db.query(TelegramUser).filter(
                    TelegramUser.telegram_user_id == user_id
                ).first()
                
                if not user:
                    user = TelegramUser(telegram_user_id=user_id)
                    db.add(user)
                    db.flush()  # Get the ID
                
                # Create file record
                file_record = FileRecord(
                    id=file_id,
                    telegram_file_id=telegram_file_id,
                    original_filename=filename,
                    file_size=file_size,
                    file_path=str(file_path),
                    file_mime_type=mime_type,
                    user_id=user.id,
                    status=FileStatus.ACTIVE,
                    expires_at=expires_at,
                    checksum=checksum,
                )
                db.add(file_record)
                
                # Update user last activity
                user.last_activity = datetime.utcnow()
                
                db.commit()
                bot_logger.info(f"File saved: {file_id} ({filename}) - {file_size} bytes - User: {user_id}")
                
            finally:
                db.close()

            return file_id, file_size

        except Exception as e:
            # Clean up file if it exists
            if file_path.exists():
                try:
                    await aiofiles.os.remove(file_path)
                except Exception:
                    pass
            bot_logger.error(f"Error saving file: {e}")
            raise

    async def get_file(
        self, 
        file_id: str, 
        user_id: Optional[int] = None,
        ip_address: Optional[str] = None,
    ) -> Optional[Tuple[Path, str]]:
        """
        Retrieve file information and log download.

        Args:
            file_id: The file ID to retrieve
            user_id: User ID for analytics (optional)
            ip_address: IP address for analytics (optional)

        Returns:
            Tuple of (file_path, original_filename) or None if not found
        """
        db = SessionLocal()
        try:
            file_record = db.query(FileRecord).filter(FileRecord.id == file_id).first()
            if not file_record:
                return None

            # Check if file is expired
            if file_record.is_expired():
                file_record.status = FileStatus.EXPIRED
                db.commit()
                return None

            # Check if file exists on disk
            file_path = Path(file_record.file_path)
            if not file_path.exists():
                file_record.status = FileStatus.DELETED
                db.commit()
                return None

            # Update file statistics
            file_record.update_access()
            file_record.download_count += 1
            file_record.total_download_size += file_record.file_size
            
            # Get or create user for tracking
            user = None
            if file_record.user_id:
                user = db.query(TelegramUser).filter(
                    TelegramUser.id == file_record.user_id
                ).first()
            
            # Log download history
            download_record = DownloadHistory(
                file_id=file_id,
                user_id=file_record.user_id,
                downloaded_bytes=file_record.file_size,
                ip_address=ip_address,
            )
            db.add(download_record)
            
            db.commit()
            
            bot_logger.info(
                f"File downloaded: {file_id} ({file_record.original_filename}) "
                f"- User: {user.telegram_user_id if user else 'unknown'} - IP: {ip_address}"
            )

            return file_path, file_record.original_filename

        finally:
            db.close()

    async def delete_file(self, file_id: str, soft_delete: bool = True) -> bool:
        """
        Delete a file and optionally its record.

        Args:
            file_id: File ID to delete
            soft_delete: If True, mark as deleted instead of removing

        Returns:
            True if successful
        """
        db = SessionLocal()
        try:
            file_record = db.query(FileRecord).filter(FileRecord.id == file_id).first()
            if not file_record:
                return False

            file_path = Path(file_record.file_path)
            try:
                if file_path.exists():
                    await aiofiles.os.remove(file_path)
                    bot_logger.info(f"File deleted from disk: {file_id}")
            except Exception as e:
                bot_logger.warning(f"Could not delete file from disk: {file_id} - {e}")

            if soft_delete:
                file_record.status = FileStatus.DELETED
                db.commit()
            else:
                db.delete(file_record)
                db.commit()

            return True

        finally:
            db.close()

    async def cleanup_expired_files(self) -> int:
        """Delete files that have expired based on retention policy."""
        db = SessionLocal()
        try:
            expired_files = db.query(FileRecord).filter(
                FileRecord.expires_at <= datetime.utcnow()
            ).all()

            deleted_count = 0
            for file_record in expired_files:
                try:
                    await self.delete_file(file_record.id, soft_delete=True)
                    deleted_count += 1
                except Exception as e:
                    bot_logger.warning(f"Error cleaning up file {file_record.id}: {e}")

            if deleted_count > 0:
                bot_logger.info(f"Cleaned up {deleted_count} expired files")
            
            return deleted_count

        finally:
            db.close()

    async def get_storage_info(self) -> dict:
        """Get comprehensive storage statistics."""
        db = SessionLocal()
        try:
            # Query statistics
            active_files = db.query(FileRecord).filter(
                FileRecord.status == FileStatus.ACTIVE
            ).count()
            total_files = db.query(FileRecord).count()
            
            # Total size calculation
            total_size_result = db.query(func.sum(FileRecord.file_size)).filter(
                FileRecord.status == FileStatus.ACTIVE
            ).scalar()
            total_size = total_size_result or 0
            
            # Download statistics
            total_downloads = db.query(func.sum(FileRecord.download_count)).scalar() or 0
            total_downloads_bytes = db.query(func.sum(FileRecord.total_download_size)).scalar() or 0
            
            # User count
            unique_users = db.query(func.count(FileRecord.user_id.distinct())).scalar() or 0

            # Update statistics table
            stats = db.query(DatabaseStatistics).first()
            if stats:
                stats.total_files = total_files
                stats.active_files = active_files
                stats.total_size_bytes = total_size
                stats.total_downloads = total_downloads
                stats.total_downloads_bytes = total_downloads_bytes
                stats.unique_users = unique_users
                stats.updated_at = datetime.utcnow()
                db.commit()

            return {
                "total_files": total_files,
                "active_files": active_files,
                "total_size_bytes": total_size,
                "total_size_gb": round(total_size / (1024**3), 2),
                "total_downloads": total_downloads,
                "total_downloads_bytes": total_downloads_bytes,
                "total_downloads_gb": round(total_downloads_bytes / (1024**3), 2),
                "unique_users": unique_users,
                "available_space_gb": round(self._get_available_space() / (1024**3), 2),
            }

        finally:
            db.close()

    def _get_available_space(self) -> int:
        """Get available disk space in bytes."""
        try:
            stat = os.statvfs(self.storage_path)
            return stat.f_bavail * stat.f_frsize
        except Exception as e:
            bot_logger.warning(f"Could not get available space: {e}")
            return 0


storage_manager = StorageManager()
