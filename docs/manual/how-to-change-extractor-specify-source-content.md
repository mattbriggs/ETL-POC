# How To: Change the Extractor for “Specify source content”

This guide explains how to **switch**, **modify**, or **replace** the extractor used to pull source content into the pipeline’s **intermediate DocBook** (the “Specify source content” step). It covers:

- How the extractor registry works
- Switching extractors by **config only** (no code changes)
- Editing or creating a custom extractor class
- Wiring it into the registry
- Testing your changes

> Audience: pipeline engineers and maintainers.



## 1) Mental model

- The **Extract stage** routes each input file to a **format-specific extractor** using a **registry** keyed by file extension.
- An extractor is a small class with:
  - `name`: a unique string (e.g., `"pandoc-md"`, `"oxygen-docx"`)
  - `exts`: tuple of handled extensions (e.g., `(".md",)`)
  - `extract(src, dst, runner)`: does the work (often a CLI call) and writes **immutable** output to `dst` (DocBook XML).
- Routing can be **overridden at runtime** via `config.yaml` (no code edits) using `handler_overrides`.

Directory structure (simplified):

```
dita_etl/
  stages/
    extract.py                # ExtractStage: builds registry, runs in parallel
    extractors/
      base.py                 # FileExtractor protocol (interface)
      md_pandoc.py            # .md → DocBook via Pandoc
      html_pandoc.py          # .html/.htm → DocBook via Pandoc
      docx_pandoc.py          # .docx → DocBook via Pandoc
      docx_oxygen.py          # (optional) .docx → DocBook via Oxygen script
```



## 2) Easiest path: switch the extractor in config

If your goal is to change **which extractor handles a file type** (e.g., use Oxygen for `.docx` instead of Pandoc), do it in `config/config.yaml`:

```yaml
extract:
  handler_overrides:
    ".docx": "oxygen-docx"   # route DOCX to the Oxygen extractor by name
  max_workers: 8             # optional: tune parallelism
```

Requirements:
- The extractor named `"oxygen-docx"` must be available (e.g., `docx_oxygen.py` defines `class DocxOxygenExtractor: name = "oxygen-docx"`).
- `ExtractStage` must pass `handler_overrides` from config (your orchestrator already does this if you followed prior steps).

Zero code edits. Re-run:

```bash
python scripts/cli.py --config config/config.yaml --input /path/to/corpus
```



## 3) Modify the existing extractor (“Specify source content”)

If you need to change **how** an extractor works (arguments, pre/post processing), edit its class.

Example: tweak Pandoc Markdown extractor:

**`dita_etl/stages/extractors/md_pandoc.py`**
```python
from __future__ import annotations
from ...runners import SubprocessRunner

class MdPandocExtractor:
    name = "pandoc-md"
    exts = (".md",)

    def __init__(self, pandoc_path: str):
        self.pandoc = pandoc_path

    def extract(self, src: str, dst: str, runner: SubprocessRunner) -> None:
        # Add filters, metadata, or a reference doc if you want
        args = [
            self.pandoc,
            "-f", "gfm",
            "-t", "docbook",
            # Example additions:
            # "--metadata", "toc=true",
            # "--filter", "/usr/local/bin/pandoc-citeproc",
            src, "-o", dst,
        ]
        runner.run(args)
```

Rules:
- **Never** modify input files in place.
- **Always** write the complete artifact to `dst` (DocBook XML).
- Keep it **deterministic**: fixed args, no env randomness.



## 4) Create a new extractor (custom “Specify source content”)

If you’re adding a new source or toolchain, create a new class and register it.

### 4.1 Create the extractor

**`dita_etl/stages/extractors/pages_oxygen.py`**
```python
from __future__ import annotations
import os
from ...runners import SubprocessRunner

class PagesOxygenExtractor:
    name = "oxygen-pages"
    exts = (".pages",)

    def __init__(self, oxygen_scripts_dir: str):
        if not oxygen_scripts_dir:
            raise ValueError("oxygen_scripts_dir is required for oxygen-pages")
        self.scripts = oxygen_scripts_dir

    def extract(self, src: str, dst: str, runner: SubprocessRunner) -> None:
        # Call a wrapper script that runs Oxygen CLI scenario
        script = os.path.join(self.scripts, "pages2docbook.sh")
        runner.run([script, src, dst])
```

### 4.2 Import it so the registry can see it

**`dita_etl/stages/extractors/__init__.py`**
```python
from .base import FileExtractor
from .md_pandoc import MdPandocExtractor
from .html_pandoc import HtmlPandocExtractor
from .docx_pandoc import DocxPandocExtractor
from .docx_oxygen import DocxOxygenExtractor          # if present
from .pages_oxygen import PagesOxygenExtractor        # <-- add this

__all__ = [
    "FileExtractor",
    "MdPandocExtractor",
    "HtmlPandocExtractor",
    "DocxPandocExtractor",
    "DocxOxygenExtractor",
    "PagesOxygenExtractor",
]
```

