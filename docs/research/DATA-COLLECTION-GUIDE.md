# Data Collection Guide — Phase 1 Gates
**Version:** 1.0 | **Date:** 2026-09-03
**Purpose:** Step-by-step instructions for the first data collection sprint.
**Prerequisite:** Read DATA-FEASIBILITY-REPORT.md and SOURCE-MATRIX.md first.

This document tells the data collection agent exactly what to do, in what order,
and what outputs each gate must produce. No modeling until G1–G4 are complete.

---

## Gate G1 — IPO Universe List (2018–2024 Mainboard)

**Output file:** `docs/research/data/ipo_universe_raw.csv`

**Required columns:**
```
ipo_id            (sequential integer, our internal ID)
company_name
nse_symbol        (if listed on NSE; else blank)
bse_code          (if listed on BSE; else blank)
exchange          (NSE | BSE | BOTH)
segment           (MAINBOARD)
open_date         (YYYY-MM-DD)
close_date        (YYYY-MM-DD)
listing_date      (YYYY-MM-DD)
issue_price       (₹, numeric)
price_band_low    (₹, numeric)
price_band_high   (₹, numeric)
lot_size          (shares per lot, integer)
min_application_amount (₹, numeric = lot_size × issue_price)
issue_size_cr     (total issue size in crores, numeric)
fresh_issue_cr    (fresh issue portion in crores, numeric)
ofs_cr            (OFS portion in crores, numeric)
retail_quota_pct  (%, numeric)
qib_quota_pct     (%, numeric)
nii_quota_pct     (%, numeric)
sebi_nii_regime   (PRE_2022 | POST_2022; based on close_date)
timeline_regime   (T6 | T3; T3 applies to close_date >= 2023-12-01)
source            (e.g. chittorgarh_2021_page + nse_equity_master)
data_quality      (VERIFIED_PRIMARY | VERIFIED_SECONDARY | UNVERIFIED_SECONDARY)
notes             (any flags, anomalies)
```

**Collection method:**
1. Start with Chittorgarh year-wise Mainboard IPO tables (2018–2024)
2. For each IPO, cross-reference issue terms with NSE/BSE IPO pages
3. Verify issue price and listing date on NSE/BSE equity master
4. Compute derived fields (min_application_amount, sebi_nii_regime, timeline_regime)
5. Flag any IPO where open_date is unavailable or issue_price is unverifiable as UNVERIFIED

**Acceptance criteria:**
- At least 400 records for 2018–2024 Mainboard IPOs
- issue_price verified (VERIFIED_PRIMARY or VERIFIED_SECONDARY) for ≥90% of records
- listing_date verified for ≥95% of records
- Zero records with fabricated data; MISSING preferred over fabrication

---

## Gate G2 — Listing Prices (Bhav Copy OPEN on Day 1)

**Output file:** `docs/research/data/listing_prices_raw.csv`

**Required columns:**
```
ipo_id            (foreign key to ipo_universe_raw.csv)
company_name
nse_symbol
listing_date
bhav_open         (₹; OPEN price from NSE Bhav Copy on listing_date)
bhav_high         (₹; HIGH price from NSE Bhav Copy on listing_date)
bhav_low          (₹; LOW price from NSE Bhav Copy on listing_date)
bhav_close        (₹; CLOSE price from NSE Bhav Copy on listing_date)
bhav_volume       (shares traded on listing date)
issue_price       (₹; copy from ipo_universe for easy validation)
listing_return    (computed: (bhav_open - issue_price) / issue_price)
positive_listing  (boolean: bhav_open > issue_price)
source_exchange   (NSE | BSE)
source_file       (e.g. "NSE_Bhav_2021-11-10.csv")
data_quality      (VERIFIED_PRIMARY | MISSING)
notes
```

**Collection method:**
1. For each IPO in G1 with a valid listing_date, download NSE daily Bhav Copy for that date
2. NSE Bhav Copies are available at: nseindia.com (Historical Data section) as daily ZIP/CSV
3. Match by NSE symbol (nse_symbol from G1) or company name
4. If NSE Bhav Copy is unavailable or symbol mismatch, try BSE Bhav Copy as fallback
5. Record the source_exchange and source_file for every row
6. Mark any IPO where Day 1 Bhav Copy cannot be found as data_quality = MISSING

