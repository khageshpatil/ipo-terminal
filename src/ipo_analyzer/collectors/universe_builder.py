"""
Universe builder — merges scraped records, deduplicates, validates,
and writes the canonical ipo_universe_2018_2024.csv.

Output schema matches the domain IPO model expectations:
  ipo_id, company_name, nse_symbol, exchange, segment, open_date, close_date,
  listing_date, issue_price, price_band_low, price_band_high, lot_size,
  issue_size_cr, fresh_issue_cr, ofs_cr, retail_quota_pct, qib_quota_pct,
  nii_quota_pct, subscription_qib_x, subscription_nii_x, subscription_retail_x,
  subscription_total_x, listing_open_price, listing_open_quality, listing_return_pct,
  source, source_url, scraped_at
"""

from __future__ import annotations

import json
import logging
from dataclasses import asdict
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Optional

import pandas as pd

from .models import CollectionReport, RawIPORecord

logger = logging.getLogger(__name__)

_OUT_DIR = Path("data/universe")
_OUT_CSV = _OUT_DIR / "ipo_universe_2018_2024.csv"
_REPORT_JSON = _OUT_DIR / "collection_report.json"


def _normalize_name(name: str) -> str:
    """Canonical company name for deduplication."""
    import re
    name = name.lower().strip()
    # Remove common suffixes
    for suffix in [" limited", " ltd", " ltd.", " private", " pvt", " pvt.", " inc", " corp"]:
        name = name.replace(suffix, "")
    # Remove non-alphanumeric
    name = re.sub(r"[^a-z0-9 ]", " ", name)
    name = re.sub(r"\s+", " ", name).strip()
    return name


def _deduplicate(records: list[RawIPORecord]) -> list[RawIPORecord]:
    """
    Deduplicate records by company name (normalized).
    When duplicates exist, prefer:
    1. Record with Bhav Copy price
    2. Record with listing_date
    3. Record with more non-null fields
    4. Most recently scraped
    """
    groups: dict[str, list[RawIPORecord]] = {}
    for rec in records:
        key = _normalize_name(rec.company_name)
        groups.setdefault(key, []).append(rec)

    deduped: list[RawIPORecord] = []
    for key, group in groups.items():
        if len(group) == 1:
            deduped.append(group[0])
            continue

        # Score each record
        def score(r: RawIPORecord) -> int:
            s = 0
            if r.bhav_listing_open is not None:
                s += 100
            if r.listing_date is not None:
                s += 50
            if r.close_date is not None:
                s += 20
            if r.issue_price is not None:
                s += 10
            if r.subscription_total_x is not None:
                s += 10
            if r.nse_symbol is not None:
                s += 5
            return s

        best = max(group, key=score)

        # Merge missing fields from other sources into best
        for other in group:
            if other is best:
                continue
            # Fill in fields that best is missing
            if best.nse_symbol is None and other.nse_symbol:
                best.nse_symbol = other.nse_symbol
            if best.listing_date is None and other.listing_date:
                best.listing_date = other.listing_date
            if best.close_date is None and other.close_date:
                best.close_date = other.close_date
            if best.open_date is None and other.open_date:
                best.open_date = other.open_date
            if best.issue_price is None and other.issue_price:
                best.issue_price = other.issue_price
            if best.lot_size is None and other.lot_size:
                best.lot_size = other.lot_size
            if best.subscription_qib_x is None and other.subscription_qib_x:
                best.subscription_qib_x = other.subscription_qib_x
            if best.subscription_nii_x is None and other.subscription_nii_x:
                best.subscription_nii_x = other.subscription_nii_x
            if best.subscription_retail_x is None and other.subscription_retail_x:
                best.subscription_retail_x = other.subscription_retail_x
            if best.subscription_total_x is None and other.subscription_total_x:
                best.subscription_total_x = other.subscription_total_x

        deduped.append(best)

    return deduped


def _filter_mainboard_2018_2024(records: list[RawIPORecord]) -> list[RawIPORecord]:
    """
    Keep only records that are likely Mainboard IPOs in 2018–2024.
    Criteria:
    - listing_date or close_date in 2018–2024
    - Not already known to be SME (caught in scraper, but double-check issue size)
    """
    filtered = []
    for rec in records:
        ref_date = rec.listing_date or rec.close_date or rec.open_date
        if ref_date is None:
            # Include if we can't determine year — will be marked as needing review
            filtered.append(rec)
            continue
        if not (2018 <= ref_date.year <= 2024):
            continue
        # Rough SME filter: issue size < 10 Cr is almost certainly SME
        if rec.issue_size_cr is not None and rec.issue_size_cr < 10:
            continue
        filtered.append(rec)
    return filtered


def _compute_return(issue_price: Optional[float], listing_open: Optional[float]) -> Optional[float]:
    if issue_price and listing_open and issue_price > 0:
        return round((listing_open - issue_price) / issue_price * 100, 2)
    return None


