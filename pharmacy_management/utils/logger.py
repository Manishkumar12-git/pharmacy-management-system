"""
================================================================================
Pharmacy Management System - Structured Logging Utility
================================================================================
Module: pharmacy_management.utils.logger
Quality Objective: Q10 - Improve Documentation & Traceability

Description:
    Provides structured, thread-safe logging facilities across all system tiers.
    Configures both a rotating file logger for permanent auditability and
    a formatted console stream for developer diagnostics.
================================================================================
"""

import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from pharmacy_management.config import settings

_loggers = {}


def setup_system_logging(log_file: str = None, level: str = None) -> logging.Logger:
    """Configures the root logging infrastructure for the pharmacy application.

    Args:
        log_file (str, optional): Target log file path. Defaults to settings.LOG_FILE.
        level (str, optional): Logging verbosity level ('DEBUG', 'INFO', 'WARNING', 'ERROR').
            Defaults to settings.LOG_LEVEL.

    Returns:
        logging.Logger: The configured root logger instance.
    """
    file_path = log_file or settings.LOG_FILE
    log_level = getattr(logging, (level or settings.LOG_LEVEL).upper(), logging.INFO)

    root_logger = logging.getLogger("PharmaCare")
    root_logger.setLevel(log_level)

    # Avoid duplicate handlers if setup is called multiple times
    if root_logger.handlers:
        return root_logger

    formatter = logging.Formatter(
        fmt=settings.LOG_FORMAT,
        datefmt=settings.LOG_DATE_FORMAT
    )

    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # Rotating File Handler (Max 5MB per file, up to 5 backups)
    try:
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)
        file_handler = RotatingFileHandler(
            file_path,
            maxBytes=5 * 1024 * 1024,
            backupCount=5,
            encoding="utf-8"
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    except Exception as exc:
        root_logger.warning("Failed to initialize rotating file logger: %s", exc)

    return root_logger


def get_logger(module_name: str) -> logging.Logger:
    """Returns a namespaced logger child for the requested module.

    Args:
        module_name (str): The name of the calling module (typically __name__).

    Returns:
        logging.Logger: Namespaced logger object.
    """
    if module_name not in _loggers:
        # Ensure root logger initialized
        setup_system_logging()
        logger = logging.getLogger(f"PharmaCare.{module_name}")
        _loggers[module_name] = logger
    return _loggers[module_name]

