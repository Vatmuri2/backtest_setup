# utils/logger.py
import logging
from pathlib import Path
from typing import Optional

__all__ = ['setup_logging']

def setup_logging(
    name: Optional[str] = None,
    log_level: int = logging.INFO,
    log_file: str = "backtest.log",
    console: bool = True
) -> logging.Logger:
    """Configure logging for backtesting
    
    Args:
        name: Logger name
        log_level: Logging level (e.g., logging.INFO)
        log_file: Name of log file
        console: Whether to show logs in console
    """
    logger = logging.getLogger(name or "backtest")
    logger.setLevel(log_level)
    
    # Clear existing handlers
    if logger.hasHandlers():
        logger.handlers.clear()
    
    # Create logs directory if it doesn't exist
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    
    # File handler
    file_handler = logging.FileHandler(logs_dir / log_file)
    file_handler.setFormatter(logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    ))
    logger.addHandler(file_handler)
    
    # Console handler
    if console:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter(
            "%(levelname)s - %(message)s"
        ))
        logger.addHandler(console_handler)
    
    return logger

# Create default logger instance
logger = setup_logging()