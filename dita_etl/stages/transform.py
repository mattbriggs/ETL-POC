
from __future__ import annotations
import os, pathlib, re
from typing import Dict, List
from .base import Stage, StageResult
from ..runners import SubprocessRunner, SubprocessError
from ..io_utils import ensure_dir, write_text, read_text
from ..classify import classify_topic

DITA_TEMPLATE = {
    "concept": lambda title, body: f'<concept id="c1"><title>{title}</title><conbody>{body}</conbody></concept>',
    "task": lambda title, body: f'<task id="t1"><title>{title}</title><taskbody>{body}</taskbody></task>',
    "reference": lambda title, body: f'<reference id="r1"><title>{title}</title><refbody>{body}</refbody></reference>',
}

class TransformStage(Stage):
    def __init__(self, java_path: str, saxon_jar: str, xsl_path: str, output_dir: str, rules_by_filename, rules_by_content, runner: SubprocessRunner | None = None):
        self.java_path = java_path
        self.saxon_jar = saxon_jar
        self.xsl_path = xsl_path
        self.output_dir = output_dir
        self.rules_by_filename = rules_by_filename
        self.rules_by_content = rules_by_content
        self.runner = runner or SubprocessRunner()

    def _apply_xslt(self, src_xml: str) -> str:
        # In real use, call Saxon. For scaffold, we simply return the source content.
        # Command (documented): java -jar saxon.jar -s:src.xml -xsl:stylesheet.xsl -o:-
        # We keep it simple to ease unit testing.
        return read_text(src_xml)

    def _title_from_content(self, text: str) -> str:
        # naive title: first line without tags
        m = re.search(r"<title>(.*?)</title>", text, re.IGNORECASE)
        return m.group(1) if m else "Untitled"

    def _body_from_content(self, text: str) -> str:
        # naive body extraction: everything inside <para> becomes <p/>
        paras = re.findall(r"<para>(.*?)</para>", text, re.IGNORECASE | re.DOTALL)
        if not paras:
            # fallback to whole
            return f"<p>{re.sub('<[^>]+>', '', text)[:200]}</p>"
        return "".join(f"<p>{p.strip()}</p>" for p in paras)

    def run(self, intermediates: Dict[str, str]) -> StageResult:
        ensure_dir(self.output_dir)
        outputs: Dict[str, List[str]] = {}
        errors: Dict[str, str] = {}
        for src, xml in intermediates.items():
            try:
                txt = self._apply_xslt(xml)
                title = self._title_from_content(txt)
                body = self._body_from_content(txt)
                topic_type = classify_topic(os.path.basename(src), txt, self.rules_by_filename, self.rules_by_content)
                root = DITA_TEMPLATE[topic_type](title, body)
                out_name = pathlib.Path(src).stem + f"_{topic_type}.dita"
                out_path = os.path.join(self.output_dir, out_name)
                write_text(out_path, root)
                outputs.setdefault(src, []).append(out_path)
            except Exception as e:
                errors[src] = str(e)
        msg = f"Transformed {len(outputs)} intermediates into DITA topics."
        return StageResult(success=len(errors)==0, message=msg, data={"outputs": outputs, "errors": errors})
