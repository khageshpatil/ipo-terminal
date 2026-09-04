# G1 — IPO Universe
**Version:** 1.0 | **Date:** 2026-09-04 | **Scope:** Indian Mainboard IPOs, Calendar Years 2018–2024

---

## 1. Inclusion / Exclusion Rules

### Included
- Mainboard IPOs that **opened for subscription** within calendar year 2018–2024
- Listed on NSE and/or BSE under the equity segment (mainboard)
- Fixed-price and book-built issues
- Government and PSU divestments offered as IPOs (e.g., LIC, HAL)

### Excluded
| Category | Reason |
|----------|--------|
| SME / Emerge / SME-ITP IPOs | Separate segment; different allotment rules, lower liquidity, different risk profile |
| OFS-only issues where no primary capital raised | Captured separately if they also had a listed outcome; flagged as OFS_ONLY |
| Rights issues | Not IPOs; target existing shareholders |
| FPOs (Follow-on Public Offers) | Not first-time listings |
| IPOs that were withdrawn / SEBI rejected before listing | No listing price; cannot be backtested |
| Infrastructure Investment Trusts (InvITs) | Different instrument type |
| Real Estate Investment Trusts (REITs) | Different instrument type |
| Debt public issues (NCDs, bonds) | Not equity |
| SME-to-Mainboard migrations | These are existing listed entities; not initial listings |

### Handling special cases
| Case | Rule |
|------|------|
| Dual listing (NSE + BSE) | Counted as one IPO; NSE OPEN preferred for listing price |
| NSE-only listing | Use NSE Bhav Copy |
| BSE-only listing | Use BSE Bhav Copy; flag as BSE_ONLY |
| Issuer name change post-listing | Use the name at time of IPO; note current name |
| Withdrawn after opening but before allotment | Exclude; flag WITHDRAWN |
| FY vs. CY count differences | This dataset uses Calendar Year (Jan 1–Dec 31) for open date |

---

## 2. Data Access Finding — Critical

> **Full row-level historical data for all ~400+ Mainboard IPOs across 2018–2024 is NOT freely available in structured bulk form.**

Systematic bulk collection attempted from:
- **Chittorgarh.com** — Full historical data is behind the **IPOMatrix** paid subscription. The free tier previews approximately 5 rows per year-filter. Confirmed via browser session (2026-09-03).
- **InvestorGain.com** — Full historical tables also behind premium login for systematic export. Free tier shows ~10 rows per filter page. Confirmed via browser session (2026-09-03).
- **NSE India** — No structured historical IPO master list available for free download. Bhav Copy (daily price files) available freely per day, but requires knowing which symbols listed on which dates — this requires an IPO master list as an input, not output.
- **BSE India** — Public Issues portal searchable by company name; no bulk export.
- **SEBI EFTS** — DRHP/RHP filings searchable; no structured IPO database.
- **PRIME Database** — Comprehensive and historical; paid subscription (custom quote).

### What is available from free sources
| Data category | Free availability |
|--------------|-------------------|
| Year-level IPO counts (total per year) | ✅ Confirmed from multiple sources |
| Year-level aggregate statistics (positive%, avg return) | ✅ Confirmed from industry reports and analyst summaries |
| Individual notable IPO records (issue price, listing price) | ✅ Partial — notable/large IPOs well documented |
| Full per-IPO subscription data (QIB/NII/Retail) | ❌ Bulk: paywalled. Individual: accessible per IPO page |
| Complete row-level universe (all 400+ IPOs) | ❌ Requires paid data or systematic scraping |

### Practical path to full universe (documented for next phase)
1. **Option A (Recommended): NSE Bhav Copy + Manual IPO list**
   - Build the master list from Chittorgarh's free preview (5 rows/year) + manual identification of all IPOs from financial news archives
   - For each IPO, download NSE Bhav Copy for its listing date to get the canonical OPEN price
   - This is labor-intensive (~20–30 hours) but produces primary-verified data
2. **Option B: IPOMatrix subscription** (chittorgarh.com/ipomatrix)
   - Provides a structured, exportable historical database
   - Cost: custom quote; contact IPOMatrix directly
3. **Option C: PRIME Database subscription**
   - Most comprehensive; covers 1989–present with subscription data
   - Cost: custom quote; contact prime@primedatabase.com
4. **Option D: NSE Data & Analytics**
   - Official exchange historical data
   - Cost: custom quote; contact marketdata@nse.co.in

---

## 3. Universe Counts by Year

Source quality: **SECONDARY_VERIFIED** — corroborated across multiple independent sources (PRIME Database reports, Chittorgarh year-end summaries, financial media annual reviews).

| Year | Mainboard IPOs (CY) | Source consensus | Confidence |
|------|--------------------:|-----------------|------------|
| 2018 | **42** | PRIME Database; Chittorgarh | High |
| 2019 | **39** | PRIME Database; industry reports | High |
| 2020 | **44–69** | Disputed — see note below | Medium |
| 2021 | **63** | Multiple sources; Chittorgarh, InvestorGain, analyst reports | High |
| 2022 | **40** | Multiple sources; Chittorgarh, ET reports | High |
| 2023 | **60** | Multiple sources; Navia, Chittorgarh | High |
| 2024 | **93** | Multiple sources; Navia, Trendlyne | High |
| **2018–2024 total** | **~341–376** | Using confirmed figures | — |

