"""Unit tests for dita_etl.extractors (individual extractor classes)."""

from pathlib import Path

import pytest

from dita_etl.extractors.docx_pandoc import DocxPandocExtractor
from dita_etl.extractors.html_pandoc import HtmlPandocExtractor
from dita_etl.extractors.md_pandoc import MdPandocExtractor
from dita_etl.extractors.registry import build_registry
from dita_etl.io.subprocess_runner import RunnerError


class RecordingRunner:
    """Test double that records calls and writes a stub XML output file."""

    def __init__(self, fail_on: set[str] | None = None) -> None:
        self.calls: list[list[str]] = []
        self.fail_on: set[str] = fail_on or set()

    def run(self, args: list[str], cwd: str | None = None) -> str:
        self.calls.append(list(args))
        # Identify destination from -o flag
        if "-o" in args:
            dst = args[args.index("-o") + 1]
            if dst in self.fail_on:
                raise RunnerError(f"Simulated failure for {dst}")
            Path(dst).parent.mkdir(parents=True, exist_ok=True)
            Path(dst).write_text("<docbook/>", encoding="utf-8")
        return ""


def _assert_pandoc_args(call: list[str], reader: str, src: str, dst: str) -> None:
    assert call[0].endswith("pandoc"), f"Expected pandoc, got {call[0]}"
    assert call[1] == "-f"
    assert call[2] == reader
    assert call[3] == "-t"
    assert call[4] == "docbook"
    assert src in call
    assert "-o" in call
    assert dst in call


class TestMdPandocExtractor:
    def test_args_shape(self, tmp_path):
        runner = RecordingRunner()
        ext = MdPandocExtractor("/usr/local/bin/pandoc")
        src = str(tmp_path / "a.md")
        dst = str(tmp_path / "a.xml")
        Path(src).write_text("# Title\n\nContent", encoding="utf-8")

        ext.extract(src, dst, runner)

        assert len(runner.calls) == 1
        _assert_pandoc_args(runner.calls[0], "gfm", src, dst)

    def test_attrs(self):
        ext = MdPandocExtractor("pandoc")
        assert ext.name == "pandoc-md"
        assert ".md" in ext.exts


class TestHtmlPandocExtractor:
    def test_args_shape(self, tmp_path):
        runner = RecordingRunner()
        ext = HtmlPandocExtractor("/usr/local/bin/pandoc")
        src = str(tmp_path / "b.html")
        dst = str(tmp_path / "b.xml")
        Path(src).write_text("<h1>B</h1>", encoding="utf-8")

        ext.extract(src, dst, runner)

        _assert_pandoc_args(runner.calls[0], "html", src, dst)

    def test_handles_htm_extension(self):
        ext = HtmlPandocExtractor("pandoc")
        assert ".htm" in ext.exts


class TestDocxPandocExtractor:
    def test_args_shape(self, tmp_path):
        runner = RecordingRunner()
        ext = DocxPandocExtractor("/usr/local/bin/pandoc")
        src = str(tmp_path / "c.docx")
        dst = str(tmp_path / "c.xml")
        Path(src).write_bytes(b"PK\x03\x04stub")

        ext.extract(src, dst, runner)

        _assert_pandoc_args(runner.calls[0], "docx", src, dst)


class TestBuildRegistry:
    def test_default_mappings(self):
        reg = build_registry(pandoc_path="pandoc")
        assert ".md" in reg
        assert ".html" in reg
        assert ".htm" in reg
        assert ".docx" in reg
        assert isinstance(reg[".md"], MdPandocExtractor)
        assert isinstance(reg[".html"], HtmlPandocExtractor)
        assert isinstance(reg[".docx"], DocxPandocExtractor)

    def test_override_docx(self, tmp_path):
        scripts_dir = str(tmp_path)
        reg = build_registry(
            pandoc_path="pandoc",
            handler_overrides={".docx": "oxygen-docx"},
            oxygen_scripts_dir=scripts_dir,
        )
        from dita_etl.extractors.docx_oxygen import DocxOxygenExtractor
        assert isinstance(reg[".docx"], DocxOxygenExtractor)

    def test_unknown_override_raises(self):
        with pytest.raises(ValueError, match="Unknown extractor"):
            build_registry(
                pandoc_path="pandoc",
                handler_overrides={".md": "nonexistent-extractor"},
            )
