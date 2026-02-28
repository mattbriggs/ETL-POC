"""Unit tests for dita_etl.assess.scoring and dita_etl.assess.predict."""

import pytest

from dita_etl.assess.predict import predict_topic_type
from dita_etl.assess.scoring import score_risk, score_topicization

_WEIGHTS_TOPICIZATION = {
    "heading_ladder_valid": 10,
    "avg_section_len_target": 15,
    "tables_simple": 10,
    "lists_depth_ok": 10,
    "images_with_alt": 5,
}
_WEIGHTS_RISK = {
    "deep_nesting": 20,
    "complex_tables": 25,
    "unresolved_anchors": 15,
    "mixed_inline_blocks": 10,
}
_TARGET = [50, 500]


class TestScoreTopicization:
    def test_all_positive(self):
        metrics = {
            "heading_ladder_valid": True,
            "avg_section_tokens": 200,
            "tables_simple": True,
            "lists_depth_ok": True,
            "images_with_alt": True,
        }
        score = score_topicization(metrics, _WEIGHTS_TOPICIZATION, _TARGET)
        assert score == 50  # sum of all weights

    def test_all_negative(self):
        metrics = {
            "heading_ladder_valid": False,
            "avg_section_tokens": 1,
            "tables_simple": False,
            "lists_depth_ok": False,
            "images_with_alt": False,
        }
        score = score_topicization(metrics, _WEIGHTS_TOPICIZATION, _TARGET)
        assert score == 0

    def test_clamped_to_100(self):
        heavy_weights = {k: 50 for k in _WEIGHTS_TOPICIZATION}
        metrics = {
            "heading_ladder_valid": True,
            "avg_section_tokens": 200,
            "tables_simple": True,
            "lists_depth_ok": True,
            "images_with_alt": True,
        }
        assert score_topicization(metrics, heavy_weights, _TARGET) == 100

    def test_out_of_range_tokens_not_scored(self):
        metrics = {
            "heading_ladder_valid": False,
            "avg_section_tokens": 1000,  # above target range
            "tables_simple": False,
            "lists_depth_ok": False,
            "images_with_alt": False,
        }
        score = score_topicization(metrics, _WEIGHTS_TOPICIZATION, _TARGET)
        assert score == 0


class TestScoreRisk:
    def test_no_risk_factors(self):
        metrics = {
            "deep_nesting": False,
            "complex_tables": False,
            "unresolved_anchors": False,
            "mixed_inline_blocks": False,
        }
        assert score_risk(metrics, _WEIGHTS_RISK) == 0

    def test_all_risk_factors(self):
        metrics = {
            "deep_nesting": True,
            "complex_tables": True,
            "unresolved_anchors": True,
            "mixed_inline_blocks": True,
        }
        assert score_risk(metrics, _WEIGHTS_RISK) == 70

    def test_single_risk_factor(self):
        metrics = {
            "deep_nesting": False,
            "complex_tables": True,
            "unresolved_anchors": False,
            "mixed_inline_blocks": False,
        }
        assert score_risk(metrics, _WEIGHTS_RISK) == 25


class TestPredictTopicType:
    _LANDMARKS: dict = {}

    def test_predicts_task(self):
        feats = {
            "ordered_lists": 3,
            "imperative_density": 0.02,
            "has_steps_title": False,
            "tables": 0,
            "reference_markers": 0,
        }
        topic_type, confidence, reasons = predict_topic_type(feats, self._LANDMARKS)
        assert topic_type == "task"
        assert confidence > 0.5
        assert len(reasons) > 0

    def test_predicts_reference_via_tables(self):
        feats = {
            "ordered_lists": 0,
            "imperative_density": 0.0,
            "has_steps_title": False,
            "tables": 2,
            "reference_markers": 0,
        }
        topic_type, _, _ = predict_topic_type(feats, self._LANDMARKS)
        assert topic_type == "reference"

    def test_predicts_concept_default(self):
        feats = {
            "ordered_lists": 0,
            "imperative_density": 0.0,
            "has_steps_title": False,
            "tables": 0,
            "reference_markers": 0,
        }
        topic_type, _, _ = predict_topic_type(feats, self._LANDMARKS)
        assert topic_type == "concept"

    def test_task_requires_ordered_list(self):
        # High imperative density but NO ordered list → should not be task
        feats = {
            "ordered_lists": 0,
            "imperative_density": 0.9,
            "has_steps_title": True,
            "tables": 0,
            "reference_markers": 0,
        }
        topic_type, _, _ = predict_topic_type(feats, self._LANDMARKS)
        assert topic_type != "task"