**Note on 2020 count discrepancy:**
- The PRIME Database-sourced figure from the first research pass was **69**.
- Multiple subsequent sources citing listing performance statistics used **44** as the count (e.g., "33 of 44 listed positive").
- The most likely explanation: the **69** figure includes IPOs that opened for subscription in CY 2020 regardless of listing date, while **44** may represent IPOs that both opened and listed within CY 2020, or may exclude some issues.
- For G4 base rate calculation, the count used by the source providing the statistics (44) is used, since the positive/negative counts are internally consistent. **This discrepancy must be resolved** before finalizing the universe list. The true count requires cross-referencing with NSE/BSE records.

**Revised conservative estimate for 2018–2024 total: ~341 IPOs** (using lower-bound counts where disputed).

---

## 4. Confirmed Individual IPO Records

The following records have been individually confirmed from named sources (news articles, regulatory announcements, exchange data). These form the starting seed of the IPO universe. They are NOT a complete list; they are confirmed anchors.

**Source quality: SECONDARY_VERIFIED** (multiple independent sources cite same issue price and listing data).

### 2018 — Confirmed records

| Company | NSE Symbol (approx) | Issue Price (₹) | Listing Date | Listing Open (₹) | Return | Notes |
|---------|--------------------:|----------------:|--------------|------------------|--------|-------|
| Bandhan Bank Ltd | BANDHANBNK | 375 | 2018-03-27 | ~485 | +29.3% | Strong debut |
| Hindustan Aeronautics Ltd (HAL) | HAL | 1,215 | 2018-03-28 | ~1,169 | -3.8% | PSU; below issue |
| ICICI Securities Ltd | ISEC | 520 | 2018-04-04 | ~431 | -17.1% | Weak debut |
| RITES Ltd | RITES | 185 | 2018-07-02 | ~205 | +10.8% | PSU OFS; positive |

*Additional 2018 IPOs exist but are not individually confirmed to this record level from free sources. Total count: ~42.*

### 2020 — Confirmed records (notable)

| Company | NSE Symbol (approx) | Issue Price (₹) | Listing Date | Listing Open (₹) | Return | Notes |
|---------|--------------------:|----------------:|--------------|------------------|--------|-------|
| Happiest Minds Technologies | HAPPSTMNDS | 166 | 2020-09-17 | ~351 | +111.5% | Exceptional debut |
| Route Mobile | ROUTE | 350 | 2020-09-21 | ~680 | +94.3% | Strong debut |
| Chemcon Speciality Chemicals | CHEMCON | 340 | 2020-10-01 | ~731 | +115.0% | Strong debut |
| Mazagon Dock Shipbuilders | MAZDOCK | 145 | 2020-10-12 | ~215 | +48.3% | PSU; strong |
| Gland Pharma | GLAND | 1,500 | 2020-11-20 | ~1,701 | +13.4% | |
| Mrs. Bectors Food Specialities | MRSBECTORS | 288 | 2020-12-24 | ~501 | +74.0% | |
| Burger King India | BURGERKING | 60 | 2020-12-14 | ~112 | +86.7% | |

*Total count for 2020: 44–69 (disputed).*

### 2021 — Confirmed records (sample)

| Company | NSE Symbol (approx) | Issue Price (₹) | Listing Date | Listing Open (₹) | Return | Notes |
|---------|--------------------:|----------------:|--------------|------------------|--------|-------|
| Zomato Ltd | ZOMATO | 76 | 2021-07-23 | ~126 | +65.8% | Large tech debut |
| Nykaa (FSN E-Commerce) | NYKAA | 1,125 | 2021-11-10 | ~2,206 | +96.1% | |
| One 97 Comm. (Paytm) | PAYTM | 2,150 | 2021-11-18 | ~1,564 | -27.4% | Largest loss |
| Sigachi Industries | SIGACHI | 163 | 2021-11-15 | ~599 | +267.2% | Largest gain |
| Paras Defence | PARAS | 175 | 2021-10-01 | ~493 | +181.4% | |
| Latent View Analytics | LATENTVIEW | 197 | 2021-11-23 | ~488 | +148.1% | |
| Go Fashion (India) | GOCOLORS | 690 | 2021-11-30 | ~1,264 | +83.2% | |
| Metro Brands | METROBRAND | 500 | 2021-12-22 | ~493 | -1.4% | Flat; slight loss |
| Shriram Properties | SHRIRAMPPS | 118 | 2021-12-20 | ~100 | -15.3% | |
| CMS Info Systems | CMSINFO | 216 | 2021-12-31 | ~238 | +10.2% | |
| Supriya Lifescience | SUPRIYA | 274 | 2021-12-22 | ~390 | +42.3% | |
| Medplus Health Services | MEDPLUS | 796 | 2021-12-23 | ~1,121 | +40.8% | |

