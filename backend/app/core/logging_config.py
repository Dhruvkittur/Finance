"""
FinPilot AI — Logging Configuration
=====================================
Structured JSON logging for production with:
- Console handler for development
- File rotation for production
- Correlation ID propagation
- Log level control via environment
"""

import logging
import logging.handlers
import os
import sys
from pathlib import Path


class JSONFormatter(logging.Formatter):
    """Format log records as structured JSON for production log aggregation."""

    def format(self, record: logging.LogRecord) -> str:
        import json
        from datetime import datetime, timezone

        log_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Include extra fields (e.g., request_id)
        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id
        if hasattr(record, "user_id"):
            log_data["user_id"] = record.user_id

        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data)


def configure_logging() -> None:
    """
    Configure application-wide logging.
    Uses colored console output in development and JSON file logging in production.
    """
    from app.core.config import settings

    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

    # Create log directory
    log_dir = Path(settings.LOG_DIR)
    log_dir.mkdir(parents=True, exist_ok=True)

    handlers = []

    # ── Console Handler ────────────────────────────────────────────────────────
    console_handler = logging.StreamHandler(sys.stdout)
    if settings.APP_DEBUG:
        console_format = "%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(message)s"
        console_handler.setFormatter(logging.Formatter(console_format, datefmt="%H:%M:%S"))
    else:
        console_handler.setFormatter(JSONFormatter())
    handlers.append(console_handler)

    # ── File Handler (Rotating) ────────────────────────────────────────────────
    file_handler = logging.handlers.RotatingFileHandler(
        filename=log_dir / "finpilot.log",
        maxBytes=settings.LOG_MAX_SIZE_MB * 1024 * 1024,
        backupCount=settings.LOG_BACKUP_COUNT,
        encoding="utf-8",
    )
    file_handler.setFormatter(JSONFormatter())
    handlers.append(file_handler)

    # ── Error File Handler ─────────────────────────────────────────────────────
    error_handler = logging.handlers.RotatingFileHandler(
        filename=log_dir / "finpilot_errors.log",
        maxBytes=settings.LOG_MAX_SIZE_MB * 1024 * 1024,
        backupCount=settings.LOG_BACKUP_COUNT,
        encoding="utf-8",
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(JSONFormatter())
    handlers.append(error_handler)

    # ── Root Logger Configuration ──────────────────────────────────────────────
    logging.basicConfig(
        level=log_level,
        handlers=handlers,
        force=True,
    )

    # Suppress noisy third-party loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(
        logging.INFO if settings.DATABASE_ECHO else logging.WARNING
    )
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("chromadb").setLevel(logging.WARNING)
