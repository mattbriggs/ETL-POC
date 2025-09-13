from __future__ import annotations
import os, hashlib
from typing import Any, Dict, List
from .assess_config import AssessConfig
from .structure import sectionize_markdown, heading_ladder_valid
from .features import extract_features
from .dedupe import cluster_near_duplicates
from .scoring import score_topicization, score_risk, predict_topic_type
from .emit import write_json, render_report_html, write_text

def file_bytes(path: str) -> int:
    return os.path.getsize(path)

def file_sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def read_text(path: str) -> str:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except UnicodeDecodeError:
        with open(path, "r", encoding="latin-1") as f:
            return f.read()

def assess_file_markdown(path: str, cfg: AssessConfig) -> Dict[str, Any]:
    text = read_text(path)
    secs = sectionize_markdown(text)
    feats = [extract_features(s, cfg.classification) for s in secs]
    avg_tokens = int(sum(f["tokens"] for f in feats) / max(1, len(feats)))
    metrics = {
        "heading_ladder_valid": heading_ladder_valid(secs),
        "avg_section_tokens": avg_tokens,
        "tables_simple": all(f["tables"] <= 1 for f in feats),
        "lists_depth_ok": True,
        "images_with_alt": True,  # naive placeholder
        "deep_nesting": False,
        "complex_tables": any(f["tables"] > 1 for f in feats),
        "unresolved_anchors": False,
        "mixed_inline_blocks": False,
    }
    readiness = score_topicization(metrics, cfg.scoring.topicization_weights, cfg.limits.target_section_tokens)
    risk = score_risk(metrics, cfg.scoring.risk_weights)
    preds = []
    for i, (s, f) in enumerate(zip(secs, feats)):
        t, conf, reasons = predict_topic_type(f, cfg.classification)
        preds.append({"index": i, "title": s.get("title",""), "pred": t, "confidence": conf, "reasons": reasons})
    return {
        "path": path,
        "size": file_bytes(path),
        "sha256": file_sha256(path),
        "sections": len(secs),
        "metrics": metrics,
        "topicization_readiness": readiness,
        "conversion_risk": risk,
        "predictions": preds,
        "raw_sections": [{"title": s.get("title",""), "content": s.get("content","")} for s in secs],
    }

def assess_batch(input_files: List[str], cfg: AssessConfig, out_dir: str = "build/assess") -> Dict[str, Any]:
    os.makedirs(out_dir, exist_ok=True)
    results = []
    for p in input_files:
        if p.lower().endswith(".md"):
            results.append(assess_file_markdown(p, cfg))
        else:
            results.append({
                "path": p, "size": file_bytes(p), "sha256": file_sha256(p),
                "sections": 1, "metrics": {}, "topicization_readiness": 50, "conversion_risk": 50,
                "predictions": [], "raw_sections":[{"title":"Document","content": read_text(p)}]
            })
    items = [(r["path"], (r["raw_sections"][0]["content"] if r["raw_sections"] else "")) for r in results]
    clusters = cluster_near_duplicates(
        items,
        ngram=cfg.shingling.ngram,
        num_perm=cfg.shingling.minhash_num_perm,
        threshold=cfg.shingling.threshold,
    )
    inventory = {"files": results}
    write_json(os.path.join(out_dir, "inventory.json"), inventory)
    write_json(os.path.join(out_dir, "dedupe_map.json"), {"clusters": clusters})
    plans_dir = os.path.join(out_dir, "plans"); os.makedirs(plans_dir, exist_ok=True)
    for r in results:
        default_type = r["predictions"][0]["pred"] if r["predictions"] else "concept"
        plan = {
            "source": r["path"],
            "chunking": {"level": 1, "nested_topics": True},
            "default_topic_type": default_type,
            "sections": r["predictions"],
            "risk": r["conversion_risk"],
            "readiness": r["topicization_readiness"],
        }
        base = os.path.basename(r["path"])
        write_json(os.path.join(plans_dir, base + ".conversion_plan.json"), plan)
    report_html = render_report_html(inventory, clusters)
    write_text(os.path.join(out_dir, "report.html"), report_html)
    return {
        "inventory": os.path.join(out_dir, "inventory.json"),
        "dedupe": os.path.join(out_dir, "dedupe_map.json"),
        "report": os.path.join(out_dir, "report.html"),
        "plans_dir": plans_dir,
    }