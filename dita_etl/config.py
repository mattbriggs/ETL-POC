"""Pipeline configuration dataclasses.

Configuration is loaded once at startup from a YAML file and passed
immutably through the pipeline. No I/O occurs after initial loading.

Unknown keys in any section raise :class:`ValueError` immediately so that
mis-spelled or stale configuration is caught at startup rather than silently
ignored.

Example YAML structure::

    tooling:
      pandoc_path: /usr/local/bin/pandoc
      java_path: /usr/bin/java
      saxon_jar: /opt/saxon/saxon9he.jar

    source_formats:
      treat_as_html: [".html", ".htm"]

    extract:
      max_workers: 4
      handler_overrides:
        ".docx": "oxygen-docx"

    dita_output:
      output_folder: build/out
      map_title: "My Documentation Set"

    classification_rules:
      by_filename:
        - match: "index"
          type: "concept"
      by_content:
        - match: "procedure"
          type: "task"
"""

from __future__ import annotations

from dataclasses import dataclass, field, fields as dc_fields
from typing import Any

import yaml


# ---------------------------------------------------------------------------
# Sub-configuration dataclasses
# ---------------------------------------------------------------------------


@dataclass
class ClassificationRule:
    """A single topic-classification rule.

    :param pattern: Glob pattern (for filename rules) or regex fragment (for
        content rules). The legacy ``match`` key is also accepted.
    :param type: DITA topic type to assign when the rule matches — one of
        ``"concept"``, ``"task"``, or ``"reference"``.
    """

    pattern: str
    type: str

    def __init__(
        self,
        match: str | None = None,
        pattern: str | None = None,
        type: str = "",
    ) -> None:
        self.pattern = pattern or match or ""
        self.type = type

    @property
    def topic_type(self) -> str:
        """Alias for :attr:`type` for API consistency."""
        return self.type


@dataclass
class Chunking:
    """Chunking parameters used during topic generation.

    :param level: Heading level at which to split into separate topics.
    :param nested_topics: Whether to nest child topics under their parent.
    """

    level: int = 1
    nested_topics: bool = True


@dataclass
class DITAOutput:
    """DITA output settings.

    :param dita_version: Target DITA version string (e.g. ``"1.3"``).
    :param use_specialization: Whether to emit DITA specialization elements.
    :param output_folder: Root folder for all pipeline build artefacts.
    :param map_title: Title written into the generated DITA map.
    """

    dita_version: str = "1.3"
    use_specialization: bool = False
    output_folder: str = "out/dita"
    map_title: str = "Documentation Set"


@dataclass
class Tooling:
    """External tool configuration.

    :param pandoc_path: Absolute path (or command name) for the Pandoc binary.
    :param oxygen_scripts_dir: Optional path to Oxygen XML Editor's scripts
        directory, required only when using the Oxygen DOCX extractor.
    :param saxon_jar: Path to the Saxon HE JAR file for XSLT transformation.
    :param java_path: Absolute path (or command name) for the Java binary.
    """

    pandoc_path: str = "pandoc"
    oxygen_scripts_dir: str | None = None
    saxon_jar: str = "saxon-he.jar"
    java_path: str = "java"


@dataclass
class ExtractConfig:
    """Extract stage configuration.

    :param handler_overrides: Mapping of file extension to extractor name,
        e.g. ``{".docx": "oxygen-docx"}``. Overrides the default handler
        chosen by the registry for matched extensions.
    :param max_workers: Thread-pool size for parallel extraction. ``None``
        uses a sensible default based on CPU count.
    """

    handler_overrides: dict[str, str] = field(default_factory=dict)
    max_workers: int | None = None


# ---------------------------------------------------------------------------
# Strict instantiation helper
# ---------------------------------------------------------------------------


