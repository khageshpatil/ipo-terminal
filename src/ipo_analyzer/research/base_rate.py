"""
Base-rate analysis for IPO listing outcomes.

Computes descriptive statistics from a set of ListingOutcome records.
This is research-only — it describes what happened, not what a model predicts.

WARNING: Statistics computed from the 35-record confirmed sample are
biased upward. Famous/notable IPOs are overrepresented. The output
always includes a bias warning when the sample is the research CSV.
"""

from __future__ import annotations

import statistics
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Optional

from ipo_analyzer.domain.outcomes import ListingOutcome
from ipo_analyzer.domain.quality import DataQuality


@dataclass
class ReturnStats:
    """Descriptive statistics for a set of listing returns."""

    n: int
    positive_count: int
    positive_rate: float

    mean: float
    median: float
    std: float
    min_val: float
    max_val: float
    p25: float
    p75: float

    pct_gt_5: float
    pct_gt_10: float
    pct_gt_15: float
    pct_gt_20: float
    pct_lt_0: float
    pct_lt_neg5: float
    pct_lt_neg10: float
    pct_lt_neg20: float

    quality_counts: dict[str, int] = field(default_factory=dict)
    """Count of records by DataQuality level."""

    @property
    def negative_count(self) -> int:
        return self.n - self.positive_count

    @property
    def negative_rate(self) -> float:
        return 1.0 - self.positive_rate


@dataclass
class BaseRateReport:
    """
    Full base-rate analysis output.

    overall:        Statistics across all records.
    by_year:        Statistics grouped by IPO subscription year.
    bias_warning:   Always set when using the 35-record sample.
    excluded:       Records excluded from analysis and why.
    """

    dataset_description: str
    n_total_loaded: int
    n_with_outcome: int
    n_excluded: int

    overall: ReturnStats
    by_year: dict[int, ReturnStats]

    bias_warning: Optional[str] = None
    excluded_reasons: list[str] = field(default_factory=list)


def _percentile(sorted_vals: list[float], p: float) -> float:
    """Simple linear interpolation percentile on a sorted list."""
    if not sorted_vals:
        return float("nan")
    n = len(sorted_vals)
    if n == 1:
        return sorted_vals[0]
    idx = p / 100 * (n - 1)
    lo = int(idx)
    hi = lo + 1
    if hi >= n:
        return sorted_vals[-1]
    frac = idx - lo
    return sorted_vals[lo] + frac * (sorted_vals[hi] - sorted_vals[lo])


def _compute_stats(outcomes: list[ListingOutcome]) -> ReturnStats:
    """Compute ReturnStats from a list of ListingOutcome records."""
    returns = [float(o.listing_return) for o in outcomes]
    n = len(returns)
    if n == 0:
        return ReturnStats(
            n=0, positive_count=0, positive_rate=0.0,
            mean=float("nan"), median=float("nan"), std=float("nan"),
            min_val=float("nan"), max_val=float("nan"), p25=float("nan"), p75=float("nan"),
            pct_gt_5=0.0, pct_gt_10=0.0, pct_gt_15=0.0, pct_gt_20=0.0,
            pct_lt_0=0.0, pct_lt_neg5=0.0, pct_lt_neg10=0.0, pct_lt_neg20=0.0,
        )

    sorted_r = sorted(returns)
    pos = sum(1 for o in outcomes if o.positive_listing)

    quality_counts: dict[str, int] = {}
    for o in outcomes:
        k = o.listing_price_quality.value
        quality_counts[k] = quality_counts.get(k, 0) + 1

    return ReturnStats(
        n=n,
        positive_count=pos,
        positive_rate=pos / n,
        mean=statistics.mean(returns),
        median=statistics.median(returns),
        std=statistics.stdev(returns) if n > 1 else 0.0,
        min_val=min(returns),
        max_val=max(returns),
        p25=_percentile(sorted_r, 25),
        p75=_percentile(sorted_r, 75),
        pct_gt_5=sum(1 for o in outcomes if o.return_gt_5) / n,
        pct_gt_10=sum(1 for o in outcomes if o.return_gt_10) / n,
        pct_gt_15=sum(1 for o in outcomes if o.return_gt_15) / n,
        pct_gt_20=sum(1 for o in outcomes if o.return_gt_20) / n,
        pct_lt_0=sum(1 for o in outcomes if o.return_lt_0) / n,
        pct_lt_neg5=sum(1 for o in outcomes if o.return_lt_neg5) / n,
        pct_lt_neg10=sum(1 for o in outcomes if o.return_lt_neg10) / n,
        pct_lt_neg20=sum(1 for o in outcomes if o.return_lt_neg20) / n,
        quality_counts=quality_counts,
    )


def compute_base_rate(
    outcomes: list[ListingOutcome],
    ipos_by_id: Optional[dict] = None,
    dataset_description: str = "Unknown dataset",
    n_total_loaded: int = 0,
    is_biased_sample: bool = True,
) -> BaseRateReport:
    """
    Compute base-rate statistics from a list of ListingOutcome records.

    Parameters
    ----------
    outcomes:
        ListingOutcome records to analyse.
    ipos_by_id:
        Optional dict mapping ipo_id to IPO, used for year grouping.
    dataset_description:
        Human-readable description of the dataset.
    n_total_loaded:
        Total IPOs loaded (including those without a listing outcome).
    is_biased_sample:
        If True, attach the standard bias warning for the 35-record sample.
    """
    excluded: list[str] = []
    usable: list[ListingOutcome] = []

    for o in outcomes:
        if not o.listing_price_quality.is_usable_for_research():
            excluded.append(
                f"{o.ipo_id}: quality={o.listing_price_quality.value} — excluded from stats"
            )
        else:
            usable.append(o)

    overall = _compute_stats(usable)

    # Group by year using IPO entity if provided, else use listing_date.year
    by_year: dict[int, list[ListingOutcome]] = {}
    for o in usable:
        if ipos_by_id and o.ipo_id in ipos_by_id:
            year = ipos_by_id[o.ipo_id].year
        else:
            year = o.listing_date.year
        by_year.setdefault(year, []).append(o)

    by_year_stats = {yr: _compute_stats(lst) for yr, lst in sorted(by_year.items())}

    bias_warning = None
    if is_biased_sample:
        bias_warning = (
            "IMPORTANT — SAMPLING BIAS: This analysis uses a non-random sample of "
            f"{len(usable)} notable/famous IPOs. Large winners and famous failures "
            "are overrepresented. These statistics DO NOT represent the true historical "
            "base rate of the full Mainboard IPO universe (~480 IPOs, 2018–2024). "
            "The sample exists only to validate the data pipeline. "
            "Do not use these figures as strategy evidence."
        )

    return BaseRateReport(
        dataset_description=dataset_description,
        n_total_loaded=n_total_loaded or len(outcomes),
        n_with_outcome=len(usable),
        n_excluded=len(excluded),
        overall=overall,
        by_year=by_year_stats,
        bias_warning=bias_warning,
        excluded_reasons=excluded,
    )
