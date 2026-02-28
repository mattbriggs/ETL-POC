"""Unit tests for dita_etl.stages.transform.TransformStage."""

from pathlib import Path

import pytest

from dita_etl.contracts import TransformInput
from dita_etl.stages.transform import TransformStage


def _write_docbook(tmp_path: Path, stem: str, content: str) -> str:
    p = tmp_path / f"{stem}.xml"
    p.write_text(content, encoding="utf-8")
    return str(p)


class TestTransformStage:
    def _stage(self) -> TransformStage:
        return TransformStage()

    def test_generates_concept_by_default(self, tmp_path):
        xml_path = _write_docbook(
            tmp_path, "intro", "<title>Introduction</title><para>Overview text.</para>"
        )
        out_dir = str(tmp_path / "dita")
        input_ = TransformInput(
            intermediates={"intro.md": xml_path},
            output_dir=out_dir,
        )
        output = self._stage().run(input_)

        assert output.success is True
        assert "intro.md" in output.topics
        topic_path = output.topics["intro.md"][0]
        assert Path(topic_path).exists()
        dita = Path(topic_path).read_text(encoding="utf-8")
        assert "<concept" in dita or "<task" in dita or "<reference" in dita

    def test_task_detected_via_content_rules(self, tmp_path):
        from dita_etl.config import ClassificationRule

        xml_path = _write_docbook(
            tmp_path, "guide", "<title>Guide</title><para>Procedure text.</para>"
        )
        out_dir = str(tmp_path / "dita")
        rule = ClassificationRule(pattern="procedure", type="task")
        input_ = TransformInput(
            intermediates={"guide.md": xml_path},
            output_dir=out_dir,
            rules_by_content=(rule,),
        )
        output = self._stage().run(input_)

        assert output.success is True
        topic_path = output.topics["guide.md"][0]
        assert "_task.dita" in topic_path

    def test_missing_xml_file_recorded_as_error(self, tmp_path):
        out_dir = str(tmp_path / "dita")
        input_ = TransformInput(
            intermediates={"missing.md": str(tmp_path / "nonexistent.xml")},
            output_dir=out_dir,
        )
        output = self._stage().run(input_)
        assert output.success is False
        assert "missing.md" in output.errors

    def test_output_schema(self, tmp_path):
        xml_path = _write_docbook(tmp_path, "doc", "<title>Doc</title><para>Content.</para>")
        input_ = TransformInput(
            intermediates={"doc.md": xml_path},
            output_dir=str(tmp_path / "dita"),
        )
        output = self._stage().run(input_)
        assert isinstance(output.topics, dict)
        assert isinstance(output.errors, dict)
        assert isinstance(output.success, bool)
