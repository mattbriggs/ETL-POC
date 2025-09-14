from ...runners import SubprocessRunner

class DocxPandocExtractor:
    name = "pandoc-docx"
    exts = (".docx",)

    def __init__(self, pandoc_path: str):
        self.pandoc = pandoc_path

    def extract(self, src: str, dst: str, runner: SubprocessRunner) -> None:
        args = [self.pandoc, "-f", "docx", "-t", "docbook", src, "-o", dst]
        runner.run(args)