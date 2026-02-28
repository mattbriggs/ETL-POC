"""DITA topic-type classifier — pure functional core.

Classification proceeds in priority order:

1. Filename rules (glob-style pattern matching against the basename).
2. Content rules (regex search against the full document text).
3. Built-in heuristics (keyword frequency in content).
4. Default fallback → ``"concept"``.

All functions are pure: they take data and return data with no side effects.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from dita_etl.config import ClassificationRule

# DITA topic types supported by the pipeline.
TOPIC_TYPES = frozenset({"concept", "task", "reference"})

# Built-in heuristic patterns.
_TASK_RE = re.compile(r"\b(step|click|select|open|run|press|type)\b", re.IGNORECASE)
_REF_RE = re.compile(r"\b(table of|parameters|syntax|options|defaults)\b", re.IGNORECASE)


def classify_topic(
    filename: str,
    content: str,
    rules_by_filename: list["ClassificationRule"],
    rules_by_content: list["ClassificationRule"],
) -> str:
    """Determine the DITA topic type for a document.

    :param filename: Basename of the source file (e.g. ``"guide.md"``).
    :param content: Full text content of the (intermediate) document.
    :param rules_by_filename: Ordered list of filename classification rules.
    :param rules_by_content: Ordered list of content classification rules.
    :returns: One of ``"concept"``, ``"task"``, or ``"reference"``.

    :Example:

    .. code-block:: python

        result = classify_topic(
            "install.md",
            "Click the button to install...",
            rules_by_filename=[],
            rules_by_content=[],
        )
        assert result == "task"
    """
    # 1. Filename rules (convert simple glob * → .* for regex)
    for rule in rules_by_filename or []:
        pattern = rule.pattern.replace("*", ".*")
        if re.fullmatch(pattern, filename):
            return _validated(rule.topic_type)

    # 2. Content rules
    for rule in rules_by_content or []:
        if re.search(rule.pattern, content, re.IGNORECASE):
            return _validated(rule.topic_type)

    # 3. Heuristics
    if _TASK_RE.search(content):
        return "task"
    if _REF_RE.search(content):
        return "reference"

    # 4. Default
    return "concept"


def _validated(topic_type: str) -> str:
    """Return *topic_type* after normalising and validating.

    Falls back to ``"concept"`` for unknown types rather than crashing,
    so a misconfigured rule degrades gracefully.

    :param topic_type: Raw type string from a classification rule.
    :returns: Validated and lower-cased topic type string.
    """
    normalised = topic_type.lower().strip()
    return normalised if normalised in TOPIC_TYPES else "concept"
