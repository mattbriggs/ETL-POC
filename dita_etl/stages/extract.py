
from __future__ import annotations
import os, pathlib
from typing import List, Dict
from .base import Stage, StageResult
from ..runners import SubprocessRunner, SubprocessError
from ..io_utils import ensure_dir
from ..hashing import file_sha256

class ExtractStage(Stage):
    def __init__(self, pandoc_path: str, oxygen_scripts_dir: str | None, intermediate_dir: str, runner: SubprocessRunner | None = None):
        self.pandoc_path = pandoc_path
        self.oxygen_scripts_dir = oxygen_scripts_dir
        self.intermediate_dir = intermediate_dir
        self.runner = runner or SubprocessRunner()

    def _pandoc_to_docbook(self, src: str, dst: str) -> None:
        args = [self.pandoc_path, "-f", "auto", "-t", "docbook", src, "-o", dst]
        self.runner.run(args)

    def run(self, inputs: List[str]) -> StageResult:
        ensure_dir(self.intermediate_dir)
        outputs: Dict[str, str] = {}
        errors: Dict[str, str] = {}
        for src in inputs:
            base = pathlib.Path(src).stem + ".xml"
            dst = os.path.join(self.intermediate_dir, base)
            try:
                self._pandoc_to_docbook(src, dst)
                outputs[src] = dst
            except SubprocessError as e:
                errors[src] = str(e)
        msg = f"Extracted {len(outputs)} / {len(inputs)} files to intermediate."
        return StageResult(success=len(errors)==0, message=msg, data={"outputs": outputs, "errors": errors})
