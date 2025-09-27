import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

_LOGGER_NAME = "binance_bot"


def get_log_file_path() -> Path:
    # bot.log at project root
    root = Path(__file__).resolve().parent.parent
    return root / "bot.log"


def setup_logger(name: str = _LOGGER_NAME) -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger  # already configured

    logger.setLevel(logging.INFO)

    # File handler (rotating)
    log_file = get_log_file_path()
    log_file.parent.mkdir(parents=True, exist_ok=True)
    file_handler = RotatingFileHandler(str(log_file), maxBytes=1_000_000, backupCount=3)
    file_formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    # Console handler
    console_handler = logging.StreamHandler()
    console_formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(message)s",
        datefmt="%H:%M:%S",
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    logger.propagate = False
    return logger