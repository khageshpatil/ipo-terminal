"""
Capital allocation — Phase 7.

Given available capital and a list of IPOAnalysis objects, recommend
how many applications to make and to which IPOs.

Rules:
  - Minimum application = 1 lot × issue_price
  - Maximum applications per IPO is unconstrained (user can apply multiple lots)
  - Capital is allocated in order of expected_profit_per_application (descending)
  - Never recommend applying to SKIP-rated IPOs
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Optional

from ipo_analyzer.backtest.decision_engine import IPOAnalysis


@dataclass
class AllocationLine:
    ipo_id: str
    company_name: str
    recommendation: str
    issue_price: Optional[Decimal]
    lot_size: Optional[int]
    lots_to_apply: int
    capital_required: Decimal
    expected_profit: Optional[Decimal]
    allotment_probability: Optional[float]
    expected_return_pct: Optional[float]


@dataclass
class AllocationPlan:
    available_capital: Decimal
    total_capital_deployed: Decimal
    remaining_capital: Decimal
    lines: list[AllocationLine] = field(default_factory=list)
    skipped_ipos: list[str] = field(default_factory=list)

    def summary_text(self) -> str:
        lines = [
            f"\nCapital Plan  (Available: Rs {float(self.available_capital):,.0f})",
            f"{'='*70}",
            f"{'IPO':<35} {'Lots':>5} {'Capital':>12} {'E[Profit]':>12} {'P(Allot)':>9}",
            f"{'-'*70}",
        ]
        for ln in self.lines:
            profit_str = f"Rs {float(ln.expected_profit):,.0f}" if ln.expected_profit else "—"
            allot_str = f"{ln.allotment_probability:.0%}" if ln.allotment_probability else "—"
            lines.append(
                f"{ln.company_name[:34]:<35} {ln.lots_to_apply:>5} "
                f"Rs {float(ln.capital_required):>10,.0f} {profit_str:>12} {allot_str:>9}"
            )
        lines += [
            f"{'='*70}",
            f"  Total deployed:  Rs {float(self.total_capital_deployed):,.0f}",
            f"  Remaining:       Rs {float(self.remaining_capital):,.0f}",
            f"  IPOs applied to: {len(self.lines)}",
        ]
        return "\n".join(lines)


def allocate_capital(
    available_capital: int | Decimal,
    analyses: list[IPOAnalysis],
    ipos_by_id: Optional[dict] = None,    # ipo_id → UniverseIPO (for lot_size/price)
    max_lots_per_ipo: int = 1,            # default: 1 lot per IPO (minimize capital)
    skip_watch: bool = False,             # if True, only allocate to APPLY-rated IPOs
) -> AllocationPlan:
    """
    Produce a capital allocation plan from a list of IPOAnalysis objects.

    The allocation is greedy: sort by expected_profit_per_application descending,
    apply as many lots as fit within capital constraints.
    """
    capital = Decimal(str(available_capital))

    # Filter to investable IPOs
    investable = [
        a for a in analyses
        if a.recommendation == "APPLY" or (not skip_watch and a.recommendation == "WATCH")
    ]

    # Sort by expected profit descending (None → treated as 0)
    def _sort_key(a: IPOAnalysis) -> float:
        if a.expected_profit_per_application is not None:
            return float(a.expected_profit_per_application)
        if a.expected_return_pct is not None:
            return a.expected_return_pct
        return 0.0

    investable.sort(key=_sort_key, reverse=True)

    plan = AllocationPlan(
        available_capital=capital,
        total_capital_deployed=Decimal(0),
        remaining_capital=capital,
    )

    remaining = capital

    # SEBI retail minimum application ≈ ₹14,000 — used as fallback when lot_size unknown
    SEBI_MIN_APP = Decimal("14000")

    for analysis in investable:
        cap_per_lot = analysis.capital_required_per_lot
        if cap_per_lot is None or cap_per_lot <= 0:
            # Fallback: use SEBI minimum application as proxy for 1 lot
            # This allows the capital planner to work with historical data that lacks lot_size
            cap_per_lot = SEBI_MIN_APP

        max_affordable_lots = int(remaining // cap_per_lot)
        if max_affordable_lots == 0:
            plan.skipped_ipos.append(f"{analysis.ipo_id}: insufficient capital")
            continue

        lots = min(max_affordable_lots, max_lots_per_ipo)
        cost = cap_per_lot * lots
        profit = (
            analysis.expected_profit_per_application * lots
            if analysis.expected_profit_per_application is not None
            else None
        )

        plan.lines.append(AllocationLine(
            ipo_id=analysis.ipo_id,
            company_name=analysis.company_name,
            recommendation=analysis.recommendation,
            issue_price=None,   # not stored on analysis; caller can fill
            lot_size=None,
            lots_to_apply=lots,
            capital_required=cost,
            expected_profit=profit,
            allotment_probability=analysis.p_allotment,
            expected_return_pct=analysis.expected_return_pct,
        ))
        remaining -= cost

    plan.total_capital_deployed = capital - remaining
    plan.remaining_capital = remaining
    return plan
