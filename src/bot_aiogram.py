"""Telegram bot handler using aiogram - async and modern approach."""

import asyncio
from typing import Optional
from io import BytesIO

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.enums import ChatAction

from src.config import config
from src.storage import storage_manager
from src.rate_limiter import rate_limiter
from src.logging_config import bot_logger, log_structured


class FileUploadStates(StatesGroup):
    """FSM states for file upload process."""
    waiting_for_file = State()


class AiogramBot:
    """Modern Telegram bot using aiogram with async/await."""

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
        """Handle /stats command."""
        try:
            stats = await storage_manager.get_storage_info()
            await message.answer(
                f"📊 <b>آمار ذخیره سازی:</b>\n\n"
                f"کل فایل‌ها: {stats['total_files']}\n"
                f"اندازه کل: {stats['total_size_gb']:.2f} GB\n"
                f"فضای دسترس: {stats['available_space_gb']:.2f} GB\n",
                parse_mode="HTML"
            )
            log_structured(
                bot_logger, "info", "Stats retrieved",
                user_id=message.from_user.id
            )
        except Exception as e:
            bot_logger.error(f"Error getting stats: {str(e)}")
            await message.answer("❌ خطا در دریافت آمار")

    async def cmd_cancel(self, message: types.Message, state: FSMContext):
        """Handle /cancel command."""
        current_state = await state.get_state()
        if current_state is None:
            return

        await state.clear()
        await message.answer("❌ عملیات لغو شد")

    async def handle_file(self, message: types.Message):
        """Handle file uploads (documents, videos, audio)."""
        user_id = message.from_user.id

        # Rate limiting
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
        elif message.video:
            file_obj = message.video
            filename = f"video_{file_obj.file_unique_id}.mp4"
        elif message.audio:
            file_obj = message.audio
            filename = f"audio_{file_obj.file_unique_id}.mp3"
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
            await message.chat.send_action(ChatAction.UPLOAD_DOCUMENT)

            file = await self.bot.get_file(file_obj.file_id)
            file_stream = await self.bot.download(file)

            # Save to storage
            file_bytes = await file_stream.read()
            file_id, stored_size = await storage_manager.save_file_stream(
                telegram_file_id=file_obj.file_unique_id,
                filename=filename,
                file_stream=[file_bytes],
                user_id=user_id,
            )

            # Generate download link
            download_url = f"{config.DOWNLOAD_URL_BASE}/download/{file_id}"

            # Update message with result
            await processing_msg.edit_text(
                f"✅ <b>فایل آپلود شد!</b>\n\n"
                f"📁 نام: <code>{filename}</code>\n"
                f"💾 اندازه: {stored_size / (1024**2):.2f} MB\n"
                f"🔗 لینک:\n<code>{download_url}</code>\n\n"
                f"لینک {config.FILE_RETENTION_DAYS} روز فعال می‌ماند.",
                parse_mode="HTML"
            )

            log_structured(
                bot_logger, "info", "File uploaded",
                user_id=user_id,
                file_id=file_id,
                filename=filename,
                size_mb=stored_size / (1024**2)
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
