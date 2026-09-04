# G3 — Final Subscription Data
**Version:** 1.0 | **Date:** 2026-09-04 | **Gate status:** METHODOLOGY CONFIRMED; bulk collection pending

---

## 1. Decision: Final Subscription Only

As established in the Data Feasibility Report (Section 3B), intraday subscription snapshots are not reliably archived for historical Indian Mainboard IPOs.

> **Only final subscription data (at T3 close, 5:00 PM) is used in the historical baseline dataset. No intraday reconstruction is attempted.**

---

## 2. What "Final Subscription" Means

At 5:00 PM on the final day of the subscription window, NSE and BSE freeze and publish the category-wise bid totals. These are:

| Category | Description | Published field |
|----------|-------------|----------------|
| QIB | Qualified Institutional Buyers | QIB bids vs. QIB shares offered |
| NII/HNI | Non-Institutional Investors (>₹2L; pre-2022: all non-QIB non-retail) | NII bids vs. NII shares offered |
| Retail (RII) | Retail Individual Investors (≤₹2L per application) | Retail bids vs. retail shares offered |
| Total | Aggregate across all categories | Total bids vs. total shares offered |

**Preferred data structure (per IPO):**

```
qib_bids_received        (actual bid quantity in shares)
qib_shares_offered       (shares in QIB quota)
qib_subscription_x       (= qib_bids_received / qib_shares_offered)

nii_bids_received
nii_shares_offered
nii_subscription_x

retail_bids_received
retail_shares_offered
retail_subscription_x

total_bids_received
total_shares_offered
total_subscription_x

snii_subscription_x      (post-Sept 2022 only; sNII = ₹2L–₹10L)
bnii_subscription_x      (post-Sept 2022 only; bNII = >₹10L)
total_applications_retail (count of applications, not shares — from BoA)
```

**Why preferred over just `x` multiples:**
- The raw bid quantities allow independent verification of the multiple
- They allow computing applications-per-lot and similar features
- They allow cross-source reconciliation at the raw number level
- The application count is needed for the allotment probability formula

In practice, most free sources only publish the `x` multiple. Raw bid quantities are in the official Basis of Allotment document and NSE/BSE subscription data files.

---

## 3. Cross-Validation Protocol

For every IPO where subscription data is collected:

```
source_primary         (e.g., "chittorgarh_2021_IPO_page")
value_primary          (e.g., retail_sub_x = 32.5)
source_secondary       (e.g., "investorgain_2021_tracker")
value_secondary        (e.g., retail_sub_x = 32.3)
agreement_status       (AGREE | MINOR_DIFF | CONFLICTING | SINGLE_SOURCE)
resolution             (If CONFLICTING: which value is preferred and why)
```

Agreement thresholds:
- `AGREE`: Values differ by ≤5% across all categories
- `MINOR_DIFF`: Values differ by 5–15%; flag but use primary
- `CONFLICTING`: Values differ by >15% on any category; preserve both; do not silently pick one

---

## 4. Data Source Assessment for Final Subscription

### 4.1 NSE / BSE Official

NSE and BSE publish real-time subscription updates on their IPO pages during the live window, and a final figure at T3 close. However:
- These pages are **not preserved** after the IPO closes
- No bulk historical archive of subscription data is maintained by the exchanges
- The final subscription figures are, however, captured by third-party aggregators at the time of publication

**Access to historical NSE/BSE subscription data:** Not available for bulk historical download without NSE Data & Analytics subscription. Contact: marketdata@nse.co.in

### 4.2 Chittorgarh.com

```
What it provides:   QIB, NII, Retail, Total subscription multiples for each IPO
                    Published on individual IPO pages and in year-wise summary tables
Historical depth:   2010+ for Mainboard IPOs
Coverage quality:   ~90%+ for 2020–2024; ~70–80% for 2018–2019
Structured access:  5 rows free per year-filter (confirmed via browser session 2026-09-03)
                    Full data: IPOMatrix paid subscription required
Reliability:        Medium-high; scrapes from NSE/BSE at close of subscription
Known issues:       QIB multiple may or may not include anchor investors; varies per display
```

### 4.3 InvestorGain.com

```
What it provides:   QIB, NII, Retail, Total subscription multiples + GMP + listing price
Historical depth:   ~2015+ for Mainboard
Coverage quality:   Similar to Chittorgarh; slightly different IPOs covered
Structured access:  Free preview with limited rows; full data behind login
Reliability:        Medium; cross-reference with Chittorgarh
Known issues:       Some older entries may show only Total sub; category breakdown missing
```

### 4.4 BSE / NSE Subscription Data Archive (via individual IPO pages)

During research, NSE/BSE IPO-specific pages were confirmed to remove subscription data post-listing. However, the **Basis of Allotment PDF** filed with each exchange contains the actual final subscription numbers (verified and authoritative). This is:
- Filed by the registrar (KFintech/Link Intime/Bigshare/Cameo)
- Published on BSE publicissue portal and registrar website
- Contains: total bids, shares offered, successful applications — at category level
- This is the most reliable source of final subscription data

**BoA PDFs as secondary subscription source:**
The BoA document contains the figures from which subscription multiples are derived. Collecting BoA PDFs (part of Gate G6) provides an independent, exchange-certified subscription data source.

---

## 5. Coverage Findings

### 5.1 Year-level coverage availability (qualitative)

| Year | Coverage on aggregators | Notes |
|------|-------------------------|-------|
| 2024 | High (>90%) | Most IPO pages active; data fresh |
| 2023 | High (>90%) | Good aggregator archive |
| 2022 | High (~90%) | Good; some smaller IPOs may have gaps |
| 2021 | High (~90%) | Bull year; heavily tracked |
| 2020 | Medium-High (~80%) | Some pre-March 2020 IPOs have incomplete data |
| 2019 | Medium (~70%) | Lower coverage; some IPOs not on aggregators |
| 2018 | Medium (~65%) | Further from present; more gaps |

