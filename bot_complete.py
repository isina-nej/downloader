#!/usr/bin/env python3
"""
Telegram File Downloader Bot - Complete Version with Download & Download Links
"""

import asyncio
import logging
import os
import sys
import uuid
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout,
    force=True
)
logger = logging.getLogger(__name__)
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger('telegram').setLevel(logging.WARNING)

# Load environment
load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
STORAGE_PATH = Path(os.getenv("STORAGE_PATH", "./storage"))
STORAGE_PATH.mkdir(exist_ok=True)

# Download links config
BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")
WEB_PORT = int(os.getenv("WEB_PORT", "8000"))

# Import telegram modules
try:
    from telegram import Update
    from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
except ImportError as e:
    print(f"❌ Import Error: {e}")
    sys.exit(1)

print("\n" + "="*60)
print("🤖 TELEGRAM FILE DOWNLOADER BOT (COMPLETE)")
print("="*60)

if not TOKEN or TOKEN == "your_bot_token":
    print("❌ ERROR: TELEGRAM_BOT_TOKEN not configured")
    sys.exit(1)

print(f"✅ Token: {TOKEN[:30]}...")
print(f"✅ Storage: {STORAGE_PATH.absolute()}")
print(f"✅ Download Base URL: {BASE_URL}")
print("="*60 + "\n")


# ============ FILE MANAGER ============

class FileManager:
    """Handle file downloads and storage"""
    
    def __init__(self, storage_path: Path):
        self.storage_path = storage_path
        self.metadata_file = storage_path / "files.txt"
    
    async def save_file(self, file_id: str, file_name: str, file_size: int, user_id: int) -> dict:
        """Download file from Telegram and save locally"""
        try:
            unique_id = str(uuid.uuid4())[:8]
            file_ext = Path(file_name).suffix or ".bin"
            saved_name = f"{unique_id}_{file_name}"
            saved_path = self.storage_path / saved_name
            
            logger.info(f"[SAVE] Starting download: {file_name}")
            
            # Create metadata entry
            metadata = {
                "id": unique_id,
                "file_name": file_name,
                "saved_name": saved_name,
                "file_size": file_size,
                "user_id": user_id,
                "timestamp": datetime.now().isoformat(),
                "download_count": 0
            }
            
            # Save metadata
            with open(self.metadata_file, 'a') as f:
                f.write(f"{unique_id}|{file_name}|{saved_name}|{file_size}|{user_id}|{metadata['timestamp']}\n")
            
            logger.info(f"[SAVE] ✅ File registered: {unique_id}")
            return metadata
            
        except Exception as e:
            logger.error(f"[SAVE] ❌ Error: {e}")
            raise

    def get_download_link(self, file_id: str, file_name: str) -> str:
        """Generate download link"""
        return f"{BASE_URL}/download/{file_id}/{file_name}"


file_manager = FileManager(STORAGE_PATH)


# ============ COMMAND HANDLERS ============

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    user = update.effective_user
    logger.info(f"[START] @{user.username} ({user.first_name})")
    
    text = (
        f"👋 سلام {user.first_name}!\n\n"
        "🤖 **ربات دانلود فایل فعال است!**\n\n"
        "📝 دستورات:\n"
        "  /start - شروع\n"
        "  /help - راهنمایی\n"
        "  /stats - آمار\n"
        "  /stop - توقف\n\n"
        "💾 **فایل برای ربات ارسال کنید!**"
    )
    
    await update.message.reply_text(text)
    logger.info(f"[START] ✅ Reply sent")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command"""
    user = update.effective_user
    logger.info(f"[HELP] @{user.username}")
    
    text = (
        "📖 **راهنمایی:**\n\n"
        "**مراحل استفاده:**\n"
        "1️⃣ فایل ارسال کنید\n"
        "2️⃣ ربات دانلود می‌کند\n"
        "3️⃣ لینک دانلود دریافت کنید\n"
        "4️⃣ از هر جایی دانلود کنید\n\n"
        "✨ **فایل‌های پشتیبانی:**\n"
        "  ✅ سند (Document)\n"
        "  ✅ ویدیو (Video)\n"
        "  ✅ صوت (Audio)\n"
        "  ✅ تصویر (Photo)\n"
    )
    
    await update.message.reply_text(text)
    logger.info(f"[HELP] ✅ Reply sent")


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /stats command"""
    user = update.effective_user
    logger.info(f"[STATS] @{user.username}")
    
    # Count files
    files = list(STORAGE_PATH.glob('*'))
    file_count = len([f for f in files if f.is_file() and f.name != "files.txt"])
    total_size = sum(f.stat().st_size for f in files if f.is_file() and f.name != "files.txt") / (1024**2)
    
    text = (
        "📊 **آمار سرور:**\n\n"
        f"  📁 فایل‌ها: {file_count}\n"
        f"  💾 حجم کل: {total_size:.2f} MB\n"
        f"  🌐 سرور: {BASE_URL}\n"
        f"  ✅ وضعیت: فعال\n\n"
        "🚀 سرور آماده است!"
    )
    
    await update.message.reply_text(text)
    logger.info(f"[STATS] ✅ Reply sent")