def _assign_ids(records: list[RawIPORecord]) -> list[tuple[str, RawIPORecord]]:
    """Assign sequential ipo_ids, sorted by listing_date then company name."""
    sorted_recs = sorted(
        records,
        key=lambda r: (r.listing_date or date(2099, 1, 1), r.company_name),
    )
    return [(str(i + 1), rec) for i, rec in enumerate(sorted_recs)]


def build_universe_csv(
    records: list[RawIPORecord],
    output_path: Path = _OUT_CSV,
) -> pd.DataFrame:
    """
    Merge, deduplicate, validate, and write the universe CSV.
    Returns the resulting DataFrame.
    """
    logger.info("Universe builder: %d raw records in", len(records))

    # Deduplicate
    records = _deduplicate(records)
    logger.info("After dedup: %d records", len(records))

    # Filter to mainboard 2018-2024
    records = _filter_mainboard_2018_2024(records)
    logger.info("After year/segment filter: %d records", len(records))

    # Assign IDs
    id_recs = _assign_ids(records)

    rows = []
    for ipo_id, rec in id_recs:
        listing_open = rec.bhav_listing_open or rec.listing_open_approx
        quality = rec.canonical_quality()
        computed_return = _compute_return(rec.issue_price, listing_open)

        rows.append({
            "ipo_id": ipo_id,
            "company_name": rec.company_name,
            "nse_symbol": rec.nse_symbol or "",
            "exchange": "NSE",
            "segment": "MAINBOARD",
            "open_date": rec.open_date.isoformat() if rec.open_date else "",
            "close_date": rec.close_date.isoformat() if rec.close_date else "",
            "listing_date": rec.listing_date.isoformat() if rec.listing_date else "",
            "issue_price": rec.issue_price or "",
            "price_band_low": rec.price_band_low or "",
            "price_band_high": rec.price_band_high or "",
            "lot_size": rec.lot_size or "",
            "issue_size_cr": rec.issue_size_cr or "",
            "fresh_issue_cr": rec.fresh_issue_cr or "",
            "ofs_cr": rec.ofs_cr or "",
            "retail_quota_pct": rec.retail_quota_pct or "",
            "qib_quota_pct": rec.qib_quota_pct or "",
            "nii_quota_pct": rec.nii_quota_pct or "",
            "subscription_qib_x": rec.subscription_qib_x or "",
            "subscription_nii_x": rec.subscription_nii_x or "",
            "subscription_retail_x": rec.subscription_retail_x or "",
            "subscription_total_x": rec.subscription_total_x or "",
            "listing_open_price": listing_open or "",
            "listing_open_quality": quality,
            "listing_return_pct": (
                computed_return if computed_return is not None
                else rec.listing_return_pct or ""
            ),
            "source": rec.source,
            "source_url": rec.source_url or "",
            "scraped_at": rec.scraped_at or "",
        })

    df = pd.DataFrame(rows)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info("Universe CSV written: %s (%d rows)", output_path, len(df))
    return df


def generate_quality_report(df: pd.DataFrame) -> dict:
    """
    Generate a lightweight quality report (Phase 2.4 acceptance gate).
    Returns a dict suitable for JSON output.
    """
    total = len(df)
    with_listing_price = df["listing_open_price"].replace("", None).dropna().shape[0]
    primary_verified = (df["listing_open_quality"] == "PRIMARY_VERIFIED").sum()
    secondary_verified = (df["listing_open_quality"] == "SECONDARY_VERIFIED").sum()
    missing_price = (df["listing_open_quality"] == "MISSING").sum()
    with_subscription = df["subscription_total_x"].replace("", None).dropna().shape[0]
    missing_close_date = (df["close_date"] == "").sum()
    missing_listing_date = (df["listing_date"] == "").sum()
    missing_issue_price = (df["issue_price"] == "").sum()

    # Usable = has issue_price AND listing_open_price AND close_date
    usable_mask = (
        (df["issue_price"] != "") &
        (df["listing_open_price"] != "") &
        (df["close_date"] != "")
    )
    usable = usable_mask.sum()

    # Base rate on usable records
    positive = 0
    mean_return = None
    if usable > 0:
        usable_df = df[usable_mask].copy()
        usable_df["_ret"] = pd.to_numeric(usable_df["listing_return_pct"], errors="coerce")
        positive = (usable_df["_ret"] > 0).sum()
        mean_return = round(float(usable_df["_ret"].mean()), 2)

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_ipos_discovered": total,
        "usable_ipos": int(usable),
        "missing_listing_price": int(missing_price),
        "primary_verified_listing_price": int(primary_verified),
        "secondary_verified_listing_price": int(secondary_verified),
        "with_subscription_data": int(with_subscription),
        "missing_issue_price": int(missing_issue_price),
        "missing_close_date": int(missing_close_date),
        "missing_listing_date": int(missing_listing_date),
        "positive_listing_count": int(positive),
        "positive_listing_rate_pct": round(positive / usable * 100, 1) if usable > 0 else None,
        "mean_listing_return_pct": mean_return,
    }
    return report
