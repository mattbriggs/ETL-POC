from ...runners import SubprocessRunner

import os

class DocxOxygenExtractor:
    name = "oxygen-docx"
    exts = (".docx",)

    def __init__(self, oxygen_scripts_dir: str):
        self.oxygen = oxygen_scripts_dir

    def extract(self, src: str, dst: str, runner: SubprocessRunner) -> None:
        # Example: call your Oxygen batch script that yields DocBook/HTML
        script = os.path.join(self.oxygen, "docx2docbook.sh")
        runner.run([script, src, dst])