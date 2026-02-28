"""Unit tests for dita_etl.assess.structure."""

from dita_etl.assess.structure import heading_ladder_valid, sectionize_markdown


class TestSectionizeMarkdown:
    def test_single_heading(self):
        text = "# Title\n\nSome content."
        secs = sectionize_markdown(text)
        assert len(secs) >= 1
        titled = [s for s in secs if s["title"] == "Title"]
        assert titled
        assert "Some content." in titled[0]["content"]

    def test_multiple_headings(self):
        text = "# One\n\nFirst.\n## Two\n\nSecond."
        secs = sectionize_markdown(text)
        titles = [s["title"] for s in secs]
        assert "One" in titles
        assert "Two" in titles

    def test_preamble_before_first_heading(self):
        text = "Intro text.\n# Section"
        secs = sectionize_markdown(text)
        assert secs[0]["title"] == "Document"
        assert "Intro text." in secs[0]["content"]

    def test_empty_input(self):
        secs = sectionize_markdown("")
        assert secs == []

    def test_heading_levels_recorded(self):
        text = "# H1\n\n## H2\n\n### H3\n\n"
        secs = sectionize_markdown(text)
        levels = [s["level"] for s in secs if s["title"] in ("H1", "H2", "H3")]
        assert levels == [1, 2, 3]

    def test_no_headings_returns_single_section(self):
        text = "Just some plain text without headings."
        secs = sectionize_markdown(text)
        assert len(secs) == 1
        assert secs[0]["title"] == "Document"


class TestHeadingLadderValid:
    def test_valid_sequential(self):
        secs = [
            {"level": 1}, {"level": 2}, {"level": 3}
        ]
        assert heading_ladder_valid(secs) is True

    def test_valid_with_decrements(self):
        secs = [
            {"level": 2}, {"level": 3}, {"level": 2}
        ]
        assert heading_ladder_valid(secs) is True

    def test_invalid_skip(self):
        secs = [
            {"level": 1}, {"level": 3}  # skips 2
        ]
        assert heading_ladder_valid(secs) is False

    def test_empty_returns_true(self):
        assert heading_ladder_valid([]) is True

    def test_single_section_returns_true(self):
        assert heading_ladder_valid([{"level": 2}]) is True

    def test_same_level_repeated_is_valid(self):
        secs = [{"level": 2}, {"level": 2}, {"level": 2}]
        assert heading_ladder_valid(secs) is True
