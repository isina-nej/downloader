"""Telegram bot handler using aiogram - professional implementation."""

import asyncio
from typing import Optional
from io import BytesIO
from datetime import datetime

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.enums import ChatAction

from src.config import config
from src.storage import storage_manager
from src.rate_limiter import rate_limiter
from src.database import SessionLocal, TelegramUser
from src.logging_config import bot_logger, log_structured


class FileUploadStates(StatesGroup):
    """FSM states for file upload process."""
    waiting_for_file = State()


class AiogramBot:
    """Professional Telegram bot using aiogram 3.x with full feature support."""

    def __init__(self):
        """Initialize aiogram bot."""
        self.bot = Bot(token=config.TELEGRAM_BOT_TOKEN)
        self.dp = Dispatcher()
        self._setup_handlers()

    def _setup_handlers(self):
        """Register all command and message handlers."""
        # Commands
        self.dp.message.register(self.cmd_start, Command("start"))
        self.dp.message.register(self.cmd_help, Command("help"))
        self.dp.message.register(self.cmd_stats, Command("stats"))
        self.dp.message.register(self.cmd_cancel, Command("cancel"))

        # File handlers - documents, videos, audio
        self.dp.message.register(
            self.handle_file,
            F.document
        )
        self.dp.message.register(
            self.handle_file,
            F.video
        )
        self.dp.message.register(
            self.handle_file,
            F.audio
        )

        # Default handler for unknown messages
        self.dp.message.register(self.handle_default)

    async def cmd_start(self, message: types.Message):
        """Handle /start command."""
        await message.answer(
            "👋 سلام! به دانلودر فایل تلگرام خوش آمدید!\n\n"
            "من می‌تونم:\n"
            "1. فایل‌های شما رو دانلود کنم\n"
            "2. یک لینک اشتراک‌پذیر بسازم\n\n"
            "برای دستورات بیشتر: /help"
        )
        bot_logger.info(f"User {message.from_user.id} started bot")

    async def cmd_help(self, message: types.Message):
        """Handle /help command."""
        await message.answer(
            "📖 **راهنمای استفاده:**\n\n"
            "1. فایل بفرستید (سند، ویدیو یا صوت)\n"
            "2. منتظر بمانید...\n"
            "3. لینک دانلود رو بگیرید\n\n"
            "**دستورات:**\n"
            "/start - شروع\n"
            "/help - این پیام\n"
            "/stats - آمار ذخیره سازی\n"
            "/cancel - لغو عملیات\n\n"
            "**محدودیت‌ها:**\n"
            f"• حداکثر اندازه: {config.MAX_FILE_SIZE / (1024**3):.2f} GB\n"
            f"• مدت نگهداری: {config.FILE_RETENTION_DAYS} روز\n",
            parse_mode="HTML"
        )

    async def cmd_stats(self, message: types.Message):
        """Handle /stats command with comprehensive statistics."""
        try:
            stats = await storage_manager.get_storage_info()
            
            await message.answer(
                f"📊 <b>آمار ذخیره سازی:</b>\n\n"
                f"📁 کل فایل‌ها: {stats['total_files']}\n"
                f"✅ فایل‌های فعال: {stats['active_files']}\n"
                f"💾 اندازه کل: {stats['total_size_gb']:.2f} GB\n"
                f"⬇️ دانلود‌های کل: {stats['total_downloads']}\n"
                f"📥 حجم دانلود‌شده: {stats['total_downloads_gb']:.2f} GB\n"
                f"👥 کاربران منحصر: {stats['unique_users']}\n"
                f"💿 فضای دسترس: {stats['available_space_gb']:.2f} GB\n",
                parse_mode="HTML"
            )
            
            # Log stats
            log_structured(
                bot_logger, 
                "info", 
                "Stats retrieved",
                user_id=message.from_user.id,
                total_files=stats['total_files'],
                total_size_gb=stats['total_size_gb']
            )
        except Exception as e:
            bot_logger.error(f"Error getting stats: {e}")
            await message.answer("❌ خطا در دریافت آمار!")

    async def cmd_cancel(self, message: types.Message, state: FSMContext):
        """Handle /cancel command."""
        current_state = await state.get_state()
        if current_state is None:
            return

        await state.clear()
        await message.answer("❌ عملیات لغو شد")

    async def handle_file(self, message: types.Message):
        """Handle file uploads with professional tracking."""
        user_id = message.from_user.id

        # Rate limiting check
        is_allowed = await rate_limiter.is_allowed(str(user_id))
        if not is_allowed:
            await message.answer("⏱️ محدودیت درخواست! لطفا منتظر بمانید.")
            log_structured(
                bot_logger, "warning", "Rate limit exceeded",
                user_id=user_id
            )
            return

        # Get file object based on message type
        if message.document:
            file_obj = message.document
            filename = file_obj.file_name or f"file_{file_obj.file_unique_id}"
            mime_type = file_obj.mime_type
        elif message.video:
            file_obj = message.video
            filename = f"video_{file_obj.file_unique_id}.mp4"
            mime_type = file_obj.mime_type or "video/mp4"
        elif message.audio:
            file_obj = message.audio
            filename = f"audio_{file_obj.file_unique_id}.mp3"
            mime_type = file_obj.mime_type or "audio/mpeg"
        else:
            await message.answer("❌ نوع فایل پشتیبانی نشده")
            return

        file_size = file_obj.file_size or 0

        # Validate file size
        if file_size > config.MAX_FILE_SIZE:
            await message.answer(
                f"❌ فایل خیلی بزرگه! حداکثر: {config.MAX_FILE_SIZE / (1024**3):.2f} GB"
            )
            return

        # Show processing message
        processing_msg = await message.answer(
            f"⏳ درحال پردازش {filename}...\n"
            f"اندازه: {file_size / (1024**2):.2f} MB"
        )

        try:
            # Download file
            # Chat doesn't implement send_action directly in this version of aiogram.
            await self.bot.send_chat_action(chat_id=message.chat.id, action=ChatAction.UPLOAD_DOCUMENT)

            file = await self.bot.get_file(file_obj.file_id)
            file_stream = await self.bot.download(file)  # returns a stream-like object

            # Save to storage with mime type and user metadata
            file_bytes = await file_stream.read()
            file_id, stored_size = await storage_manager.save_file_stream(
                telegram_file_id=file_obj.file_unique_id,
                filename=filename,
                file_stream=[file_bytes],
                user_id=user_id,
                mime_type=mime_type,
                username=message.from_user.username,
                first_name=message.from_user.first_name,
                last_name=message.from_user.last_name,
            )

            # Generate download link
            download_url = f"{config.DOWNLOAD_URL_BASE}/download/{file_id}"

            # Update message with result
            await processing_msg.edit_text(
                f"✅ <b>فایل آپلود شد!</b>\n\n"
                f"📁 نام: <code>{filename}</code>\n"
                f"💾 اندازه: {stored_size / (1024**2):.2f} MB\n"
                f"🔗 لینک:\n<code>{download_url}</code>\n\n"
                f"⏰ لینک {config.FILE_RETENTION_DAYS} روز فعال می‌ماند.",
                parse_mode="HTML"
            )

            log_structured(
                bot_logger, "info", "File uploaded successfully",
                user_id=user_id,
                file_id=file_id,
                filename=filename,
                size_mb=round(stored_size / (1024**2), 2),
                mime_type=mime_type
            )

        except ValueError as e:
            await processing_msg.edit_text(f"❌ خطا: {str(e)}")
            bot_logger.error(f"Validation error for user {user_id}: {str(e)}")

        except Exception as e:
            await processing_msg.edit_text("❌ خطا در پردازش فایل")
            bot_logger.error(f"Error processing file for user {user_id}: {str(e)}")

    async def handle_default(self, message: types.Message):
        """Handle unknown messages."""
        await message.answer(
            "❓ پیام نامشخص!\n\n"
            "لطفا فایل بفرستید یا /help استفاده کنید."
        )

    async def start(self):
        """Start the bot with polling."""
        bot_logger.info("Starting aiogram bot...")
        try:
            await self.dp.start_polling(self.bot)
        except Exception as e:
            # Detect Telegram conflict error coming from server and re-raise to stop the process
            if "Conflict" in str(e):
                bot_logger.error("Telegram conflict error detected: another getUpdates request is running. Ensure only one bot instance is running.")
                raise
            bot_logger.error(f"Bot polling error: {str(e)}")
        finally:
            await self.bot.session.close()

    async def stop(self):
        """Stop the bot."""
        await self.bot.session.close()
        bot_logger.info("Bot stopped")


async def create_aiogram_bot() -> AiogramBot:
    """Factory function to create aiogram bot instance."""
    return AiogramBot()
