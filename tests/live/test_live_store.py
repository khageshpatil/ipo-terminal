"""
Tests for the live observation store.
Uses a temporary directory — does not touch real data/live/.
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from ipo_analyzer.live.models import LiveIPO, LiveObservation
from ipo_analyzer.live.store import (
    _ipo_to_dict,
    _dict_to_ipo,
    _obs_to_dict,
    _dict_to_obs,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def make_ipo(**kwargs) -> LiveIPO:
    defaults = dict(
        ipo_id="TESTCO-2025",
        company_name="Test Company Ltd",
        nse_symbol="TESTCO",
        status="OPEN",
        open_date="2025-09-01",
        close_date="2025-09-03",
        issue_price=150.0,
        price_band_low=140.0,
        price_band_high=150.0,
        lot_size=100,
        issue_size_cr=500.0,
        subscription_qib_x=12.5,
        subscription_nii_x=8.3,
        subscription_retail_x=4.1,
        subscription_total_x=7.8,
        subscription_is_final=False,
        gmp_inr=25.0,
        gmp_pct=16.7,
        gmp_source="CHITTORGARH_GMP",
        source="CHITTORGARH_LIVE",
        source_url="https://www.chittorgarh.com/test",
        observed_at="2025-09-02T10:30:00+00:00",
        retrieved_at="2025-09-02T10:31:00+00:00",
    )
    defaults.update(kwargs)
    return LiveIPO(**defaults)


# ---------------------------------------------------------------------------
# Serialisation round-trips
# ---------------------------------------------------------------------------

def test_ipo_roundtrip():
    """LiveIPO → dict → LiveIPO preserves all fields."""
    ipo = make_ipo()
    restored = _dict_to_ipo(_ipo_to_dict(ipo))
    assert restored.ipo_id == ipo.ipo_id
    assert restored.company_name == ipo.company_name
    assert restored.subscription_qib_x == ipo.subscription_qib_x
    assert restored.gmp_inr == ipo.gmp_inr
    assert restored.status == ipo.status


def test_ipo_roundtrip_none_fields():
    """None fields round-trip correctly (no fabrication)."""
    ipo = make_ipo(
        subscription_qib_x=None,
        subscription_nii_x=None,
        gmp_inr=None,
        nse_symbol=None,
    )
    restored = _dict_to_ipo(_ipo_to_dict(ipo))
    assert restored.subscription_qib_x is None
    assert restored.gmp_inr is None
    assert restored.nse_symbol is None


def test_obs_roundtrip():
    """LiveObservation → dict → LiveObservation preserves all fields."""
    obs = LiveObservation(
        ipo_id="TESTCO-2025",
        field_name="subscription_total_x",
        value=7.8,
        observed_at="2025-09-02T10:30:00+00:00",
        retrieved_at="2025-09-02T10:31:00+00:00",
        source="CHITTORGARH_LIVE",
        source_url="https://test.com",
        is_final=False,
    )
    restored = _dict_to_obs(_obs_to_dict(obs))
    assert restored.ipo_id == obs.ipo_id
    assert restored.field_name == obs.field_name
    assert restored.value == obs.value
    assert restored.is_final is False


def test_obs_roundtrip_none_value():
    """Observation with None value (missing, not fabricated)."""
    obs = LiveObservation(
        ipo_id="TESTCO-2025",
        field_name="gmp_inr",
        value=None,
        observed_at="2025-09-02T10:30:00+00:00",
        retrieved_at="2025-09-02T10:31:00+00:00",
        source="CHITTORGARH_LIVE",
    )
    restored = _dict_to_obs(_obs_to_dict(obs))
    assert restored.value is None


# ---------------------------------------------------------------------------
# Store write / read (patched to temp dir)
# ---------------------------------------------------------------------------

@pytest.fixture()
def tmp_store(tmp_path, monkeypatch):
    """Redirect the store's _BASE path to a tmp directory."""
    monkeypatch.setattr("ipo_analyzer.live.store._BASE", tmp_path / "live")
    return tmp_path / "live"


