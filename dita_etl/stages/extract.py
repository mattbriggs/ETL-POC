from __future__ import annotations

import os
import pathlib
import shutil
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List

from .base import Stage, StageResult
from ..runners import SubprocessRunner, SubprocessError
from ..io_utils import ensure_dir

from .extractors.base import FileExtractor
from .extractors.md_pandoc import MdPandocExtractor
from .extractors.html_pandoc import HtmlPandocExtractor
from .extractors.docx_pandoc import DocxPandocExtractor
from .extractors.docx_oxygen import DocxOxygenExtractor


class ExtractStage(Stage):
    """
    ExtractStage:
    Routes files to format-specific extractors and produces intermediate XML (DocBook).
    - Supports Markdown, HTML, and DOCX formats.
    - Preserves folder structure for assets (styles/images).
    - Threaded per-file execution for I/O-bound extractors.
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

        # Default parallelism for subprocess I/O
        self.max_workers = max_workers or max(2, min(8, (os.cpu_count() or 4)))

    def _build_registry(self, overrides: Dict[str, str]) -> Dict[str, FileExtractor]:
        """
        Create a registry mapping file extensions to extractor instances.
        Allows optional overrides from configuration.
        """
        handlers: List[FileExtractor] = [
            MdPandocExtractor(self.pandoc_path),     # .md → DocBook
            HtmlPandocExtractor(self.pandoc_path),   # .html/.htm → DocBook
            DocxPandocExtractor(self.pandoc_path),   # .docx → DocBook
        ]

        registry: Dict[str, FileExtractor] = {}
        name_map = {h.name: h for h in handlers}

        for handler in handlers:
            for ext in getattr(handler, "exts", ()):
                registry[ext.lower()] = handler

        # Optional: Enable Oxygen DOCX handler
        # if self.oxygen_scripts_dir:
        #     oxy = DocxOxygenExtractor(self.oxygen_scripts_dir)
        #     name_map[oxy.name] = oxy

        # Apply any overrides from config
        for ext, name in overrides.items():
            if name in name_map:
                registry[ext.lower()] = name_map[name]

        return registry

    def _extract_one(self, src: str) -> tuple[str, str]:
        """
        Extract a single file to intermediate XML using its registered handler.
        """
        ext = pathlib.Path(src).suffix.lower()
        base_name = pathlib.Path(src).stem + ".xml"
        dst = os.path.join(self.intermediate_dir, base_name)

        handler = self.registry.get(ext)
        if not handler:
            raise SubprocessError(f"No extractor registered for extension: {ext}")

        handler.extract(src, dst, self.runner)
        return src, dst


    def _copy_assets(self, src_root: str):
        """
        Copy asset directories or flat-file assets from src_root into the intermediate_dir.
        Supports local, network, and cloud-synced (OneDrive/iCloud) folders safely.
        """
        import shutil
        from ..io_utils import ensure_dir

        asset_folders = ("styles", "images", "imagers")

        for folder in asset_folders:
            src_path = os.path.join(src_root, folder)
            dst_path = os.path.join(self.intermediate_dir, folder)

            if not os.path.exists(src_path):
                continue

            ensure_dir(dst_path)

            # Iterate contents to handle both files and subdirectories
            for item in os.listdir(src_path):
                src_item = os.path.join(src_path, item)
                dst_item = os.path.join(dst_path, item)

                # Copy files directly
                if os.path.isfile(src_item):
                    try:
                        shutil.copy2(src_item, dst_item)
                    except Exception as e:
                        print(f"⚠️ Skipped file {src_item}: {e}")

                # Recursively copy subfolders
                elif os.path.isdir(src_item):
                    try:
                        shutil.copytree(src_item, dst_item, dirs_exist_ok=True)
                    except Exception as e:
                        print(f"⚠️ Skipped folder {src_item}: {e}")


    def run(self, inputs: List[str]) -> StageResult:
        """
        Run extraction for all source files.
        Produces intermediate XMLs and copies static assets.
        """
        ensure_dir(self.intermediate_dir)
        ensure_dir(os.path.join(self.intermediate_dir, "styles"))
        ensure_dir(os.path.join(self.intermediate_dir, "images"))

        # Infer root of inputs for asset copying
        if inputs:
            common_root = str(pathlib.Path(inputs[0]).parents[0])
            self._copy_assets(common_root)

        outputs: Dict[str, str] = {}
        errors: Dict[str, str] = {}

        with ThreadPoolExecutor(max_workers=self.max_workers) as pool:
            futures = {pool.submit(self._extract_one, src): src for src in inputs}
            for fut in as_completed(futures):
                src = futures[fut]
                try:
                    src_file, dst_file = fut.result()
                    outputs[src_file] = dst_file
                except Exception as exc:
                    errors[src] = str(exc)

        success = len(errors) == 0
        message = f"Extracted {len(outputs)} / {len(inputs)} files to intermediate."

        return StageResult(
            success=success,
            message=message,
            data={"outputs": outputs, "errors": errors},
        )