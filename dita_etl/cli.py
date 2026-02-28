"""Command-line interface — imperative shell.

This module is the outermost imperative shell. It parses arguments,
configures logging, calls the pipeline, and handles top-level errors.
No business logic lives here.

Usage::

    dita-etl run --config config/config.yaml --input docs/

Or directly::

    python -m dita_etl.cli run --config config/config.yaml --input docs/
"""

from __future__ import annotations

import sys

import click

from dita_etl.logging_config import configure_logging
from dita_etl.pipeline import run_pipeline


@click.group()
@click.option(
    "--log-level",
    default="INFO",
    show_default=True,
    type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR"], case_sensitive=False),
    help="Logging verbosity level.",
)
def main(log_level: str) -> None:
    """DITA ETL Pipeline — convert source documents to DITA XML."""
    configure_logging(level=log_level)


@main.command()
@click.option(
    "--config",
    default="config/config.yaml",
    show_default=True,
    metavar="PATH",
    help="Path to the main pipeline configuration YAML file.",
)
@click.option(
    "--assess-config",
    default="config/assess.yaml",
    show_default=True,
    metavar="PATH",
    help="Path to the assessment configuration YAML file.",
)
@click.option(
    "--input",
    "input_dir",
    default="sample_data/input",
    show_default=True,
    metavar="DIR",
    help="Root directory containing source documents.",
)
def run(config: str, assess_config: str, input_dir: str) -> None:
    """Run the full ETL pipeline (Assess → Extract → Transform → Load)."""
    try:
        result = run_pipeline(
            config_path=config,
            assess_config_path=assess_config,
            input_dir=input_dir,
        )
        click.echo(f"Pipeline complete. DITA map: {result.map_path}")
        if not result.extract.success:
            click.secho(
                f"  Extract errors: {list(result.extract.errors.keys())}",
                fg="yellow",
                err=True,
            )
        if not result.transform.success:
            click.secho(
                f"  Transform errors: {list(result.transform.errors.keys())}",
                fg="yellow",
                err=True,
            )
    except FileNotFoundError as exc:
        click.secho(f"Error: {exc}", fg="red", err=True)
        sys.exit(1)
    except Exception as exc:  # noqa: BLE001
        click.secho(f"Unexpected error: {exc}", fg="red", err=True)
        sys.exit(2)


@main.command()
@click.option(
    "--config",
    default="config/config.yaml",
    show_default=True,
    metavar="PATH",
    help="Path to the main pipeline configuration YAML file.",
)
@click.option(
    "--assess-config",
    default="config/assess.yaml",
    show_default=True,
    metavar="PATH",
    help="Path to the assessment configuration YAML file.",
)
@click.option(
    "--input",
    "input_dir",
    default="sample_data/input",
    show_default=True,
    metavar="DIR",
    help="Root directory containing source documents.",
)
def assess(config: str, assess_config: str, input_dir: str) -> None:
    """Run the Assess stage only (no extraction or DITA output)."""
    from dita_etl.assess.config import AssessConfig
    from dita_etl.assess.inventory import assess_batch
    from dita_etl.config import Config
    from dita_etl.io.filesystem import discover_files

    try:
        cfg = Config.load(config)
        acfg = AssessConfig.load(assess_config)
        source_paths = discover_files(input_dir, cfg.source_extensions())
        out_dir = f"{cfg.dita_output.output_folder}/assess"
        paths = assess_batch(source_paths, acfg, out_dir=out_dir)
        click.echo(f"Assessment complete. Report: {paths['report']}")
    except FileNotFoundError as exc:
        click.secho(f"Error: {exc}", fg="red", err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
