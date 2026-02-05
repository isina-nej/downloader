#!/usr/bin/env python3
"""
Simple Web Server for Download Links
"""

import logging
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
import uvicorn
import os
from dotenv import load_dotenv

load_dotenv()

STORAGE_PATH = Path(os.getenv("STORAGE_PATH", "./storage"))
WEB_PORT = int(os.getenv("WEB_PORT", "8000"))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="File Downloader API")


@app.get("/")
async def home():
    return {"message": "🤖 File Downloader API", "status": "running"}


@app.get("/download/{file_id}/{file_name}")
async def download_file(file_id: str, file_name: str):
    """Download a file by ID and name"""
    try:
        # Find any file starting with file_id
        files = list(STORAGE_PATH.glob(f"{file_id}_*"))
        
        if not files:
            logger.error(f"[DOWNLOAD] File not found: {file_id}")
            logger.error(f"[DOWNLOAD] Available files: {list(STORAGE_PATH.glob('*'))}")
            raise HTTPException(status_code=404, detail="File not found")
        
        file_path = files[0]
        logger.info(f"[DOWNLOAD] ✅ {file_id} -> {file_path.name}")
        
        return FileResponse(
            path=file_path,
            filename=file_name,
            media_type="application/octet-stream"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[DOWNLOAD] ❌ Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/files")
async def list_files():
    """List all available files (DEBUG)"""
    files = list(STORAGE_PATH.glob('*'))
    return {
        "total": len(files),
        "files": [f.name for f in files]
    }


@app.get("/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    print("\n" + "="*60)
    print("🌐 WEB SERVER")
    print("="*60)
    print(f"✅ Port: {WEB_PORT}")
    print(f"✅ Storage: {STORAGE_PATH.absolute()}")
    print("="*60 + "\n")
    
    uvicorn.run(app, host="0.0.0.0", port=WEB_PORT, log_level="info")
