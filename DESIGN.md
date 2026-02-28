# Design Document

This document describes the architecture, patterns, and data flows of the DITA ETL pipeline.

---

## 1. System context

```mermaid
flowchart TD
    USER(["User / CI system"])
    CLI["dita-etl CLI\ncli.py + Click"]
    PL["Pipeline orchestrator\npipeline.py"]
    FS[("Filesystem\nsource docs")]
    OUT[("Filesystem\nbuild/out/")]
    PANDOC["Pandoc\n(subprocess)"]
    OXY["Oxygen scripts\n(optional subprocess)"]

    USER -->|"dita-etl run --input ..."| CLI
    CLI -->|"run_pipeline()"| PL
    FS -->|"source .md / .html / .docx"| PL
    PL -->|"DocBook XML"| PANDOC
    PL -->|"DocBook XML (DOCX only)"| OXY
    PL -->|"*.dita + index.ditamap"| OUT
```

---

## 2. Pipeline stage flow

The pipeline is composed of four sequential stages. Every stage boundary
is crossed through a **typed, immutable contract dataclass**.

```mermaid
flowchart LR
    IN[("Source files")]

    subgraph S0["Stage 0 · Assess"]
        direction TB
        A["AssessStage.run()"]
        A0["assess/inventory.py\nassess_batch()"]
        A --> A0
    end

    subgraph S1["Stage 1 · Extract"]
        direction TB
        E["ExtractStage.run()"]
        E0["ThreadPoolExecutor\n+ extractor registry"]
        E --> E0
    end

    subgraph S2["Stage 2 · Transform"]
        direction TB
        T["TransformStage.run()"]
        T0["classify_topic()\nbuild_topic()"]
        T --> T0
    end

    subgraph S3["Stage 3 · Load"]
        direction TB
        L["LoadStage.run()"]
        L0["build_map()\ncopy_assets()"]
        L --> L0
    end

    OUT[("index.ditamap\n+ topics/ + assets/")]

    IN --> S0
    S0 -->|"AssessOutput"| S1
    S1 -->|"ExtractOutput"| S2
    S2 -->|"TransformOutput"| S3
    S3 --> OUT
```

---

## 3. Stage contracts (class diagram)

All contracts are `@dataclass(frozen=True)` with `__post_init__` validation.

```mermaid
classDiagram
    class ContractError {
        <<exception>>
    }

    class AssessInput {
        +source_paths: tuple[str, ...]
        +output_dir: str
        +config_path: str
        +__post_init__()
    }

    class AssessOutput {
        +inventory_path: str
        +dedupe_path: str
        +report_path: str
        +plans_dir: str
        +__post_init__()
    }

    class ExtractInput {
        +source_paths: tuple[str, ...]
        +intermediate_dir: str
        +handler_overrides: dict[str, str]
        +max_workers: int | None
        +__post_init__()
    }

    class ExtractOutput {
        +outputs: dict[str, str]
        +errors: dict[str, str]
        +success: bool
    }

    class TransformInput {
        +intermediates: dict[str, str]
        +output_dir: str
        +rules_by_filename: tuple
        +rules_by_content: tuple
        +__post_init__()
    }

    class TransformOutput {
        +topics: dict[str, list[str]]
        +errors: dict[str, str]
        +success: bool
    }

    class LoadInput {
        +topics: dict[str, list[str]]
        +output_dir: str
        +map_title: str
        +intermediate_dir: str | None
        +__post_init__()
    }

    class LoadOutput {
        +map_path: str
        +topic_count: int
        +__post_init__()
    }

    class PipelineOutput {
        +assess: AssessOutput
        +extract: ExtractOutput
        +transform: TransformOutput
        +load: LoadOutput
        +map_path: str
    }

    AssessInput ..> ContractError : raises
    AssessOutput ..> ContractError : raises
    ExtractInput ..> ContractError : raises
    LoadInput ..> ContractError : raises
    LoadOutput ..> ContractError : raises

    PipelineOutput *-- AssessOutput
    PipelineOutput *-- ExtractOutput
    PipelineOutput *-- TransformOutput
    PipelineOutput *-- LoadOutput
```

---

## 4. Layered architecture

The codebase is split into a **functional core** (pure functions, no I/O) and an **imperative shell** (stages, orchestrator, CLI) that handles all side effects.

