# G1-G4 Data Quality Report
**Version:** 1.0 | **Date:** 2026-09-04

---

## 1. Coverage Matrix by Field

Fields are assessed across all target IPOs (estimated universe: 341–406 Mainboard IPOs, 2018–2024 CY).

| Field | Available (records) | Missing (records) | Coverage % | Quality class | Notes |
|-------|--------------------:|------------------:|-----------:|--------------|-------|
| **Company name** | ~341–406 (aggregate) | 0 at aggregate level | 100% (aggregate) | SECONDARY_VERIFIED | Year-level counts confirmed; per-row names require paid data |
| **Listing date** | ~35 (individual confirmed) | ~306–371 | ~9% (per-row) | PRIMARY_VERIFIED: 0; SECONDARY_VERIFIED: 35 | Aggregate year-count confirmed; per-row requires data collection |
| **Issue price** | ~35 (individual confirmed) | ~306–371 | ~9% (per-row) | SECONDARY_VERIFIED: 35 | Same status as listing date |
| **Listing price (Bhav OPEN)** | ~35 (approximate, secondary) | ~306–371 | ~9% (per-row) | PRIMARY_VERIFIED: 0; SECONDARY_VERIFIED (approx): 35 | No direct Bhav Copy lookup yet done; all approximate |
| **Listing return (%)** | ~35 (from confirmed records) | ~306–371 | ~9% (per-row) | SECONDARY_VERIFIED: 35 | Computed from secondary-verified prices |
| **NSE symbol** | ~35 (noted) | ~306–371 | ~9% | SECONDARY_VERIFIED | Needs G1 universe collection |
| **Exchange** | ~35 | ~306–371 | ~9% | SECONDARY_VERIFIED | |
| **Open date** | ~35 | ~306–371 | ~9% | SECONDARY_VERIFIED | |
| **Close date** | ~35 | ~306–371 | ~9% | SECONDARY_VERIFIED | |
| **Lot size** | ~35 | ~306–371 | ~9% | SECONDARY_VERIFIED | |
| **Issue size** | ~35 | ~306–371 | ~9% | SECONDARY_VERIFIED | |
| **Price band** | ~35 | ~306–371 | ~9% | SECONDARY_VERIFIED | |
| **QIB subscription (x)** | 6 (individual) | ~335–400 | ~2% (per-row) | SECONDARY_VERIFIED: 6 | |
| **NII subscription (x)** | 6 | ~335–400 | ~2% | SECONDARY_VERIFIED: 6 | |
| **Retail subscription (x)** | 6 | ~335–400 | ~2% | SECONDARY_VERIFIED: 6 | |
| **Total subscription (x)** | 6 | ~335–400 | ~2% | SECONDARY_VERIFIED: 6 | |
| **sebi_nii_regime flag** | Derivable from close_date once universe built | — | — | DERIVED | Formula: close_date >= 2022-09-01 → POST_2022 |
| **timeline_regime flag** | Derivable from close_date | — | — | DERIVED | Formula: close_date >= 2023-12-01 → T3 |
| **Nifty/VIX historical** | Full series (aggregate) | 0 | ~100% | PRIMARY_VERIFIED | NSE historical data; freely downloadable |
| **Fundamentals (from RHP)** | 0 per-row | All | 0% | NOT_STARTED | PDF parsing not yet started |
| **Basis of Allotment** | 0 systematic | All | 0% | NOT_STARTED | Collection not yet started |

---

## 2. Coverage by Year (Per-Row Status)

This table shows the current state of individual IPO records, not aggregate statistics.

| Year | Total IPOs (est.) | Records with issue price (confirmed) | Records with listing price (approx.) | Records with any subscription data | Complete rows (all 3 fields) |
|------|------------------:|-------------------------------------:|-------------------------------------:|------------------------------------:|-----------------------------:|
| 2018 | ~42 | 4 | 4 | 0 | 0 |
| 2019 | ~39 | 0 | 0 | 0 | 0 |
| 2020 | ~44–69 | 7 | 7 | 0 | 0 |
| 2021 | 63 | 12 | 12 | 3 | 3 |
| 2022 | 40 | 2 | 2 | 1 | 1 |
| 2023 | 60 | 0 | 0 | 0 | 0 |
| 2024 | 93 | 10 | 10 | 2 | 2 |
| **Total** | **341–406** | **35** | **35** | **6** | **6** |

