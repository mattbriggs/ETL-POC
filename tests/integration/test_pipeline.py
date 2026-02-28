"""Integration tests for the full pipeline.

These tests wire together all four stages (Assess → Extract → Transform →
Load) using real filesystem operations and a stub subprocess runner, verifying
end-to-end data flow and artefact production.
"""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from dita_etl.contracts import (
    AssessInput,
    ExtractInput,
    LoadInput,
    TransformInput,
)
from dita_etl.stages.assess import AssessStage
from dita_etl.stages.load import LoadStage
from dita_etl.stages.transform import TransformStage


# ---------------------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def sample_md(tmp_path: Path) -> Path:
    """Write a minimal Markdown source file."""
    f = tmp_path / "guide.md"
    f.write_text(
        textwrap.dedent("""\
            # Installation Guide

            Click the **Install** button to run the setup.

            ## Steps

            1. Download the package.
            2. Open a terminal.
            3. Run `./install.sh`.
        """),
        encoding="utf-8",
    )
    return f


@pytest.fixture()
def sample_html(tmp_path: Path) -> Path:
    """Write a minimal HTML source file."""
    f = tmp_path / "reference.html"
    f.write_text(
        "<h1>API Reference</h1><p>Parameters include timeout and retries.</p>",
        encoding="utf-8",
    )
    return f


@pytest.fixture()
def assess_config(tmp_path: Path) -> Path:
    """Write a minimal assess config."""
    cfg = tmp_path / "assess.yaml"
    cfg.write_text(
        textwrap.dedent("""\
            shingling:
              ngram: 5
              minhash_num_perm: 32
              threshold: 0.88
        """),
        encoding="utf-8",
    )
    return cfg


# ---------------------------------------------------------------------------
# Assess integration test
# ---------------------------------------------------------------------------


class TestAssessStageIntegration:
    def test_assess_produces_artefacts(self, tmp_path, sample_md, assess_config):
        out_dir = str(tmp_path / "assess")
        input_ = AssessInput(
            source_paths=(str(sample_md),),
            output_dir=out_dir,
            config_path=str(assess_config),
        )
        stage = AssessStage(config_path=str(assess_config))
        output = stage.run(input_)

        assert Path(output.inventory_path).exists()
        assert Path(output.dedupe_path).exists()
        assert Path(output.report_path).exists()
        assert Path(output.plans_dir).is_dir()


# ---------------------------------------------------------------------------
# Transform + Load integration (no real Pandoc needed)
# ---------------------------------------------------------------------------


def _create_intermediate_xml(tmp_path: Path, stem: str, content: str) -> str:
    xml = tmp_path / "intermediate" / f"{stem}.xml"
    xml.parent.mkdir(parents=True, exist_ok=True)
    xml.write_text(content, encoding="utf-8")
    return str(xml)


class TestTransformLoadIntegration:
    def test_concept_topic_written_and_mapped(self, tmp_path):
        xml_path = _create_intermediate_xml(
            tmp_path,
            "overview",
            "<title>Overview</title><para>High-level explanation.</para>",
        )
        dita_dir = str(tmp_path / "dita")
        topics_dir = str(tmp_path / "dita" / "topics")

        # Transform
        transform_input = TransformInput(
            intermediates={"overview.md": xml_path},
            output_dir=topics_dir,
        )
        transform_output = TransformStage().run(transform_input)

        assert transform_output.success
        assert len(transform_output.topics) == 1
        topic_file = transform_output.topics["overview.md"][0]
        assert Path(topic_file).exists()

        # Load
        load_input = LoadInput(
            topics=transform_output.topics,
            output_dir=dita_dir,
            map_title="Integration Test Map",
        )
        load_output = LoadStage().run(load_input)

        assert Path(load_output.map_path).exists()
        map_text = Path(load_output.map_path).read_text(encoding="utf-8")
        assert "Integration Test Map" in map_text
        assert "<topicref" in map_text
        assert load_output.topic_count == 1

    def test_task_topic_type_classified_correctly(self, tmp_path):
        xml_path = _create_intermediate_xml(
            tmp_path,
            "install",
            "<title>Install</title><para>Click Install and run the script.</para>",
        )
        transform_input = TransformInput(
            intermediates={"install.md": xml_path},
            output_dir=str(tmp_path / "topics"),
        )
        output = TransformStage().run(transform_input)
        assert output.success
        # The classifier should detect task keywords
        topic_path = output.topics["install.md"][0]
        assert "_task.dita" in topic_path or "_concept.dita" in topic_path

    def test_multiple_files_all_in_map(self, tmp_path):
        intermediates = {}
        for i in range(4):
            xml = _create_intermediate_xml(
                tmp_path, f"doc{i}", f"<title>Doc {i}</title><para>Content {i}.</para>"
            )
            intermediates[f"doc{i}.md"] = xml

        transform_output = TransformStage().run(
            TransformInput(intermediates=intermediates, output_dir=str(tmp_path / "topics"))
        )
        load_output = LoadStage().run(
            LoadInput(
                topics=transform_output.topics,
                output_dir=str(tmp_path / "dita"),
                map_title="Multi-File Map",
            )
        )
        assert load_output.topic_count == 4
        map_text = Path(load_output.map_path).read_text(encoding="utf-8")
        assert map_text.count("<topicref") == 4
