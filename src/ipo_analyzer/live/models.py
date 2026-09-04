"""
Live IPO data models.

Separate from the historical domain IPO model — these represent
currently-active or upcoming IPOs scraped from live sources.

Key design decisions:
- All monetary values are Optional[float] (not Decimal) for scraping simplicity
- observed_at is always stored — every field is a timestamped observation
- DataQuality is propagated from source
- GMP is explicitly marked as unofficial
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class LiveIPO:
    """
    A currently active or upcoming IPO scraped from a live source.
    This is NOT the same as the historical domain IPO — it is the
    raw live view, updated on each refresh.
    """
    # Identity
    ipo_id: str                          # slug: e.g. "AADHAAR-2025"
    company_name: str
    nse_symbol: Optional[str] = None
    segment: str = "MAINBOARD"           # MAINBOARD or SME

    # Timeline
    open_date: Optional[str] = None      # YYYY-MM-DD
    close_date: Optional[str] = None     # YYYY-MM-DD
    listing_date: Optional[str] = None   # YYYY-MM-DD (estimated)

    # Issue terms
    issue_price: Optional[float] = None  # Upper band / final price
    price_band_low: Optional[float] = None
    price_band_high: Optional[float] = None
    lot_size: Optional[int] = None
    issue_size_cr: Optional[float] = None
    fresh_issue_cr: Optional[float] = None
    ofs_cr: Optional[float] = None

    # Subscription (latest available — may be intraday or final)
    subscription_qib_x: Optional[float] = None
    subscription_nii_x: Optional[float] = None
    subscription_retail_x: Optional[float] = None
    subscription_total_x: Optional[float] = None
    subscription_is_final: bool = False  # True after close date

    # GMP — unofficial, stored separately, never used in backtest
    gmp_inr: Optional[float] = None
    gmp_pct: Optional[float] = None
    gmp_source: Optional[str] = None

    # Status
    status: str = "UNKNOWN"             # OPEN, UPCOMING, CLOSED, LISTED

    # Provenance
    source: str = "UNKNOWN"
    source_url: Optional[str] = None
    observed_at: Optional[str] = None   # ISO UTC — when values were true
    retrieved_at: Optional[str] = None  # ISO UTC — when we fetched


@dataclass
class LiveObservation:
    """
    A single timestamped observation of a changing field for a live IPO.
    Stored append-only — never overwrites previous observations.

    This is the raw building block for the prospective time-series dataset.
    """
    ipo_id: str
    field_name: str          # e.g. "subscription_total_x", "gmp_inr"
    value: Optional[float]   # None = explicitly missing (not fabricated)
    observed_at: str         # ISO UTC string
    retrieved_at: str        # ISO UTC string
    source: str
    source_url: Optional[str] = None
    is_final: bool = False   # True when subscription window is closed
