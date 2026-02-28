"""Structured logging configuration for the pipeline.

Logging is configured at the orchestration boundary only. Stage internals
are silent by default; callers that want per-stage visibility should set
the appropriate log level.

Usage::

    from dita_etl.logging_config import configure_logging
    configure_logging(level="INFO")
"""

from __future__ import annotations

import logging
import sys


def configure_logging(level: str = "INFO") -> None:
    """Configure the root ``dita_etl`` logger with a structured formatter.

    :param level: Logging level name (e.g. ``"DEBUG"``, ``"INFO"``,
        ``"WARNING"``).  Case-insensitive.
    """
    numeric_level = getattr(logging, level.upper(), logging.INFO)

    handler = logging.StreamHandler(sys.stderr)
    handler.setLevel(numeric_level)
    handler.setFormatter(_StructuredFormatter())

    logger = logging.getLogger("dita_etl")
    logger.setLevel(numeric_level)
    logger.handlers.clear()
    logger.addHandler(handler)
    logger.propagate = False


def get_logger(name: str) -> logging.Logger:
    """Return a child logger under the ``dita_etl`` namespace.

    :param name: Dotted sub-name, e.g. ``"pipeline"`` or ``"stages.extract"``.
    :returns: A :class:`logging.Logger` instance.
    """
    return logging.getLogger(f"dita_etl.{name}")


class _StructuredFormatter(logging.Formatter):
    """Minimal structured log formatter.

    Emits lines in the form::

        [LEVEL] dita_etl.pipeline | message  {key=value ...}
    """

    def format(self, record: logging.LogRecord) -> str:
        level = record.levelname
        name = record.name
        msg = record.getMessage()

        # Collect any extra key=value pairs attached to the record.
        reserved = {
            "args", "created", "exc_info", "exc_text", "filename",
            "funcName", "levelname", "levelno", "lineno", "message",
            "module", "msecs", "msg", "name", "pathname", "process",
            "processName", "relativeCreated", "stack_info", "taskName",
            "thread", "threadName",
        }
        extras = {
            k: v for k, v in record.__dict__.items() if k not in reserved
        }
        suffix = "  {" + "  ".join(f"{k}={v!r}" for k, v in extras.items()) + "}" if extras else ""
        return f"[{level}] {name} | {msg}{suffix}"
