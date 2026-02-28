"""Deprecated — use ``dita_etl.assess.report`` instead."""

import warnings

warnings.warn(
    "dita_etl.assess.emit is deprecated. Use dita_etl.assess.report instead.",
    DeprecationWarning,
    stacklevel=2,
)

from dita_etl.assess.report import render_report_html, write_json, write_text  # noqa: F401

__all__ = ["write_json", "render_report_html", "write_text"]
