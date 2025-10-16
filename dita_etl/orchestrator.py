from __future__ import annotations
import os
import glob
from typing import List, Dict
from prefect import flow, task, get_run_logger

from .config import Config
from .stages.extract import ExtractStage
from .stages.transform import TransformStage
from .stages.load import LoadStage
from .runners import SubprocessRunner

# ---- Stage 0 (Assessment) imports ----
from .assess.assess_config import AssessConfig
from .assess.inventory import assess_batch as assess_run


@task
def list_inputs(input_dir: str, exts: List[str]) -> List[str]:
    """
    Discover all files recursively that match any of the configured extensions.
    """
    files: List[str] = []
    patterns = [f"**/*{ext}" for ext in exts]
    for pattern in patterns:
        files.extend(glob.glob(os.path.join(input_dir, pattern), recursive=True))

    files = sorted([p for p in files if os.path.isfile(p)])
    return files


@task
def run_assessment(config_path: str, input_dir: str, output_root: str) -> dict:
    """
    Stage 0: Inventory & Assessment — emits assess/{inventory.json, report.html, ...}
    """
    logger = get_run_logger()
    acfg = AssessConfig.load(config_path)

    files = [
        p for p in glob.glob(os.path.join(input_dir, "**/*"), recursive=True)
        if os.path.isfile(p)
    ]

    assess_dir = os.path.join(output_root, "assess")
    os.makedirs(assess_dir, exist_ok=True)

    results = assess_run(files, acfg, out_dir=assess_dir)
    logger.info(f"Assessment artifacts written to: {assess_dir}")
    return results


@task
def run_extract(cfg: Config, inputs: list[str]) -> dict[str, str]:
    """
    Stage 1: Extract — converts source files into canonical intermediate XML (DocBook/HTML5).
    """
    intermediate_dir = os.path.join(cfg.dita_output.output_folder, "intermediate")
    os.makedirs(intermediate_dir, exist_ok=True)

    stage = ExtractStage(
        cfg.tooling.pandoc_path,
        cfg.tooling.oxygen_scripts_dir,
        intermediate_dir=intermediate_dir,
        runner=SubprocessRunner(),
    )
    result = stage.run(inputs=inputs)
    return result.data["outputs"]


@task
def run_transform(cfg: Config, intermediates: Dict[str, str]) -> Dict[str, List[str]]:
    """
    Stage 2: Transform — converts intermediate XML into DITA topics.
    """
    saxon_jar = getattr(cfg.tooling, "saxon_jar", None) or getattr(
        cfg.tooling, "saxonn_jar", None
    )

    transform_dir = os.path.join(cfg.dita_output.output_folder, "dita", "topics")
    os.makedirs(transform_dir, exist_ok=True)

    stage = TransformStage(
        cfg.tooling.java_path,
        saxon_jar,
        xsl_path="xsl/docbook2dita.xsl",
        output_dir=transform_dir,
        rules_by_filename=cfg.classification_rules.get("by_filename", []),
        rules_by_content=cfg.classification_rules.get("by_content", []),
    )
    result = stage.run(intermediates=intermediates)
    return result.data["outputs"]


@task
def run_load(cfg: Config, topics: Dict[str, List[str]]) -> str:
    """
    Stage 3: Load — assembles DITA topics into a map and ensures assets are copied.
    """
    load_dir = os.path.join(cfg.dita_output.output_folder, "dita")
    os.makedirs(load_dir, exist_ok=True)

    stage = LoadStage(output_dir=load_dir, map_title=cfg.dita_output.map_title)
    result = stage.run(topics=topics)
    return result.data["map"]


@flow(name="DITA ETL Pipeline")
def build_flow(
    config_path: str = "config/config.yaml",
    input_dir: str = "sample_data/input",
) -> str:
    """
    Orchestrates all ETL stages (Assess → Extract → Transform → Load).
    """
    cfg = Config.load(config_path)
    output_root = cfg.dita_output.output_folder

    # ---- Stage 0: Assessment ----
    _ = run_assessment(config_path="config/assess.yaml", input_dir=input_dir, output_root=output_root)

    # Determine extensions from config or defaults
    exts: List[str] = []
    for key, vals in getattr(cfg, "source_formats", {}).items():
        if key.startswith("treat_as_"):
            for v in vals:
                if isinstance(v, str) and v.startswith("."):
                    exts.append(v)
    if not exts:
        exts = [".md", ".docx", ".html"]

    # ---- Stage 1: Extract ----
    inputs = list_inputs(input_dir, exts)
    intermediates = run_extract(cfg, inputs)

    # ---- Stage 2: Transform ----
    topics = run_transform(cfg, intermediates)

    # ---- Stage 3: Load ----
    map_path = run_load(cfg, topics)

    return map_path