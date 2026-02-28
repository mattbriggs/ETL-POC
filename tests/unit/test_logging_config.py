"""Unit tests for dita_etl.logging_config."""

import logging

import pytest

from dita_etl.logging_config import _StructuredFormatter, configure_logging, get_logger


class TestGetLogger:
    def test_returns_logger_in_namespace(self):
        logger = get_logger("pipeline")
        assert logger.name == "dita_etl.pipeline"

    def test_returns_logging_logger(self):
        assert isinstance(get_logger("test"), logging.Logger)

    def test_different_names_different_loggers(self):
        assert get_logger("a") is not get_logger("b")


class TestConfigureLogging:
    def test_sets_debug_level(self):
        configure_logging("DEBUG")
        assert logging.getLogger("dita_etl").level == logging.DEBUG

    def test_sets_info_level(self):
        configure_logging("INFO")
        assert logging.getLogger("dita_etl").level == logging.INFO

    def test_case_insensitive(self):
        configure_logging("warning")
        assert logging.getLogger("dita_etl").level == logging.WARNING

    def test_adds_stream_handler(self):
        configure_logging("INFO")
        logger = logging.getLogger("dita_etl")
        assert any(isinstance(h, logging.StreamHandler) for h in logger.handlers)

    def test_does_not_propagate(self):
        configure_logging("INFO")
        assert logging.getLogger("dita_etl").propagate is False


class TestStructuredFormatter:
    def _make_record(self, msg: str, level: int = logging.INFO, **extras) -> logging.LogRecord:
        record = logging.LogRecord(
            name="dita_etl.pipeline",
            level=level,
            pathname="",
            lineno=0,
            msg=msg,
            args=(),
            exc_info=None,
        )
        for k, v in extras.items():
            setattr(record, k, v)
        return record

    def test_format_contains_level(self):
        fmt = _StructuredFormatter()
        record = self._make_record("hello", logging.WARNING)
        result = fmt.format(record)
        assert "[WARNING]" in result

    def test_format_contains_logger_name(self):
        fmt = _StructuredFormatter()
        record = self._make_record("msg")
        result = fmt.format(record)
        assert "dita_etl.pipeline" in result

    def test_format_contains_message(self):
        fmt = _StructuredFormatter()
        record = self._make_record("my message")
        result = fmt.format(record)
        assert "my message" in result

    def test_extra_fields_included(self):
        fmt = _StructuredFormatter()
        record = self._make_record("event", files=42)
        result = fmt.format(record)
        assert "files" in result
        assert "42" in result

    def test_no_extras_no_braces(self):
        fmt = _StructuredFormatter()
        record = self._make_record("clean")
        result = fmt.format(record)
        # No trailing extras block when no extra keys provided
        assert "{" not in result
