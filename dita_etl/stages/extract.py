from __future__ import annotations

import os
import pathlib
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List

from .base import Stage, StageResult
from ..runners import SubprocessRunner, SubprocessError
from ..io_utils import ensure_dir

from .extractors.base import FileExtractor
from .extractors.md_pandoc import MdPandocExtractor
from .extractors.html_pandoc import HtmlPandocExtractor
from .extractors.docx_pandoc import DocxPandocExtractor
from .extractors.docx_oxygen import DocxOxygenExtractor  # available if you choose to use it


class ExtractStage(Stage):
    """
    Routes files to format-specific extractors and produces intermediate XML (DocBook).

    - Strategy/Registry pattern: extensions -> extractor instance
    - Threaded per-file execution for I/O-bound CLIs (Pandoc, Oxygen, etc.)
    - Deterministic: caller passes sorted inputs; outputs written to intermediate_dir
    """

    def __init__(
        self,
        pandoc_path: str,
        oxygen_scripts_dir: str | None,
        intermediate_dir: str,
        runner: SubprocessRunner | None = None,
        handler_overrides: Dict[str, str] | None = None,
        max_workers: int | None = None,
    ):
        self.pandoc_path = pandoc_path
        self.oxygen_scripts_dir = oxygen_scripts_dir
        self.intermediate_dir = intermediate_dir
        self.runner = runner or SubprocessRunner()
        self.registry = self._build_registry(handler_overrides or {})
        # Reasonable default: limited parallelism for I/O-bound subprocess calls
        self.max_workers = max_workers or max(2, min(8, (os.cpu_count() or 4)))

    def _build_registry(self, overrides: Dict[str, str]) -> Dict[str, FileExtractor]:
        # Default handlers
        handlers: List[FileExtractor] = [
            MdPandocExtractor(self.pandoc_path),      # .md via Pandoc (gfm)
            HtmlPandocExtractor(self.pandoc_path),    # .html/.htm via Pandoc (html)
            DocxPandocExtractor(self.pandoc_path),    # .docx via Pandoc
            # DocxOxygenExtractor(self.oxygen_scripts_dir)  # enable by override if preferred
        ]

        reg: Dict[str, FileExtractor] = {}
        name_map = {h.name: h for h in handlers}

        # Map extensions to default handlers
        for h in handlers:
            for ext in getattr(h, "exts", ()):
                reg[ext.lower()] = h

        # Allow config overrides, e.g., {".docx": "oxygen-docx"}
        # If you want to support Oxygen explicitly by name, ensure it's in name_map
        # (Uncomment DocxOxygenExtractor above and add to name_map)
        # Example:
        # if self.oxygen_scripts_dir:
        #     oxy = DocxOxygenExtractor(self.oxygen_scripts_dir)
        #     name_map[oxy.name] = oxy

        for ext, name in overrides.items():
            if name in name_map:
                reg[ext.lower()] = name_map[name]

        return reg

    def _extract_one(self, src: str) -> tuple[str, str]:
        ext = pathlib.Path(src).suffix.lower()
        base = pathlib.Path(src).stem + ".xml"
        dst = os.path.join(self.intermediate_dir, base)

        handler = self.registry.get(ext)
        if not handler:
            raise SubprocessError(f"No extractor registered for extension: {ext}")
        handler.extract(src, dst, self.runner)
        return src, dst

    def run(self, inputs: List[str]) -> StageResult:
        ensure_dir(self.intermediate_dir)

        outputs: Dict[str, str] = {}
        errors: Dict[str, str] = {}

        # Parallel per-file extraction (I/O/subprocess-bound; safe with threads)
        with ThreadPoolExecutor(max_workers=self.max_workers) as pool:
            futures = {pool.submit(self._extract_one, src): src for src in inputs}
            for fut in as_completed(futures):
                src = futures[fut]
                try:
                    s, dst = fut.result()
                    outputs[s] = dst
                except Exception as e:
                    # Capture per-file failure; do not abort the entire run
                    errors[src] = str(e)

        msg = f"Extracted {len(outputs)} / {len(inputs)} files to intermediate."
        return StageResult(
            success=len(errors) == 0,
            message=msg,
            data={"outputs": outputs, "errors": errors},
        )