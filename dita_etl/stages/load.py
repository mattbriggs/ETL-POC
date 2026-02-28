"""Stage 3 — Load.

Assembles DITA topics into a DITA map and copies associated assets.
Map generation is delegated to the pure ``dita_etl.transforms.dita`` module.
"""

from __future__ import annotations

import os
import pathlib

from dita_etl.contracts import LoadInput, LoadOutput
from dita_etl.io.filesystem import copy_assets, ensure_dir, write_text
from dita_etl.transforms.dita import build_map


class LoadStage:
    """Stage 3: assemble DITA topics into a map and collocate assets.

    Expected output structure::

        output_dir/
        ├── topics/
        │   ├── guide_task.dita
        │   └── ref_reference.dita
        ├── assets/
        │   ├── styles/
        │   └── images/
        └── index.ditamap
    """

    def run(self, input_: LoadInput) -> LoadOutput:
        """Execute the load stage.

        :param input_: Validated :class:`~dita_etl.contracts.LoadInput`
            contract.
        :returns: :class:`~dita_etl.contracts.LoadOutput` contract with
            the path to the written DITA map.
        """
        ensure_dir(input_.output_dir)

        # Flatten topics from all source files
        all_topics: list[str] = []
        for topic_list in input_.topics.values():
            all_topics.extend(topic_list)

        # Build and write the DITA map (pure function → I/O write)
        map_xml = build_map(input_.map_title, all_topics, input_.output_dir)
        map_path = os.path.join(input_.output_dir, "index.ditamap")
        write_text(map_path, map_xml)

        # Copy assets from intermediate directory when available
        if input_.intermediate_dir and os.path.exists(input_.intermediate_dir):
            asset_dst = os.path.join(input_.output_dir, "assets")
            copy_assets(
                src_root=input_.intermediate_dir,
                dst_root=asset_dst,
                asset_folders=("images", "styles", "imagers"),
            )

        return LoadOutput(map_path=map_path, topic_count=len(all_topics))
