# CONTEXT — IPO Listing-Gain Decision Engine

## Product
A decision-support system for Indian IPO applications focused exclusively on listing-day gains. It evaluates IPO terms, valuation, fundamentals, subscription, GMP and market conditions, estimates listing probability/return, estimates allotment probability, calculates expected profit per application, and produces APPLY / WATCH / SKIP.

## Domain language
- **Issue price:** final IPO price per share.
- **Listing price:** official first exchange listing price used as the canonical V1 exit.
- **Listing return:** `(listing_price - issue_price) / issue_price`.
- **Allotment:** receiving IPO shares.
- **Allotment probability:** estimated probability of receiving shares for a valid application under the applicable rules.
- **GMP:** Grey Market Premium; unofficial market indicator, never exchange-certified.
- **Subscription:** demand relative to category shares available.
- **Point-in-time data:** information actually available by a specified timestamp.
- **Decision timestamp:** time at which a recommendation is generated.
- **Expected listing return:** predicted future listing return.
- **Expected profit per application:** expected economic result of one application after allotment probability, return distribution and costs.
- **Confidence:** trust indicator based on data quality/model coverage; not itself a probability.
- **APPLY / WATCH / SKIP:** action states.

## Product is not
- A long-term stock-picking system.
- An automated broker/order execution system.
- A guarantee of IPO allotment or profit.
- A GMP-only tracker.
