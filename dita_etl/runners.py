"""Deprecated — use ``dita_etl.io.subprocess_runner`` instead."""

import warnings

warnings.warn(
    "dita_etl.runners is deprecated. Use dita_etl.io.subprocess_runner instead.",
    DeprecationWarning,
    stacklevel=2,
)

from dita_etl.io.subprocess_runner import RunnerError as SubprocessError  # noqa: F401
from dita_etl.io.subprocess_runner import SubprocessRunner  # noqa: F401

__all__ = ["SubprocessRunner", "SubprocessError"]
