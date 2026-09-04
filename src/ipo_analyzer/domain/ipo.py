"""
Core IPO domain entities.

IPO is the root aggregate. IssueTerms is always embedded in an IPO.
All monetary values use Decimal for precision. All dates are calendar
dates (datetime.date). Timestamps are UTC-aware datetimes.
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator, model_validator


class Segment(str, Enum):
    """Stock exchange listing segment."""

    MAINBOARD = "MAINBOARD"
    SME = "SME"


class Exchange(str, Enum):
    """Primary listing exchange."""

    NSE = "NSE"
    BSE = "BSE"
    BOTH = "BOTH"  # Listed on both NSE and BSE


class IssueType(str, Enum):
    """Nature of the public offering."""

    BOOK_BUILT = "BOOK_BUILT"
    FIXED_PRICE = "FIXED_PRICE"
    BOOK_BUILT_PSU = "BOOK_BUILT_PSU"  # PSU divestment via book-building


class NiiRegime(str, Enum):
    """
    SEBI NII allotment regime.

    PRE_2022:  NII allotment was fully pro-rata (larger applications got more shares).
    POST_2022: SEBI split NII into sNII (₹2L–₹10L) and bNII (>₹10L);
               minimum-lot lottery within each sub-category (effective Sep 2022).
    """

    PRE_2022 = "PRE_2022"
    POST_2022 = "POST_2022"

    @classmethod
    def from_close_date(cls, close_date: date) -> "NiiRegime":
        """Determine regime from IPO subscription close date."""
        cutoff = date(2022, 9, 1)
        return cls.POST_2022 if close_date >= cutoff else cls.PRE_2022


class TimelineRegime(str, Enum):
    """
    SEBI settlement timeline regime.

    T6:  IPO listing on T+6 from close (pre-December 2023).
         Capital blocked for ~9–13 calendar days.
    T3:  IPO listing on T+3 from close (effective December 1, 2023).
         Capital blocked for ~5–8 calendar days.
    """

    T6 = "T6"
    T3 = "T3"

    @classmethod
    def from_close_date(cls, close_date: date) -> "TimelineRegime":
        """Determine timeline regime from IPO subscription close date."""
        cutoff = date(2023, 12, 1)
        return cls.T3 if close_date >= cutoff else cls.T6


class IssueTerms(BaseModel):
    """
    The commercial terms of the public offering as filed with SEBI.

    Point-in-time: these reflect the RHP/Prospectus at time of filing.
    They must never be updated from post-IPO sources.
    """

    open_date: Optional[date] = None
    """First day of subscription window. May be approximate for older records."""

    close_date: date
    """Last day of subscription window. Used for regime determination."""

    listing_date: date
    """Date on which shares first traded on exchange."""

    issue_price: Decimal
    """
    Per-share price paid by allotted investors (in INR).
    For book-built issues: the final price band cut-off.
    For fixed-price issues: the stated fixed price.
    Must be > 0.
    """

    price_band_low: Optional[Decimal] = None
    """Lower bound of price band. None for fixed-price issues."""

    price_band_high: Optional[Decimal] = None
    """Upper bound of price band. None for fixed-price issues."""

    lot_size: Optional[int] = None
    """Minimum shares per application lot. Used for allotment calculation."""

    issue_size_cr: Optional[Decimal] = None
    """Total issue size in INR crore (fresh + OFS)."""

    fresh_issue_cr: Optional[Decimal] = None
    """Fresh capital raised portion in INR crore."""

    ofs_cr: Optional[Decimal] = None
    """Offer-for-sale portion in INR crore."""

    retail_quota_pct: Optional[Decimal] = None
    """Percentage of issue reserved for retail (RII) investors (typically 35%)."""

    qib_quota_pct: Optional[Decimal] = None
    """Percentage reserved for QIBs (typically 50% for book-built)."""

    nii_quota_pct: Optional[Decimal] = None
    """Percentage reserved for NIIs/HNIs (typically 15%)."""

    issue_type: Optional[IssueType] = None

    @field_validator("issue_price")
    @classmethod
    def issue_price_must_be_positive(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError(f"issue_price must be positive, got {v}")
        return v

    @field_validator("lot_size")
    @classmethod
    def lot_size_must_be_positive(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and v <= 0:
            raise ValueError(f"lot_size must be positive, got {v}")
        return v

    @model_validator(mode="after")
    def listing_date_after_close(self) -> "IssueTerms":
        if self.listing_date < self.close_date:
            raise ValueError(
                f"listing_date ({self.listing_date}) must be >= close_date ({self.close_date})"
            )
        return self

    @property
    def min_application_amount(self) -> Optional[Decimal]:
        """Minimum application amount in INR. None if lot_size is unknown."""
        if self.lot_size is None:
            return None
        return self.issue_price * self.lot_size

    @property
    def fresh_issue_fraction(self) -> Optional[Decimal]:
        """Fraction of total issue that is fresh capital. None if data missing."""
        if self.fresh_issue_cr is None or self.issue_size_cr is None:
            return None
        if self.issue_size_cr == 0:
            return None
        return self.fresh_issue_cr / self.issue_size_cr

    @property
    def ofs_fraction(self) -> Optional[Decimal]:
        """Fraction of total issue that is OFS (promoter exit signal)."""
        if self.ofs_cr is None or self.issue_size_cr is None:
            return None
        if self.issue_size_cr == 0:
            return None
        return self.ofs_cr / self.issue_size_cr


class IPO(BaseModel):
    """
    Root aggregate for an IPO event.

    An IPO is uniquely identified by ipo_id. The company_name and
    nse_symbol are as-at-IPO — they should not be updated to reflect
    post-listing name changes (which should be stored as a separate note).
    """

    ipo_id: str
    """
    Canonical internal identifier. Format: "{NSE_SYMBOL}-{YEAR}" where
    available, or a descriptive slug. Must be unique within the system.
    """

    company_name: str
    """Company name as it appeared in the IPO prospectus."""

    nse_symbol: Optional[str] = None
    """NSE trading symbol post-listing. Approximate for older records."""

    bse_code: Optional[str] = None
    """BSE scrip code post-listing."""

    exchange: Exchange
    """Primary listing exchange. BOTH for dual-listed."""

    segment: Segment = Segment.MAINBOARD
    """Always MAINBOARD in Phase 1. SME excluded per scope."""

    issue_terms: IssueTerms
    """Commercial terms of the issue."""

    sebi_nii_regime: NiiRegime
    """Determined from issue_terms.close_date. Stored explicitly for auditability."""

    timeline_regime: TimelineRegime
    """T3 or T6 regime. Stored explicitly for opportunity cost calculation."""

    source: str
    """Description of primary data source for this IPO record."""

    source_reference: Optional[str] = None
    """Specific URL, document ID, or file reference."""

    retrieved_at: datetime
    """When this record was ingested into the system (UTC)."""

    notes: Optional[str] = None
    """Free-text notes, caveats, or anomaly flags for this IPO."""

    @field_validator("retrieved_at")
    @classmethod
    def retrieved_at_must_be_utc(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("retrieved_at must be timezone-aware (UTC)")
        return v

    @classmethod
    def build_id(cls, nse_symbol: Optional[str], company_name: str, year: int) -> str:
        """Generate a canonical ipo_id from available fields."""
        if nse_symbol:
            slug = nse_symbol.upper()
        else:
            slug = company_name.upper().replace(" ", "_")[:20]
        return f"{slug}-{year}"

    @property
    def year(self) -> int:
        """Calendar year of subscription close."""
        return self.issue_terms.close_date.year

    def __repr__(self) -> str:
        return f"IPO({self.ipo_id!r}, {self.company_name!r}, {self.year})"


# Sentinel for "no subscription data available at this decision point"
_UTCNOW = datetime.now(tz=timezone.utc)
