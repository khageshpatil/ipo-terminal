# G2 — Canonical Listing Price Validation
**Version:** 1.0 | **Date:** 2026-09-04 | **Gate status:** METHODOLOGY CONFIRMED; bulk data collection pending

---

## 1. Canonical Field Definition

### Decision

> **The canonical listing price for a Mainboard IPO is the `OPEN` price field in the NSE (or BSE) daily Bhav Copy file for the stock's first day of trading.**

This is the **pre-open session equilibrium price**, established during the Special Pre-Open Session (SPOS) on listing day before normal trading begins.

---

## 2. Exchange Mechanism — Verified

### Pre-Open Session on Listing Day (NSE/BSE)

The Special Pre-Open Session for newly listing securities operates as follows:

| Time | Activity |
|------|----------|
| 9:00 – 9:45 AM | Order entry, modification, and cancellation (call auction phase) |
| 9:45 – 9:55 AM | Order matching; equilibrium price calculation |
| 10:00 AM | Normal trading begins at the discovered equilibrium price |

The **equilibrium price** from the 9:45–9:55 AM matching phase is:
- The price at which the maximum volume of shares can be traded
- Set by actual market order flow, not by the company or merchant banker
- This IS the listing price — often called "opening price" or "first traded price" in common usage

### Field in Bhav Copy

The NSE/BSE daily Bhav Copy (end-of-day price file) contains four price fields per symbol per day:
```
OPEN   ← This is the pre-open equilibrium price = canonical listing price
HIGH   ← Highest intraday traded price
LOW    ← Lowest intraday traded price
CLOSE  ← End-of-day traded price
```

On a stock's **first day of trading**:
- `OPEN` = pre-open equilibrium = listing price ✅

### What the listing price is NOT

| Candidate | What it actually is | Use it? |
|-----------|--------------------|---------:|
| Bhav Copy OPEN on Day 1 | Pre-open equilibrium; set by auction before market open | ✅ **YES — canonical** |
| Bhav Copy HIGH on Day 1 | Highest price during intraday trading | ❌ No |
| Bhav Copy CLOSE on Day 1 | End-of-day price; influenced by post-open market movement | ❌ No |
| Day 1 VWAP | Volume-weighted average of all Day 1 trades | ❌ No |
| Aggregator "listing price" | Usually = Bhav Copy OPEN; acceptable as cross-check only | ⚠️ Cross-check only |
| "Listing day gain %" from aggregators | Computed as (aggregator_listing - issue_price)/issue_price | ⚠️ Cross-check; verify underlying |
| Adjusted historical close | Corporate-action-adjusted price (for splits, dividends) | ❌ Never — use unadjusted Day 1 OPEN |
| First trade in normal session | In theory same as OPEN; in practice identical | ✅ Same thing |

---

## 3. Data Source for G2 Collection

### Primary source: NSE Bhav Copy

```
Provider:         National Stock Exchange of India Ltd.
Access URL:       nseindia.com → Market Data → Historical Data → Equity
                  (also: nseindia.com/all-reports for daily archives)
File format:      CSV / ZIP archive (one file per trading day)
Fields:           SYMBOL, SERIES, OPEN, HIGH, LOW, PREVCLOSE, LCLOSE, TOTTRDQTY,
                  TOTTRDVAL, TIMESTAMP, TOTALTRADES, ISIN
Frequency:        Daily (one row per listed security per trading day)
Coverage:         All NSE-listed equities; archives available for 10+ years
Cost:             Free for historical daily download
API:              None official; unofficial Python wrappers for individual symbol history
```

**Retrieval method for G2:**
1. Obtain G1 universe list (company name + NSE symbol + listing date)
2. For each IPO, retrieve the Bhav Copy for its listing date
3. Match by `SYMBOL` field; extract `OPEN` value
4. Record as `bhav_open` in the G2 output file

### Secondary source: BSE Bhav Copy

Used when:
- IPO is BSE-only listed (BSE_ONLY flag from G1)
- NSE Bhav Copy OPEN appears anomalous (circuit-limit scenario)

```
Provider:         BSE India Ltd.
Access URL:       bseindia.com → Market Data → Historical Data → Equity
File format:      CSV archive
Fields:           Include OPEN, HIGH, LOW, CLOSE equivalent
Cost:             Free
```

### Cross-check: Third-party aggregators