**Overall per-row coverage:**
- Universe confirmed: ~9% by records (35/341+)
- Listing price confirmed (primary): **0%**
- Listing price confirmed (secondary/approximate): ~9%
- Subscription confirmed: ~2% (6/341+)
- Complete rows (all fields): ~2% (6/341+)

---

## 3. Aggregate Statistics Coverage (Year-Level)

At the **year level**, the following statistics are confirmed from independent sources. These are usable for G4 base rate calculation even without complete per-row data.

| Year | IPO count | Positive (count) | Negative (count) | Positive rate | Avg return | Median return | Source quality |
|------|----------:|----------------:|----------------:|--------------|-----------|--------------|---------------|
| 2018 | ~42 | Unknown | Unknown | Not confirmed | Not confirmed | Not confirmed | UNVERIFIED |
| 2019 | ~39 | ~27 | ~12 | ~69% | ~15.3% (open) | Not confirmed | SECONDARY_VERIFIED (one study; count inconsistency) |
| 2020 | ~44–69 | ~33 | ~11 | ~75% | ~14.3% (open) | Not confirmed | SECONDARY_VERIFIED (count disputed) |
| 2021 | 63 | 46 | 17 | **73.0%** | ~31.3–31.9% | ~14.7% | SECONDARY_VERIFIED (multiple sources agree) |
| 2022 | 40 | 23 | ~15 | **57.5%** | ~9.37% | ~3.5% | SECONDARY_VERIFIED (multiple sources agree) |
| 2023 | 60 | Not confirmed | Not confirmed | Not confirmed | Not confirmed | ~16.5% (median) | PARTIAL — median only confirmed |
| 2024 | 93 | **74** | **19** | **79.6%** | ~28.2% | Not confirmed | SECONDARY_VERIFIED (multiple sources agree) |

**Notes on confidence:**
- 2021, 2022, 2024: **Highest confidence** — count, positive/negative breakdown, and return statistics confirmed by 3+ independent sources
- 2019, 2020: **Medium confidence** — positive rate confirmed but count disputed; one source cited; count inconsistency not resolved
- 2023: **Partial** — count confirmed; positive/negative breakdown not independently confirmed; median return figure from one source
- 2018: **Low confidence** — only narrative evidence ("7 of 10 biggest in red"); no reliable positive/negative count

---

## 4. Source Quality Classification

### By field type

| Source type | Fields covered | Quality class | Limitations |
|-------------|---------------|--------------|-------------|
| NSE/BSE Bhav Copy (direct download) | Listing price (OPEN), subsequent prices | **PRIMARY_VERIFIED** | Requires knowing the symbol and listing date first; not yet collected |
| SEBI EFTS filings (DRHP/RHP PDFs) | Issue terms, fundamentals, valuation, peers | **PRIMARY_VERIFIED** | PDF-only; requires parsing; not yet collected |
| Named financial news reports (ET, Mint, BS) | Issue price, listing price for notable IPOs | **SECONDARY_VERIFIED** | Named, multiple sources; approximate prices |
| Industry annual reports (EY, PRIME Database reports) | Year-level counts and statistics | **SECONDARY_VERIFIED** | Aggregate only; methodology may vary |
| IPO tracking websites (Chittorgarh, InvestorGain) | Full subscription and listing data | **SECONDARY_VERIFIED** | Paywalled for bulk; cross-source agreement recommended |
| AI-generated search summaries | Aggregated statistics | **UNVERIFIED** | Must not be used as primary; requires cross-reference |

### Source quality decisions

For this research sprint, statistics that are:
- Cited by 3+ independent sources with consistent values → **SECONDARY_VERIFIED**
- Cited by 2 sources with consistent values → **SECONDARY_VERIFIED** (with flag)
- Cited by 1 source only → **UNVERIFIED** (noted as such)
- Computed from primary exchange files → **PRIMARY_VERIFIED** (none achieved yet)

---

## 5. Known Limitations for Later Modeling

### L1 — Per-row dataset not built (Critical)

