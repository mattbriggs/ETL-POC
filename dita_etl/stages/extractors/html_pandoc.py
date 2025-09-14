from ...runners import SubprocessRunner

class HtmlPandocExtractor:
    name = "pandoc-html"
    exts = (".html", ".htm")

    def __init__(self, pandoc_path: str):
        self.pandoc = pandoc_path

    def extract(self, src: str, dst: str, runner: SubprocessRunner) -> None:
        args = [self.pandoc, "-f", "html", "-t", "docbook", src, "-o", dst]
        runner.run(args)