**Acceptance criteria:**
- listing_return computed for ≥95% of IPOs in G1 universe
- bhav_open verified from Bhav Copy (not from aggregator site "listing price")
- Data quality VERIFIED_PRIMARY for all records sourced directly from Bhav Copy
- Do NOT use Chittorgarh / InvestorGain listing price column as the canonical value
  (use it only as a sanity check cross-reference)

---

## Gate G3 — Final Subscription Data

**Output file:** `docs/research/data/subscription_final_raw.csv`

**Required columns:**
```
ipo_id
company_name
close_date
retail_subscription_x      (times oversubscribed; numeric)
nii_subscription_x         (times oversubscribed; numeric)
qib_subscription_x         (times oversubscribed; numeric)
total_subscription_x       (times oversubscribed; numeric)
snii_subscription_x        (post-2022 only; else NULL)
bnii_subscription_x        (post-2022 only; else NULL)
retail_oversubscribed      (boolean)
nii_oversubscribed         (boolean)
qib_oversubscribed         (boolean)
any_category_under_1x      (boolean)
retail_allotment_prob      (computed: min(1.0, 1/max(1, retail_subscription_x)))
source_primary             (e.g. chittorgarh_2021_ipo_page)
source_secondary           (e.g. investorgain_2021_tracker; for cross-check)
cross_source_agreement     (boolean: do primary and secondary agree within 5%?)
data_quality               (VERIFIED_SECONDARY | CONFLICTING | MISSING)
notes
```

**Collection method:**
1. For each IPO in G1, navigate to its individual page on Chittorgarh for final subscription
2. Record QIB/NII/Retail/Total subscription values
3. Cross-reference with InvestorGain for the same IPO
4. If the two sources differ by >5% on any category, flag as CONFLICTING and note both values
5. For post-Sept-2022 IPOs, record sNII and bNII separately if available
6. Compute retail_allotment_prob from SEBI formula

**Acceptance criteria:**
- Subscription data (at minimum: total_subscription_x) for ≥80% of G1 IPOs
- Category breakdown (QIB/NII/Retail) for ≥70% of G1 IPOs
- Cross-source agreement documented for all records where two sources were consulted
- CONFLICTING flag used where sources disagree; do not silently prefer one

---

## Gate G4 — Base Rate Computation

**Output file:** `docs/research/data/base_rate_analysis.md`

**Once G1–G3 are complete, compute and document:**

```
Total IPOs in universe: N
IPOs with verified listing price (bhav_open): N_price
IPOs with positive listing (bhav_open > issue_price): N_positive
Base rate (all years): N_positive / N_price

Year-wise breakdown:
  2018: count, positive_count, positive_pct, mean_return, median_return, p10_return, p90_return
  2019: ...
  2020: ...
  2021: ...
  2022: ...
  2023: ...
  2024: ...

Subscription-stratified:
  total_sub_x < 10: mean_return, positive_pct
  10 <= total_sub_x < 50: mean_return, positive_pct
  total_sub_x >= 50: mean_return, positive_pct
  any_category_under_1x = True: mean_return, positive_pct

Market regime:
  nifty_return_30d > 5%: mean_return, positive_pct
  nifty_return_30d between -2% and 5%: mean_return, positive_pct
  nifty_return_30d < -2%: mean_return, positive_pct

Apply-Every-IPO baseline:
  Assume retail minimum lot, one application per IPO
  Apply retail_allotment_prob to simulate allotment
  Compute: profit per application (gross, net after STT+DP, pre-tax)
  Report: mean profit/application, total profit over period, hit rate, max loss
```

**Acceptance criteria:**
- Base rate computed from actual data, not from search results
- Year-wise breakdown completed
- Apply-Every-IPO baseline computed with allotment simulation
- Document any significant findings that challenge or confirm the strategy assumptions

---

## Gate G5 — Market Data Collection

**Output file:** `docs/research/data/market_data.csv`

**Required columns:**
```
date              (YYYY-MM-DD, daily, 2017-01-01 to present)
nifty50_close     (Nifty 50 index close)
nifty50_open      (optional)
india_vix_close   (India VIX daily close; available from 2008)
nifty_bank_close  (optional; for sector features)
nifty_it_close    (optional; for sector features)
```

**Source:** NSE India historical index data downloads (free, no API needed)
- Nifty 50: nseindia.com > Market Data > Historical Data > Indices
- India VIX: nseindia.com > Market Data > Historical Data > VIX

