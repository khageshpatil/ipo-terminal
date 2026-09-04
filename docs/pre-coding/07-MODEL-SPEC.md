# Model Specification V1

## Outputs
- P(positive listing)
- Expected listing return
- P(>5/10/15/20%)
- Expected negative loss / downside percentiles
- P(allotment)
- EV net/application
- Confidence
- Recommendation

## Feature groups
- Fundamentals
- Valuation
- Subscription dynamics
- GMP dynamics
- Market regime
- Issue structure

## V1 model
Start interpretable:
- calibrated logistic regression or equivalent classifier for positive listing
- regularized/robust/quantile approach for returns and downside
- separate allotment estimator

Do not begin with complex ensembles.

## Score
A human-readable score may exist for explanations, but is not the trading decision.

## Leakage protection
Every feature records source, observed_at, eligibility rule, transformation and missing-data behavior.

## Missing data
Never fabricate. Critical missing data should lower confidence or block APPLY.

## Calibration
Validate that predicted probability bands correspond reasonably to observed frequencies.

## Explainability
For every decision show key positive/negative drivers, source freshness and model/feature/strategy versions.

## Future experiments
Tree ensembles, interactions, regime models and learned weighting only after the transparent baseline is fully validated.
