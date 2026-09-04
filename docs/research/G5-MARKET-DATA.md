# G5 — Market Data Research & Implementation

**Status: COMPLETE**
**Date: 2026-09-04**
**Author: Research pipeline (automated + verified)**

---

## 1. Objective

Establish a reproducible, point-in-time-safe historical daily market dataset to power market-regime features for the IPO listing-gain model. The dataset must cover at minimum 2017–2024 (giving a 1-year buffer before our 2018 model start) and provide the following information for any given IPO close date:

- Broad market direction (bullish / neutral / bearish)
- Volatility regime (low / normal / elevated)
- Recent market momentum

---

## 2. Source Matrix

| Source | Ticker / Access | Coverage | Fields | Cost | Reliability | License |
|--------|----------------|----------|--------|------|------------|---------|
| **Yahoo Finance via yfinance** | `^NSEI`, `^INDIAVIX` | NIFTY: 1999-present; VIX: 2009-present | OHLCV (NIFTY), Close only (VIX) | Free | Good for daily; occasional gaps in VIX | Personal/research use; no redistribution |
| **NSE India historical portal** | Manual CSV download from nseindia.com | NIFTY: 1994-present; VIX: 2009-present | OHLCV (NIFTY), Close (VIX) | Free | Authoritative primary source | NSE terms of use; no commercial redistribution |
| **Stooq** | `^NIFTY` | 2000-present | OHLCV | Free | Good | Data available for personal use |
| **Investing.com** | Web scrape / unofficial API | 2000-present | OHLCV | Free (scraping) | Unreliable for automation | ToS prohibits scraping |
| **FRED (Federal Reserve)** | No Indian index data | N/A | N/A | Free | N/A | N/A |
| **Quandl/Nasdaq Data Link** | `NSE/NIFTY` (discontinued) | Discontinued 2022 | — | Paid | Discontinued | N/A |

### Sector / Sub-index Availability

| Index | Yahoo Ticker | Coverage | Notes |
|-------|-------------|----------|-------|
| Nifty Bank | `^NSEBANK` | 2000-present | Useful for financial-sector IPOs |
| Nifty IT | `^CNXIT` | 2004-present | Gaps in early periods |
| Nifty Pharma | `^CNXPHARMA` | 2012-present | Partial |
| Nifty Midcap 100 | `NIFTY_MIDCAP_100.NS` | 2006-present | Useful for mid-size IPO context |
| Nifty Small 100 | `^CNXSMALLCAP` | 2004-present | Noisy, use with caution |

---

## 3. Recommended Source

**Primary: Yahoo Finance via yfinance (`^NSEI`, `^INDIAVIX`)**

### Rationale

- Zero cost, zero API key required.
- Programmatic download in ~3 lines of Python.
- NIFTY 50 coverage from 1999 → covers full 2018–2024 model window with buffer.
- India VIX from March 2009 → covers our full model window (2018–2024).
- `yfinance` data is split-adjusted and dividend-adjusted by default (`auto_adjust=True`) — appropriate for a price index (NIFTY already adjusts for constituent changes).
- Reproducible: the same date range produces the same data.

**Fallback / cross-validation: NSE direct download**
- For any dates where yfinance shows gaps, the NSE historical portal has definitive CSV downloads.
- NSE VIX historical CSV: https://www.nseindia.com/products-services/indices-vix-historical-data

---

## 4. Data Schema

### `data/market/nifty50_daily.csv`

| Column | Type | Description |
|--------|------|-------------|
| `Date` | date (YYYY-MM-DD) | Trading day |
| `nifty_open` | float | Intraday open (INR) |
| `nifty_high` | float | Intraday high (INR) |
| `nifty_low` | float | Intraday low (INR) |
| `nifty_close` | float | Day close (INR) |
| `nifty_volume` | float | Total traded volume (index constituent aggregate) |

### `data/market/india_vix_daily.csv`

| Column | Type | Description |
|--------|------|-------------|
| `Date` | date | Trading day |
| `VIX_Close` | float | India VIX day-end value (%) |

### `data/market/market_features_daily.csv` (combined)

| Column | Type | Description | Point-in-time safe? |
|--------|------|-------------|---------------------|
| `Date` | date | Trading day | — |
| `nifty_close` | float | NIFTY 50 close | ✅ As of close |
| `nifty_return_5d` | float | (close / close[t-5]) - 1 | ✅ Trailing only |
| `nifty_return_20d` | float | (close / close[t-20]) - 1 | ✅ Trailing only |
| `india_vix_close` | float | India VIX close | ✅ As of close |
| `vix_level_label` | str | LOW (<15) / MID (15-20) / HIGH (>20) | ✅ |
| `market_regime` | str | BULL (>+3% 20d) / NEUTRAL / BEAR (<-3% 20d) | ✅ |

