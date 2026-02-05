"""Telegram bot handler for file downloads."""

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from telegram.constants import ChatAction
from src.config import config
from src.storage import storage_manager
from src.rate_limiter import rate_limiter
from src.logging_config import bot_logger, log_structured


class TelegramBot:
    """Telegram bot application handler."""

    def __init__(self):
        """Initialize Telegram bot."""
        self.app = Application.builder().token(config.TELEGRAM_BOT_TOKEN).build()
        self._setup_handlers()

    def _setup_handlers(self):
        """Set up command and message handlers."""
        self.app.add_handler(CommandHandler("start", self.start_command))
        self.app.add_handler(CommandHandler("help", self.help_command))
        self.app.add_handler(CommandHandler("stats", self.stats_command))
        self.app.add_handler(
            MessageHandler(filters.Document.ALL, self.handle_document)
        )
        self.app.add_handler(
            MessageHandler(filters.VIDEO, self.handle_video)
        )
        self.app.add_handler(
            MessageHandler(filters.AUDIO, self.handle_audio)
        )

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command."""
        await update.message.reply_text(
            "👋 Welcome to Telegram File Downloader!\n\n"
            "Send me any file (document, video, or audio) and I'll:\n"
            "1. Download it to secure storage\n"
            "2. Generate a unique shareable link\n\n"
            "Use /help for more information."
        )
        bot_logger.info(f"User {update.effective_user.id} started the bot")

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command."""
        await update.message.reply_text(
            "📖 **How to use:**\n\n"
            "1. Send a file (document, video, or audio)\n"
            "2. Wait for processing (shows progress)\n"
            "3. Get a download link\n\n"
            "**Commands:**\n"
            "/start - Show welcome message\n"
            "/help - Show this message\n"
            "/stats - Show storage statistics\n\n"
            "**Limits:**\n"
            f"• Max file size: {config.MAX_FILE_SIZE / (1024**3):.2f} GB\n"
            f"• Files retained for: {config.FILE_RETENTION_DAYS} days\n",
            parse_mode="Markdown"
        )

    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /stats command."""
        try:
            stats = await storage_manager.get_storage_info()
            await update.message.reply_text(
                f"📊 **Storage Statistics:**\n\n"
                f"Total files: {stats['total_files']}\n"
                f"Total size: {stats['total_size_gb']:.2f} GB\n"
                f"Available space: {stats['available_space_gb']:.2f} GB\n",
                parse_mode="Markdown"
            )
        except Exception as e:
            bot_logger.error(f"Error getting stats: {str(e)}")
            await update.message.reply_text("❌ Error retrieving statistics")

    async def handle_document(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle document uploads."""
        await self._process_file(update, context, update.message.document)

    async def handle_video(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle video uploads."""
        await self._process_file(update, context, update.message.video)

    async def handle_audio(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle audio uploads."""
        await self._process_file(update, context, update.message.audio)

    async def _process_file(self, update: Update, context: ContextTypes.DEFAULT_TYPE, file_obj):
        """Process file upload."""
        user_id = update.effective_user.id

        # Check rate limit
        is_allowed = await rate_limiter.is_allowed(str(user_id))
        if not is_allowed:
            await update.message.reply_text(
                "⏱️ Rate limit exceeded. Please wait before sending another file."
            )
            log_structured(
                bot_logger,
                "warning",
                "Rate limit exceeded",
                user_id=user_id
            )
            return

        try:
            # Get file info
            filename = file_obj.file_name or f"file_{file_obj.file_unique_id}"
            file_size = file_obj.file_size or 0

            # Validate file size
            if file_size > config.MAX_FILE_SIZE:
                await update.message.reply_text(
                    f"❌ File too large! Maximum size is {config.MAX_FILE_SIZE / (1024**3):.2f} GB"
                )
                return

            # Show processing message
            processing_msg = await update.message.reply_text(
                f"⏳ Processing {filename}...\n"
                f"Size: {file_size / (1024**2):.2f} MB"
            )

            # Download file
            # Use bot.send_chat_action instead of chat.send_action (Chat object may not have send_action)
            await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.UPLOAD_DOCUMENT)
            file = await context.bot.get_file(file_obj.file_id)
            file_stream = await file.download_as_bytearray()

            # Stream to storage
            file_id, stored_size = await storage_manager.save_file_stream(
                telegram_file_id=file_obj.file_unique_id,
                filename=filename,
                file_stream=[file_stream],  # Convert bytes to iterable
                user_id=user_id,
            )

            # Generate download link
            download_url = f"{config.DOWNLOAD_URL_BASE}/download/{file_id}"

            # Update message with result
            await processing_msg.edit_text(
                f"✅ **File Uploaded Successfully!**\n\n"
                f"📁 File: `{filename}`\n"
                f"💾 Size: {stored_size / (1024**2):.2f} MB\n"
                f"🔗 Link: `{download_url}`\n\n"
                f"The link will be available for {config.FILE_RETENTION_DAYS} days.",
                parse_mode="Markdown"
            )

            log_structured(
                bot_logger,
                "info",
                "File uploaded successfully",
                user_id=user_id,
                file_id=file_id,
                filename=filename,
                size_mb=stored_size / (1024**2)
            )

        except ValueError as e:
            await update.message.reply_text(f"❌ Error: {str(e)}")
            bot_logger.error(f"Validation error for user {user_id}: {str(e)}")

        except Exception as e:
            await update.message.reply_text(
                "❌ Error processing file. Please try again."
            )
            bot_logger.error(f"Error processing file for user {user_id}: {str(e)}")

    async def start(self):
        """Start the bot."""
        await self.app.initialize()
        await self.app.start()
        bot_logger.info("Bot started successfully")

    async def stop(self):
        """Stop the bot."""
        await self.app.stop()
        await self.app.shutdown()
        bot_logger.info("Bot stopped")

    def run_polling(self):
        """Run bot in polling mode."""
        try:
            self.app.run_polling()
        except Exception as e:
            if "Conflict" in str(e):
                bot_logger.error("Telegram conflict error detected: another getUpdates request is running. Ensure only one bot instance is running.")
                raise
            bot_logger.error(f"Polling error: {e}")
            raise


async def create_bot() -> TelegramBot:
    """Factory function to create bot instance."""
    return TelegramBot()
