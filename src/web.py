"""FastAPI web server for file downloads."""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import asyncio
from pathlib import Path
from src.config import config
from src.storage import storage_manager
from src.database import init_db
from src.logging_config import web_logger, log_structured


app = FastAPI(
    title="Telegram File Downloader",
    description="Web server for downloading files uploaded via Telegram bot",
    version="1.0.0"
)


@app.on_event("startup")
async def startup():
    """Initialize database on startup."""
    init_db()
    web_logger.info("Web server started")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "Telegram File Downloader",
        "version": "1.0.0",
        "status": "running",
        "download_endpoint": "/download/{file_id}"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        stats = await storage_manager.get_storage_info()
        return {
            "status": "healthy",
            "storage": stats
        }
    except Exception as e:
        web_logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=503, detail="Service unavailable")


@app.get("/download/{file_id}")
async def download_file(file_id: str, background_tasks: BackgroundTasks):
    """
    Download a file by ID.

    Args:
        file_id: The unique file ID
        background_tasks: Background task runner for cleanup

    Returns:
        FileResponse with the file content
    """
    try:
        # Validate file_id format (UUID)
        if not _is_valid_uuid(file_id):
            log_structured(
                web_logger,
                "warning",
                "Invalid file ID format",
                file_id=file_id
            )
            raise HTTPException(status_code=400, detail="Invalid file ID format")

        # Get file from storage
        result = await storage_manager.get_file(file_id)
        if result is None:
            log_structured(
                web_logger,
                "warning",
                "File not found",
                file_id=file_id
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
            filename=original_filename
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


@app.post("/cleanup")
async def cleanup_old_files(background_tasks: BackgroundTasks):
    """
    Trigger cleanup of old files (admin endpoint).
    
    Should be protected with authentication in production.
    """
    try:
        # Run cleanup in background
        background_tasks.add_task(_perform_cleanup)
        return {"status": "cleanup started"}
    except Exception as e:
        web_logger.error(f"Cleanup error: {str(e)}")
        raise HTTPException(status_code=500, detail="Cleanup failed")


@app.get("/stats")
async def get_stats():
    """Get storage statistics."""
    try:
        stats = await storage_manager.get_storage_info()
        return stats
    except Exception as e:
        web_logger.error(f"Stats error: {str(e)}")
        raise HTTPException(status_code=500, detail="Could not retrieve statistics")


async def _perform_cleanup():
    """Perform file cleanup in background."""
    try:
        deleted_count = await storage_manager.cleanup_old_files()
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
