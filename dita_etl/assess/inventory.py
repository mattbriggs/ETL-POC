"""Assessment batch runner — imperative shell for the assess sub-pipeline.

:func:`assess_batch` is the only function in this module that touches the
filesystem. All analytical logic is delegated to pure functions in the
sibling modules.
"""

from __future__ import annotations

import os
from typing import Any

from dita_etl.assess.config import AssessConfig
from dita_etl.assess.dedupe import cluster_near_duplicates
from dita_etl.assess.features import extract_features
from dita_etl.assess.predict import predict_topic_type
from dita_etl.assess.report import render_report_html, write_json, write_text
from dita_etl.assess.scoring import score_risk, score_topicization
from dita_etl.assess.structure import heading_ladder_valid, sectionize_markdown
from dita_etl.io.filesystem import file_sha256, read_text


# ---------------------------------------------------------------------------
# Per-file assessment (pure data transformation)
# ---------------------------------------------------------------------------


def _assess_markdown(path: str, text: str, cfg: AssessConfig) -> dict[str, Any]:
    """Assess a single Markdown file and return its metrics dictionary.

    :param path: Source file path (used only as a metadata label).
    :param text: Full text content of the file.
    :param cfg: Assessment configuration.
    :returns: Per-file assessment result dictionary.
    """
    sections = sectionize_markdown(text)
    features_list = [extract_features(s, cfg.classification) for s in sections]

    avg_tokens = int(
        sum(f["tokens"] for f in features_list) / max(1, len(features_list))
    )
    metrics: dict[str, Any] = {
        "heading_ladder_valid": heading_ladder_valid(sections),
        "avg_section_tokens": avg_tokens,
        "tables_simple": all(f["tables"] <= 1 for f in features_list),
        "lists_depth_ok": True,
        "images_with_alt": True,
        "deep_nesting": False,
        "complex_tables": any(f["tables"] > 1 for f in features_list),
        "unresolved_anchors": False,
        "mixed_inline_blocks": False,
    }

    readiness = score_topicization(
        metrics,
        cfg.scoring.topicization_weights,
        cfg.limits.target_section_tokens,
    )
    risk = score_risk(metrics, cfg.scoring.risk_weights)

    predictions = []
    for idx, (section, feats) in enumerate(zip(sections, features_list)):
        topic_type, confidence, reasons = predict_topic_type(feats, cfg.classification)
        predictions.append({
            "index": idx,
            "title": section.get("title", ""),
            "pred": topic_type,
            "confidence": confidence,
            "reasons": reasons,
        })

    return {
        "path": path,
        "size": os.path.getsize(path),
        "sha256": file_sha256(path),
        "sections": len(sections),
        "metrics": metrics,
        "topicization_readiness": readiness,
        "conversion_risk": risk,
        "predictions": predictions,
        "raw_sections": [
            {"title": s.get("title", ""), "content": s.get("content", "")}
            for s in sections
        ],
    }


def _assess_generic(path: str, text: str) -> dict[str, Any]:
    """Produce a minimal assessment result for non-Markdown files.

    :param path: Source file path.
    :param text: Full text content of the file.
    :returns: Per-file assessment result dictionary with placeholder scores.
    """
    return {
        "path": path,
        "size": os.path.getsize(path),
        "sha256": file_sha256(path),
        "sections": 1,
        "metrics": {},
        "topicization_readiness": 50,
        "conversion_risk": 50,
        "predictions": [],
        "raw_sections": [{"title": "Document", "content": text}],
    }


# ---------------------------------------------------------------------------
# Batch runner (imperative shell)
# ---------------------------------------------------------------------------


def assess_batch(
    input_files: list[str],
    cfg: AssessConfig,
    out_dir: str = "build/assess",
) -> dict[str, Any]:
    """Assess a batch of source files and write artefacts to *out_dir*.

    Written artefacts:

    * ``inventory.json`` – per-file assessment results.
    * ``dedupe_map.json`` – near-duplicate cluster assignments.
    * ``report.html`` – human-readable summary report.
    * ``plans/<filename>.conversion_plan.json`` – per-file conversion plans.

    :param input_files: List of source file paths to assess.
    :param cfg: Assessment configuration.
    :param out_dir: Output directory for all assessment artefacts.
    :returns: Dictionary of paths to the written artefact files.
    """
    os.makedirs(out_dir, exist_ok=True)

    results: list[dict[str, Any]] = []
    for path in input_files:
        text = read_text(path)
        if path.lower().endswith(".md"):
            results.append(_assess_markdown(path, text, cfg))
        else:
            results.append(_assess_generic(path, text))

    # Near-duplicate clustering
    corpus = [
        (r["path"], r["raw_sections"][0]["content"] if r["raw_sections"] else "")
        for r in results
    ]
    clusters = cluster_near_duplicates(
        corpus,
        ngram=cfg.shingling.ngram,
        num_perm=cfg.shingling.minhash_num_perm,
        threshold=cfg.shingling.threshold,
    )

    # Write artefacts
    inventory: dict[str, Any] = {"files": results}
    write_json(os.path.join(out_dir, "inventory.json"), inventory)
    write_json(os.path.join(out_dir, "dedupe_map.json"), {"clusters": clusters})

    # Per-file conversion plans
    plans_dir = os.path.join(out_dir, "plans")
    os.makedirs(plans_dir, exist_ok=True)
    for result in results:
        default_type = result["predictions"][0]["pred"] if result["predictions"] else "concept"
        plan = {
            "source": result["path"],
            "chunking": {"level": 1, "nested_topics": True},
            "default_topic_type": default_type,
            "sections": result["predictions"],
            "risk": result["conversion_risk"],
            "readiness": result["topicization_readiness"],
        }
        base = os.path.basename(result["path"])
        write_json(os.path.join(plans_dir, f"{base}.conversion_plan.json"), plan)

    # HTML report
    report_html = render_report_html(inventory, clusters)
    report_path = os.path.join(out_dir, "report.html")
    write_text(report_path, report_html)

    return {
        "inventory": os.path.join(out_dir, "inventory.json"),
        "dedupe": os.path.join(out_dir, "dedupe_map.json"),
        "report": report_path,
        "plans_dir": plans_dir,
    }
