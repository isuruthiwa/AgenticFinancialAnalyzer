"""
Logging setup and configuration.

Provides centralized logging configuration with Rich console output,
file logging, and structured log formatting for the CSE prediction platform.
"""

import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Dict, Optional

from rich.console import Console
from rich.logging import RichHandler


def setup_logging(
    level: str = "INFO",
    config: Optional[Dict] = None,
    enable_file_logging: bool = True
) -> None:
    """
    Set up logging configuration with Rich console and optional file output.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        config: Optional configuration dictionary
        enable_file_logging: Whether to enable file logging
    """
    # Parse logging level
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    
    # Get configuration
    if config is None:
        config = {}
    
    logging_config = config.get("logging", {})
    log_format = logging_config.get(
        "format", 
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    log_file = logging_config.get("file", "logs/agenticfa.log")
    
    # Clear existing handlers
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    
    # Create Rich console handler
    console = Console()
    rich_handler = RichHandler(
        console=console,
        show_time=True,
        show_level=True,
        show_path=False,
        rich_tracebacks=True,
        tracebacks_show_locals=False
    )
    rich_handler.setLevel(numeric_level)
    
    # Create formatter for Rich handler
    rich_formatter = logging.Formatter(
        fmt="%(message)s",
        datefmt="[%X]"
    )
    rich_handler.setFormatter(rich_formatter)
    
    # Add Rich handler to root logger
    root_logger.addHandler(rich_handler)
    root_logger.setLevel(numeric_level)
    
    # Set up file logging if enabled
    if enable_file_logging:
        setup_file_logging(log_file, log_format, numeric_level)
    
    # Configure third-party loggers
    configure_third_party_loggers()
    
    # Log startup message
    logger = logging.getLogger(__name__)
    logger.info(f"Logging initialized - Level: {level}, File: {log_file if enable_file_logging else 'disabled'}")


def setup_file_logging(log_file: str, log_format: str, level: int) -> None:
    """
    Set up file logging with rotation.
    
    Args:
        log_file: Path to log file
        log_format: Log message format
        level: Logging level
    """
    # Ensure log directory exists
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Create rotating file handler
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(level)
    
    # Create formatter for file handler
    file_formatter = logging.Formatter(
        fmt=log_format,
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    file_handler.setFormatter(file_formatter)
    
    # Add file handler to root logger
    root_logger = logging.getLogger()
    root_logger.addHandler(file_handler)


def configure_third_party_loggers() -> None:
    """Configure logging levels for third-party libraries."""
    # Reduce noise from third-party libraries
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.pool").setLevel(logging.WARNING)
    logging.getLogger("lightgbm").setLevel(logging.WARNING)
    logging.getLogger("transformers").setLevel(logging.WARNING)
    logging.getLogger("sentence_transformers").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger with the specified name.
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)


class StructuredLogger:
    """
    Structured logging helper for consistent log formatting.
    """
    
    def __init__(self, name: str):
        """
        Initialize structured logger.
        
        Args:
            name: Logger name
        """
        self.logger = logging.getLogger(name)
    
    def log_operation_start(self, operation: str, **kwargs) -> None:
        """Log the start of an operation."""
        extra_info = " ".join([f"{k}={v}" for k, v in kwargs.items()])
        self.logger.info(f"Starting {operation} {extra_info}")
    
    def log_operation_end(self, operation: str, duration: float, **kwargs) -> None:
        """Log the end of an operation."""
        extra_info = " ".join([f"{k}={v}" for k, v in kwargs.items()])
        self.logger.info(f"Completed {operation} in {duration:.2f}s {extra_info}")
    
    def log_error(self, operation: str, error: Exception, **kwargs) -> None:
        """Log an error with context."""
        extra_info = " ".join([f"{k}={v}" for k, v in kwargs.items()])
        self.logger.error(f"Error in {operation}: {error} {extra_info}", exc_info=True)
    
    def log_data_stats(self, data_type: str, count: int, **kwargs) -> None:
        """Log data statistics."""
        extra_info = " ".join([f"{k}={v}" for k, v in kwargs.items()])
        self.logger.info(f"Data stats - {data_type}: {count} records {extra_info}")


def log_function_call(func):
    """
    Decorator to log function calls with timing.
    
    Args:
        func: Function to decorate
        
    Returns:
        Decorated function
    """
    import functools
    import time
    
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        logger = logging.getLogger(func.__module__)
        
        start_time = time.time()
        logger.debug(f"Calling {func.__name__} with args={args}, kwargs={kwargs}")
        
        try:
            result = func(*args, **kwargs)
            duration = time.time() - start_time
            logger.debug(f"Completed {func.__name__} in {duration:.2f}s")
            return result
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"Error in {func.__name__} after {duration:.2f}s: {e}")
            raise
    
    return wrapper


def setup_debug_logging() -> None:
    """Enable debug logging for troubleshooting."""
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    
    # Enable debug for key modules
    logging.getLogger("data_sources").setLevel(logging.DEBUG)
    logging.getLogger("processing").setLevel(logging.DEBUG)
    logging.getLogger("models").setLevel(logging.DEBUG)
    logging.getLogger("storage").setLevel(logging.DEBUG)
    
    logger = logging.getLogger(__name__)
    logger.info("Debug logging enabled")


def disable_debug_logging() -> None:
    """Disable debug logging to reduce noise."""
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    logger = logging.getLogger(__name__)
    logger.info("Debug logging disabled")