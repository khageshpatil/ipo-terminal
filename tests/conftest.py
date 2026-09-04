"""
Shared test fixtures for all test modules.
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path

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
from ipo_analyzer.domain.outcomes import ListingOutcome
from ipo_analyzer.domain.quality import DataQuality

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

UTC = timezone.utc

# The research CSV path relative to repo root
RESEARCH_CSV = Path("data/research/ipo_universe_confirmed_sample.csv")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_utc(*args: int) -> datetime:
    """Construct a UTC-aware datetime from (year, month, day, ...)."""
    return datetime(*args, tzinfo=UTC)


# ---------------------------------------------------------------------------
# IPO fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def zomato_terms() -> IssueTerms:
    return IssueTerms(
        close_date=date(2021, 7, 16),
        listing_date=date(2021, 7, 23),
        issue_price=Decimal("76"),
        lot_size=195,
    )


@pytest.fixture
def zomato_ipo(zomato_terms: IssueTerms) -> IPO:
    return IPO(
        ipo_id="ZOMATO-2021",
        company_name="Zomato Ltd",
        nse_symbol="ZOMATO",
        exchange=Exchange.BOTH,
        segment=Segment.MAINBOARD,
        issue_terms=zomato_terms,
        sebi_nii_regime=NiiRegime.PRE_2022,
        timeline_regime=TimelineRegime.T6,
        source="test fixture",
        retrieved_at=make_utc(2026, 9, 4),
    )


@pytest.fixture
def zomato_outcome() -> ListingOutcome:
    return ListingOutcome.compute(
        ipo_id="ZOMATO-2021",
        listing_date=date(2021, 7, 23),
        issue_price=Decimal("76"),
        listing_price=Decimal("126"),
        listing_price_quality=DataQuality.SECONDARY_VERIFIED,
        source="test fixture",
        source_reference=None,
        observed_at=make_utc(2021, 7, 23, 4, 0, 0),
        retrieved_at=make_utc(2026, 9, 4),
    )


@pytest.fixture
def paytm_ipo() -> IPO:
    terms = IssueTerms(
        close_date=date(2021, 11, 10),
        listing_date=date(2021, 11, 18),
        issue_price=Decimal("2150"),
        lot_size=6,
    )
    return IPO(
        ipo_id="PAYTM-2021",
        company_name="One 97 Communications (Paytm)",
        nse_symbol="PAYTM",
        exchange=Exchange.BOTH,
        segment=Segment.MAINBOARD,
        issue_terms=terms,
        sebi_nii_regime=NiiRegime.PRE_2022,
        timeline_regime=TimelineRegime.T6,
        source="test fixture",
        retrieved_at=make_utc(2026, 9, 4),
    )


@pytest.fixture
def paytm_outcome() -> ListingOutcome:
    return ListingOutcome.compute(
        ipo_id="PAYTM-2021",
        listing_date=date(2021, 11, 18),
        issue_price=Decimal("2150"),
        listing_price=Decimal("1564"),
        listing_price_quality=DataQuality.SECONDARY_VERIFIED,
        source="test fixture",
        source_reference=None,
        observed_at=make_utc(2021, 11, 18, 4, 0, 0),
        retrieved_at=make_utc(2026, 9, 4),
    )


@pytest.fixture
def lic_ipo() -> IPO:
    terms = IssueTerms(
        close_date=date(2022, 5, 9),
        listing_date=date(2022, 5, 17),
        issue_price=Decimal("949"),
        lot_size=15,
    )
    return IPO(
        ipo_id="LICI-2022",
        company_name="Life Insurance Corporation (LIC)",
        nse_symbol="LICI",
        exchange=Exchange.BOTH,
        segment=Segment.MAINBOARD,
        issue_terms=terms,
        sebi_nii_regime=NiiRegime.PRE_2022,
        timeline_regime=TimelineRegime.T6,
        source="test fixture",
        retrieved_at=make_utc(2026, 9, 4),
    )


@pytest.fixture
def zomato_subscription(zomato_ipo: IPO) -> SubscriptionSnapshot:
    """Final subscription data for Zomato (2021). Observed at close_date + 1 day."""
    return SubscriptionSnapshot(
        ipo_id="ZOMATO-2021",
        observed_at=make_utc(2021, 7, 17, 12, 0, 0),  # day after close
        retrieved_at=make_utc(2026, 9, 4),
        source="Manual research",
        source_reference="Economic Times Jul 2021",
        quality=DataQuality.SECONDARY_VERIFIED,
        retail_subscription_x=Decimal("7.5"),
        nii_subscription_x=Decimal("32.0"),
        qib_subscription_x=Decimal("51.8"),
        total_subscription_x=Decimal("38.2"),
        is_final=True,
    )
