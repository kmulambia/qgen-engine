from concurrent_log_handler import ConcurrentRotatingFileHandler
import logging
from pathlib import Path
from functools import lru_cache
from typing import Optional, Union

# NOTE : To change
# Constants
DEFAULT_LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
DEFAULT_LOG_LEVEL = logging.INFO
MAX_LOG_SIZE = 100 * 1024 * 1024  # 5MB
BACKUP_COUNT = 3


class LogSetup:
    """
    Simple logging setup with file rotation and console output.
    Uses singleton pattern to avoid multiple instantiations.
    """
    _instance = None
    _initialized_loggers = {}
    _default_log_dir = Path("logs")

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LogSetup, cls).__new__(cls)
            # Ensure logs directory exists
            cls._default_log_dir.mkdir(exist_ok=True)
        return cls._instance

    @classmethod
    def setup_logger(
            cls,
            name: str,
            log_path: Optional[Union[str, Path]] = None,
            level: int = DEFAULT_LOG_LEVEL,
            console: bool = True,
            sqlalchemy_log_level: int = logging.CRITICAL
    ) -> logging.Logger:
        """
        Set up a logger with both file and console handlers.

        Args:
            name: Logger name
            log_path: Path to log file
            level: Logging level for the main logger
            console: Whether to output to console
            sqlalchemy_log_level: Log level for SQLAlchemy logs
        """
        # Return existing logger if already set up
        if name in cls._initialized_loggers:
            return cls._initialized_loggers[name]

        logger = logging.getLogger(name)
        logger.setLevel(level)

        # Prevent duplicate handlers
        logger.handlers.clear()

        # Create formatter
        formatter = logging.Formatter(DEFAULT_LOG_FORMAT)

        # Add console handler if requested
        if console:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)

        # If no log_path provided, create default one in logs directory
        if log_path is None:
            log_path = cls._default_log_dir / f"{name.replace('.', '_')}.log"
        else:
            log_path = Path(log_path)
            log_path.parent.mkdir(parents=True, exist_ok=True)

        # Add file handler
        file_handler = ConcurrentRotatingFileHandler(
            str(log_path),
            maxBytes=MAX_LOG_SIZE,
            backupCount=BACKUP_COUNT,
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        # Configure SQLAlchemy logs for both file and console
        cls._setup_sqlalchemy_logs(sqlalchemy_log_level, formatter)

        # Store logger in initialized loggers
        cls._initialized_loggers[name] = logger
        return logger

    @classmethod
    def _setup_sqlalchemy_logs(cls, sqlalchemy_log_level: int, formatter: logging.Formatter):
        """Configure SQLAlchemy logging for both file and console."""
        # SQLAlchemy engine logger
        sqlalchemy_logger = logging.getLogger("sqlalchemy.engine")
        sqlalchemy_logger.setLevel(sqlalchemy_log_level)

        # Remove existing handlers to avoid duplication
        sqlalchemy_logger.handlers.clear()

        # Add console handler for SQLAlchemy logs
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        sqlalchemy_logger.addHandler(console_handler)

        # Add file handler for SQLAlchemy logs
        file_handler = ConcurrentRotatingFileHandler(
            str(cls._default_log_dir / "sqlalchemy.log"),
            maxBytes=MAX_LOG_SIZE,
            backupCount=BACKUP_COUNT,
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        sqlalchemy_logger.addHandler(file_handler)


@lru_cache(maxsize=None)
def get_logger(
        name: str,
        log_path: Optional[Union[str, Path]] = None,
        level: int = DEFAULT_LOG_LEVEL,
        sqlalchemy_log_level: int = logging.CRITICAL
) -> logging.Logger:
    """
    Get or create a logger with the specified configuration.

    Args:
        name: Logger name
        log_path: Path to log file (optional)
        level: Logging level
        sqlalchemy_log_level: Log level for SQLAlchemy logs

    Returns:
        Configured logger instance

    Example:
        >>> logger = get_logger("my_app")  # Will create logs/my_app.log
        >>> logger.info("Application started")
    """
    return LogSetup().setup_logger(
        name,
        log_path,
        level,
        sqlalchemy_log_level=sqlalchemy_log_level
    )
