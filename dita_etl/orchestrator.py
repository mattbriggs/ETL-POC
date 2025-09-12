
from __future__ import annotations
import os, glob
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict
from prefect import flow, task
from .config import Config
from .stages.extract import ExtractStage
from .stages.transform import TransformStage
from .stages.load import LoadStage
from .runners import SubprocessRunner

@task
def list_inputs(input_dir: str, exts: List[str]) -> List[str]:
    files = []
    for ext in exts:
        files.extend(glob.glob(os.path.join(input_dir, f"*{ext}")))
    return sorted(files)

@task
def run_extract(cfg: Config, inputs: List[str]) -> Dict[str, str]:
    stg = ExtractStage(cfg.tooling.pandoc_path, cfg.tooling.oxygen_scripts_dir, intermediate_dir="build/intermediate", runner=SubprocessRunner())
    res = stg.run(inputs=inputs)
    return res.data["outputs"]

@task
def run_transform(cfg: Config, intermediates: Dict[str, str]) -> Dict[str, List[str]]:
    stg = TransformStage(cfg.tooling.java_path, cfg.tooling.saxonn_jar if hasattr(cfg.tooling,'saxonn_jar') else cfg.tooling.saxon_jar,
                         xsl_path="xsl/docbook2dita.xsl",
                         output_dir=cfg.dita_output.output_folder,
                         rules_by_filename=cfg.classification_rules.get("by_filename", []),
                         rules_by_content=cfg.classification_rules.get("by_content", []))
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
    # Determine extensions from config or default
    exts = []
    for key, vals in cfg.source_formats.items():
        if key.startswith("treat_as_"):
            for v in vals:
                if v.startswith("."):
                    exts.append(v)
    if not exts:
        exts = [".md", ".docx", ".html"]
    inputs = list_inputs(input_dir, exts)
    interm = run_extract(cfg, inputs)
    topics = run_transform(cfg, interm)
    map_path = run_load(cfg, topics)
    return map_path
