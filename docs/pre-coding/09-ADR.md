# Architecture Decision Records

## ADR-001 — Listing-day exit
Accepted. Official listing price is the canonical V1 historical exit because it is objective and reproducible.

## ADR-002 — Mainboard vs SME
Accepted. Keep separate populations/models until evidence justifies combining them.

## ADR-003 — GMP provenance
Accepted. GMP is unofficial; store source/timestamp/quality and preserve source-specific values.

## ADR-004 — Point-in-time data
Accepted. No future information in historical or live decision snapshots.

## ADR-005 — Prediction vs decision
Accepted. Predictions are separate from APPLY/WATCH/SKIP economic decisioning.

## ADR-006 — Score is explanatory
Accepted. No fixed 100-point score is the ultimate trading rule.

## ADR-007 — Transparent V1 modeling
Accepted. Start interpretable to understand signal value and reduce overfitting risk.

## ADR-008 — Baselines
Accepted. Benchmark against Apply-Every-IPO, GMP-only and Subscription-only.

## ADR-009 — No order execution
Accepted. V1 is decision support only.
