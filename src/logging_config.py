"""Logging and monitoring utilities."""

import logging
import json
from datetime import datetime
from pathlib import Path
from src.config import config

# Create logs directory
log_dir = Path("./logs")
log_dir.mkdir(exist_ok=True)


def setup_logger(name: str) -> logging.Logger:
    """Set up a logger with structured logging."""
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, config.LOG_LEVEL))

    # File handler
    file_handler = logging.FileHandler(log_dir / f"{name}.log")
    file_handler.setLevel(getattr(logging, config.LOG_LEVEL))

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, config.LOG_LEVEL))

    # Formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


def log_structured(logger: logging.Logger, level: str, message: str, **kwargs):
    """Log structured JSON data."""
    log_data = {
        "timestamp": datetime.utcnow().isoformat(),
        "message": message,
        **kwargs,
    }
    getattr(logger, level.lower())(json.dumps(log_data))


# Module loggers
bot_logger = setup_logger("bot")
storage_logger = setup_logger("storage")
web_logger = setup_logger("web")
