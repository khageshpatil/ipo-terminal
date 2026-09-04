"""
Rule-based V1 strategy — Phase 4A.

A transparent, interpretable strategy based on three signal groups:
  1. Demand signal   — subscription multiples (QIB, NII, Retail, Total)
  2. Market regime   — Nifty 20D return, India VIX level
  3. Issue structure — issue size, OFS ratio

Thresholds are NOT optimised. They are reasonable starting priors.
All estimates are RULE_ESTIMATE, not MODEL_PREDICTION.

The engine is designed so that swapping this strategy function for
an ML model requires zero changes to the backtest engine or decision engine.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from ipo_analyzer.backtest.engine import Decision, Recommendation


@dataclass
class RuleConfig:
    """
    Configurable thresholds for the rule-based strategy.
    All values are intentionally conservative defaults.
    Tune after seeing the actual base-rate data.
    """

    # Subscription thresholds (multiples)
    qib_min: float = 1.0          # QIB subscription minimum to qualify
    nii_min: float = 5.0          # NII (HNI) minimum
    retail_min: float = 1.0       # Retail minimum
    total_min: float = 10.0       # Total subscription minimum for APPLY

    total_strong: float = 50.0    # Above this → confident APPLY signal
    total_weak: float = 10.0      # Below this → SKIP regardless

    # Market regime
    nifty_20d_min: float = -0.05  # Max tolerated 20D market decline (−5%)
    vix_max: float = 25.0         # Max India VIX for APPLY recommendation
    vix_extreme: float = 35.0     # Above this → SKIP regardless

    # Issue structure
    ofs_ratio_max: float = 0.80   # Max fraction that is OFS (promoters cashing out)
    issue_size_max_cr: float = 5000.0  # Very large issues dilute retail return

    # P(positive listing) estimates by signal strength
    # These are RULE_ESTIMATE priors calibrated loosely on historical data
    # Will be replaced by trained model estimates in later phases
    p_pos_strong: float = 0.78    # Strong demand + good market
    p_pos_moderate: float = 0.62  # Moderate demand
    p_pos_weak: float = 0.45      # Weak demand (below thresholds)
    p_pos_base: float = 0.60      # Base rate estimate (no data)

    # Expected return estimates (%)
    er_strong: float = 15.0
    er_moderate: float = 7.0
    er_base: float = 0.0


_DEFAULT_CONFIG = RuleConfig()


def _score_subscription(features: dict, cfg: RuleConfig) -> tuple[str, list[str]]:
    """
    Return ('STRONG'|'MODERATE'|'WEAK'|'UNKNOWN', reason_lines).
    """
    qib = features.get("subscription_qib_x")
    nii = features.get("subscription_nii_x")
    retail = features.get("subscription_retail_x")
    total = features.get("subscription_total_x")

    if total is None:
        return "UNKNOWN", ["QIB/NII/Retail subscription: data not available at decision time"]

    reasons = []
    reasons.append(f"Total subscription: {total:.1f}x")
    if qib is not None:
        reasons.append(f"QIB: {qib:.1f}x")
    if nii is not None:
        reasons.append(f"NII: {nii:.1f}x")
    if retail is not None:
        reasons.append(f"Retail: {retail:.1f}x")

    if total < cfg.total_weak:
        return "WEAK", reasons
    if total >= cfg.total_strong and (qib is None or qib >= cfg.qib_min):
        return "STRONG", reasons
    if total >= cfg.total_min and (qib is None or qib >= cfg.qib_min):
        return "MODERATE", reasons
    return "WEAK", reasons


def _score_market(features: dict, cfg: RuleConfig) -> tuple[str, list[str]]:
    """Return ('POSITIVE'|'NEUTRAL'|'NEGATIVE', reason_lines)."""
    regime = features.get("market_regime")
    vix = features.get("market_india_vix_close")
    ret_20d = features.get("market_nifty_return_20d")

    reasons = []
    if regime:
        reasons.append(f"Market regime: {regime}")
    if vix is not None:
        reasons.append(f"India VIX: {vix:.1f}")
    if ret_20d is not None:
        reasons.append(f"Nifty 20D return: {ret_20d:+.1%}")

    negative = False
    if vix is not None and vix > cfg.vix_extreme:
        reasons.append(f"[!] VIX > {cfg.vix_extreme} — extreme fear")
        return "NEGATIVE", reasons
    if ret_20d is not None and ret_20d < cfg.nifty_20d_min:
        reasons.append(f"[!] Nifty 20D return below {cfg.nifty_20d_min:.0%}")
        negative = True
    if vix is not None and vix > cfg.vix_max:
        reasons.append(f"[!] VIX elevated (>{cfg.vix_max})")
        negative = True

    if regime == "BULL" and not negative:
        return "POSITIVE", reasons
    if regime == "BEAR" or negative:
        return "NEGATIVE", reasons
    return "NEUTRAL", reasons


def _score_structure(features: dict, cfg: RuleConfig) -> tuple[str, list[str]]:
    """Return ('OK'|'CAUTION'|'SKIP', reason_lines)."""
    ofs_pct = features.get("ofs_pct")          # fraction of total that is OFS (0–1)
    issue_size = features.get("issue_size_cr")

    reasons = []
    caution = False

    if ofs_pct is not None:
        reasons.append(f"OFS ratio: {ofs_pct:.0%}")
        if ofs_pct > cfg.ofs_ratio_max:
            reasons.append(f"[!] High OFS — promoters selling >{cfg.ofs_ratio_max:.0%} of issue")
            caution = True

    if issue_size is not None:
        reasons.append(f"Issue size: {issue_size:.0f} Cr")
        if issue_size > cfg.issue_size_max_cr:
            reasons.append(f"[!] Large issue size (>{cfg.issue_size_max_cr:.0f} Cr) — dilution risk")
            caution = True

    if caution:
        return "CAUTION", reasons
    if not reasons:
        return "UNKNOWN", ["Issue structure: no data available"]
    return "OK", reasons


def rule_based_strategy(
    ipo_id: str,
    features: dict,
    config: Optional[RuleConfig] = None,
) -> Decision:
    """
    V1 rule-based strategy.

    Feature keys expected (all optional — gracefully degrades):
      subscription_qib_x, subscription_nii_x, subscription_retail_x, subscription_total_x
      market_regime, market_india_vix_close, market_nifty_return_20d
      ofs_pct, issue_size_cr

    Returns a Decision with RULE_ESTIMATE confidence.
    """
    cfg = config or _DEFAULT_CONFIG

    sub_score, sub_reasons = _score_subscription(features, cfg)
    mkt_score, mkt_reasons = _score_market(features, cfg)
    str_score, str_reasons = _score_structure(features, cfg)

    all_reasons: list[str] = sub_reasons + mkt_reasons + str_reasons

    # Decision logic
    if sub_score == "WEAK":
        rec = Recommendation.SKIP
        p_pos = cfg.p_pos_weak
        er = cfg.er_base
        all_reasons.append("=> Low subscription — SKIP")

    elif sub_score == "UNKNOWN":
        # No subscription data — watch only, cannot commit
        rec = Recommendation.WATCH
        p_pos = cfg.p_pos_base
        er = cfg.er_base
        all_reasons.append("=> No subscription data — WATCH")

    elif sub_score == "STRONG" and mkt_score != "NEGATIVE" and str_score != "SKIP":
        rec = Recommendation.APPLY
        p_pos = cfg.p_pos_strong if mkt_score == "POSITIVE" else cfg.p_pos_moderate
        er = cfg.er_strong if mkt_score == "POSITIVE" else cfg.er_moderate
        all_reasons.append("=> Strong demand, acceptable market — APPLY")

    elif sub_score == "MODERATE" and mkt_score == "POSITIVE" and str_score == "OK":
        rec = Recommendation.APPLY
        p_pos = cfg.p_pos_moderate
        er = cfg.er_moderate
        all_reasons.append("=> Moderate demand + positive market — APPLY")

    elif mkt_score == "NEGATIVE":
        rec = Recommendation.SKIP
        p_pos = cfg.p_pos_weak
        er = cfg.er_base
        all_reasons.append("=> Unfavourable market conditions — SKIP")

    else:
        # Moderate demand + neutral market or structure caution
        rec = Recommendation.WATCH
        p_pos = cfg.p_pos_moderate * 0.9
        er = cfg.er_moderate * 0.5
        all_reasons.append("=> Mixed signals — WATCH")

    return Decision(
        ipo_id=ipo_id,
        recommendation=rec,
        p_positive=p_pos,
        expected_return_pct=er,
        confidence="RULE_ESTIMATE",
        reason_lines=all_reasons,
    )


def make_rule_strategy(config: Optional[RuleConfig] = None):
    """
    Return a strategy callable compatible with the backtest engine.

    Usage:
        strategy = make_rule_strategy(RuleConfig(total_min=20.0))
        report = run_backtest(strategy, "RuleV1-T20", outcomes, features)
    """
    cfg = config or _DEFAULT_CONFIG

    def _strategy(ipo_id: str, features: dict) -> Decision:
        return rule_based_strategy(ipo_id, features, cfg)

    _strategy.__name__ = "rule_based_v1"
    return _strategy
