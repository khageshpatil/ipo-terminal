# Data Feasibility Report — IPO Listing-Gain Decision Engine
**Version:** 1.0
**Date:** 2026-09-03
**Status:** Research complete — Pre-coding gate
**Scope:** Secondary research; every finding requires direct source validation before production use.

---

## Executive Conclusion

> **Can our intended listing-gain strategy be honestly backtested with real historical data?**

**YES — with a significantly reduced feature set.**

The original strategy specification assumed access to historical intraday subscription snapshots
and historical GMP time-series data. Neither is reliably available for historical IPO events.
A backtest built on the documented feature set (subscription velocity, GMP momentum) would either
be impossible to construct honestly or would produce contaminated results.

However, a reduced but honest backtest IS feasible using:
- Final-day subscription figures (QIB/NII/Retail)
- Issue terms and structure
- SEBI-formula allotment probability (deterministic)
- Market/Nifty regime data
- Fundamental proxies extracted from prospectuses
- Official listing prices from exchange Bhav Copy

The strategy must be redesigned to work with final-day subscription only for historical training.
Intraday subscription velocity and GMP features can be added in live production once the system
captures them itself — but they cannot be used in the historical backtest without contamination.

---

## Dataset Traffic-Light Classification

| Dataset                    | Status |
|----------------------------|--------|
| IPO master (issue terms)   | 🟢 Strong |
| Listing prices (label)     | 🟢 Strong |
| Market/Nifty/VIX           | 🟢 Strong |
| Transaction costs          | 🟢 Strong (well-defined) |
| Final subscription (QIB/NII/Retail) | 🟡 Partial |
| Basis of allotment (historical) | 🟡 Partial |
| SEBI/RHP fundamentals      | 🟡 Partial (PDF barrier) |
| Peer valuation (DRHP-stated) | 🟡 Partial (biased, but usable) |
| GMP (realtime, production) | 🟡 Partial (unofficial) |
| Intraday subscription snapshots | 🔴 Weak/Unavailable |
| Historical GMP time-series  | 🔴 Weak/Unavailable |

---

## Section 1 — Historical IPO Universe

### 1.1 Sample size by year (Mainboard only)

Source: PRIME Database industry reports, aggregator cross-references.

| Year | Approx. Mainboard IPOs | Notes |
|------|------------------------|-------|
| 2015 | 42 | |
| 2016 | 53 | |
| 2017 | 81 | Peak year |
| 2018 | 42 | |
| 2019 | 39 | Market caution post-NBFC crisis |
| 2020 | 69 | COVID recovery; includes several large issues |
| 2021 | 76 | Bull market boom |
| 2022 | 56 | Rate-hike volatility |
| 2023 | 60 | Selective recovery |
| 2024 | 93 | New record high |
| **2018–2024 total** | **~535** | |
| **2020–2024 total** | **~354** | Better data quality period |

**Conclusion on sample size:** A 2018–2024 window gives approximately 535 raw Mainboard IPO
events. After applying completeness filters (verified issue price + verified listing price +
usable subscription data), expect 400–480 usable observations. This is workable but not large
for supervised ML. Models must be kept simple and validated with wide confidence intervals.

> **WARNING:** The 2020–2021 IPO boom contains a disproportionate share of strongly positive
> listing events due to exceptional liquidity conditions. Any model trained primarily on
> 2020–2021 will exhibit severe regime bias. The full 2018–2024 window is required, and
> performance must be evaluated separately per market regime.

### 1.2 IPO universe sources

| Source | Data available | Historical depth | Structured? | Access |
|--------|---------------|-----------------|-------------|--------|
| NSE India (nseindia.com) | Issue terms, dates, listing data, equity Bhav Copy | 10+ years (Bhav Copy) | Partial CSV download; no historical subscription API | Free; no API for IPO history |
| BSE India (bseindia.com) | Issue terms, offer documents, allotment links, Bhav Copy | 10+ years | Partial; offer docs as PDFs | Free |
| SEBI EFTS (sebi.gov.in/filings) | DRHP, RHP, Final Prospectus PDFs | 2004–present | PDF only; searchable by name/date | Free |
| Chittorgarh.com | Year-wise IPO list, issue price, listing price, final subscription | 2006–present | Web tables; limited export | Free (basic), paid (IPOMatrix) |
| InvestorGain.com | IPO performance, GMP summary, subscription | ~2015–present | Web tables; no API | Free |
| PRIME Database | Full primary market database including subscription, issue responses | 1989–present | Structured (paid) | Paid; contact required |
| Trendlyne.com | IPO dashboard, listing stats, subscription summary | ~2018–present | Web; some export | Freemium |

**Practical universe-building approach:**
1. Use Chittorgarh year-wise pages to build the initial IPO list
2. Cross-reference issue terms with NSE/BSE
3. Use BSE publicissue portal for offer document PDFs
4. Validate listing prices against NSE/BSE daily Bhav Copy

---

## Section 2 — Official Data Source Matrix

### 2.1 NSE India

