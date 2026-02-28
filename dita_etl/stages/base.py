"""Deprecated — stages now use typed contracts from ``dita_etl.contracts``.

``StageResult`` and the abstract ``Stage`` base class are retained here for
backwards compatibility only. New stages should accept and return the
concrete contract dataclasses defined in ``dita_etl.contracts``.
"""

from __future__ import annotations

import warnings
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

warnings.warn(
    "dita_etl.stages.base (StageResult, Stage) is deprecated. "
    "Use typed contracts from dita_etl.contracts instead.",
    DeprecationWarning,
    stacklevel=2,
)


@dataclass
class StageResult:
    """Deprecated generic stage result. Use typed output contracts instead."""

    success: bool
    message: str
    data: dict[str, Any] = field(default_factory=dict)


class Stage(ABC):
    """Deprecated abstract base class. Stages no longer inherit from this."""

    @abstractmethod
    def run(self, **kwargs) -> StageResult:  # type: ignore[override]
        ...
