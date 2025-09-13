
# Design and Maintenance


This design keeps the pipeline **predictable, observable, and evolvable**. The assessment stage isn’t a report for curiosity; it’s a **contracted, machine-consumable gate** that drives chunking and classification decisions, cuts waste by deduping early, and lets you prioritize fixes where they’ll save the most effort.

## Architecture
- **Stages** (Strategy pattern): `ExtractStage`, `TransformStage`, `LoadStage` implement a common `Stage` interface, enabling substitution and composition.
- **Runner** (Adapter): `SubprocessRunner` abstracts shell commands (Pandoc/Saxon/Oxygen). Swap with a different runner or a dry-run.
- **Classification** (Policy): `classify_topic` applies config rules then heuristics.
- **Config** (Builder): Dataclasses parse YAML into strongly-typed objects.
- **Flow**: Prefect tasks wrap each stage; a flow wires them together. Parallelism is enabled at the task level and can be extended with thread pools within tasks for heavy I/O.

## Determinism
- Stable iteration orders, explicit inputs/outputs, and immutable artifacts. Hashing utilities (`hashing.py`) allow cache keys and verification.

## Graceful Degradation
- Extraction errors are captured per-file; pipeline continues. Errors are returned in `StageResult.data["errors"]`.

## Extending Formats
- Implement additional converters in `ExtractStage` (e.g., detect .docx -> use Oxygen Batch Converter).
- Add mapping templates/XSLT in `TransformStage` for richer DITA outputs (e.g., steps/cmd, tables, images).

## Custom DITA
- If using specialized DTDs, generate proper root elements and DOCTYPEs in `TransformStage`. Parameterize via config.

## Testing
- Tests mock `SubprocessRunner.run`, avoiding real tool calls.
- Fixtures in `tests/` cover all class methods for 100% method coverage.
- Use `pytest -q --cov=dita_etl`

## Maintenance
- Keep config-driven rules up to date.
- Replace placeholder XSLT with real mapping and wire Saxon call in `_apply_xslt`.
- Optionally adopt DVC or Prefect blocks for artifact/version management.

Here’s an expanded, nuts-and-bolts design you can drop into `docs/design.md` (or merge into your existing “Design & Maintenance” section). I’ve folded in the **Assessment (Stage 0)** architecture and contracts, and tightened the patterns, data shapes, and operational guidance.

# Detailed design of the DITA ETL Pipeline

## 0) Design Goals (non-negotiables)

- **Isolate concerns:** Each stage does one job. I/O is explicit. Artifacts are immutable and content-addressable (hashable).
- **Contracts over tools:** Stages communicate through **documented schemas** (JSON/YAML), not library return types.
- **Deterministic:** Same inputs ⇒ same outputs. Stable ordering, normalized encodings, sorted globs, fixed seeds.
- **Config-first:** Mappings, taxonomies, chunk rules, and output flavors live in versioned YAML/JSON.
- **Graceful degradation:** Per-file failure is quarantined; the pipeline continues.
- **Testable:** Fixtures and **golden files** verify every stage; subprocess calls are mocked.


## 1) High-Level Architecture

```mermaid
flowchart LR
  subgraph Stage0[Assessment]
    A0[Inventory Builder] --> A1[Duplicate Detector]
    A1 --> A2[Readiness & Risk Scorer]
    A2 --> A3[Conversion Plan Emitter]
  end

  subgraph Stage1[Extract]
    E0[Format Detector] --> E1[Pandoc / Oxygen / CLI]
    E1 --> E2[Intermediate (DocBook/HTML5)]
  end

  subgraph Stage2[Transform]
    T0[XSLT/Saxon\nDocBook→DITA] --> T1[Topic Splitter]
    T1 --> T2[Classification Router\n(concept/task/reference)]
  end

  subgraph Stage3[Load]
    L0[DITA Map Builder] --> L1[Output Folder]
  end

  Stage0 -->|plans/*.conversion_plan.json| Stage2
  Stage1 -->|intermediate/*.xml| Stage2
  Stage2 -->|*.dita/.ditamap| Stage3
```