```
Source:           NSE India
URL:              https://www.nseindia.com/market-data/all-upcoming-issues-ipo
Data available:   Issue terms, price band, listing dates, live subscription (IPO open only),
                  historical equity Bhav Copy (OPEN/HIGH/LOW/CLOSE/VOLUME per day)
Historical depth: Equity price data: 10+ years via daily Bhav Copy download.
                  IPO subscription: live window only; no historical intraday archive.
                  IPO master info: accessible for listed securities via equity pages.
Timestamp:        Bhav Copy is date-indexed. Subscription data is only live.
Structured/API:   No official free public API. Unofficial Python libraries
                  (nsepython, stock-nse-india) wrap equity data only; not IPO subscription.
                  NSE Data & Analytics (paid): marketdata@nse.co.in, +91-22-2659-8385.
Access method:    Web HTML pages; downloadable CSV/ZIP Bhav Copy archives.
Reliability:      High for exchange-certified equity price data.
                  Unknown / unreliable for historical subscription (not exchange-maintained).
Limitations:      No structured historical subscription API. IPO-specific pages removed
                  after listing. Intraday subscription not archived.
```

### 2.2 BSE India

```
Source:           BSE India
URL:              https://www.bseindia.com/publicissue.html
Data available:   Offer documents (DRHP/RHP/Prospectus/BoA links), IPO master data,
                  historical equity Bhav Copy.
Historical depth: Offer document archive from ~mid-2000s onward.
                  Equity Bhav Copy: 10+ years.
Timestamp:        Date-level for equity data. Filing date on offer documents.
Structured/API:   No official free API. HTML portal; CSV Bhav Copy.
Access method:    BSE publicissue portal (company name search); CSV download for equity data.
Reliability:      High — BSE is a regulated exchange.
Limitations:      Offer documents are PDFs; subscription history not archived in structured
                  form; BoA link coverage decreases for older issues.
```

### 2.3 SEBI EFTS

```
Source:           SEBI Electronic Filing System
URL:              https://www.sebi.gov.in/filings.html > Public Issues
Data available:   DRHP, RHP, Final Prospectus for all public issues.
                  Searchable by company name, date range, document type.
Historical depth: Deep archive from approximately 2004 onward.
Timestamp:        Filing dates recorded. Financial periods stated within each document.
Structured/API:   No API. PDF documents only.
Access method:    Web search on sebi.gov.in; PDFs downloadable.
Reliability:      Highest — these are legal regulatory filings.
Limitations:      All data is in PDF; requires structured extraction (OCR / parsing).
                  Financial table layouts vary across issuers and years.
                  No machine-readable API; bulk extraction requires engineering investment.
```

### 2.4 Registrar Sources

```
Source:           KFintech (ipostatus.kfintech.com),
                  Link Intime (linkintime.co.in/MIPO/),
                  Bigshare Services, Cameo Corporate Services
Data available:   IPO allotment status per applicant (PAN-based lookup);
                  Basis of Allotment (BoA) documents as PDFs.
Historical depth: Recent/current IPOs prioritised. BoA PDFs for 3–5 years typically accessible.
                  Older data may be unavailable without contacting registrar directly.
Timestamp:        BoA documents are dated; published 1–2 days before listing (T+1).
Structured/API:   No API. PAN-based lookup portals; PDF downloads for BoA.
Access method:    Per-IPO lookup; PDF downloads.
Reliability:      High — registrars are regulated intermediaries; BoA is authoritative.
Limitations:      No bulk download or structured historical database.
                  Must identify the correct registrar for each IPO.
                  Pre-2018 records may be offline only.
                  BoA PDFs vary in layout; require parsing for structured fields.
```

---

## Section 3 — Historical Subscription Data

### 3A. Final Subscription Figures

**Conclusion: PARTIAL HISTORY — 2018–present, adequate quality, third-party sourced**

Final category-wise subscription (QIB / NII / Retail / Total) at close of the IPO is
published by NSE/BSE and archived by third-party aggregators. Coverage by period:

| Period | Coverage | Notes |
|--------|----------|-------|
| 2021–2024 | ~90%+ of Mainboard IPOs | High aggregator coverage |
| 2018–2020 | ~70–80% | Some smaller IPOs missing |
| 2015–2017 | <50% | Sparse on aggregators; use PRIME Database if available |

**Source hierarchy for final subscription:**
1. BSE/NSE official press releases and IPO pages (authoritative; not bulk-accessible)
2. Chittorgarh.com — year-wise tables (most comprehensive free archive)
3. InvestorGain.com — similar archive, complementary coverage
4. PRIME Database — professional archive (paid; most complete)

**Reliability check:** Final subscription figures on aggregators can be cross-validated
against the Basis of Allotment document, which contains actual final subscription as part
of the allotment calculation. This provides an independent validation path.

**Point-in-time quality:** ✅ Final subscription is inherently point-in-time — it represents
the state at close of the subscription window (T, 5:00 PM). No leakage risk at T3.

---

### 3B. Intraday Subscription Snapshots

**Conclusion: NOT RELIABLY AVAILABLE historically**

**Key findings:**

1. NSE and BSE publish near-real-time subscription updates on their IPO pages during the
   live subscription window. Once the window closes, this data is removed. There is no
   regulatory requirement to archive intraday subscription data.

2. Some IPO tracking websites have scraped subscription data during live windows for some
   recent IPOs. However, this is ad-hoc, not systematic, and available for a small subset
   of IPOs. Timestamps on historical "snapshots" may reflect retrieval time rather than
   exchange publication time.

3. Coverage decreases sharply before 2021 and is essentially absent before 2019.

4. No public dataset of consistently timestamped historical intraday IPO subscription
   snapshots exists for Indian Mainboard IPOs spanning 2018–2024.

**Critical implication:**

