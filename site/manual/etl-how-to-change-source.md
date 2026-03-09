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

2. `Config.source_extensions()` (in `dita_etl/pipeline.py`) reads that section and collects all extensions.

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
dita-etl run --config config/config.yaml --input path/to/input
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

You can toggle the active source type by maintaining separate config files and passing the right one at runtime:

```bash
dita-etl run --config config/html.yaml --input ./input
dita-etl run --config config/markdown.yaml --input ./input
```