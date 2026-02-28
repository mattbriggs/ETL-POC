"""Deprecated — use ``dita_etl.assess.config`` instead."""

import warnings

warnings.warn(
    "dita_etl.assess.assess_config is deprecated. "
    "Use dita_etl.assess.config.AssessConfig instead.",
    DeprecationWarning,
    stacklevel=2,
)

from dita_etl.assess.config import (  # noqa: F401
    AssessConfig,
    Duplication,
    Limits,
    Shingling,
    ScoringWeights,
)

__all__ = ["AssessConfig", "Shingling", "ScoringWeights", "Limits", "Duplication"]
