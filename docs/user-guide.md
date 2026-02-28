# User Guide — Running a migration job

This guide walks through a complete source-to-DITA migration: setting up
the project, running the assessment, reading the results, configuring
classification rules, and running the full pipeline to produce DITA output.

---

## Prerequisites

| Requirement | Notes |
|---|---|
| Python ≥ 3.12 | `python3 --version` |
| Pandoc | `brew install pandoc` (macOS) or [pandoc.org](https://pandoc.org) |
| Git | To clone the repository |
| Oxygen XML Editor scripts | Optional — only needed for `.docx` via the Oxygen extractor |

---

## 1. Install

```bash
git clone https://github.com/your-org/ETL-POC.git
cd ETL-POC

python3 -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate

pip install -e ".[dev]"
```

Verify:

```bash
dita-etl --help
```

---

## 2. Organise your source content

Place all source files in a single input directory. Mixed formats are
supported in the same run:

```
docs/
├── install-guide.md
├── api-reference.html
├── release-notes.md
└── spec.docx
```

Sub-directories are discovered recursively.

---

## 3. Create config files

### `config/config.yaml`

```yaml
tooling:
  pandoc_path: pandoc          # or absolute path: /usr/local/bin/pandoc

source_formats:
  treat_as_markdown: [".md"]
  treat_as_html:     [".html", ".htm"]
  treat_as_docx:     [".docx"]

dita_output:
  output_folder: build/out
  map_title: "My Documentation Set"

extract:
  max_workers: 4               # parallel extraction threads

classification_rules:
  by_filename:
    - match: "*guide*"
      type: "task"
    - match: "*reference*"
      type: "reference"
    - match: "index"
      type: "concept"
  by_content:
    - match: "procedure"
      type: "task"
    - match: "parameters"
      type: "reference"
```

### `config/assess.yaml`

Start with the defaults — they work well for most content sets:

```yaml
shingling:
  ngram: 7
  minhash_num_perm: 64
  threshold: 0.88

scoring:
  topicization_weights:
    heading_ladder_valid: 10
    avg_section_len_target: 15
    tables_simple: 10
    lists_depth_ok: 10
    images_with_alt: 5
  risk_weights:
    deep_nesting: 20
    complex_tables: 25
    unresolved_anchors: 15
    mixed_inline_blocks: 10

classification:
  task_keywords: ["click", "run", "open", "select", "type", "press"]
  task_landmarks: ["prerequisites", "steps", "results", "troubleshooting"]
  reference_markers: ["parameters", "options", "syntax", "defaults"]

limits:
  target_section_tokens: [50, 500]
```

---

## 4. Run the assessment first

Before converting anything, run Stage 0 alone to understand your content:

```bash
dita-etl assess \
  --config config/config.yaml \
  --assess-config config/assess.yaml \
  --input docs/
```

This writes to `build/out/assess/` and prints:

```
Assessment complete. Report: build/out/assess/report.html
```

### What the assessment produces

| File | What to look at |
|---|---|
| `report.html` | Open in a browser — sortable table of all files with readiness and risk scores |
| `inventory.json` | Machine-readable per-file metrics (section count, avg tokens, heading validity) |
| `dedupe_map.json` | Near-duplicate clusters — files grouped by content similarity |
| `plans/<file>.conversion_plan.json` | Per-file predicted topic type and section-level predictions |

### Reading `report.html`

The report shows every source file ranked by **topicization readiness**
(0–100, higher is better) and **conversion risk** (0–100, lower is better).

- **High readiness, low risk** — convert as-is.
- **High readiness, high risk** — convert, but review complex tables or deep
  nesting manually after.
- **Low readiness** — the file is likely a large container document that
  should be split before conversion. Check the section count and average
  token length.

### Reading a conversion plan

```json
{
  "source": "docs/install-guide.md",
  "default_topic_type": "task",
  "sections": [
    { "title": "Installation", "pred": "task", "confidence": 0.91 },
    { "title": "Prerequisites", "pred": "task", "confidence": 0.85 },
    { "title": "Configuration options", "pred": "reference", "confidence": 0.78 }
  ],
  "risk": 12,
  "readiness": 88
}
```

- `default_topic_type` — the predicted type used by the Transform stage.
- Section-level `pred` and `confidence` — use these to spot sections that
  may need to be split into separate topics.

### Handling near-duplicates

Open `dedupe_map.json` and look for clusters with more than one member.
Decide which canonical version to keep before running the full pipeline.
The assessment only **proposes** — it does not delete files.

---

## 5. Tune classification rules

After reviewing the assessment, add or adjust `classification_rules` in
`config.yaml` to fix any mis-predicted files. Rules take priority over the
assess-stage prediction:

```yaml
classification_rules:
  by_filename:
    - match: "release-notes"   # always a reference topic
      type: "reference"
```

Pattern matching uses `fnmatch` glob syntax against the **file stem**
(no extension). `"*guide*"` matches `install-guide.md`, `install-guide.html`.

---

## 6. Run the full pipeline

```bash
dita-etl run \
  --config config/config.yaml \
  --assess-config config/assess.yaml \
  --input docs/
```

The pipeline runs all four stages in sequence:

```
Stage 0  Assess    — re-reads source, writes plans/
Stage 1  Extract   — converts source → DocBook XML (via Pandoc/Oxygen)
Stage 2  Transform — classifies + converts DocBook → DITA topics
Stage 3  Load      — assembles index.ditamap, copies assets
```

On success:

```
Pipeline complete. DITA map: build/out/dita/index.ditamap
```

If any files fail extraction or transformation, warnings are printed but
the pipeline continues. Errors are recorded in the `PipelineOutput` contracts
and summarised in the terminal.

Increase log verbosity to see per-file detail:

```bash
dita-etl --log-level DEBUG run --config config/config.yaml --input docs/
```

---

## 7. Examine the output

```
build/out/
├── assess/
│   ├── inventory.json
│   ├── dedupe_map.json
│   ├── report.html
│   └── plans/
│       ├── install-guide.md.conversion_plan.json
│       └── api-reference.html.conversion_plan.json
│
├── intermediate/
│   └── *.xml                  # DocBook staging files (inspect if topics look wrong)
│
└── dita/
    ├── topics/
    │   ├── install-guide_task.dita
    │   ├── api-reference_reference.dita
    │   └── release-notes_reference.dita
    ├── assets/
    │   ├── images/
    │   └── styles/
    └── index.ditamap
```

Open `dita/index.ditamap` in an XML editor (e.g. Oxygen XML Editor) or
DITA-OT to validate and publish.

---

## 8. Classification priority reference

When multiple signals apply to the same file, this order decides:

| Priority | Signal | Example |
|---|---|---|
| 1 | `by_filename` config rule | `"*guide*"` → `task` |
| 2 | `by_content` config rule | content contains `"procedure"` → `task` |
| 3 | Assess plan hint | predictor confidence ≥ threshold → `reference` |
| 4 | Built-in heuristics | content contains `click`, `run` → `task` |
| 5 | Default | → `concept` |

Config rules always win. An invalid or missing plan file falls through
gracefully to heuristics.

---

## 9. Iterating

The typical iterate cycle is:

1. Run `dita-etl assess` and review `report.html`.
2. Add `classification_rules` for files that need overrides.
3. Run `dita-etl run` and open the `.dita` output.
4. If a topic looks wrong, check `intermediate/*.xml` to see the DocBook
   source — this isolates whether the issue is in extraction or transformation.
5. Adjust config and re-run. Because every stage is deterministic and
   stateless, reruns are safe with the same input directory.

---

## 10. Running tests and CI

```bash
python -m pytest          # full suite with coverage gate (≥90%)
python -m pytest tests/unit/          # unit tests only
python -m pytest tests/integration/  # integration tests only
```

CI enforces the same gate on every push and pull request to `main` via
[`.github/workflows/ci.yml`](../.github/workflows/ci.yml).