> **SUBSCRIPTION VELOCITY AND ACCELERATION FEATURES (Day 1 vs Day 2 buildup) CANNOT BE
> USED IN HISTORICAL BACKTESTING.**
>
> These features are only viable in live production when the system itself captures
> real-time snapshots during the subscription window. Including them in a historical
> model would create systematic train/test contamination — the model would be trained
> on features that did not exist in historical data and cannot be reconstructed.

**What we CAN use from subscription (historical):**
- Total subscription multiplier at T3 close
- QIB subscription fraction
- NII subscription fraction
- Retail subscription fraction
- Whether any category was under-subscribed (boolean)

**What we CANNOT use in historical training:**
- Day 1 subscription level
- Day 2 subscription level
- Intraday progression or velocity
- Subscription acceleration between days

---

## Section 4 — Historical GMP

**Conclusion: NOT RELIABLY AVAILABLE as genuine time-series; EXCLUDED from historical backtest**

### 4.1 Source-by-source assessment

```
Source:           InvestorGain.com
Historical range: ~2018–present
IPOs covered:     Most Mainboard IPOs; coverage patchy pre-2020
Granularity:      Single GMP value per IPO per "period" — NOT a daily time-series.
                  The "GMP Performance Tracker" shows one GMP value per IPO alongside
                  actual listing price.
Timestamp quality: UNKNOWN. No documented methodology for when the GMP value was captured.
                   May be a composite, average, or final-day value.
Observed vs retro: UNKNOWN — retroactive editing cannot be ruled out.
Reliability:       Low to medium. Unofficial; no methodology disclosure.
Licensing:         Free for reading. Commercial use terms not clearly stated.
```

```
Source:           Chittorgarh.com
Historical range: ~2017–present
IPOs covered:     Most Mainboard IPOs; some SME
Granularity:      Single GMP "at time of subscription" per IPO in annual tables.
                  Individual IPO pages may show multiple data points but inconsistently.
Timestamp quality: LOW — "Day 1 GMP", "Day 3 GMP" labels exist on some pages but are
                   not rigorously timestamped and may be retroactively filled.
Observed vs retro: HIGH RISK — websites can update historical pages without notice.
Reliability:       Low. Information sourced from grey market dealer networks.
Licensing:         Free for reading. IPOMatrix premium for bulk. Commercial use unclear.
```

```
Source:           IPOWatch.in
Historical range: ~2019–present
IPOs covered:     Mainboard and SME; smaller coverage than Chittorgarh
Granularity:      Per-IPO GMP with some day-wise breakdown on individual pages
Timestamp quality: LOW — same retroactive risk as above
Reliability:       Low
```

```
Source:           Wayback Machine (web.archive.org)
Historical range: Varies by URL; some GMP pages archived from 2019 onward
IPOs covered:     Unpredictable — depends on Wayback crawl frequency for each URL
Granularity:      Point-in-time snapshot of whatever the page showed at crawl time
Timestamp quality: HIGH — Wayback timestamps are reliable and cannot be retroactively edited
Observed vs retro: GOOD — archived pages reflect the state at crawl time
Reliability:       Medium — limited and unpredictable coverage
Notes:             This is the ONLY source of genuinely verified point-in-time historical GMP.
                   Coverage is too sparse and unpredictable for use as a systematic source.
                   Could supplement individual verifications but cannot replace systematic data.
```

### 4.2 Why historical GMP is excluded

Even if a GMP value exists for a historical IPO, two issues are unresolvable at scale:

1. **Retroactive editing:** GMP sites can update historical pages. A site showing "GMP was ₹80"
   may have updated this after the actual listing was known. Without per-snapshot Wayback
   verification, we cannot confirm the GMP was genuinely observed before listing.

2. **No time-series:** Available historical GMP is a single-point summary per IPO, not a
   day-by-day series. The GMP momentum feature (change from Day 1 to Day 3) described in the
   strategy spec is completely unavailable historically.

**Recommendations:**
- Exclude GMP from all historical model training and backtesting.
- GMP dynamics (change, momentum, volatility, cross-source agreement) are designated as
  **live-only features** — only usable once the production system captures them in real-time.
- For historical research, test whether NII subscription level serves as a partial proxy
  for market sentiment that GMP would otherwise capture.
- For live production: capture GMP from minimum two sources with explicit provenance
  and UTC timestamp. Cross-source agreement is itself a signal.

---

## Section 5 — Allotment / Basis of Allotment

### 5.1 SEBI Allotment Mechanics (Documented)

**Retail Individual Investor (RII) — applications up to ₹2 lakh:**
- Lottery-based when oversubscribed
- Each application for the minimum lot = one lottery entry
- Applying for more lots does NOT increase probability
- Formula (deterministic post-close):
  ```
  P(allotment_retail) = min(1.0, eligible_successful_applicants / total_valid_retail_applications)
  Approximation: if retail_sub_x > 1 → P ≈ 1 / retail_sub_x
                 if retail_sub_x ≤ 1 → P = 1.0
  ```

**NII / HNI — pre-September 2022 (pro-rata):**
- Proportional allotment: larger application = proportionally more shares
- P(allotment) ≈ 1.0 if NII_sub_x ≤ 1; else shares received ≈ (application / total_bids) × available_shares

**NII / HNI — post-September 2022 reform (sNII / bNII lottery):**
- SEBI split NII into sNII (₹2L–₹10L) and bNII (>₹10L)
- sNII receives 1/3 of NII quota; bNII receives 2/3
- Within each sub-category: minimum-lot lottery first (like retail), then pro-rata for remainder
- This regime change is material — the historical dataset spans both regimes

