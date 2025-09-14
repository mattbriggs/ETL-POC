import os
from pathlib import Path
import pytest

from dita_etl.stages.extractors.md_pandoc import MdPandocExtractor
from dita_etl.stages.extractors.html_pandoc import HtmlPandocExtractor
from dita_etl.stages.extractors.docx_pandoc import DocxPandocExtractor
from dita_etl.runners import SubprocessRunner

class DummyRunner(SubprocessRunner):
    def __init__(self):
        super().__init__()
        self.calls = []

    def run(self, args):
        self.calls.append(list(args))
        if "-o" in args:
            dst = args[-1]
            Path(dst).parent.mkdir(parents=True, exist_ok=True)
            Path(dst).write_text("<docbook/>", encoding="utf-8")

def _assert_common_pandoc_shape(call, reader, src, dst):
    # pandoc binary
    assert call[0].endswith("pandoc")
    # reader
    assert call[1] == "-f"
    assert call[2] == reader
    # writer
    assert call[3] == "-t"
    assert call[4] == "docbook"
    # source and output
    assert call[-3] == src
    assert call[-2] == "-o"
    assert call[-1] == dst

def test_md_pandoc_args(tmp_path):
    runner = DummyRunner()
    ext = MdPandocExtractor(pandoc_path="/usr/local/bin/pandoc")
    src = str(tmp_path / "a.md")
    dst = str(tmp_path / "out.xml")
    Path(src).write_text("# Title\n\nContent", encoding="utf-8")

    ext.extract(src, dst, runner)

    assert Path(dst).exists()
    assert len(runner.calls) == 1
    _assert_common_pandoc_shape(runner.calls[0], "gfm", src, dst)

def test_html_pandoc_args(tmp_path):
    runner = DummyRunner()
    ext = HtmlPandocExtractor(pandoc_path="/usr/local/bin/pandoc")
    src = str(tmp_path / "b.html")
    dst = str(tmp_path / "out.xml")
    Path(src).write_text("<h1>B</h1>", encoding="utf-8")

    ext.extract(src, dst, runner)

    assert Path(dst).exists()
    _assert_common_pandoc_shape(runner.calls[0], "html", src, dst)

def test_docx_pandoc_args(tmp_path):
    runner = DummyRunner()
    ext = DocxPandocExtractor(pandoc_path="/usr/local/bin/pandoc")
    src = str(tmp_path / "c.docx")
    dst = str(tmp_path / "out.xml")
    Path(src).write_bytes(b"PK\x03\x04stubdocx")

    ext.extract(src, dst, runner)

    assert Path(dst).exists()
    _assert_common_pandoc_shape(runner.calls[0], "docx", src, dst)