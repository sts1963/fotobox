from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path


def configure_logging(
    log_file: Path,
    level: int = logging.INFO,
    max_bytes: int = 5 * 1024 * 1024,
    backup_count: int = 5,
) -> None:
    """
    Configure application logging.

    Logs are written both to stdout and to a rotating file.
    """

    log_file.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    root_logger = logging.getLogger()

    # Avoid duplicate handlers when tests/imports reload modules.
    if getattr(root_logger, "_fotobox_configured", False):
        return

    root_logger.setLevel(level)

    formatter = logging.Formatter(
        "%(asctime)s "
        "%(levelname)-8s "
        "%(name)s: "
        "%(message)s"
    )

    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)

    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8",
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)

    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)

    root_logger._fotobox_configured = True

