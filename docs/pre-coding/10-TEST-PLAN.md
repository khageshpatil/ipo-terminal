# Test Plan V1

## Unit/domain
Test listing return, probability bounds, expected profit, recommendation gates, capital constraints and invalid inputs.

## Point-in-time tests
A 12:00 prediction must never see 15:00 data.

## Data contracts
Verify required fields, timestamps, normalization, duplicates, source lineage and schema drift.

## Feature tests
Use fixed fixtures for subscription velocity, GMP momentum, peer premium and market windows.

## Backtest tests
Synthetic fixtures may test engine correctness, but synthetic performance must never be presented as strategy evidence.

## Model tests
Check prediction bounds, deterministic inference for fixed artifacts, calibration pipeline and artifact compatibility.

## Integration
Provider → normalization → feature snapshot → model → decision.

## UI
Verify recommendation, timestamp/source, stale/missing warnings, capital changes and agreement with API/backtest values.

## Reproducibility
A run must be tied to data snapshot, code revision, model version, strategy version and parameters.
