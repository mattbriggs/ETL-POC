# What “complex” means in DITA terms

Complex tables remain the hardest element to carry through a doc → DITA pipeline. The current implementation can preserve some structures—especially if extraction retains DocBook CALS (from DOCX or HTML)—but only with a robust DocBook→DITA CALS mapping step. Right now, the assessment logic is too coarse and the transform XSL is still a placeholder. Without those upgrades, truly “complex” cases—multi-row headers, row and column spans, stubs, footnotes, wide cells, or nested tables—will be degraded or fail outright. The path forward is clear: strengthen extraction fidelity, add a normalizer, and implement a proper CALS mapping. That combination will allow the pipeline to handle complex tables consistently and predictably.

DITA 1.3 supports two table models:
- **`simpletable`**: no spans, no multi-row headers—keep it for trivial cases.
- **CALS `table`**: `tgroup`/`colspec`/`thead`/`tbody`/`row`/`entry` with `@namest/@nameend` (colspans) and `@morerows` (rowspans), captions, stubs, entry content (lists, images), and attributes like `@frame`, `@colsep`, `@rowsep`.

**Unsupported or problematic in DITA**:
- Nested tables inside cells (must be flattened/split).
- Arbitrary CSS layout tables (need normalization).
- Semantically ambiguous HTML (headers without a clear scope).



# Best-practice approach for complex tables

## 1) Preserve structure at extraction (non-negotiable)
- **DOCX**: Prefer **Oxygen** (or a DOCX→DocBook converter that emits CALS) over stock Pandoc. Pandoc is good, but DOCX vertical merges/complex headers can degrade.
- **HTML**: Route HTML with `<thead>/<tbody>/<th rowspan|colspan>` through **Pandoc → DocBook** (keeps CALS reasonably well) or direct XSLT HTML→DITA.
- **Markdown**: GFM pipe tables don’t support row/col spans. If authors embedded HTML tables, treat as HTML. Otherwise, expect **simpletable** only.

**Action in your repo**  
Use the new extractor registry to **route formats**:
- `.docx` → `oxygen-docx` (preferred)  
- `.html/.htm` → `pandoc-html`  
- `.md` → `pandoc-md` (but only simple tables unless inline HTML)

Config:
```yaml
extract:
  handler_overrides:
    ".docx": "oxygen-docx"
```

## 2) Normalize tables in the intermediate
Add a **TableNormalizer.xsl** that runs **before** DocBook→DITA:
- Promote captions/notes to a consistent place.
- Split nested tables (convert nested to a sibling table with a cross-reference or list + table).
- Ensure all headers reside in `thead` with proper `scope`.
- Generate/repair `colspec` and fill in `@namest/@nameend` and `@morerows`.
- Collapse CSS/HTML niceties to CALS semantics.

Wire it:  
`DocBook.xml --(TableNormalizer.xsl)--> DocBook[Tidy].xml --(DocBook2DITA.xsl)--> DITA`

## 3) Map CALS → DITA CALS precisely
Replace the placeholder transform with a **CALS-preserving** XSLT:
- For each `table`:
  - Copy `tgroup/@cols`, `colspec/@colname/@colnum`.
  - Map `thead/tbody/tfoot`.
  - For each `entry`, preserve inline content and apply `@namest/@nameend` and `@morerows`.
  - Convert footnotes to DITA footnote markup (or note + xref).
  - Carry over `@frame/@rowsep/@colsep` where meaningful.
- Detect “simple” tables (no spans, no thead, no complex entry content) and downshift to `simpletable` for cleaner output.

## 4) Lossy cases: decide & document
- **Nested tables**: split into (para + second table) and add an `xref`/`note` telling the reader this was originally nested.
- **Heavily styled layout tables**: convert to **conceptual content** (sections/lists) + a simple summary table, or keep as CALS with a warning.
- **Column groups with ambiguous headers**: duplicate header text into cells and set `@scope` to avoid reader confusion.



# Can your current ETL handle this today?

**Extraction**
- Markdown: ✅ simple tables (pipe). ❌ complex spans unless HTML is embedded.
- HTML: ✅ row/col spans, multi-header rows are usually preserved by Pandoc.
- DOCX: ⚠️ Pandoc may flatten vertical merges; **use Oxygen** for better CALS fidelity.

**Transform**
- Current XSL is a placeholder: ❌ won’t reliably emit valid **CALS** with spans. Needs the mapping above.

**Assessment**
- Today you flag “complex_tables” if there’s >1 table—too crude. You need **feature detection**:
  - Count `rowspan/colspan`, number of header rows, presence of nested tables, cell block elements (lists, images), footnotes.
  - Score risk based on these signals and annotate a **table plan** (e.g., “downgrade to simpletable”, “split nested tables”, “requires Oxygen route”).

**Bottom line**: With **Oxygen extraction for DOCX**, **HTML/Pandoc kept**, and adding **TableNormalizer + CALS XSL**, yes—you can handle complex tables with high fidelity. Without those changes, expect loss or failures on real-world complex tables.



# Concrete changes to make (small, targeted)

1) **Extractor routing (already supported)**
   - Set `.docx → oxygen-docx` in `config.yaml`.

2) **Add a table-aware assessment**
   - In `assess/features.py`, when the section contains `<table>`, compute:
     - `has_rowspan`, `has_colspan`, `header_rows`, `nested_tables`, `cells_with_blocks`, `footnotes`.
   - In `assess/scoring.py`, bump `conversion_risk` with weights for those features.
   - Emit a **`tables`** array per file in `inventory.json` with per-table metrics.

3) **Add `xsl/TableNormalizer.xsl`**
   - Normalize DocBook tables as above.

4) **Replace `xsl/docbook2dita.xsl` with CALS mapping**
   - Preserve CALS structure; downshift to `simpletable` where safe.

5) **Tests (goldens)**
   - Fixtures:
     - HTML with multi-row headers, col/row spans, footnotes.
     - DOCX with vertical merges and captions.
     - Markdown with embedded HTML complex table.
   - Golden DITA verifying:
     - `@namest/@nameend/@morerows` correct.
     - Header scopes, captions preserved.
     - Nested tables converted per policy.



# Decision tree (cheap and effective)

- **DOCX**  
  → Oxygen extraction  
  → Normalizer XSL  
  → CALS mapping XSL  
  → **DITA CALS**

- **HTML with spans**  
  → Pandoc DocBook  
  → Normalizer XSL  
  → CALS mapping XSL  
  → **DITA CALS**

- **Markdown pipe table (no spans)**  
  → Pandoc DocBook  
  → Downshift to **simpletable**

- **Markdown with embedded `<table>`**  
  → Treat as HTML case above.

- **Nested tables anywhere**  
  → Split; emit secondary table with note/xref.



# Risks & mitigations

- **Lossy DOCX vertical merges with Pandoc** → Route to Oxygen.
- **Authoring variability** (CSS-styled headers) → Normalizer that promotes headers into `thead` and assigns `scope`.
- **Invalid output** → Add Schematron/XSD validation step post-transform; quarantine bad topics and keep the run going.



# What I’d add to your repo (minimal PR)

- `xsl/TableNormalizer.xsl` (HTML & DocBook modes).
- A real `xsl/DocBook2DITA-CALS.xsl`.
- Assessment table probes + risk tuning.
- 3–4 table fixtures + golden DITA.
- A config switch `tables.nested_policy: split|inline-note|fail` and `tables.downshift_simple: true`.

If you want, I can sketch the XSLT skeletons for the normalizer and the CALS mapper so you can slot them in next.