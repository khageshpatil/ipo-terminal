# G1-G4 Research Results
**Version:** 1.0 | **Date:** 2026-09-04
**Scope:** Indian Mainboard IPOs, Calendar Years 2018–2024
**Status:** G1–G3 methodology confirmed; G4 base rate computed from confirmed aggregate statistics

---

## Executive Summary

### How many real, usable Mainboard IPOs do we have?

| Status | Count |
|--------|------:|
| Estimated total Mainboard IPOs, 2018–2024 (CY) | **341–406** |
| Individual records with confirmed issue price (secondary-verified) | **35** |
| Individual records with confirmed listing price (secondary-verified, approximate) | **35** |
| Individual records with subscription data | **6** |
| Records usable for model training right now | **0** (no primary-verified listing prices yet) |

**Honest assessment:** The per-row dataset does not yet exist. All 341–406 IPO records must be collected before model training begins. The collection path is unblocked and well-defined — it requires either an IPOMatrix/PRIME Database subscription (~1 day with paid access) or a systematic manual collection of NSE Bhav Copy files (~25–40 hours without paid access).

What does exist — and is confirmed — is the **aggregate statistical picture** for each year, which is sufficient to establish the base rate and return distribution at the year-cohort level.

---

## Base-Rate Result

### Primary statistic: Percentage of Mainboard IPOs listing above issue price

**Verified at year level (2021, 2022, 2024 — highest confidence):**

| Year | Total IPOs | Positive listings | Negative listings | Positive rate | Confidence |
|------|----------:|------------------:|------------------:|--------------|-----------|
| 2018 | ~42 | Unknown | Unknown | **Not established** | ⛔ Low |
| 2019 | ~39 | ~27 | ~12 | **~69%** | 🟡 Medium (one study; count inconsistency) |
| 2020 | ~44–69 | ~33 | ~11 | **~75%** (of 44) | 🟡 Medium (count disputed) |
| 2021 | **63** | **46** | **17** | **73.0%** | ✅ High (3+ independent sources) |
| 2022 | **40** | **23** | **~15** | **57.5%** | ✅ High (3+ independent sources) |
| 2023 | **60** | Unknown | Unknown | **~55–65% (est.)** | 🟡 Medium (only median return confirmed) |
| 2024 | **93** | **74** | **19** | **79.6%** | ✅ High (3+ independent sources) |

### Aggregate base rate estimate (2018–2024)

Using only the years with confirmed data and filling 2018/2019/2023 with conservative estimates:

| Scenario | IPOs used | Positive | Positive rate |
|----------|----------:|--------:|--------------|
| **Best-confirmed only** (2021+2022+2024) | 196 | 143 | **73.0%** |
| **Mid estimate** (all years, using estimated counts for uncertain years) | ~370 | ~243 | **~65.7%** |
| **Conservative estimate** (assuming 2018 was poor; downside years weighted) | ~370 | ~228 | **~61.6%** |

> **Working base rate: 65–73%** for listing above issue price.
> The true figure will be established precisely once the per-row dataset is built.

**Critical implication for strategy:**
The strategy's proposed APPLY threshold requires confidence of ≥70%. The unconditional base rate is itself near that level in bull years (2021: 73%, 2024: 80%) but substantially below in bear years (2022: 57.5%). A model must demonstrably outperform the unconditional base rate in its selected cohort to add value. The baseline "apply to everything" strategy already earns roughly 65–73% positive outcomes — any model must beat this unconditional rate with statistical confidence before it warrants deployment.

---

## Return Distribution

### Confirmed statistics by year

**2021** — Most complete return statistics available

| Statistic | Value | Source |
|-----------|------:|--------|
| Total Mainboard IPOs | 63 | Multiple sources |
| Positive listings | 46 (73.0%) | Multiple sources |
| Negative listings | 17 (27.0%) | Multiple sources |
| Mean listing return (at OPEN) | **~31.3–31.9%** | Industry reports |
| Median listing return | **~14.7%** | Research summary |
| Max listing return | **+267.2%** (Sigachi Industries) | Named source |
| Min listing return | **−27.4%** (Paytm) | Named source |
| % above +5% | Not confirmed at year level | — |
| % above +10% | Not confirmed at year level | — |
| % above +20% | Not confirmed at year level | — |
| % below 0% | 27.0% | Confirmed |
| % below −5% | Not confirmed | — |

