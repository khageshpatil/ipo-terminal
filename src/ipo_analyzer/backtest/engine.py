"""
Backtest engine — Phase 5.

Runs a strategy over a historical IPO dataset and computes P&L metrics.

Architecture note: strategies are plain callables (IPO, features) → Decision.
The engine handles iteration, allotment modelling, and capital accounting.
ML models plug in as drop-in replacements for rule-based strategies later.
"""

from __future__ import annotations

import statistics
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from typing import Callable, Optional, Protocol

from ipo_analyzer.allotment.retail_formula import (
    expected_gross_pnl_per_application,
    retail_allotment_probability,
)
from ipo_analyzer.domain.outcomes import ListingOutcome
from ipo_analyzer.domain.quality import DataQuality


# ---------------------------------------------------------------------------
# Decision protocol — strategies must return this
# ---------------------------------------------------------------------------

class Recommendation:
    APPLY = "APPLY"
    SKIP = "SKIP"
    WATCH = "WATCH"


@dataclass
class Decision:
    """
    Output of a strategy for a single IPO.
    Strategy implementations return this; the engine acts on it.
    """
    ipo_id: str
    recommendation: str          # APPLY / SKIP / WATCH

    # Scores / estimates from the strategy
    p_positive: Optional[float] = None     # Estimated probability of positive listing
    expected_return_pct: Optional[float] = None
    confidence: str = "RULE_ESTIMATE"      # RULE_ESTIMATE | MODEL_PREDICTION

    # Reason string for UI "WHY?" section
    reason_lines: list[str] = field(default_factory=list)

    def is_apply(self) -> bool:
        return self.recommendation == Recommendation.APPLY


# Strategy type alias — takes (ipo_id, feature_dict) and returns Decision
StrategyFn = Callable[[str, dict], Decision]


# ---------------------------------------------------------------------------
# Per-IPO backtest result
# ---------------------------------------------------------------------------

@dataclass
class BacktestIPOResult:
    ipo_id: str
    year: int
    company_name: str

    decision: Decision

    # Outcome (None if decision was SKIP)
    listing_return: Optional[Decimal] = None
    listing_price_quality: Optional[DataQuality] = None
    positive_listing: Optional[bool] = None

    # Allotment
    retail_subscription_x: Optional[Decimal] = None
    allotment_probability: Optional[float] = None
    lot_size: Optional[int] = None
    issue_price: Optional[Decimal] = None

    # P&L (in INR, per application)
    expected_pnl_per_application: Optional[Decimal] = None
    # Capital required for one lot application
    capital_required: Optional[Decimal] = None

    def applied(self) -> bool:
        return self.decision.is_apply()

    def realised_return_pct(self) -> Optional[float]:
        if self.listing_return is None:
            return None
        return float(self.listing_return) * 100


# ---------------------------------------------------------------------------
# Capital scenarios
# ---------------------------------------------------------------------------

CAPITAL_SCENARIOS = [25_000, 50_000, 1_00_000, 5_00_000]


@dataclass
class CapitalScenario:
    """P&L for one capital level across all applied IPOs."""
    capital_inr: int
    n_ipos_applied: int
    n_ipos_allotted_expected: float   # sum of P(allotment) across applied
    total_expected_pnl: float         # sum of E[PnL] across applied
    total_capital_deployed: float     # sum of min application amounts applied
    capital_utilisation_pct: float
    annualised_return_pct: Optional[float]   # annualised over coverage period


# ---------------------------------------------------------------------------
# Full backtest report
# ---------------------------------------------------------------------------

@dataclass
class BacktestReport:
    strategy_name: str
    strategy_version: str = "1.0"
    dataset_description: str = ""

    results: list[BacktestIPOResult] = field(default_factory=list)

    # Core metrics
    n_total_ipos: int = 0
    n_applied: int = 0
    n_skipped: int = 0

    # Among applied IPOs with known outcomes
    n_positive: int = 0
    n_negative: int = 0
    hit_rate: float = 0.0                   # positive / applied (with outcome)
    mean_listing_return_pct: float = 0.0
    median_listing_return_pct: float = 0.0
    max_gain_pct: float = 0.0
    max_loss_pct: float = 0.0
    std_return_pct: float = 0.0

    # Allotment-weighted metrics
    mean_expected_pnl_per_app: Optional[float] = None

    # Vs benchmark
    benchmark_hit_rate: Optional[float] = None    # Apply-Every-IPO hit rate

    # Yearly breakdown: {year: {metric: value}}
    yearly: dict[int, dict] = field(default_factory=dict)

    # Capital scenarios
    capital_scenarios: list[CapitalScenario] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

