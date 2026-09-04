"""
Shared data models for the collectors layer.

These are lightweight dataclasses used during collection/scraping only.
Once merged and validated, data is converted to domain IPO/ListingOutcome objects.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Optional


@dataclass
class RawIPORecord:
    """
    A single IPO record as collected from a data source.
    All fields are optional except company_name; validation happens later.
    """
    # Identity
    company_name: str
    nse_symbol: Optional[str] = None
    bse_code: Optional[str] = None

    # Timeline
    open_date: Optional[date] = None
    close_date: Optional[date] = None
    listing_date: Optional[date] = None

    # Issue terms
    issue_price: Optional[float] = None           # Upper band if book-built
    price_band_low: Optional[float] = None
    price_band_high: Optional[float] = None
    lot_size: Optional[int] = None
    issue_size_cr: Optional[float] = None         # Total issue size (₹ Crore)
    fresh_issue_cr: Optional[float] = None
    ofs_cr: Optional[float] = None

    # Quotas (%)
    retail_quota_pct: Optional[float] = None
    qib_quota_pct: Optional[float] = None
    nii_quota_pct: Optional[float] = None

    # Listing outcome (secondary-verified from aggregator)
    listing_open_approx: Optional[float] = None  # Secondary-verified open price
    listing_return_pct: Optional[float] = None   # As reported by source

    # Subscription (final, after close)
    subscription_qib_x: Optional[float] = None
    subscription_nii_x: Optional[float] = None
    subscription_retail_x: Optional[float] = None
    subscription_total_x: Optional[float] = None

    # Provenance
    source: str = "UNKNOWN"
    source_url: Optional[str] = None
    scraped_at: Optional[str] = None  # ISO timestamp string

    # PRIMARY_VERIFIED listing price (from Bhav Copy, filled later)
    bhav_listing_open: Optional[float] = None
    bhav_listing_date_confirmed: Optional[date] = None
    bhav_source_url: Optional[str] = None

    def has_listing_outcome(self) -> bool:
        return self.bhav_listing_open is not None or self.listing_open_approx is not None

    def canonical_listing_price(self) -> Optional[float]:
        """Return PRIMARY_VERIFIED price if available, else secondary."""
        return self.bhav_listing_open or self.listing_open_approx

    def canonical_quality(self) -> str:
        if self.bhav_listing_open is not None:
            return "PRIMARY_VERIFIED"
        if self.listing_open_approx is not None:
            return "SECONDARY_VERIFIED"
        return "MISSING"


@dataclass
class CollectionReport:
    """Summary of a scraping run."""
    source: str
    years_requested: list[int] = field(default_factory=list)
    records_collected: int = 0
    records_failed: int = 0
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def add_error(self, msg: str) -> None:
        self.errors.append(msg)

    def add_warning(self, msg: str) -> None:
        self.warnings.append(msg)
