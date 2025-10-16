# How the Source Type Is Controlled

| Goal | What to Change | Result |
|------|----------------|--------|
| Run HTML-only | `treat_as_html` in config | Converts all `.htm/.html` to DITA |
| Run Markdown-only | `treat_as_markdown` in config | Converts `.md` to DITA |
| Run mixed sources | Keep both | Handles both at once |
| Switch dynamically | Add CLI flag `--format` | One-liner toggle |

1. In your **`config/config.yaml`**, there’s a key like this:
   ```yaml
   source_formats:
     treat_as_markdown: [".md"]
     treat_as_html: [".html", ".htm"]
     treat_as_docx: [".docx"]
   ```

2. The orchestrator determines which file types to ingest from that section:
   ```python
   for key, vals in getattr(cfg, "source_formats", {}).items():
       if key.startswith("treat_as_"):
           for v in vals:
               if isinstance(v, str) and v.startswith("."):
                   exts.append(v)
   ```

3. The **extract stage** automatically routes `.md`, `.html`, and `.docx` through their respective extractors:
   - `MdPandocExtractor`
   - `HtmlPandocExtractor`
   - `DocxPandocExtractor`


## To Switch Input Type

You just modify your config YAML (or have multiple configs):

#### Markdown → HTML
```yaml
source_formats:
  treat_as_html: [".html", ".htm"]
```

#### HTML → Markdown
```yaml
source_formats:
  treat_as_markdown: [".md"]
```

#### DOCX → HTML (mixed input)
```yaml
source_formats:
  treat_as_html: [".html"]
  treat_as_docx: [".docx"]
```

Then rerun:
```bash
python3 scripts/cli.py --config config/config.yaml --input path/to/input
```


### ⚙️ Bonus Tip — Add Bidirectional Conversion

If you want to **convert Markdown ⇄ HTML** with the same system, you can:

- In the `ExtractStage`, enable both extractors:
  ```yaml
  source_formats:
    treat_as_markdown: [".md"]
    treat_as_html: [".html", ".htm"]
  ```
- This will let the system treat both `.md` and `.htm` as valid source types.
- The pipeline normalizes everything into DocBook XML before converting to DITA, so it’s format-agnostic at runtime.


### Advanced Option: Add a Format Switch Parameter

You can even make the CLI dynamic.  
In `cli.py`, add a flag:
```bash
python3 scripts/cli.py --config config/config.yaml --input ./input --format html
```

Then, in `orchestrator.py`:
```python
if args.format == "html":
    cfg.source_formats = {"treat_as_html": [".html", ".htm"]}
elif args.format == "markdown":
    cfg.source_formats = {"treat_as_markdown": [".md"]}
```

That way, you can toggle the mode without editing YAML.