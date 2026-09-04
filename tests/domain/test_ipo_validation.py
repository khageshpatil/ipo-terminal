"""
Tests for IPO domain entity validation.
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

UTC = timezone.utc


class TestIssueTermsValidation:
    def test_valid_terms(self) -> None:
        terms = IssueTerms(
            close_date=date(2021, 7, 16),
            listing_date=date(2021, 7, 23),
            issue_price=Decimal("76"),
        )
        assert terms.issue_price == Decimal("76")

    def test_zero_issue_price_rejected(self) -> None:
        with pytest.raises(Exception, match="positive"):
            IssueTerms(
                close_date=date(2021, 7, 16),
                listing_date=date(2021, 7, 23),
                issue_price=Decimal("0"),
            )

    def test_negative_issue_price_rejected(self) -> None:
        with pytest.raises(Exception):
            IssueTerms(
                close_date=date(2021, 7, 16),
                listing_date=date(2021, 7, 23),
                issue_price=Decimal("-10"),
            )

    def test_listing_before_close_rejected(self) -> None:
        with pytest.raises(Exception, match="listing_date"):
            IssueTerms(
                close_date=date(2021, 7, 23),
                listing_date=date(2021, 7, 16),  # before close!
                issue_price=Decimal("76"),
            )

    def test_lot_size_zero_rejected(self) -> None:
        with pytest.raises(Exception, match="positive"):
            IssueTerms(
                close_date=date(2021, 7, 16),
                listing_date=date(2021, 7, 23),
                issue_price=Decimal("76"),
                lot_size=0,
            )

    def test_min_application_amount(self) -> None:
        terms = IssueTerms(
            close_date=date(2021, 7, 16),
            listing_date=date(2021, 7, 23),
            issue_price=Decimal("76"),
            lot_size=195,
        )
        assert terms.min_application_amount == Decimal("76") * 195

    def test_ofs_fraction(self) -> None:
        terms = IssueTerms(
            close_date=date(2021, 7, 16),
            listing_date=date(2021, 7, 23),
            issue_price=Decimal("76"),
            issue_size_cr=Decimal("9375"),
            ofs_cr=Decimal("375"),
            fresh_issue_cr=Decimal("9000"),
        )
        expected = Decimal("375") / Decimal("9375")
        assert abs(terms.ofs_fraction - expected) < Decimal("0.0001")  # type: ignore[operator]

    def test_fresh_fraction_complements_ofs(self) -> None:
        terms = IssueTerms(
            close_date=date(2021, 7, 16),
            listing_date=date(2021, 7, 23),
            issue_price=Decimal("76"),
            issue_size_cr=Decimal("9375"),
            ofs_cr=Decimal("375"),
            fresh_issue_cr=Decimal("9000"),
        )
        total = terms.ofs_fraction + terms.fresh_issue_fraction  # type: ignore[operator]
        assert abs(total - Decimal("1")) < Decimal("0.001")


class TestRegimeDetection:
    def test_pre_2022_regime(self) -> None:
        assert NiiRegime.from_close_date(date(2021, 7, 16)) == NiiRegime.PRE_2022

    def test_post_2022_regime_on_cutoff(self) -> None:
        assert NiiRegime.from_close_date(date(2022, 9, 1)) == NiiRegime.POST_2022

    def test_post_2022_regime_after_cutoff(self) -> None:
        assert NiiRegime.from_close_date(date(2023, 3, 15)) == NiiRegime.POST_2022

    def test_t6_regime(self) -> None:
        assert TimelineRegime.from_close_date(date(2021, 7, 16)) == TimelineRegime.T6

    def test_t3_regime_on_cutoff(self) -> None:
        assert TimelineRegime.from_close_date(date(2023, 12, 1)) == TimelineRegime.T3

    def test_t3_regime_after_cutoff(self) -> None:
        assert TimelineRegime.from_close_date(date(2024, 3, 15)) == TimelineRegime.T3


class TestIPOEntity:
    def test_naive_retrieved_at_rejected(self) -> None:
        terms = IssueTerms(
            close_date=date(2021, 7, 16),
            listing_date=date(2021, 7, 23),
            issue_price=Decimal("76"),
        )
        with pytest.raises(Exception, match="timezone"):
            IPO(
                ipo_id="TEST",
                company_name="Test Co",
                exchange=Exchange.BOTH,
                segment=Segment.MAINBOARD,
                issue_terms=terms,
                sebi_nii_regime=NiiRegime.PRE_2022,
                timeline_regime=TimelineRegime.T6,
                source="test",
                retrieved_at=datetime(2026, 9, 4, 0, 0),  # NAIVE
            )

    def test_year_property(self) -> None:
        terms = IssueTerms(
            close_date=date(2024, 10, 11),
            listing_date=date(2024, 10, 16),
            issue_price=Decimal("151"),
        )
        ipo = IPO(
            ipo_id="TEST-2024",
            company_name="Test 2024",
            exchange=Exchange.NSE,
            segment=Segment.MAINBOARD,
            issue_terms=terms,
            sebi_nii_regime=NiiRegime.POST_2022,
            timeline_regime=TimelineRegime.T3,
            source="test",
            retrieved_at=datetime(2026, 9, 4, tzinfo=UTC),
        )
        assert ipo.year == 2024

    def test_build_id_with_symbol(self) -> None:
        assert IPO.build_id("ZOMATO", "Zomato Ltd", 2021) == "ZOMATO-2021"

    def test_build_id_without_symbol(self) -> None:
        result = IPO.build_id(None, "Hypothetical Test Company", 2023)
        assert "2023" in result