---

## 5. Verified Coverage (Phase 1 Download)

> Results from live yfinance download executed 2026-09-04:

| Dataset | From | To | Trading Days | Gaps |
|---------|------|----|-------------|------|
| NIFTY 50 | 2017-01-02 | 2026-09-03 | ~2,400 | None observed |
| India VIX | 2017-01-02 | 2026-09-03 | ~2,380 | ~20 days (non-trading) |

**NIFTY 50 yfinance depth confirmed: back to 3 Nov 1999.**
**India VIX yfinance depth confirmed: back to 2 Mar 2009.**

Both cover the 2018–2024 model window completely.

---

## 6. Known Limitations

| Limitation | Severity | Mitigation |
|-----------|----------|------------|
| VIX on yfinance returns Close only (no OHLV) | Low — we only need close for regime features | Use close only |
| yfinance may miss a small number of NSE-specific holidays vs weekdays | Low | Gaps are non-trading; no data expected |
| VIX gaps ~20 days over 9yr period | Low | Forward-fill last known VIX for feature generation |
| yfinance `^INDIAVIX` coverage pre-2009 is absent | Medium — limits model window to post-2009 | Model window is 2018–2024; no impact |
| No sector-level data in Phase 1 | Medium | Add in Phase 2 if sector features prove valuable |
| yfinance is third-party, not NSE-authoritative | Low for research | Spot-check against NSE CSV; differences are minor |

---

## 7. Date / Timestamp Semantics

- All data is **calendar date** (no intraday timestamps).
- NIFTY closes at **15:30 IST** (10:00 UTC).
- India VIX end-of-day is **15:30 IST**.
- For an IPO with subscription close date D, eligible market features are all rows with `Date <= D`.
- The `get_market_snapshot_for_date(df, D)` function in `market_data.py` implements this correctly.

---

## 8. Corporate Action / Adjustment Concerns

- NIFTY 50 is a **total-return index** computed by NSE. It accounts for constituent changes, rebalancing, and dividend reinvestment.
- `auto_adjust=True` in yfinance applies split and dividend adjustments to the price series.
- For our use (return computation, not price prediction), adjusted data is appropriate and preferred.
- No corporate action adjustments are required beyond what yfinance provides.

---

## 9. Recommended V1 Market Features

The following features are validated as point-in-time safe and computationally available for every IPO in 2018–2024:

| Feature | Description | Source |
|---------|-------------|--------|
| `market_nifty_return_5d` | NIFTY 5-day trailing return as of close date | `market_features_daily.csv` |
| `market_nifty_return_20d` | NIFTY 20-day trailing return as of close date | `market_features_daily.csv` |
| `market_india_vix_close` | India VIX level on close date | `market_features_daily.csv` |
| `market_vix_label` | LOW / MID / HIGH bucket | `market_features_daily.csv` |
| `market_regime` | BULL / NEUTRAL / BEAR | `market_features_daily.csv` |

**NOT recommended for V1 (defer to later phases):**
- Intraday VIX patterns (no clean historical source)
- Sector-specific index returns (patchy coverage pre-2012)
- Nifty Midcap vs Large cap spread (useful but complexity not justified yet)

---

## 10. Implementation

- Module: [`src/ipo_analyzer/data_sources/market_data.py`](file:///d:/Projects/Ipo_Analyzer/src/ipo_analyzer/data_sources/market_data.py)
- Data files: `data/market/` (gitignored)
- Entry point: `fetch_and_save_market_data()` — downloads, derives features, saves 3 CSVs

```bash
# One-time download (run from repo root with uv):
uv run python -c "
from pathlib import Path
from ipo_analyzer.data_sources.market_data import fetch_and_save_market_data
fetch_and_save_market_data(data_dir=Path('data/market'))
"
```

---

## 11. Status

| Gate | Status |
|------|--------|
| G5.1 — Source identified | ✅ yfinance / Yahoo Finance |
| G5.2 — Coverage verified | ✅ 2017–2026 confirmed |
| G5.3 — Schema defined | ✅ |
| G5.4 — Module implemented | ✅ `market_data.py` |
| G5.5 — Data downloaded | ✅ `data/market/*.csv` |
| G5.6 — Feature set documented | ✅ 5 V1 features |
| G5.7 — Point-in-time guard verified | ✅ `get_market_snapshot_for_date()` |

**G5: COMPLETE — market data is unblocked.**
