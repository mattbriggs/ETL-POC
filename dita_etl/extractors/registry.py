"""Factory for building the extractor registry (Factory pattern).

The registry maps lowercase file extensions to :class:`FileExtractor`
instances. Callers can supply ``handler_overrides`` to reroute specific
extensions to alternative extractors at runtime.

Example::

    registry = build_registry(
        pandoc_path="/usr/local/bin/pandoc",
        handler_overrides={".docx": "oxygen-docx"},
        oxygen_scripts_dir="/opt/oxygen/scripts",
    )
    extractor = registry[".md"]
"""

from __future__ import annotations

from dita_etl.extractors.base import FileExtractor
from dita_etl.extractors.docx_oxygen import DocxOxygenExtractor
from dita_etl.extractors.docx_pandoc import DocxPandocExtractor
from dita_etl.extractors.html_pandoc import HtmlPandocExtractor
from dita_etl.extractors.md_pandoc import MdPandocExtractor


def build_registry(
    pandoc_path: str,
    handler_overrides: dict[str, str] | None = None,
    oxygen_scripts_dir: str | None = None,
) -> dict[str, FileExtractor]:
    """Build a mapping of file extension → :class:`FileExtractor`.

    Default mappings:

    * ``.md``           → :class:`~dita_etl.extractors.md_pandoc.MdPandocExtractor`
    * ``.html``, ``.htm`` → :class:`~dita_etl.extractors.html_pandoc.HtmlPandocExtractor`
    * ``.docx``         → :class:`~dita_etl.extractors.docx_pandoc.DocxPandocExtractor`

    :param pandoc_path: Absolute path or command name for the Pandoc binary.
    :param handler_overrides: Optional mapping of ``extension → extractor name``
        to override the default registry entries.
    :param oxygen_scripts_dir: Path to Oxygen XML Editor scripts directory.
        Required only when an override references ``"oxygen-docx"``.
    :returns: Dictionary mapping lowercase extensions to extractor instances.
    :raises ValueError: If an override names an unknown extractor.
    """
    overrides = handler_overrides or {}

    # Build base handlers
    default_handlers: list[FileExtractor] = [
        MdPandocExtractor(pandoc_path),
        HtmlPandocExtractor(pandoc_path),
        DocxPandocExtractor(pandoc_path),
    ]

    # Build name → instance map (includes optional Oxygen handler)
    name_map: dict[str, FileExtractor] = {h.name: h for h in default_handlers}
    if oxygen_scripts_dir:
        oxy: FileExtractor = DocxOxygenExtractor(oxygen_scripts_dir)
        name_map[oxy.name] = oxy

    # Populate extension → handler mapping from defaults
    registry: dict[str, FileExtractor] = {}
    for handler in default_handlers:
        for ext in handler.exts:
            registry[ext.lower()] = handler

    # Apply caller-supplied overrides
    for ext, extractor_name in overrides.items():
        if extractor_name not in name_map:
            raise ValueError(
                f"Unknown extractor '{extractor_name}' for extension '{ext}'. "
                f"Available: {sorted(name_map)}"
            )
        registry[ext.lower()] = name_map[extractor_name]

    return registry
