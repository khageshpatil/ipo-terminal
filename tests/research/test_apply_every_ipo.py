"""
Tests for Apply-Every-IPO baseline strategy.

Covers:
- Listing-return baseline: all records with outcomes
- Allotment-aware baseline: only records with subscription data
- Records without allotment data are excluded from allotment stats only (not listing stats)
- Bias warning is attached
- Expected P&L formula correctness
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal

import pytest

from ipo_analyzer.allotment.retail_formula import (
    expected_gross_pnl_per_application,
    retail_allotment_probability,
)
from ipo_analyzer.domain.observations import SubscriptionSnapshot
from ipo_analyzer.domain.outcomes import ListingOutcome
from ipo_analyzer.domain.quality import DataQuality
from ipo_analyzer.strategy.apply_every_ipo import run_apply_every_ipo

UTC = timezone.utc
_RETRIEVED = datetime(2026, 9, 4, tzinfo=UTC)


def _outcome(
    ipo_id: str,
    issue: str,
    listing: str,
    year: int = 2021,
    quality: DataQuality = DataQuality.SECONDARY_VERIFIED,
) -> ListingOutcome:
    d = date(year, 6, 15)
    return ListingOutcome.compute(
        ipo_id=ipo_id,
        listing_date=d,
        issue_price=Decimal(issue),
        listing_price=Decimal(listing),
        listing_price_quality=quality,
        source="test",
        source_reference=None,
        observed_at=datetime(year, 6, 15, 4, 0, tzinfo=UTC),
        retrieved_at=_RETRIEVED,
    )


def _sub(ipo_id: str, retail_x: str) -> SubscriptionSnapshot:
    return SubscriptionSnapshot(
        ipo_id=ipo_id,
        observed_at=datetime(2021, 6, 10, 12, 0, tzinfo=UTC),
        retrieved_at=_RETRIEVED,
        source="test",
        source_reference="test",
        quality=DataQuality.SECONDARY_VERIFIED,
        retail_subscription_x=Decimal(retail_x),
        is_final=True,
    )


class TestAllotmentFormula:
    def test_guaranteed_allotment_under_1x(self) -> None:
        result = retail_allotment_probability(Decimal("0.5"))
        assert result.allotment_probability == Decimal("1")
        assert result.method == "guaranteed"

    def test_guaranteed_allotment_at_exactly_1x(self) -> None:
        result = retail_allotment_probability(Decimal("1"))
        assert result.allotment_probability == Decimal("1")

    def test_lottery_at_7_5x(self) -> None:
        """Zomato: retail_subscription_x=7.5 → prob=1/7.5≈0.1333"""
        result = retail_allotment_probability(Decimal("7.5"))
        assert result.method == "lottery"
        assert float(result.allotment_probability) == pytest.approx(1 / 7.5, rel=1e-4)

    def test_lottery_at_28_7x(self) -> None:
        """Sigachi: retail=28.7x → prob≈0.0349"""
        result = retail_allotment_probability(Decimal("28.7"))
        assert float(result.allotment_probability) == pytest.approx(1 / 28.7, rel=1e-4)

    def test_negative_subscription_raises(self) -> None:
        with pytest.raises(ValueError, match=">="):
            retail_allotment_probability(Decimal("-1"))

    def test_expected_pnl_positive_ipo(self) -> None:
        """
        retail_x=7.5, issue=76, lot_size=195, listing_return=+0.658
        P(allot)=1/7.5=0.1333
        gross_pnl_if_allotted = 0.658 * 76 * 195 = 9749.64
        E[pnl] = 0.1333 * 9749.64 ≈ 1299.7
        """
        pnl = expected_gross_pnl_per_application(
            retail_subscription_x=Decimal("7.5"),
            issue_price=Decimal("76"),
            lot_size=195,
            listing_return=Decimal("0.6579"),
        )
        assert pnl is not None
        assert float(pnl) == pytest.approx(1299.7, rel=0.02)

    def test_expected_pnl_negative_ipo(self) -> None:
        """Paytm: retail_x≈1.7, issue=2150, lot=6, return=-0.2726"""
        pnl = expected_gross_pnl_per_application(
            retail_subscription_x=Decimal("1.7"),
            issue_price=Decimal("2150"),
            lot_size=6,
            listing_return=Decimal("-0.2726"),
        )
        assert pnl is not None
        assert float(pnl) < 0  # Expected loss


class TestApplyEveryIPOBaseline:
    def test_listing_return_baseline_all_records(self) -> None:
        outcomes = [
            _outcome("A", "100", "130"),  # +30%
            _outcome("B", "100", "115"),  # +15%
            _outcome("C", "100", "85"),   # -15%
        ]
        report = run_apply_every_ipo(outcomes)
        assert report.n_total == 3
        assert report.n_positive == 2
        assert report.positive_rate == pytest.approx(2 / 3)
        assert report.mean_listing_return == pytest.approx(0.10, abs=0.001)

    def test_no_allotment_data_gives_zeros(self) -> None:
        outcomes = [_outcome("A", "100", "130")]
        report = run_apply_every_ipo(outcomes, subscriptions=None)
        assert report.n_with_allotment_data == 0
        assert report.n_without_allotment_data == 1
        assert report.mean_expected_pnl is None

    def test_allotment_aware_subset(self) -> None:
        outcomes = [
            _outcome("A", "100", "130"),  # has subscription
            _outcome("B", "100", "115"),  # no subscription
        ]
        subscriptions = {"A": _sub("A", "7.5")}
        report = run_apply_every_ipo(outcomes, subscriptions=subscriptions)
        assert report.n_with_allotment_data == 1
        assert report.n_without_allotment_data == 1
        # Listing baseline should include both
        assert report.n_total == 2

    def test_empty_input(self) -> None:
        report = run_apply_every_ipo([])
        assert report.n_total == 0
        assert report.positive_rate == 0.0

    def test_bias_warning_present(self) -> None:
        report = run_apply_every_ipo([_outcome("A", "100", "130")])
        assert report.bias_warning != ""
        assert len(report.bias_warning) > 10

    def test_unverified_quality_excluded_from_baseline(self) -> None:
        outcomes = [
            _outcome("A", "100", "130", quality=DataQuality.SECONDARY_VERIFIED),
            _outcome("B", "100", "150", quality=DataQuality.UNVERIFIED),
        ]
        report = run_apply_every_ipo(outcomes)
        # UNVERIFIED should not pass is_usable_for_research()
        assert report.n_total == 1
