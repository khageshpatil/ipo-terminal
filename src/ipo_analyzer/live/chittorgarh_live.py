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
from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo
from typing import Optional

from ipo_analyzer.live.models import LiveIPO

logger = logging.getLogger(__name__)

_PERF_URL = "https://www.chittorgarh.com/ipo/ipo_perf_tracker.asp?year={year}"


_IST = ZoneInfo("Asia/Kolkata")


def determine_status(
    open_date: Optional[date],
    close_date: Optional[date],
    listing_date: Optional[date],
    now: Optional[datetime] = None,
) -> str:
    """Classify an IPO using actual calendar dates in the India timezone."""
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        raise ValueError("now must be timezone-aware")
    today = now.astimezone(_IST).date()

    if listing_date and today >= listing_date:
        return "LISTED"
    if open_date and today < open_date:
        return "UPCOMING"
    if open_date and close_date and open_date <= today <= close_date:
        return "OPEN"
    if close_date and today > close_date and (not listing_date or today < listing_date):
        return "CLOSED"
    return "UNKNOWN"


def _raw_to_live_ipo(raw, now: str) -> Optional[LiveIPO]:
    """Convert a RawIPORecord to a LiveIPO."""
    listing_date = raw.listing_date.isoformat() if raw.listing_date else None
    status = determine_status(raw.open_date, raw.close_date, raw.listing_date)
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
        open_date=raw.open_date.isoformat() if raw.open_date else None,
        close_date=raw.close_date.isoformat() if raw.close_date else None,
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
    from ipo_analyzer.collectors.chittorgarh import (
        scrape_chittorgarh,
        scrape_chittorgarh_current,
    )

    now = datetime.now(timezone.utc).isoformat()
    if years is None:
        years = [datetime.now().year]

    logger.info("Fetching current IPOs via Chittorgarh dashboard...")
    current_records, current_report = scrape_chittorgarh_current()
    current_ipos = [_raw_to_live_ipo(r, now) for r in current_records]
    current_ipos = [i for i in current_ipos if i is not None]

    logger.info("Fetching listed IPOs via Chittorgarh perf-tracker (years=%s)...", years)
    records, report = scrape_chittorgarh(years, delay_seconds=1.0)

    for err in report.errors:
        logger.error("Chittorgarh error: %s", err)

    ipos = [_raw_to_live_ipo(r, now) for r in records]
    ipos = [i for i in ipos if i is not None]
    current_keys = {i.nse_symbol or i.company_name.lower() for i in current_ipos}
    ipos = current_ipos + [
        i for i in ipos if (i.nse_symbol or i.company_name.lower()) not in current_keys
    ]

    # Optional enrichment/discovery source. A provider outage must not remove
    # records already discovered from Chittorgarh.
    try:
        from ipo_analyzer.data_sources.investorgain import fetch_investorgain_ipos

        investor_ipos = fetch_investorgain_ipos()
    except Exception as exc:
        logger.warning("InvestorGain adapter failed: %s", exc)
        investor_ipos = []

    def identity(ipo: LiveIPO) -> str:
        if ipo.nse_symbol:
            return ipo.nse_symbol.upper()
        return re.sub(r"\b(ltd|limited|ipo)\b|[^a-z0-9]", "", ipo.company_name.lower())

    by_identity = {identity(ipo): ipo for ipo in ipos}
    for investor_ipo in investor_ipos:
        existing = by_identity.get(identity(investor_ipo))
        if existing is None:
            ipos.append(investor_ipo)
            by_identity[identity(investor_ipo)] = investor_ipo
            continue
        # InvestorGain is preferred for live status/subscription/GMP where it
        # has a value; Chittorgarh remains the fallback for missing fields.
        for field_name in (
            "open_date", "close_date", "listing_date", "status",
            "subscription_qib_x", "subscription_nii_x",
            "subscription_retail_x", "subscription_total_x",
            "gmp_inr", "gmp_pct",
        ):
            value = getattr(investor_ipo, field_name)
            if value is not None and (field_name != "status" or value != "UNKNOWN"):
                setattr(existing, field_name, value)
        if investor_ipo.source_url:
            existing.source_url = investor_ipo.source_url
        existing.source = "INVESTORGAIN+CHITTORGARH"
    ipos.sort(key=lambda x: x.listing_date or "0000-00-00", reverse=True)

    logger.info("Live fetch complete: %d IPOs", len(ipos))
    return ipos
