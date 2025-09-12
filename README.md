
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
