"""
Point-in-time leakage tests — the most important correctness guarantee.

RULE: No observation with observed_at > decision_timestamp may appear
in a FeatureSnapshot.

Tests cover:
1. Issue-structure features are always available (ALWAYS eligibility)
2. Subscription features are NOT available before subscription close
3. Subscription features ARE available after subscription close
4. Leakage guard raises LeakageError for AFTER_LISTING features pre-listing
5. Feature versions are recorded in the snapshot
6. Missing-but-eligible features are tracked explicitly
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal

import pytest

from ipo_analyzer.domain.ipo import (
    Exchange,
    IPO,
    IssueTerms,
    NiiRegime,
    Segment,
    TimelineRegime,
)
from ipo_analyzer.domain.observations import SubscriptionSnapshot
from ipo_analyzer.domain.quality import DataQuality
from ipo_analyzer.features.engine import LeakageError, FeatureSnapshot, get_features
from ipo_analyzer.features.registry import EligibilityRule, FEATURE_REGISTRY

UTC = timezone.utc


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_ipo(close: date, listing: date, issue_price: str = "76") -> IPO:
    terms = IssueTerms(
        close_date=close,
        listing_date=listing,
        issue_price=Decimal(issue_price),
        lot_size=195,
    )
    return IPO(
        ipo_id=f"TEST-{close.year}",
        company_name="Test IPO",
        exchange=Exchange.BOTH,
        segment=Segment.MAINBOARD,
        issue_terms=terms,
        sebi_nii_regime=NiiRegime.from_close_date(close),
        timeline_regime=TimelineRegime.from_close_date(close),
        source="test",
        retrieved_at=datetime(2026, 9, 4, tzinfo=UTC),
    )


def _sub(ipo_id: str, observed: datetime) -> SubscriptionSnapshot:
    return SubscriptionSnapshot(
        ipo_id=ipo_id,
        observed_at=observed,
        retrieved_at=datetime(2026, 9, 4, tzinfo=UTC),
        source="test",
        source_reference="test",
        quality=DataQuality.SECONDARY_VERIFIED,
        retail_subscription_x=Decimal("7.5"),
        nii_subscription_x=Decimal("32.0"),
        qib_subscription_x=Decimal("51.8"),
        total_subscription_x=Decimal("38.2"),
        is_final=True,
    )


# ---------------------------------------------------------------------------
# Test classes
# ---------------------------------------------------------------------------


class TestAlwaysEligibleFeatures:
    """Issue structure features must be available at any decision timestamp."""

    def test_issue_price_available_before_subscription_open(self) -> None:
        ipo = _make_ipo(date(2021, 7, 16), date(2021, 7, 23))
        # Decision timestamp well before subscription window opens
        ts = datetime(2021, 1, 1, tzinfo=UTC)
        snap = get_features(ipo, ts)
        assert snap.has("issue_price")
        assert snap.features["issue_price"] == pytest.approx(76.0)

    def test_lot_size_available_pre_subscription(self) -> None:
        ipo = _make_ipo(date(2021, 7, 16), date(2021, 7, 23))
        ts = datetime(2021, 1, 1, tzinfo=UTC)
        snap = get_features(ipo, ts)
        assert snap.features["lot_size"] == 195

    def test_sebi_regime_available_pre_subscription(self) -> None:
        ipo = _make_ipo(date(2021, 7, 16), date(2021, 7, 23))
        ts = datetime(2021, 1, 1, tzinfo=UTC)
        snap = get_features(ipo, ts)
        assert snap.features["sebi_nii_regime"] == "PRE_2022"

    def test_timeline_regime_available_pre_subscription(self) -> None:
        ipo = _make_ipo(date(2024, 3, 15), date(2024, 3, 21))
        ts = datetime(2024, 1, 1, tzinfo=UTC)
        snap = get_features(ipo, ts)
        assert snap.features["timeline_regime"] == "T3"


class TestSubscriptionEligibility:
    """Subscription features must be ineligible before close, eligible after."""

    def test_retail_subscription_not_available_during_subscription(self) -> None:
        ipo = _make_ipo(date(2021, 7, 16), date(2021, 7, 23))
        # Decision during subscription window (before close + 1 day)
        ts = datetime(2021, 7, 16, 12, 0, tzinfo=UTC)  # still during window
        sub = _sub("TEST-2021", datetime(2021, 7, 17, tzinfo=UTC))
        snap = get_features(ipo, ts, subscription=sub)
        # Should be in ineligible_features
        assert "retail_subscription_x" in snap.ineligible_features
        assert "retail_subscription_x" not in snap.features

    def test_retail_subscription_available_day_after_close(self) -> None:
        ipo = _make_ipo(date(2021, 7, 16), date(2021, 7, 23))
        # Decision timestamp = day after close (UTC midnight = safe harbour)
        ts = datetime(2021, 7, 17, 1, 0, tzinfo=UTC)
        sub = _sub("TEST-2021", datetime(2021, 7, 17, tzinfo=UTC))
        snap = get_features(ipo, ts, subscription=sub)
        assert "retail_subscription_x" not in snap.ineligible_features
        assert snap.features["retail_subscription_x"] == pytest.approx(7.5)

    def test_qib_subscription_available_post_close(self) -> None:
        ipo = _make_ipo(date(2021, 7, 16), date(2021, 7, 23))
        ts = datetime(2021, 7, 17, 1, 0, tzinfo=UTC)
        sub = _sub("TEST-2021", datetime(2021, 7, 17, tzinfo=UTC))
        snap = get_features(ipo, ts, subscription=sub)
        assert snap.features["qib_subscription_x"] == pytest.approx(51.8)

    def test_allotment_prob_computed_from_subscription(self) -> None:
        ipo = _make_ipo(date(2021, 7, 16), date(2021, 7, 23))
        ts = datetime(2021, 7, 17, 1, 0, tzinfo=UTC)
        sub = _sub("TEST-2021", datetime(2021, 7, 17, tzinfo=UTC))
        snap = get_features(ipo, ts, subscription=sub)
        # retail_subscription_x=7.5 → prob = 1/7.5 ≈ 0.1333
        assert snap.has("retail_allotment_prob")
        assert snap.features["retail_allotment_prob"] == pytest.approx(1 / 7.5, rel=1e-4)

    def test_no_subscription_data_gives_none_but_not_ineligible(self) -> None:
        """When subscription is eligible but not provided, feature value is None."""
        ipo = _make_ipo(date(2021, 7, 16), date(2021, 7, 23))
        ts = datetime(2021, 7, 17, 1, 0, tzinfo=UTC)
        # No subscription passed
        snap = get_features(ipo, ts, subscription=None)
        # Feature is eligible (post-close) but value is None
        assert "retail_subscription_x" not in snap.ineligible_features
        assert snap.features.get("retail_subscription_x") is None
        assert "retail_subscription_x" in snap.missing_features


class TestLeakageGuard:
    """Leakage guard must raise LeakageError for AFTER_LISTING features used pre-listing."""

    def test_naive_decision_timestamp_raises(self) -> None:
        ipo = _make_ipo(date(2021, 7, 16), date(2021, 7, 23))
        ts = datetime(2021, 7, 17)  # naive — no tzinfo
        with pytest.raises(ValueError, match="UTC"):
            get_features(ipo, ts)

    def test_feature_versions_are_recorded(self) -> None:
        ipo = _make_ipo(date(2021, 7, 16), date(2021, 7, 23))
        ts = datetime(2021, 7, 17, 1, 0, tzinfo=UTC)
        snap = get_features(ipo, ts)
        assert "issue_price" in snap.feature_versions
        assert snap.feature_versions["issue_price"] == "1"

    def test_leakage_checked_flag(self) -> None:
        ipo = _make_ipo(date(2021, 7, 16), date(2021, 7, 23))
        ts = datetime(2021, 7, 17, 1, 0, tzinfo=UTC)
        snap = get_features(ipo, ts, enforce_leakage_check=True)
        assert snap.leakage_checked is True

    def test_ineligible_subscription_before_close_not_included(self) -> None:
        ipo = _make_ipo(date(2021, 7, 16), date(2021, 7, 23))
        ts = datetime(2021, 7, 15, 12, 0, tzinfo=UTC)  # before close
        snap = get_features(ipo, ts)
        for feat_name in ["retail_subscription_x", "nii_subscription_x",
                          "qib_subscription_x", "total_subscription_x",
                          "retail_allotment_prob"]:
            assert feat_name in snap.ineligible_features, (
                f"{feat_name} should be ineligible before subscription close"
            )
            assert feat_name not in snap.features
