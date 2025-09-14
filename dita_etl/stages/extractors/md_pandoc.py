from __future__ import annotations
from ...runners import SubprocessRunner

class MdPandocExtractor:
    name = "pandoc-md"
    exts = (".md",)

    def __init__(self, pandoc_path: str):
        self.pandoc = pandoc_path

    def extract(self, src: str, dst: str, runner: SubprocessRunner) -> None:
        args = [self.pandoc, "-f", "gfm", "-t", "docbook", src, "-o", dst]
        runner.run(args)