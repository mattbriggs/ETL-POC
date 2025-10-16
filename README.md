# DITA-ETL Pipeline

A modular, Prefect-orchestrated ETL system for converting mixed-format content (HTML, Markdown, DOCX) into structured DITA XML.

Supports assessment, extraction, transformation, and load stages with parallel execution, graceful degradation, and YAML-driven configuration.

## Installation

```bash
git clone https://github.com/your-org/ETL-POC.git
cd ETL-POC
python3 -m venv my_env
source my_env/bin/activate
pip install -e .
```

## Project Structure

```
ETL-POC/
├── dita_etl/                 # Core package
│   ├── stages/               # Extract, transform, load stages
│   ├── assess/               # Inventory, deduplication, scoring
│   ├── orchestrator.py       # Prefect flow definition
│   └── config.py             # Dataclass configuration loader
├── config/config.yaml        # Example pipeline configuration
├── sample_data/input/        # Example markdown/html inputs
├── scripts/cli.py            # Command-line entry point
└── build/                    # Output artifacts (created automatically)
```

## Setting Up the Prefect Server

Prefect handles orchestration, logging, and visualization.  
The ETL pipeline requires a live Prefect API server when run in connected mode.

### Start the Prefect Server (in a separate terminal)

```bash
prefect server start
```

You should see:

```
Starting Prefect server...
⌛ Waiting for API to start...
INFO:     Uvicorn running on http://127.0.0.1:4200 (Press CTRL+C to quit)
INFO:     Prefect UI available at http://127.0.0.1:4200
```

Keep this window open — this is your live orchestration server.

### Configure the CLI Terminal Environment

Open a **new terminal** for the ETL process:

```bash
cd ETL-POC
source my_env/bin/activate
export PREFECT_API_URL="http://127.0.0.1:4200/api"
```

### Verify Connection

```bash
curl http://127.0.0.1:4200/api/admin/version
```

Expected output:

```json
{"prefect_version": "3.x.x"}
```

### Run the Pipeline

```bash
python3 scripts/cli.py --config config/config.yaml --input "/path/to/input/files"
```

You should see log output like:

```
17:32:22.144 | INFO    | prefect.engine - Flow 'DITA ETL Pipeline' started
17:32:22.901 | INFO    | prefect.task_runner - Task run_extract completed
17:32:27.702 | INFO    | prefect.engine - Flow run completed: COMPLETED
```

Visit [http://127.0.0.1:4200](http://127.0.0.1:4200) to view detailed logs and task visualizations.

## Configuration

### Example: Markdown -> DITA

```yaml
source_formats:
  treat_as_markdown: [".md"]

tooling:
  pandoc_path: "/usr/local/bin/pandoc"
  oxygen_scripts_dir: null
  java_path: "/usr/bin/java"
  saxon_jar: "/usr/local/lib/saxon-he.jar"

dita_output:
  output_folder: "build/dita_output"
  map_title: "Markdown to DITA Conversion"

classification_rules:
  by_filename:
    - pattern: "guide"
      type: "task"
  by_content:
    - pattern: "install"
      type: "concept"
```

### Example: HTML -> DITA

```yaml
source_formats:
  treat_as_html: [".html", ".htm"]

tooling:
  pandoc_path: "/usr/local/bin/pandoc"
  oxygen_scripts_dir: "/Applications/oxygen/scripts"
  java_path: "/usr/bin/java"
  saxon_jar: "/usr/local/lib/saxon-he.jar"

dita_output:
  output_folder: "build/dita_output"
  map_title: "HTML to DITA Conversion"

classification_rules:
  by_filename:
    - pattern: "reference"
      type: "reference"
  by_content:
    - pattern: "procedure"
      type: "task"
```

## Output Artifacts

After a successful run:

```
build/
├── assess/                  # Stage 0 assessment reports
│   ├── inventory.json
│   ├── dedupe_map.json
│   └── report.html
├── intermediate/            # Stage 1 normalized XML (DocBook/HTML5)
├── dita_output/             # Stage 3 DITA topics + map
│   ├── topic-1.dita
│   ├── topic-2.dita
│   └── index.ditamap
```

## Common Issues

### Prefect Connection Refused
If you see:
```
RuntimeError: Failed to reach API at http://127.0.0.1:4200/api/
```
-> The Prefect server is not running.  
Start it with:
```bash
prefect server start
```

### Output Folder Missing
No need to pre-create output folders — the ETL automatically calls `ensure_dir()` for intermediate and output directories.

## Notes for Extensibility

- To add a **new extractor** (e.g., `pptx`, `xml`, `pdf`):
  - Add a new extractor under `dita_etl/stages/extractors/`
  - Register it in `ExtractStage._build_registry()`
- To tune classification or chunking:
  - Edit your YAML config and re-run
- To run assessments only:
  ```bash
  python3 scripts/cli.py --config config/config.yaml --input <dir> --stage assess
  ```
