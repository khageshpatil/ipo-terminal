"""Timezone-safe live IPO status classification tests."""

from datetime import date, datetime, timezone

import pytest

from ipo_analyzer.live.chittorgarh_live import determine_status


UTC = timezone.utc


@pytest.mark.parametrize(
    ("now", "expected"),
    [
        (datetime(2026, 9, 8, 18, tzinfo=UTC), "UPCOMING"),
        (datetime(2026, 9, 9, 4, 30, tzinfo=UTC), "OPEN"),  # 10:00 IST
        (datetime(2026, 9, 11, 18, tzinfo=UTC), "OPEN"),
        (datetime(2026, 9, 12, 4, 30, tzinfo=UTC), "CLOSED"),
        (datetime(2026, 9, 17, 4, 30, tzinfo=UTC), "LISTED"),
    ],
)
def test_status_boundaries_are_timezone_safe(now, expected):
    assert determine_status(
        date(2026, 9, 9),
        date(2026, 9, 11),
        date(2026, 9, 17),
        now,
    ) == expected


def test_missing_listing_date_can_still_be_open_or_closed():
    now = datetime(2026, 9, 10, 12, tzinfo=UTC)
    assert determine_status(date(2026, 9, 9), date(2026, 9, 11), None, now) == "OPEN"
    assert determine_status(date(2026, 9, 1), date(2026, 9, 3), None, now) == "CLOSED"


def test_missing_dates_are_unknown_not_fabricated():
    now = datetime(2026, 9, 10, 12, tzinfo=UTC)
    assert determine_status(None, None, None, now) == "UNKNOWN"
    assert determine_status(date(2026, 9, 9), None, None, now) == "UNKNOWN"


def test_naive_now_is_rejected():
    with pytest.raises(ValueError, match="timezone-aware"):
        determine_status(None, None, None, datetime(2026, 9, 10))
