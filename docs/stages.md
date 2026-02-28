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

**Output artefacts:**

| File | Description |
|---|---|
| `inventory.json` | Per-file metrics, section counts, scores |
| `dedupe_map.json` | Near-duplicate cluster assignments |
| `report.html` | Human-readable summary table |
| `plans/<file>.conversion_plan.json` | Predicted topic types and chunking hints |

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

Override the extractor for a specific extension via `config.yaml`:

```yaml
extract:
  handler_overrides:
    ".docx": "oxygen-docx"
```

---

## Stage 2 — Transform

**Class:** `dita_etl.stages.transform.TransformStage`

Reads each intermediate DocBook XML file, classifies it into a DITA topic
type, and writes a minimal valid DITA topic file.

Classification priority:

1. `classification_rules.by_filename` — glob pattern match against the
   source filename.
2. `classification_rules.by_content` — regex search against the DocBook
   text.
3. Built-in heuristics — keyword frequency (`click`, `run`, `parameters`…).
4. Default → `concept`.

---

## Stage 3 — Load

**Class:** `dita_etl.stages.load.LoadStage`

Assembles all DITA topic paths into a single `index.ditamap` and copies
asset directories (images, styles) from the intermediate folder into
`output_dir/assets/`.

The DITA map is built by the pure function
`dita_etl.transforms.dita.build_map()` — no I/O inside that function.
