"""Unit tests for dita_etl.transforms.classify."""

import pytest

from dita_etl.config import ClassificationRule
from dita_etl.transforms.classify import TOPIC_TYPES, classify_topic, _validated


class TestValidated:
    def test_known_type_passthrough(self):
        assert _validated("concept") == "concept"
        assert _validated("task") == "task"
        assert _validated("reference") == "reference"

    def test_unknown_type_falls_back_to_concept(self):
        assert _validated("bogus") == "concept"

    def test_normalises_case(self):
        assert _validated("TASK") == "task"
        assert _validated("  Reference  ") == "reference"


class TestClassifyTopic:
    def test_filename_rule_matches(self):
        rules = [ClassificationRule(pattern="guide*", type="task")]
        result = classify_topic("guide.md", "Hello world.", rules, [])
        assert result == "task"

    def test_filename_rule_wildcard(self):
        rules = [ClassificationRule(pattern="*reference*", type="reference")]
        result = classify_topic("api_reference.md", "Some text.", rules, [])
        assert result == "reference"

    def test_content_rule_matches(self):
        rules = [ClassificationRule(pattern="procedure", type="task")]
        result = classify_topic("doc.md", "This is a procedure.", [], rules)
        assert result == "task"

    def test_filename_rule_takes_priority_over_content(self):
        fn_rules = [ClassificationRule(pattern="index*", type="concept")]
        ct_rules = [ClassificationRule(pattern="click", type="task")]
        result = classify_topic("index.md", "Click the button.", fn_rules, ct_rules)
        assert result == "concept"

    def test_task_heuristic(self):
        result = classify_topic("doc.md", "Click the button to select.", [], [])
        assert result == "task"

    def test_reference_heuristic(self):
        result = classify_topic("doc.md", "Parameters include timeout and size.", [], [])
        assert result == "reference"

    def test_default_concept(self):
        result = classify_topic("doc.md", "This is an overview.", [], [])
        assert result == "concept"

    def test_all_return_values_are_valid(self):
        for text in ["Click here", "Parameters table", "Introduction"]:
            assert classify_topic("f.md", text, [], []) in TOPIC_TYPES

    def test_no_rules_no_heuristic_match(self):
        result = classify_topic("doc.md", "The sky is blue.", [], [])
        assert result == "concept"

    # --- Verbatim config.py docstring examples ---

    def test_config_example_filename_rule_index(self):
        # config.py docstring: by_filename match: "index" type: "concept"
        # Regression: bare stem pattern "index" must match "index.md".
        rules = [ClassificationRule(match="index", type="concept")]
        result = classify_topic("index.md", "Overview of the system.", rules, [])
        assert result == "concept"

    def test_config_example_content_rule_procedure(self):
        # config.py docstring: by_content match: "procedure" type: "task"
        rules = [ClassificationRule(match="procedure", type="task")]
        result = classify_topic("doc.md", "Follow this procedure.", [], rules)
        assert result == "task"

    def test_filename_stem_matched_not_full_basename(self):
        # Pattern without wildcard must match the stem, not the full "stem.ext".
        rules = [ClassificationRule(pattern="index", type="concept")]
        assert classify_topic("index.md", "x", rules, []) == "concept"
        assert classify_topic("index.html", "x", rules, []) == "concept"
        assert classify_topic("notindex.md", "x", rules, []) == "concept"

    # --- plan_type parameter tests ---

    def test_plan_type_used_when_no_rule_matches(self):
        # No rules and neutral content → plan_type should be used.
        result = classify_topic("doc.md", "The sky is blue.", [], [], plan_type="reference")
        assert result == "reference"

    def test_config_rule_beats_plan_type(self):
        # A filename rule takes priority over plan_type.
        rules = [ClassificationRule(pattern="guide*", type="task")]
        result = classify_topic("guide.md", "The sky is blue.", rules, [], plan_type="reference")
        assert result == "task"

    def test_plan_type_beats_heuristic(self):
        # Content has "click" (task heuristic), but plan_type says "concept".
        result = classify_topic("doc.md", "Click the button.", [], [], plan_type="concept")
        assert result == "concept"

    def test_invalid_plan_type_ignored(self):
        # An unknown plan_type must not suppress heuristics.
        result = classify_topic("doc.md", "Click the button.", [], [], plan_type="bogus")
        assert result == "task"
