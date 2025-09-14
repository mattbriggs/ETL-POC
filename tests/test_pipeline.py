
import os
import io
import json
import shutil
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Assume project structure: dita_etl/stages/... etc.
# We import the classes under test; adjust import roots if your package name differs.
from dita_etl.stages.extract import ExtractStage
from dita_etl.stages.extractors.md_pandoc import MdPandocExtractor
from dita_etl.stages.extractors.html_pandoc import HtmlPandocExtractor
from dita_etl.stages.extractors.docx_pandoc import DocxPandocExtractor

from dita_etl.runners import SubprocessRunner, SubprocessError


@pytest.fixture()
def tmpdir():
    d = Path(tempfile.mkdtemp(prefix="etltest_"))
    try:
        yield d
    finally:
        shutil.rmtree(d, ignore_errors=True)


class DummyRunner(SubprocessRunner):
    """A runner that records the args and can be configured to fail on certain sources."""
    def __init__(self, fail_on=None):
        super().__init__()
        self.calls = []
        self.fail_on = set(fail_on or [])

    def run(self, args):
        # args example: [pandoc, -f, gfm, -t, docbook, src, -o, dst]
        self.calls.append(list(args))
        src = args[-3] if "-o" in args else args[-1]  # naive, fine for our CLI shapes
        if src in self.fail_on:
            raise SubprocessError(f"Boom: {src}")
        # pretend it created output
        if "-o" in args:
            dst = args[-1]
            Path(dst).parent.mkdir(parents=True, exist_ok=True)
            Path(dst).write_text("<docbook/>", encoding="utf-8")


def make_sources(tmp: Path):
    files = []
    (tmp / "a.md").write_text("# A\n", encoding="utf-8")
    files.append(str(tmp / "a.md"))
    (tmp / "b.html").write_text("<h1>B</h1>", encoding="utf-8")
    files.append(str(tmp / "b.html"))
    (tmp / "c.docx").write_bytes(b"PK\x03\x04stubdocx")  # doesn't matter; we mock runner
    files.append(str(tmp / "c.docx"))
    return files


def test_registry_default_mapping(tmpdir):
    stage = ExtractStage(
        pandoc_path="/usr/local/bin/pandoc",
        oxygen_scripts_dir=None,
        intermediate_dir=str(tmpdir / "intermediate"),
        runner=DummyRunner(),
    )

    # Verify ext -> handler mapping
    reg = stage.registry
    assert ".md" in reg and isinstance(reg[".md"], MdPandocExtractor)
    assert ".html" in reg and isinstance(reg[".html"], HtmlPandocExtractor)
    assert ".htm" in reg and isinstance(reg[".htm"], HtmlPandocExtractor)
    assert ".docx" in reg and isinstance(reg[".docx"], DocxPandocExtractor)


def test_extract_parallel_success(tmpdir):
    files = make_sources(tmpdir)
    runner = DummyRunner()
    stage = ExtractStage(
        pandoc_path="/usr/local/bin/pandoc",
        oxygen_scripts_dir=None,
        intermediate_dir=str(tmpdir / "intermediate"),
        runner=runner,
        max_workers=4,
    )

    res = stage.run(files)
    assert res.success is True
    # All files extracted
    assert set(res.data["outputs"].keys()) == set(files)
    # Outputs exist
    for dst in res.data["outputs"].values():
        assert Path(dst).exists()
        assert Path(dst).read_text(encoding="utf-8").strip() == "<docbook/>"
    # We should have one pandoc invocation per file
    assert len(runner.calls) == len(files)
    # Ensure args include expected -f reader per ext
    calls_str = [" ".join(c) for c in runner.calls]
    assert any(" -f gfm -t docbook " in c for c in calls_str)  # md
    assert any(" -f html -t docbook " in c for c in calls_str)  # html/htm
    assert any(" -f docx -t docbook " in c for c in calls_str)  # docx


def test_extract_parallel_with_failures(tmpdir):
    files = make_sources(tmpdir)
    # Force one file to fail
    failing_src = str(tmpdir / "b.html")
    runner = DummyRunner(fail_on={failing_src})

    stage = ExtractStage(
        pandoc_path="/usr/local/bin/pandoc",
        oxygen_scripts_dir=None,
        intermediate_dir=str(tmpdir / "intermediate"),
        runner=runner,
        max_workers=3,
    )

    res = stage.run(files)
    # Should not be fully successful
    assert res.success is False
    # Exactly one error captured
    assert set(res.data["errors"].keys()) == {failing_src}
    # Others succeeded
    succeeded = set(files) - {failing_src}
    assert set(res.data["outputs"].keys()) == succeeded
    for s in succeeded:
        assert Path(res.data["outputs"][s]).exists()


def test_handler_overrides(tmpdir, monkeypatch):
    files = make_sources(tmpdir)
    # Create a fake oxygen extractor and ensure override routes .docx to it
    from types import SimpleNamespace

    class FakeOxy:
        name = "oxygen-docx"
        exts = (".docx",)
        def __init__(self, scripts_dir): self.scripts_dir = scripts_dir
        def extract(self, src, dst, runner): 
            Path(dst).parent.mkdir(parents=True, exist_ok=True)
            Path(dst).write_text("<docbook via oxygen/>", encoding="utf-8")

    # Monkeypatch registry builder to include our fake oxygen handler
    from dita_etl.stages import extract as extract_mod

    orig_build = extract_mod.ExtractStage._build_registry

    def patched_build(self, overrides):
        reg = orig_build(self, overrides)
        # inject fake by name into name map behavior: mimic override by replacing mapping directly
        reg[".docx"] = FakeOxy("/tmp/oxygen")
        # If user passed override to oxygen-docx, it's already mapped above.
        return reg

    monkeypatch.setattr(extract_mod.ExtractStage, "_build_registry", patched_build)

    stage = ExtractStage(
        pandoc_path="/usr/local/bin/pandoc",
        oxygen_scripts_dir="/opt/oxygen/scripts",
        intermediate_dir=str(tmpdir / "intermediate"),
        runner=DummyRunner(),
        handler_overrides={".docx": "oxygen-docx"},
        max_workers=2,
    )

    res = stage.run(files)
    # .docx should come from oxygen path
    docx_out = res.data["outputs"][str(tmpdir / "c.docx")]
    assert Path(docx_out).read_text(encoding="utf-8").strip() == "<docbook via oxygen/>"


def test_return_schema(tmpdir):
    files = make_sources(tmpdir)
    stage = ExtractStage(
        pandoc_path="/usr/local/bin/pandoc",
        oxygen_scripts_dir=None,
        intermediate_dir=str(tmpdir / "intermediate"),
        runner=DummyRunner(),
        max_workers=2,
    )
    res = stage.run(files)
    assert set(res.data.keys()) == {"outputs", "errors"}
    assert isinstance(res.data["outputs"], dict)
    assert isinstance(res.data["errors"], dict)
    assert isinstance(res.success, bool)
    assert isinstance(res.message, str)