**QIB — Qualified Institutional Buyers:**
- Discretionary allotment; typically high certainty of receiving shares if bid accepted
- Not relevant for the retail investor the product targets

> **REGIME FLAG REQUIRED:** Every IPO record must carry a `sebi_nii_regime` field:
> - `PRE_2022` for IPOs closing before September 1, 2022
> - `POST_2022` for IPOs closing on or after September 1, 2022
> Allotment probability formulas differ between regimes.

**Key insight for the model:** For retail post-close, allotment probability is DETERMINISTIC
from SEBI mechanics + final subscription. No ML model is needed at T3. The estimator is
only needed at T0–T2 (before final subscription is known) — in that case we are estimating
final subscription (the uncertain variable), not allotment given subscription.

### 5.2 Basis of Allotment document availability

| Source | Coverage | Format | Notes |
|--------|----------|--------|-------|
| BSE publicissue portal | Good 2016–present; patchy pre-2016 | PDF links per IPO | Must be located per IPO |
| NSE IPO section | Good for listed companies | PDF links | |
| KFintech | IPOs where they are registrar (~40% of Mainboard) | PDF download | |
| Link Intime | IPOs where they are registrar (~35% of Mainboard) | PDF download | |
| Bigshare / Cameo | Remaining IPOs | PDF download | |
| Chittorgarh | Partial — links to BoA for many IPOs | External PDF links | Useful as directory |

**Historical coverage estimate:**
- 2020–2024: ~85–90% of Mainboard IPOs have accessible BoA PDFs
- 2018–2019: ~70–80%
- Pre-2017: Coverage drops significantly

**Data inside each BoA document:**
- Total valid applications per category
- Shares offered per category
- Number of successful applicants
- Lottery ratios and basis (1:N or pro-rata details)

This data enables: (a) computing actual historical P(allotment), (b) validating the SEBI formula
approximation, (c) training a pre-close allotment forecasting model.

---

## Section 6 — Listing Price Definition

### 6.1 Resolved definition

**Listing price = OPEN price in the NSE/BSE Bhav Copy on the stock's first trading day.**

On listing day, the exchange conducts a Special Pre-Open Session (9:00–9:55 AM):
- 9:00–9:45 AM: Order entry/modification/cancellation (IEP shown)
- 9:45–9:55 AM: Order matching at equilibrium price
- Resulting equilibrium price = the price at which the first trades execute = "listing price"
- Regular trading begins at 10:00 AM from this price

The `OPEN` field in the exchange Bhav Copy for a stock's first trading day is this equilibrium
price. It is exchange-certified, reproducible from official archives, and available for all
listed securities going back many years.

### 6.2 Disambiguation

| Term | Definition | Use in system |
|------|------------|--------------|
| **Listing price** | Pre-open equilibrium price on Day 1 = Bhav Copy OPEN | ✅ Canonical V1 target |
| **Opening price** | Same as listing price (common synonym) | ✅ Same thing |
| **First traded price** | Same as above in normal pre-open sessions | ✅ Same thing |
| **Day-1 close** | End-of-day price on first trading day | ❌ Not our target — influenced by post-open market movement |
| **Day-1 VWAP** | Volume-weighted average of all Day-1 trades | ❌ Not our target |
| **Issue price** | Fixed IPO allocation price per share | This is the cost basis |

### 6.3 Cross-validation note

Third-party sites (Chittorgarh, InvestorGain) report "listing price" which they derive from
Bhav Copy OPEN. These should match the exchange data. Prefer the Bhav Copy directly.

---

## Section 7 — Fundamentals and Valuation Feasibility

### 7.1 What is available from SEBI prospectuses

Every SEBI-mandated RHP/Prospectus contains:
- Last 3 audited fiscal years of financial statements (P&L, Balance Sheet, Cash Flow)
- Key metrics: Revenue, EBITDA, PAT, EPS, OCF, Capex
- Debt and leverage information
- Promoter holding (pre and post IPO)
- OFS vs fresh issue split
- Issue proceeds utilization plan
- Related party transactions (listed, qualitative)
- Litigation disclosures (qualitative)
- Peer comparison table with valuation multiples

**Point-in-time property:** ✅ Inherent. The prospectus contains financials as of the fiscal
periods ending before the DRHP/RHP filing date. A 2020 IPO prospectus contains FY2018/19/20
financials — NOT contaminated by post-IPO annual reports or restatements.

### 7.2 Engineering challenges

| Challenge | Severity | Mitigation |
|-----------|----------|------------|
| All data in PDF format | High | pdfplumber / camelot for table extraction; expect ~20% manual correction rate on first pass |
| Variable table layouts across issuers | Medium | Template matching; validate with 50-IPO sample |
| Financial period varies by filing date | Low | Parse "period ended" from each table header |
| Restatements between DRHP and RHP | Medium | Use RHP as canonical; flag DRHP-only records |
| Missing FCF / free cash flow | Medium | Mark `MISSING`; do not impute |
| Customer concentration / litigation | High | Qualitative — requires NLP or manual binary flag (out of scope V1) |

### 7.3 Commercial alternatives

Refinitiv (LSEG), Bloomberg, Capitaline hold structured Indian company financials. However:
- These may populate with post-IPO annual report data (not prospectus-era financials)
- Point-in-time accuracy for IPO-era data is uncertain — databases may backfill retroactively
- Subscription costs are material

