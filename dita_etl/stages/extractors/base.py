"""Deprecated — use ``dita_etl.extractors.base`` instead."""

import warnings

warnings.warn(
    "dita_etl.stages.extractors is deprecated. "
    "Use dita_etl.extractors instead.",
    DeprecationWarning,
    stacklevel=2,
)

from dita_etl.extractors.base import FileExtractor  # noqa: F401

__all__ = ["FileExtractor"]