The full row-level dataset of 341–406 IPOs does not yet exist. G4 base rates are computed from aggregate statistics, not from the per-row dataset. Before model training, the per-row dataset must be built via paid data access or systematic collection.

**Impact:** Cannot train a model. Cannot compute full distribution statistics. Cannot validate per-feature correlations.

### L2 — 2020 count discrepancy (High)

Two different counts exist for 2020 Mainboard IPOs: 44 and 69. The discrepancy has not been resolved. The positive-rate statistics use 44 as the base; if the true count is 69, the 75% positive rate may be overstated.

**Impact:** Year-2020 base rate estimate may be wrong. Affects aggregate base rate.

### L3 — 2018 base rate unknown (High)

No reliable positive/negative count exists for 2018. Only narrative evidence ("7 of 10 biggest were in red by September 2018") exists, and this refers to performance through September (not listing day), and only for the 10 largest IPOs.

**Impact:** 2018 is the most uncertain year. If included in aggregate base rate, it introduces significant estimation error.

### L4 — Listing prices are approximations (High for individual records)

All 35 confirmed individual listing prices are secondary-sourced approximations, not primary Bhav Copy values. They are usable for illustration and sanity-checking but cannot be used as training labels.

**Impact:** 0 training-quality listing prices are currently available.

### L5 — Subscription data is minimal (High)

Only 6 subscription records are confirmed individually. No year-level aggregate subscription statistics (e.g., average subscription multiple by year) have been confirmed from primary sources.

**Impact:** Cannot yet assess subscription coverage quality or compute subscription-stratified base rates.

### L6 — 2023 positive/negative split unconfirmed (Medium)

The 2023 positive rate is not independently confirmed. Only the median return (~16.5%) is confirmed. The IPO count (60) is confirmed.

**Impact:** 2023 base rate estimated from median return direction only; may be materially different from actual count.

### L7 — Anchor investor inclusion in QIB varies (Medium)

QIB subscription multiples reported on different platforms may or may not include anchor investor allocations. This creates up to 2–3× discrepancy in QIB multiples between platforms.

**Impact:** QIB subscription feature will have systematic noise if not normalized. Resolution requires documenting the inclusion rule per data source.

### L8 — Aggregator GMP data excluded (Low — confirmed)

Historical GMP is excluded from all training data per the feasibility report decision. This is a confirmed design choice, not a data quality limitation.

---

## 6. Data Quality Decision Matrix

This table summarizes which data is usable at each stage:

| Use case | Current usability | What's needed |
|----------|------------------|---------------|
| G4 year-level base rate calculation | ✅ Partial — 2021, 2022, 2024 reliable; others uncertain | Accept current for initial estimate |
| G4 full distribution statistics | ❌ Not yet — requires per-row dataset | Complete G1 + G2 data collection |
| Model training | ❌ Not yet | Complete G1 + G2 + G3 + G5 + G7 data collection |
| Allotment model validation | ❌ Not yet | G6 (BoA collection) required |
| Subscription-stratified analysis | ❌ Not yet | G3 full collection required |
| Market regime analysis | ✅ Nifty/VIX freely available | Download and compute rolling features |

---

## 7. Priority Data Gaps

Ordered by impact on the project:

1. **Per-row IPO universe (G1)** — Everything depends on this. Subscribe to IPOMatrix or build from Bhav Copy. **Blocks all subsequent gates.**
2. **NSE Bhav Copy listing prices (G2)** — Dependent on G1. After G1 is done, Bhav Copy collection is largely mechanical. ~10 hours to complete.
3. **Subscription data (G3)** — Dependent on G1. Either IPOMatrix or per-page collection. ~20–40 hours.
4. **Market data (G5)** — Independent of G1–G3. NSE index data is freely downloadable. ~1–2 hours. Should be done now.
5. **BoA sample (G6)** — Validates allotment formula. ~10 hours for 50 IPOs.
6. **PDF parsing prototype (G7)** — Tests fundamentals extraction. ~4–6 hours for 10 IPOs.
7. **2020 count discrepancy** — Resolve 44 vs. 69 count before finalizing universe.
8. **2018 base rate** — Confirm positive/negative split for 2018 from Chittorgarh data.
