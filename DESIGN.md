
# Design & Maintenance

## Architecture
- **Stages** (Strategy pattern): `ExtractStage`, `TransformStage`, `LoadStage` implement a common `Stage` interface, enabling substitution and composition.
- **Runner** (Adapter): `SubprocessRunner` abstracts shell commands (Pandoc/Saxon/Oxygen). Swap with a different runner or a dry-run.
- **Classification** (Policy): `classify_topic` applies config rules then heuristics.
- **Config** (Builder): Dataclasses parse YAML into strongly-typed objects.
- **Flow**: Prefect tasks wrap each stage; a flow wires them together. Parallelism is enabled at the task level and can be extended with thread pools within tasks for heavy I/O.

## Determinism
- Stable iteration orders, explicit inputs/outputs, and immutable artifacts. Hashing utilities (`hashing.py`) allow cache keys and verification.

## Graceful Degradation
- Extraction errors are captured per-file; pipeline continues. Errors are returned in `StageResult.data["errors"]`.

## Extending Formats
- Implement additional converters in `ExtractStage` (e.g., detect .docx -> use Oxygen Batch Converter).
- Add mapping templates/XSLT in `TransformStage` for richer DITA outputs (e.g., steps/cmd, tables, images).

## Custom DITA
- If using specialized DTDs, generate proper root elements and DOCTYPEs in `TransformStage`. Parameterize via config.

## Testing
- Tests mock `SubprocessRunner.run`, avoiding real tool calls.
- Fixtures in `tests/` cover all class methods for 100% method coverage.
- Use `pytest -q --cov=dita_etl`

## Maintenance
- Keep config-driven rules up to date.
- Replace placeholder XSLT with real mapping and wire Saxon call in `_apply_xslt`.
- Optionally adopt DVC or Prefect blocks for artifact/version management.
