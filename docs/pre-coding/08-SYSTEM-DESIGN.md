# System Design V1

## Architecture

```text
NSE/BSE/SEBI + GMP/market providers
        ↓
Source adapters
        ↓
Raw observation store
        ↓
Normalization + validation
        ↓
Point-in-time feature layer
        ↓
Listing model + allotment model
        ↓
Decision engine
        ↓
Capital optimizer
        ↓
API
        ↓
Dashboard
```

## Technology direction
- Backend: Python/FastAPI
- Research: Python
- Data processing: pandas/polars as justified
- DB: PostgreSQL
- Frontend: Next.js/React
- Charts: Plotly or equivalent
- Scheduled ingestion: worker/scheduler

## Boundaries
`data_sources`, `raw_data`, `normalization`, `features`, `models`, `allotment`, `strategy`, `backtest`, `api`, `web`.

No scraping in request handlers. No strategy logic in UI. No future outcome data in inference.

## Core entities
IPO, IssueTerms, OfferDocument, FinancialSnapshot, ValuationSnapshot, SubscriptionSnapshot, GMPSnapshot, MarketSnapshot, FeatureSnapshot, ModelPrediction, Recommendation, AllotmentOutcome, ListingOutcome, BacktestRun, DataSource, IngestionRun.

## Auditability
Any recommendation must be reproducible from its raw observations, feature version, model version, strategy version and decision timestamp.

## Security/reliability
Secrets only in environment/secret storage. Provider failures must be visible. No live broker execution in V1.
