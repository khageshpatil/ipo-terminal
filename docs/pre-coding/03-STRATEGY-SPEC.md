# Strategy Specification V1

## Objective
Maximize expected **net listing-day profit** from valid IPO applications.

## Primary target
`R = (ListingPrice - IssuePrice) / IssuePrice`

Primary classification label:
`positive_listing = ListingPrice > IssuePrice`

Secondary thresholds:
- `R > 5%`
- `R > 10%`
- `R > 15%`
- `R > 20%`

## Predictions
For IPO i at time t:
- `P_positive`
- `ExpectedReturn`
- downside/tail measures
- `P_allotment`
- `EV_net_per_application`
- confidence

## Economics
For application amount A:
`Profit_if_allotted = A * R`

A simple gross EV:
`P(allotment) * E[Profit_if_allotted]`

Full V1 EV:
`P(allotment) * E[profit_if_allotted] - applicable costs`

## APPLY — starting hypothesis
All must hold:
- `P_positive >= 70%`
- `ExpectedReturn >= +8%`
- `EV_net > 0`
- downside passes validated risk rule
- critical data quality acceptable
- application/category constraints satisfied

These are starting hypotheses, not proven market laws.

## WATCH
Use when evidence is promising but below APPLY, materially conflicting, near a threshold, or waiting on better/updated data.

## SKIP
Use when:
- `P_positive < 50%`, OR
- expected return <= 0, OR
- expected value <= 0, OR
- downside breaches validated rule, OR
- critical data is insufficient/unreliable.

## Risk
Do not choose the permanent downside threshold before examining historical return distributions. Research:
- expected loss if negative
- 5th/10th percentile return
- expected shortfall where appropriate
- comparable worst losses

Freeze final thresholds using training/validation only.

## Dynamic decisioning
Recommendations can change during the IPO. Preserve every decision with timestamp and model version.

## Decision times to backtest
- T0 pre-IPO
- T1 end Day 1
- T2 end Day 2
- T3 final pre-close

## Capital
Capital is variable. Allocation maximizes expected profit subject to actual IPO/category/application constraints. Do not assume independent allotment outcomes when mechanics imply dependence.
