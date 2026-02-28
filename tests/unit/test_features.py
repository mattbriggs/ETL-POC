"""Unit tests for dita_etl.assess.features."""

from dita_etl.assess.features import count_tokens, extract_features, imperative_density

_LANDMARKS = {
    "task_keywords": ["click", "run", "open"],
    "task_landmarks": ["steps", "prerequisites"],
    "reference_markers": ["parameters", "syntax"],
}


class TestCountTokens:
    def test_simple_words(self):
        assert count_tokens("hello world") == 2

    def test_punctuation_excluded(self):
        assert count_tokens("hello, world!") == 2

    def test_empty_string(self):
        assert count_tokens("") == 0

    def test_numbers_counted(self):
        assert count_tokens("step 1 of 3") == 4


class TestImperativeDensity:
    def test_no_imperatives(self):
        assert imperative_density("The sky is blue.", ["click", "run"]) == 0.0

    def test_with_imperatives(self):
        density = imperative_density("Click here and run the script.", ["click", "run"])
        assert density > 0.0

    def test_empty_text_returns_zero(self):
        assert imperative_density("", ["click"]) == 0.0


class TestExtractFeatures:
    def _section(self, title="", content=""):
        return {"title": title, "content": content}

    def test_basic_token_count(self):
        feats = extract_features(self._section(content="Hello world test"), _LANDMARKS)
        assert feats["tokens"] == 3

    def test_ordered_list_detected(self):
        content = "1. First item\n2. Second item"
        feats = extract_features(self._section(content=content), _LANDMARKS)
        assert feats["ordered_lists"] >= 2

    def test_unordered_list_detected(self):
        content = "- Item A\n- Item B"
        feats = extract_features(self._section(content=content), _LANDMARKS)
        assert feats["unordered_lists"] >= 2

    def test_table_detected(self):
        content = "| A | B |\n|---|---|\n| 1 | 2 |"
        feats = extract_features(self._section(content=content), _LANDMARKS)
        assert feats["tables"] >= 1

    def test_has_steps_title(self):
        feats = extract_features(self._section(title="Steps to Install"), _LANDMARKS)
        assert feats["has_steps_title"] is True

    def test_no_steps_title(self):
        feats = extract_features(self._section(title="Introduction"), _LANDMARKS)
        assert feats["has_steps_title"] is False

    def test_reference_markers_counted(self):
        content = "The parameters and syntax are explained below."
        feats = extract_features(self._section(content=content), _LANDMARKS)
        assert feats["reference_markers"] >= 2

    def test_empty_section(self):
        feats = extract_features(self._section(), _LANDMARKS)
        assert feats["tokens"] == 0
        assert feats["tables"] == 0
