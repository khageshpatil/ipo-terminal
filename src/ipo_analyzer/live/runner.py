"""
Live IPO runner — Phase D.

Orchestrates:
  fetch → store observations → build features → run rule strategy → return LiveDecision

This is the main production loop. Call refresh_live_ipos() on a schedule.
Each call creates new timestamped observations without overwriting history.

Decision output is RULE_ESTIMATE — clearly labelled, not a model prediction.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from ipo_analyzer.live.models import LiveIPO
from ipo_analyzer.live.store import (
    load_all_live_ipos,
    save_live_ipo,
)
from ipo_analyzer.strategy.rule_based import rule_based_strategy

logger = logging.getLogger(__name__)


@dataclass
class LiveDecision:
    """
    Strategy output for a currently active IPO.
    RULE_ESTIMATE — not a model prediction.
    """
    ipo_id: str
    company_name: str
    recommendation: str          # APPLY / WATCH / SKIP
    confidence: str = "RULE_ESTIMATE"
    strategy_version: str = "RULE_V1"
    drivers: list[str] = field(default_factory=list)
    p_positive: Optional[float] = None
    expected_return_pct: Optional[float] = None
    reason_lines: list[str] = field(default_factory=list)

    # Signal breakdown
    sub_score: str = "UNKNOWN"   # STRONG / MODERATE / WEAK / UNKNOWN
    mkt_score: str = "UNKNOWN"   # POSITIVE / NEUTRAL / NEGATIVE / UNKNOWN
    str_score: str = "UNKNOWN"   # OK / CAUTION / SKIP / UNKNOWN

    # Data quality
    data_quality: str = "PARTIAL"    # FULL / PARTIAL / MINIMAL
    missing_fields: list[str] = field(default_factory=list)
    features_snapshot: dict = field(default_factory=dict)
    market_as_of: Optional[str] = None

    # Timestamps
    decision_at: str = ""


def _build_features_from_live(
    ipo: LiveIPO,
    decision_timestamp: Optional[datetime] = None,
) -> dict:
    """
    Build a feature dict from a LiveIPO for the rule strategy.
    Maps LiveIPO fields to the keys expected by rule_based_strategy().

    Subscription keys: subscription_qib_x, subscription_nii_x,
                       subscription_retail_x, subscription_total_x
    Market keys: market_regime, market_india_vix_close, market_nifty_return_20d
    Structure keys: ofs_pct, issue_size_cr
    """
    decision_timestamp = decision_timestamp or datetime.now(timezone.utc)
    features: dict = {}

    # A live snapshot is usable only if it was observed no later than the
    # decision. Missing timestamps remain missing; they are never fabricated.
    observation_is_available = True
    if ipo.observed_at:
        try:
            observed_at = datetime.fromisoformat(ipo.observed_at.replace("Z", "+00:00"))
            if observed_at.tzinfo is None:
                observation_is_available = False
            else:
                observation_is_available = observed_at <= decision_timestamp
        except ValueError:
            observation_is_available = False

    # Subscription signals
    features["subscription_qib_x"] = ipo.subscription_qib_x if observation_is_available else None
    features["subscription_nii_x"] = ipo.subscription_nii_x if observation_is_available else None
    features["subscription_retail_x"] = ipo.subscription_retail_x if observation_is_available else None
    features["subscription_total_x"] = ipo.subscription_total_x if observation_is_available else None

    # Issue structure
    features["issue_size_cr"] = ipo.issue_size_cr
    if ipo.issue_size_cr and ipo.ofs_cr:
        features["ofs_pct"] = round(ipo.ofs_cr / ipo.issue_size_cr, 4)
    else:
        features["ofs_pct"] = None

    # Market regime — load from latest market data file (best effort)
    try:
        import pandas as pd
        from pathlib import Path
        mkt_path = Path("data/market/market_features_daily.csv")
        if mkt_path.exists():
            mkt_df = pd.read_csv(mkt_path)
            mkt_df["Date"] = pd.to_datetime(mkt_df["Date"]).dt.date
            from ipo_analyzer.data_sources.market_data import get_market_snapshot_for_date
            # Use today's market snapshot
            today = decision_timestamp.date()
            snap = get_market_snapshot_for_date(mkt_df, today)
            if snap:
                features["market_regime"] = snap.market_regime
                features["market_india_vix_close"] = snap.india_vix_close
                features["market_nifty_return_20d"] = snap.nifty_return_20d
                features["market_nifty_return_5d"] = snap.nifty_return_5d
                features["market_as_of"] = str(today)
    except Exception as e:
        logger.debug("Market data unavailable for live features: %s", e)

    return features


def _assess_data_quality(ipo: LiveIPO, features: dict) -> tuple[str, list[str]]:
    """Return (quality_label, missing_field_names)."""
    missing = []

    if features.get("subscription_total_x") is None:
        missing.append("subscription_total_x")
    if features.get("subscription_qib_x") is None:
        missing.append("subscription_qib_x")
    if features.get("subscription_retail_x") is None:
        missing.append("subscription_retail_x")
    if ipo.issue_price is None:
        missing.append("issue_price")
    if ipo.lot_size is None:
        missing.append("lot_size")
    if features.get("market_regime") is None:
        missing.append("market_regime")

    if len(missing) == 0:
        quality = "FULL"
    elif features.get("subscription_total_x") is not None:
        quality = "PARTIAL"
    else:
        quality = "MINIMAL"

    return quality, missing


def run_live_decision(ipo: LiveIPO) -> LiveDecision:
    """
    Run the rule strategy against a single live IPO.
    Returns a LiveDecision — always labelled RULE_ESTIMATE.
    """
    decision_at = datetime.now(timezone.utc)
    now = decision_at.isoformat()
    features = _build_features_from_live(ipo, decision_at)
    quality, missing = _assess_data_quality(ipo, features)

    # Run rule strategy
    decision = rule_based_strategy(ipo_id=ipo.ipo_id, features=features)

    return LiveDecision(
        ipo_id=ipo.ipo_id,
        company_name=ipo.company_name,
        recommendation=decision.recommendation.value
            if hasattr(decision.recommendation, "value")
            else str(decision.recommendation),
        confidence="RULE_ESTIMATE",
        strategy_version=decision.strategy_version,
        drivers=decision.drivers,
        p_positive=decision.p_positive,
        expected_return_pct=decision.expected_return_pct,
        reason_lines=decision.reason_lines,
        data_quality=quality,
        missing_fields=missing,
        features_snapshot=features,
        market_as_of=features.get("market_as_of"),
        decision_at=now,
    )


def refresh_live_ipos() -> list[LiveDecision]:
    """
    Main production refresh loop.

    1. Fetch fresh data from Chittorgarh
    2. Save each IPO (appends new observations to JSONL)
    3. Run rule strategy on each
    4. Return decisions

    Call this on a schedule (every 30–60 minutes during market hours).
    """
    from ipo_analyzer.live.chittorgarh_live import fetch_live_ipos

    logger.info("=== Live IPO refresh starting ===")
    fresh_ipos = fetch_live_ipos()

    if not fresh_ipos:
        logger.warning("No live IPOs fetched — returning cached data")
        cached = load_all_live_ipos()
        return [run_live_decision(ipo) for ipo in cached]

    decisions = []
    for ipo in fresh_ipos:
        try:
            save_live_ipo(ipo)
            d = run_live_decision(ipo)
            decisions.append(d)
            logger.info(
                "  %-40s → %-5s  sub=%.1fx  quality=%s",
                ipo.company_name[:40],
                d.recommendation,
                ipo.subscription_total_x or 0.0,
                d.data_quality,
            )
        except Exception as e:
            logger.error("Failed to process %s: %s", ipo.company_name, e)

    logger.info("=== Refresh complete: %d IPOs processed ===", len(decisions))
    return decisions


def get_cached_decisions() -> list[LiveDecision]:
    """Return decisions from cached (last-fetched) live IPO data."""
    ipos = load_all_live_ipos()
    return [run_live_decision(ipo) for ipo in ipos]
