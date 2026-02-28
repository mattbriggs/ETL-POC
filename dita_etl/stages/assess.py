"""Stage 0 — Assessment.

Runs the assessment sub-pipeline on all source files and writes artefacts
(inventory, dedupe map, HTML report, conversion plans) to the output
directory.
"""

from __future__ import annotations

from dita_etl.assess.config import AssessConfig
from dita_etl.assess.inventory import assess_batch
from dita_etl.contracts import AssessInput, AssessOutput


class AssessStage:
    """Stage 0: assess source documents before conversion.

    Produces an inventory, near-duplicate report, HTML summary, and per-file
    conversion plans that inform downstream stages.

    :param config_path: Path to the assessment YAML configuration file.
    """

    def __init__(self, config_path: str) -> None:
        self._config_path = config_path

    def run(self, input_: AssessInput) -> AssessOutput:
        """Execute the assessment stage.

        :param input_: Validated :class:`~dita_etl.contracts.AssessInput`
            contract.
        :returns: :class:`~dita_etl.contracts.AssessOutput` contract with
            paths to the written artefacts.
        """
        cfg = AssessConfig.load(input_.config_path)
        paths = assess_batch(
            list(input_.source_paths),
            cfg,
            out_dir=input_.output_dir,
        )
        return AssessOutput(
            inventory_path=paths["inventory"],
            dedupe_path=paths["dedupe"],
            report_path=paths["report"],
            plans_dir=paths["plans_dir"],
        )
