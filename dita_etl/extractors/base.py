"""FileExtractor protocol — the Strategy interface for format extraction.

Any object that satisfies :class:`FileExtractor` can be registered as an
extractor without subclassing. This keeps extractors orthogonal and trivially
testable in isolation.
"""

from __future__ import annotations

from typing import Protocol

from dita_etl.io.subprocess_runner import Runner


class FileExtractor(Protocol):
    """Protocol for format-specific document extractors.

    Implementations convert a single source file into intermediate DocBook XML.
    They must be stateless and thread-safe so they can be shared across a
    :class:`~concurrent.futures.ThreadPoolExecutor`.

    :cvar name: Unique extractor identifier (e.g. ``"pandoc-md"``).
    :cvar exts: Tuple of file extensions handled by this extractor
        (e.g. ``(".md",)``).
    """

    name: str
    exts: tuple[str, ...]

    def extract(self, src: str, dst: str, runner: Runner) -> None:
        """Convert *src* to DocBook XML at *dst*.

        :param src: Absolute path to the source document.
        :param dst: Absolute path where the DocBook XML output should be written.
        :param runner: Subprocess runner used to invoke external tools.
        :raises RunnerError: If the underlying tool exits with a non-zero code.
        """
        ...
