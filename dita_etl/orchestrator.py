from __future__ import annotations
import os, glob
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
    Discover files recursively that match any of the configured extensions.
    """
    files: List[str] = []
    patts = [f"**/*{ext}" for ext in exts]
    for patt in patts:
        files.extend(glob.glob(os.path.join(input_dir, patt), recursive=True))
    # Only files, stable order
    files = sorted([p for p in files if os.path.isfile(p)])
    return files


@task
def run_assessment(config_path: str, input_dir: str) -> dict:
    """
    Stage 0: Inventory & Assessment -- emits build/assess/{inventory.json, report.html, ...}
    """
    logger = get_run_logger()
    acfg = AssessConfig.load(config_path)

    # Recurse for anything under input_dir
    files = [p for p in glob.glob(os.path.join(input_dir, "**/*"), recursive=True) if os.path.isfile(p)]

    # Absolute output dir avoids CWD surprises
    out_dir = os.path.abspath(os.path.join(os.getcwd(), "build", "assess"))
    os.makedirs(out_dir, exist_ok=True)

    results = assess_run(files, acfg, out_dir=out_dir)
    logger.info(f"Assessment artifacts written: {results}")
    # Typical: results['report'] == {abs}/build/assess/report.html
    return results


@task
def run_extract(cfg: Config, inputs: List[str]) -> Dict[str, str]:
    stg = ExtractStage(
        cfg.tooling.pandoc_path,
        cfg.tooling.oxygen_scripts_dir,
        intermediate_dir="build/intermediate",
        runner=SubprocessRunner(),
    )
    res = stg.run(inputs=inputs)
    return res.data["outputs"]


@task
def run_transform(cfg: Config, intermediates: Dict[str, str]) -> Dict[str, List[str]]:
    # tolerate either cfg.tooling.saxon_jar or legacy cfg.tooling.saxonn_jar
    saxon_jar = getattr(cfg.tooling, "saxon_jar", None) or getattr(cfg.tooling, "saxonn_jar", None)

    stg = TransformStage(
        cfg.tooling.java_path,
        saxon_jar,
        xsl_path="xsl/docbook2dita.xsl",
        output_dir=cfg.dita_output.output_folder,
        rules_by_filename=cfg.classification_rules.get("by_filename", []),
        rules_by_content=cfg.classification_rules.get("by_content", []),
    )
    res = stg.run(intermediates=intermediates)
    return res.data["outputs"]


@task
def run_load(cfg: Config, topics: Dict[str, List[str]]) -> str:
    stg = LoadStage(output_dir=cfg.dita_output.output_folder, map_title=cfg.dita_output.map_title)
    res = stg.run(topics=topics)
    return res.data["map"]


@flow(name="DITA ETL Pipeline")
def build_flow(config_path: str = "config/config.yaml", input_dir: str = "sample_data/input"):
    cfg = Config.load(config_path)

    # ---- Stage 0: Assessment (runs before anything else) ----
    _ = run_assessment(config_path="config/assess.yaml", input_dir=input_dir)

    # Determine extensions from config or default
    exts: List[str] = []
    for key, vals in getattr(cfg, "source_formats", {}).items():
        if key.startswith("treat_as_"):
            for v in vals:
                if isinstance(v, str) and v.startswith("."):
                    exts.append(v)
    if not exts:
        exts = [".md", ".docx", ".html"]

    inputs = list_inputs(input_dir, exts)
    interm = run_extract(cfg, inputs)
    topics = run_transform(cfg, interm)
    map_path = run_load(cfg, topics)
    return map_path