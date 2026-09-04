# Data Sources & Ingestion Specification

## Source hierarchy
### Tier 1
NSE, BSE, SEBI/public issue documents.

### Tier 2
Licensed structured market-data providers.

### Tier 3
Specialized IPO/GMP providers.

### Tier 4
Manual fallback for exceptional gaps, always flagged and sourced.

## Realtime policy
True tick-by-tick data is not required initially. Use configurable event/periodic snapshots that reconstruct the information available at each decision point.

Initial research cadence:
- pre-open/pre-IPO
- hourly during subscription
- final pre-close
- listing outcome

## Source conflicts
Prefer primary sources where available. Preserve conflicting observations. GMP remains source-specific and unofficial.

## Provider validation gate
Before production dependency, verify:
- API availability
- licensing/commercial-use rights
- rate limits
- authentication
- uptime/reliability
- historical coverage
- timestamp fidelity
- latency
- cost
- archival behavior
- failure handling

## Ingestion
Adapters must be isolated, idempotent, validated and observable. Handle downtime, malformed responses, duplicates, schema drift and rate limits.