def run_backtest(
    strategy_fn: StrategyFn,
    strategy_name: str,
    outcomes: list[ListingOutcome],
    features_by_id: dict[str, dict],           # pre-computed feature snapshots as plain dicts
    ipos_by_id: Optional[dict] = None,         # ipo_id → IPO domain object
    subscriptions_by_id: Optional[dict] = None,
    dataset_description: str = "",
    benchmark_hit_rate: Optional[float] = None,
) -> BacktestReport:
    """
    Run a strategy over a dataset of ListingOutcomes.

    Parameters
    ----------
    strategy_fn :
        Callable(ipo_id, feature_dict) → Decision
    outcomes :
        Historical listing outcomes to evaluate on.
    features_by_id :
        Pre-computed features for each ipo_id. Must be point-in-time safe
        (only features available at decision time). Passed as plain dicts.
    ipos_by_id :
        Optional IPO domain objects for lot size / issue price.
    subscriptions_by_id :
        Optional SubscriptionSnapshots for allotment calculation.
    """
    report = BacktestReport(
        strategy_name=strategy_name,
        dataset_description=dataset_description,
        benchmark_hit_rate=benchmark_hit_rate,
    )

    applied_returns: list[float] = []
    expected_pnls: list[float] = []
    results: list[BacktestIPOResult] = []

    for outcome in outcomes:
        if not outcome.listing_price_quality.is_usable_for_research():
            continue

        ipo_id = outcome.ipo_id
        ipo = ipos_by_id.get(ipo_id) if ipos_by_id else None
        sub = subscriptions_by_id.get(ipo_id) if subscriptions_by_id else None
        features = features_by_id.get(ipo_id, {})

        year = ipo.year if ipo else outcome.listing_date.year
        lot_size: Optional[int] = ipo.issue_terms.lot_size if ipo else None
        retail_x: Optional[Decimal] = sub.retail_subscription_x if sub else None

        # Run the strategy
        decision = strategy_fn(ipo_id, features)

        # Allotment computation
        allotment_prob: Optional[float] = None
        expected_pnl: Optional[Decimal] = None
        capital_required: Optional[Decimal] = None

        if retail_x is not None and lot_size is not None:
            est = retail_allotment_probability(retail_x)
            allotment_prob = float(est.probability)
            expected_pnl = expected_gross_pnl_per_application(
                retail_subscription_x=retail_x,
                issue_price=outcome.issue_price,
                lot_size=lot_size,
                listing_return=outcome.listing_return,
            )

        if lot_size is not None and outcome.issue_price > 0:
            capital_required = outcome.issue_price * lot_size

        result = BacktestIPOResult(
            ipo_id=ipo_id,
            year=year,
            company_name=ipo.company_name if ipo else ipo_id,
            decision=decision,
            listing_return=outcome.listing_return,
            listing_price_quality=outcome.listing_price_quality,
            positive_listing=outcome.positive_listing,
            retail_subscription_x=retail_x,
            allotment_probability=allotment_prob,
            lot_size=lot_size,
            issue_price=outcome.issue_price,
            expected_pnl_per_application=expected_pnl,
            capital_required=capital_required,
        )
        results.append(result)

        if decision.is_apply() and outcome.listing_return is not None:
            applied_returns.append(float(outcome.listing_return) * 100)
            if expected_pnl is not None:
                expected_pnls.append(float(expected_pnl))

    report.results = results
    report.n_total_ipos = len(results)
    report.n_applied = sum(1 for r in results if r.applied())
    report.n_skipped = report.n_total_ipos - report.n_applied

    applied_with_outcome = [r for r in results if r.applied() and r.listing_return is not None]
    report.n_positive = sum(1 for r in applied_with_outcome if r.positive_listing)
    report.n_negative = len(applied_with_outcome) - report.n_positive

    if applied_returns:
        report.hit_rate = report.n_positive / len(applied_with_outcome)
        report.mean_listing_return_pct = statistics.mean(applied_returns)
        report.median_listing_return_pct = statistics.median(applied_returns)
        report.max_gain_pct = max(applied_returns)
        report.max_loss_pct = min(applied_returns)
        report.std_return_pct = statistics.stdev(applied_returns) if len(applied_returns) > 1 else 0.0

    if expected_pnls:
        report.mean_expected_pnl_per_app = statistics.mean(expected_pnls)

    # Yearly breakdown
    years_seen: set[int] = {r.year for r in results if r.applied()}
    for y in sorted(years_seen):
        yr = [r for r in results if r.year == y and r.applied() and r.listing_return is not None]
        if not yr:
            continue
        rets = [float(r.listing_return) * 100 for r in yr]
        report.yearly[y] = {
            "n": len(yr),
            "positive": sum(1 for r in yr if r.positive_listing),
            "mean_return": round(statistics.mean(rets), 2),
            "median_return": round(statistics.median(rets), 2),
            "max_gain": round(max(rets), 2),
            "max_loss": round(min(rets), 2),
        }

    return report


def print_backtest_report(report: BacktestReport) -> None:
    """Print a concise backtest summary to stdout."""
    print(f"\n{'='*60}")
    print(f"BACKTEST: {report.strategy_name}")
    print(f"Dataset: {report.dataset_description}")
    print(f"{'='*60}")
    print(f"  Total IPOs:          {report.n_total_ipos}")
    print(f"  Applied:             {report.n_applied}")
    print(f"  Skipped:             {report.n_skipped}")
    print(f"  Hit rate (applied):  {report.hit_rate:.1%}")
    print(f"  Mean return:         {report.mean_listing_return_pct:+.1f}%")
    print(f"  Median return:       {report.median_listing_return_pct:+.1f}%")
    print(f"  Max gain:            {report.max_gain_pct:+.1f}%")
    print(f"  Max loss:            {report.max_loss_pct:+.1f}%")
    if report.benchmark_hit_rate:
        delta = report.hit_rate - report.benchmark_hit_rate
        print(f"  vs benchmark:        {delta:+.1%}")
    if report.yearly:
        print(f"\n  Yearly breakdown:")
        for y, stats in sorted(report.yearly.items()):
            print(f"    {y}: n={stats['n']:3d} | +{stats['positive']} | "
                  f"mean={stats['mean_return']:+.1f}% | "
                  f"max={stats['max_gain']:+.1f}% | "
                  f"min={stats['max_loss']:+.1f}%")
    print("=" * 60)
