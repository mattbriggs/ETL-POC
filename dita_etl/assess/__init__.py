"""Content assessment sub-pipeline.

Provides pure functions for analysing source documents before conversion:
structural scoring, topic-type prediction, and near-duplicate detection.

Public API::

    from dita_etl.assess.config import AssessConfig
    from dita_etl.assess.inventory import assess_batch
"""

from dita_etl.assess.config import AssessConfig
from dita_etl.assess.inventory import assess_batch

__all__ = ["AssessConfig", "assess_batch"]