- **Orchestrator:** Prefect flow (`build_flow`) wires the stages. Each stage is a **Strategy** (OOP) with a common interface `Stage.run(inputs) -> StageResult`.
- **Runner:** `SubprocessRunner` is an **Adapter** around CLI tools (Pandoc, Saxon, Oxygen). It captures `stdout/stderr/rc`, normalizes errors.
- **Policies:** Classification and chunking are **Policy** objects driven by config; heuristics are pluggable.


## 2) Core Modules & Patterns

### 2.1 Stage base class

```python
class StageResult:
    success: bool
    message: str
    data: dict  # explicit, serializable payload

class Stage(Protocol):
    def run(self, inputs: Any) -> StageResult: ...
```

- **Never** return in-memory ASTs across stage boundaries. Persist artifacts, return **paths** + structured JSON.

### 2.2 Extract (Stage 1)

- **Responsibility:** Normalize source → Intermediate (DocBook/HTML5) with explicit reader selection:
  - `.md` → Pandoc `-f gfm`
  - `.html`/`.htm` → Pandoc `-f html`
  - `.docx`/others → Oxygen Batch Converter or Pandoc if supported
- **Outputs:** `build/intermediate/<basename>.xml` (+ checksum sidecars optional).
- **Contract (extract.result.json):**
  ```json
  {
    "inputs": [".../a.md",".../b.html"],
    "outputs": {".../a.md":"build/intermediate/a.xml"},
    "errors": {".../bad.docx":"<stderr excerpt>"}
  }
  ```

### 2.3 Transform (Stage 2)

- **Responsibility:** Map Intermediate → DITA topics + map.
- **Inputs:** `intermediate/*.xml`, **and** optional **conversion plans** from Stage 0.
- **Steps:**
  1) **DocBook→DITA** (Saxon + XSL): produce semantically conservative DITA.
  2) **Topic Splitter:** split by heading level (configurable) and by **plan** sections.
  3) **Classification Router:** set root element `concept|task|reference` per plan or heuristic fallback.
- **Outputs:** `build/out/*.dita`, `build/out/out.ditamap`.

### 2.4 Load (Stage 3)

- **Responsibility:** Build a DITA map, ensure referential integrity, prep for CCMS import.
- **Outputs:** `build/out/out.ditamap` and folder of topics/media.

---

## 3) Assessment (Stage 0) — Detailed Design

**Purpose:** Upstream quality gate. Quantify structure, duplication, and expected conversion pain before extraction/transform.

### 3.1 Submodules

- `assess_config.py` (**@dataclass** config):
  - `shingling` (ngram, permutations, threshold)
  - `scoring` (topicization/risk weights)
  - `classification` (keywords/landmarks)
  - `limits` (target section size)
  - `duplication` (policy knobs)
- `structure.py`: lightweight **sectionizer** (Markdown today; extend with HTML/DOCX adapters).
- `features.py`: counts lists, tables, images, links; token counts; **imperative density**; landmarks.
- `dedupe.py`: MinHash signatures; greedy clustering by Jaccard similarity.
- `scoring.py`: readiness (0–100) + risk (0–100); **predict_topic_type** per section.
- `inventory.py`: **facade** to run batch assessment, write artifacts.
- `emit.py`: write `inventory.json`, `dedupe_map.json`, and **`report.html`**.

### 3.2 Contracts (Schemas)

**`build/assess/inventory.json`**
```json
{
  "files": [
    {
      "path": "/abs/path/file.md",
      "size": 12345,
      "sha256": "…",
      "sections": 6,
      "metrics": {
        "heading_ladder_valid": true,
        "avg_section_tokens": 140,
        "tables_simple": true,
        "lists_depth_ok": true,
        "images_with_alt": true,
        "deep_nesting": false,
        "complex_tables": false,
        "unresolved_anchors": false,
        "mixed_inline_blocks": false
      },
      "topicization_readiness": 75,
      "conversion_risk": 20,
      "predictions": [
        {"index":0,"title":"Intro","pred":"concept","confidence":0.6,"reasons":["expository default"]},
        {"index":1,"title":"Install","pred":"task","confidence":0.85,"reasons":["ordered list + imperative/steps"]}
      ],
      "raw_sections": [
        {"title":"Intro","content":"…"},
        {"title":"Install","content":"…"}
      ]
    }
  ]
}
```

