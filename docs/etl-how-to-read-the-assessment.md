# How To: Configure and Read the ETL Assessment

This guide explains how to configure and interpret the **Assessment Stage (Stage 0)** in the ETL pipeline. The goal of this stage is to help you **understand the structure, quality, and duplication risks** in your source documents *before* they are converted into DITA XML.

The assessment is designed for support staff and engineers working with Component Content Management Systems (CCMS) who need to improve the reliability and semantic value of their content migration.

## 1. What the Assessment Does

The Assessment Stage scans your source documents (Markdown, HTML, DOCX, etc.) and produces:

- **`inventory.json`** — machine-readable metrics for every file.
- **`dedupe_map.json`** — clusters of duplicate and near-duplicate documents.
- **`plans/*.conversion_plan.json`** — per-file guidance for how to chunk content and classify topics.
- **`report.html`** — a human-readable dashboard that summarizes risk and readiness.

This gives you an **evidence-based preview** of conversion complexity and identifies documents that require cleanup or deduplication before automated conversion to DITA.

## 2. Configuring the Assessment

The assessment uses a YAML configuration file: `config/assess.yaml`.

Key sections you can adjust:

### Shingling and Duplicate Detection

```yaml
shingling:
  ngram: 7                 # how many tokens per shingle
  minhash_num_perm: 64     # number of hash permutations
  threshold: 0.88          # similarity threshold (0-1) for near duplicates
```
- Lower the `threshold` to detect looser matches (more aggressive dedupe).
- Increase `ngram` for stricter text chunking.

### Scoring Weights

```yaml
scoring:
  topicization_weights:
    heading_ladder_valid: 10
    avg_section_len_target: 15
    tables_simple: 10
    lists_depth_ok: 10
    images_with_alt: 5
  risk_weights:
    deep_nesting: 20
    complex_tables: 25
    unresolved_anchors: 15
    mixed_inline_blocks: 10
```
- Adjust weights to reflect what matters most in your content (e.g., penalize complex tables more heavily if your downstream XSLT struggles with them).

### Classification Rules
```yaml
classification:
  task_keywords: ["click","run","open","select","type","press"]
  task_landmarks: ["prerequisites","steps","results","troubleshooting"]
  reference_markers: ["parameters","options","syntax","defaults"]
```
- Tune keywords so the system better predicts whether a section is a **concept**, **task**, or **reference** topic.

### Limits

```yaml
limits:
  target_section_tokens: [50, 500]
```
- Defines the "ideal" section size for DITA topics. Shorter or longer sections reduce the readiness score.

---

## 3. Running the Assessment

Run the pipeline normally:

```bash
python scripts/cli.py --config config/config.yaml --input /path/to/source
```

The assessment will run as Stage 0, producing artifacts under:

```
build/assess/
  ├── inventory.json
  ├── dedupe_map.json
  ├── report.html
  └── plans/
      ├── file1.md.conversion_plan.json
      ├── file2.docx.conversion_plan.json
      ...
```

## 4. Reading the Output

### Report (report.html)

Open `build/assess/report.html` in a browser. It shows:

- **File list** with size, section count, readiness score, and risk score.
- **Duplicate clusters** listing files that are exact or near-duplicates.

Use this as your first stop for a quick overview.

### Inventory (inventory.json)

This JSON contains detailed metrics per file:
- `size` (bytes), `sections` (count), `sha256` (fingerprint).
- `topicization_readiness` (0-100): higher means easier to split into DITA topics.
- `conversion_risk` (0-100): higher means more structural problems (deep nesting, complex tables, etc.).
- `predictions`: per-section suggested type (concept, task, reference).

This is useful for automation or dashboards.

### Duplicate Map (dedupe_map.json)
Lists clusters of files that are highly similar. Each cluster is an array of file paths. Use this to:
- Remove redundant files before conversion.
- Decide which copy is canonical.

### Conversion Plans (plans/*.conversion_plan.json)
Each file gets a plan with:
- `chunking`: rules for splitting into topics (e.g., split at H1 headings).
- `default_topic_type`: predicted type if no per-section classification is applied.
- `sections`: predictions for each section, with confidence scores and reasons.

You can feed these into the transformation stage to influence DITA output.

## 5. Using Assessment Results to Improve ETL

1. **Deduplication** — Quarantine duplicates before feeding into Extract/Transform. This avoids wasted effort and redundant topics in DITA.
2. **Chunking Strategy** — Adjust conversion rules based on readiness scores. Poor scores often mean inconsistent heading usage; fix these in the source.
3. **Classification Tuning** — Update `assess.yaml` classification rules when predictions don't match your authoring model.
4. **Prioritization** — High-risk files should be reviewed manually before conversion; low-risk files can be converted automatically.

## 6. Best Practices

- **Iterate configs**: Adjust weights and rules in `assess.yaml` as you learn what patterns your corpus has.
- **Version configs**: Keep `assess.yaml` in version control alongside the content model so assessments are reproducible.
- **Review `report.html` regularly**: It's your early-warning system for bad inputs.
- **Automate quarantine**: Integrate duplicate clusters and high-risk flags into your pipeline to automatically skip or isolate problematic files.

