"""CLI smoke tests for dita_etl.cli."""

from __future__ import annotations

import textwrap

import pytest
from click.testing import CliRunner

from dita_etl.cli import main
from dita_etl.contracts import (
    AssessOutput,
    ExtractOutput,
    LoadOutput,
    PipelineOutput,
    TransformOutput,
)


def _fake_pipeline_result(tmp_path, extract_errors: dict | None = None) -> PipelineOutput:
    """Build a minimal PipelineOutput suitable for monkeypatching."""
    map_path = str(tmp_path / "out.ditamap")
    return PipelineOutput(
        assess=AssessOutput(
            inventory_path=str(tmp_path / "inventory.json"),
            dedupe_path=str(tmp_path / "dedupe.json"),
            report_path=str(tmp_path / "report.html"),
            plans_dir=str(tmp_path / "plans"),
        ),
        extract=ExtractOutput(
            outputs={} if extract_errors else {"f.md": "f.xml"},
            errors=extract_errors or {},
        ),
        transform=TransformOutput(topics={"f.md": [map_path]}, errors={}),
        load=LoadOutput(map_path=map_path, topic_count=1),
    )


class TestCliHelp:
    def test_main_help(self):
        result = CliRunner().invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "DITA ETL Pipeline" in result.output

    def test_run_help(self):
        result = CliRunner().invoke(main, ["run", "--help"])
        assert result.exit_code == 0
        assert "--config" in result.output
        assert "--input" in result.output

    def test_assess_help(self):
        result = CliRunner().invoke(main, ["assess", "--help"])
        assert result.exit_code == 0
        assert "--config" in result.output


class TestCliRunErrors:
    def test_run_missing_config_exits_1(self, tmp_path):
        result = CliRunner().invoke(main, [
            "run",
            "--config", str(tmp_path / "nonexistent.yaml"),
            "--assess-config", str(tmp_path / "assess.yaml"),
            "--input", str(tmp_path),
        ])
        assert result.exit_code == 1

    def test_run_unexpected_error_exits_2(self, monkeypatch):
        def bad_run(**kw):
            raise RuntimeError("something went wrong")

        monkeypatch.setattr("dita_etl.cli.run_pipeline", bad_run)
        result = CliRunner().invoke(main, ["run"])
        assert result.exit_code == 2
        assert "Unexpected error" in result.output


class TestCliRunSuccess:
    def test_run_prints_map_path(self, monkeypatch, tmp_path):
        fake = _fake_pipeline_result(tmp_path)
        monkeypatch.setattr("dita_etl.cli.run_pipeline", lambda **kw: fake)

        result = CliRunner().invoke(main, ["run"])
        assert result.exit_code == 0
        assert "Pipeline complete" in result.output
        assert fake.map_path in result.output

    def test_run_warns_on_extract_errors(self, monkeypatch, tmp_path):
        fake = _fake_pipeline_result(tmp_path, extract_errors={"f.md": "pandoc failed"})
        monkeypatch.setattr("dita_etl.cli.run_pipeline", lambda **kw: fake)

        # Default CliRunner mixes stderr into output, so the secho warning is visible.
        result = CliRunner().invoke(main, ["run"])
        assert result.exit_code == 0
        assert "Extract errors" in result.output


class TestCliAssessSuccess:
    def test_assess_command_produces_report(self, tmp_path):
        input_dir = tmp_path / "input"
        input_dir.mkdir()
        (input_dir / "guide.md").write_text(
            "# Guide\n\nContent about the system.\n", encoding="utf-8"
        )
        config_path = tmp_path / "config.yaml"
        config_path.write_text(
            textwrap.dedent(f"""\
                dita_output:
                  output_folder: {tmp_path / 'out'}
                  map_title: Test Map
            """),
            encoding="utf-8",
        )
        assess_config_path = tmp_path / "assess.yaml"
        assess_config_path.write_text("", encoding="utf-8")

        result = CliRunner().invoke(main, [
            "assess",
            "--config", str(config_path),
            "--assess-config", str(assess_config_path),
            "--input", str(input_dir),
        ])
        assert result.exit_code == 0
        assert "Assessment complete" in result.output


class TestCliAssessErrors:
    def test_assess_missing_config_exits_1(self, tmp_path):
        result = CliRunner().invoke(main, [
            "assess",
            "--config", str(tmp_path / "nonexistent.yaml"),
        ])
        assert result.exit_code == 1