async def stop_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /stop command"""
    user = update.effective_user
    logger.info(f"[STOP] @{user.username} requested stop")
    
    await update.message.reply_text("👋 ربات متوقف می‌شود...")
    logger.info(f"[STOP] Stopping app...")
    
    if context.application:
        asyncio.create_task(context.application.stop())


async def document_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle document uploads"""
    user = update.effective_user
    doc = update.message.document
    
    size_mb = doc.file_size / (1024**2) if doc.file_size else 0
    logger.info(f"[DOCUMENT] @{user.username} sent {doc.file_name} ({size_mb:.2f} MB)")
    
    # Show processing message
    processing_msg = await update.message.reply_text(
        f"📄 **سند دریافت شد!**\n\n"
        f"  📝 نام: {doc.file_name}\n"
        f"  📦 اندازه: {size_mb:.2f} MB\n\n"
        "⏳ در حال دانلود..."
    )
    
    try:
        # Download file from Telegram
        logger.info(f"[DOCUMENT] Downloading file...")
        file = await context.bot.get_file(doc.file_id)
        file_path = STORAGE_PATH / doc.file_name
        await file.download_to_drive(file_path)
        logger.info(f"[DOCUMENT] ✅ Downloaded to {file_path}")
        
        # Save metadata
        metadata = await file_manager.save_file(
            file.file_id,
            doc.file_name,
            doc.file_size or 0,
            user.id
        )
        
        # Generate download link
        download_link = file_manager.get_download_link(metadata["id"], doc.file_name)
        
        # Send download link
        link_text = (
            f"✅ **فایل دانلود شد!**\n\n"
            f"  📝 نام: {doc.file_name}\n"
            f"  📦 اندازه: {size_mb:.2f} MB\n"
            f"  🆔 ID: {metadata['id']}\n\n"
            f"🔗 **لینک دانلود:**\n"
            f"{download_link}"
        )
        
        await processing_msg.edit_text(link_text)
        logger.info(f"[DOCUMENT] ✅ Link sent")
        
    except Exception as e:
        logger.error(f"[DOCUMENT] ❌ Error: {e}")
        await processing_msg.edit_text(
            f"❌ **خطا در دانلود!**\n\n"
            f"مشکل: {str(e)[:100]}"
        )


async def video_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle video uploads"""
    user = update.effective_user
    video = update.message.video
    
    size_mb = video.file_size / (1024**2) if video.file_size else 0
    file_name = f"video_{video.file_unique_id}.mp4"
    
    logger.info(f"[VIDEO] @{user.username} sent video ({size_mb:.2f} MB)")
    
    # Show processing message
    processing_msg = await update.message.reply_text(
        f"🎥 **ویدیو دریافت شد!**\n\n"
        f"  ⏱️ مدت: {video.duration}s\n"
        f"  📦 اندازه: {size_mb:.2f} MB\n\n"
        "⏳ در حال دانلود..."
    )
    
    try:
        # Download file
        logger.info(f"[VIDEO] Downloading file...")
        file = await context.bot.get_file(video.file_id)
        file_path = STORAGE_PATH / file_name
        await file.download_to_drive(file_path)
        logger.info(f"[VIDEO] ✅ Downloaded")
        
        # Save metadata
        metadata = await file_manager.save_file(
            file.file_id,
            file_name,
            video.file_size or 0,
            user.id
        )
        
        # Generate download link
        download_link = file_manager.get_download_link(metadata["id"], file_name)
        
        # Send link
        link_text = (
            f"✅ **ویدیو دانلود شد!**\n\n"
            f"  📦 اندازه: {size_mb:.2f} MB\n"
            f"  🆔 ID: {metadata['id']}\n\n"
            f"🔗 **لینک دانلود:**\n"
            f"{download_link}"
        )
        
        await processing_msg.edit_text(link_text)
        logger.info(f"[VIDEO] ✅ Link sent")
        
    except Exception as e:
        logger.error(f"[VIDEO] ❌ Error: {e}")
        await processing_msg.edit_text(f"❌ خطا: {str(e)[:100]}")


async def audio_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle audio uploads"""
    user = update.effective_user
    audio = update.message.audio
    
    size_mb = audio.file_size / (1024**2) if audio.file_size else 0
    file_name = f"audio_{audio.file_unique_id}.mp3"
    
    logger.info(f"[AUDIO] @{user.username} sent audio ({size_mb:.2f} MB)")
    
    # Show processing message
    processing_msg = await update.message.reply_text(
        f"🎵 **صوت دریافت شد!**\n\n"
        f"  ⏱️ مدت: {audio.duration}s\n"
        f"  📦 اندازه: {size_mb:.2f} MB\n\n"
        "⏳ در حال دانلود..."
    )
    
    try:
        # Download file
        logger.info(f"[AUDIO] Downloading file...")
        file = await context.bot.get_file(audio.file_id)
        file_path = STORAGE_PATH / file_name
        await file.download_to_drive(file_path)
        logger.info(f"[AUDIO] ✅ Downloaded")
        
        # Save metadata
        metadata = await file_manager.save_file(
            file.file_id,
            file_name,
            audio.file_size or 0,
            user.id
        )
        
        # Generate download link
        download_link = file_manager.get_download_link(metadata["id"], file_name)
        
        # Send link
        link_text = (
            f"✅ **صوت دانلود شد!**\n\n"
            f"  📦 اندازه: {size_mb:.2f} MB\n"
            f"  🆔 ID: {metadata['id']}\n\n"
            f"🔗 **لینک دانلود:**\n"
            f"{download_link}"
        )
        
        await processing_msg.edit_text(link_text)
        logger.info(f"[AUDIO] ✅ Link sent")
        
    except Exception as e:
        logger.error(f"[AUDIO] ❌ Error: {e}")
        await processing_msg.edit_text(f"❌ خطا: {str(e)[:100]}")