def _strict(cls: type, data: dict[str, Any]) -> Any:
    """Instantiate *cls* from *data*, raising :class:`ValueError` on unknown keys.

    :param cls: Dataclass type to instantiate.
    :param data: Mapping of keyword arguments sourced from YAML.
    :returns: New instance of *cls*.
    :raises ValueError: If *data* contains keys not declared as fields on *cls*.
    """
    valid = {f.name for f in dc_fields(cls)}
    unknown = set(data) - valid
    if unknown:
        raise ValueError(
            f"Unknown config key(s) in {cls.__name__}: {sorted(unknown)}"
        )
    return cls(**data)


# ---------------------------------------------------------------------------
# Root config
# ---------------------------------------------------------------------------


@dataclass
class Config:
    """Root configuration object for the full ETL pipeline.

    :param source_formats: Mapping of treat-as keys to lists of file
        extensions, e.g. ``{"treat_as_html": [".html", ".htm"]}``.
    :param classification_rules: Mapping with ``"by_filename"`` and
        ``"by_content"`` keys, each containing a list of
        :class:`ClassificationRule` objects.
    :param chunking: Chunking parameters.
    :param dita_output: DITA output settings.
    :param tooling: External tool paths.
    :param extract: Extract stage settings (handler overrides, worker count).
    """

    source_formats: dict[str, list[str]] = field(
        default_factory=lambda: {"treat_as_markdown": [".md"]}
    )
    classification_rules: dict[str, list[ClassificationRule]] = field(
        default_factory=dict
    )
    chunking: Chunking = field(default_factory=Chunking)
    dita_output: DITAOutput = field(default_factory=DITAOutput)
    tooling: Tooling = field(default_factory=Tooling)
    extract: ExtractConfig = field(default_factory=ExtractConfig)

    # ------------------------------------------------------------------
    # Factory (imperative shell: file I/O lives only here)
    # ------------------------------------------------------------------

    @staticmethod
    def load(path: str) -> "Config":
        """Load and parse a YAML configuration file.

        :param path: Path to the YAML configuration file.
        :returns: Fully populated :class:`Config` instance.
        :raises FileNotFoundError: If *path* does not exist.
        :raises yaml.YAMLError: If the file is not valid YAML.
        """
        with open(path) as fh:
            data: dict[str, Any] = yaml.safe_load(fh) or {}

        unknown_top = set(data) - {f.name for f in dc_fields(Config)}
        if unknown_top:
            raise ValueError(
                f"Unknown top-level config key(s): {sorted(unknown_top)}"
            )

        def _rules(lst: list[dict[str, Any]] | None) -> list[ClassificationRule]:
            result: list[ClassificationRule] = []
            for r in lst or []:
                unknown = set(r) - {"match", "pattern", "type"}
                if unknown:
                    raise ValueError(
                        f"Unknown key(s) in classification rule: {sorted(unknown)}"
                    )
                result.append(ClassificationRule(**r))
            return result

        cr_data = data.get("classification_rules") or {}
        classification_rules: dict[str, list[ClassificationRule]] = {
            "by_filename": _rules(cr_data.get("by_filename")),
            "by_content": _rules(cr_data.get("by_content")),
        }

        return Config(
            source_formats=data.get("source_formats") or {},
            classification_rules=classification_rules,
            chunking=_strict(Chunking, data.get("chunking") or {}),
            dita_output=_strict(DITAOutput, data.get("dita_output") or {}),
            tooling=_strict(Tooling, data.get("tooling") or {}),
            extract=_strict(ExtractConfig, data.get("extract") or {}),
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def source_extensions(self) -> list[str]:
        """Return all configured source file extensions.

        :returns: Sorted, deduplicated list of extension strings (e.g.
            ``[".docx", ".html", ".md"]``).
        """
        exts: list[str] = []
        for vals in self.source_formats.values():
            for v in vals:
                if isinstance(v, str) and v.startswith("."):
                    exts.append(v)
        return sorted(set(exts)) or [".md", ".docx", ".html"]
