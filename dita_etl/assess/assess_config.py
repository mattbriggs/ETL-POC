from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional
import yaml

@dataclass
class Shingling:
    stopwords: Optional[str] = None
    ngram: int = 7
    minhash_num_perm: int = 64
    threshold: float = 0.88

@dataclass
class ScoringWeights:
    topicization_weights: Dict[str, int] = field(default_factory=lambda: {
        "heading_ladder_valid": 10,
        "avg_section_len_target": 15,
        "tables_simple": 10,
        "lists_depth_ok": 10,
        "images_with_alt": 5,
    })
    risk_weights: Dict[str, int] = field(default_factory=lambda: {
        "deep_nesting": 20,
        "complex_tables": 25,
        "unresolved_anchors": 15,
        "mixed_inline_blocks": 10,
    })

@dataclass
class Limits:
    target_section_tokens: List[int] = field(default_factory=lambda: [50, 500])

@dataclass
class Duplication:
    prefer_paths: List[str] = field(default_factory=list)
    action: str = "propose"

@dataclass
class AssessConfig:
    intermediate: str = "docbook5"
    shingling: Shingling = field(default_factory=Shingling)
    scoring: ScoringWeights = field(default_factory=ScoringWeights)
    classification: Dict[str, List[str]] = field(default_factory=lambda: {
        "task_keywords": ["click","run","open","select","type","press"],
        "task_landmarks": ["prerequisites","steps","results","troubleshooting"],
        "reference_markers": ["parameters","options","syntax","defaults"],
    })
    duplication: Duplication = field(default_factory=Duplication)
    limits: Limits = field(default_factory=Limits)

    @staticmethod
    def load(path: str) -> "AssessConfig":
        with open(path, "r") as f:
            data = yaml.safe_load(f) or {}
        cfg = AssessConfig()
        # shallow/deep-ish merge
        for k, v in data.items():
            if hasattr(cfg, k) and isinstance(getattr(cfg, k), (Shingling, ScoringWeights, Limits, Duplication)):
                obj = getattr(cfg, k)
                for kk, vv in v.items():
                    setattr(obj, kk, vv)
            else:
                setattr(cfg, k, v)
        return cfg