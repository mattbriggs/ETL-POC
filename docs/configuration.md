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

# Override which extractor handles an extension
extract:
  handler_overrides:
    ".docx": "oxygen-docx"       # optional

# Topic-type classification rules (evaluated in order)
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

## Environment variables

No environment variables are required. All configuration is file-based.
Paths in YAML files may be absolute or relative to the working directory.
