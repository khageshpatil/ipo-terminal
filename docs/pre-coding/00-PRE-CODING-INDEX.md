# IPO Listing-Gain Decision Engine — Pre-Coding Documentation Pack
Status: Strategy V1 / pre-coding baseline

## Source of truth
1. 01-CONTEXT.md
2. 02-PRD.md
3. 03-STRATEGY-SPEC.md
4. 04-DATA-SPEC.md
5. 05-DATA-SOURCES.md
6. 06-BACKTEST-SPEC.md
7. 07-MODEL-SPEC.md
8. 08-SYSTEM-DESIGN.md
9. 09-ADR.md
10. 10-TEST-PLAN.md
11. 11-IMPLEMENTATION-PLAN.md
12. AGENTS.md
13. 12-DATA-RESEARCH-CHECKLIST.md

## Non-negotiables
- Primary objective: listing-day profit, not long-term investment.
- Canonical historical exit: official listing price.
- Capital is configurable.
- Universe: all sufficiently-data-backed IPO opportunities; Mainboard and SME remain separate populations.
- Dynamic data is point-in-time and timestamped.
- GMP is unofficial and must retain provenance.
- Separate listing probability, expected return, allotment probability, downside and expected application profit.
- APPLY/WATCH/SKIP thresholds are hypotheses until validated out-of-sample.
- No look-ahead bias.
- Compare against simple baselines.
- Never fabricate missing critical data.
