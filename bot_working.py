"""Telegram File Downloader Bot - Working Version"""

import asyncio
import logging
import os
from pathlib import Path
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
from telegram.constants import ChatAction

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Load environment
load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
STORAGE_PATH = Path(os.getenv("STORAGE_PATH", "./storage"))
STORAGE_PATH.mkdir(exist_ok=True)

print("\n" + "="*50)
print("🤖 TELEGRAM BOT INITIALIZATION")
print("="*50)
print(f"✅ Token: {TOKEN[:30]}...")
print(f"✅ Storage: {STORAGE_PATH.absolute()}")
print("="*50 + "\n")


class TelegramBot:
    """Main Bot Class"""

    def __init__(self):
        """Initialize bot"""
        self.app = Application.builder().token(TOKEN).build()
        self.setup_handlers()

    def setup_handlers(self):
        """Setup all command handlers"""
        print("[SETUP] Adding command handlers...")
        
        # Commands
        self.app.add_handler(CommandHandler("start", self.start_handler))
        self.app.add_handler(CommandHandler("help", self.help_handler))
        self.app.add_handler(CommandHandler("stats", self.stats_handler))
        self.app.add_handler(CommandHandler("stop", self.stop_handler))
        
        # Messages
        self.app.add_handler(MessageHandler(filters.Document.ALL, self.document_handler))
        self.app.add_handler(MessageHandler(filters.VIDEO, self.video_handler))
        self.app.add_handler(MessageHandler(filters.AUDIO, self.audio_handler))
        
        print("[SETUP] ✅ All handlers registered\n")

    async def start_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user_id = update.effective_user.id
        user_name = update.effective_user.first_name
        
        print(f"[START] User {user_id} ({user_name}) started bot")
        
        await update.message.reply_text(
            f"👋 سلام {user_name}!\n\n"
            "🤖 **ربات دانلود فایل تلگرام** فعال است!\n\n"
            "📝 دستورات:\n"
            "/help - راهنمایی\n"
            "/stats - آمار\n"
            "/stop - توقف ربات\n\n"
            "📁 فایل برای ربات ارسال کنید!"
        )

    async def help_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        user_id = update.effective_user.id
        print(f"[HELP] User {user_id} requested help")
        
        await update.message.reply_text(
            "📖 **راهنمایی استفاده:**\n\n"
            "1️⃣ فایل (سند، ویدیو، صوت) برای ربات ارسال کنید\n"
            "2️⃣ ربات دانلود و پردازش می‌کند\n"
            "3️⃣ لینک دانلود دریافت کنید\n\n"
            "✨ ویژگی‌ها:\n"
            "✅ دانلود Async\n"
            "✅ ذخیره‌سازی امن\n"
            "✅ لینک‌های دانلود\n\n"
            "❓ سوال؟ /stats را بزن!"
        )

    async def stats_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /stats command"""
        user_id = update.effective_user.id
        print(f"[STATS] User {user_id} requested stats")
        
        # Count files
        files = list(STORAGE_PATH.glob('*'))
        total_size = sum(f.stat().st_size for f in files if f.is_file())
        
        await update.message.reply_text(
            "📊 **آمار سرور:**\n\n"
            f"📁 تعداد فایل‌ها: {len(files)}\n"
            f"💾 حجم کل: {total_size / (1024**2):.2f} MB\n"
            f"📂 مسیر: {STORAGE_PATH.absolute()}\n\n"
            "✅ سرور در حال کار است!"
        )

    async def stop_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /stop command"""
        user_id = update.effective_user.id
        print(f"[STOP] User {user_id} requested stop")
        
        await update.message.reply_text("👋 ربات متوقف می‌شود...")
        
        # Stop the app
        await self.app.stop()

    async def document_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle document uploads"""
        user_id = update.effective_user.id
        doc = update.message.document
        
        print(f"[DOCUMENT] User {user_id} sent: {doc.file_name} ({doc.file_size} bytes)")
        
        await update.message.reply_text(
            f"📄 **سند دریافت شد!**\n\n"
            f"📝 نام: {doc.file_name}\n"
            f"📦 اندازه: {doc.file_size / (1024**2):.2f} MB\n\n"
            "⏳ در حال دانلود..."
        )

    async def video_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle video uploads"""
        user_id = update.effective_user.id
        video = update.message.video
        
        print(f"[VIDEO] User {user_id} sent video ({video.file_size} bytes)")
        
        await update.message.reply_text(
            f"🎥 **ویدیو دریافت شد!**\n\n"
            f"📦 اندازه: {video.file_size / (1024**2):.2f} MB\n\n"
            "⏳ در حال دانلود..."
        )

    async def audio_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle audio uploads"""
        user_id = update.effective_user.id
        audio = update.message.audio
        
        print(f"[AUDIO] User {user_id} sent audio ({audio.file_size} bytes)")
        
        await update.message.reply_text(
            f"🎵 **صوت دریافت شد!**\n\n"
            f"📦 اندازه: {audio.file_size / (1024**2):.2f} MB\n\n"
            "⏳ در حال دانلود..."
        )

    async def run(self):
        """Run the bot"""
        print("[RUN] Starting bot...\n")
        
        await self.app.initialize()
        print("[RUN] ✅ App initialized")
        
        await self.app.start()
        print("[RUN] ✅ App started")
        
        # Start polling
        print("[RUN] ⏳ Starting polling...\n")
        print("="*50)
        print("✅ BOT IS RUNNING!")
        print("="*50)
        print("Send /start to test")
        print("Press Ctrl+C to stop\n")
        print("="*50 + "\n")
        
        try:
            await self.app.updater.start_polling(
                allowed_updates=Update.ALL_TYPES,
                drop_pending_updates=False,
            )
        except KeyboardInterrupt:
            print("\n[RUN] Keyboard interrupt")
        except Exception as e:
            print(f"\n[ERROR] {e}")
        finally:
            print("\n[RUN] Stopping bot...")
            await self.app.stop()
            print("[RUN] ✅ Bot stopped")


async def main():
    """Main entry point"""
    print("\n🚀 STARTING TELEGRAM BOT\n")
    
    if not TOKEN:
        print("❌ ERROR: TELEGRAM_BOT_TOKEN not found in .env")
        return

    # Single-instance lock to prevent Telegram getUpdates conflicts
    from src.singleton_lock import SingleInstance
    from pathlib import Path

    lock = SingleInstance(Path("./bot.pid"))
    try:
        lock.acquire()
    except RuntimeError as e:
        print(str(e))
        return

    try:
        bot = TelegramBot()
        await bot.run()
    finally:
        try:
            lock.release()
        except Exception:
            pass


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Bot stopped by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