**Recommendation:** Use SEBI prospectus PDFs as the primary source for IPO-era fundamentals.
This is the only guaranteed point-in-time source. For V1, extract a core set: Revenue CAGR,
PAT margin, EPS, P/E at issue price, debt/equity ratio, fresh/OFS ratio, promoter holding.
Expand to full set in V2 after baseline validation.

---

## Section 8 — Peer Valuation

### 8.1 Approach A — Issuer-stated peers (DRHP/RHP)

Every RHP includes a "Basis for Offer Price" section with a peer comparison table showing
selected listed peers, their financial metrics, and valuation multiples (P/E, P/B, EV/EBITDA).

**Feasibility:** ✅ This data EXISTS in every prospectus and is accessible via SEBI EFTS.

**Bias (confirmed):** Issuers and merchant bankers systematically select peers with higher
multiples to make the IPO price appear favourable. SEBI requires transparency of selection but
does not mandate objectively chosen peers. Biases include: cherry-picking high-multiple peers,
scale mismatches, sector reclassification to attract a premium.

**Useful for V1 as a feature, not as a clean benchmark:**
- `issuer_pe` = issue_price / IPO-era EPS (computable directly)
- `stated_peer_median_pe` = median P/E of DRHP-stated peers (from prospectus table)
- `pe_premium_to_peers` = (issuer_pe - stated_peer_median_pe) / stated_peer_median_pe

The magnitude of cherry-picking itself may be predictive. A company claiming to be "at peer
median" when priced at 3× peer median is a negative signal regardless of the direction of bias.

**Point-in-time quality:** ✅ The peer metrics in the prospectus reflect a specific stated date.
Peer stock prices can be verified against historical Bhav Copy data for cross-validation.

### 8.2 Approach B — System-selected peers

**Feasibility:** ❌ Not practical for V1.

Requires: (1) sector taxonomy, (2) point-in-time database of listed company financials,
(3) peer-selection algorithm. All three require significant infrastructure and introduce
their own methodology choices.

**Recommendation:**
> Use Approach A (DRHP-stated peers) in V1 with a clear `DRHP_STATED_BIAS` data quality flag.
> Develop Approach B in V2 after the baseline model is validated.

---

## Section 9 — Transaction Cost Model

### 9.1 Application side costs

| Cost | Applies? | Amount | Notes |
|------|----------|--------|-------|
| IPO application brokerage | ❌ No | Zero | Subscription-based; no brokerage on application |
| UPI/ASBA processing fee | ❌ No | Zero | Bank processes block; no investor charge |
| Stamp duty on application | ❌ No | Zero | Stamp duty is on transfer, not application |

**Application-side costs: zero for retail ASBA/UPI applicants.**

### 9.2 Sale-side costs (listing-day delivery sale)

| Cost | Rate | Notes |
|------|------|-------|
| Brokerage | Varies | Zero at zero-brokerage brokers; ₹20/trade flat at discount brokers. Must be configurable. |
| STT (Securities Transaction Tax) | 0.1% of sell value | Mandatory; sell side only for equity delivery |
| NSE Exchange Transaction Charge | ~0.00297% of turnover | Exchange-specific |
| BSE Exchange Transaction Charge | ~₹375 per crore | Different rate structure |
| SEBI Turnover Fee | 0.0001% of turnover | Very small |
| DP (Demat) Charges | ₹13–₹25 flat per scrip + 18% GST | Fixed per debit from demat; broker-specific |
| GST | 18% on (brokerage + exchange charges + SEBI fee) | Applied to service fees, not STT |
| Stamp duty | 0.015% (buy side only) | NOT applicable on sell side |

**Illustrative total regulatory cost for a ₹15,000 minimum lot sale:**
- STT: 0.1% × ₹15,000 = ₹15
- Exchange charges: ~0.003% × ₹15,000 = ₹0.45
- SEBI fee: ~0.0001% × ₹15,000 = ₹0.015
- DP charges: ~₹15–₹20
- GST on charges: ~₹1–₹2
- **Total: ~₹32–₹38 per minimum lot (excluding brokerage and capital gains tax)**

**Materiality check:** On a ₹15,000 application with 2% listing gain (₹300 gross profit),
regulatory costs of ~₹35 reduce profit by ~12%. At 8% gain (₹1,200), they reduce by ~3%.
This makes the +8% threshold approximately right as a minimum meaningful return.

**Capital gains tax:**
- Listing day sale = Short-Term Capital Gains (sold within 12 months of allotment)
- STCG rate: 20% (as of 2024 Union Budget; was 15% before)
- Must be tracked as a configurable historical rate — rate changed during the backtest window
- Report pre-tax EV and post-tax EV separately

### 9.3 Recommended V1 cost model parameters

```python
# Configurable per run; defaults below reflect standard retail conditions
BROKERAGE_PER_TRADE = 0          # ₹ (zero-brokerage default; override as needed)
STT_SELL_RATE = 0.001            # 0.1% of sell value
EXCHANGE_CHARGE_RATE = 0.0000297 # ~0.00297% (NSE); varies
SEBI_FEE_RATE = 0.000001         # 0.0001%
DP_CHARGE_FLAT = 20              # ₹ per scrip per debit
GST_RATE = 0.18                  # 18% on service fees
STCG_RATE = 0.20                 # 20% short-term capital gains (post-2024)
# Historical: use 0.15 for listings before July 23, 2024

# Opportunity cost
OPPORTUNITY_COST_RATE = "91_day_tbill_annualized"  # configurable; see Section 10
```

