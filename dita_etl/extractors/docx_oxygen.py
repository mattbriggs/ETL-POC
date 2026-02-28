"""DOCX → DocBook extractor via Oxygen XML Editor batch scripts."""

from __future__ import annotations

import os

from dita_etl.io.subprocess_runner import Runner


class DocxOxygenExtractor:
    """Converts DOCX to DocBook using Oxygen XML Editor's batch conversion scripts.

    Use this extractor when Pandoc's DOCX rendering is insufficient and an
    Oxygen XML Editor installation is available.

    :param oxygen_scripts_dir: Path to the Oxygen scripts directory, e.g.
        ``/Applications/Oxygen XML Editor.app/Contents/tools/scripts``.
    """

    name = "oxygen-docx"
    exts = (".docx",)

    def __init__(self, oxygen_scripts_dir: str) -> None:
        self._scripts_dir = oxygen_scripts_dir

    def extract(self, src: str, dst: str, runner: Runner) -> None:
        """Convert *src* (DOCX) to DocBook XML at *dst* via Oxygen scripts.

        :param src: Source DOCX file path.
        :param dst: Destination DocBook XML file path.
        :param runner: Subprocess runner.
        :raises RunnerError: If the Oxygen script exits with a non-zero code.
        """
        script = os.path.join(self._scripts_dir, "docx2docbook.sh")
        runner.run([script, src, dst])
