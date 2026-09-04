# G1 — Full Historical Data Acquisition Decision

**Status: RECOMMENDATION MADE — AWAITING USER DECISION**
**Date: 2026-09-04**

---

## 1. The Core Problem

The Phase 1 pipeline is validated on 25 records with `SECONDARY_VERIFIED` listing prices.
This is sufficient as a **pipeline fixture only**.

To build a meaningful backtest we need:

| Requirement | Current State | Target |
|-------------|--------------|--------|
| IPO universe (Mainboard, 2018–2024) | 25 records confirmed | ~480 IPOs |
| Canonical listing prices (PRIMARY_VERIFIED) | 0 | ~480 |
| Final subscription data | 0 | ~300+ (post-2018 best effort) |
| Point-in-time safe data | ✅ Architecture ready | — |

**Until the IPO universe + canonical listing prices are resolved, model training cannot begin.**

---

## 2. Minimum Dataset for the First Meaningful Backtest

The minimum viable dataset to produce a statistically credible backtest requires:

- **≥ 200 Mainboard IPOs** with verified listing prices (PRIMARY_VERIFIED from exchange)
- **Coverage 2018–2024** (captures PRE_2022 and POST_2022 SEBI NII regimes)
- **At minimum**: ipo_id, company, close_date, listing_date, issue_price, listing_open_price (from exchange Bhav Copy)
- **Desirable but not blocking**: subscription data, lot size, issue size

A dataset of ≥300 IPOs would allow meaningful train/test splits and regime-specific analysis.

---

## 3. The Three Acquisition Paths

### Option 1 — IPOMatrix / Chittorgarh.com (Paid)

**Product:** IPOMatrix.com — structured historical IPO data from Chittorgarh.com

| Dimension | Details |
|-----------|---------|
| **Coverage** | Mainboard + SME IPOs, **2004–present** (Elite plan) |
| **Fields** | 100+ per IPO: issue size, price band, lot size, subscription (QIB/NII/Retail/Total/Day-wise), anchor allocation, listing prices (open, high, low, close), GMP history, listing gain/loss |
| **Export format** | Web download; CSV/Excel export confirmed for subscribers |
| **Historical depth** | Elite: 2004-present (~22 years). Pro: 2021–present only |
| **Pricing (annual)** | Starter ₹5,000+GST (1yr data), **Pro ₹25,000+GST (5yr = 2021–2026)**, **Elite ₹1,00,000+GST (since 2004)** |
| **Student discount** | 25% on Pro/Elite |
| **Point-in-time** | Historical subscription data is end-of-subscription (not intraday). This matches our requirement. |
| **Quality** | Secondary-verified (aggregated from NSE/BSE + manual research). Not NSE-authoritative listing prices. |
| **Licensing** | Research/personal use. Commercial redistribution prohibited. |

**For our model window (2018–2024):**
- Pro plan (₹25k+GST = ~₹29.5k) covers only 2021–2026. **Insufficient — misses 2018–2020.**
- Elite plan (₹1L+GST = ~₹1.18L) covers 2004–present. **Covers full model window.**

**Assessment:**
- Elite plan gives us the full dataset immediately, in clean format.
- The ₹1.18L cost is the principal concern.
- Listing prices will be **SECONDARY_VERIFIED** — they source from the exchange but are not raw Bhav Copy files.
- For a research/backtest model, SECONDARY_VERIFIED listing prices are acceptable IF cross-validated.

---

### Option 2 — Systematic NSE/BSE Bhav Copy Collection (Free)

**What it is:** NSE publishes a daily Bhav Copy (end-of-day price file) for every trading day. Each file contains OPEN, HIGH, LOW, CLOSE, and VOLUME for every listed security. The OPEN price on a stock's listing day = the listing price (determined in pre-open call auction).

