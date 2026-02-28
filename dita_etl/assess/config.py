"""Assessment-stage configuration dataclasses.

Loaded from ``config/assess.yaml`` once at startup and passed immutably
through the assessment pipeline.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import yaml


@dataclass
class Shingling:
    """MinHash shingling parameters for near-duplicate detection.

    :param stopwords: Optional path to a stopword list (currently unused).
    :param ngram: Size of each shingle (token n-gram window).
    :param minhash_num_perm: Number of permutations for the MinHash signature.
    :param threshold: Jaccard similarity threshold above which two documents
        are considered near-duplicates.
    """

    stopwords: str | None = None
    ngram: int = 7
    minhash_num_perm: int = 64
    threshold: float = 0.88


@dataclass
class ScoringWeights:
    """Weights used by the topicization-readiness and conversion-risk scorers.

    :param topicization_weights: Per-metric additive weights for the readiness
        score (0-100).
    :param risk_weights: Per-metric additive weights for the risk score (0-100).
    """

    topicization_weights: dict[str, int] = field(
        default_factory=lambda: {
            "heading_ladder_valid": 10,
            "avg_section_len_target": 15,
            "tables_simple": 10,
            "lists_depth_ok": 10,
            "images_with_alt": 5,
        }
    )
    risk_weights: dict[str, int] = field(
        default_factory=lambda: {
            "deep_nesting": 20,
            "complex_tables": 25,
            "unresolved_anchors": 15,
            "mixed_inline_blocks": 10,
        }
    )


@dataclass
class Limits:
    """Content length thresholds for scoring.

    :param target_section_tokens: ``[min, max]`` token range for an
        "ideally-sized" section.
    """

    target_section_tokens: list[int] = field(default_factory=lambda: [50, 500])


@dataclass
class Duplication:
    """Near-duplicate handling settings.

    :param prefer_paths: Path prefixes that should be preferred when resolving
        duplicate clusters.
    :param action: What to do with detected duplicates — ``"propose"`` emits
        recommendations; future values may include ``"remove"`` or ``"merge"``.
    """

    prefer_paths: list[str] = field(default_factory=list)
    action: str = "propose"


@dataclass
class AssessConfig:
    """Root configuration object for the assessment stage.

    :param intermediate: Intermediate format name used in reports.
    :param shingling: MinHash shingling parameters.
    :param scoring: Scoring weights for readiness and risk.
    :param classification: Keyword lists used by the topic-type predictor.
    :param duplication: Near-duplicate handling settings.
    :param limits: Content length thresholds.
    """

    intermediate: str = "docbook5"
    shingling: Shingling = field(default_factory=Shingling)
    scoring: ScoringWeights = field(default_factory=ScoringWeights)
    classification: dict[str, list[str]] = field(
        default_factory=lambda: {
            "task_keywords": ["click", "run", "open", "select", "type", "press"],
            "task_landmarks": ["prerequisites", "steps", "results", "troubleshooting"],
            "reference_markers": ["parameters", "options", "syntax", "defaults"],
        }
    )
    duplication: Duplication = field(default_factory=Duplication)
    limits: Limits = field(default_factory=Limits)

    # ------------------------------------------------------------------
    # Factory (imperative shell: file I/O lives only here)
    # ------------------------------------------------------------------

    @staticmethod
    def load(path: str) -> "AssessConfig":
        """Load an assessment configuration from a YAML file.

        :param path: Path to the YAML configuration file.
        :returns: Populated :class:`AssessConfig` instance.
        :raises FileNotFoundError: If *path* does not exist.
        """
        with open(path) as fh:
            data: dict[str, Any] = yaml.safe_load(fh) or {}

        cfg = AssessConfig()
        _nested_types = {
            "shingling": Shingling,
            "scoring": ScoringWeights,
            "limits": Limits,
            "duplication": Duplication,
        }
        for key, value in data.items():
            if key in _nested_types and isinstance(value, dict):
                obj = getattr(cfg, key)
                for sub_key, sub_val in value.items():
                    setattr(obj, sub_key, sub_val)
            else:
                setattr(cfg, key, value)
        return cfg
