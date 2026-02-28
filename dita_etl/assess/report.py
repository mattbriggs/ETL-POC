"""Assessment report rendering — pure function + I/O helpers.

:func:`render_report_html` is a pure function that builds the HTML string.
:func:`write_json` and :func:`write_text` are thin I/O wrappers kept here
(rather than in ``dita_etl.io``) because they are only used by the assess
stage.
"""

from __future__ import annotations

import html
import json
import os
from typing import Any


# ---------------------------------------------------------------------------
# Pure: HTML report generation
# ---------------------------------------------------------------------------


def render_report_html(
    inventory: dict[str, Any],
    dedupe_clusters: list[list[str]],
) -> str:
    """Render an HTML assessment report.

    :param inventory: Inventory dictionary with a ``"files"`` key containing
        a list of per-file assessment result dicts.
    :param dedupe_clusters: Near-duplicate clusters as returned by
        :func:`~dita_etl.assess.dedupe.cluster_near_duplicates`.
    :returns: Complete HTML document as a string.
    """
    rows = []
    for f in inventory["files"]:
        rows.append(
            f"<tr>"
            f"<td>{html.escape(f['path'])}</td>"
            f"<td>{f['size']}</td>"
            f"<td>{f['sections']}</td>"
            f"<td>{f['topicization_readiness']}</td>"
            f"<td>{f['conversion_risk']}</td>"
            f"</tr>"
        )
    table_rows = "\n".join(rows)

    dup_items = "".join(
        f"<li>{', '.join(map(html.escape, cluster))}</li>"
        for cluster in dedupe_clusters
        if len(cluster) > 1
    )
    dup_section = f"<ul>{dup_items}</ul>" if dup_items else "<p>No near-duplicates found.</p>"

    return f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>Assessment Report</title>
  <style>
    body {{ font-family: system-ui, sans-serif; max-width: 1200px; margin: 0 auto; padding: 1rem; }}
    table {{ border-collapse: collapse; width: 100%; }}
    td, th {{ border: 1px solid #ddd; padding: 6px 10px; text-align: left; }}
    th {{ background: #f4f4f4; }}
  </style>
</head>
<body>
<h1>Assessment Report</h1>
<h2>Summary</h2>
<p>Total files: {len(inventory['files'])}</p>
<table>
  <thead>
    <tr><th>File</th><th>Bytes</th><th>Sections</th><th>Readiness</th><th>Risk</th></tr>
  </thead>
  <tbody>{table_rows}</tbody>
</table>
<h2>Near-Duplicate Clusters</h2>
{dup_section}
</body>
</html>"""


# ---------------------------------------------------------------------------
# I/O: serialisation helpers used only by the assess stage
# ---------------------------------------------------------------------------


def write_json(path: str, obj: Any) -> None:
    """Serialise *obj* to pretty-printed JSON at *path*.

    :param path: Destination file path (parent directories created as needed).
    :param obj: JSON-serialisable object.
    """
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, indent=2)


def write_text(path: str, text: str) -> None:
    """Write *text* to *path*.

    :param path: Destination file path (parent directories created as needed).
    :param text: Content to write.
    """
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)
