"""
Live IPO source orchestration.

InvestorGain is the primary live source. Chittorgarh is an optional fallback for
provider outages and for fields absent from the primary response.

Missing values remain None and are never fabricated.
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


def _identity(ipo: LiveIPO) -> str:
    if ipo.nse_symbol:
        return ipo.nse_symbol.upper()
    return re.sub(r"\b(ltd|limited|ipo)\b|[^a-z0-9]", "", ipo.company_name.lower())


def merge_live_sources(
    primary: list[LiveIPO],
    fallback: list[LiveIPO],
) -> list[LiveIPO]:
    """Merge fallback values without allowing them to overwrite primary data."""
    merged = list(primary)
    by_identity = {_identity(ipo): ipo for ipo in merged}
    fallback_fields = (
        "company_name", "nse_symbol", "segment", "open_date", "close_date",
        "listing_date", "issue_price", "price_band_low", "price_band_high",
        "lot_size", "issue_size_cr", "fresh_issue_cr", "ofs_cr",
        "subscription_qib_x", "subscription_nii_x", "subscription_retail_x",
        "subscription_total_x", "gmp_inr", "gmp_pct", "gmp_source",
    )
    for candidate in fallback:
        key = _identity(candidate)
        existing = by_identity.get(key)
        if existing is None:
            merged.append(candidate)
            by_identity[key] = candidate
            continue

        used_fallback = False
        for field_name in fallback_fields:
            if getattr(existing, field_name) is None:
                value = getattr(candidate, field_name)
                if value is not None:
                    setattr(existing, field_name, value)
                    used_fallback = True
        if existing.status == "UNKNOWN" and candidate.status != "UNKNOWN":
            existing.status = candidate.status
            used_fallback = True
        if existing.source_url is None and candidate.source_url:
            existing.source_url = candidate.source_url
            used_fallback = True
        if used_fallback:
            existing.source = "INVESTORGAIN+CHITTORGARH"

    merged.sort(key=lambda x: x.listing_date or "0000-00-00", reverse=True)
    return merged


def _fetch_chittorgarh_fallback(years: list[int], now: str) -> list[LiveIPO]:
    from ipo_analyzer.collectors.chittorgarh import (
        scrape_chittorgarh,
        scrape_chittorgarh_current,
    )

    logger.info("Fetching optional Chittorgarh fallback data...")
    current_records, _ = scrape_chittorgarh_current()
    current_ipos = [_raw_to_live_ipo(r, now) for r in current_records]
    current_ipos = [i for i in current_ipos if i is not None]

    records, report = scrape_chittorgarh(years, delay_seconds=1.0)
    for err in report.errors:
        logger.error("Chittorgarh fallback error: %s", err)
    listed_ipos = [_raw_to_live_ipo(r, now) for r in records]
    listed_ipos = [i for i in listed_ipos if i is not None]
    current_keys = {_identity(i) for i in current_ipos}
    return current_ipos + [i for i in listed_ipos if _identity(i) not in current_keys]


def fetch_live_ipos(years: Optional[list] = None) -> list[LiveIPO]:
    """
    Fetch current-year IPO data from Chittorgarh performance tracker.
    Returns list of LiveIPO objects sorted by listing_date descending.
    Missing fields are None — never fabricated.
    """
    now = datetime.now(timezone.utc).isoformat()
    if years is None:
        years = [datetime.now().year]

    try:
        from ipo_analyzer.data_sources.investorgain import fetch_investorgain_ipos

        investor_ipos = fetch_investorgain_ipos()
    except Exception as exc:
        logger.warning("InvestorGain adapter failed: %s", exc)
        investor_ipos = []

    try:
        fallback_ipos = _fetch_chittorgarh_fallback(years, now)
    except Exception as exc:
        logger.warning("Chittorgarh fallback failed: %s", exc)
        fallback_ipos = []

    ipos = merge_live_sources(investor_ipos, fallback_ipos)

    logger.info("Live fetch complete: %d IPOs", len(ipos))
    return ipos
