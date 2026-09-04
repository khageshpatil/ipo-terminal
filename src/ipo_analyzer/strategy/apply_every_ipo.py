"""
Apply-Every-IPO baseline strategy.

The simplest possible baseline: for every eligible IPO in the dataset,
the decision is always APPLY with the minimum retail lot.

This is NOT a predictive strategy. It is the benchmark against which
any model must be compared. A model that does not beat this baseline
on out-of-sample data has no demonstrated value.

Two sub-baselines:
1. listing_return_baseline: raw listing return distribution, no allotment considered.
2. allotment_aware_baseline: accounts for allotment probability using SEBI formula.
   Only computed where retail_subscription_x is available.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Optional

from ipo_analyzer.allotment.retail_formula import (
    AllotmentEstimate,
    expected_gross_pnl_per_application,
    retail_allotment_probability,
)
from ipo_analyzer.domain.observations import SubscriptionSnapshot
from ipo_analyzer.domain.outcomes import ListingOutcome
from ipo_analyzer.domain.quality import DataQuality


@dataclass
class ApplicationResult:
    """Result of applying to one IPO under the Apply-Every-IPO strategy."""

    ipo_id: str
    year: int

    # From listing outcome
    listing_return: Decimal
    positive_listing: bool
    issue_price: Decimal
    listing_price: Decimal
    listing_price_quality: DataQuality

    # Allotment (where available)
    retail_subscription_x: Optional[Decimal] = None
    allotment_estimate: Optional[AllotmentEstimate] = None
    expected_gross_pnl: Optional[Decimal] = None
    """E[gross P&L] per application = P(allotment) × (return × issue_price × lot_size)"""

    lot_size: Optional[int] = None
    min_application_inr: Optional[Decimal] = None

    has_allotment_data: bool = False


@dataclass
class BaselineReport:
    """
    Full Apply-Every-IPO baseline report.

    listing_return_baseline:    Statistics ignoring allotment probability.
    allotment_aware_baseline:   Statistics on expected value per application.
    n_without_allotment_data:   IPOs excluded from allotment baseline.
    """

    strategy_name: str = "Apply-Every-IPO"
    strategy_version: str = "1.0"
    dataset_description: str = ""

    results: list[ApplicationResult] = field(default_factory=list)

    # Listing return baseline (all records with a listing outcome)
    n_total: int = 0
    n_positive: int = 0
    n_negative: int = 0
    positive_rate: float = 0.0
    mean_listing_return: float = 0.0
    median_listing_return: float = 0.0

    # Allotment-aware baseline (only records with subscription data)
    n_with_allotment_data: int = 0
    n_without_allotment_data: int = 0
    mean_expected_pnl: Optional[float] = None
    median_expected_pnl: Optional[float] = None

    bias_warning: str = (
        "This baseline is computed on a biased 35-record sample. "
        "Results are pipeline validation only, not strategy evidence."
    )


def run_apply_every_ipo(
    outcomes: list[ListingOutcome],
    subscriptions: Optional[dict[str, SubscriptionSnapshot]] = None,
    ipos_by_id: Optional[dict] = None,
    dataset_description: str = "35-record confirmed sample",
) -> BaselineReport:
    """
    Run the Apply-Every-IPO baseline against a set of listing outcomes.

    Parameters
    ----------
    outcomes:
        ListingOutcome records (from the research CSV loader).
    subscriptions:
        Optional mapping from ipo_id to SubscriptionSnapshot.
        Where present, allotment probability is computed.
        Where absent, the IPO is included in listing-return baseline only.
    ipos_by_id:
        Optional mapping from ipo_id to IPO (for lot_size and year).
    dataset_description:
        Human-readable description.
    """
    import statistics as stats

    report = BaselineReport(dataset_description=dataset_description)
    results: list[ApplicationResult] = []

    for outcome in outcomes:
        if not outcome.listing_price_quality.is_usable_for_research():
            continue

        ipo = ipos_by_id.get(outcome.ipo_id) if ipos_by_id else None
        year = ipo.year if ipo else outcome.listing_date.year
        lot_size = ipo.issue_terms.lot_size if ipo else None
        min_app = (
            outcome.issue_price * lot_size
            if lot_size is not None
            else None
        )

        sub = subscriptions.get(outcome.ipo_id) if subscriptions else None
        retail_x = sub.retail_subscription_x if sub else None

        allotment_est: Optional[AllotmentEstimate] = None
        expected_pnl: Optional[Decimal] = None

        if retail_x is not None and lot_size is not None:
            allotment_est = retail_allotment_probability(retail_x)
            expected_pnl = expected_gross_pnl_per_application(
                retail_subscription_x=retail_x,
                issue_price=outcome.issue_price,
                lot_size=lot_size,
                listing_return=outcome.listing_return,
            )

        result = ApplicationResult(
            ipo_id=outcome.ipo_id,
            year=year,
            listing_return=outcome.listing_return,
            positive_listing=outcome.positive_listing,
            issue_price=outcome.issue_price,
            listing_price=outcome.listing_price,
            listing_price_quality=outcome.listing_price_quality,
            retail_subscription_x=retail_x,
            allotment_estimate=allotment_est,
            expected_gross_pnl=expected_pnl,
            lot_size=lot_size,
            min_application_inr=min_app,
            has_allotment_data=retail_x is not None,
        )
        results.append(result)

    report.results = results
    report.n_total = len(results)

    if results:
        returns = [float(r.listing_return) for r in results]
        report.n_positive = sum(1 for r in results if r.positive_listing)
        report.n_negative = report.n_total - report.n_positive
        report.positive_rate = report.n_positive / report.n_total
        report.mean_listing_return = stats.mean(returns)
        report.median_listing_return = stats.median(returns)

    # Records with subscription data (retail_x available), regardless of lot_size
    results_with_sub = [r for r in results if r.has_allotment_data]
    report.n_with_allotment_data = len(results_with_sub)
    report.n_without_allotment_data = report.n_total - report.n_with_allotment_data

    # Expected P&L only computable where lot_size AND retail_x are both present
    pnl_results = [r for r in results_with_sub if r.expected_gross_pnl is not None]
    if pnl_results:
        pnls = [float(r.expected_gross_pnl) for r in pnl_results]  # type: ignore[arg-type]
        report.mean_expected_pnl = stats.mean(pnls)
        report.median_expected_pnl = stats.median(pnls)

    return report
