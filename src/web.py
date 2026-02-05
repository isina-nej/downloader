"""FastAPI web server for file downloads with professional endpoints."""

from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from fastapi.responses import FileResponse, JSONResponse
import asyncio
from pathlib import Path
from src.config import config
from src.storage import storage_manager
from src.database import init_db, SessionLocal, DatabaseStatistics, FileRecord, TelegramUser
from src.logging_config import web_logger, log_structured


app = FastAPI(
    title="Telegram File Downloader",
    description="Professional file management and download service",
    version="2.0.0"
)


@app.on_event("startup")
async def startup():
    """Initialize database on startup."""
    init_db()
    web_logger.info("Web server started - Database initialized")


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "service": "Telegram File Downloader",
        "version": "2.0.0",
        "status": "running",
        "endpoints": {
            "download": "/download/{file_id}",
            "health": "/health",
            "statistics": "/statistics",
            "admin": "/admin/stats",
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint with storage info."""
    try:
        stats = await storage_manager.get_storage_info()
        return {
            "status": "healthy",
            "storage": {
                "total_files": stats["total_files"],
                "active_files": stats["active_files"],
                "total_size_gb": stats["total_size_gb"],
                "available_space_gb": stats["available_space_gb"],
            }
        }
    except Exception as e:
        web_logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=503, detail="Service unavailable")


@app.get("/download/{file_id}")
async def download_file(
    file_id: str, 
    request: Request,
    background_tasks: BackgroundTasks
):
    """
    Download a file by ID with tracking.

    Args:
        file_id: The unique file ID (UUID format)
        request: HTTP request object
        background_tasks: Background task runner

    Returns:
        FileResponse with the file content

    Raises:
        HTTPException: If file not found or invalid
    """
    try:
        # Validate file_id format (UUID)
        if not _is_valid_uuid(file_id):
            log_structured(
                web_logger,
                "warning",
                "Invalid file ID format",
                file_id=file_id,
                ip=request.client.host
            )
            raise HTTPException(status_code=400, detail="Invalid file ID format")

        # Get IP address for analytics
        ip_address = request.client.host if request.client else "unknown"

        # Get file from storage with tracking
        result = await storage_manager.get_file(
            file_id,
            ip_address=ip_address
        )
        if result is None:
            log_structured(
                web_logger,
                "warning",
                "File not found or expired",
                file_id=file_id,
                ip=ip_address
            )
            raise HTTPException(status_code=404, detail="File not found or expired")

        file_path, original_filename = result

        # Verify file exists
        if not file_path.exists():
            log_structured(
                web_logger,
                "error",
                "File path does not exist",
                file_id=file_id,
                path=str(file_path)
            )
            raise HTTPException(status_code=404, detail="File not found")

        log_structured(
            web_logger,
            "info",
            "File download started",
            file_id=file_id,
            filename=original_filename,
            ip=ip_address
        )

        # Return file
        return FileResponse(
            path=file_path,
            filename=original_filename,
            media_type="application/octet-stream"
        )

    except HTTPException:
        raise
    except Exception as e:
        web_logger.error(f"Error downloading file {file_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Error processing download")


@app.get("/statistics")
async def get_statistics():
    """Get comprehensive statistics."""
    try:
        stats = await storage_manager.get_storage_info()
        return {
            "storage": {
                "total_files": stats["total_files"],
                "active_files": stats["active_files"],
                "total_size_gb": stats["total_size_gb"],
                "available_space_gb": stats["available_space_gb"],
            },
            "downloads": {
                "total_downloads": stats["total_downloads"],
                "total_downloaded_gb": stats["total_downloads_gb"],
            },
            "users": {
                "unique_users": stats["unique_users"],
            }
        }
    except Exception as e:
        web_logger.error(f"Statistics error: {str(e)}")
        raise HTTPException(status_code=500, detail="Could not retrieve statistics")


@app.get("/admin/stats")
async def admin_statistics():
    """Get detailed admin statistics with database info."""
    try:
        db = SessionLocal()
        try:
            # Basic statistics
            stats = await storage_manager.get_storage_info()
            
            # Database statistics
            db_stats = db.query(DatabaseStatistics).first()
            
            # Recent files
            recent_files = db.query(FileRecord).order_by(
                FileRecord.created_at.desc()
            ).limit(10).all()
            
            # Most downloaded files
            top_files = db.query(FileRecord).order_by(
                FileRecord.download_count.desc()
            ).limit(10).all()
            
            # Top users
            top_users = db.query(TelegramUser).order_by(
                TelegramUser.last_activity.desc()
            ).limit(10).all()
            
            return {
                "storage": stats,
                "database_stats": db_stats.to_dict() if db_stats else None,
                "recent_files": [f.to_dict() for f in recent_files],
                "top_files": [
                    {**f.to_dict(), "user_id": f.user.telegram_user_id if f.user else None}
                    for f in top_files
                ],
                "top_users": [u.to_dict() for u in top_users],
            }
        finally:
            db.close()
    except Exception as e:
        web_logger.error(f"Admin stats error: {str(e)}")
        raise HTTPException(status_code=500, detail="Could not retrieve admin statistics")


@app.post("/cleanup")
async def cleanup_old_files(background_tasks: BackgroundTasks):
    """
    Trigger cleanup of expired files (admin endpoint).
    
    Should be protected with authentication in production.
    """
    try:
        # Run cleanup in background
        background_tasks.add_task(_perform_cleanup)
        return {"status": "cleanup started", "message": "Expired files cleanup in progress"}
    except Exception as e:
        web_logger.error(f"Cleanup error: {str(e)}")
        raise HTTPException(status_code=500, detail="Cleanup failed")


async def _perform_cleanup():
    """Perform file cleanup in background."""
    try:
        deleted_count = await storage_manager.cleanup_expired_files()
        log_structured(
            web_logger,
            "info",
            "Cleanup completed",
            deleted_files=deleted_count
        )
    except Exception as e:
        web_logger.error(f"Cleanup error: {str(e)}")


def _is_valid_uuid(value: str) -> bool:
    """Validate UUID format."""
    import re
    uuid_pattern = re.compile(
        r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
        re.IGNORECASE
    )
    return uuid_pattern.match(value) is not None


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for all unhandled errors."""
    web_logger.error(f"Unhandled error: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )
