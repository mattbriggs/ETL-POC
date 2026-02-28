"""Deprecated — use ``dita_etl.io.filesystem`` instead."""

import warnings

warnings.warn(
    "dita_etl.hashing is deprecated. Use dita_etl.io.filesystem instead.",
    DeprecationWarning,
    stacklevel=2,
)

from dita_etl.io.filesystem import file_sha256, normalize_path, text_sha256  # noqa: F401

__all__ = ["file_sha256", "text_sha256", "normalize_path"]
