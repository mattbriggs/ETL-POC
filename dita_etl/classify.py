
from __future__ import annotations
import re
from typing import Optional, List
from .config import ClassificationRule

def classify_topic(filename: str, content: str, rules_by_filename: List[ClassificationRule], rules_by_content: List[ClassificationRule]) -> str:
    # filename rules first
    for r in rules_by_filename or []:
        pattern = r.pattern.replace("*", ".*")
        if re.fullmatch(pattern, filename):
            return r.topic_type
    # content rules
    for r in rules_by_content or []:
        if re.search(r.pattern, content, re.IGNORECASE):
            return r.topic_type
    # heuristics
    if re.search(r'\b(step|click|select|open|run)\b', content, re.IGNORECASE):
        return "task"
    if re.search(r'\b(table of|parameters|syntax)\b', content, re.IGNORECASE):
        return "reference"
    return "concept"