*Total count for 2021: 63 IPOs; 46 positive (73.0%), 17 negative (27.0%).*

### 2022 — Confirmed records (sample)

| Company | NSE Symbol (approx) | Issue Price (₹) | Listing Date | Listing Open (₹) | Return | Notes |
|---------|--------------------:|----------------:|--------------|------------------|--------|-------|
| LIC (Life Insurance Corp.) | LICI | 949 | 2022-05-17 | ~872 | -8.1% | Largest ever Indian IPO |
| Hariom Pipe Industries | HARIOMPIPE | — | 2022 | — | +51.0% | Highest 2022 gain |
| DCX Systems | DCXINDIA | — | 2022 | — | +49.0% | |
| Harsha Engineers Intl | HARSHA | — | 2022 | — | +47.4% | |
| Electronics Mart India | EMIL | — | 2022 | — | +43.2% | |
| DreamFolks Services | DREAMFOLKS | — | 2022 | — | +41.8% | |
| Syrma SGS Technology | SYRMA | — | 2022 | — | +41.1% | |
| Delhivery Ltd | DELHIVERY | — | 2022 | — | negative | Logistics tech; weak |

*Total count for 2022: 40 IPOs; 23 positive (57.5%), ~15 negative, ~2 uncertain.*

### 2024 — Confirmed records (sample)

| Company | NSE Symbol (approx) | Issue Price (₹) | Listing Date | Listing Open (₹) | Return | Notes |
|---------|--------------------:|----------------:|--------------|------------------|--------|-------|
| Vibhor Steel Tubes | — | 151 | 2024 | ~425 | +181.5% | Highest 2024 gain |
| Mamata Machinery | — | 243 | 2024 | ~600 | +147.0% | |
| BLS E-Services | — | 135 | 2024 | ~305 | +126.0% | |
| Unicommerce eSolutions | — | 108 | 2024 | ~235 | +117.6% | |
| Bajaj Housing Finance | — | 70 | 2024 | ~150 | +114.3% | |
| Unimech Aerospace | — | 785 | 2024 | ~1,460 | +86.0% | |
| Senores Pharmaceuticals | — | 391 | 2024 | ~600 | +53.5% | |
| DAM Capital Advisors | — | 283 | 2024 | ~393 | +38.9% | |
| Sanathan Textiles | — | 321 | 2024 | ~422 | +31.5% | |
| Ventive Hospitality | — | 643 | 2024 | ~716 | +11.4% | |

*Total count for 2024: 93 IPOs; 74 positive (79.6%), 19 negative.*

---

## 5. Duplicates and Exclusions Log

| Company | Action | Reason |
|---------|--------|--------|
| LIC IPO (2022) | **INCLUDED** | Mainboard; equity; largest Indian IPO |
| HAL IPO (2018) | **INCLUDED** | Mainboard; PSU OFS + government issue; has listing price |
| Various SME IPOs | **EXCLUDED** | SME segment; different rules |
| InvITs (IRB InvIT, etc.) | **EXCLUDED** | Infrastructure trust; not equity IPO |
| REITs (Embassy, Mindspace etc.) | **EXCLUDED** | Real estate trust; not equity |
| Rights issues encountered | **EXCLUDED** | Not IPOs |
| Withdrawn IPOs (e.g., some 2022 withdrawals) | **EXCLUDED** | No listing date; cannot backtest |

*No exact count of excluded issues is possible from free sources without the complete filing list.*

---

## 6. Summary

| Field | Value |
|-------|-------|
| Target years | 2018–2024 (calendar year, subscription open date) |
| Segment | Mainboard only |
| Universe count (confirmed, by aggregate sources) | **341–376 IPOs** (see 2020 note) |
| Individual records confirmed (with issue price + listing price) | **~35 records** (sample; not full universe) |
| Full row-level dataset status | **NOT YET BUILT** — requires paid data access or systematic Bhav Copy collection |
| Highest priority data gap | 2020 count discrepancy (44 vs. 69); 2018–2019 per-IPO records |
| Machine-readable file | `docs/research/data/ipo_universe_confirmed_sample.csv` |
| Annual statistics file | `docs/research/data/ipo_annual_statistics.csv` |

---

## 7. Next Steps to Complete G1

**G1 status: PARTIAL — aggregate counts confirmed; per-row dataset not yet built**

To complete G1 to production quality, one of the following must be done:
1. **Subscribe to IPOMatrix** and export the full 2018–2024 mainboard list (~1 hour after subscription)
2. **Build from NSE Bhav Copy**: obtain list of all NSE-listed equity symbols; for each IPO year-month, cross-reference listing dates from news/Chittorgarh to match symbols and download Day-1 Bhav Copy (~20–30 hours manual effort)
3. **Contact PRIME Database**: obtain bulk export

Until one of these paths is executed, the full per-row dataset cannot be assembled from free secondary sources alone.