---

## Section 10 — Blocked Capital Opportunity Cost

### 10.1 ASBA Timeline

**Current (effective December 1, 2023): T+3**

| Day | Event |
|-----|-------|
| T – 3 to T | Application window; funds blocked via ASBA/UPI lien |
| T | Subscription closes (5:00 PM) |
| T+1 | Allotment finalized; lottery conducted |
| T+2 | Non-allottees: lien released. Allottees: shares credited to demat |
| T+3 | Listing day; trading begins 10:00 AM |

**Failed allotment blocked window:** Application date → T+2 (approximately 5–8 calendar days)
**Successful allotment + listing day sale:** Application date → T+3 (approximately 6–10 calendar days), then cash from sale receipt

**Historical note (pre-December 2023): T+6**
Before December 1, 2023, the timeline was T+6: capital was blocked for approximately 9–13
calendar days. This regime change must be tracked in the historical dataset:
- `timeline_regime = T6` for IPOs closing before December 1, 2023
- `timeline_regime = T3` for IPOs closing on or after December 1, 2023

**ASBA interest note:** Under ASBA, the blocked amount remains in the investor's savings account
and continues earning savings interest during the block period. This partially offsets the
opportunity cost. For conservatism, V1 does not credit this back (slightly overstates cost).

### 10.2 Opportunity cost recommendation

**Recommended: Option B — configurable opportunity cost rate (91-day T-bill annualized)**

**Rationale:**
- 91-day T-bill yield is a widely accepted risk-free rate in Indian finance
- It reflects the actual borrowing cost of capital for the blocking period
- It was approximately 5.5–7.5% annualized during 2018–2024

**Formula:**
```
block_days = (listing_date - application_date)  # calendar days
annual_rate = tbill_91d_rate_at_decision_date   # configurable; use historical rate for backtest
opportunity_cost_per_lot = (application_amount_per_lot × annual_rate × block_days) / 365
```

**Full V1 EV formula (per application, retail minimum lot):**
```
gross_profit = lot_size × issue_price × expected_listing_return
allotment_prob = min(1.0, 1 / max(1, expected_final_retail_sub_x))

sell_side_costs = (lot_size × listing_price × STT_rate)
                + (lot_size × listing_price × exchange_charge_rate)
                + (lot_size × listing_price × sebi_fee_rate)
                + DP_charge_flat
                + brokerage_per_trade
                + GST_rate × (brokerage + exchange_charge + sebi_fee)

opportunity_cost = lot_size × issue_price × tbill_rate × block_days / 365

net_profit_if_allotted = gross_profit - sell_side_costs - opportunity_cost

EV_net_per_application = allotment_prob × net_profit_if_allotted
```

---

## Section 11 — Coverage Matrix

| Dataset | Historical coverage | Point-in-time quality | Source quality | Usable for historical backtest? |
|---------|--------------------|-----------------------|----------------|--------------------------------|
| IPO master (dates, price, lot size) | 🟢 2015–2024, ~95% | ✅ DRHP/RHP filings | 🟢 NSE/BSE + SEBI | ✅ Yes |
| Listing prices (label) | 🟢 2005–2024, ~99% | ✅ Bhav Copy Day 1 OPEN | 🟢 NSE/BSE Bhav Copy | ✅ Yes |
| Final subscription (QIB/NII/Retail) | 🟡 2018–2024, ~80% | ✅ Captured at T3 close | 🟡 Third-party aggregators | ✅ Yes (with source flag) |
| Final subscription pre-2018 | 🔴 2015–2017, <50% | Partial | 🔴 Sparse | ⚠️ Conditional |
| Intraday subscription snapshots | 🔴 Not available historically | ❌ Not archived | ❌ None reliable | ❌ No |
| GMP (production, realtime) | 🟡 Obtainable going forward | ✅ If captured with timestamp | 🔴 Unofficial, multiple sources | ✅ Live only (not historical) |
| Historical GMP time-series | 🔴 Not reliably available | ❌ Retroactive risk | 🔴 No methodology | ❌ No |
| Allotment / BoA documents | 🟡 2018–2024, ~80–90% | ✅ Post-listing outcome data | 🟡 Exchange/registrar PDFs | ✅ Yes |
| SEBI/RHP fundamentals | 🟡 2004–present (PDFs) | ✅ Prospectus is point-in-time | 🟢 SEBI EFTS | ✅ Yes (requires PDF parsing) |
| Peer valuation (DRHP-stated) | 🟡 2015–present (PDFs) | ✅ From prospectus | 🟡 Biased but usable | ✅ Yes with bias flag |
| Market / Nifty / VIX | 🟢 VIX 2008+; Nifty 1990s+ | ✅ Date-indexed | 🟢 NSE historical | ✅ Yes |
| Sector index returns | 🟢 2010–present | ✅ Date-indexed | 🟢 NSE sectoral | ✅ Yes |
| Transaction costs | 🟢 Rates documented | ✅ Use historical rates per regime | 🟢 SEBI/exchange publications | ✅ Yes |

---

## Section 12 — Blocking Data Gaps

### Critical — blocks V1 historical backtest as originally documented

