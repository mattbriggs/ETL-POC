"""Unit tests for dita_etl.transforms.dita."""

import pytest

from dita_etl.transforms.dita import (
    build_map,
    build_topic,
    extract_body,
    extract_title,
    make_topicref,
)


class TestExtractTitle:
    def test_finds_title_tag(self):
        assert extract_title("<title>Hello World</title><para>body</para>") == "Hello World"

    def test_case_insensitive(self):
        assert extract_title("<TITLE>Caps</TITLE>") == "Caps"

    def test_missing_title_returns_untitled(self):
        assert extract_title("<para>No title here.</para>") == "Untitled"

    def test_returns_first_title_only(self):
        assert extract_title("<title>First</title><title>Second</title>") == "First"


class TestExtractBody:
    def test_converts_para_to_p(self):
        xml = "<para>Hello world.</para>"
        body = extract_body(xml)
        assert "<p>Hello world.</p>" in body

    def test_multiple_paras(self):
        xml = "<para>One.</para><para>Two.</para>"
        body = extract_body(xml)
        assert "<p>One.</p>" in body
        assert "<p>Two.</p>" in body

    def test_fallback_strips_tags(self):
        xml = "<section><b>plain text</b></section>"
        body = extract_body(xml)
        assert "<p>" in body
        assert "plain text" in body


class TestBuildTopic:
    def test_concept_structure(self):
        xml = build_topic("My Title", "<p>Body.</p>", "concept")
        assert "<concept" in xml
        assert "<title>My Title</title>" in xml
        assert "<conbody>" in xml

    def test_task_structure(self):
        xml = build_topic("Install", "<p>Step 1.</p>", "task")
        assert "<task" in xml
        assert "<taskbody>" in xml

    def test_reference_structure(self):
        xml = build_topic("API Ref", "<p>Params.</p>", "reference")
        assert "<reference" in xml
        assert "<refbody>" in xml

    def test_title_is_escaped(self):
        xml = build_topic("A & B", "<p>Body.</p>", "concept")
        assert "A &amp; B" in xml

    def test_invalid_type_raises(self):
        with pytest.raises(ValueError, match="Unknown topic_type"):
            build_topic("Title", "<p>Body.</p>", "invalid_type")

    def test_custom_id(self):
        xml = build_topic("T", "<p>B.</p>", "concept", topic_id="myid")
        assert 'id="myid"' in xml


class TestMakeTopicref:
    def test_relative_path(self, tmp_path):
        topic = tmp_path / "topics" / "guide_task.dita"
        topic.parent.mkdir()
        topic.write_text("content")
        ref = make_topicref(str(topic), str(tmp_path))
        assert 'href="topics/guide_task.dita"' in ref

    def test_returns_topicref_element(self, tmp_path):
        topic = tmp_path / "a.dita"
        topic.write_text("x")
        ref = make_topicref(str(topic), str(tmp_path))
        assert ref.strip().startswith("<topicref")


class TestBuildMap:
    def test_contains_title(self, tmp_path):
        topic = tmp_path / "a_concept.dita"
        topic.write_text("x")
        xml = build_map("My Map", [str(topic)], str(tmp_path))
        assert "<title>My Map</title>" in xml

    def test_contains_topicref(self, tmp_path):
        topic = tmp_path / "a_concept.dita"
        topic.write_text("x")
        xml = build_map("Map", [str(topic)], str(tmp_path))
        assert "<topicref" in xml

    def test_empty_topics(self, tmp_path):
        xml = build_map("Empty Map", [], str(tmp_path))
        assert "<title>Empty Map</title>" in xml
        assert "<topicref" not in xml

    def test_title_escaped(self, tmp_path):
        xml = build_map("A & B", [], str(tmp_path))
        assert "A &amp; B" in xml
