"""Document-readiness and conversion-risk scorers — pure functions.

All functions are pure: no I/O, no side effects.
"""

from __future__ import annotations

from typing import Any


def _clamp(value: int, lo: int, hi: int) -> int:
    """Clamp *value* to the inclusive range [*lo*, *hi*].

    :param value: Input integer.
    :param lo: Lower bound.
    :param hi: Upper bound.
    :returns: Clamped integer.
    """
    return max(lo, min(hi, value))


def score_topicization(
    metrics: dict[str, Any],
    weights: dict[str, int],
    target_range: list[int],
) -> int:
    """Compute a topicization-readiness score in the range 0–100.

    Higher values indicate a document that is well-structured for conversion
    to DITA topics.

    :param metrics: Metrics dictionary as produced by
        :func:`~dita_etl.assess.inventory.assess_file_markdown`.
    :param weights: Per-metric additive weights from
        :class:`~dita_etl.assess.config.ScoringWeights`.
    :param target_range: ``[min_tokens, max_tokens]`` for the ideal section
        length.
    :returns: Integer readiness score clamped to [0, 100].
    """
    score = 0
    if metrics.get("heading_ladder_valid"):
        score += weights.get("heading_ladder_valid", 0)
    lo, hi = target_range[0], target_range[1]
    avg = metrics.get("avg_section_tokens", 0)
    if lo <= avg <= hi:
        score += weights.get("avg_section_len_target", 0)
    if metrics.get("tables_simple"):
        score += weights.get("tables_simple", 0)
    if metrics.get("lists_depth_ok"):
        score += weights.get("lists_depth_ok", 0)
    if metrics.get("images_with_alt"):
        score += weights.get("images_with_alt", 0)
    return _clamp(score, 0, 100)


def score_risk(
    metrics: dict[str, Any],
    weights: dict[str, int],
) -> int:
    """Compute a conversion-risk score in the range 0–100.

    Higher values indicate a document with structural patterns that are
    difficult to convert reliably.

    :param metrics: Metrics dictionary as produced by
        :func:`~dita_etl.assess.inventory.assess_file_markdown`.
    :param weights: Per-metric additive weights from
        :class:`~dita_etl.assess.config.ScoringWeights`.
    :returns: Integer risk score clamped to [0, 100].
    """
    score = 0
    if metrics.get("deep_nesting"):
        score += weights.get("deep_nesting", 0)
    if metrics.get("complex_tables"):
        score += weights.get("complex_tables", 0)
    if metrics.get("unresolved_anchors"):
        score += weights.get("unresolved_anchors", 0)
    if metrics.get("mixed_inline_blocks"):
        score += weights.get("mixed_inline_blocks", 0)
    return _clamp(score, 0, 100)
