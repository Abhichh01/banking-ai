"""
Logging configuration for the Banking AI system.
"""
import logging
import sys
from pathlib import Path
from typing import Optional

from loguru import logger

from app.core.config import get_settings

settings = get_settings()

class InterceptHandler(logging.Handler):
    """
    Default handler from examples in loguru documentation.
    See https://loguru.readthedocs.io/en/stable/overview.html#entirely-compatible-with-standard-logging
    """
    def emit(self, record):
        # Get corresponding Loguru level if it exists
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Find caller from where originated the logged message
        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )

def setup_logging(
    json_logs: bool = False,
    log_level: Optional[str] = None,
) -> None:
    """
    Initialize logging configuration.
    
    Args:
        json_logs: Whether to use JSON-formatted logs
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    log_level = log_level or settings.LOG_LEVEL
    
    # Clear existing loggers
    logging.root.handlers = [InterceptHandler()]
    
    # Configure loguru
    logger.remove()  # Remove default handler
    
    # Add console handler
    logger.add(
        sys.stderr,
        level=log_level.upper(),
        format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
              "<level>{level: <8}</level> | "
              "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
    )
    
    # Add file handler if LOG_FILE is set
    if settings.LOG_FILE:
        log_file = Path(settings.LOG_FILE)
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        logger.add(
            str(log_file),
            rotation="10 MB",
            retention="30 days",
            level=log_level.upper(),
            format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}",
            enqueue=True,
            backtrace=True,
            diagnose=True
        )
    
    # Set log level for third-party libraries
    for name in logging.root.manager.loggerDict:
        if name.startswith(('uvicorn', 'fastapi')):
            logging.getLogger(name).handlers = [InterceptHandler()]
    
    logging.getLogger("uvicorn").handlers = [InterceptHandler()]
    logging.getLogger("uvicorn.access").handlers = [InterceptHandler()]
    
    # Set log level for our application
    logger.info(f"Logging configured with level: {log_level}")
