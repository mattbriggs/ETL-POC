"""Deprecated — use ``dita_etl.io.filesystem`` instead."""

import warnings

warnings.warn(
    "dita_etl.io_utils is deprecated. Use dita_etl.io.filesystem instead.",
    DeprecationWarning,
    stacklevel=2,
)

from dita_etl.io.filesystem import (  # noqa: F401
    copy_assets as quarantine,
    ensure_dir,
    read_text,
    write_text,
)
from dita_etl.io.filesystem import copy_assets as copy_into  # noqa: F401

__all__ = ["ensure_dir", "write_text", "read_text", "quarantine", "copy_into"]
