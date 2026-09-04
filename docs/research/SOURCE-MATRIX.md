# Source Matrix — IPO Listing-Gain Decision Engine
**Version:** 1.0 | **Date:** 2026-09-03

For every source, verification against the actual live URL must precede production dependency.

---

## Tier 1 — Official / Regulatory Sources

| Source | URL | Data available | Depth | API? | Cost | Reliability | Notes |
|--------|-----|----------------|-------|------|------|-------------|-------|
| NSE India — IPO pages | nseindia.com/market-data/all-upcoming-issues-ipo | Issue terms; live subscription | Current only (subscription) | No official API | Free | High (exchange-certified) | Subscription data removed post-close |
| NSE India — Bhav Copy (historical equity) | nseindia.com (Data Products section) | OHLCV daily per symbol | 10+ years | No (CSV download) | Free for public; paid for bulk | High | Bhav Copy OPEN on listing day = listing price |
| BSE India — Public Issues | bseindia.com/publicissue.html | Offer documents, BoA links, IPO master | 10+ years | No | Free | High | Offer docs as PDFs |
| BSE India — Bhav Copy | bseindia.com | OHLCV daily per symbol | 10+ years | No (CSV download) | Free | High | Alternative to NSE |
| SEBI EFTS | sebi.gov.in/filings.html | DRHP, RHP, Final Prospectus | 2004–present | No | Free | Highest (legal filings) | PDF only; requires structured extraction |
| NSE Data & Analytics | nseindia.com/products/content/other_data_info.htm | Historical IPO subscription (structured) | Historical | Contact required | Paid (quoted on request) | High | Contact: marketdata@nse.co.in; +91-22-2659-8385 |

---

## Tier 2 — Licensed / Professional Sources

| Source | URL | Data available | Depth | API? | Cost | Reliability | Notes |
|--------|-----|----------------|-------|------|------|-------------|-------|
| PRIME Database | primedatabase.com | Full primary market DB: subscription, issue responses, pricing, financials | 1989–present | No (subscription-based structured DB) | Paid (custom quote) | High | Contact: prime@primedatabase.com; +91-11-4100-8346. Most comprehensive single source. |
| Trendlyne | trendlyne.com | IPO dashboard, subscription, listing stats | ~2018–present | Freemium API | Freemium | Medium | Useful for secondary validation |

---

## Tier 3 — Specialized IPO / GMP Aggregators

| Source | URL | Data available | Depth | Structured? | Reliability | Key limitation |
|--------|-----|----------------|-------|-------------|-------------|----------------|
| Chittorgarh | chittorgarh.com | Year-wise IPO list, issue price, listing price, final subscription, GMP summary | 2006–present | Web tables; limited export | Medium (scrapes exchanges) | Not structured/API; GMP timestamps unverified; IPOMatrix premium for bulk |
| InvestorGain | investorgain.com | IPO performance tracker, GMP summary, subscription history | ~2015–present | Web tables; no API | Medium | Same caveats as Chittorgarh; single GMP value per IPO (not time-series) |
| IPOWatch | ipowatch.in | IPO info, GMP, subscription | ~2019–present | Web tables; no API | Low–Medium | Smaller coverage; same retroactive risk for GMP |
| IPOMatrix (Chittorgarh premium) | chittorgarh.com/iipomatrix | Deep historical IPO data including subscription detail | 2006–present | Paid export | Medium-High | Paid; may provide more granular subscription history than free tier |

---

## Tier 3 — Registrar Sources (Allotment / BoA)

| Registrar | URL | Data | Depth | Access | Reliability | Notes |
|-----------|-----|------|-------|--------|-------------|-------|
| KFintech | ipostatus.kfintech.com | Allotment status (PAN lookup), BoA PDFs | Recent / 3–5 yr archive | PAN lookup; PDF download | High (regulated) | Handles ~40% of Mainboard IPOs |
| Link Intime (MUFG Intime) | linkintime.co.in/MIPO/Ipoallotment.html | Allotment status (PAN lookup), BoA PDFs | Recent / 3–5 yr archive | PAN lookup; PDF download | High (regulated) | Handles ~35% of Mainboard IPOs |
| Bigshare Services | bigshareonline.com | Allotment status, BoA PDFs | Varies | Web lookup | High (regulated) | Smaller share of IPOs |
| Cameo Corporate Services | cameoindia.com | Allotment status, BoA PDFs | Varies | Web lookup | High (regulated) | Smaller share of IPOs |

---

## Tier 4 — Manual / Research Fallback

| Source | Use case | Notes |
|--------|----------|-------|
| Wayback Machine (web.archive.org) | Point-in-time GMP verification for specific IPOs | Only truly verified historical GMP. Coverage unpredictable. |
| SEBI Annual Reports | Aggregate IPO statistics, regulatory changes | Useful for confirming year-wise IPO counts and regime changes |
| Financial newspapers (Mint, ET, Business Standard archives) | Qualitative context, IPO-era market sentiment | Secondary reference only; not a data source |

---

## Market Data Sources

| Source | Data | Depth | Access | Notes |
|--------|------|-------|--------|-------|
| NSE India — Historical Indices | Nifty 50 index level, daily OHLC | 1990s–present | Free download (CSV) | Use for nifty_return features |
| NSE India — India VIX | Daily VIX values | 2008–present | Free download (CSV) | Use for volatility regime |
| NSE India — Sectoral Indices | NIFTY IT, Bank, FMCG etc. daily | 2010–present | Free download (CSV) | Use for sector regime features |
| RBI Website | 91-day T-bill yields (weekly auction) | Available for opportunity cost rate | Free download | rbi.org.in; use for blocked capital cost |

---

*Source matrix is based on secondary research. All URLs and access details must be verified
before production use. Licensing, terms of service, and commercial-use rights must be
reviewed for any source used in a commercial system.*