```mermaid
flowchart TB
    subgraph Shell["Imperative Shell  —  side effects allowed"]
        CLI["cli.py\nClick entry-point"]
        PL["pipeline.py\nOrchestrator"]
        ST0["stages/assess.py"]
        ST1["stages/extract.py"]
        ST2["stages/transform.py"]
        ST3["stages/load.py"]
        IO1["io/filesystem.py"]
        IO2["io/subprocess_runner.py"]
        INV["assess/inventory.py\n(batch runner)"]
    end

    subgraph Core["Functional Core  —  pure functions, zero I/O"]
        CL["transforms/classify.py"]
        DT["transforms/dita.py"]
        STR["assess/structure.py"]
        FT["assess/features.py"]
        SC["assess/scoring.py"]
        PR["assess/predict.py"]
        DD["assess/dedupe.py"]
        RPT["assess/report.py\n(render only)"]
    end

    subgraph Config["Configuration"]
        CFG["config.py"]
        ACFG["assess/config.py"]
        CTR["contracts.py"]
        LOG["logging_config.py"]
    end

    CLI --> PL
    PL --> ST0 & ST1 & ST2 & ST3
    ST0 --> INV
    INV --> STR & FT & SC & PR & DD & RPT
    ST1 --> IO1 & IO2
    ST2 --> CL & DT & IO1
    ST3 --> DT & IO1
    INV --> IO1

    Shell -.->|"reads"| Config
    Core -.->|"no dependency on"| IO1
    Core -.->|"no dependency on"| IO2
```

---

## 5. Full pipeline sequence

```mermaid
sequenceDiagram
    actor User
    participant CLI as cli.py
    participant PL as pipeline.py
    participant CFG as Config
    participant S0 as AssessStage
    participant S1 as ExtractStage
    participant S2 as TransformStage
    participant S3 as LoadStage
    participant FS as Filesystem

    User->>CLI: dita-etl run --config ... --input ...
    CLI->>PL: run_pipeline(config_path, assess_config_path, input_dir)
    PL->>CFG: Config.load(config_path)
    CFG-->>PL: Config
    PL->>FS: discover_files(input_dir, extensions)
    FS-->>PL: [source_paths]

    PL->>S0: run(AssessInput)
    S0->>FS: read each source file
    S0->>S0: sectionize → features → score → predict → dedupe
    S0->>FS: write inventory.json, dedupe_map.json, report.html, plans/
    S0-->>PL: AssessOutput

    PL->>S1: run(ExtractInput)
    S1->>S1: build_registry() → ext→extractor map
    loop parallel ThreadPoolExecutor
        S1->>FS: run pandoc/oxygen subprocess
        FS-->>S1: DocBook XML
    end
    S1-->>PL: ExtractOutput(outputs, errors)

    PL->>S2: run(TransformInput)
    loop for each DocBook XML
        S2->>S2: classify_topic()
        S2->>S2: extract_title() + extract_body()
        S2->>S2: build_topic()
        S2->>FS: write *.dita
    end
    S2-->>PL: TransformOutput(topics, errors)

    PL->>S3: run(LoadInput)
    S3->>S3: build_map() → make_topicref() per topic
    S3->>FS: write index.ditamap
    S3->>FS: copy_assets(intermediate → output/assets/)
    S3-->>PL: LoadOutput(map_path, topic_count)

    PL-->>CLI: PipelineOutput
    CLI-->>User: exit 0
```

---

## 6. Assess sub-pipeline

Stage 0 runs a full analysis sub-pipeline on the source files before any conversion happens.

```mermaid
flowchart TD
    IN["Source file\n(.md or other)"]

    subgraph IO["I/O shell — assess/inventory.py"]
        READ["read_text(path)"]
        WJ1["write_json → inventory.json"]
        WJ2["write_json → dedupe_map.json"]
        WH["write_text → report.html"]
        WP["write_json → plans/*.json"]
    end

    subgraph MD["Markdown path (pure)"]
        SEC["structure.sectionize_markdown()"]
        FEA["features.extract_features()  ×n sections"]
        SCT["scoring.score_topicization()"]
        SCR["scoring.score_risk()"]
        PRD["predict.predict_topic_type()  ×n sections"]
    end

    subgraph GEN["Generic path (pure)"]
        G["_assess_generic()\nplaceholder scores"]
    end

    subgraph DUP["Deduplication (pure)"]
        MH["dedupe.minhash_signature()  ×n files"]
        CL["dedupe.cluster_near_duplicates()"]
    end

    subgraph RPT["Report (pure render)"]
        RH["report.render_report_html()"]
    end

    IN --> READ
    READ -->|".md"| SEC
    READ -->|"other"| G

    SEC --> FEA --> SCT & SCR & PRD
    SCT & SCR & PRD --> WJ1
    G --> WJ1

    WJ1 -->|"all results"| MH --> CL --> WJ2
    WJ1 & WJ2 --> RH --> WH
    WJ1 --> WP
```

---

## 7. Extract stage — Strategy + Factory

