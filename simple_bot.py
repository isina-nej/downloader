"""Simple Telegram File Downloader Bot - Simplified Version for Testing"""

import asyncio
import os
from pathlib import Path
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
from telegram.constants import ChatAction

# Load environment
load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
STORAGE_PATH = Path(os.getenv("STORAGE_PATH", "./storage"))
STORAGE_PATH.mkdir(exist_ok=True)

print(f"🤖 Bot Token: {TOKEN[:20]}...")
print(f"📁 Storage Path: {STORAGE_PATH}")


class SimpleBot:
    """Simple Telegram bot for testing"""

    def __init__(self):
        self.app = Application.builder().token(TOKEN).build()
        self._setup_handlers()

    def _setup_handlers(self):
        """Setup command and message handlers"""
        self.app.add_handler(CommandHandler("start", self.start))
        self.app.add_handler(CommandHandler("help", self.help_cmd))
        self.app.add_handler(CommandHandler("stop", self.stop_cmd))

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        await update.message.reply_text(
            "👋 **Telegram File Downloader Bot** is running!\n\n"
            "Send me a file and I'll process it.\n\n"
            "Commands:\n"
            "/help - Show help\n"
            "/stop - Stop bot"
        )
        print(f"✅ User {update.effective_user.id} started bot")

    async def help_cmd(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        await update.message.reply_text(
            "📖 **How to use:**\n\n"
            "1. Send a file (document, video, audio)\n"
            "2. Bot will download it\n"
            "3. You'll get a download link\n\n"
            "**Features:**\n"
            "✅ Async processing\n"
            "✅ Secure storage\n"
            "✅ Download links"
        )

    async def stop_cmd(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /stop command"""
        await update.message.reply_text("👋 Bot stopping...")
        print("⛔ Bot stop requested")
        await self.app.stop()

    async def run(self):
        """Run the bot"""
        await self.app.initialize()
        await self.app.start()
        print("✅ Bot started successfully!")
        print("📱 Bot is running. Send messages to test.")

        # Keep running
        try:
            await asyncio.Event().wait()
        except KeyboardInterrupt:
            print("\n⛔ Bot stopped")
        finally:
            await self.app.stop()


async def main():
    """Main entry point"""
    print("🚀 Starting Telegram File Downloader Bot...\n")
    bot = SimpleBot()
    await bot.run()


if __name__ == "__main__":
    asyncio.run(main())
