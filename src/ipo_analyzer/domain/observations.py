"""
Time-varying observations tied to an IPO.

Every observation records:
- observed_at: the real-world time the value was true (or the closest approximation)
- retrieved_at: when we ingested/stored this observation
- source: provider description
- source_reference: specific URL, file path, or document ID
- quality: DataQuality classification

These are separate from the IPO root entity precisely because they
are time-varying and may be updated as new data arrives.

Point-in-time rule: a feature computed at decision_timestamp D may only
use observations where observed_at <= D.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, field_validator

from ipo_analyzer.domain.quality import DataQuality


class Observation(BaseModel):
    """
    Base class for all time-varying observations associated with an IPO.
    Subclasses must not remove any of these provenance fields.
    """

    ipo_id: str
    """Foreign key to IPO.ipo_id."""

    observed_at: datetime
    """
    The real-world time at which the observation was valid.
    For final subscription data: the subscription window close time (typically 5:00 PM on close_date).
    For listing prices: the pre-open equilibrium matching time on listing_date (~9:45 AM IST).
    Must be UTC-aware.
    """

    retrieved_at: datetime
    """
    When this record was ingested into our system.
    Always >= observed_at. Must be UTC-aware.
    """

    source: str
    """Description of the data provider (e.g., 'NSE Bhav Copy', 'Chittorgarh')."""

    source_reference: str
    """Specific locator: URL, filename, document ID."""

    quality: DataQuality

    @field_validator("observed_at", "retrieved_at")
    @classmethod
    def must_be_utc_aware(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("All observation datetimes must be UTC-aware")
        return v

    @field_validator("retrieved_at")
    @classmethod
    def retrieved_not_before_observed(cls, v: datetime) -> datetime:
        # We can't cross-check with observed_at here in a single-field validator;
        # model_validator handles that if needed per subclass.
        return v


class SubscriptionSnapshot(Observation):
    """
    Final category-wise subscription data for an IPO at the close of the
    subscription window (T+0, ~5:00 PM on close_date).

    These values are final and do not change after publication.
    They represent the number of times each investor category's quota
    was oversubscribed by bid quantity.

    Point-in-time: eligible only when decision_timestamp >= observed_at
    (i.e., after subscription window closed).
    """

    retail_subscription_x: Optional[Decimal] = None
    """Times retail (RII) quota was subscribed. None = data not available."""

    nii_subscription_x: Optional[Decimal] = None
    """Times NII/HNI quota was subscribed (combined sNII+bNII or pre-2022 NII)."""

    qib_subscription_x: Optional[Decimal] = None
    """
    Times QIB quota was subscribed. WARNING: may or may not include anchor
    investors depending on source. Check qib_includes_anchor flag.
    """

    total_subscription_x: Optional[Decimal] = None
    """Overall subscription multiple across all categories."""

    snii_subscription_x: Optional[Decimal] = None
    """Small NII (₹2L–₹10L) subscription. Populated for POST_2022 regime only."""

    bnii_subscription_x: Optional[Decimal] = None
    """Big NII (>₹10L) subscription. Populated for POST_2022 regime only."""

    qib_includes_anchor: Optional[bool] = None
    """
    If True: qib_subscription_x denominator is total QIB quota (incl. anchor).
    If False: denominator is public QIB quota only.
    If None: unknown; assume True (most common in aggregator reporting).
    """

    is_final: bool = True
    """
    True if this snapshot represents the final published subscription figure.
    False for intraday snapshots (which are excluded from historical backtesting).
    """

    @field_validator(
        "retail_subscription_x",
        "nii_subscription_x",
        "qib_subscription_x",
        "total_subscription_x",
        "snii_subscription_x",
        "bnii_subscription_x",
    )
    @classmethod
    def subscription_must_be_non_negative(cls, v: Optional[Decimal]) -> Optional[Decimal]:
        if v is not None and v < 0:
            raise ValueError(f"Subscription multiple cannot be negative, got {v}")
        return v


class GMPSnapshot(Observation):
    """
    Grey Market Premium snapshot at a specific point in time.

    GMP is explicitly unofficial and must NEVER be used as a historical
    backtest feature (per ADR-003 and feasibility report). Stored for
    live production use only; excluded from historical training data.

    This entity exists in the domain model so the data pipeline can
    receive and store GMP snapshots without confusing them with verified data.
    """

    gmp_inr: Optional[Decimal] = None
    """Grey Market Premium in INR per share above issue price."""

    gmp_pct: Optional[Decimal] = None
    """Grey Market Premium as percentage of issue price."""

    source_name: Optional[str] = None
    """Name of GMP provider (e.g., 'investorgain_gmp', 'ipowatch_gmp')."""


class MarketSnapshot(Observation):
    """
    Market regime snapshot (index levels, volatility) on a specific date.

    Used to characterise the market environment at the time of subscription close.
    Source: NSE historical data (freely downloadable).
    """

    snapshot_date: Optional[str] = None
    """Calendar date this snapshot represents (YYYY-MM-DD string; date avoided for Pydantic v2 compat)."""

    nifty50_close: Optional[Decimal] = None
    """Nifty 50 closing level on this date."""

    nifty50_1m_return: Optional[Decimal] = None
    """Nifty 50 return over the prior 30 calendar days."""

    nifty50_3m_return: Optional[Decimal] = None
    """Nifty 50 return over the prior 90 calendar days."""

    india_vix_close: Optional[Decimal] = None
    """India VIX (volatility index) closing level."""

    nifty_ipo_index: Optional[Decimal] = None
    """Nifty IPO Index closing level (available from 2020 onwards)."""
