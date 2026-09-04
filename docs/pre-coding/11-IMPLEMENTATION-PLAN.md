# Implementation Plan V1

## Phase 0 — Setup
Read all pre-coding docs. Configure Matt Pocock skills for the repo. Establish issue tracker/doc layout. Confirm Python/Node/Postgres environment.

## Phase 1 — Data model
Implement canonical entities, timestamped observations, provenance and quality states.

## Phase 2 — Historical dataset
Build verified historical dataset and completeness report.

## Phase 3 — Point-in-time features
Implement eligibility, feature calculations, freshness and leakage tests.

## Phase 4 — Baselines
Implement Apply-Every-IPO, GMP-only and Subscription-only.

## Phase 5 — Models
Implement listing classifier, return/downside model and allotment estimator.

## Phase 6 — Decision engine
Implement EV, risk filters, APPLY/WATCH/SKIP, confidence and explanations.

## Phase 7 — Capital optimizer
Support variable capital and real application constraints.

## Phase 8 — Backtest
Chronological validation, walk-forward testing, Monte Carlo allotment and benchmark reports.

## Phase 9 — Live ingestion
Only after historical validation: provider integrations, scheduled snapshots, freshness monitoring.

## Phase 10 — Dashboard
IPO watchlist, recommendation cards, evidence, live snapshots, capital planner and backtest/reporting.

## Phase 11 — Hardening
Observability, source failure handling, security, deployment and final docs.

## Definition of done
- Leakage tests pass.
- Historical dataset is documented.
- Strategy is benchmarked.
- Probabilities are evaluated for calibration.
- Model/strategy versions are reproducible.
- Live source licensing/availability is verified.
