"""Section feature extraction — pure functions.

Computes a feature vector for a single Markdown section. All functions are
pure: identical inputs always produce identical outputs with no side effects.
"""

from __future__ import annotations

import re
from typing import Any

_LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
_IMAGE_RE = re.compile(r"!\[([^\]]*)\]\(([^)]+)\)")
_ORDERED_LIST_RE = re.compile(r"^\s*\d+[.)]\s+", re.MULTILINE)
_UNORDERED_LIST_RE = re.compile(r"^\s*[-*+]\s+", re.MULTILINE)
_TABLE_RE = re.compile(r"^\s*\|.*\|\s*$", re.MULTILINE)


def count_tokens(text: str) -> int:
    """Count word tokens in *text* using a simple ``\\w+`` pattern.

    :param text: Input text.
    :returns: Number of token matches.
    """
    return len(re.findall(r"\w+", text))


def imperative_density(text: str, verbs: list[str]) -> float:
    """Compute the ratio of imperative verb occurrences to total token count.

    :param text: Input text.
    :param verbs: List of imperative verbs to search for (case-insensitive).
    :returns: Ratio between 0.0 and 1.0.
    """
    total_tokens = count_tokens(text) or 1
    hits = sum(
        len(re.findall(r"\b" + re.escape(v) + r"\b", text, re.IGNORECASE))
        for v in verbs
    )
    return hits / total_tokens


def extract_features(
    section: dict[str, Any],
    landmarks: dict[str, list[str]],
) -> dict[str, Any]:
    """Compute a feature dictionary for a single document section.

    :param section: Section dict with ``"title"`` and ``"content"`` keys, as
        returned by :func:`~dita_etl.assess.structure.sectionize_markdown`.
    :param landmarks: Classification keyword lists from
        :class:`~dita_etl.assess.config.AssessConfig`. Expected keys:
        ``"task_keywords"``, ``"task_landmarks"``, ``"reference_markers"``.
    :returns: Dictionary of feature names to scalar values.

    Returned keys:

    * ``tokens`` – total word count.
    * ``ordered_lists`` – number of ordered list items.
    * ``unordered_lists`` – number of unordered list items.
    * ``tables`` – number of table rows.
    * ``images`` – number of inline images.
    * ``links`` – number of inline hyperlinks.
    * ``has_steps_title`` – whether the section title contains a task landmark.
    * ``imperative_density`` – ratio of imperative verbs to total tokens.
    * ``reference_markers`` – count of reference marker keywords found.
    """
    content: str = section.get("content", "")
    title: str = section.get("title", "")

    return {
        "tokens": count_tokens(content),
        "ordered_lists": len(_ORDERED_LIST_RE.findall(content)),
        "unordered_lists": len(_UNORDERED_LIST_RE.findall(content)),
        "tables": len(_TABLE_RE.findall(content)),
        "images": len(_IMAGE_RE.findall(content)),
        "links": len(_LINK_RE.findall(content)),
        "has_steps_title": any(
            k.lower() in title.lower()
            for k in landmarks.get("task_landmarks", [])
        ),
        "imperative_density": imperative_density(
            content, landmarks.get("task_keywords", [])
        ),
        "reference_markers": sum(
            1
            for k in landmarks.get("reference_markers", [])
            if k.lower() in content.lower()
        ),
    }
