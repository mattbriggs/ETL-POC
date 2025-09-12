
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict, Optional
import yaml, os

@dataclass
class ClassificationRule:
    pattern: str
    topic_type: str  # 'concept'|'task'|'reference'

@dataclass
class Chunking:
    level: int = 1
    nested_topics: bool = True

@dataclass
class DITAOutput:
    dita_version: str = "1.3"
    use_specialization: bool = False
    output_folder: str = "out/dita"
    map_title: str = "Documentation Set"

@dataclass
class Tooling:
    pandoc_path: str = "pandoc"
    oxygen_scripts_dir: Optional[str] = None  # e.g., /Applications/Oxygen XML Editor/tools/scripts
    saxon_jar: str = "saxon-he.jar"
    java_path: str = "java"

@dataclass
class Config:
    source_formats: Dict[str, list] = field(default_factory=lambda: {"treat_as_markdown": [".md"]})
    classification_rules: Dict[str, List[ClassificationRule]] = field(default_factory=dict)
    chunking: Chunking = field(default_factory=Chunking)
    dita_output: DITAOutput = field(default_factory=DITAOutput)
    tooling: Tooling = field(default_factory=Tooling)

    @staticmethod
    def load(path: str) -> "Config":
        with open(path, "r") as f:
            data = yaml.safe_load(f) or {}
        def rules(lst):
            return [ClassificationRule(**r) for r in (lst or [])]
        cr = {
            "by_filename": rules(data.get("classification_rules", {}).get("by_filename")),
            "by_content": rules(data.get("classification_rules", {}).get("by_content")),
        }
        chunk = Chunking(**(data.get("chunking") or {}))
        out = DITAOutput(**(data.get("dita_output") or {}))
        tool = Tooling(**(data.get("tooling") or {}))
        return Config(
            source_formats=data.get("source_formats") or {},
            classification_rules=cr,
            chunking=chunk,
            dita_output=out,
            tooling=tool,
        )