def test_save_and_load_ipo(tmp_store):
    from ipo_analyzer.live.store import save_live_ipo, load_live_ipo
    ipo = make_ipo()
    save_live_ipo(ipo)

    loaded = load_live_ipo("TESTCO-2025")
    assert loaded is not None
    assert loaded.ipo_id == "TESTCO-2025"
    assert loaded.company_name == "Test Company Ltd"
    assert loaded.subscription_total_x == pytest.approx(7.8)


def test_save_creates_observations_jsonl(tmp_store):
    from ipo_analyzer.live.store import save_live_ipo
    ipo = make_ipo()
    save_live_ipo(ipo)

    obs_path = tmp_store / "ipos" / "TESTCO-2025" / "observations.jsonl"
    assert obs_path.exists()
    lines = obs_path.read_text().strip().splitlines()
    # Should have 6 entries (one per _LIVE_FIELDS)
    assert len(lines) == 6
    first = json.loads(lines[0])
    assert first["ipo_id"] == "TESTCO-2025"
    assert "field_name" in first
    assert "value" in first
    assert "observed_at" in first


def test_multiple_saves_append_observations(tmp_store):
    from ipo_analyzer.live.store import save_live_ipo, load_observations
    ipo1 = make_ipo(subscription_total_x=5.0, observed_at="2025-09-02T09:30:00+00:00")
    ipo2 = make_ipo(subscription_total_x=9.2, observed_at="2025-09-02T10:30:00+00:00")

    save_live_ipo(ipo1)
    save_live_ipo(ipo2)

    obs = load_observations("TESTCO-2025")
    total_obs = [o for o in obs if o.field_name == "subscription_total_x"]
    assert len(total_obs) == 2
    assert total_obs[0].value == pytest.approx(5.0)
    assert total_obs[1].value == pytest.approx(9.2)


def test_load_missing_returns_none(tmp_store):
    from ipo_analyzer.live.store import load_live_ipo
    assert load_live_ipo("NONEXISTENT-9999") is None


def test_load_all_live_ipos(tmp_store):
    from ipo_analyzer.live.store import save_live_ipo, load_all_live_ipos
    ipo_a = make_ipo(ipo_id="ALPHA-2025", company_name="Alpha Ltd")
    ipo_b = make_ipo(ipo_id="BETA-2025",  company_name="Beta Ltd")
    save_live_ipo(ipo_a)
    save_live_ipo(ipo_b)

    all_ipos = load_all_live_ipos()
    ids = {i.ipo_id for i in all_ipos}
    assert "ALPHA-2025" in ids
    assert "BETA-2025" in ids


def test_index_updated_on_save(tmp_store):
    from ipo_analyzer.live.store import save_live_ipo
    ipo = make_ipo()
    save_live_ipo(ipo)

    index_path = tmp_store / "index.json"
    assert index_path.exists()
    index = json.loads(index_path.read_text())
    assert "TESTCO-2025" in index
    assert index["TESTCO-2025"]["status"] == "OPEN"


def test_get_latest_subscription(tmp_store):
    from ipo_analyzer.live.store import save_live_ipo, get_latest_subscription
    ipo1 = make_ipo(
        subscription_qib_x=5.0, subscription_total_x=4.0,
        observed_at="2025-09-02T09:00:00+00:00"
    )
    ipo2 = make_ipo(
        subscription_qib_x=12.5, subscription_total_x=9.2,
        observed_at="2025-09-02T11:00:00+00:00"
    )
    save_live_ipo(ipo1)
    save_live_ipo(ipo2)

    latest = get_latest_subscription("TESTCO-2025")
    # Should return latest values
    assert latest["qib"] == pytest.approx(12.5)
    assert latest["total"] == pytest.approx(9.2)
