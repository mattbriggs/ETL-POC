"""DITA topic-type classifier — pure functional core.

Classification proceeds in priority order:

1. Filename rules (glob-style pattern matching against the basename).
2. Content rules (regex search against the full document text).
3. Plan type hint (``default_topic_type`` from the Assess-stage conversion plan).
4. Built-in heuristics (keyword frequency in content).
5. Default fallback → ``"concept"``.

All functions are pure: they take data and return data with no side effects.
"""

from __future__ import annotations

import fnmatch
import re
from pathlib import Path
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
    plan_type: str | None = None,
) -> str:
    """Determine the DITA topic type for a document.

    :param filename: Basename of the source file (e.g. ``"guide.md"``).
    :param content: Full text content of the (intermediate) document.
    :param rules_by_filename: Ordered list of filename classification rules.
    :param rules_by_content: Ordered list of content classification rules.
    :param plan_type: Optional topic-type hint from the Assess-stage conversion
        plan. Overrides built-in heuristics but not config rules. Ignored when
        ``None`` or not a valid DITA topic type.
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
    # 1. Filename rules (glob matched against the file stem, without extension)
    stem = Path(filename).stem
    for rule in rules_by_filename or []:
        if fnmatch.fnmatch(stem, rule.pattern):
            return _validated(rule.topic_type)

    # 2. Content rules
    for rule in rules_by_content or []:
        if re.search(rule.pattern, content, re.IGNORECASE):
            return _validated(rule.topic_type)

    # 3. Plan type hint (from Assess-stage conversion plan)
    if plan_type is not None and plan_type.lower().strip() in TOPIC_TYPES:
        return _validated(plan_type)

    # 4. Heuristics
    if _TASK_RE.search(content):
        return "task"
    if _REF_RE.search(content):
        return "reference"

    # 5. Default
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