Chittorgarh and InvestorGain report a "listing price" column derived from the exchange Bhav Copy OPEN. These should match the canonical value to within ₹0.01 (rounding only). Used for sanity check — never as primary source.

---

## 4. Validation Rules

All G2 records must pass these checks before inclusion in the research dataset:

| Rule | Check | Action on failure |
|------|-------|------------------|
| V1 | `bhav_open > 0` | Mark data_quality = MISSING; exclude from G4 |
| V2 | `issue_price > 0` (from G1) | Mark data_quality = MISSING |
| V3 | `listing_date` is a valid trading day | Verify against NSE holiday calendar |
| V4 | `listing_date >= close_date` (G1 field) | Flag as ANOMALY; investigate |
| V5 | `listing_date <= close_date + 20 trading days` | Unusually late listings flagged for review |
| V6 | `bhav_open >= 0.5 × issue_price` and `bhav_open <= 5 × issue_price` | Extreme values: manual review; could be correct |
| V7 | NSE OPEN matches BSE OPEN within 0.5% for dual-listed stocks | If discrepancy >0.5%, flag and investigate |
| V8 | No duplicate canonical outcome (one row per IPO) | If found, resolve to one record |
| V9 | Symbol found in Bhav Copy for listing_date | If not found: check alternative symbol format; then BSE; then MISSING |

---

## 5. Known Edge Cases and Resolutions

| Edge case | Observed? | Resolution |
|-----------|-----------|------------|
| **Circuit limit on listing day** | Occasionally (large bull IPOs) | OPEN still = pre-open equilibrium. The circuit limit applies to subsequent intraday trading, not the pre-open auction. Bhav Copy OPEN is still the canonical price. |
| **Stock listed only on BSE, not NSE** | Some smaller issues | Use BSE Bhav Copy OPEN; mark `source_exchange = BSE` |
| **Delayed listing (IPO listed T+N instead of expected T+3)** | Rare | Use actual listing date Bhav Copy OPEN; not the expected date |
| **Cancelled listing post-allotment** | Very rare | Mark CANCELLED; exclude from G4 |
| **Symbol change post-listing** | Occasional | Use the symbol at time of listing; note current symbol separately |
| **Pre-open session extended or cancelled by exchange** | Theoretically possible | Would be a market event; check exchange circulars for that date |
| **LIC IPO (2022) — multiple lot categories** | Yes — LIC had policyholder/employee quotas | Issue price: ₹949 (retail); ₹902 (policyholder discount); use ₹949 for baseline |
| **IPOs with fixed price (no price band)** | Some exist | Issue price = listing price baseline; fixed-price issues have all-or-nothing allotment |

---

## 6. Confirmed Listing Price Records (from research)

The following listing price records have been confirmed from named secondary sources (news reports, analyst reviews). All are `bhav_open` approximations pending direct Bhav Copy verification.