```mermaid
flowchart TD
    EI["ExtractInput\nsource_paths, intermediate_dir\nhandler_overrides"]

    subgraph Factory["build_registry() — Factory"]
        REG["dict[ext → FileExtractor]"]
        MD["MdPandocExtractor\n.md"]
        HTML["HtmlPandocExtractor\n.html / .htm"]
        DOCX["DocxPandocExtractor\n.docx (default)"]
        OXY["DocxOxygenExtractor\n.docx (override)"]
        REG --> MD & HTML & DOCX
        REG -.->|"handler_overrides"| OXY
    end

    subgraph Pool["ThreadPoolExecutor"]
        W1["worker: a.md → a.xml"]
        W2["worker: b.html → b.xml"]
        W3["worker: c.docx → c.xml"]
    end

    subgraph Strategy["FileExtractor protocol"]
        direction LR
        FE["FileExtractor\nextract(src, dst, runner)"]
        SR["SubprocessRunner\nrun(args) → stdout"]
        FE --> SR
    end

    EI --> Factory
    Factory --> Pool
    Pool --> Strategy
    Strategy -->|"pandoc/oxygen subprocess"| FS[("intermediate/*.xml")]
    Pool -->|"ExtractOutput"| EO["ExtractOutput\noutputs: dict\nerrors: dict"]
```

---

## 8. Transform data flow

```mermaid
flowchart LR
    XML["intermediate/\ndoc.xml\n(DocBook)"]

    subgraph Pure["Functional core — transforms/"]
        ET["dita.extract_title()\n→ str"]
        EB["dita.extract_body()\n→ str (DITA p elements)"]
        CT["classify.classify_topic()\n→ topic_type: str"]
        BT["dita.build_topic()\n→ DITA XML string"]
    end

    subgraph Rules["Classification priority"]
        R1["1. filename rules"]
        R2["2. content rules"]
        R3["3. heuristics\n(imperative density etc.)"]
        R4["4. default: concept"]
        R1 --> R2 --> R3 --> R4
    end

    FS["topics/\ndoc_concept.dita\n(DITA 1.3)"]

    XML --> ET & EB & CT
    CT --- Rules
    ET & EB & CT --> BT
    BT -->|"write_text()"| FS
```

---

## 9. Load assembly

```mermaid
flowchart TD
    TI["TransformOutput\ntopics: dict[src → list[dita_path]]"]

    subgraph Pure["Functional core — transforms/dita.py"]
        MT["make_topicref(topic_path, base_dir)\n→ topicref href XML\n(walk_up=True for sibling dirs)"]
        BM["build_map(title, topic_paths, base_dir)\n→ DITA map XML string"]
        ESC["saxutils.escape()\n→ safe title"]
    end

    subgraph IO["I/O — imperative shell"]
        WT["write_text(map_path, map_xml)"]
        CA["copy_assets(intermediate → output/assets/)"]
    end

    OUT["output/\n├── topics/*.dita\n├── assets/\n│   ├── images/\n│   └── styles/\n└── index.ditamap"]

    TI --> MT --> BM
    ESC --> BM
    BM --> WT --> OUT
    CA --> OUT
```

---

## 10. Module dependency graph

Arrows point from importer to importee. Modules in the functional core have
**no arrows** pointing to `io/`.

```mermaid
graph TD
    CLI["cli.py"] --> PL["pipeline.py"]
    PL --> CFG["config.py"]
    PL --> CTR["contracts.py"]
    PL --> LOG["logging_config.py"]
    PL --> IOF["io/filesystem.py"]

    PL --> SA["stages/assess.py"]
    PL --> SE["stages/extract.py"]
    PL --> ST["stages/transform.py"]
    PL --> SL["stages/load.py"]

    SA --> INV["assess/inventory.py"]
    SA --> CTR

    INV --> STR["assess/structure.py 🟢"]
    INV --> FT["assess/features.py 🟢"]
    INV --> SC["assess/scoring.py 🟢"]
    INV --> PR["assess/predict.py 🟢"]
    INV --> DD["assess/dedupe.py 🟢"]
    INV --> RPT["assess/report.py 🟢"]
    INV --> ACFG["assess/config.py"]
    INV --> IOF

    SE --> REG["extractors/registry.py"]
    SE --> IOR["io/subprocess_runner.py"]
    SE --> IOF
    SE --> CTR

    REG --> MD["extractors/md_pandoc.py"]
    REG --> HTML["extractors/html_pandoc.py"]
    REG --> DOCXP["extractors/docx_pandoc.py"]
    REG --> DOCXO["extractors/docx_oxygen.py"]

    ST --> CL["transforms/classify.py 🟢"]
    ST --> DT["transforms/dita.py 🟢"]
    ST --> IOF
    ST --> CTR

    SL --> DT
    SL --> IOF
    SL --> CTR

    classDef pure fill:#d4edda,stroke:#28a745,color:#155724
    class STR,FT,SC,PR,DD,RPT,CL,DT pure
```

