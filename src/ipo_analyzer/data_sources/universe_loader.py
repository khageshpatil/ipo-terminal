"""
Universe CSV loader — reads data/universe/ipo_universe_2018_2024.csv
and produces domain IPO objects + ListingOutcome objects compatible
with the existing pipeline (research_csv.py loader style).

This is the bridge between the raw collected data and the backtest engine.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Optional

import pandas as pd

from ipo_analyzer.domain.quality import DataQuality

logger = logging.getLogger(__name__)

DEFAULT_CSV = Path("data/universe/ipo_universe_2018_2024.csv")


@dataclass
class UniverseIPO:
    """
    Lightweight IPO record from the universe CSV.
    Not the full domain IPO — only the fields the backtest needs.
    """
    ipo_id: str
    company_name: str
    nse_symbol: str
    exchange: str
    segment: str

    open_date: Optional[date]
    close_date: Optional[date]
    listing_date: Optional[date]

    issue_price: Optional[Decimal]
    lot_size: Optional[int]
    issue_size_cr: Optional[float]
    fresh_issue_cr: Optional[float]
    ofs_cr: Optional[float]

    subscription_qib_x: Optional[float]
    subscription_nii_x: Optional[float]
    subscription_retail_x: Optional[float]
    subscription_total_x: Optional[float]

    listing_open_price: Optional[Decimal]
    listing_open_quality: str         # PRIMARY_VERIFIED | SECONDARY_VERIFIED | MISSING
    listing_return_pct: Optional[float]

    source: str

    @property
    def year(self) -> Optional[int]:
        d = self.listing_date or self.close_date
        return d.year if d else None

    @property
    def ofs_ratio(self) -> Optional[float]:
        if self.fresh_issue_cr is None or self.ofs_cr is None:
            return None
        total = self.fresh_issue_cr + self.ofs_cr
        return self.ofs_cr / total if total > 0 else None

    def quality_flag(self) -> DataQuality:
        if self.listing_open_quality == "PRIMARY_VERIFIED":
            return DataQuality.PRIMARY_VERIFIED
        if self.listing_open_quality == "SECONDARY_VERIFIED":
            return DataQuality.SECONDARY_VERIFIED
        return DataQuality.MISSING

    def is_usable(self) -> bool:
        """Minimum fields required for the baseline analysis."""
        return (
            self.issue_price is not None
            and self.listing_open_price is not None
            and self.listing_open_quality != "MISSING"
        )

    def listing_return(self) -> Optional[Decimal]:
        if self.issue_price and self.listing_open_price and self.issue_price > 0:
            return (self.listing_open_price - self.issue_price) / self.issue_price
        return None

    def positive_listing(self) -> Optional[bool]:
        ret = self.listing_return()
        return ret > 0 if ret is not None else None

    def as_feature_dict(self) -> dict:
        """Return fields usable as model features (issue structure + subscription)."""
        return {
            "issue_size_cr": self.issue_size_cr,
            "fresh_issue_cr": self.fresh_issue_cr,
            "ofs_cr": self.ofs_cr,
            "ofs_pct": self.ofs_ratio,
            "subscription_qib_x": self.subscription_qib_x,
            "subscription_nii_x": self.subscription_nii_x,
            "subscription_retail_x": self.subscription_retail_x,
            "subscription_total_x": self.subscription_total_x,
            "lot_size": self.lot_size,
        }


def _d(v) -> Optional[date]:
    if pd.isna(v) or str(v).strip() in ("", "nan"):
        return None
    try:
        return date.fromisoformat(str(v).strip())
    except (ValueError, AttributeError):
        return None


def _dec(v) -> Optional[Decimal]:
    if pd.isna(v) or str(v).strip() in ("", "nan"):
        return None
    try:
        return Decimal(str(v).strip())
    except (InvalidOperation, ValueError):
        return None


def _f(v) -> Optional[float]:
    if pd.isna(v) or str(v).strip() in ("", "nan"):
        return None
    try:
        return float(v)
    except (ValueError, TypeError):
        return None


def _i(v) -> Optional[int]:
    f = _f(v)
    return int(f) if f is not None else None


def load_universe(
    csv_path: Path = DEFAULT_CSV,
    min_quality: str = "SECONDARY_VERIFIED",
    years: Optional[list[int]] = None,
    segment: str = "MAINBOARD",
) -> list[UniverseIPO]:
    """
    Load the universe CSV and return UniverseIPO objects.

    Parameters
    ----------
    csv_path : Path
        Path to ipo_universe_2018_2024.csv
    min_quality : str
        Minimum listing price quality: 'PRIMARY_VERIFIED' or 'SECONDARY_VERIFIED'
    years : list[int], optional
        Filter to specific years (by listing_date year)
    segment : str
        Filter segment (MAINBOARD by default)
    """
    if not csv_path.exists():
        raise FileNotFoundError(
            f"Universe CSV not found: {csv_path}\n"
            "Run: python scripts/build_universe.py"
        )

    df = pd.read_csv(csv_path, dtype=str, keep_default_na=False)
    logger.info("Loaded %d rows from %s", len(df), csv_path)

    records: list[UniverseIPO] = []
    skipped = 0

    for _, row in df.iterrows():
        quality = str(row.get("listing_open_quality", "MISSING")).strip()

        # Quality filter
        if min_quality == "PRIMARY_VERIFIED" and quality != "PRIMARY_VERIFIED":
            skipped += 1
            continue

        # Segment filter
        seg = str(row.get("segment", "")).strip().upper()
        if segment and seg != segment.upper():
            skipped += 1
            continue

        ipo = UniverseIPO(
            ipo_id=str(row.get("ipo_id", "")).strip(),
            company_name=str(row.get("company_name", "")).strip(),
            nse_symbol=str(row.get("nse_symbol", "")).strip(),
            exchange=str(row.get("exchange", "NSE")).strip(),
            segment=seg or "MAINBOARD",
            open_date=_d(row.get("open_date")),
            close_date=_d(row.get("close_date")),
            listing_date=_d(row.get("listing_date")),
            issue_price=_dec(row.get("issue_price")),
            lot_size=_i(row.get("lot_size")),
            issue_size_cr=_f(row.get("issue_size_cr")),
            fresh_issue_cr=_f(row.get("fresh_issue_cr")),
            ofs_cr=_f(row.get("ofs_cr")),
            subscription_qib_x=_f(row.get("subscription_qib_x")),
            subscription_nii_x=_f(row.get("subscription_nii_x")),
            subscription_retail_x=_f(row.get("subscription_retail_x")),
            subscription_total_x=_f(row.get("subscription_total_x")),
            listing_open_price=_dec(row.get("listing_open_price")),
            listing_open_quality=quality,
            listing_return_pct=_f(row.get("listing_return_pct")),
            source=str(row.get("source", "")).strip(),
        )

        # Year filter
        if years and ipo.year not in years:
            skipped += 1
            continue

        records.append(ipo)

    usable = sum(1 for r in records if r.is_usable())
    logger.info(
        "Universe: %d records loaded, %d usable, %d skipped (quality/segment/year filter)",
        len(records), usable, skipped,
    )
    return records


def compute_base_rate(ipos: list[UniverseIPO]) -> dict:
    """
    Compute the Apply-Every-IPO base rate from the universe.
    Only counts usable records.
    """
    import statistics

    usable = [r for r in ipos if r.is_usable()]
    if not usable:
        return {"error": "No usable records"}

    returns = [float(r.listing_return()) * 100 for r in usable if r.listing_return() is not None]
    positive = sum(1 for r in usable if r.positive_listing())

    result = {
        "total_ipos": len(ipos),
        "usable_ipos": len(usable),
        "positive_listings": positive,
        "negative_listings": len(usable) - positive,
        "positive_rate_pct": round(positive / len(usable) * 100, 1),
        "mean_return_pct": round(statistics.mean(returns), 2) if returns else None,
        "median_return_pct": round(statistics.median(returns), 2) if returns else None,
        "max_gain_pct": round(max(returns), 2) if returns else None,
        "max_loss_pct": round(min(returns), 2) if returns else None,
        "std_return_pct": round(statistics.stdev(returns), 2) if len(returns) > 1 else None,
    }

    # By year
    from collections import defaultdict
    by_year: dict = defaultdict(list)
    for r in usable:
        if r.year and r.listing_return() is not None:
            by_year[r.year].append(float(r.listing_return()) * 100)

    result["by_year"] = {}
    for y in sorted(by_year):
        yr_rets = by_year[y]
        yr_pos = sum(1 for v in yr_rets if v > 0)
        result["by_year"][y] = {
            "n": len(yr_rets),
            "positive": yr_pos,
            "positive_rate_pct": round(yr_pos / len(yr_rets) * 100, 1),
            "mean_return_pct": round(statistics.mean(yr_rets), 2),
        }

    return result
