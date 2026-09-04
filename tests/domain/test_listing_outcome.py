"""
Tests for ListingOutcome domain entity.

Covers:
- Correct return calculation
- Positive/negative classification
- All threshold labels (>5%, >10%, >15%, >20%, <0%, <-5%, <-10%, <-20%)
- Invalid price validation
- Naive datetime rejection
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal

import pytest

from ipo_analyzer.domain.outcomes import ListingOutcome
from ipo_analyzer.domain.quality import DataQuality

UTC = timezone.utc


def make_outcome(
    issue_price: str,
    listing_price: str,
    ipo_id: str = "TEST-2021",
) -> ListingOutcome:
    """Helper to build a ListingOutcome from string decimals."""
    return ListingOutcome.compute(
        ipo_id=ipo_id,
        listing_date=date(2021, 1, 15),
        issue_price=Decimal(issue_price),
        listing_price=Decimal(listing_price),
        listing_price_quality=DataQuality.SECONDARY_VERIFIED,
        source="test",
        source_reference=None,
        observed_at=datetime(2021, 1, 15, 4, 0, tzinfo=UTC),
        retrieved_at=datetime(2021, 1, 15, 5, 0, tzinfo=UTC),
    )


class TestListingReturnCalculation:
    def test_positive_return(self) -> None:
        o = make_outcome("100", "130")
        assert o.listing_return == Decimal("0.30")
        assert o.listing_return_pct == Decimal("30")

    def test_negative_return(self) -> None:
        o = make_outcome("100", "80")
        assert o.listing_return == Decimal("-0.20")
        assert o.listing_return_pct == Decimal("-20")

    def test_zero_return(self) -> None:
        o = make_outcome("100", "100")
        assert o.listing_return == Decimal("0")
        assert o.positive_listing is False  # equal is NOT positive
        assert o.return_lt_0 is False

    def test_zomato_known_values(self) -> None:
        """Zomato: issue=76, listing=126 → +65.78..."""
        o = make_outcome("76", "126")
        expected = (Decimal("126") - Decimal("76")) / Decimal("76")
        assert abs(o.listing_return - expected) < Decimal("0.0001")

    def test_paytm_known_values(self) -> None:
        """Paytm: issue=2150, listing=1564 → -27.25..."""
        o = make_outcome("2150", "1564")
        expected = (Decimal("1564") - Decimal("2150")) / Decimal("2150")
        assert abs(o.listing_return - expected) < Decimal("0.0001")
        assert o.listing_return < 0

    def test_bandhan_known_values(self) -> None:
        """Bandhan Bank: issue=375, listing=485 → +29.33..."""
        o = make_outcome("375", "485")
        expected = (Decimal("485") - Decimal("375")) / Decimal("375")
        assert abs(o.listing_return - expected) < Decimal("0.0001")


class TestClassificationLabels:
    def test_positive_listing_true(self) -> None:
        assert make_outcome("100", "101").positive_listing is True

    def test_positive_listing_false_at_issue_price(self) -> None:
        assert make_outcome("100", "100").positive_listing is False

    def test_positive_listing_false_below(self) -> None:
        assert make_outcome("100", "99").positive_listing is False

    def test_return_lt_0(self) -> None:
        # listing=95, issue=100 → return=-5.0% exactly
        # -5.0% is < 0% but NOT strictly < -5% (it's equal to -5%)
        o = make_outcome("100", "95")
        assert o.return_lt_0 is True
        assert o.return_lt_neg5 is False  # exactly -5% is NOT < -5%
        assert o.return_lt_neg10 is False

    def test_return_lt_neg5_strict(self) -> None:
        # listing=94, issue=100 → return=-6% → strictly < -5%
        o = make_outcome("100", "94")
        assert o.return_lt_neg5 is True
        assert o.return_lt_neg10 is False

    def test_return_lt_neg10(self) -> None:
        o = make_outcome("100", "88")
        assert o.return_lt_neg10 is True
        assert o.return_lt_neg20 is False

    def test_return_lt_neg20(self) -> None:
        o = make_outcome("100", "78")
        assert o.return_lt_neg20 is True

    def test_return_gt_5(self) -> None:
        o = make_outcome("100", "106")
        assert o.return_gt_5 is True
        assert o.return_gt_10 is False

    def test_return_gt_10(self) -> None:
        o = make_outcome("100", "111")
        assert o.return_gt_10 is True
        assert o.return_gt_15 is False

    def test_return_gt_15(self) -> None:
        o = make_outcome("100", "116")
        assert o.return_gt_15 is True
        assert o.return_gt_20 is False

    def test_return_gt_20(self) -> None:
        o = make_outcome("100", "121")
        assert o.return_gt_20 is True

    def test_exactly_at_threshold_is_not_above(self) -> None:
        """A return of exactly 10% is NOT > 10%."""
        o = make_outcome("100", "110")
        assert o.return_gt_10 is False

    def test_sigachi_extreme_positive(self) -> None:
        """Sigachi Industries: issue=163, listing=599 → +267.2%"""
        o = make_outcome("163", "599")
        assert o.return_gt_20 is True
        assert o.positive_listing is True
        assert float(o.listing_return_pct) > 260

    def test_paytm_extreme_negative(self) -> None:
        """Paytm: issue=2150, listing=1564 → -27.25%"""
        o = make_outcome("2150", "1564")
        assert o.return_lt_neg20 is True
        assert o.positive_listing is False


class TestValidation:
    def test_zero_issue_price_raises(self) -> None:
        with pytest.raises(Exception):
            make_outcome("0", "100")

    def test_negative_issue_price_raises(self) -> None:
        with pytest.raises(Exception):
            make_outcome("-10", "100")

    def test_zero_listing_price_raises(self) -> None:
        with pytest.raises(Exception):
            make_outcome("100", "0")

    def test_naive_observed_at_raises(self) -> None:
        with pytest.raises(Exception):
            ListingOutcome.compute(
                ipo_id="X",
                listing_date=date(2021, 1, 1),
                issue_price=Decimal("100"),
                listing_price=Decimal("110"),
                listing_price_quality=DataQuality.SECONDARY_VERIFIED,
                source="test",
                source_reference=None,
                observed_at=datetime(2021, 1, 1, 4, 0),  # NAIVE — no tzinfo
                retrieved_at=datetime(2021, 1, 1, 5, 0, tzinfo=UTC),
            )


class TestDataQualityFlags:
    def test_secondary_verified_not_usable_for_training(self) -> None:
        o = make_outcome("100", "130")
        assert o.listing_price_quality == DataQuality.SECONDARY_VERIFIED
        assert o.listing_price_quality.is_usable_for_training() is False
        assert o.listing_price_quality.is_usable_for_research() is True