async def photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle photo uploads"""
    user = update.effective_user
    photo = update.message.photo[-1]  # Get largest photo
    
    size_mb = photo.file_size / (1024**2) if photo.file_size else 0
    file_name = f"photo_{photo.file_unique_id}.jpg"
    
    logger.info(f"[PHOTO] @{user.username} sent photo ({size_mb:.2f} MB)")
    
    # Show processing message
    processing_msg = await update.message.reply_text(
        f"📷 **تصویر دریافت شد!**\n\n"
        f"  📦 اندازه: {size_mb:.2f} MB\n\n"
        "⏳ در حال دانلود..."
    )
    
    try:
        # Download file
        logger.info(f"[PHOTO] Downloading file...")
        file = await context.bot.get_file(photo.file_id)
        file_path = STORAGE_PATH / file_name
        await file.download_to_drive(file_path)
        logger.info(f"[PHOTO] ✅ Downloaded")
        
        # Save metadata
        metadata = await file_manager.save_file(
            file.file_id,
            file_name,
            photo.file_size or 0,
            user.id
        )
        
        # Generate download link
        download_link = file_manager.get_download_link(metadata["id"], file_name)
        
        # Send link
        link_text = (
            f"✅ **تصویر دانلود شد!**\n\n"
            f"  📦 اندازه: {size_mb:.2f} MB\n"
            f"  🆔 ID: {metadata['id']}\n\n"
            f"🔗 **لینک دانلود:**\n"
            f"{download_link}"
        )
        
        await processing_msg.edit_text(link_text)
        logger.info(f"[PHOTO] ✅ Link sent")
        
    except Exception as e:
        logger.error(f"[PHOTO] ❌ Error: {e}")
        await processing_msg.edit_text(f"❌ خطا: {str(e)[:100]}")


async def unknown_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle unknown messages"""
    await update.message.reply_text(
        "❓ دستور نشناخته است.\n"
        "دستورات: /start, /help, /stats, /stop"
    )


# ============ MAIN APPLICATION ============

async def main():
    """Main entry point"""
    print("🚀 Initializing Application...\n")
    
    # Create application
    app = Application.builder().token(TOKEN).build()
    
    print("📝 Setting up handlers...")
    
    # Command handlers
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("stats", stats_command))
    app.add_handler(CommandHandler("stop", stop_command))
    
    # File handlers
    app.add_handler(MessageHandler(filters.Document.ALL, document_handler))
    app.add_handler(MessageHandler(filters.VIDEO, video_handler))
    app.add_handler(MessageHandler(filters.AUDIO, audio_handler))
    app.add_handler(MessageHandler(filters.PHOTO, photo_handler))
    
    # Unknown handler
    app.add_handler(MessageHandler(filters.TEXT, unknown_handler))
    
    print("✅ Handlers registered\n")
    
    print("="*60)
    print("✅ BOT IS RUNNING AND READY!")
    print("="*60)
    print("\n📱 Features:")
    print("   • Download files from Telegram")
    print("   • Generate download links")
    print("   • Support documents, videos, audio, photos")
    print("\n🔔 Press Ctrl+C to stop\n")
    print("="*60 + "\n")
    
    # Start bot
    logger.info("Starting polling...")
    
    await app.initialize()
    await app.start()
    
    try:
        await app.updater.start_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=False,
        )
        logger.info("✅ Polling started")
        
        # Keep running
        while True:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt")
    except Exception as e:
        logger.error(f"Error: {e}")
    finally:
        logger.info("Stopping application")
        await app.stop()
        print("✅ Bot stopped\n")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Bot shutdown")
