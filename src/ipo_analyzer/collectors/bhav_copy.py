"""
NSE Bhav Copy downloader — PRIMARY_VERIFIED listing prices.

For each IPO (symbol, listing_date), downloads the daily Bhav Copy ZIP for that date
and extracts the OPEN price from the EQ series row.

URL pattern:
  https://nsearchives.nseindia.com/content/historical/EQUITIES/{YYYY}/{MMM}/cm{DD}{MMM}{YYYY}bhav.csv.zip
  e.g. https://nsearchives.nseindia.com/content/historical/EQUITIES/2021/JUL/cm14JUL2021bhav.csv.zip

Bhav Copy columns:
  SYMBOL, SERIES, OPEN, HIGH, LOW, CLOSE, LAST, PREVCLOSE, TOTTRDQTY, TOTTRDVAL, TIMESTAMP, TOTALTRADES
"""

from __future__ import annotations

import io
import logging
import time
import zipfile
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

import pandas as pd

from .models import RawIPORecord

logger = logging.getLogger(__name__)

_ARCHIVE_URL = (
    "https://nsearchives.nseindia.com/content/historical/EQUITIES"
    "/{year}/{mon}/cm{dd}{mon}{year}bhav.csv.zip"
)

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "*/*",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.nseindia.com/",
}

_CACHE_DIR = Path("data/bhav_cache")


def _get_session():
    try:
        from curl_cffi import requests as cffi_requests
        session = cffi_requests.Session(impersonate="chrome124")
        return session, "curl_cffi"
    except Exception:
        import requests
        s = requests.Session()
        s.headers.update(_HEADERS)
        return s, "requests"


def _bhav_url(d: date) -> str:
    mon = d.strftime("%b").upper()   # JAN, FEB, ...
    dd = d.strftime("%d")
    year = d.strftime("%Y")
    return _ARCHIVE_URL.format(year=year, mon=mon, dd=dd)


def _fetch_bhav_df(session, d: date, use_cache: bool = True) -> Optional[pd.DataFrame]:
    """
    Fetch and parse the Bhav Copy for a given date.
    Returns a DataFrame with all rows, or None if not available
    (weekends, holidays, or archive unavailable).
    """
    url = _bhav_url(d)

    # Cache check
    cache_path = _CACHE_DIR / f"bhav_{d.isoformat()}.parquet"
    if use_cache and cache_path.exists():
        try:
            return pd.read_parquet(cache_path)
        except Exception:
            pass

    try:
        resp = session.get(url, timeout=30)
        if resp.status_code != 200:
            return None  # likely holiday/weekend
        content = resp.content
    except Exception as e:
        logger.debug("Bhav fetch error %s: %s", d, e)
        return None

    # Unzip in memory
    try:
        with zipfile.ZipFile(io.BytesIO(content)) as zf:
            csv_name = zf.namelist()[0]
            with zf.open(csv_name) as f:
                df = pd.read_csv(f)
    except Exception as e:
        logger.error("Bhav parse error for %s: %s", d, e)
        return None

    # Normalize columns
    df.columns = [c.strip().upper() for c in df.columns]
    for col in ["SYMBOL", "SERIES", "OPEN", "HIGH", "LOW", "CLOSE", "PREVCLOSE"]:
        if col not in df.columns:
            df[col] = None

    # Cache
    if use_cache:
        _CACHE_DIR.mkdir(parents=True, exist_ok=True)
        try:
            df.to_parquet(cache_path, index=False)
        except Exception:
            pass

    return df


def _find_listing_open(
    df: pd.DataFrame,
    symbol: str,
    fallback_series: tuple[str, ...] = ("EQ", "BE", "N"),
) -> Optional[float]:
    """
    Find the OPEN price for a symbol in a Bhav Copy DataFrame.
    Tries EQ series first, then BE (trade-for-trade, common on listing day), then N.
    """
    sym_upper = symbol.strip().upper()

    for series in fallback_series:
        mask = (df["SYMBOL"].str.strip().str.upper() == sym_upper) & (
            df["SERIES"].str.strip().str.upper() == series
        )
        rows = df[mask]
        if not rows.empty:
            open_price = rows.iloc[0]["OPEN"]
            try:
                val = float(open_price)
                if val > 0:
                    return val
            except (ValueError, TypeError):
                pass

    return None


def _try_date_range(session, symbol: str, listing_date: date, days_ahead: int = 3) -> tuple[Optional[float], Optional[date]]:
    """
    Try listing_date ± a few days to handle approximate listing dates.
    Returns (price, actual_date) or (None, None).
    """
    for delta in range(days_ahead + 1):
        for direction in ([0] if delta == 0 else [delta, -delta]):
            d = listing_date + timedelta(days=direction)
            if d.weekday() >= 5:  # skip weekends
                continue
            df = _fetch_bhav_df(session, d)
            if df is None:
                continue
            price = _find_listing_open(df, symbol)
            if price is not None:
                return price, d
    return None, None


def fetch_listing_prices(
    records: list[RawIPORecord],
    delay_seconds: float = 1.0,
    use_cache: bool = True,
) -> list[RawIPORecord]:
    """
    For each RawIPORecord with a nse_symbol and listing_date, fetch the
    PRIMARY_VERIFIED listing price from NSE Bhav Copy.

    Mutates records in-place (adds bhav_listing_open, bhav_listing_date_confirmed,
    bhav_source_url).

    Returns the same list (for chaining).
    """
    session, session_type = _get_session()
    logger.info("Bhav Copy fetcher using %s", session_type)
    _CACHE_DIR.mkdir(parents=True, exist_ok=True)

    needs_bhav = [r for r in records if r.nse_symbol and r.listing_date]
    no_symbol = [r for r in records if not r.nse_symbol]
    no_date = [r for r in records if r.nse_symbol and not r.listing_date]

    logger.info(
        "Bhav lookup: %d need price, %d no symbol, %d no date",
        len(needs_bhav), len(no_symbol), len(no_date),
    )

    ok = 0
    failed = 0

    for rec in needs_bhav:
        symbol = rec.nse_symbol
        listing_date = rec.listing_date

        price, actual_date = _try_date_range(session, symbol, listing_date)

        if price is not None:
            rec.bhav_listing_open = price
            rec.bhav_listing_date_confirmed = actual_date
            rec.bhav_source_url = _bhav_url(actual_date)
            ok += 1
            if actual_date != listing_date:
                logger.info(
                    "%s: price %.2f found on %s (expected %s)",
                    symbol, price, actual_date, listing_date,
                )
        else:
            logger.warning("%s: no Bhav Copy price found near %s", symbol, listing_date)
            failed += 1

        time.sleep(delay_seconds)

    logger.info("Bhav Copy: %d succeeded, %d failed (no symbol/date: %d+%d)", ok, failed, len(no_symbol), len(no_date))
    return records


def get_listing_price_for_symbol(
    symbol: str,
    listing_date: date,
    use_cache: bool = True,
    delay_seconds: float = 0.5,
) -> Optional[float]:
    """
    Convenience function: get the listing OPEN price for a single symbol.
    Returns None if not found.
    """
    session, _ = _get_session()
    price, _ = _try_date_range(session, symbol, listing_date)
    return price
