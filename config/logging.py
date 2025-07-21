"""Logging configuration for Discord Task Manager."""

import logging
import logging.handlers
import os
from pathlib import Path

from config.settings import settings


def setup_logging():
    """Set up logging configuration."""

    # Create logs directory if it doesn't exist
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)

    # Set up logging level
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)

    # Create formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Set up root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # File handler with rotation
    file_handler = logging.handlers.RotatingFileHandler(
        filename=logs_dir / "discord_task_manager.log",
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    # Discord.py specific logging
    discord_logger = logging.getLogger("discord")
    discord_logger.setLevel(logging.INFO)

    # SQLAlchemy logging (only for debug mode)
    if settings.debug:
        sqlalchemy_logger = logging.getLogger("sqlalchemy.engine")
        sqlalchemy_logger.setLevel(logging.INFO)

    logging.info("Logging configuration complete")


# Initialize logging when module is imported
setup_logging()
