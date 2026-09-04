"""
Decision engine — Phase 6.

Takes pre-computed features for one IPO and returns a structured decision
with probability estimates, expected economics, and a human-readable "WHY?" section.

Architecture principle:
  - Accepts a StrategyFn (or model callable) as a constructor argument
  - The Decision object is the same regardless of whether a rule or ML model produced it
  - Confidence field distinguishes RULE_ESTIMATE from MODEL_PREDICTION
  - Capital allocation is separate (Phase 7)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Optional

from ipo_analyzer.backtest.engine import Decision, Recommendation
from ipo_analyzer.backtest.engine import StrategyFn


@dataclass
class IPOAnalysis:
    """
    Full analysis output for a single IPO — what the UI and API expose.
    """
    ipo_id: str
    company_name: str

    # Core decision
    recommendation: str         # APPLY / SKIP / WATCH
    confidence: str             # RULE_ESTIMATE | MODEL_PREDICTION

    # Probability estimates
    p_positive: Optional[float]       # P(listing_open > issue_price)
    expected_return_pct: Optional[float]

    # Allotment-adjusted economics
    p_allotment: Optional[float]      # P(retail allotment)
    expected_profit_per_application: Optional[Decimal]   # E[P&L] per application in INR
    capital_required_per_lot: Optional[Decimal]
    lots_required: int = 1            # minimum = 1

    # Risk
    downside_pct: Optional[float] = None    # estimated loss if listing is negative

    # Feature snapshot used (point-in-time safe)
    features_snapshot: dict = field(default_factory=dict)

    # WHY explanation
    reason_lines: list[str] = field(default_factory=list)

    # Data freshness
    subscription_as_of: Optional[str] = None
    market_as_of: Optional[str] = None

    def why_text(self) -> str:
        """Human-readable explanation for the UI."""
        icon = {"APPLY": "[GO]", "SKIP": "[NO]", "WATCH": "[??]"}.get(self.recommendation, "[ ]")
        lines = [f"{icon} {self.recommendation}", ""]
        lines.append("Why?")
        lines.extend(f"  {r}" for r in self.reason_lines)
        lines.append("")
        if self.p_positive is not None:
            lines.append(f"  P(positive listing):     {self.p_positive:.0%}  [{self.confidence}]")
        if self.expected_return_pct is not None:
            lines.append(f"  Expected return:         {self.expected_return_pct:+.1f}%  [{self.confidence}]")
        if self.p_allotment is not None:
            lines.append(f"  Allotment probability:   {self.p_allotment:.0%}")
        if self.expected_profit_per_application is not None:
            lines.append(f"  Expected profit/app:     Rs {float(self.expected_profit_per_application):,.0f}")
        return "\n".join(lines)


class DecisionEngine:
    """
    Wraps any strategy function and produces IPOAnalysis objects.

    The strategy_fn is the only thing that changes between rule-based and ML phases.
    Everything else (allotment, capital, formatting) stays the same.
    """

    def __init__(
        self,
        strategy_fn: StrategyFn,
        allotment_model=None,    # optional: callable(retail_x) → AllotmentEstimate
    ):
        self.strategy_fn = strategy_fn
        self.allotment_model = allotment_model

    def analyse(
        self,
        ipo_id: str,
        company_name: str,
        features: dict,
        issue_price: Optional[Decimal] = None,
        lot_size: Optional[int] = None,
        retail_subscription_x: Optional[Decimal] = None,
    ) -> IPOAnalysis:
        """
        Run the strategy and produce an IPOAnalysis.

        Parameters
        ----------
        ipo_id : str
        company_name : str
        features : dict
            Point-in-time safe feature snapshot.
        issue_price : Decimal, optional
            Required for capital and P&L calculation.
        lot_size : int, optional
            Required for capital and P&L calculation.
        retail_subscription_x : Decimal, optional
            For allotment probability calculation.
        """
        decision: Decision = self.strategy_fn(ipo_id, features)

        # Allotment calculation
        p_allotment: Optional[float] = None
        expected_profit: Optional[Decimal] = None
        capital_per_lot: Optional[Decimal] = None

        if retail_subscription_x is not None:
            try:
                from ipo_analyzer.allotment.retail_formula import (
                    expected_gross_pnl_per_application,
                    retail_allotment_probability,
                )
                est = retail_allotment_probability(retail_subscription_x)
                p_allotment = float(est.probability)

                if issue_price is not None and lot_size is not None:
                    # Use expected_return as listing_return estimate
                    er = decision.expected_return_pct or 0.0
                    listing_return_est = Decimal(str(er / 100))
                    expected_profit = expected_gross_pnl_per_application(
                        retail_subscription_x=retail_subscription_x,
                        issue_price=issue_price,
                        lot_size=lot_size,
                        listing_return=listing_return_est,
                    )
            except Exception:
                pass

        if issue_price is not None and lot_size is not None:
            capital_per_lot = issue_price * lot_size

        return IPOAnalysis(
            ipo_id=ipo_id,
            company_name=company_name,
            recommendation=decision.recommendation,
            confidence=decision.confidence,
            p_positive=decision.p_positive,
            expected_return_pct=decision.expected_return_pct,
            p_allotment=p_allotment,
            expected_profit_per_application=expected_profit,
            capital_required_per_lot=capital_per_lot,
            features_snapshot=features,
            reason_lines=decision.reason_lines,
        )

    def analyse_batch(
        self,
        ipos: list[dict],  # list of dicts with keys: ipo_id, company_name, features, ...
    ) -> list[IPOAnalysis]:
        results = []
        for ipo in ipos:
            analysis = self.analyse(
                ipo_id=ipo["ipo_id"],
                company_name=ipo.get("company_name", ipo["ipo_id"]),
                features=ipo.get("features", {}),
                issue_price=ipo.get("issue_price"),
                lot_size=ipo.get("lot_size"),
                retail_subscription_x=ipo.get("retail_subscription_x"),
            )
            results.append(analysis)
        return results
