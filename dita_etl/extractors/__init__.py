"""Format-specific extractors (Strategy pattern).

Each extractor implements the :class:`~dita_etl.extractors.base.FileExtractor`
protocol and is responsible for converting one or more source formats into
intermediate DocBook XML.
"""
