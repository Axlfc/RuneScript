import io
import logging
import sys
from datetime import datetime


class Logger:
    """Simple logger for Git GUI operations"""

    def __init__(self, log_file=None):
        self.logger = logging.getLogger("GitGUI")
        self.logger.setLevel(logging.INFO)

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)

        # Formatter
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(formatter)

        # Add console handler
        self.logger.addHandler(console_handler)

        # File handler (optional)
        if log_file:
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(logging.INFO)
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)

    def info(self, message):
        self.logger.info(message)

    def error(self, message):
        self.logger.error(message)

    def warning(self, message):
        self.logger.warning(message)

    def debug(self, message):
        self.logger.debug(message)


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        # Console handler (UTF-8 safe)
        console_stream = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
        handler = logging.StreamHandler(console_stream)

        console_handler = logging.StreamHandler(console_stream)

        # File handler
        file_handler = logging.FileHandler("git_cli.log", encoding='utf-8')

        formatter = logging.Formatter('[%(asctime)s] %(levelname)s: %(message)s')
        for h in (console_handler, file_handler):
            h.setFormatter(formatter)
            logger.addHandler(h)

        logger.setLevel(logging.INFO)

    return logger

