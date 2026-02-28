"""Unit tests for dita_etl.stages.load.LoadStage."""

from pathlib import Path

import pytest

from dita_etl.contracts import LoadInput
from dita_etl.stages.load import LoadStage


def _create_topic(out_dir: Path, name: str) -> str:
    """Create a stub DITA topic inside *out_dir*/topics/ so relative paths work."""
    topics = out_dir / "topics"
    topics.mkdir(parents=True, exist_ok=True)
    p = topics / name
    p.write_text(f"<concept id='c1'><title>{name}</title><conbody/></concept>")
    return str(p)


class TestLoadStage:
    def _stage(self) -> LoadStage:
        return LoadStage()

    def test_writes_ditamap(self, tmp_path):
        out_dir = str(tmp_path / "dita")
        Path(out_dir).mkdir()
        topic = _create_topic(Path(out_dir), "guide_task.dita")
        input_ = LoadInput(
            topics={"src.md": [topic]},
            output_dir=out_dir,
            map_title="My Map",
        )
        output = self._stage().run(input_)

        assert Path(output.map_path).exists()
        map_text = Path(output.map_path).read_text(encoding="utf-8")
        assert "<map>" in map_text
        assert "<title>My Map</title>" in map_text
        assert "<topicref" in map_text

    def test_topic_count(self, tmp_path):
        out_dir = str(tmp_path / "dita")
        Path(out_dir).mkdir()
        topics = [_create_topic(Path(out_dir), f"t{i}.dita") for i in range(3)]
        input_ = LoadInput(
            topics={f"src{i}.md": [topics[i]] for i in range(3)},
            output_dir=out_dir,
            map_title="Map",
        )
        output = self._stage().run(input_)
        assert output.topic_count == 3

    def test_empty_topics_produces_empty_map(self, tmp_path):
        out_dir = str(tmp_path / "dita")
        Path(out_dir).mkdir()
        input_ = LoadInput(topics={}, output_dir=out_dir, map_title="Empty")
        output = self._stage().run(input_)
        assert output.topic_count == 0
        assert Path(output.map_path).exists()

    def test_copies_assets_when_intermediate_dir_provided(self, tmp_path):
        intermediate = tmp_path / "intermediate"
        images = intermediate / "images"
        images.mkdir(parents=True)
        (images / "logo.png").write_bytes(b"\x89PNG stub")

        out_dir = str(tmp_path / "dita")
        Path(out_dir).mkdir()
        topic = _create_topic(Path(out_dir), "doc.dita")
        input_ = LoadInput(
            topics={"doc.md": [topic]},
            output_dir=out_dir,
            map_title="Map",
            intermediate_dir=str(intermediate),
        )
        self._stage().run(input_)
        assert (Path(out_dir) / "assets" / "images" / "logo.png").exists()

    def test_map_title_escaped(self, tmp_path):
        out_dir = str(tmp_path / "dita")
        Path(out_dir).mkdir()
        input_ = LoadInput(topics={}, output_dir=out_dir, map_title="A & B")
        self._stage().run(input_)
        map_text = Path(out_dir, "index.ditamap").read_text(encoding="utf-8")
        assert "A &amp; B" in map_text
