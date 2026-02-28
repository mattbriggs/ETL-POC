"""Unit tests for dita_etl.stages.extract.ExtractStage."""

from pathlib import Path

import pytest

from dita_etl.contracts import ExtractInput
from dita_etl.io.subprocess_runner import RunnerError
from dita_etl.stages.extract import ExtractStage


class RecordingRunner:
    def __init__(self, fail_on: set[str] | None = None) -> None:
        self.calls: list[list[str]] = []
        self.fail_on: set[str] = fail_on or set()

    def run(self, args: list[str], cwd: str | None = None) -> str:
        self.calls.append(list(args))
        if "-o" in args:
            dst = args[args.index("-o") + 1]
            if any(dst == f for f in self.fail_on):
                raise RunnerError(f"Simulated failure: {dst}")
            Path(dst).parent.mkdir(parents=True, exist_ok=True)
            Path(dst).write_text("<docbook/>", encoding="utf-8")
        return ""


def _make_sources(tmp: Path) -> list[str]:
    (tmp / "a.md").write_text("# A\n", encoding="utf-8")
    (tmp / "b.html").write_text("<h1>B</h1>", encoding="utf-8")
    (tmp / "c.docx").write_bytes(b"PK\x03\x04stub")
    return [str(tmp / "a.md"), str(tmp / "b.html"), str(tmp / "c.docx")]


class TestExtractStage:
    def _stage(self) -> ExtractStage:
        return ExtractStage(pandoc_path="/usr/local/bin/pandoc")

    def test_success_all_files(self, tmp_path, monkeypatch):
        files = _make_sources(tmp_path)
        runner = RecordingRunner()
        stage = self._stage()

        # Monkeypatch SubprocessRunner inside extract stage
        import dita_etl.stages.extract as mod
        monkeypatch.setattr(mod, "SubprocessRunner", lambda: runner)

        input_ = ExtractInput(
            source_paths=tuple(files),
            intermediate_dir=str(tmp_path / "intermediate"),
        )
        output = stage.run(input_)

        assert output.success is True
        assert set(output.outputs.keys()) == set(files)
        for dst in output.outputs.values():
            assert Path(dst).exists()

    def test_partial_failure(self, tmp_path, monkeypatch):
        files = _make_sources(tmp_path)
        # Compute what the destination for b.html would be
        import dita_etl.stages.extract as mod

        b_xml = str(tmp_path / "intermediate" / "b.xml")
        runner = RecordingRunner(fail_on={b_xml})
        monkeypatch.setattr(mod, "SubprocessRunner", lambda: runner)

        input_ = ExtractInput(
            source_paths=tuple(files),
            intermediate_dir=str(tmp_path / "intermediate"),
        )
        output = self._stage().run(input_)

        assert output.success is False
        assert len(output.errors) == 1

    def test_unknown_extension_recorded_as_error(self, tmp_path, monkeypatch):
        strange = tmp_path / "doc.xyz"
        strange.write_text("content")

        import dita_etl.stages.extract as mod
        runner = RecordingRunner()
        monkeypatch.setattr(mod, "SubprocessRunner", lambda: runner)

        input_ = ExtractInput(
            source_paths=(str(strange),),
            intermediate_dir=str(tmp_path / "intermediate"),
        )
        output = self._stage().run(input_)
        assert output.success is False
        assert str(strange) in output.errors

    def test_output_schema(self, tmp_path, monkeypatch):
        files = _make_sources(tmp_path)
        import dita_etl.stages.extract as mod
        monkeypatch.setattr(mod, "SubprocessRunner", lambda: RecordingRunner())

        input_ = ExtractInput(
            source_paths=tuple(files),
            intermediate_dir=str(tmp_path / "intermediate"),
        )
        output = self._stage().run(input_)

        assert isinstance(output.outputs, dict)
        assert isinstance(output.errors, dict)
        assert isinstance(output.success, bool)