**2022** — Second most complete

| Statistic | Value | Source |
|-----------|------:|--------|
| Total Mainboard IPOs | 40 | Multiple sources |
| Positive listings | 23 (57.5%) | Multiple sources |
| Negative listings | ~15 (~37.5%) | Multiple sources |
| Mean listing return | **~9.37%** | Industry reports |
| Median listing return | **~3.5%** | Research summary |
| Max listing return | **~51%** (Hariom Pipe Industries) | Named source |
| Min listing return | LIC (−8.1%); Delhivery worse | Named sources |
| % below 0% | ~37.5% | Estimated from count |

**2024** — Count and rate confirmed; distribution statistics partial

| Statistic | Value | Source |
|-----------|------:|--------|
| Total Mainboard IPOs | 93 | Multiple sources |
| Positive listings | 74 (79.6%) | Multiple sources |
| Negative listings | 19 (20.4%) | Multiple sources |
| Mean listing return | **~28.2%** | Trendlyne |
| Max listing return | **~181%** (Vibhor Steel Tubes) | Named source |
| % below 0% | 20.4% | Confirmed |

**2019 and 2020** — Lower confidence; counts disputed

| Year | Mean return (at open) | Mean return (at close) | Positive rate | Note |
|------|-----------------------|------------------------|--------------|------|
| 2019 | ~15.3% | ~19.2% | ~69% | Source: one academic/research study; count disputed |
| 2020 | ~14.3% | ~15.1% | ~75% | Same study; count disputed (44 vs 69) |

**2018** — Return distribution NOT established
Narrative evidence only: "7 of 10 largest IPOs were in red by September 2018." This reflects performance through September, not listing-day returns, and covers only the 10 largest — not representative of the year.

**2023** — Partial
Median return ~16.5% confirmed from one source. No positive/negative count confirmed.

---

### Estimated full-period return distribution (2018–2024)

Using confirmed year-level data (2021, 2022, 2024) as anchors and research-based estimates for other years:

| Return bucket | Estimated % of all IPOs | Confidence |
|---------------|------------------------|-----------|
| Below −20% | ~4–6% | Low confidence |
| −20% to −10% | ~6–8% | Low confidence |
| −10% to 0% | ~18–22% | Medium confidence |
| 0% to +5% | ~10–13% | Medium confidence |
| +5% to +10% | ~8–10% | Medium confidence |
| +10% to +20% | ~14–17% | Medium confidence |
| +20% to +50% | ~16–20% | Medium confidence |
| Above +50% | ~10–15% | Low confidence |

**Mean return (estimated): ~18–22%** (bull years pull this up; bear years pull it down)
**Median return (estimated): ~8–14%** (more robust; estimated from available medians)
**Standard deviation: ~35–50%** (wide; bimodal distribution; bull/bear regime drives it)

> All values in this section are research-derived estimates and will be replaced by computed statistics once the per-row dataset is built.

---

### Distribution shape observations (from confirmed data)

1. **Strongly right-skewed.** The maximum return in any given year is 100–270%; the minimum is typically −25 to −35%. The distribution is not normal — it has a heavy right tail.

2. **Regime-dependent.** The distribution shifts substantially between bull and bear market periods:
   - 2021 (bull): mean ~31%, median ~15%, 73% positive
   - 2022 (rate hikes): mean ~9%, median ~3.5%, 57.5% positive
   A model trained only on bull-year data will massively overestimate expected returns.

3. **A small number of outliers drive the mean.** In 2021, Sigachi (+267%), Paras (+181%), Latent View (+148%) are extreme observations. Without these, the mean would be substantially lower. The median (~14.7%) is a more robust central tendency measure.

