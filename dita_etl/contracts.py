"""Stage input/output contracts.

All contracts are immutable frozen dataclasses that validate their contents
on construction. They form the type-safe boundaries between pipeline stages,
making implicit assumptions explicit and enabling confident refactoring.

Example usage::

    input_ = ExtractInput(
        source_paths=("docs/guide.md", "docs/ref.html"),
        intermediate_dir="build/intermediate",
    )
    output = extract_stage.run(input_)
    assert output.success
"""

from __future__ import annotations

from dataclasses import dataclass, field


class ContractError(ValueError):
    """Raised when a stage contract is violated at construction time."""


# ---------------------------------------------------------------------------
# Assess stage
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class AssessInput:
    """Input contract for the Assess stage.

    :param source_paths: Absolute or relative paths of all source files to
        assess.
    :param output_dir: Directory where assessment artefacts will be written.
    :param config_path: Path to the assessment YAML configuration file.
    """

    source_paths: tuple[str, ...]
    output_dir: str
    config_path: str

    def __post_init__(self) -> None:
        if not self.source_paths:
            raise ContractError("AssessInput.source_paths must not be empty")
        if not self.output_dir:
            raise ContractError("AssessInput.output_dir must not be empty")
        if not self.config_path:
            raise ContractError("AssessInput.config_path must not be empty")


@dataclass(frozen=True)
class AssessOutput:
    """Output contract for the Assess stage.

    :param inventory_path: Path to the written ``inventory.json`` file.
    :param dedupe_path: Path to the written ``dedupe_map.json`` file.
    :param report_path: Path to the written HTML report file.
    :param plans_dir: Directory containing per-file conversion plan JSONs.
    """

    inventory_path: str
    dedupe_path: str
    report_path: str
    plans_dir: str

    def __post_init__(self) -> None:
        if not self.inventory_path:
            raise ContractError("AssessOutput.inventory_path must not be empty")


# ---------------------------------------------------------------------------
# Extract stage
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ExtractInput:
    """Input contract for the Extract stage.

    :param source_paths: Paths to source documents to convert.
    :param intermediate_dir: Directory where intermediate DocBook XML files
        will be written.
    :param handler_overrides: Optional mapping of file extension to extractor
        name, e.g. ``{".docx": "oxygen-docx"}``.
    :param max_workers: Thread-pool size for parallel extraction. ``None``
        uses a sensible default based on CPU count.
    """

    source_paths: tuple[str, ...]
    intermediate_dir: str
    handler_overrides: dict[str, str] = field(default_factory=dict)
    max_workers: int | None = None

    def __post_init__(self) -> None:
        if not self.source_paths:
            raise ContractError("ExtractInput.source_paths must not be empty")
        if not self.intermediate_dir:
            raise ContractError("ExtractInput.intermediate_dir must not be empty")
        if self.max_workers is not None and self.max_workers < 1:
            raise ContractError("ExtractInput.max_workers must be >= 1")


@dataclass(frozen=True)
class ExtractOutput:
    """Output contract for the Extract stage.

    :param outputs: Mapping of source path → intermediate XML path for every
        successfully extracted file.
    :param errors: Mapping of source path → error message for every file that
        failed extraction.
    """

    outputs: dict[str, str]
    errors: dict[str, str]

    @property
    def success(self) -> bool:
        """``True`` when no extraction errors occurred."""
        return len(self.errors) == 0


# ---------------------------------------------------------------------------
# Transform stage
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class TransformInput:
    """Input contract for the Transform stage.

    :param intermediates: Mapping of source path → intermediate XML path
        (output of the Extract stage).
    :param output_dir: Directory where DITA topic files will be written.
    :param rules_by_filename: Classification rules matched against filenames.
    :param rules_by_content: Classification rules matched against file content.
    :param plans_dir: Optional path to the directory containing per-file
        conversion plan JSONs from the Assess stage. When set, the Transform
        stage looks up ``<basename>.conversion_plan.json`` and uses
        ``default_topic_type`` as a classification hint (lower priority than
        config rules, higher than built-in heuristics).
    """

    intermediates: dict[str, str]
    output_dir: str
    rules_by_filename: tuple[object, ...] = field(default_factory=tuple)
    rules_by_content: tuple[object, ...] = field(default_factory=tuple)
    plans_dir: str | None = None

    def __post_init__(self) -> None:
        if not self.output_dir:
            raise ContractError("TransformInput.output_dir must not be empty")


@dataclass(frozen=True)
class TransformOutput:
    """Output contract for the Transform stage.

    :param topics: Mapping of source path → list of generated DITA topic
        paths.
    :param errors: Mapping of source path → error message for every file that
        failed transformation.
    """

    topics: dict[str, list[str]]
    errors: dict[str, str]

    @property
    def success(self) -> bool:
        """``True`` when no transform errors occurred."""
        return len(self.errors) == 0


# ---------------------------------------------------------------------------
# Load stage
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class LoadInput:
    """Input contract for the Load stage.

    :param topics: Mapping of source path → list of DITA topic paths (output
        of the Transform stage).
    :param output_dir: Directory where the DITA map and assets will be written.
    :param map_title: Human-readable title for the generated DITA map.
    :param intermediate_dir: Optional path to the intermediate directory so
        that assets (images, styles) can be copied to the output.
    """

    topics: dict[str, list[str]]
    output_dir: str
    map_title: str
    intermediate_dir: str | None = None

    def __post_init__(self) -> None:
        if not self.output_dir:
            raise ContractError("LoadInput.output_dir must not be empty")
        if not self.map_title:
            raise ContractError("LoadInput.map_title must not be empty")


@dataclass(frozen=True)
class LoadOutput:
    """Output contract for the Load stage.

    :param map_path: Absolute path to the written DITA map file.
    :param topic_count: Number of topic references included in the map.
    """

    map_path: str
    topic_count: int

    def __post_init__(self) -> None:
        if self.topic_count < 0:
            raise ContractError("LoadOutput.topic_count must be >= 0")


# ---------------------------------------------------------------------------
# Top-level pipeline result
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class PipelineOutput:
    """Aggregated result returned by the full pipeline run.

    :param assess: Output from the Assess stage.
    :param extract: Output from the Extract stage.
    :param transform: Output from the Transform stage.
    :param load: Output from the Load stage.
    """

    assess: AssessOutput
    extract: ExtractOutput
    transform: TransformOutput
    load: LoadOutput

    @property
    def map_path(self) -> str:
        """Convenience accessor for the final DITA map path."""
        return self.load.map_path
