"""Deprecated — use ``dita_etl.transforms.classify`` instead."""

import warnings

warnings.warn(
    "dita_etl.classify is deprecated. Use dita_etl.transforms.classify instead.",
    DeprecationWarning,
    stacklevel=2,
)

from dita_etl.transforms.classify import classify_topic  # noqa: F401

__all__ = ["classify_topic"]