4. **Negative listing risk is real and non-trivial.** Even in the best year (2024), 20% of IPOs listed below issue price. In 2022, ~37% did. An APPLY strategy must account for 20–40% probability of immediate loss in any given year.

---

## Subscription Coverage

| Year | Subscription data expected | Confirmed individual records |
|------|---------------------------|---------------------------:|
| 2018 | ~27 usable records (est.) | 0 |
| 2019 | ~27 usable records (est.) | 0 |
| 2020 | ~35–55 usable records (est.) | 0 |
| 2021 | ~57 usable records (est.) | 3 (Zomato, Paytm, Nykaa) |
| 2022 | ~36 usable records (est.) | 1 (LIC) |
| 2023 | ~54 usable records (est.) | 0 |
| 2024 | ~84 usable records (est.) | 2 (Bajaj Housing, Sigachi) |
| **Total** | **~320–340 expected** | **6 confirmed** |

**Coverage: 2% (6/~340) — insufficient for any analysis. Requires systematic collection.**

### Key subscription observations from confirmed records

| IPO | Year | Retail Sub (x) | NII Sub (x) | QIB Sub (x) | Total Sub (x) | Listing return | Insight |
|-----|------|---------------|-------------|-------------|---------------|----------------|---------|
| Sigachi Industries | 2021 | ~28.7 | ~228 | ~247.7 | ~101.9 | +267.2% | Extreme subscription → extreme listing gain |
| Paytm | 2021 | ~1.7 | ~24.2 | ~179.0 | ~89.1 | −27.4% | High QIB, low retail → loss; high QIB does not guarantee gain |
| Nykaa | 2021 | ~12.2 | ~112 | ~92.0 | ~82.0 | +96.1% | Strong subscription → strong gain |
| Zomato | 2021 | ~7.5 | ~32.0 | ~51.8 | ~38.2 | +65.8% | Moderate subscription → moderate-strong gain |
| LIC | 2022 | ~1.99 | ~2.91 | ~2.83 | ~2.95 | −8.1% | Low subscription (just ~3x) → listing loss |
| Bajaj Housing Finance | 2024 | ~7.4 | ~41.6 | ~208.7 | ~63.6 | +114.3% | Very high QIB → strong gain |

**Preliminary observation (6 records, not statistically significant):** Very high total subscription (>50x) appears to correlate with strong positive listing in this sample. Very low subscription (~3x) correlates with negative listing. The Paytm case is instructive — extremely high QIB but near-zero retail enthusiasm; listing was a major loss. Retail subscription may be a stronger signal than QIB-alone.

---

## Listing Price Confidence

### Why Bhav Copy OPEN is the canonical target

The `OPEN` field in the NSE/BSE daily Bhav Copy for a stock's first trading day is:

1. **Exchange-certified.** Produced by NSE/BSE from actual order matching during the Special Pre-Open Session. Not derived or estimated.
2. **Point-in-time.** The value is fixed at the moment of market open on listing day. It cannot change retroactively.
3. **Publicly archived.** NSE Bhav Copies are freely downloadable for all trading days going back 10+ years.
4. **Unambiguous.** The pre-open equilibrium is the same price regardless of whether the stock is on NSE or BSE (within 0.5%; cross-check validates this).
5. **Not the same as Day-1 close.** The close price is influenced by 6 hours of subsequent trading. It is NOT the listing event price.

### Confirmed methodology

All 35 approximately confirmed listing prices in this research sprint are **not primary-verified** — they were sourced from news reports and analyst summaries. They are correct in direction (positive/negative) and approximately correct in magnitude but should not be used as training labels.

**What is confirmed:** The Bhav Copy OPEN field is unambiguously the right field. Its collection is mechanical once the universe list (G1) is complete.

**What is pending:** Actual Bhav Copy download for all 341+ listing dates.

---

## Data Gaps