| Dimension | Details |
|-----------|---------|
| **Coverage** | All NSE-listed equities, 1994–present |
| **Historical depth** | Complete. 2018–2024 fully available. |
| **URL pattern** | `https://nsearchives.nseindia.com/content/historical/EQUITIES/{YYYY}/{MMM}/cm{DD}{MMM}{YYYY}bhav.csv.zip` |
| **Format** | ZIP-compressed CSV; columns: SYMBOL, SERIES, OPEN, HIGH, LOW, CLOSE, LAST, PREVCLOSE, TOTTRDQTY, TOTTRDVAL, TIMESTAMP, TOTALTRADES |
| **Listing price** | `OPEN` on the listing date for Series `EQ` — this is the pre-open call auction price. **PRIMARY_VERIFIED.** |
| **Cost** | **Free** |
| **Engineering effort** | Medium: ~3–5 days to build automation + symbol mapping |
| **Point-in-time** | Perfect — exchange-authoritative data at close |
| **Access restrictions** | Requires browser-like headers (User-Agent, Referer). No authentication needed. |
| **Quality** | PRIMARY_VERIFIED — direct exchange data |
| **Limitations** | **Does NOT give us the IPO universe list.** We must separately compile which symbols listed on which date. |

**Critical constraint:** The Bhav Copy gives us *what we need for listing prices*, but **not the IPO list itself**. We must first know (company name, symbol, listing_date) before we can look up the Bhav Copy for that day. This means we need the universe list from another source.

**Assessment:**
- Best source for **listing prices** (PRIMARY_VERIFIED, free).
- Not usable alone — needs the universe list as input.
- Automation is feasible: ~480 one-file downloads across 7 years.
- Symbol mapping is the only challenge: symbols sometimes differ from trading names.

---

### Option 3 — PRIME Database (Paid Enterprise)

**What it is:** PRIME Database — established 1989, the original Indian primary market data repository. Covers all public issues, rights issues, QIPs, delistings.

| Dimension | Details |
|-----------|---------|
| **Coverage** | All Indian public issues, **1989–present** |
| **Fields** | Issue data, subscription (category-wise), listing prices, post-listing performance (1W/1M/3M/6M/12M), fundamentals summary, promoter data |
| **Historical depth** | Complete. Best deep-history source available. |
| **Pricing** | **Not disclosed publicly.** Custom quotes. Enterprise pricing. Estimated: ₹2–5L/year for full access (institutional). |
| **Export format** | Web interface + data export (format varies by plan) |
| **Quality** | HIGH — manually curated, cross-verified |
| **Point-in-time** | Good for historical; no intraday data |
| **Licensing** | Commercial license. Institutional clients include SEBI, mutual funds, investment banks. |
| **Contact** | prime@primedatabase.com / +91-11-4100-8346 |

**Assessment:**
- Best quality and coverage of the three options.
- Pricing is opaque and likely institutional (₹2–5L+ estimated).
- Contact required to get even a quote.
- Appropriate for a funded project; overkill for research phase.
- Would give us the cleanest dataset but at unclear cost and unknown timeline.

---

## 4. Decision Framework Scoring

### Criteria Weights

| Criterion | Weight |
|-----------|-------:|
| Historical coverage (2018–2024 complete) | 30% |
| Data quality (PRIMARY vs SECONDARY) | 25% |
| Point-in-time suitability | 20% |
| Cost | 10% |
| Engineering effort | 10% |
| Long-term usability | 5% |

### Scoring (1–10 per criterion)

| Option | Coverage (30%) | Quality (25%) | PIT (20%) | Cost (10%) | Engineering (10%) | Long-term (5%) | **Weighted Score** |
|--------|:--------------:|:-------------:|:---------:|:----------:|:-----------------:|:--------------:|:------------------:|
| **Option 1: IPOMatrix Elite** | 9 | 7 | 8 | 3 | 9 | 6 | **7.55** |
| **Option 2: NSE Bhav Copy** | 8 | 10 | 10 | 10 | 5 | 8 | **8.65** |
| **Option 3: PRIME Database** | 10 | 10 | 9 | 2 | 8 | 10 | **8.35** |
| **Option 2+1 Hybrid** | 10 | 9 | 10 | 6 | 6 | 8 | **8.95** |

> **Scoring notes:**
> - Option 2 cost is 10/10 (free), but engineering is 5/10 (requires universe list input from another source).
> - Option 1 Elite cost is 3/10 (₹1.18L/year is significant for research); quality is 7/10 (secondary-verified listing prices).
> - Option 3 cost is 2/10 (estimated ₹2–5L/year institutional pricing).
> - The Hybrid (Option 2+1) scores highest: use IPOMatrix **Pro** (₹29.5k) for the IPO universe + subscription data, and Bhav Copy for PRIMARY_VERIFIED listing prices.

