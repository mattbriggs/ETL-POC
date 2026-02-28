"""Deprecated — use ``dita_etl.pipeline.run_pipeline`` instead.

This module was the Prefect-based orchestrator. It has been replaced by
a pure-Python pipeline with no external orchestration dependency.
"""

import warnings

warnings.warn(
    "dita_etl.orchestrator is deprecated. Use dita_etl.pipeline.run_pipeline instead.",
    DeprecationWarning,
    stacklevel=2,
)


def build_flow(*args, **kwargs):
    """Deprecated shim — delegates to :func:`dita_etl.pipeline.run_pipeline`."""
    warnings.warn(
        "build_flow() is deprecated. Use dita_etl.pipeline.run_pipeline() instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    from dita_etl.pipeline import run_pipeline
    return run_pipeline(*args, **kwargs)
