from __future__ import annotations
import re
from typing import Any, Dict, List

LINK_RE = re.compile(r'\[([^\]]+)\]\(([^\)]+)\)')
IMAGE_RE = re.compile(r'!\[([^\]]*)\]\(([^\)]+)\)')
ORDERED_LIST_RE = re.compile(r'^\s*\d+[.)]\s+', re.MULTILINE)
UNORDERED_LIST_RE = re.compile(r'^\s*[-*+]\s+', re.MULTILINE)
TABLE_RE = re.compile(r'^\s*\|.*\|\s*$', re.MULTILINE)

def count_tokens(text: str) -> int:
    return len(re.findall(r'\w+', text))

def imperative_density(text: str, verbs: List[str]) -> float:
    tokens = count_tokens(text) or 1
    hits = sum(len(re.findall(r'\b' + re.escape(v) + r'\b', text, re.IGNORECASE)) for v in verbs)
    return hits / tokens

def extract_features(section: Dict[str, Any], landmarks: Dict[str, List[str]]) -> Dict[str, Any]:
    content = section.get("content","")
    title = section.get("title","")
    feats = {
        "tokens": count_tokens(content),
        "ordered_lists": len(ORDERED_LIST_RE.findall(content)),
        "unordered_lists": len(UNORDERED_LIST_RE.findall(content)),
        "tables": len(TABLE_RE.findall(content)),
        "images": len(IMAGE_RE.findall(content)),
        "links": len(LINK_RE.findall(content)),
        "has_steps_title": any(k.lower() in title.lower() for k in landmarks.get("task_landmarks",[])),
        "imperative_density": imperative_density(content, landmarks.get("task_keywords",[])),
        "reference_markers": sum(1 for k in landmarks.get("reference_markers",[]) if k.lower() in content.lower())
    }
    return feats