---

## 5. The Recommended Approach: Hybrid (Option 2 + Option 1 Pro)

### Strategy

| Phase | Source | What we get | Cost | Quality |
|-------|--------|-------------|------|---------|
| **Phase A** — Universe + Subscription | Free aggregators (Chittorgarh free pages, InvestorGain, MoneyControl) | IPO universe 2018–2024: name, symbol, dates, issue price, subscription | Free | SECONDARY_VERIFIED |
| **Phase B** — Listing Prices | NSE Bhav Copy (automated) | OPEN price on listing day for each symbol | Free | PRIMARY_VERIFIED |
| **Phase C** (Optional upgrade) | IPOMatrix Pro ₹29.5k | Structured subscription data 2021–2026 + validation | ₹29.5k | SECONDARY_VERIFIED |
| **Phase D** (Optional) | IPOMatrix Elite ₹1.18L | Full 2004–present structured data | ₹1.18L | SECONDARY_VERIFIED |

### Phase A Detail — Bootstrap from Free Sources

The IPO universe for 2018–2024 (~480 IPOs) can be assembled from:

1. **Chittorgarh.com free pages** — Lists all Mainboard/SME IPOs with basic data (name, dates, issue price, subscription, listing gain %). Free, paginated.
2. **InvestorGain.com** — Similar to Chittorgarh; cross-validation source.
3. **MoneyControl IPO section** — Historical IPO list with performance data.
4. **SEBI ICDR filings page** — Official but not structured; requires scraping.

**Estimated manual/semi-automated effort for Phase A:** 2–4 days to build a scraper + 1–2 days validation.

**Risk:** Free aggregators may have errors or gaps (typically ±5%). Acceptable for a research dataset if cross-validated.

### Phase B Detail — NSE Bhav Copy Automation

For each IPO in the universe (company, symbol, listing_date):
1. Download the Bhav Copy ZIP for the listing_date.
2. Find the row where SYMBOL matches and SERIES = 'EQ'.
3. Extract the OPEN price as the listing price.

**Accuracy:** PRIMARY_VERIFIED. This is the exchange-authoritative price.
**Edge cases:**
- Some IPOs list as 'BE' series (trade-for-trade) on listing day → use 'BE' row if 'EQ' absent.
- Symbol must match exactly (case-sensitive, no spaces). Occasional mismatches need manual lookup.
- BSE Bhav Copy is also available for cross-validation (`bseindia.com/download/BhavCopy/Equity/{date}_BSEALL.zip`).

**Estimated engineering effort:** 3–5 days for a robust downloader + symbol mapper.

---

## 6. Answering the Decision Questions

### Q1: Minimum dataset for the first meaningful backtest?

**200+ Mainboard IPOs with PRIMARY_VERIFIED listing prices, covering 2018–2024.**

Specifically:
- `ipo_id`, `company_name`, `nse_symbol`, `close_date`, `listing_date`, `issue_price`, `listing_open_price`
- All fields from the confirmed CSV schema already in the pipeline.

### Q2: Which acquisition path gives the best cost/quality combination?

**Hybrid: Free web scraping (universe) + NSE Bhav Copy (listing prices).**

- Total cost: ₹0 (excluding engineering time)
- Listing prices: PRIMARY_VERIFIED
- Universe: SECONDARY_VERIFIED (acceptable; spot-checkable against SEBI filings)
- Engineering time: ~5–9 days

### Q3: Can we realistically reach ≥300 usable Mainboard IPOs?

**Yes.** The Mainboard IPO count for 2018–2024 is approximately:
- 2018: ~25 | 2019: ~16 | 2020: ~14 | 2021: ~63 | 2022: ~40 | 2023: ~57 | 2024: ~90+
- **Total: ~305–320 Mainboard IPOs** (SME excluded)

After filtering for: listing price available + issue price confirmed + close date known,
we conservatively expect **280–310 usable records.**

### Q4: What fields will still be missing?

| Field | Availability | Notes |
|-------|-------------|-------|
| Intraday subscription (day-wise) | Low | Not reliably archived for 2018–2020 |
| GMP history | Low | No reliable archive |
| EBITDA / fundamentals | Low | RHP extraction not ready (G7) |
| Sector/industry classification | Medium | Available from NSE sector classification |
| Anchor allocation | Medium | Available on SEBI / IPOMatrix |

