from __future__ import annotations
import re
from typing import Any, Dict, List

HEADING_RE = re.compile(r'^(#{1,6})\s+(.*)')

def sectionize_markdown(text: str) -> List[Dict[str, Any]]:
    # Very simple sectionizer for Markdown: returns dicts with level/title/content
    lines = text.splitlines()
    sections = []
    cur = {"level": 0, "title": "Document", "content": []}
    for line in lines:
        m = HEADING_RE.match(line)
        if m:
            if cur["content"]:
                sections.append({**cur, "content": "\n".join(cur["content"]).strip()})
                cur = {"level": 0, "title": "", "content": []}
            cur["level"] = len(m.group(1))
            cur["title"] = m.group(2).strip()
        else:
            cur["content"].append(line)
    if cur["content"] or cur["title"]:
        sections.append({**cur, "content": "\n".join(cur["content"]).strip()})
    return sections

def heading_ladder_valid(sections: List[Dict[str, Any]]) -> bool:
    last = 0
    for s in sections:
        lvl = s.get("level", 1) or 1
        if last and lvl - last > 1:
            return False
        last = lvl
    return True