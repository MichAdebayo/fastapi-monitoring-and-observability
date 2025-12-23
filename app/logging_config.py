from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional


def setup_logging(log_file: Optional[str] = None, level: int = logging.INFO) -> None:
    """Configure a central logger that writes to a file and the console.

    - Ensures the `logs/` directory exists.
    - Adds a rotating file handler writing to `logs/app.log` by default.
    - Leaves existing handlers for uvicorn intact while ensuring our module
      loggers emit to the file.
    """
    if log_file is None:
        log_file = "logs/app.log"

    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Standard message format: timestamp + level + [context] message
    formatter = logging.Formatter("%(asctime)s %(levelname)-5s [%(name)s] %(message)s")

    # Avoid adding duplicate file handlers if called multiple times
    for h in list(root_logger.handlers):
        if isinstance(h, RotatingFileHandler) and getattr(
            h, "baseFilename", None
        ) == str(log_path):
            break
    else:
        file_handler = RotatingFileHandler(
            str(log_path), maxBytes=10 * 1024 * 1024, backupCount=3
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    # Console handler for local development (mirror file format)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # Ensure our app logger uses the same level and expose short-named contexts
    logging.getLogger("app").setLevel(level)
    logging.getLogger("api").setLevel(level)
    logging.getLogger("db").setLevel(level)
    logging.getLogger("service.item").setLevel(level)
