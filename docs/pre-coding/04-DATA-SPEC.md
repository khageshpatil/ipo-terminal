# Data Specification V1

## Rule
Raw observations, normalized records, features, predictions and outcomes are separate layers.

Every changing observation stores:
- value
- observed_at
- retrieved_at
- source
- source timestamp if available
- unit
- quality/status
- provenance/reference
- ingestion run

## IPO master
`ipo_id, issuer_name, symbol, exchange, segment, open_date, close_date, listing_date, price_band_low, price_band_high, issue_price, lot_size, minimum_application_amount, issue_size, fresh_issue_amount, ofs_amount, retail_quota, qib_quota, nii_quota`

## Fundamentals
Revenue, EBITDA, margins, PAT, EPS, operating cash flow, free cash flow when available, growth/CAGR, debt/net debt, leverage, interest coverage, net worth, ROE, ROCE, promoter holding/OFS, customer concentration, related-party flags, litigation/regulatory flags, contingent liabilities.

## Valuation
P/E, P/B, EV/EBITDA, implied market cap, peer median multiples, premium/discount to peers.

## Subscription snapshots
Timestamped QIB/NII/Retail/Total bids and times, shares offered where available. Derived velocity/acceleration and category mix features.

## GMP snapshots
GMP, GMP %, source, source timestamp, source quality, cross-source agreement. Derived change, momentum, volatility and GMP-to-price.

## Market
Nifty level/returns, volatility measure, sector returns/momentum, recent IPO performance.

## Outcomes
Issue price, listing price, listing return, first traded/opening price if available, day-1 OHLC, volume, VWAP if available.

## Allotment
Category, applications, shares offered, successful applicants, allotment ratio, modeled allotment probability, basis-of-allotment reference.

## Quality states
VERIFIED_PRIMARY, VERIFIED_SECONDARY, UNVERIFIED_SECONDARY, STALE, MISSING, CONFLICTING, MANUAL_REVIEW.

Critical fields may not be silently overwritten with inferred/missing values.