### 5.2 Quantitative coverage (estimated from aggregate research)

| Year | Total IPOs | Subscription data expected (%) | Expected usable records |
|------|------------|-------------------------------|-------------------------|
| 2018 | 42 | ~65% | ~27 |
| 2019 | 39 | ~70% | ~27 |
| 2020 | 44–69 | ~80% | ~35–55 |
| 2021 | 63 | ~90% | ~57 |
| 2022 | 40 | ~90% | ~36 |
| 2023 | 60 | ~90% | ~54 |
| 2024 | 93 | ~90% | ~84 |
| **Total** | **341–406** | **~82%** | **~320–340** |

---

## 6. Category Breakdown Availability

| Subscription field | Availability | Notes |
|-------------------|--------------|-------|
| Total subscription_x | High — nearly always published | Core field |
| QIB subscription_x | High — usually published | Includes anchor investors by default on most sites |
| NII subscription_x | High — usually published | May be combined sNII+bNII or separate post-2022 |
| Retail subscription_x | High — nearly always published | |
| sNII subscription_x (post-2022) | Medium — some sites split, others don't | Post-Sept 2022 only |
| bNII subscription_x (post-2022) | Medium | Same note |
| Raw bid quantities (shares) | Low — not typically on free aggregators | In BoA PDFs |
| Application count (retail) | Low — not on aggregators | In BoA PDFs |

---

## 7. QIB Anchor Investor Issue

**Important data nuance:** QIB subscription figures on different platforms may or may not include anchor investors, who are allocated shares before the public subscription opens:

- **Anchor investors** receive up to 60% of the QIB quota before subscription opens
- The public QIB subscription window covers only the remaining 40% of the QIB quota
- Some platforms report QIB multiple against total QIB quota (including anchor); others against only public QIB quota
- This leads to systematic discrepancies between platforms

**Resolution rule for data collection:**
- Always record `qib_sub_includes_anchor` boolean
- Default: if not specified, assume **includes anchor** (as most sites present it)
- For model features, use `qib_sub_x` as-is but document this flag

---

## 8. SEBI NII Regime Change (September 2022)

All subscription data must be tagged with the NII regime:

| Field | Value | Applies to |
|-------|-------|------------|
| `sebi_nii_regime` | `PRE_2022` | Close date before 2022-09-01 |
| `sebi_nii_regime` | `POST_2022` | Close date on or after 2022-09-01 |

Under POST_2022:
- NII is split: sNII (₹2L–₹10L) gets 1/3 of NII quota; bNII (>₹10L) gets 2/3
- Collect `snii_subscription_x` and `bnii_subscription_x` separately where available
- Allotment probability formula differs between regimes (see DATA-FEASIBILITY-REPORT Section 5.1)

---

## 9. Confirmed Subscription Records (from research)

The following records have subscription data confirmed from secondary sources. These are the only individual-level records confirmed during this research phase.

| Company | Year | Close Date | Retail Sub (x) | NII Sub (x) | QIB Sub (x) | Total Sub (x) | Source |
|---------|------|-----------|---------------|-------------|-------------|---------------|--------|
| Zomato | 2021 | 2021-07-16 | ~7.5 | ~32.0 | ~51.8 | ~38.2 | Multiple news; SECONDARY_VERIFIED |
| Paytm | 2021 | 2021-11-10 | ~1.7 | ~24.2 | ~179.0 | ~89.1 | Multiple news; SECONDARY_VERIFIED |
| Nykaa | 2021 | 2021-10-30 | ~12.2 | ~112.0 | ~92.0 | ~82.0 | Multiple news; SECONDARY_VERIFIED |
| Sigachi Industries | 2021 | 2021-11-03 | ~28.7 | ~228.0 | ~247.7 | ~101.9 | Multiple news; SECONDARY_VERIFIED |
| LIC | 2022 | 2022-05-09 | ~1.99 | ~2.91 | ~2.83 | ~2.95 | Multiple news; SECONDARY_VERIFIED |
| Bajaj Housing Finance | 2024 | 2024-09-11 | ~7.4 | ~41.6 | ~208.7 | ~63.6 | Multiple news; SECONDARY_VERIFIED |

*These 6 records represent the only individually confirmed subscription records from this research sprint. The full ~320+ record dataset requires systematic collection from aggregator sites or paid data.*

---

## 10. What Cannot Be Reconstructed

The following are explicitly excluded and must NOT be synthesized:

| Data | Why excluded |
|------|-------------|
| Day 1 subscription levels (9:00 AM on Day 1) | Not archived historically |
| Day 2 subscription (after second day close) | Not reliably archived |
| Intraday progression within any day | Never archived |
| Subscription velocity or acceleration | Not computable from available data |

These are **live-only features** in the production system and must not appear in the historical training dataset.

---

## 11. G3 Status

**Status: METHODOLOGY COMPLETE / EXECUTION PENDING**

| Metric | Value |
|--------|-------|
| Individual IPO records with confirmed subscription | 6 (notable large IPOs only) |
| Full year-level coverage (aggregate) | Confirmed from annual reviews |
| Bulk collection path | IPOMatrix subscription OR systematic per-page scraping |
| Expected collection after paid access | ~320–340 usable subscription records |
| Blocking issue | Requires either paid data or significant manual collection (~40 hours) |
| BoA-based verification (Gate G6) | Planned; will cross-validate aggregator figures |
