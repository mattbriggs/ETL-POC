"""Pipeline orchestrator — imperative shell.

:func:`run_pipeline` is the single entry point that composes the four
pipeline stages in order.  It is the only module that:

* performs filesystem setup (creating output directories),
* constructs stage instances from configuration,
* emits structured log messages at stage boundaries,
* propagates typed contracts between stages.

Pure transformation logic lives in ``dita_etl.transforms``;
I/O primitives live in ``dita_etl.io``.
"""

from __future__ import annotations

from dita_etl.config import Config
from dita_etl.contracts import (
    AssessInput,
    ExtractInput,
    LoadInput,
    PipelineOutput,
    TransformInput,
)
from dita_etl.io.filesystem import discover_files, ensure_dir
from dita_etl.logging_config import get_logger
from dita_etl.stages.assess import AssessStage
from dita_etl.stages.extract import ExtractStage
from dita_etl.stages.load import LoadStage
from dita_etl.stages.transform import TransformStage

_LOG = get_logger("pipeline")


def run_pipeline(
    config_path: str = "config/config.yaml",
    assess_config_path: str = "config/assess.yaml",
    input_dir: str = "sample_data/input",
) -> PipelineOutput:
    """Run the full ETL pipeline: Assess → Extract → Transform → Load.

    :param config_path: Path to the main pipeline YAML configuration file.
    :param assess_config_path: Path to the assessment YAML configuration file.
    :param input_dir: Root directory containing source documents.
    :returns: :class:`~dita_etl.contracts.PipelineOutput` with the results
        of all four stages.
    :raises FileNotFoundError: If *config_path* or *input_dir* does not exist.

    :Example:

    .. code-block:: python

        result = run_pipeline(
            config_path="config/config.yaml",
            assess_config_path="config/assess.yaml",
            input_dir="docs/",
        )
        print(f"Map written to: {result.map_path}")
    """
    cfg = Config.load(config_path)
    output_root = cfg.dita_output.output_folder
    ensure_dir(output_root)

    extensions = cfg.source_extensions()
    source_paths = discover_files(input_dir, extensions)

    _LOG.info("Pipeline starting", extra={"input_dir": input_dir, "files": len(source_paths)})

    # ------------------------------------------------------------------ #
    # Stage 0: Assess
    # ------------------------------------------------------------------ #
    assess_dir = f"{output_root}/assess"
    ensure_dir(assess_dir)

    assess_stage = AssessStage(config_path=assess_config_path)
    assess_input = AssessInput(
        source_paths=tuple(source_paths),
        output_dir=assess_dir,
        config_path=assess_config_path,
    )
    assess_output = assess_stage.run(assess_input)
    _LOG.info("Assess complete", extra={"report": assess_output.report_path})

    # ------------------------------------------------------------------ #
    # Stage 1: Extract
    # ------------------------------------------------------------------ #
    intermediate_dir = f"{output_root}/intermediate"

    extract_stage = ExtractStage(
        pandoc_path=cfg.tooling.pandoc_path,
        oxygen_scripts_dir=cfg.tooling.oxygen_scripts_dir,
    )
    extract_input = ExtractInput(
        source_paths=tuple(source_paths),
        intermediate_dir=intermediate_dir,
        handler_overrides=cfg.extract.handler_overrides,
        max_workers=cfg.extract.max_workers,
    )
    extract_output = extract_stage.run(extract_input)
    _LOG.info(
        "Extract complete",
        extra={
            "succeeded": len(extract_output.outputs),
            "failed": len(extract_output.errors),
        },
    )

    # ------------------------------------------------------------------ #
    # Stage 2: Transform
    # ------------------------------------------------------------------ #
    topics_dir = f"{output_root}/dita/topics"
    ensure_dir(topics_dir)

    transform_stage = TransformStage()
    transform_input = TransformInput(
        intermediates=extract_output.outputs,
        output_dir=topics_dir,
        rules_by_filename=tuple(cfg.classification_rules.get("by_filename", [])),
        rules_by_content=tuple(cfg.classification_rules.get("by_content", [])),
    )
    transform_output = transform_stage.run(transform_input)
    _LOG.info(
        "Transform complete",
        extra={
            "topics": sum(len(v) for v in transform_output.topics.values()),
            "failed": len(transform_output.errors),
        },
    )

    # ------------------------------------------------------------------ #
    # Stage 3: Load
    # ------------------------------------------------------------------ #
    dita_dir = f"{output_root}/dita"

    load_stage = LoadStage()
    load_input = LoadInput(
        topics=transform_output.topics,
        output_dir=dita_dir,
        map_title=cfg.dita_output.map_title,
        intermediate_dir=intermediate_dir,
    )
    load_output = load_stage.run(load_input)
    _LOG.info("Load complete", extra={"map": load_output.map_path})

    return PipelineOutput(
        assess=assess_output,
        extract=extract_output,
        transform=transform_output,
        load=load_output,
    )