| Gap | Impact | Resolution |
|-----|--------|------------|
| Intraday subscription data | Velocity/acceleration features impossible historically | Remove from historical model. Add as live-only features in production. |
| Historical GMP time-series | GMP momentum/dynamics impossible historically | Remove from historical model. Capture in production from Day 1. |
| PDF parsing infrastructure | Cannot extract fundamentals at scale without it | Required engineering task before Phase 2. Scope: extract core financials from RHP PDFs for ~480 IPOs. High effort; ~2–3 weeks. |
| BoA PDF collection | Allotment model unvalidatable | Collect BoA PDFs; extract category-wise allotment data for allotment model validation. |

### High — affects model quality

| Gap | Impact | Resolution |
|-----|--------|------------|
| Final subscription coverage pre-2018 | Shrinks training set | Use 2018 as practical start date for high-quality subscription data |
| NII 2022 regime break | Different allotment formula for pre/post-Sept 2022 IPOs | Add `sebi_nii_regime` flag to all IPO records; use correct formula per regime |
| DRHP peer cherry-picking bias | Valuation features inherit selection bias | Flag as `DRHP_STATED_BIAS`; use premium/discount to stated peers as a feature |
| STCG rate change (2024) | Historical cost calculations must use rate at listing date | Parameterize STCG rate by date; track rate change (15% → 20% July 23, 2024) |
| T+6 → T+3 timeline change | Opportunity cost differs across history | Track `timeline_regime` per IPO; use correct block duration in cost model |

### Medium — manageable

| Gap | Impact | Resolution |
|-----|--------|------------|
| Small IPO fundamental coverage | Smaller IPOs may have incomplete PDF data | Use data quality flags; potentially exclude if critical fields missing |
| Aggregator cross-source discrepancies | Some final subscription figures may differ by rounding | Cross-validate against BoA documents where available |
| Rare delayed/partial listing | Bhav Copy OPEN may be misleading for circuit-limit opens | Flag these manually; exclude or handle separately |

---

## Section 13 — Recommended V1 Dataset

**Feature set available for historical backtest (2018–2024 Mainboard IPOs)**

### Issue structure features ✅
```
issue_price
lot_size
min_application_amount
issue_size_cr
fresh_issue_fraction       (fresh_issue / total_issue_size)
ofs_fraction               (ofs / total_issue_size; high OFS = promoter exit signal)
retail_quota_pct
qib_quota_pct
nii_quota_pct
price_band_width_pct       ((band_high - band_low) / band_high)
sebi_nii_regime            (PRE_2022 | POST_2022)
timeline_regime            (T6 | T3)
```

### Fundamental features ✅ (from SEBI RHP PDFs; requires parsing)
```
revenue_cagr_3yr
ebitda_margin_latest
pat_margin_latest
pe_ratio_at_issue          (issue_price / restated_eps)
debt_equity_ratio
roe_latest
roce_latest
promoter_holding_pre_ipo_pct
ofs_fraction               (duplicate as fundamental signal)
ocf_positive               (boolean: was operating cash flow positive in latest year?)
data_quality_fundamentals  (VERIFIED_PRIMARY | MISSING | CONFLICTING)
```

### Valuation features ✅ (from SEBI RHP PDFs)
```
pe_ratio_at_issue
stated_peer_median_pe      (median P/E of DRHP-stated peers)
pe_premium_to_peers        ((issuer_pe - peer_median_pe) / peer_median_pe)
implied_mcap_to_issue_size (implied market cap at issue price / issue size)
data_quality_valuation     (VERIFIED_PRIMARY | MISSING)
```

### Final subscription features ✅ (from Chittorgarh / InvestorGain)
```
retail_subscription_x
nii_subscription_x
qib_subscription_x
total_subscription_x
retail_oversubscribed      (retail_subscription_x > 1)
nii_oversubscribed         (nii_subscription_x > 1)
qib_oversubscribed         (qib_subscription_x > 1)
any_category_under_1x      (boolean)
data_quality_subscription  (VERIFIED_PRIMARY | VERIFIED_SECONDARY | MISSING)
```

### Allotment features ✅ (deterministic SEBI formula)
```
retail_allotment_prob      = min(1.0, 1 / max(1.0, retail_subscription_x))
snii_allotment_prob        (post-Sept 2022: similar lottery; pre: proportional)
```

### Market regime features ✅ (from NSE historical data)
```
nifty_return_30d           (prior 30-day Nifty return at IPO open date)
nifty_return_7d            (prior 7-day Nifty return)
india_vix_at_open          (VIX level at IPO subscription open date)
nifty_return_listing_minus1 (Nifty return on day before listing; NOT during subscription)
recent_ipo_avg_return_30d  (mean listing return of Mainboard IPOs listed in prior 30 days;
                            strict: listing_date < current_ipo_open_date)
recent_ipo_pct_positive_30d (% of prior-30-day IPOs with positive listing)
```

### NOT included in V1 historical model ❌
```
Subscription velocity / acceleration   → live-only feature
Subscription Day 1 / Day 2 levels      → live-only feature
GMP or GMP momentum                    → live-only feature
NLP sentiment / news                   → out of scope per PRD
Customer concentration (qualitative)   → out of scope V1
Litigation flags (qualitative)         → out of scope V1
```

---

## Section 14 — Estimated Base Rates (Indicative)

Based on secondary research; must be verified against actual collected data before use.