**These fields are NOT blocking.** The V1 model excludes them by design.

### Q5: Timeline and cost of each option?

| Option | Time to first backtest-ready dataset | Cost |
|--------|--------------------------------------|------|
| Hybrid (Recommended) | 2–3 weeks engineering | ₹0 |
| IPOMatrix Elite | 1 week (download + validate) | ₹1.18L/yr |
| PRIME Database | 4–8 weeks (quote + onboarding) | ₹2–5L/yr (estimated) |

### Q6: Fallback if preferred option fails?

**Primary:** Hybrid (free scraping + Bhav Copy)

**Fallback sequence:**
1. If scraping is blocked → switch to IPOMatrix Pro (₹29.5k) for subscription data; Bhav Copy still works independently.
2. If Bhav Copy automation fails (NSE changes URLs) → use manual download of historical Bhav Copy for listing dates (NSE provides bulk historical archives).
3. If listing prices are still incomplete after both → use SECONDARY_VERIFIED prices from InvestorGain/Chittorgarh, clearly labelled; retrain when PRIMARY_VERIFIED data is acquired.

---

## 7. Fields Still Missing After Hybrid Approach

Even with the full 480-IPO dataset, the following will remain as data gaps for the V1 model:

| Field | Status |
|-------|--------|
| Pre-subscription GMP | EXCLUDED (no reliable archive) |
| Day-wise subscription (intraday) | EXCLUDED (no reliable archive pre-2021) |
| PDF-extracted fundamentals (revenue, PAT) | DEFERRED (G7 Phase 2) |
| Anchor allocation detail | AVAILABLE but low priority |
| Bhav Copy OPEN vs pre-open equilibrium distinction | LOW RISK (NSE pre-open auction determines OPEN; this is the correct listing price) |

---

## RECOMMENDATION: OPTION 2 + OPTION 1 HYBRID

**Use free web aggregators (Chittorgarh free pages, InvestorGain) for the IPO universe + subscription overview, and NSE Bhav Copy for PRIMARY_VERIFIED listing prices.**

### Why not Option 3 (PRIME)?
- Pricing opaque; institutional budget required
- 4–8 week onboarding timeline
- Quality advantage doesn't justify the cost for a research project

### Why not Option 1 alone (IPOMatrix Elite)?
- ₹1.18L/year is expensive; subscription data is secondary-verified, not primary
- Makes sense as a **later upgrade** if the model is productionised

### Why this Hybrid?
1. **Zero monetary cost** for the research phase — preserves budget optionality
2. **Listing prices are PRIMARY_VERIFIED** — the most important quality concern is resolved
3. **Universe from free aggregators is good enough for research** — errors are ±5% and detectable
4. **Fully automatable** — once built, can be re-run for any future period
5. **Engineering risk is manageable** — NSE Bhav Copy URL format is well-documented
6. **Upgrade path is clean** — if IPOMatrix Elite is later purchased, it slots into the same schema

### Decision required from user

> **Before Phase A begins, confirm:**
> 1. Approve Hybrid approach (₹0 cost, 5–9 days engineering)
> 2. OR approve IPOMatrix Pro (₹29.5k) for faster structured data, covering 2021–2026 only
> 3. OR approve IPOMatrix Elite (₹1.18L) for full history in one shot

---

## 8. Next Engineering Tasks After Decision

Assuming Hybrid is approved:

| Task | Effort | Output |
|------|--------|--------|
| Build Chittorgarh/InvestorGain scraper for universe | 2–3 days | `data/universe/ipo_universe_2018_2024.csv` |
| Build NSE Bhav Copy downloader + symbol mapper | 2–3 days | `data/market/bhav_listing_prices.csv` |
| Merge + validate against confirmed 25-record sample | 1 day | Merged universe with PRIMARY_VERIFIED listing prices |
| Upgrade all labels from SECONDARY to PRIMARY_VERIFIED | 0.5 days (code) | `DataQuality.PRIMARY_VERIFIED` throughout |
| Re-run base-rate analysis on full dataset | 0.5 days | True historical base rate (~280–310 IPOs) |
| **Total** | **~6–8 days** | **Backtest-ready full dataset** |
