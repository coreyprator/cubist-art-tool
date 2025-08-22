"""
Cubist Logger Utility
Reusable logging setup for CLI, GUI, and tests.
"""

import os
import logging

LOG_DIR = os.path.join(os.path.dirname(__file__), "logs")
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "run_log.txt")
ERROR_LOG_FILE = os.path.join(LOG_DIR, "error_log.txt")

logger = logging.getLogger("cubist_logger")
logger.setLevel(logging.INFO)

# File handler for all logs
if not logger.hasHandlers():
    file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
    file_handler.setLevel(logging.INFO)
    file_formatter = logging.Formatter("[%(asctime)s] %(levelname)s: %(message)s")
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    # File handler for errors only
    error_handler = logging.FileHandler(ERROR_LOG_FILE, encoding="utf-8")
    error_handler.setLevel(logging.ERROR)
    error_formatter = logging.Formatter("[%(asctime)s] %(levelname)s: %(message)s")
    error_handler.setFormatter(error_formatter)
    logger.addHandler(error_handler)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter("%(levelname)s: %(message)s")
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)


def log_message(message, level="info"):
    """
    Log a message to the main Cubist logger.
    Args:
        message (str): The message to log.
        level (str): Log level ('info', 'error', 'warning', 'debug').
    """
    if level == "info":
        logger.info(message)
    elif level == "error":
        logger.error(message)
    elif level == "warning":
        logger.warning(message)
    elif level == "debug":
        logger.debug(message)
    else:
        logger.info(message)
