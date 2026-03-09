# Development of the ETL Process

This document outlines the roadmap for evolving the ETL pipeline from the current starter implementation into a complete, production-grade solution for transforming unstructured and mixed content into structured DITA XML.

## Phase 1: Foundation (Current State)

- **Assessment Module**  
  - Supports Markdown parsing, basic sectionization, duplicate detection, and scoring.  
  - Produces `inventory.json`, `dedupe_map.json`, `report.html`, and per-file `conversion_plan.json`.

- **Core ETL Stages**  
  - **Extract**: Pandoc used for Markdown and HTML inputs, producing DocBook intermediates.  
  - **Transform**: Placeholder XSLT pipeline (DocBook -> DITA).  
  - **Load**: Generates a single DITA map referencing output topics.

- **Configuration**  
  - Config-driven via `config.yaml` and `assess.yaml`.  
  - Supports classification rules, chunking, and duplicate detection parameters.

## Phase 2: Broader Format Support

- **Docx and HTML Parsers**  
  - Add format-specific extractors for Microsoft Word (`.docx`) and HTML.  
  - Ensure consistent DocBook/DITA-ready intermediate representations.  
  - Handle embedded media (images, tables, footnotes) gracefully.

- **Apple Pages and Other Formats**  
  - Use Pandoc adapters or Oxygen CLI scenarios for niche formats (e.g., Pages, LaTeX, OPML).  
  - Establish a unified error-handling strategy so failed conversions are quarantined.

## Phase 3: Smarter Transformation

- **Integrate Conversion Plans**  
  - Feed `conversion_plan.json` into the transformation stage.  
  - Honor chunking rules and predicted topic types (concept/task/reference).  
  - Allow overrides via configuration for edge cases.

- **Semantic Enrichment**  
  - Enhance classification with NLP-based heuristics (e.g., imperative detection, glossary recognition).  
  - Add metadata mapping: author, product version, taxonomy terms -> DITA attributes.

## Phase 4: Quality and Monitoring

- **Dashboards**  
  - Build visualization dashboards (e.g., in Streamlit, Grafana, or a CCMS plugin) to track:  
    - Readiness and risk scores over time.  
    - Duplicate clusters.  
    - Progress toward "clean" content suitable for automated conversion.

- **Test Suites**  
  - Golden files for expected ETL output.  
  - Automated regression tests for classification and scoring.

- **Metrics**  
  - Add per-run hashes and provenance records for full reproducibility.  
  - Monitor failed conversions and quarantined files.

## Phase 5: Enterprise Integration

- **CCMS Integration**  
  - Connect pipeline outputs directly into a CCMS repository.  
  - Validate produced DITA topics and maps against custom DTDs and schemas.

- **Scalability**  
  - Run pipeline in parallel (multi-threading and distributed execution).  
  - Containerize (Docker) for portability across environments.

- **Extensibility**  
  - Plug-in architecture for adding new format handlers or classification modules.  
  - Clear contracts between stages to allow swapping components.

## End State: Complete Solution

The complete ETL process will:

- Accept a wide range of input formats (Markdown, HTML, Docx, Pages, LaTeX, OPML, etc.).
- Produce deterministic, config-driven DITA 1.3 topics and maps.
- Provide actionable assessments (`report.html`) for content cleanup prior to conversion.
- Automatically honor conversion plans for chunking and classification.
- Offer dashboards and metrics for continuous monitoring and improvement.
- Integrate cleanly with enterprise CCMS and publishing workflows.

## Next Steps

1. Implement Docx and HTML assessment and extraction.  
2. Wire `conversion_plan.json` into transformation stage logic.  
3. Build prototype dashboard to visualize risk/readiness trends.  
4. Extend test coverage to 100% for assessment and extraction modules.  
5. Prepare CCMS integration pilot.