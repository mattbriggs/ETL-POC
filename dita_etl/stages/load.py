from __future__ import annotations

import os
import pathlib
import shutil
from typing import Dict, List

from .base import Stage, StageResult
from ..io_utils import ensure_dir, write_text


MAP_TEMPLATE = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE map PUBLIC "-//OASIS//DTD DITA Map//EN" "map.dtd">
<map>
  <title>{title}</title>
  {refs}
</map>
"""


def make_topicref(path: str, base_dir: str) -> str:
    """
    Generate a <topicref> element with a path relative to the map file.
    """
    abs_path = pathlib.Path(path).resolve()
    rel_path = abs_path.relative_to(pathlib.Path(base_dir).resolve())
    return f'  <topicref href="{rel_path.as_posix()}" />'


class LoadStage(Stage):
    """
    Assembles transformed DITA topics into a single DITA map and
    collocates associated assets (CSS, images).

    Expected structure:
        output_dir/
          ├── topics/
          │   ├── topic1.dita
          │   └── ...
          ├── assets/
          │   ├── styles/
          │   └── images/
          └── index.ditamap
    """

    def __init__(self, output_dir: str, map_title: str):
        self.output_dir = output_dir
        self.map_title = map_title

    def _copy_assets(self, intermediate_root: str):
        """
        Copy assets (images, styles, imagers) from the intermediate directory
        into the final DITA output folder under 'assets/'.
        """
        asset_root = os.path.join(self.output_dir, "assets")
        ensure_dir(asset_root)

        for folder in ("images", "styles", "imagers"):
            src_path = os.path.join(intermediate_root, folder)
            if os.path.exists(src_path):
                dst_path = os.path.join(asset_root, folder)
                shutil.copytree(src_path, dst_path, dirs_exist_ok=True)

    def run(self, topics: Dict[str, List[str]]) -> StageResult:
        """
        Write a DITA map referencing all topics and copy assets.
        """
        ensure_dir(self.output_dir)

        # Flatten list of topics
        all_topics: List[str] = []
        for lst in topics.values():
            all_topics.extend(lst)

        # Compute relative topicref paths
        refs = "\n  ".join(
            make_topicref(p, self.output_dir) for p in sorted(all_topics)
        )

        # Write DITA map file
        map_xml = MAP_TEMPLATE.format(title=self.map_title, refs=refs)
        map_path = os.path.join(self.output_dir, "index.ditamap")
        write_text(map_path, map_xml)

        # Locate intermediate folder for assets
        intermediate_root = os.path.join(
            pathlib.Path(self.output_dir).parents[0], "intermediate"
        )
        if os.path.exists(intermediate_root):
            self._copy_assets(intermediate_root)

        message = (
            f"Wrote DITA map '{map_path}' with {len(all_topics)} topics. "
            "Assets copied to assets/ if available."
        )

        return StageResult(
            success=True,
            message=message,
            data={"map": map_path, "topics": all_topics},
        )