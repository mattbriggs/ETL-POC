
from __future__ import annotations
import os, pathlib
from typing import Dict, List
from .base import Stage, StageResult
from ..io_utils import ensure_dir, write_text

MAP_TEMPLATE = '''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE map PUBLIC "-//OASIS//DTD DITA Map//EN" "map.dtd">
<map>
  <title>{title}</title>
  {refs}
</map>'''

def make_topicref(path: str) -> str:
    href = pathlib.Path(path).name
    return f'  <topicref href="{href}" />'

class LoadStage(Stage):
    def __init__(self, output_dir: str, map_title: str):
        self.output_dir = output_dir
        self.map_title = map_title

    def run(self, topics: Dict[str, List[str]]) -> StageResult:
        ensure_dir(self.output_dir)
        all_topics: List[str] = []
        for lst in topics.values():
            all_topics.extend(lst)
        refs = "\n  ".join(make_topicref(p) for p in sorted(all_topics))
        map_xml = MAP_TEMPLATE.format(title=self.map_title, refs=refs)
        map_path = os.path.join(self.output_dir, "out.ditamap")
        write_text(map_path, map_xml)
        return StageResult(success=True, message=f"Wrote map with {len(all_topics)} topics.", data={"map": map_path, "topics": all_topics})