**`build/assess/dedupe_map.json`**
```json
{ "clusters": [
  ["/abs/a.md","/abs/b.md"],
  ["/abs/c.md"]
]}
```

**`build/assess/plans/<filename>.conversion_plan.json`**
```json
{
  "source": "/abs/path/file.md",
  "chunking": {"level": 1, "nested_topics": true},
  "default_topic_type": "task",
  "sections": [
    {"index":0,"title":"Intro","pred":"concept","confidence":0.6,"reasons":["…"]},
    {"index":1,"title":"Install","pred":"task","confidence":0.85,"reasons":["…"]}
  ],
  "risk": 20,
  "readiness": 75
}
```

**`build/assess/report.html`**
- A single HTML file summarizing per-file readiness/risk and duplicate clusters (no runtime deps).

### 3.3 How Stage 0 informs Stage 2

- **Chunking:** `chunking.level` controls where topics split (e.g., H1 boundary).
- **Root topic type:** `default_topic_type` sets `concept/task/reference` for the new topic root.
- **Per-section overrides:** optional—if `sections[i].pred` is present, the splitter can emit nested topics with specific roots.
- **Risk/readiness gates:** Transform stage can **quarantine** sources with `risk ≥ threshold` or `readiness < floor`.

### 3.4 Extending assessment beyond Markdown

Add format adapters in `inventory.py`:
- `.html`: use an HTML parser; derive sections from H1..H6; reuse `features.py`.
- `.docx`: `python-docx` for headings & paragraphs **or** `docx→html` via Pandoc then reuse HTML adapter.
- Keep **contracts identical** so downstream doesn’t care about the format.

## 4) Concurrency & Orchestration

- **Prefect tasks** are the unit of orchestration; prefer **idempotent** tasks with explicit inputs/outputs on disk.
- For I/O-heavy extract/assess, you may parallelize within the task:
  - Thread pools (safe for CLI calls / file I/O).
  - Cap concurrency via config (`max_workers`) to avoid thrashing Pandoc/Saxon.
- Avoid shared mutable state. Write to **unique** temp folders per file, then move into final locations.

**Recommendation:** Keep parallelism coarse-grained (per file) and deterministic (sorted input glob, stable worker count).


## 5) Determinism & Caching

- **Stable globs:** use `glob("**/*", recursive=True)` + `sorted()` + filter files only.
- **Normalization:** UTF-8 decoding with fallback; normalize newlines to `\n`.
- **Content addressing:** write optional `<artifact>.sha256` next to each artifact; embed hashes into `inventory.json`.
- **Cache keys:** hash of (tool versions + config YAML + input file hash) can gate re-runs.


## 6) Error Handling & Degradation

- Each stage returns:
  ```json
  { "outputs": {...}, "errors": {"path":"stderr excerpt"} }
  ```
- Failing files are **quarantined** (do not block the run). Emit a `build/quarantine/` folder if you want to copy originals for manual triage.
- Prefect flow logs summarize per-stage error counts; **never** swallow the stderr—truncate and store in `*.err.txt` sidecars.

---

## 7) Configuration Model

- **Project config (`config/config.yaml`)**: tooling paths (pandoc/java/saxon/oxygen), output folders, classification policies, map title, etc.
- **Assessment config (`config/assess.yaml`)**: shingling/scoring/limits/classification.
- **Override precedence:** CLI `--config` → project `config.yaml` → internal defaults. Assessment has its own file to allow **independent tuning**.

All configs are **schema-checked** in dataclasses; unknown keys should warn (don’t silently ignore).


## 8) Contracts & Schemas (source of truth)

- Treat JSON outputs as **public contracts**. Version them:
  - `schema_version: "1.0"` fields embedded in `inventory.json` and plans.
  - Bump minor when adding fields; bump major for breaking changes.
