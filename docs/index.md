# DITA ETL Pipeline

A composable, pure-Python pipeline for converting mixed-format source
documents (Markdown, HTML, DOCX) into structured DITA 1.3 XML.

## Key features

- **Four stages** — Assess, Extract, Transform, Load — each with single
  responsibility and validated I/O contracts.
- **Functional core** — pure transformation functions contain all business
  logic; I/O is isolated at the imperative shell boundary.
- **Strategy pattern** — pluggable extractors for each source format.
- **Factory pattern** — config-driven extractor registry.
- **No external orchestrator** — plain Python, no heavy frameworks required.
- **90%+ test coverage** enforced by pytest-cov.

## Quick links

- [Architecture and pipeline diagram](pipeline.md)
- [Stage reference](stages.md)
- [Configuration guide](configuration.md)

## Install

```bash
pip install -e ".[dev]"
```

## Run

```bash
dita-etl run --config config/config.yaml --input sample_data/input/
```
