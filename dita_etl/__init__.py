"""
DITA ETL package entrypoint.

This module exposes the main Prefect flow for CLI execution
without importing heavy dependencies during test discovery.
"""

__version__ = "0.1.0"

def build_flow(*args, **kwargs):
    """
    Lazy import of the Prefect build_flow function.
    Avoids Prefect initialization at import time.
    """
    from .orchestrator import build_flow as _build_flow
    return _build_flow(*args, **kwargs)