**Derived features computed at feature-layer time (not stored raw):**
```
nifty_return_7d(t)  = (nifty50_close[t] - nifty50_close[t-7]) / nifty50_close[t-7]
nifty_return_30d(t) = (nifty50_close[t] - nifty50_close[t-30]) / nifty50_close[t-30]
```

**Acceptance criteria:**
- Daily data from 2017-01-01 (to allow 30-day lookback for 2018 IPOs)
- No gaps greater than 3 trading days (holidays expected; extended gaps flag an error)

---

## Gate G6 — Basis of Allotment Sample Collection

**Output file:** `docs/research/data/boa_sample/` (directory of PDFs) +
               `docs/research/data/boa_sample_index.csv`

**Purpose:** Validate the SEBI allotment formula approximation against actual data.

**Sample strategy:** Collect BoA PDFs for 50 IPOs sampled across:
- All 7 years (2018–2024), ~7 per year
- Range of subscription levels: some <10x, some 10–50x, some >50x retail
- Mix of registrars (KFintech, Link Intime, others)

**For each BoA, extract to boa_sample_index.csv:**
```
ipo_id
company_name
listing_date
registrar
total_retail_applications_received
retail_shares_offered
successful_retail_applicants
allotment_ratio_retail             (successful / total applications)
actual_retail_allotment_prob       (= allotment_ratio_retail)
formula_retail_allotment_prob      (= min(1.0, 1 / max(1, retail_sub_x)))
formula_vs_actual_error            (actual - formula)
total_nii_applications_received
nii_regime                         (PRE_2022 | POST_2022)
source_url                         (URL of BoA PDF)
pdf_filename                       (local filename)
```

**Acceptance criteria:**
- 50 BoA PDFs collected
- For all 50: at minimum total_retail_applications and successful_retail_applicants extracted
- formula_vs_actual_error computed and analysed (mean absolute error should be <5%pp)
- If mean error >5%pp, the allotment formula must be revisited before model training

---

## Gate G7 — PDF Parsing Prototype

**Output:** Working Python script (saved to `docs/research/scratch/pdf_parser_test.py`) +
           extracted data for 10 IPOs (CSV)

**Purpose:** Validate that RHP PDF parsing is feasible before committing to full extraction.

**Test set:** Select 10 IPOs from the G1 universe:
- 2 from 2018, 2 from 2020, 2 from 2021, 2 from 2022, 2 from 2023
- Mix of large and small IPOs
- Mix of sectors

**For each IPO, attempt to extract from the RHP/Prospectus (via SEBI EFTS):**
```
revenue_latest_cr
revenue_yr1_cr
revenue_yr2_cr
pat_latest_cr
eps_latest
debt_cr
promoter_holding_pre_pct
ofs_pct
stated_peer_median_pe
issuer_pe_at_issue_price
source_document          (SEBI EFTS URL)
extraction_method        (automated | manual_assist | failed)
confidence               (HIGH | MEDIUM | LOW)
notes
```

**Acceptance criteria:**
- Successfully extract core financials (revenue, PAT, EPS) from ≥7 of 10 test IPOs
- Document failure modes for the remaining cases
- If success rate <70%, escalate: manual extraction or commercial data provider needed for full run
- This gate determines whether PDF parsing is a viable path or requires alternative data sources

---

## Important Behavioral Rules for Data Collection

1. **Never fabricate.** If data is unavailable, mark `data_quality = MISSING`. Do not impute,
   estimate, or fill in values without marking them as inferred.

2. **Record provenance.** Every value must have a source field. "I looked it up" is not a source.

3. **Do not use today's data for historical features.** If you look up an IPO's issue price on
   a company's current investor relations page, note that this could have been updated since the
   IPO. Prefer DRHP/RHP as the authoritative source.

4. **Cross-validate.** For critical fields (issue_price, listing_price, subscription), compare
   at least two sources where possible.

5. **Preserve conflicts.** If two sources give different values, record both values and flag
   CONFLICTING. Do not silently choose one.

6. **No look-ahead.** Market data features must use dates before the relevant decision timestamp.
   Do not accidentally include the Nifty return on listing day itself as an input feature.

7. **Do not start modeling.** These gates produce a dataset. Modeling begins only after the
   dataset is complete and the base rate is computed.

---

*This guide is a living document. Update it if new sources or methods are found during collection.*
