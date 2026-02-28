"""Markdown structural analysis — pure functions.

Provides sectionization and structural-validity checks for Markdown source
documents. All functions are pure: they take text and return data structures
with no I/O or side effects.
"""

from __future__ import annotations

import re
from typing import Any

_HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)", re.MULTILINE)


def sectionize_markdown(text: str) -> list[dict[str, Any]]:
    """Split a Markdown document into logical sections at heading boundaries.

    Each section is represented as a dictionary with keys:

    * ``"level"`` – heading depth (1–6; 0 for the implicit preamble section).
    * ``"title"`` – heading text, or ``"Document"`` for the preamble.
    * ``"content"`` – body text between this heading and the next.

    :param text: Raw Markdown source text.
    :returns: Ordered list of section dictionaries.

    :Example:

    .. code-block:: python

        secs = sectionize_markdown("# Intro\\n\\nHello\\n## Details\\n\\nMore")
        assert secs[0]["title"] == "Intro"
        assert secs[1]["title"] == "Details"
    """
    lines = text.splitlines()
    sections: list[dict[str, Any]] = []
    current: dict[str, Any] = {"level": 0, "title": "Document", "content": []}

    for line in lines:
        match = _HEADING_RE.match(line)
        if match:
            if current["content"]:
                sections.append(
                    {**current, "content": "\n".join(current["content"]).strip()}
                )
            current = {
                "level": len(match.group(1)),
                "title": match.group(2).strip(),
                "content": [],
            }
        else:
            current["content"].append(line)

    # Flush the final section — skip the default preamble if it has no content
    if current["level"] > 0 or current["content"]:
        sections.append(
            {**current, "content": "\n".join(current["content"]).strip()}
        )
    return sections


def heading_ladder_valid(sections: list[dict[str, Any]]) -> bool:
    """Check that heading levels do not skip more than one level at a time.

    A document that jumps from ``##`` directly to ``####`` (skipping ``###``)
    is considered invalid.

    :param sections: Section list as returned by :func:`sectionize_markdown`.
    :returns: ``True`` if the heading ladder is valid; ``False`` otherwise.
    """
    last = 0
    for section in sections:
        level = section.get("level", 1) or 1
        if last and (level - last) > 1:
            return False
        last = level
    return True