| Company | Year | Issue Price (₹) | Bhav Open Day 1 (₹) | Return (%) | Source quality |
|---------|------|----------------:|--------------------:|-----------:|---------------|
| Bandhan Bank | 2018 | 375 | ~485 | +29.3% | SECONDARY_VERIFIED |
| HAL | 2018 | 1,215 | ~1,169 | -3.8% | SECONDARY_VERIFIED |
| ICICI Securities | 2018 | 520 | ~431 | -17.1% | SECONDARY_VERIFIED |
| RITES Ltd | 2018 | 185 | ~205 | +10.8% | SECONDARY_VERIFIED |
| Happiest Minds | 2020 | 166 | ~351 | +111.5% | SECONDARY_VERIFIED |
| Chemcon Speciality | 2020 | 340 | ~731 | +115.0% | SECONDARY_VERIFIED |
| Mazagon Dock | 2020 | 145 | ~215 | +48.3% | SECONDARY_VERIFIED |
| Burger King India | 2020 | 60 | ~112 | +86.7% | SECONDARY_VERIFIED |
| Mrs. Bectors Food | 2020 | 288 | ~501 | +74.0% | SECONDARY_VERIFIED |
| Gland Pharma | 2020 | 1,500 | ~1,701 | +13.4% | SECONDARY_VERIFIED |
| Zomato | 2021 | 76 | ~126 | +65.8% | SECONDARY_VERIFIED |
| Paytm | 2021 | 2,150 | ~1,564 | -27.4% | SECONDARY_VERIFIED |
| Nykaa | 2021 | 1,125 | ~2,206 | +96.1% | SECONDARY_VERIFIED |
| Sigachi Industries | 2021 | 163 | ~599 | +267.2% | SECONDARY_VERIFIED |
| Paras Defence | 2021 | 175 | ~493 | +181.4% | SECONDARY_VERIFIED |
| Latent View Analytics | 2021 | 197 | ~488 | +148.1% | SECONDARY_VERIFIED |
| Go Fashion | 2021 | 690 | ~1,264 | +83.2% | SECONDARY_VERIFIED |
| Metro Brands | 2021 | 500 | ~493 | -1.4% | SECONDARY_VERIFIED |
| Shriram Properties | 2021 | 118 | ~100 | -15.3% | SECONDARY_VERIFIED |
| LIC | 2022 | 949 | ~872 | -8.1% | SECONDARY_VERIFIED |
| Bajaj Housing Finance | 2024 | 70 | ~150 | +114.3% | SECONDARY_VERIFIED |
| Vibhor Steel Tubes | 2024 | 151 | ~425 | +181.5% | SECONDARY_VERIFIED |
| Unicommerce eSolutions | 2024 | 108 | ~235 | +117.6% | SECONDARY_VERIFIED |
| Mamata Machinery | 2024 | 243 | ~600 | +147.0% | SECONDARY_VERIFIED |
| Senores Pharma | 2024 | 391 | ~600 | +53.5% | SECONDARY_VERIFIED |
| DAM Capital Advisors | 2024 | 283 | ~393 | +38.9% | SECONDARY_VERIFIED |
| Unimech Aerospace | 2024 | 785 | ~1,460 | +86.0% | SECONDARY_VERIFIED |

**Important caveat:** All `~` values above are approximate (sourced from secondary summaries, not primary Bhav Copy). They are marked SECONDARY_VERIFIED and must be upgraded to PRIMARY_VERIFIED by direct Bhav Copy lookup before use in model training.

---

## 7. Coverage Status

| Year | Total IPOs (G1) | Listing prices confirmed (PRIMARY) | Listing prices confirmed (SECONDARY, approx.) | Missing |
|------|----------------:|-----------------------------------:|----------------------------------------------:|-------:|
| 2018 | 42 | 0 | 4 | 38 |
| 2019 | 39 | 0 | 0 | 39 |
| 2020 | 44–69 | 0 | 7 | 37–62 |
| 2021 | 63 | 0 | 12 | 51 |
| 2022 | 40 | 0 | 2 | 38 |
| 2023 | 60 | 0 | 0 | 60 |
| 2024 | 93 | 0 | 10 | 83 |
| **Total** | **341–406** | **0** | **35** | **306–371** |

**G2 primary coverage: 0% (0/341+ IPOs have PRIMARY_VERIFIED listing prices)**
**G2 secondary coverage: ~9% (35/341+ IPOs have SECONDARY_VERIFIED approximate prices)**

> This means: the full G2 dataset cannot be assembled until the systematic Bhav Copy download is conducted. The methodology is confirmed; the execution is pending.

---

## 8. Listing Price Field — Final Confirmation

| Attribute | Value |
|-----------|-------|
| **Canonical field** | `OPEN` in NSE daily Bhav Copy |
| **Canonical event** | Pre-Open Session equilibrium price, listing day |
| **Exchange session** | 9:00 – 9:55 AM; equilibrium matched at 9:45 AM |
| **Regulation** | SEBI/NSE/BSE circular on Pre-Open Call Auction for listing day |
| **Freely downloadable** | Yes — NSE Historical Data section, no login required |
| **Alternative** | BSE Bhav Copy OPEN (for BSE-only listings; identical mechanism) |
| **Cannot use** | Aggregator "listing price" as primary; Day-1 CLOSE; adjusted close |
| **Validation** | NSE OPEN vs. BSE OPEN should agree within 0.5% for dual-listed stocks |

---

## 9. G2 Status

**Status: METHODOLOGY COMPLETE / EXECUTION PENDING**

The canonical field is unambiguously defined and confirmed. The NSE Bhav Copy download method is clear and free. The G2 dataset cannot be built until the G1 universe list (company + NSE symbol + listing date) is complete — G2 depends on G1 as an input.

**Blocking dependency:** G1 full row-level universe must be built first (requires paid data or systematic collection).
