"""
Live IPO adapter for Chittorgarh.

Uses the proven Chittorgarh performance tracker URL (same as historical scraper)
but fetches the CURRENT year to get all 2026 IPOs including those listed this week.

URL: https://www.chittorgarh.com/ipo/ipo_perf_tracker.asp?year=2026

Data quality:
- Subscription data is FINAL (post-close) from Chittorgarh aggregator
- open_date / close_date are inferred from listing_date using T+3 regime
"""

from __future__ import annotations

import logging
import re
from datetime import datetime, timedelta, timezone
from typing import Optional

from ipo_analyzer.live.models import LiveIPO

logger = logging.getLogger(__name__)

_PERF_URL = "https://www.chittorgarh.com/ipo/ipo_perf_tracker.asp?year={year}"


def _determine_status(listing_date_str: Optional[str]) -> str:
    """Infer status from listing_date."""
    if not listing_date_str:
        return "UNKNOWN"
    today = datetime.now(timezone.utc).date()
    try:
        listing = datetime.strptime(listing_date_str, "%Y-%m-%d").date()
    except ValueError:
        return "UNKNOWN"

    # Approximate close date: T+3 regime → close ≈ listing - 4 calendar days
    approx_close = listing - timedelta(days=4)

    if listing > today:
        if approx_close >= today:
            return "OPEN"
        return "UPCOMING"
    # Already listed (including today) → CLOSED for UI purposes
    return "CLOSED"


def _raw_to_live_ipo(raw, now: str) -> Optional[LiveIPO]:
    """Convert a RawIPORecord to a LiveIPO."""
    listing_date = raw.listing_date.isoformat() if raw.listing_date else None
    status = _determine_status(listing_date)
    year = raw.listing_date.year if raw.listing_date else datetime.now().year

    if raw.nse_symbol:
        ipo_id = f"{raw.nse_symbol.upper()}-{year}"
    else:
        slug = re.sub(r"[^A-Z0-9]", "_", raw.company_name.upper())[:20].rstrip("_")
        ipo_id = f"{slug}-{year}"

    return LiveIPO(
        ipo_id=ipo_id,
        company_name=raw.company_name,
        nse_symbol=raw.nse_symbol,
        segment="MAINBOARD",
        listing_date=listing_date,
        issue_price=raw.issue_price,
        price_band_low=raw.price_band_low,
        price_band_high=raw.price_band_high,
        lot_size=raw.lot_size,
        issue_size_cr=raw.issue_size_cr,
        subscription_qib_x=raw.subscription_qib_x,
        subscription_nii_x=raw.subscription_nii_x,
        subscription_retail_x=raw.subscription_retail_x,
        subscription_total_x=raw.subscription_total_x,
        subscription_is_final=True,
        status=status,
        source="CHITTORGARH_LIVE",
        source_url=_PERF_URL.format(year=year),
        observed_at=now,
        retrieved_at=now,
    )


def fetch_live_ipos(years: Optional[list] = None) -> list[LiveIPO]:
    """
    Fetch current-year IPO data from Chittorgarh performance tracker.
    Returns list of LiveIPO objects sorted by listing_date descending.
    Missing fields are None — never fabricated.
    """
    from ipo_analyzer.collectors.chittorgarh import scrape_chittorgarh

    now = datetime.now(timezone.utc).isoformat()
    if years is None:
        years = [datetime.now().year]

    logger.info("Fetching live IPOs via Chittorgarh perf-tracker (years=%s)...", years)
    records, report = scrape_chittorgarh(years, delay_seconds=1.0)

    for err in report.errors:
        logger.error("Chittorgarh error: %s", err)

    ipos = [_raw_to_live_ipo(r, now) for r in records]
    ipos = [i for i in ipos if i is not None]
    ipos.sort(key=lambda x: x.listing_date or "0000-00-00", reverse=True)

    logger.info("Live fetch complete: %d IPOs", len(ipos))
    return ipos
