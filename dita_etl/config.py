"""Pipeline configuration dataclasses.

Configuration is loaded once at startup from a YAML file and passed
immutably through the pipeline. No I/O occurs after initial loading.

Example YAML structure::

    tooling:
      pandoc_path: /usr/local/bin/pandoc
      java_path: /usr/bin/java
      saxon_jar: /opt/saxon/saxon9he.jar

    source_formats:
      treat_as_html: [".html", ".htm"]

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

from dataclasses import dataclass, field
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

        def _rules(lst: list[dict[str, Any]] | None) -> list[ClassificationRule]:
            return [ClassificationRule(**r) for r in (lst or [])]

        cr_data = data.get("classification_rules") or {}
        classification_rules: dict[str, list[ClassificationRule]] = {
            "by_filename": _rules(cr_data.get("by_filename")),
            "by_content": _rules(cr_data.get("by_content")),
        }

        return Config(
            source_formats=data.get("source_formats") or {},
            classification_rules=classification_rules,
            chunking=Chunking(**(data.get("chunking") or {})),
            dita_output=DITAOutput(**(data.get("dita_output") or {})),
            tooling=Tooling(**(data.get("tooling") or {})),
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