> 🟢 = pure function module (no `io/` imports, no side effects)

---

## 11. Source file lifecycle

State transitions for a single source file as it moves through the pipeline.

```mermaid
stateDiagram-v2
    [*] --> Discovered : discover_files()

    Discovered --> Assessed : AssessStage reads content,\nscores readiness + risk,\npredicts topic type

    Assessed --> Extracted : ExtractStage runs\npandoc/oxygen subprocess\n→ DocBook XML

    Extracted --> ExtractionFailed : subprocess error\nor unknown extension
    ExtractionFailed --> [*] : recorded in\nExtractOutput.errors

    Extracted --> Transformed : TransformStage classifies,\nextracts title+body,\nbuilds DITA XML

    Transformed --> TransformFailed : XML parse error\nor unknown topic type
    TransformFailed --> [*] : recorded in\nTransformOutput.errors

    Transformed --> Loaded : LoadStage generates\ntopicref in DITA map

    Loaded --> [*] : DITA topic + map\nwritten to output/
```

---

## 12. Architectural patterns

### Functional core + imperative shell

All business logic (classification, scoring, XML construction, deduplication)
lives in **pure functions** that take data in and return data out — no
filesystem access, no subprocess calls, no global state. The "shell" (CLI,
pipeline orchestrator, stage `run()` methods) handles I/O and wires pure
functions together.

| Layer | Modules | Constraint |
|---|---|---|
| Functional core | `transforms/`, `assess/structure.py`, `assess/features.py`, `assess/scoring.py`, `assess/predict.py`, `assess/dedupe.py`, `assess/report.py` | No imports from `io/` |
| Imperative shell | `cli.py`, `pipeline.py`, `stages/`, `assess/inventory.py` | May call `io/` |
| I/O boundary | `io/filesystem.py`, `io/subprocess_runner.py` | Only place `os`, `shutil`, `subprocess` are used |

**Benefits:** Pure functions are trivially unit-tested without mocking. The
functional core is portable to async or distributed runtimes without changes.

---

### Typed stage contracts

Every stage boundary is crossed using a frozen `@dataclass` with `__post_init__`
validation. Stages only accept and return these contracts — no loose `dict`,
no `**kwargs`.

**Benefits:** Contracts make implicit assumptions explicit at construction time.
Immutability (`frozen=True`) prevents accidental mutation across stage boundaries.
Type checkers (mypy) can verify the full pipeline end-to-end.

---

### Strategy pattern — format extractors

Each source format is handled by a separate class (`MdPandocExtractor`,
`HtmlPandocExtractor`, `DocxPandocExtractor`, `DocxOxygenExtractor`) that
satisfies the `FileExtractor` protocol. `ExtractStage` selects the correct
strategy at runtime via the registry.

**Benefits:** New formats can be added without touching `ExtractStage`. The
Oxygen and Pandoc DOCX extractors can be swapped via `handler_overrides`
config without code changes.

---

### Factory pattern — extractor registry

`build_registry()` is a factory function that constructs the
`extension → extractor` mapping from configuration at pipeline startup. It
encapsulates creation logic and applies caller-supplied overrides.

**Benefits:** Decouples stage construction from the registry's internal
structure. Config-driven overrides require no code changes.

---

### Protocol-based duck typing

`SubprocessRunner` satisfies the `Runner` protocol. Tests inject a
`RecordingRunner` that records calls without spawning real processes. No
monkey-patching of stdlib required in extractor tests.

---

## 13. Trade-offs

| Decision | Alternative considered | Rationale |
|---|---|---|
| Plain `dataclass` contracts | Pydantic models | Avoids a runtime dependency; stdlib validation is sufficient |
| `Protocol`-based runner | ABC inheritance | Duck typing is more composable; avoids import coupling |
| Thread pool in `ExtractStage` | `asyncio` | Pandoc calls are subprocess-bound, not coroutine-friendly; threads are simpler |
| Click CLI | argparse | Composable command groups, auto-help, better testability |
| Removed Prefect | Prefect / Airflow | Removes a heavy optional dependency; four sequential stages do not require a workflow engine |
| Separate `transforms/` module | Inline logic in stages | Enables direct unit testing of transformation logic without any I/O setup |
| `walk_up=True` in `make_topicref` | Require topics inside map dir | DITA maps legitimately reference topics in sibling directories; `walk_up` produces valid relative hrefs |
