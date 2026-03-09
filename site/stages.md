# Stage reference

## Stage 0 — Assess

**Class:** `dita_etl.stages.assess.AssessStage`

Analyses source files before conversion and writes structured assessment
artefacts to the output directory.

| Input | Type | Description |
|---|---|---|
| `source_paths` | `tuple[str, ...]` | Paths to all source documents |
| `output_dir` | `str` | Where to write assessment artefacts |
| `config_path` | `str` | Path to `assess.yaml` |

**Per-file routing:**

| Extension | Sectionizer used |
|---|---|
| `.md` | `sectionize_markdown()` — heading-boundary split |
| `.html`, `.htm` | `sectionize_html()` — regex-based HTML heading split |
| anything else | `_assess_generic()` — placeholder scores |

**Output artefacts:**

| File | Description |
|---|---|
| `inventory.json` | Per-file metrics, section counts, scores |
| `dedupe_map.json` | Near-duplicate cluster assignments |
| `report.html` | Human-readable summary table |
| `plans/<file>.conversion_plan.json` | Predicted topic types and chunking hints |

The `plans/` directory path is passed to `TransformInput.plans_dir` so that
Stage 2 can use the predicted `default_topic_type` during classification.

---

## Stage 1 — Extract

**Class:** `dita_etl.stages.extract.ExtractStage`

Converts each source file to intermediate DocBook XML using a
format-specific extractor (Strategy pattern). Extractions run in parallel
via a thread pool.

| Extractor | Extensions | Backend |
|---|---|---|
| `MdPandocExtractor` | `.md` | Pandoc (`-f gfm -t docbook`) |
| `HtmlPandocExtractor` | `.html`, `.htm` | Pandoc (`-f html -t docbook`) |
| `DocxPandocExtractor` | `.docx` | Pandoc (`-f docx -t docbook`) |
| `DocxOxygenExtractor` | `.docx` | Oxygen XML Editor scripts |

Configure parallel workers and extractor overrides via `config.yaml`:

```yaml
extract:
  max_workers: 4          # null = auto (CPUs × 2)
  handler_overrides:
    ".docx": "oxygen-docx"
```

---

## Stage 2 — Transform

**Class:** `dita_etl.stages.transform.TransformStage`

Reads each intermediate DocBook XML file, classifies it into a DITA topic
type, and writes a minimal valid DITA topic file.

Classification uses five sources evaluated in priority order:

| Priority | Source | Notes |
|---|---|---|
| 1 | `classification_rules.by_filename` | Glob pattern matched against the source file stem |
| 2 | `classification_rules.by_content` | Regex searched against the full DocBook text |
| 3 | Assess-stage plan hint | `default_topic_type` from `plans/<file>.conversion_plan.json` |
| 4 | Built-in heuristics | Keyword frequency (`click`, `run`, `parameters`…) |
| 5 | Default | `concept` |

The plan hint (priority 3) is loaded from `TransformInput.plans_dir` — set
automatically when running through `run_pipeline()`. An invalid or absent
plan falls through gracefully to the heuristics.

---

## Stage 3 — Load

**Class:** `dita_etl.stages.load.LoadStage`

Assembles all DITA topic paths into a single `index.ditamap` and copies
asset directories (images, styles) from the intermediate folder into
`output_dir/assets/`.

The DITA map is built by the pure function
`dita_etl.transforms.dita.build_map()` — no I/O inside that function.
