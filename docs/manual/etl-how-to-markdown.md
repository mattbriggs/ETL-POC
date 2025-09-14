# How to Run the DITA ETL Pipeline on a Folder of Markdown Files

This guide shows you how to run the pipeline against a directory of `.md` files, normalize them with Pandoc, and produce DITA 1.3 topics and a DITA map.

## Prerequisites

- macOS
- Python 3.10+
- Pandoc installed: `brew install pandoc`
- Prefect installed via `requirements.txt`
- Recommended: a virtual environment

## 1) Set up the project

```bash
cd /path/to/ETL-POC
python3 -m venv .venv && source .venv/bin/activate
python -m pip install -U pip
python -m pip install -r requirements.txt
python -m pip install -e .
```

> If packaging errors mention “Multiple top-level packages”, ensure `pyproject.toml` installs only `dita_etl`.

## 2) Prefect orchestration options

**Option A (recommended):** run a dedicated Prefect server in another terminal

```bash
prefect server start
# then, in the terminal where you run the pipeline:
export PREFECT_API_URL="http://127.0.0.1:4200/api"
```

**Option B:** pin Prefect 2.x for simpler local execution

```bash
python -m pip install "prefect==2.16.9"
```

## 3) Configure inputs (optional)

Open `config/config.yaml` and confirm `.md` is treated as Markdown:

```yaml
source_formats:
  treat_as_markdown: [".md"]
```

You can adjust classification heuristics in `config/assess.yaml`.

## 4) Run the pipeline on a directory of Markdown

```bash
python scripts/cli.py --config config/config.yaml --input /absolute/path/to/markdown_dir
```

### What you’ll get

- **Stage 0 (Assessment)** → `build/assess/`
  - `inventory.json` — per-file metrics and predictions
  - `dedupe_map.json` — near-duplicate clusters
  - `plans/*.conversion_plan.json` — per-file topicization plans
  - `report.html` — a human-readable summary

- **DITA Output (Stages 1–3)** → `build/out/`
  - `*.dita` — DITA topics (concept/task/reference)
  - `out.ditamap` — DITA map referencing all topics

## 5) Troubleshooting

- **`ModuleNotFoundError: dita_etl`** — use the same interpreter you installed into: `python -m pip install -e .` then `python scripts/cli.py ...`
- **Prefect ephemeral server timeout** — either run `prefect server start` and set `PREFECT_API_URL`, or install `prefect==2.16.9`.
- **`pandoc: command not found`** — install via Homebrew: `brew install pandoc`.
- **No topics produced** — verify the `--input` path; inspect `build/assess/report.html` to confirm files were seen.

## 6) Notes

- **Markdown normalization:** `.md` is read via Pandoc’s **GFM** reader (`-f gfm`) for consistent headings/lists.
- **Topic boundaries:** `#` becomes a new topic; `##+` become sections. Adjust in `plans/*.conversion_plan.json` if needed.
- **Classification:** Heuristics route sections to concept/task/reference; tune in `config/assess.yaml`.
- **Media:** Keep images next to source Markdown; relative links like `![alt](images/foo.png)` are preserved.

### Markdown-first usage

The pipeline ingests Markdown out of the box. We normalize with Pandoc’s **GitHub-Flavored Markdown** reader (`-f gfm`) before converting to DocBook and then DITA.

```bash
brew install pandoc
python3 -m venv .venv && source .venv/bin/activate
python -m pip install -U pip
python -m pip install -r requirements.txt
python -m pip install -e .
python scripts/cli.py --config config/config.yaml --input /path/to/markdown_dir
```

Notes:
- Relative image/asset links in Markdown are preserved through normalization.
- Heading policy: `#` starts a new topic; `##+` become sections. Heuristics pick concept/task/reference.

## Sanity checklist

- Ensure `pandoc` is on your PATH (`pandoc -v`).
- If you use VS Code, select the venv interpreter (⌘⇧P → *Python: Select Interpreter*).
- Prefer `python` from the venv (not the system `python3`) when running.