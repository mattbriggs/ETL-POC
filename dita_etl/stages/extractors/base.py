from __future__ import annotations
from typing import Protocol
from ...runners import SubprocessRunner

class FileExtractor(Protocol):
    name: str
    exts: tuple[str, ...]  # handled extensions, e.g. (".md",)

    def extract(self, src: str, dst: str, runner: SubprocessRunner) -> None:
        ...