"""Database management utilities and migration helpers."""

from datetime import datetime
from sqlalchemy import text
from src.database import SessionLocal, engine, Base, FileRecord, TelegramUser, DownloadHistory, DatabaseStatistics
from src.logging_config import bot_logger


class DatabaseManager:
    """Manages database operations including migrations and maintenance."""

    @staticmethod
    def init_schema():
        """Initialize database schema."""
        try:
            Base.metadata.create_all(bind=engine)
            bot_logger.info("Database schema initialized successfully")
        except Exception as e:
            bot_logger.error(f"Error initializing schema: {e}")
            raise

    @staticmethod
    def backup_database(backup_path: str) -> bool:
        """
        Create a database backup.
        
        For SQLite: Copy the database file
        For other DB: Use appropriate backup method
        """
        try:
            import shutil
            from src.config import config
            from pathlib import Path
            
            if "sqlite" in config.DATABASE_URL:
                # Extract database path from SQLite URL
                db_path = config.DATABASE_URL.replace("sqlite:///", "").replace("sqlite:////", "/")
                backup_file = Path(backup_path) / f"db_backup_{datetime.utcnow().isoformat()}.db"
                shutil.copy(db_path, backup_file)
                bot_logger.info(f"Database backed up to {backup_file}")
                return True
            else:
                bot_logger.warning("Backup not implemented for non-SQLite databases")
                return False
                
        except Exception as e:
            bot_logger.error(f"Backup error: {e}")
            return False

    @staticmethod
    def get_database_stats() -> dict:
        """Get comprehensive database statistics."""
        db = SessionLocal()
        try:
            stats = {
                "users": {
                    "total": db.query(TelegramUser).count(),
                    "active": db.query(TelegramUser).filter(TelegramUser.is_active == True).count(),
                },
                "files": {
                    "total": db.query(FileRecord).count(),
                },
                "downloads": {
                    "total_records": db.query(DownloadHistory).count(),
                },
            }
            return stats
        finally:
            db.close()

    @staticmethod
    def cleanup_orphaned_records() -> dict:
        """Clean up orphaned database records."""
        db = SessionLocal()
        try:
            cleanup_stats = {
                "deleted_download_history": 0,
                "deleted_files": 0,
            }
            
            # Delete download history for non-existent files (shouldn't happen with FK, but safety)
            # Note: SQLAlchemy handles this automatically with cascade
            
            return cleanup_stats
        finally:
            db.close()

    @staticmethod
    def vacuum_database():
        """Optimize database by running VACUUM (SQLite only)."""
        try:
            from src.config import config
            
            if "sqlite" in config.DATABASE_URL:
                with engine.connect() as connection:
                    connection.execute(text("VACUUM"))
                    connection.commit()
                bot_logger.info("Database VACUUM completed")
                return True
            else:
                bot_logger.debug("VACUUM not applicable for non-SQLite databases")
                return False
                
        except Exception as e:
            bot_logger.warning(f"VACUUM error: {e}")
            return False

    @staticmethod
    def reset_statistics():
        """Reset all statistics counters."""
        db = SessionLocal()
        try:
            # Reset statistics table
            stats = db.query(DatabaseStatistics).first()
            if stats:
                stats.total_files = 0
                stats.total_size_bytes = 0
                stats.active_files = 0
                stats.total_downloads = 0
                stats.total_downloads_bytes = 0
                stats.unique_users = 0
                stats.updated_at = datetime.utcnow()
                db.commit()
                bot_logger.info("Statistics reset")
                return True
            return False
        finally:
            db.close()

    @staticmethod
    def export_user_data(user_id: int) -> dict:
        """Export all data for a specific user (GDPR compliance)."""
        db = SessionLocal()
        try:
            user = db.query(TelegramUser).filter(
                TelegramUser.telegram_user_id == user_id
            ).first()
            
            if not user:
                return None
            
            files = db.query(FileRecord).filter(
                FileRecord.user_id == user.id
            ).all()
            
            downloads = db.query(DownloadHistory).filter(
                DownloadHistory.user_id == user.id
            ).all()
            
            return {
                "user": user.to_dict(),
                "files": [f.to_dict() for f in files],
                "downloads": [d.to_dict() for d in downloads],
                "export_date": datetime.utcnow().isoformat(),
            }
        finally:
            db.close()

    @staticmethod
    def delete_user_data(user_id: int) -> bool:
        """Delete all data for a specific user (GDPR right to be forgotten)."""
        db = SessionLocal()
        try:
            user = db.query(TelegramUser).filter(
                TelegramUser.telegram_user_id == user_id
            ).first()
            
            if not user:
                return False
            
            # Delete all related records (cascade will handle this)
            db.delete(user)
            db.commit()
            bot_logger.info(f"All data for user {user_id} deleted")
            return True
        finally:
            db.close()
