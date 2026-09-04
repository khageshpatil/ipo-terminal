# PRD — IPO Listing-Gain Decision Engine

## Goal
For each IPO and decision timestamp, answer: **Should I apply now, wait, or skip?**

## Inputs
- IPO issue terms
- Fundamentals
- Valuation and peers
- Timestamped QIB/NII/Retail subscription
- Timestamped GMP
- Market/sector conditions
- Available capital

## Outputs
- APPLY / WATCH / SKIP
- Probability of positive listing
- Expected listing return
- Probability of >5%, >10%, >15%, >20% return
- Downside indicators
- Allotment probability
- Expected profit/application
- Expected return on blocked capital
- Confidence
- Explanation of important drivers
- Decision/model/data timestamps

## Functional requirements
1. Discover upcoming/open/recent IPOs.
2. Store issue terms and category information.
3. Store point-in-time financial and offer-document fields.
4. Calculate valuation and peer comparisons.
5. Capture timestamped subscription snapshots.
6. Capture timestamped GMP observations and provenance.
7. Capture market regime features.
8. Predict listing outcomes.
9. Estimate allotment probability.
10. Calculate expected application economics.
11. Recommend APPLY/WATCH/SKIP.
12. Optimize applications for variable capital under real constraints.
13. Run historical point-in-time backtests.
14. Compare against Apply-Every-IPO, GMP-only and Subscription-only baselines.
15. Expose explanation and audit trail.

## Non-functional requirements
- Reproducible research.
- Explicit Asia/Kolkata timestamps.
- No silent critical-data fabrication.
- Versioned model/feature/strategy.
- Immutable raw observations.
- Clear research vs production separation.
- No automated orders in V1.

## Out of scope
- Long-term holding recommendations.
- Automated broker execution.
- Social/news sentiment NLP.
- Post-listing trading strategies as part of V1.
- Combining SME and Mainboard into one model without evidence.
