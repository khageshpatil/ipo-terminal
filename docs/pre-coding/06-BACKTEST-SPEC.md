# Backtest & Research Specification V1

## Research question
Does the listing-gain engine improve economic outcomes versus simple strategies using only information available at each historical decision timestamp?

## Universe
Indian Mainboard IPOs with sufficient reliable data. SME is tracked separately.

## Point-in-time rule
A prediction at t may use only information eligible at <= t. Never use future subscription, post-listing prices, later financials, future news or future GMP.

## Outcomes
Primary: listing return from official listing price.
Secondary: >5%, >10%, >15%, >20%.

## Allotment
Reconstruct historical basis-of-allotment mechanics where possible. Otherwise use a documented probabilistic simulation with reproducible seeds.

## Capital scenarios
At least test ₹25k, ₹50k, ₹1L and ₹5L as sensitivity cases. These are not permanent limits.

## Baselines
1. Apply Every IPO
2. GMP-only
3. Subscription-only
4. Full proposed model

## Validation
Use chronological train/validation/test splits and then walk-forward evaluation. Never randomly shuffle the whole history.

## Metrics
Economic: cumulative profit, profit/application, return on blocked capital, hit rate, max drawdown, worst loss, loss frequency, capital utilization.
Predictive: APPLY precision, recall, calibration, Brier score, AUC where meaningful, expected-vs-realized error.
Robustness: year, market regime, sector, IPO size, subscription, GMP availability, data completeness.

## Threshold policy
Tune only on training/validation. Lock final test before final strategy claim.

## Monte Carlo
Simulate uncertain allotment outcomes and capital allocations. Report percentile outcomes and probability of loss/benchmark outperformance.

## Evidence rule
Do not claim edge from synthetic data, tiny samples, in-sample results, or one market regime.
