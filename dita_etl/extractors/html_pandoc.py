"""HTML → DocBook extractor via Pandoc."""

from __future__ import annotations

from dita_etl.io.subprocess_runner import Runner


class HtmlPandocExtractor:
    """Converts HTML documents to DocBook 5 using Pandoc.

    :param pandoc_path: Absolute path or command name for the Pandoc binary.
    """

    name = "pandoc-html"
    exts = (".html", ".htm")

    def __init__(self, pandoc_path: str) -> None:
        self._pandoc = pandoc_path

    def extract(self, src: str, dst: str, runner: Runner) -> None:
        """Convert *src* (HTML) to DocBook XML at *dst*.

        :param src: Source HTML file path.
        :param dst: Destination DocBook XML file path.
        :param runner: Subprocess runner.
        """
        runner.run([self._pandoc, "-f", "html", "-t", "docbook", src, "-o", dst])
