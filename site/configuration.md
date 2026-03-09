# Configuration

## `config/config.yaml` — main pipeline config

```yaml
# External tool paths
tooling:
  pandoc_path: /usr/local/bin/pandoc       # required
  oxygen_scripts_dir: null                 # optional (Oxygen extractor)
  java_path: /usr/bin/java                 # optional (XSLT via Saxon)
  saxon_jar: /opt/saxon/saxon9he.jar       # optional

# Source file extensions to discover
source_formats:
  treat_as_markdown: [".md"]
  treat_as_html:     [".html", ".htm"]
  treat_as_docx:     [".docx"]

# DITA output settings
dita_output:
  output_folder: build/out
  map_title: "My Documentation Set"
  dita_version: "1.3"

# Extraction settings
extract:
  max_workers: 4             # parallel threads; null = auto (CPUs × 2)
  handler_overrides:
    ".docx": "oxygen-docx"  # override default Pandoc extractor for .docx

# Topic-type classification rules (evaluated in order, highest priority first)
classification_rules:
  by_filename:
    - match: "guide"
      type: "task"
    - match: "index"
      type: "concept"
    - match: "*reference*"
      type: "reference"
  by_content:
    - match: "procedure"
      type: "task"
    - match: "parameters"
      type: "reference"
```

### Strict validation

The config loader rejects unknown keys at every level and raises `ValueError`
with the offending key names. This prevents silent misconfiguration from
typos.

### Classification rule matching

`by_filename` patterns are matched against the **file stem** (without
extension) using `fnmatch` glob syntax. `"index"` matches `index.md` and
`index.html`; `"*reference*"` matches `api_reference.md`.

`by_content` patterns are matched as case-insensitive regex against the full
intermediate DocBook text.

### Classification priority

All five sources are evaluated in order; the first match wins:

1. `by_filename` config rules
2. `by_content` config rules
3. Assess-stage plan hint (`default_topic_type` from `plans/*.conversion_plan.json`)
4. Built-in heuristics (keyword density)
5. Default → `concept`

---

## `config/assess.yaml` — assessment config

```yaml
# Near-duplicate detection (MinHash)
shingling:
  ngram: 7                  # token n-gram window
  minhash_num_perm: 64      # MinHash permutations
  threshold: 0.88           # Jaccard similarity threshold

# Topicization-readiness scoring weights (sum → 0-100)
scoring:
  topicization_weights:
    heading_ladder_valid: 10
    avg_section_len_target: 15
    tables_simple: 10
    lists_depth_ok: 10
    images_with_alt: 5
  # Conversion-risk scoring weights (sum → 0-100)
  risk_weights:
    deep_nesting: 20
    complex_tables: 25
    unresolved_anchors: 15
    mixed_inline_blocks: 10

# Classification keyword lists
classification:
  task_keywords: ["click", "run", "open", "select", "type", "press"]
  task_landmarks: ["prerequisites", "steps", "results", "troubleshooting"]
  reference_markers: ["parameters", "options", "syntax", "defaults"]

# Near-duplicate handling
duplication:
  prefer_paths: []            # path prefixes to prefer when resolving
  action: "propose"           # "propose" | future: "remove" | "merge"

# Ideal section token range for readiness scoring
limits:
  target_section_tokens: [50, 500]
```

---

## Environment variables

No environment variables are required. All configuration is file-based.
Paths in YAML files may be absolute or relative to the working directory.