- Add `docs/schemas/*.json` (JSON Schema) to validate artifacts in CI.


## 9) Logging, Metrics, and Observability

- **Per-task logs:** echo exact CLI args (`pandoc ...`, `java -jar saxon ...`) with redacted secrets.
- **Artifacts index:** write `build/index.json` listing all produced artifacts and their hashes.
- **Timings:** measure wall-clock per file and per stage; include in `inventory.json` (`elapsed_ms`).
- **Prefect server:** prefer a dedicated local server or pin Prefect 2.x for stable dev runs (documented in README).

## 10) Testing Strategy

- **Unit tests:** one test per method. Mock `SubprocessRunner.run` to avoid external tools.
- **Golden tests:** sample inputs → expected `inventory.json`, `*.conversion_plan.json`, and `*.dita`. Compare byte-for-byte with stable whitespace rules.
- **Property tests (optional):** round-trip invariants (e.g., sectionizer never loses headings).
- **Coverage:** `pytest -q --cov=dita_etl --cov-report=term-missing`.

## 11) Extending Formats (playbook)

1. Add a **reader adapter** in Stage 0 (assessment) for new format → sections/features.
2. Add an **extractor** in Stage 1 (e.g., `.docx` → Pandoc/Oxygen).
3. Ensure **intermediate** shape is what Transform expects (DocBook/HTML5).
4. Update config with extension mapping and tool paths.
5. Add fixtures and golden files; update README.


## 12) Custom DITA / Specializations

- Parameterize root DTD/DOCTYPE in Transform:
  - `dita_type_root: "concept|task|reference|mydomain:foo"`
  - `doctype_system/public` for validators.
- Inject specialization attributes via config-driven mapping:
  - Example: map `classification.tags -> @otherprops`, product/version → `@product/@platform`.


## 13) Maintenance and Ops

- **Version everything:** config files, XSLT, and output contracts. Tag releases.
- **Upgrade gate:** when bumping tool versions (Pandoc, Saxon), run assessment on a **known corpus** and diff results (expect minor drift; investigate major swings).
- **Backfills:** if contracts evolve, add a small **migrator** script to rewrite older `inventory.json`/plans to current schema.
- **Artifacts retention:** clean `build/` periodically; keep final `out/` and assessment snapshots per run if you need drift analysis.

## 14) Known Trade-offs

- The Markdown sectionizer is intentionally simple. For high fidelity, normalize to HTML then parse headings, lists, and tables via an HTML DOM (still keep the same output contract).
- MinHash clustering is greedy; large corpora may benefit from LSH bucketing for speed. Keep the threshold conservative; manual review remains crucial.

## 15) Concrete TODOs (near-term)

- [ ] Stage 0: add HTML and DOCX adapters; unify contracts.
- [ ] Stage 2: honor `plans/*.conversion_plan.json` (chunking + root type) end-to-end.
- [ ] Stage 2: replace placeholder XSL with production DocBook→DITA mapping; add Saxon error surface.
- [ ] Add JSON Schemas; validate in CI.
- [ ] Add `build/index.json` + timing + hash sidecars.
- [ ] Dashboard MVP (Streamlit) reading `build/assess/*.json`.

### Appendix A — Example Prefect Flow (with Stage 0)

```python
@flow(name="DITA ETL Pipeline")
def build_flow(config_path: str = "config/config.yaml", input_dir: str = "sample_data/input"):
    cfg = Config.load(config_path)

    # Stage 0 — Assessment (absolute path to avoid CWD surprises)
    _ = run_assessment(config_path="config/assess.yaml", input_dir=input_dir)

    # Stage 1 — Extract
    exts = sorted({e for k,v in getattr(cfg,"source_formats",{}).items() if k.startswith("treat_as_") for e in v}) or [".md",".docx",".html"]
    inputs = list_inputs(input_dir, exts)
    intermediates = run_extract(cfg, inputs)

    # Stage 2 — Transform
    topics = run_transform(cfg, intermediates)

    # Stage 3 — Load
    map_path = run_load(cfg, topics)
    return map_path
```