"""
Tests for base-rate computation.

Covers:
- Correct positive rate from known records
- Mean/median correctness
- Year breakdown
- Excluded records (quality below threshold)
- Bias warning is always present for sample data
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal

import pytest

from ipo_analyzer.domain.outcomes import ListingOutcome
from ipo_analyzer.domain.quality import DataQuality
from ipo_analyzer.research.base_rate import BaseRateReport, ReturnStats, compute_base_rate

UTC = timezone.utc

_TS = datetime(2021, 1, 1, 4, 0, tzinfo=UTC)
_RETRIEVED = datetime(2026, 9, 4, tzinfo=UTC)


def _outcome(
    ipo_id: str,
    issue: str,
    listing: str,
    listing_year: int = 2021,
    quality: DataQuality = DataQuality.SECONDARY_VERIFIED,
) -> ListingOutcome:
    d = date(listing_year, 6, 15)
    return ListingOutcome.compute(
        ipo_id=ipo_id,
        listing_date=d,
        issue_price=Decimal(issue),
        listing_price=Decimal(listing),
        listing_price_quality=quality,
        source="test",
        source_reference=None,
        observed_at=datetime(listing_year, 6, 15, 4, 0, tzinfo=UTC),
        retrieved_at=_RETRIEVED,
    )


class TestPositiveRate:
    def test_all_positive(self) -> None:
        outcomes = [
            _outcome("A", "100", "150"),
            _outcome("B", "100", "120"),
            _outcome("C", "100", "110"),
        ]
        report = compute_base_rate(outcomes, dataset_description="test", is_biased_sample=False)
        assert report.overall.n == 3
        assert report.overall.positive_count == 3
        assert report.overall.positive_rate == pytest.approx(1.0)

    def test_all_negative(self) -> None:
        outcomes = [
            _outcome("A", "100", "80"),
            _outcome("B", "100", "90"),
        ]
        report = compute_base_rate(outcomes, dataset_description="test", is_biased_sample=False)
        assert report.overall.positive_rate == pytest.approx(0.0)
        assert report.overall.positive_count == 0

    def test_mixed_two_thirds_positive(self) -> None:
        outcomes = [
            _outcome("A", "100", "130"),  # +30%
            _outcome("B", "100", "115"),  # +15%
            _outcome("C", "100", "85"),   # -15%
        ]
        report = compute_base_rate(outcomes, dataset_description="test", is_biased_sample=False)
        assert report.overall.positive_count == 2
        assert report.overall.positive_rate == pytest.approx(2 / 3)


class TestReturnStatistics:
    def test_mean_calculation(self) -> None:
        # +30%, +15%, -15% → mean = +10%
        outcomes = [
            _outcome("A", "100", "130"),
            _outcome("B", "100", "115"),
            _outcome("C", "100", "85"),
        ]
        report = compute_base_rate(outcomes, dataset_description="test", is_biased_sample=False)
        assert report.overall.mean == pytest.approx(0.10, abs=0.001)

    def test_median_calculation(self) -> None:
        # Returns: -15%, +15%, +30% → sorted → median = +15%
        outcomes = [
            _outcome("A", "100", "130"),  # +30%
            _outcome("B", "100", "115"),  # +15%
            _outcome("C", "100", "85"),   # -15%
        ]
        report = compute_base_rate(outcomes, dataset_description="test", is_biased_sample=False)
        assert report.overall.median == pytest.approx(0.15, abs=0.001)

    def test_min_max(self) -> None:
        outcomes = [
            _outcome("A", "100", "130"),   # +30%
            _outcome("B", "100", "85"),    # -15%
            _outcome("C", "163", "599"),   # +267.2% (Sigachi)
        ]
        report = compute_base_rate(outcomes, dataset_description="test", is_biased_sample=False)
        assert report.overall.min_val == pytest.approx(-0.15, abs=0.001)
        assert report.overall.max_val > 2.5  # Sigachi is >260%

    def test_threshold_counts(self) -> None:
        outcomes = [
            _outcome("A", "100", "130"),  # +30% → gt_20=T, gt_15=T, gt_10=T, gt_5=T
            _outcome("B", "100", "108"),  # +8%  → gt_5=T, gt_10=F
            _outcome("C", "100", "85"),   # -15% → lt_0=T, lt_neg10=T
        ]
        report = compute_base_rate(outcomes, dataset_description="test", is_biased_sample=False)
        s = report.overall
        assert s.pct_gt_20 == pytest.approx(1 / 3)
        assert s.pct_gt_5 == pytest.approx(2 / 3)
        assert s.pct_lt_0 == pytest.approx(1 / 3)
        assert s.pct_lt_neg10 == pytest.approx(1 / 3)
        assert s.pct_lt_neg20 == pytest.approx(0.0)


class TestYearBreakdown:
    def test_two_years_separated(self) -> None:
        outcomes = [
            _outcome("A", "100", "150", listing_year=2021),
            _outcome("B", "100", "120", listing_year=2021),
            _outcome("C", "100", "80", listing_year=2022),
        ]
        report = compute_base_rate(outcomes, dataset_description="test", is_biased_sample=False)
        assert 2021 in report.by_year
        assert 2022 in report.by_year
        assert report.by_year[2021].n == 2
        assert report.by_year[2022].n == 1
        assert report.by_year[2021].positive_count == 2
        assert report.by_year[2022].positive_count == 0


class TestQualityFiltering:
    def test_missing_quality_excluded(self) -> None:
        outcomes = [
            _outcome("A", "100", "130", quality=DataQuality.SECONDARY_VERIFIED),
            _outcome("B", "100", "150", quality=DataQuality.MISSING),
        ]
        report = compute_base_rate(outcomes, dataset_description="test", is_biased_sample=False)
        # MISSING quality should be excluded
        assert report.n_with_outcome == 1
        assert report.n_excluded == 1

    def test_unverified_quality_excluded(self) -> None:
        outcomes = [
            _outcome("A", "100", "130", quality=DataQuality.SECONDARY_VERIFIED),
            _outcome("B", "100", "150", quality=DataQuality.UNVERIFIED),
        ]
        report = compute_base_rate(outcomes, dataset_description="test", is_biased_sample=False)
        assert report.n_with_outcome == 1


class TestBiasWarning:
    def test_bias_warning_present_for_sample(self) -> None:
        outcomes = [_outcome("A", "100", "130")]
        report = compute_base_rate(outcomes, dataset_description="test", is_biased_sample=True)
        assert report.bias_warning is not None
        assert len(report.bias_warning) > 50

    def test_no_bias_warning_when_disabled(self) -> None:
        outcomes = [_outcome("A", "100", "130")]
        report = compute_base_rate(outcomes, dataset_description="test", is_biased_sample=False)
        assert report.bias_warning is None


class TestEmptyDataset:
    def test_empty_outcomes_gives_zero_stats(self) -> None:
        report = compute_base_rate([], dataset_description="empty", is_biased_sample=False)
        assert report.overall.n == 0
        assert report.overall.positive_count == 0
