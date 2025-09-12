
from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict

@dataclass
class StageResult:
    success: bool
    message: str
    data: Dict[str, Any]

class Stage(ABC):
    @abstractmethod
    def run(self, **kwargs) -> StageResult:
        ...
