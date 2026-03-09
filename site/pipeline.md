# Architecture and pipeline

## Stage flow

```
Source files
    │
    ▼  AssessInput
┌─────────────────┐
│  Stage 0        │  inventory.json, dedupe_map.json,
│  Assess         │  report.html, plans/*.json
└────────┬────────┘
         │  AssessOutput
         ▼  ExtractInput
┌─────────────────┐
│  Stage 1        │  intermediate/*.xml  (DocBook)
│  Extract        │
└────────┬────────┘
         │  ExtractOutput → TransformInput
         ▼
┌─────────────────┐
│  Stage 2        │  dita/topics/*.dita
│  Transform      │
└────────┬────────┘
         │  TransformOutput → LoadInput
         ▼
┌─────────────────┐
│  Stage 3        │  dita/index.ditamap
│  Load           │  dita/assets/
└─────────────────┘
```

Every arrow is a typed, frozen dataclass defined in `dita_etl/contracts.py`.
Stages never communicate through shared state or global variables.

## Functional core vs. imperative shell

```
┌────────────────────────────────────────────┐
│  Imperative shell (I/O, orchestration)     │
│  cli.py  pipeline.py  stages/*.py          │
│  io/filesystem.py  io/subprocess_runner.py │
└─────────────────┬──────────────────────────┘
                  │ calls
                  ▼
┌────────────────────────────────────────────┐
│  Functional core (pure, no I/O)            │
│  transforms/classify.py                    │
│  transforms/dita.py                        │
│  assess/structure.py                       │
│  assess/features.py                        │
│  assess/scoring.py                         │
│  assess/predict.py                         │
│  assess/dedupe.py                          │
│  assess/report.py (render_report_html)     │
└────────────────────────────────────────────┘
```

Pure functions receive data and return data.
They have no side effects and do not import `os`, `shutil`, or `subprocess`.

## Design patterns applied

| Pattern | Where | Why |
|---|---|---|
| Functional core + imperative shell | Whole codebase | Testability, separation of concerns |
| Strategy | `dita_etl/extractors/` | Each format is an independent, swappable extractor |
| Factory | `dita_etl/extractors/registry.py` | Config-driven registry construction |
| Protocol / duck typing | `Runner`, `FileExtractor` | Composable without inheritance coupling |
| Typed contracts | `dita_etl/contracts.py` | Explicit, validated stage boundaries |
