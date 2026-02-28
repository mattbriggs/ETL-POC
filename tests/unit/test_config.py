"""Unit tests for dita_etl.config."""

import textwrap

import pytest

from dita_etl.config import (
    ClassificationRule,
    Config,
    Chunking,
    DITAOutput,
    Tooling,
)


def _write_yaml(tmp_path, content: str) -> str:
    p = tmp_path / "config.yaml"
    p.write_text(textwrap.dedent(content))
    return str(p)


class TestClassificationRule:
    def test_pattern_alias(self):
        r = ClassificationRule(pattern="guide.*", type="task")
        assert r.pattern == "guide.*"
        assert r.topic_type == "task"
        assert r.type == "task"

    def test_match_alias(self):
        r = ClassificationRule(match="index", type="concept")
        assert r.pattern == "index"

    def test_pattern_takes_precedence_over_match(self):
        r = ClassificationRule(match="old", pattern="new", type="reference")
        assert r.pattern == "new"


class TestConfigLoad:
    def test_load_minimal(self, tmp_path):
        path = _write_yaml(tmp_path, "")
        cfg = Config.load(path)
        assert isinstance(cfg, Config)
        assert cfg.tooling.pandoc_path == "pandoc"

    def test_load_tooling(self, tmp_path):
        path = _write_yaml(
            tmp_path,
            """\
            tooling:
              pandoc_path: /custom/pandoc
              java_path: /usr/bin/java
            """,
        )
        cfg = Config.load(path)
        assert cfg.tooling.pandoc_path == "/custom/pandoc"
        assert cfg.tooling.java_path == "/usr/bin/java"

    def test_load_dita_output(self, tmp_path):
        path = _write_yaml(
            tmp_path,
            """\
            dita_output:
              output_folder: build/myout
              map_title: My Book
            """,
        )
        cfg = Config.load(path)
        assert cfg.dita_output.output_folder == "build/myout"
        assert cfg.dita_output.map_title == "My Book"

    def test_load_classification_rules(self, tmp_path):
        path = _write_yaml(
            tmp_path,
            """\
            classification_rules:
              by_filename:
                - match: "index"
                  type: "concept"
              by_content:
                - match: "procedure"
                  type: "task"
            """,
        )
        cfg = Config.load(path)
        assert len(cfg.classification_rules["by_filename"]) == 1
        assert cfg.classification_rules["by_filename"][0].topic_type == "concept"
        assert cfg.classification_rules["by_content"][0].topic_type == "task"

    def test_load_missing_file(self):
        with pytest.raises(FileNotFoundError):
            Config.load("/nonexistent/path/config.yaml")


class TestSourceExtensions:
    def test_returns_extensions_from_config(self, tmp_path):
        path = _write_yaml(
            tmp_path,
            """\
            source_formats:
              treat_as_html: [".html", ".htm"]
              treat_as_md: [".md"]
            """,
        )
        cfg = Config.load(path)
        exts = cfg.source_extensions()
        assert ".html" in exts
        assert ".htm" in exts
        assert ".md" in exts

    def test_returns_defaults_when_empty(self, tmp_path):
        path = _write_yaml(tmp_path, "")
        cfg = Config.load(path)
        exts = cfg.source_extensions()
        # Default source_formats has treat_as_markdown: [".md"]
        assert ".md" in exts
