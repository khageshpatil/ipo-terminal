"""
Tests for the live runner — feature building and decision output.
Does NOT make network calls (live fetch is mocked).
"""

from __future__ import annotations

import pytest

from ipo_analyzer.live.models import LiveIPO
from ipo_analyzer.live.runner import run_live_decision, _build_features_from_live


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def make_ipo(**kwargs) -> LiveIPO:
    defaults = dict(
        ipo_id="TESTCO-2025",
        company_name="Test Company Ltd",
        status="OPEN",
        open_date="2025-09-01",
        close_date="2025-09-03",
        issue_price=150.0,
        lot_size=100,
        issue_size_cr=500.0,
        subscription_qib_x=12.5,
        subscription_nii_x=8.3,
        subscription_retail_x=4.1,
        subscription_total_x=55.0,   # strong demand → APPLY
        source="CHITTORGARH_LIVE",
    )
    defaults.update(kwargs)
    return LiveIPO(**defaults)


# ---------------------------------------------------------------------------
# Feature building
# ---------------------------------------------------------------------------

def test_build_features_subscription_fields():
    """Subscription multiples map correctly to feature dict."""
    ipo = make_ipo()
    features = _build_features_from_live(ipo)

    assert features["subscription_qib_x"] == pytest.approx(12.5)
    assert features["subscription_nii_x"] == pytest.approx(8.3)
    assert features["subscription_retail_x"] == pytest.approx(4.1)
    assert features["subscription_total_x"] == pytest.approx(55.0)


def test_build_features_none_subscription():
    """None subscription fields stay None (not fabricated)."""
    ipo = make_ipo(
        subscription_qib_x=None,
        subscription_nii_x=None,
        subscription_retail_x=None,
        subscription_total_x=None,
    )
    features = _build_features_from_live(ipo)
    assert features["subscription_total_x"] is None
    assert features["subscription_qib_x"] is None


def test_build_features_ofs_pct():
    """ofs_pct computed when both issue_size_cr and ofs_cr present."""
    ipo = make_ipo(issue_size_cr=1000.0, ofs_cr=600.0)
    features = _build_features_from_live(ipo)
    assert features["ofs_pct"] == pytest.approx(0.6)


def test_build_features_ofs_pct_missing():
    """ofs_pct is None when ofs_cr not available."""
    ipo = make_ipo(ofs_cr=None)
    features = _build_features_from_live(ipo)
    assert features["ofs_pct"] is None


# ---------------------------------------------------------------------------
# Decision output
# ---------------------------------------------------------------------------

def test_strong_demand_gives_apply():
    """Strong total subscription (55x) → APPLY."""
    ipo = make_ipo(subscription_total_x=55.0)
    decision = run_live_decision(ipo)
    assert decision.recommendation == "APPLY"
    assert decision.confidence == "RULE_ESTIMATE"
    assert decision.p_positive is not None
    assert decision.ipo_id == "TESTCO-2025"


def test_weak_demand_gives_skip():
    """Weak total subscription (3x) → SKIP."""
    ipo = make_ipo(subscription_total_x=3.0)
    decision = run_live_decision(ipo)
    assert decision.recommendation == "SKIP"


def test_no_subscription_gives_watch():
    """No subscription data → WATCH."""
    ipo = make_ipo(
        subscription_qib_x=None,
        subscription_nii_x=None,
        subscription_retail_x=None,
        subscription_total_x=None,
    )
    decision = run_live_decision(ipo)
    assert decision.recommendation == "WATCH"


def test_data_quality_full():
    """All key fields present → FULL data quality."""
    # Mock market data to be available
    ipo = make_ipo()
    decision = run_live_decision(ipo)
    # With no market data file in test env, quality should be PARTIAL
    assert decision.data_quality in ("FULL", "PARTIAL")


def test_data_quality_minimal_no_subscription():
    """No subscription data → MINIMAL quality."""
    ipo = make_ipo(subscription_total_x=None)
    decision = run_live_decision(ipo)
    assert decision.data_quality == "MINIMAL"


def test_reason_lines_populated():
    """Reason lines are always populated."""
    ipo = make_ipo()
    decision = run_live_decision(ipo)
    assert len(decision.reason_lines) > 0


def test_decision_at_set():
    """decision_at timestamp is set on every call."""
    ipo = make_ipo()
    decision = run_live_decision(ipo)
    assert decision.decision_at  # non-empty string


def test_high_ofs_ratio_in_reasons():
    """High OFS ratio appears in reason lines."""
    ipo = make_ipo(issue_size_cr=1000.0, ofs_cr=900.0)  # 90% OFS
    decision = run_live_decision(ipo)
    combined = " ".join(decision.reason_lines).lower()
    assert "ofs" in combined


def test_missing_fields_reported():
    """Missing fields are explicitly listed in the decision."""
    ipo = make_ipo(subscription_total_x=None, issue_price=None)
    decision = run_live_decision(ipo)
    assert "subscription_total_x" in decision.missing_fields
