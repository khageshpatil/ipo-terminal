"""
Append-only timestamped observation store for live IPO data.

Storage layout (under data/live/):
  data/live/ipos/{ipo_id}/meta.json          — latest LiveIPO snapshot
  data/live/ipos/{ipo_id}/observations.jsonl — append-only observation log
  data/live/index.json                        — known ipo_ids + last_updated

Design:
- Every refresh appends to observations.jsonl, never overwrites
- meta.json is the latest full LiveIPO snapshot (overwritten each refresh)
- index.json maps ipo_id → {company_name, status, last_updated}
- All timestamps are UTC ISO strings
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from ipo_analyzer.live.models import LiveIPO, LiveObservation

logger = logging.getLogger(__name__)

_BASE = Path("data/live")


def _ipo_dir(ipo_id: str) -> Path:
    return _BASE / "ipos" / ipo_id


def _ensure(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# Write
# ---------------------------------------------------------------------------

def save_live_ipo(ipo: LiveIPO) -> None:
    """
    Persist a full LiveIPO snapshot.
    - Overwrites meta.json (latest state)
    - Appends changed subscription/GMP fields to observations.jsonl
    """
    d = _ipo_dir(ipo.ipo_id)
    _ensure(d)

    # 1. Overwrite meta.json
    meta_path = d / "meta.json"
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(_ipo_to_dict(ipo), f, indent=2)

    # 2. Append observations for time-varying fields
    obs_path = d / "observations.jsonl"
    now = _utcnow()
    observed_at = ipo.observed_at or now
    retrieved_at = ipo.retrieved_at or now

    _LIVE_FIELDS = [
        "subscription_qib_x",
        "subscription_nii_x",
        "subscription_retail_x",
        "subscription_total_x",
        "gmp_inr",
        "gmp_pct",
    ]
    with open(obs_path, "a", encoding="utf-8") as f:
        for field_name in _LIVE_FIELDS:
            value = getattr(ipo, field_name, None)
            obs = LiveObservation(
                ipo_id=ipo.ipo_id,
                field_name=field_name,
                value=value,
                observed_at=observed_at,
                retrieved_at=retrieved_at,
                source=ipo.source,
                source_url=ipo.source_url,
                is_final=ipo.subscription_is_final,
            )
            f.write(json.dumps(_obs_to_dict(obs)) + "\n")

    # 3. Update index
    _update_index(ipo)
    logger.debug("Saved live IPO %s → %s", ipo.ipo_id, d)


def _update_index(ipo: LiveIPO) -> None:
    _ensure(_BASE)
    index_path = _BASE / "index.json"
    index: dict = {}
    if index_path.exists():
        try:
            with open(index_path, encoding="utf-8") as f:
                index = json.load(f)
        except (json.JSONDecodeError, OSError):
            pass

    index[ipo.ipo_id] = {
        "company_name": ipo.company_name,
        "nse_symbol": ipo.nse_symbol,
        "status": ipo.status,
        "open_date": ipo.open_date,
        "close_date": ipo.close_date,
        "listing_date": ipo.listing_date,
        "issue_price": ipo.issue_price,
        "last_updated": _utcnow(),
    }
    with open(index_path, "w", encoding="utf-8") as f:
        json.dump(index, f, indent=2)


# ---------------------------------------------------------------------------
# Read
# ---------------------------------------------------------------------------

def load_live_ipo(ipo_id: str) -> Optional[LiveIPO]:
    """Load the latest LiveIPO snapshot for a given ipo_id."""
    meta_path = _ipo_dir(ipo_id) / "meta.json"
    if not meta_path.exists():
        return None
    try:
        with open(meta_path, encoding="utf-8") as f:
            data = json.load(f)
        return _dict_to_ipo(data)
    except (json.JSONDecodeError, OSError, KeyError) as e:
        logger.warning("Failed to load live IPO %s: %s", ipo_id, e)
        return None


def load_all_live_ipos() -> list[LiveIPO]:
    """Load all live IPO snapshots from the index."""
    index_path = _BASE / "index.json"
    if not index_path.exists():
        return []
    try:
        with open(index_path, encoding="utf-8") as f:
            index = json.load(f)
    except (json.JSONDecodeError, OSError):
        return []

    result = []
    for ipo_id in index:
        ipo = load_live_ipo(ipo_id)
        if ipo:
            result.append(ipo)
    return result


def load_observations(ipo_id: str) -> list[LiveObservation]:
    """
    Load all stored observations for a live IPO.
    Returns observations sorted by observed_at ascending.
    """
    obs_path = _ipo_dir(ipo_id) / "observations.jsonl"
    if not obs_path.exists():
        return []

    observations = []
    with open(obs_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                d = json.loads(line)
                observations.append(_dict_to_obs(d))
            except (json.JSONDecodeError, KeyError):
                continue

    observations.sort(key=lambda o: o.observed_at)
    return observations


def get_latest_subscription(ipo_id: str) -> dict:
    """
    Return the latest known subscription values, respecting point-in-time ordering.
    Returns dict with keys: qib, nii, retail, total (all float or None).
    """
    obs = load_observations(ipo_id)
    # Walk observations newest-first for each field
    result: dict = {"qib": None, "nii": None, "retail": None, "total": None}
    _FIELD_MAP = {
        "subscription_qib_x": "qib",
        "subscription_nii_x": "nii",
        "subscription_retail_x": "retail",
        "subscription_total_x": "total",
    }
    # Walk in reverse (latest first) — fill in first non-None seen
    for o in reversed(obs):
        key = _FIELD_MAP.get(o.field_name)
        if key and result[key] is None and o.value is not None:
            result[key] = o.value
        if all(v is not None for v in result.values()):
            break
    return result


# ---------------------------------------------------------------------------
# Serialisation helpers
# ---------------------------------------------------------------------------

def _ipo_to_dict(ipo: LiveIPO) -> dict:
    return {
        "ipo_id": ipo.ipo_id,
        "company_name": ipo.company_name,
        "nse_symbol": ipo.nse_symbol,
        "segment": ipo.segment,
        "open_date": ipo.open_date,
        "close_date": ipo.close_date,
        "listing_date": ipo.listing_date,
        "issue_price": ipo.issue_price,
        "price_band_low": ipo.price_band_low,
        "price_band_high": ipo.price_band_high,
        "lot_size": ipo.lot_size,
        "issue_size_cr": ipo.issue_size_cr,
        "fresh_issue_cr": ipo.fresh_issue_cr,
        "ofs_cr": ipo.ofs_cr,
        "subscription_qib_x": ipo.subscription_qib_x,
        "subscription_nii_x": ipo.subscription_nii_x,
        "subscription_retail_x": ipo.subscription_retail_x,
        "subscription_total_x": ipo.subscription_total_x,
        "subscription_is_final": ipo.subscription_is_final,
        "gmp_inr": ipo.gmp_inr,
        "gmp_pct": ipo.gmp_pct,
        "gmp_source": ipo.gmp_source,
        "status": ipo.status,
        "source": ipo.source,
        "source_url": ipo.source_url,
        "observed_at": ipo.observed_at,
        "retrieved_at": ipo.retrieved_at,
    }


def _dict_to_ipo(d: dict) -> LiveIPO:
    return LiveIPO(
        ipo_id=d["ipo_id"],
        company_name=d["company_name"],
        nse_symbol=d.get("nse_symbol"),
        segment=d.get("segment", "MAINBOARD"),
        open_date=d.get("open_date"),
        close_date=d.get("close_date"),
        listing_date=d.get("listing_date"),
        issue_price=d.get("issue_price"),
        price_band_low=d.get("price_band_low"),
        price_band_high=d.get("price_band_high"),
        lot_size=d.get("lot_size"),
        issue_size_cr=d.get("issue_size_cr"),
        fresh_issue_cr=d.get("fresh_issue_cr"),
        ofs_cr=d.get("ofs_cr"),
        subscription_qib_x=d.get("subscription_qib_x"),
        subscription_nii_x=d.get("subscription_nii_x"),
        subscription_retail_x=d.get("subscription_retail_x"),
        subscription_total_x=d.get("subscription_total_x"),
        subscription_is_final=d.get("subscription_is_final", False),
        gmp_inr=d.get("gmp_inr"),
        gmp_pct=d.get("gmp_pct"),
        gmp_source=d.get("gmp_source"),
        status=d.get("status", "UNKNOWN"),
        source=d.get("source", "UNKNOWN"),
        source_url=d.get("source_url"),
        observed_at=d.get("observed_at"),
        retrieved_at=d.get("retrieved_at"),
    )


def _obs_to_dict(obs: LiveObservation) -> dict:
    return {
        "ipo_id": obs.ipo_id,
        "field_name": obs.field_name,
        "value": obs.value,
        "observed_at": obs.observed_at,
        "retrieved_at": obs.retrieved_at,
        "source": obs.source,
        "source_url": obs.source_url,
        "is_final": obs.is_final,
    }


def _dict_to_obs(d: dict) -> LiveObservation:
    return LiveObservation(
        ipo_id=d["ipo_id"],
        field_name=d["field_name"],
        value=d.get("value"),
        observed_at=d["observed_at"],
        retrieved_at=d["retrieved_at"],
        source=d["source"],
        source_url=d.get("source_url"),
        is_final=d.get("is_final", False),
    )
