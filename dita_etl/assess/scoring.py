from __future__ import annotations
from typing import Any, Dict, Tuple

def clamp(x, lo, hi): return max(lo, min(hi, x))

def score_topicization(metrics: Dict[str, Any], weights: Dict[str, int], target_range) -> int:
    score = 0
    if metrics.get("heading_ladder_valid"): score += weights.get("heading_ladder_valid",0)
    lo, hi = target_range
    avg = metrics.get("avg_section_tokens", 0)
    if lo <= avg <= hi: score += weights.get("avg_section_len_target",0)
    if metrics.get("tables_simple"): score += weights.get("tables_simple",0)
    if metrics.get("lists_depth_ok"): score += weights.get("lists_depth_ok",0)
    if metrics.get("images_with_alt"): score += weights.get("images_with_alt",0)
    return clamp(score, 0, 100)

def score_risk(metrics: Dict[str, Any], weights: Dict[str, int]) -> int:
    score = 0
    if metrics.get("deep_nesting"): score += weights.get("deep_nesting",0)
    if metrics.get("complex_tables"): score += weights.get("complex_tables",0)
    if metrics.get("unresolved_anchors"): score += weights.get("unresolved_anchors",0)
    if metrics.get("mixed_inline_blocks"): score += weights.get("mixed_inline_blocks",0)
    return clamp(score, 0, 100)

def predict_topic_type(section_feats: Dict[str, Any], landmarks: Dict[str, list]) -> Tuple[str, float, list]:
    reasons = []
    conf = 0.6
    if section_feats["ordered_lists"] > 0 and (section_feats["imperative_density"] > 0.005 or section_feats["has_steps_title"]):
        reasons.append("ordered list + imperative/steps")
        return "task", 0.85, reasons
    if section_feats["tables"] > 0 or section_feats["reference_markers"] > 0:
        reasons.append("tables or reference markers")
        return "reference", 0.8, reasons
    reasons.append("expository default")
    return "concept", conf, reasons