| Gap | Impact on next steps | Priority |
|-----|---------------------|----------|
| Complete IPO universe (G1) — 341+ rows | **Blocks all gates** | 🔴 Critical |
| NSE Bhav Copy listing prices (G2) — dependent on G1 | Blocks G4 final calculation | 🔴 Critical |
| Final subscription data (G3) — dependent on G1 | Blocks feature computation | 🔴 Critical |
| 2020 IPO count (44 vs. 69) — discrepancy unresolved | Affects 2020 base rate reliability | 🟡 High |
| 2018 positive/negative split — unknown | Affects 2018 contribution to aggregate | 🟡 High |
| 2023 positive/negative split — not confirmed | Affects 2023 aggregate base rate | 🟡 High |
| Market data (Nifty/VIX) — G5 | Independent; can be done in parallel | 🟢 Medium |
| Basis of Allotment sample (G6) | Validates allotment formula | 🟢 Medium |
| PDF parsing prototype (G7) | Validates fundamentals extraction feasibility | 🟢 Medium |
| Full subscription year-level averages | Cannot segment analysis by subscription level | 🟡 High |
| Historical GMP time-series | Confirmed excluded from backtest (design decision) | ✅ Resolved |

---

## Recommendation: Proceed to G5/G6?

### GO / HOLD decision

**HOLD on G5/G6 until G1 is unblocked. Immediate parallel action possible.**

The rationale:

**Why not a full GO:**
- Gates G1–G3 are methodologically complete but executionally empty — less than 10% of required records are confirmed
- G4 base rate is computed from aggregate statistics, not from the per-row dataset
- Model training cannot begin without the per-row dataset

**Why not a full HOLD:**
- The methodology is correct and confirmed
- The access path is clear: IPOMatrix subscription OR systematic Bhav Copy collection
- G5 (market data download) is fully independent and can be done immediately at zero cost
- The aggregate base rate findings are valuable and actionable:
  - Unconditional positive rate: **65–73%**
  - The strategy's 70% threshold is at the edge of the unconditional base rate — model must add genuine signal
  - Bear-year rate (2022: 57.5%) confirms the strategy cannot be "always apply"

### Specific recommendation

| Task | Recommendation |
|------|---------------|
| G5 market data (Nifty/VIX download) | **DO NOW** — independent, free, ~1–2 hours |
| G1 full collection (IPOMatrix or Bhav Copy method) | **DO NEXT** — gates everything else; decide on paid vs. manual |
| G2 Bhav Copy listing prices | **After G1** — mechanical; ~10 hours |
| G3 subscription collection | **After G1** — requires per-page extraction or paid data |
| G6 BoA sample (50 IPOs) | **After G1** — use BoA PDFs to validate allotment formula |
| G7 PDF parsing prototype | **Parallel with G5** — independent; validate feasibility before committing |
| Proceed to fundamentals / RHP extraction (G6 per plan) | **HOLD** — until G1–G4 per-row dataset exists |
| Proceed to model training | **HOLD** — until G1–G5 complete |

### Decision summary

> **GO for G5 (market data) and G7 (PDF parsing prototype) immediately.**
> **HOLD for full G6 (BoA collection) and all modeling until G1 per-row dataset is built.**
> **G1 is the single bottleneck. Resolve it by subscribing to IPOMatrix or beginning systematic Bhav Copy collection.**

---

## Appendix: Data Collection Status Snapshot

*As of 2026-09-04. To be updated as data is collected.*

| Gate | Description | Status |
|------|-------------|--------|
| G1 — IPO universe | Per-row list of all ~341+ Mainboard IPOs | 🟡 Methodology complete; 9% collected |
| G2 — Listing prices | Bhav Copy OPEN for all listing dates | 🟡 Methodology complete; 0% primary-collected |
| G3 — Final subscription | QIB/NII/Retail/Total at T3 close | 🟡 Methodology complete; 2% collected |
| G4 — Base rate | Computed from G1+G2 data | 🟡 Year-level aggregate computed; per-row pending |
| G5 — Market data | Nifty/VIX daily series | ⬜ Not started; path clear |
| G6 — BoA sample | 50 Basis of Allotment PDFs | ⬜ Not started |
| G7 — PDF parsing prototype | Fundamentals from 10 RHP PDFs | ⬜ Not started |
