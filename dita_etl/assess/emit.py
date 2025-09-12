
from __future__ import annotations
import json, os, html
from typing import Dict, Any, List

def write_json(path: str, obj: Any):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(obj, f, indent=2)

def render_report_html(inventory: Dict[str, Any], dedupe_clusters: List[List[str]]) -> str:
    rows = []
    for f in inventory["files"]:
        rows.append(f"<tr><td>{html.escape(f['path'])}</td><td>{f['size']}</td><td>{f['sections']}</td>"
                    f"<td>{f['topicization_readiness']}</td><td>{f['conversion_risk']}</td></tr>")
    table = "\n".join(rows)
    dup = "<ul>" + "".join(f"<li>{', '.join(map(html.escape,c))}</li>" for c in dedupe_clusters if len(c)>1) + "</ul>"
    return f'''<!doctype html>
<html><head><meta charset='utf-8'><title>Assessment Report</title>
<style>body{{font-family:system-ui}} table{{border-collapse:collapse;width:100%}} td,th{{border:1px solid #ddd;padding:6px}}</style>
</head><body>
<h1>Assessment Report</h1>
<h2>Summary</h2>
<p>Total files: {len(inventory['files'])}</p>
<table>
  <thead><tr><th>File</th><th>Bytes</th><th>Sections</th><th>Readiness</th><th>Risk</th></tr></thead>
  <tbody>{table}</tbody>
</table>
<h2>Duplicate Clusters</h2>
{dup}
</body></html>'''

def write_text(path: str, text: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(text)
