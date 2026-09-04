"""
Outcome entities — what actually happened after the IPO listed.

ListingOutcome is the canonical label for the listing-gain strategy.
AllotmentOutcome records what a specific investor actually received.

Both are derived/observed after listing day and must never be allowed
to leak into pre-listing feature snapshots.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, field_validator, model_validator

from ipo_analyzer.domain.quality import DataQuality


class ListingOutcome(BaseModel):
    """
    The canonical listing-day result for one IPO.

    listing_price is the NSE/BSE Bhav Copy OPEN field on listing_date —
    the pre-open session equilibrium price. This is the only acceptable
    primary source for the label. Aggregator prices are cross-checks only.

    All derived boolean fields are computed from listing_price and
    issue_price. They are stored explicitly for query efficiency.
    """

    ipo_id: str
    listing_date: date

    issue_price: Decimal
    """The per-share IPO issue price (from IssueTerms). Must match IPO.issue_terms.issue_price."""

    listing_price: Decimal
    """
    Pre-open equilibrium price on listing day (Bhav Copy OPEN).
    For SECONDARY_VERIFIED records this is approximate (sourced from news/aggregators).
    """

    listing_price_quality: DataQuality
    """
    Quality of the listing_price value.
    Phase 1 records are SECONDARY_VERIFIED (approximate, sourced from news summaries).
    Must be upgraded to PRIMARY_VERIFIED via Bhav Copy before use in model training.
    """

    source: str
    source_reference: Optional[str] = None
    observed_at: datetime
    retrieved_at: datetime

    # --- Derived fields (computed by factory method) ---
    listing_return: Decimal
    """(listing_price - issue_price) / issue_price. Signed; negative = loss."""

    positive_listing: bool
    """listing_price > issue_price."""

    return_gt_5: bool
    return_gt_10: bool
    return_gt_15: bool
    return_gt_20: bool
    return_lt_0: bool
    return_lt_neg5: bool
    return_lt_neg10: bool
    return_lt_neg20: bool

    @field_validator("observed_at", "retrieved_at")
    @classmethod
    def must_be_utc(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("ListingOutcome datetimes must be UTC-aware")
        return v

    @field_validator("issue_price", "listing_price")
    @classmethod
    def must_be_positive(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError(f"Price must be positive, got {v}")
        return v

    @classmethod
    def compute(
        cls,
        *,
        ipo_id: str,
        listing_date: date,
        issue_price: Decimal,
        listing_price: Decimal,
        listing_price_quality: DataQuality,
        source: str,
        source_reference: Optional[str],
        observed_at: datetime,
        retrieved_at: datetime,
    ) -> "ListingOutcome":
        """
        Factory method — the only correct way to create a ListingOutcome.
        Computes all derived boolean fields from the raw prices.
        """
        r = (listing_price - issue_price) / issue_price
        return cls(
            ipo_id=ipo_id,
            listing_date=listing_date,
            issue_price=issue_price,
            listing_price=listing_price,
            listing_price_quality=listing_price_quality,
            source=source,
            source_reference=source_reference,
            observed_at=observed_at,
            retrieved_at=retrieved_at,
            listing_return=r,
            positive_listing=listing_price > issue_price,
            return_gt_5=r > Decimal("0.05"),
            return_gt_10=r > Decimal("0.10"),
            return_gt_15=r > Decimal("0.15"),
            return_gt_20=r > Decimal("0.20"),
            return_lt_0=r < Decimal("0"),
            return_lt_neg5=r < Decimal("-0.05"),
            return_lt_neg10=r < Decimal("-0.10"),
            return_lt_neg20=r < Decimal("-0.20"),
        )

    @property
    def listing_return_pct(self) -> Decimal:
        """listing_return expressed as a percentage (e.g., 0.293 → 29.3)."""
        return self.listing_return * 100

    def __repr__(self) -> str:
        sign = "+" if self.listing_return >= 0 else ""
        return (
            f"ListingOutcome({self.ipo_id!r}, "
            f"{sign}{float(self.listing_return_pct):.1f}%, "
            f"quality={self.listing_price_quality.value})"
        )


class AllotmentOutcome(BaseModel):
    """
    What a specific retail investor actually received from an IPO.

    In Phase 1 this is either:
    - Computed from the SEBI retail allotment formula (DERIVED quality)
    - Loaded from a Basis of Allotment PDF (PRIMARY_VERIFIED quality)

    NOT to be confused with ListingOutcome — this records the investor's
    position, not the market outcome.
    """

    ipo_id: str
    investor_category: str = "RETAIL"

    lots_applied: int
    """Number of lots the investor applied for."""

    lots_allotted: Optional[int] = None
    """
    Lots actually allotted. None if allotment data is not available.
    Do NOT fabricate. Leave None and flag allotment_source as MISSING.
    """

    allotment_prob: Optional[Decimal] = None
    """
    Estimated probability of receiving at least 1 lot.
    For retail (post-2011 SEBI lottery): min(1, 1/retail_subscription_x).
    For pre-2011 pro-rata: different formula (not used in V1 scope).
    """

    allotment_source: DataQuality = DataQuality.MISSING

    gross_pnl_per_lot: Optional[Decimal] = None
    """
    (listing_price - issue_price) * lot_size.
    None if allotment or listing price is unavailable.
    """

    @field_validator("lots_applied")
    @classmethod
    def lots_applied_positive(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("lots_applied must be >= 1")
        return v
