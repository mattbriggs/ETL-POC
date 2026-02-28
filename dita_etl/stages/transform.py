"""Stage 2 — Transform.

Converts intermediate DocBook XML files into typed DITA topic files.
Classification and XML building are delegated to pure functions in
``dita_etl.transforms``.
"""

from __future__ import annotations

import os
import pathlib

from dita_etl.contracts import TransformInput, TransformOutput
from dita_etl.io.filesystem import ensure_dir, read_text, write_text
from dita_etl.transforms.classify import classify_topic
from dita_etl.transforms.dita import build_topic, extract_body, extract_title


class TransformStage:
    """Stage 2: convert intermediate DocBook XML to DITA topic files.

    Each intermediate XML is classified into a DITA topic type (concept,
    task, or reference) and a minimal valid DITA topic is rendered.

    .. note::
        Full XSLT transformation via Saxon is documented in the command below
        but is currently scaffolded as a pass-through to ease unit testing.
        Replace :meth:`_apply_xslt` with a real Saxon call when ready::

            java -jar saxon.jar -s:src.xml -xsl:stylesheet.xsl -o:out.dita
    """

    def run(self, input_: TransformInput) -> TransformOutput:
        """Execute the transformation stage.

        :param input_: Validated :class:`~dita_etl.contracts.TransformInput`
            contract.
        :returns: :class:`~dita_etl.contracts.TransformOutput` contract
            containing paths to generated DITA topics and any errors.
        """
        ensure_dir(input_.output_dir)
        topics: dict[str, list[str]] = {}
        errors: dict[str, str] = {}

        for src, xml_path in input_.intermediates.items():
            try:
                docbook_text = read_text(xml_path)
                title = extract_title(docbook_text)
                body = extract_body(docbook_text)
                topic_type = classify_topic(
                    os.path.basename(src),
                    docbook_text,
                    list(input_.rules_by_filename),
                    list(input_.rules_by_content),
                )
                dita_xml = build_topic(title, body, topic_type)
                out_name = pathlib.Path(src).stem + f"_{topic_type}.dita"
                out_path = os.path.join(input_.output_dir, out_name)
                write_text(out_path, dita_xml)
                topics.setdefault(src, []).append(out_path)
            except Exception as exc:  # noqa: BLE001
                errors[src] = str(exc)

        return TransformOutput(topics=topics, errors=errors)
