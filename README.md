
# DITA ETL Pipeline

A modular, config-first ETL pipeline that converts multiple source formats into **DITA 1.3** (concept/task/reference), using:
- **Pandoc** for broad format ingestion
- **Oxygen XML** / **Saxon** for XML/XSLT transforms
- **Prefect** for orchestration and parallelism
- **Python** (OOP + design patterns), with deterministic hashing, graceful degradation, and full unit tests

## Features
- Batch conversion from Markdown (and easily extended to Docx/HTML/etc.) into DITA topics
- Classification into Concept/Task/Reference via rules + heuristics
- DITA map assembly
- Config-driven (YAML) mappings, chunking, output location
- Prefect flow with task parallelism (extensible to multithreading)
- Unit tests (pytest) with 100% coverage of class methods (mocking external tools)

## Install (macOS)
```bash
# 1) Create/activate a venv
python3 -m venv .venv && source .venv/bin/activate

# 2) Install dependencies
pip install -r requirements.txt

# 3) (Optional) Install tools
# brew install pandoc
# Ensure Oxygen XML Editor is installed if you want to use its CLI scripts.
```

## Run
```bash
python scripts/cli.py --config config/config.yaml --input sample_data/input
```
Outputs DITA topics and a `out.ditamap` in `build/out/`.

## Configure
Edit `config/config.yaml` to adjust:
- `classification_rules` for topic type routing
- `chunking` behavior
- `dita_output` folder and map title
- `tooling` paths (pandoc/java/saxon/oxygen)

## Notes
- The provided XSLT (`xsl/docbook2dita.xsl`) is a placeholder. Replace with your DocBook->DITA mapping stylesheet or invoke Oxygen's Batch Converter for direct DITA output.
- External tool calls are wrapped behind a `SubprocessRunner` to ease mocking and testing.

## Running with Prefect (Important)

By default this project uses [Prefect](https://docs.prefect.io) to orchestrate the ETL pipeline.

### Prefect Ephemeral Server Issue on macOS

On macOS, Prefect 3.x sometimes fails to start its **ephemeral API server** with an error like:

```
RuntimeError: Timed out while attempting to connect to ephemeral Prefect API server.
```

If you encounter this:

### Option A — Run a dedicated Prefect server (recommended)

1. In a separate terminal, start a Prefect server:

   ```bash
   prefect server start
   ```

   By default it runs at: http://127.0.0.1:4200

   You can use the same virtual environment (`venv`) where you installed the package, but in a seperate terminaal.

   ```bash
   cd path/to/your/project
   source ./ENV/bin/activate
   perfect server start
   ```

2. In the shell where you will run the ETL pipeline, set the Prefect API URL:

   ```bash
   export PREFECT_API_URL="http://127.0.0.1:4200/api"
   ```

3. Run the CLI from the project root (with your venv activated):

   ```bash
   python scripts/cli.py --config config/config.yaml --input sample_data/input
   ```

### Option B — Pin Prefect to 2.x (simpler, stable local mode)

If you prefer not to run a server, you can use a stable 2.x release of Prefect which doesn’t rely on the ephemeral API:

```bash
python -m pip install "prefect==2.16.9"
```

Then run the CLI as usual:

```bash
python scripts/cli.py --config config/config.yaml --input sample_data/input
```

### Notes on Perfect and Virtual Environments

- Always run using the **same Python interpreter** where you installed the package (`pip install -e .`).  
- If you use VS Code, select your venv under: *Command Palette → Python: Select Interpreter*.  
- Verify Prefect version with:

  ```bash
  python -c "import prefect; print(prefect.__version__)"
  ```

## Documentation

See the [docs/](docs/) folder for design docs, class diagrams, and more.

- [Design and Maintenance](docs/about-the-design-of-the-app.md)
- [How to Run the DITA ETL Pipeline on a Folder of Markdown Files](docs/etl-how-to-markdown.md)
- [How To: Configure and Read the ETL Assessment](docs/etl-how-to-read-the-assessment.md)
- [ETL Pipeline User Manual: Converting Unstructured Content to DITA](docs/etl-user-manual.md)
- [Development of the ETL Process](docs/project.md)

## White Papers

- [Content-to-DITA ETL: Vendor-Neutral, Modular Architecture](docs/etl-design-and-structure.md)
- [ETL Pipeline for Converting Multiple Formats to DITA 1.3](docs/etl-pipeline-overview.md)