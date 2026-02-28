"""Topic-type prediction for individual sections — pure functions.

Split from ``scoring.py`` to give prediction its own single-responsibility
module with a clear, testable interface.
"""

from __future__ import annotations

from typing import Any


def predict_topic_type(
    section_feats: dict[str, Any],
    landmarks: dict[str, list[str]],
) -> tuple[str, float, list[str]]:
    """Predict the DITA topic type for a single section based on its features.

    Rules are evaluated in priority order:

    1. **Task**: ordered list present *and* (imperative density > 0.005 *or*
       steps-style title detected).
    2. **Reference**: tables present *or* reference-marker keywords found.
    3. **Concept**: default fallback.

    :param section_feats: Feature dictionary as returned by
        :func:`~dita_etl.assess.features.extract_features`.
    :param landmarks: Classification keyword lists (unused in current
        heuristic but retained for future expansion).
    :returns: Tuple of ``(topic_type, confidence, reasons)`` where
        *topic_type* is one of ``"concept"``, ``"task"``, ``"reference"``;
        *confidence* is a float in [0, 1]; and *reasons* is a list of
        human-readable strings explaining the prediction.
    """
    reasons: list[str] = []

    has_ordered = section_feats.get("ordered_lists", 0) > 0
    is_imperative = section_feats.get("imperative_density", 0.0) > 0.005
    has_steps_title = bool(section_feats.get("has_steps_title", False))
    has_tables = section_feats.get("tables", 0) > 0
    has_ref_markers = section_feats.get("reference_markers", 0) > 0

    if has_ordered and (is_imperative or has_steps_title):
        reasons.append("ordered list + imperative/steps")
        return "task", 0.85, reasons

    if has_tables or has_ref_markers:
        reasons.append("tables or reference markers")
        return "reference", 0.80, reasons

    reasons.append("expository default")
    return "concept", 0.60, reasons
