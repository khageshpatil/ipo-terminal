"""Tests for the rule-based strategy."""
from __future__ import annotations

import pytest

from ipo_analyzer.backtest.engine import Recommendation
from ipo_analyzer.strategy.rule_based import RuleConfig, rule_based_strategy


_STRONG_FEATURES = {
    "subscription_qib_x": 50.0,
    "subscription_nii_x": 200.0,
    "subscription_retail_x": 10.0,
    "subscription_total_x": 80.0,
    "market_regime": "BULL",
    "market_india_vix_close": 13.5,
    "market_nifty_return_20d": 0.05,
    "ofs_pct": 0.20,
    "issue_size_cr": 500.0,
}

_WEAK_FEATURES = {
    "subscription_total_x": 3.0,
    "market_regime": "NEUTRAL",
    "market_india_vix_close": 18.0,
}

_BEAR_FEATURES = {
    "subscription_total_x": 40.0,
    "market_regime": "BEAR",
    "market_india_vix_close": 28.0,
    "market_nifty_return_20d": -0.07,
}

_NO_DATA_FEATURES: dict = {}


class TestRuleStrategy:
    def test_strong_demand_bull_market_is_apply(self) -> None:
        d = rule_based_strategy("IPO1", _STRONG_FEATURES)
        assert d.recommendation == Recommendation.APPLY
        assert d.confidence == "RULE_ESTIMATE"
        assert d.p_positive is not None
        assert d.p_positive > 0.5

    def test_weak_demand_is_skip(self) -> None:
        d = rule_based_strategy("IPO2", _WEAK_FEATURES)
        assert d.recommendation == Recommendation.SKIP

    def test_bear_market_is_skip(self) -> None:
        d = rule_based_strategy("IPO3", _BEAR_FEATURES)
        assert d.recommendation == Recommendation.SKIP

    def test_no_data_is_watch(self) -> None:
        d = rule_based_strategy("IPO4", _NO_DATA_FEATURES)
        assert d.recommendation == Recommendation.WATCH

    def test_reason_lines_populated(self) -> None:
        d = rule_based_strategy("IPO1", _STRONG_FEATURES)
        assert len(d.reason_lines) > 0
        assert any("subscription" in r.lower() or "Total" in r for r in d.reason_lines)

    def test_extreme_vix_is_skip(self) -> None:
        features = {**_STRONG_FEATURES, "market_india_vix_close": 40.0}
        d = rule_based_strategy("IPO5", features)
        assert d.recommendation == Recommendation.SKIP

    def test_configurable_threshold(self) -> None:
        # With total_weak=100, 80x total falls below the weak threshold → SKIP
        cfg = RuleConfig(total_weak=100.0, total_min=150.0, total_strong=200.0)
        d = rule_based_strategy("IPO6", _STRONG_FEATURES, config=cfg)
        # 80x < 100x total_weak → WEAK → SKIP
        assert d.recommendation == Recommendation.SKIP

    def test_make_rule_strategy_factory(self) -> None:
        from ipo_analyzer.strategy.rule_based import make_rule_strategy
        fn = make_rule_strategy()
        d = fn("IPO1", _STRONG_FEATURES)
        assert d.ipo_id == "IPO1"
        assert d.recommendation in (Recommendation.APPLY, Recommendation.SKIP, Recommendation.WATCH)
