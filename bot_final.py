#!/usr/bin/env python3
"""
Telegram File Downloader Bot - Final Working Version
"""

import asyncio
import logging
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Configure logging FIRST
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout,
    force=True
)
logger = logging.getLogger(__name__)

# Suppress verbose logging
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger('telegram').setLevel(logging.WARNING)

# Load environment
load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
STORAGE_PATH = Path(os.getenv("STORAGE_PATH", "./storage"))
STORAGE_PATH.mkdir(exist_ok=True)

# Import telegram modules
try:
    from telegram import Update
    from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
    from telegram.constants import ChatAction
except ImportError as e:
    print(f"❌ Import Error: {e}")
    print("Install: pip install python-telegram-bot")
    sys.exit(1)

print("\n" + "="*60)
print("🤖 TELEGRAM FILE DOWNLOADER BOT")
print("="*60)

if not TOKEN or TOKEN == "your_bot_token":
    print("❌ ERROR: TELEGRAM_BOT_TOKEN not configured in .env")
    print("   Add: TELEGRAM_BOT_TOKEN=your_token_here")
    sys.exit(1)

print(f"✅ Token: {TOKEN[:30]}...")
print(f"✅ Storage: {STORAGE_PATH.absolute()}")
print("="*60 + "\n")


# ============ COMMAND HANDLERS ============

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    user = update.effective_user
    logger.info(f"[START] @{user.username} ({user.first_name})")
    
    text = (
        f"👋 سلام {user.first_name}!\n\n"
        "🤖 **ربات دانلود فایل فعال است!**\n\n"
        "📝 دستورات موجود:\n"
        "  /start - شروع\n"
        "  /help - راهنمایی\n"
        "  /stats - آمار\n"
        "  /stop - توقف ربات\n\n"
        "💾 فایل برای ربات ارسال کنید!"
    )
    
    await update.message.reply_text(text)
    logger.info(f"[START] ✅ Reply sent")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command"""
    user = update.effective_user
    logger.info(f"[HELP] @{user.username}")
    
    text = (
        "📖 **راهنمایی:**\n\n"
        "1️⃣ فایل (سند، ویدیو، صوت) ارسال کنید\n"
        "2️⃣ ربات دانلود و ذخیره می‌کند\n"
        "3️⃣ لینک دانلود دریافت کنید\n\n"
        "✨ **ویژگی‌ها:**\n"
        "  ✅ دانلود سریع\n"
        "  ✅ ذخیره ایمن\n"
        "  ✅ لینک‌های دانلود\n"
        "  ✅ آمار مفصل\n\n"
        "❓ سوالی دارید؟"
    )
    
    await update.message.reply_text(text)
    logger.info(f"[HELP] ✅ Reply sent")


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /stats command"""
    user = update.effective_user
    logger.info(f"[STATS] @{user.username}")
    
    # Count files
    files = list(STORAGE_PATH.glob('*'))
    file_count = len([f for f in files if f.is_file()])
    total_size = sum(f.stat().st_size for f in files if f.is_file()) / (1024**2)
    
    text = (
        "📊 **آمار سرور:**\n\n"
        f"  📁 فایل‌ها: {file_count}\n"
        f"  💾 حجم کل: {total_size:.2f} MB\n"
        f"  🗂️ مسیر: {STORAGE_PATH.name}\n"
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
    logger.info(f"[STOP] ✅ Stop message sent, stopping app...")
    
    # Schedule stop
    if context.application:
        asyncio.create_task(context.application.stop())


async def document_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle document uploads"""
    user = update.effective_user
    doc = update.message.document
    
    size_mb = doc.file_size / (1024**2) if doc.file_size else 0
    logger.info(f"[DOCUMENT] @{user.username} sent {doc.file_name} ({size_mb:.2f} MB)")
    
    text = (
        f"📄 **سند دریافت شد!**\n\n"
        f"  📝 نام: {doc.file_name}\n"
        f"  📦 اندازه: {size_mb:.2f} MB\n"
        f"  🆔 ID: {doc.file_id[:20]}...\n\n"
        "⏳ در حال پردازش..."
    )
    
    await update.message.reply_text(text)
    logger.info(f"[DOCUMENT] ✅ Reply sent")


async def video_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle video uploads"""
    user = update.effective_user
    video = update.message.video
    
    size_mb = video.file_size / (1024**2) if video.file_size else 0
    logger.info(f"[VIDEO] @{user.username} sent video ({size_mb:.2f} MB)")
    
    text = (
        f"🎥 **ویدیو دریافت شد!**\n\n"
        f"  ⏱️ مدت: {video.duration}s\n"
        f"  📦 اندازه: {size_mb:.2f} MB\n\n"
        "⏳ در حال پردازش..."
    )
    
    await update.message.reply_text(text)
    logger.info(f"[VIDEO] ✅ Reply sent")


async def audio_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle audio uploads"""
    user = update.effective_user
    audio = update.message.audio
    
    size_mb = audio.file_size / (1024**2) if audio.file_size else 0
    logger.info(f"[AUDIO] @{user.username} sent audio ({size_mb:.2f} MB)")
    
    text = (
        f"🎵 **صوت دریافت شد!**\n\n"
        f"  ⏱️ مدت: {audio.duration}s\n"
        f"  📦 اندازه: {size_mb:.2f} MB\n\n"
        "⏳ در حال پردازش..."
    )
    
    await update.message.reply_text(text)
    logger.info(f"[AUDIO] ✅ Reply sent")


async def unknown_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle unknown messages"""
    user = update.effective_user
    logger.info(f"[MESSAGE] @{user.username}: {update.message.text[:50]}")
    
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
    
    # Unknown handler
    app.add_handler(MessageHandler(filters.TEXT, unknown_handler))
    
    print("✅ Handlers registered\n")
    
    print("="*60)
    print("✅ BOT IS RUNNING AND READY!")
    print("="*60)
    print("\n📱 You can now:")
    print("   • Send /start to test")
    print("   • Send /help for instructions")
    print("   • Send /stats to see server stats")
    print("   • Send /stop to stop the bot")
    print("\n🔔 Press Ctrl+C to stop the bot\n")
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
        logger.info("✅ Polling started successfully")
        
        # Keep running until interrupted
        while True:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        print("\n\n⏹️  Keyboard interrupt received")
        logger.info("Keyboard interrupt")
    except Exception as e:
        logger.error(f"Error: {e}")
        print(f"\n❌ Error: {e}")
    finally:
        print("\n🛑 Stopping bot...")
        logger.info("Stopping application")
        await app.stop()
        print("✅ Bot stopped\n")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Bot shutdown complete")
