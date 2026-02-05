"""Main application entry point."""

import asyncio
import signal
from typing import Set
import uvicorn
from src.config import config
from src.database import init_db
from src.bot_aiogram import AiogramBot
from src.web import app
from src.logging_config import bot_logger


class ApplicationManager:
    """Manages both aiogram bot and web server."""

    def __init__(self):
        """Initialize application manager."""
        self.bot: AiogramBot = None
        self.web_server_task = None
        self.shutdown_event = asyncio.Event()

    async def start(self):
        """Start both bot and web server."""
        # Initialize database
        init_db()
        bot_logger.info("Database initialized")

        # Create and start bot
        self.bot = AiogramBot()
        bot_logger.info("Aiogram bot initialized")

        # Start web server in asyncio
        self.web_server_task = asyncio.create_task(self._run_web_server())

        # Set up signal handlers for graceful shutdown
        self._setup_signal_handlers()

        bot_logger.info("Application started successfully")
        
        # Start bot polling
        await self.bot.start()

    async def _run_web_server(self):
        """Run web server."""
        config_dict = uvicorn.Config(
            app,
            host=config.SERVER_HOST,
            port=config.SERVER_PORT,
            log_config=None,  # Use our logging
        )
        server = uvicorn.Server(config_dict)
        try:
            await server.serve()
        except asyncio.CancelledError:
            pass

    def _setup_signal_handlers(self):
        """Set up signal handlers for graceful shutdown."""
        loop = asyncio.get_event_loop()

        def handle_signal(signame):
            async def shutdown():
                bot_logger.info(f"Received signal {signame}, shutting down...")
                await self.shutdown()

            asyncio.create_task(shutdown())

        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(
                sig, lambda s=sig: handle_signal(s.name)
            )

    async def shutdown(self):
        """Shutdown application."""
        try:
            if self.bot:
                await self.bot.stop()
                bot_logger.info("Bot stopped")

            if self.web_server_task:
                self.web_server_task.cancel()
                try:
                    await self.web_server_task
                except asyncio.CancelledError:
                    pass
                bot_logger.info("Web server stopped")

            self.shutdown_event.set()
        except Exception as e:
            bot_logger.error(f"Error during shutdown: {str(e)}")


async def main():
    """Main entry point."""
    # Single instance enforcement
    from src.singleton_lock import SingleInstance

    lock = SingleInstance(config.PID_FILE)
    try:
        lock.acquire()
    except RuntimeError as e:
        bot_logger.error(str(e))
        print(str(e))
        return

    try:
        manager = ApplicationManager()
        await manager.start()
        
        # Keep application running
        while not manager.shutdown_event.is_set():
            await asyncio.sleep(1)

    except KeyboardInterrupt:
        bot_logger.info("Application interrupted")
    except Exception as e:
        bot_logger.error(f"Application error: {str(e)}")
        raise
    finally:
        # Release lock on exit
        try:
            lock.release()
        except Exception:
            pass


if __name__ == "__main__":
    asyncio.run(main())
