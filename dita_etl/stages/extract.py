"""Stage 1 — Extract.

Routes each source file to its registered format extractor and produces
intermediate DocBook XML files. Uses a thread pool for parallel I/O-bound
subprocess calls.
"""

from __future__ import annotations

import os
import pathlib
from concurrent.futures import ThreadPoolExecutor, as_completed

from dita_etl.contracts import ExtractInput, ExtractOutput
from dita_etl.extractors.base import FileExtractor
from dita_etl.extractors.registry import build_registry
from dita_etl.io.filesystem import copy_assets, ensure_dir
from dita_etl.io.subprocess_runner import RunnerError, SubprocessRunner


class ExtractStage:
    """Stage 1: convert source documents to intermediate DocBook XML.

    Supports Markdown, HTML, and DOCX via Pandoc by default. Additional
    or overridden extractors can be injected via ``handler_overrides``.

    :param pandoc_path: Path or command name for the Pandoc binary.
    :param oxygen_scripts_dir: Optional path to Oxygen XML scripts directory.
    """

    def __init__(
        self,
        pandoc_path: str,
        oxygen_scripts_dir: str | None = None,
    ) -> None:
        self._pandoc_path = pandoc_path
        self._oxygen_scripts_dir = oxygen_scripts_dir

    def run(self, input_: ExtractInput) -> ExtractOutput:
        """Execute the extraction stage.

        :param input_: Validated :class:`~dita_etl.contracts.ExtractInput`
            contract.
        :returns: :class:`~dita_etl.contracts.ExtractOutput` contract
            containing paths to intermediate XML files and any errors.
        """
        registry = build_registry(
            pandoc_path=self._pandoc_path,
            handler_overrides=input_.handler_overrides or {},
            oxygen_scripts_dir=self._oxygen_scripts_dir,
        )
        runner = SubprocessRunner()
        ensure_dir(input_.intermediate_dir)
        ensure_dir(os.path.join(input_.intermediate_dir, "styles"))
        ensure_dir(os.path.join(input_.intermediate_dir, "images"))

        # Copy assets from the common source root
        if input_.source_paths:
            src_root = str(pathlib.Path(input_.source_paths[0]).parent)
            copy_assets(src_root, input_.intermediate_dir)

        max_workers = input_.max_workers or max(2, min(8, os.cpu_count() or 4))

        outputs: dict[str, str] = {}
        errors: dict[str, str] = {}

        with ThreadPoolExecutor(max_workers=max_workers) as pool:
            futures = {
                pool.submit(
                    self._extract_one,
                    src,
                    input_.intermediate_dir,
                    registry,
                    runner,
                ): src
                for src in input_.source_paths
            }
            for future in as_completed(futures):
                src = futures[future]
                try:
                    src_out, dst_out = future.result()
                    outputs[src_out] = dst_out
                except Exception as exc:  # noqa: BLE001
                    errors[src] = str(exc)

        return ExtractOutput(outputs=outputs, errors=errors)

    @staticmethod
    def _extract_one(
        src: str,
        intermediate_dir: str,
        registry: dict[str, FileExtractor],
        runner: SubprocessRunner,
    ) -> tuple[str, str]:
        """Extract a single source file to intermediate XML.

        :param src: Source file path.
        :param intermediate_dir: Directory for the output XML.
        :param registry: Extension → extractor mapping.
        :param runner: Subprocess runner.
        :returns: ``(src_path, dst_path)`` tuple.
        :raises RunnerError: If the extractor subprocess fails.
        """
        ext = pathlib.Path(src).suffix.lower()
        handler = registry.get(ext)
        if handler is None:
            raise RunnerError(f"No extractor registered for extension: {ext!r}")
        dst = os.path.join(intermediate_dir, pathlib.Path(src).stem + ".xml")
        handler.extract(src, dst, runner)
        return src, dst