> The `ExtractStage` auto-builds the registry from imported classes and applies `handler_overrides` if provided.

### 4.3 Route extensions via config

```yaml
extract:
  handler_overrides:
    ".pages": "oxygen-pages"
```



## 5) What to change in `ExtractStage` (only if needed)

You generally **don’t** need to touch `ExtractStage`. If you must, there are two common tweaks:

- **Expose `max_workers` via config** (already supported):
  ```python
  ExtractStage(..., max_workers=cfg.extract.get("max_workers"))
  ```
- **Add default handlers** to the registry build if you want them *without* overrides. For example, prefer Oxygen for `.docx` by default:
  ```python
  handlers = [
      MdPandocExtractor(self.pandoc_path),
      HtmlPandocExtractor(self.pandoc_path),
      DocxOxygenExtractor(self.oxygen_scripts_dir),  # prefer Oxygen
      DocxPandocExtractor(self.pandoc_path),         # keep fallback
  ]
  ```



## 6) Tests (do not skip this)

### 6.1 Unit test the extractor args

**`tests/test_extractors.py`** already includes patterns like:

```python
def _assert_common_pandoc_shape(call, reader, src, dst):
    assert call[0].endswith("pandoc")
    assert call[1] == "-f" and call[2] == reader
    assert call[3] == "-t" and call[4] == "docbook"
    assert call[-3] == src and call[-2] == "-o" and call[-1] == dst
```

Add a test for your new extractor (e.g., Oxygen):

```python
def test_pages_oxygen_args(tmp_path, monkeypatch):
    from dita_etl.stages.extractors.pages_oxygen import PagesOxygenExtractor
    from dita_etl.runners import SubprocessRunner

    class DummyRunner(SubprocessRunner):
        def __init__(self): self.calls=[]
        def run(self, args): self.calls.append(args); Path(args[-1]).parent.mkdir(parents=True, exist_ok=True); Path(args[-1]).write_text("<docbook/>")

    runner = DummyRunner()
    ext = PagesOxygenExtractor(oxygen_scripts_dir="/opt/oxygen/scripts")
    src = str(tmp_path / "x.pages"); dst = str(tmp_path / "out.xml")
    Path(src).write_text("stub", encoding="utf-8")

    ext.extract(src, dst, runner)

    call = runner.calls[0]
    assert "/opt/oxygen/scripts/pages2docbook.sh" in call[0]
    assert call[-3] == src and call[-1] == dst
    assert Path(dst).exists()
```

### 6.2 Registry routing & overrides

Use/extend the existing `test_pipeline.py`:
- Verify `.pages` routes to `oxygen-pages` when set in `handler_overrides`.
- Ensure per-file failures are captured but don’t abort the entire run.

Run:
```bash
pytest -q
```



## 7) Operational checklist

- **Determinism:** fixed CLI args, no time-based output, same inputs → same DocBook.
- **Immutability:** never mutate sources; always fully write `dst`.
- **Graceful failure:** raise a clear `SubprocessError` so `ExtractStage` captures it per file and continues.
- **Config-first:** expose all variable aspects (script paths, flags) via `config.yaml`.
- **Docs:** update `README`/design docs with the extractor’s `name`, supported `exts`, and any prerequisites (e.g., Oxygen CLI).
- **Perf:** tune `extract.max_workers` if you see I/O saturation or tool concurrency limits.



## 8) Common pitfalls (and fixes)

- **Relative imports:** extractors live at `dita_etl/stages/extractors/`; import the runner with `from ...runners import SubprocessRunner` (three dots).
- **Registry not seeing your extractor:** make sure it’s imported in `extractors/__init__.py`.
- **Overriding doesn’t work:** the `name` in your extractor must match the string in `handler_overrides` exactly.
- **Silent failures:** if your extractor swallows exceptions or doesn’t raise on non-zero exit codes, `ExtractStage` can’t quarantine properly. Always raise `SubprocessError` (the default `SubprocessRunner` does this for you).



## 9) Quick reference

- Add/modify extractor → `dita_etl/stages/extractors/*.py`
- Register/import → `dita_etl/stages/extractors/__init__.py`
- Route by config → `config/config.yaml` → `extract.handler_overrides`
- Parallelism → `extract.max_workers` or `ExtractStage(max_workers=...)`
- Tests → `tests/test_extractors.py`, `tests/test_pipeline.py`

That’s it. With the registry + overrides in place, changing the “Specify source content” extractor is mostly a **config flip**, and deeper changes are isolated to a single, tiny class.