| Period | Approx. % positive listing | Notes |
|--------|---------------------------|-------|
| 2018–2019 | ~39–45% | Cautious market; NBFC stress |
| 2020 | Mixed; improving through year | COVID disruption early; recovery later |
| 2021 | ~65–75% | Strong bull market; high listings premium |
| 2022 | ~50–60% | Rate hikes; more selective |
| 2023 | ~55–65% | Recovery; selective IPOs |
| 2024 | ~65–75% | Record IPO year; generally strong |
| **2018–2024 combined** | **~55–62% estimated** | Must be verified empirically |

> **These are directional estimates only.** Computing the actual base rate is the first task
> in Phase 1 data collection and should be the first number reported before any modeling begins.
> The 70% APPLY threshold in the strategy spec is higher than the estimated unconditional
> base rate, which is appropriate — the model must select above-average IPOs.

---

## Section 15 — Risk Register

### Critical risks

| Risk | Description |
|------|-------------|
| PDF parsing failure rate | Extracting fundamentals from SEBI PDFs will have errors. If >30% of records have critical field errors, fundamentals cannot be used at scale. Mitigate: manual validation on 50-IPO sample before committing to full extraction. |
| Regime bias (2020–2021 boom) | Majority of positive-listing observations cluster in the bull period. Model may learn "always apply" rather than genuine signal. Mitigate: evaluate performance separately per market regime in backtesting. |
| Aggregator subscription data quality | Final subscription figures from Chittorgarh/InvestorGain may contain errors for older IPOs. Mitigate: cross-validate against BoA documents. |

### High risks

| Risk | Description |
|------|-------------|
| Small sample size | ~480 usable observations with 2018–2024 window is small for ML. Severely limits model complexity. V1 must use simple, regularized models only. |
| Allotment formula approximation | Retail formula assumes uniform minimum applications. HNIs applying as retail (against rules) distort the formula. Mitigate: validate formula against actual BoA outcomes. |
| GMP signal loss | GMP excluded from historical model; predictive power may be lower than with GMP. Accept this limitation; add GMP in live production and evaluate in shadow mode. |

### Medium risks

| Risk | Description |
|------|-------------|
| Listing price discrepancy | Some aggregator sites show day-1 close rather than day-1 open as "listing price." Always use Bhav Copy OPEN directly. |
| STCG rate change mid-history | STCG rate changed in July 2024. Historical cost calculations must use the rate prevailing at each listing date. |
| Prospectus peer cherry-picking | Valuation features inherit issuer selection bias. Treat as a feature (bias magnitude may be predictive), not as a clean benchmark. |

### Low risks

| Risk | Description |
|------|-------------|
| NSE/BSE listing asymmetry | A small number of IPOs list on only one exchange. Use NSE Bhav Copy; fallback to BSE. |
| Nifty/VIX data gaps | VIX available from 2008; no risk for 2018–2024. |

---

## Section 16 — Strategy Adjustment Required

The original strategy spec assumed GMP dynamics and subscription velocity as central features.
Both are infeasible for historical backtesting.

**Decision: Option B — Proceed with reduced feature strategy**

The reduced strategy is scientifically valid and economically meaningful. It uses:
1. Final subscription (quantifies actual market demand at close)
2. Issue fundamentals and valuation (from prospectus — inherently point-in-time)
3. Market regime (Nifty, VIX, recent IPO window)
4. Issue structure (OFS fraction, lot size, fresh issue ratio)

**GMP and subscription velocity become live-only features:**
- Designed into the production system data capture from Day 1 of going live
- Used in production predictions immediately
- Incorporated into the historical model only after 12+ months of live data accumulates
- At that point: hybrid historical + live dataset can support full feature evaluation

**Implication for model capability:**
- V1 historical model: 6–9 features; interpretable logistic regression / linear model
- V1 live model: same + live GMP + live intraday subscription snapshots (richer predictions)
- V2 (12+ months live data): full feature set, potentially ensemble models

---

## Section 17 — GO / NO-GO Decision

### ✅ CONDITIONAL GO

The strategy can be honestly backtested with real data using the reduced feature set in
Section 13. This is NOT a redesign — the same product objective, EV framework, and
APPLY/WATCH/SKIP logic applies. Only the feature inputs change for the historical phase.

**Pre-coding gates still required (before any application code):**

| Gate | Status | First action |
|------|--------|--------------|
| G1: IPO universe list (2018–2024 Mainboard, ~535 rows) | ⬜ Not done | Collect from Chittorgarh + NSE/BSE |
| G2: Listing prices (Bhav Copy OPEN, 2018–2024) | ⬜ Not done | Download NSE/BSE Bhav Copies for listing dates |
| G3: Final subscription data (QIB/NII/Retail, 2018–2024) | ⬜ Not done | Collect from Chittorgarh + InvestorGain |
| G4: Base rate computed (% positive listings 2018–2024) | ⬜ Not done | First EDA task after G1–G3 complete |
| G5: Nifty/VIX historical data (2017–2024) | ⬜ Not done | Download from NSE historical; one-time task |
| G6: BoA PDFs collected (sample: 50 IPOs) | ⬜ Not done | Validate allotment formula |
| G7: PDF parsing prototype (core financials, 10 IPOs) | ⬜ Not done | Validate feasibility before full extraction |

**G1–G4 must be complete before any feature engineering code is written.**
**G5–G7 must be complete before model training begins.**

No modeling, no feature engineering, no production ingestion pipeline until G1–G4 are done.

---

*Document version: 1.0*
*Status: Research complete. All findings are based on secondary research and require direct
source validation before production use. No data has been collected; no code has been written.*
*Next step: Execute data collection gates G1–G4.*
