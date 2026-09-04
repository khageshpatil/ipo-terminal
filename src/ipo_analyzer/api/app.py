"""
FastAPI application — v0.2.0

All analysis endpoints now serve from the real 318-IPO universe.
Backtest results are loaded from data/universe/backtest_full.json.

Routes:
  GET  /health
  GET  /ipos                         — list universe with pagination/filter
  GET  /ipos/{id}                    — single IPO details
  GET  /ipos/{id}/analysis           — full decision analysis
  POST /capital/recommendation       — capital plan for given budget
  GET  /backtests/summary            — three-strategy comparison
  GET  /backtests/per-ipo            — Rule-V1 per-IPO records
"""

from __future__ import annotations

import json
import logging
import threading
from pathlib import Path
from typing import Optional

from fastapi import BackgroundTasks, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

logger = logging.getLogger(__name__)

app = FastAPI(
    title="IPO Decision Engine",
    version="0.2.0",
    description=(
        "Rule-based IPO listing-gain decision engine. "
        "All probability estimates are RULE_ESTIMATE until an ML model is validated."
    ),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Singletons
# ---------------------------------------------------------------------------

_universe: Optional[list] = None
_strategy = None
_backtest_full: Optional[dict] = None
_backtest_per_ipo: Optional[list] = None
_live_refresh_lock = threading.Lock()
_live_last_refreshed: Optional[str] = None

BACKTEST_FULL_PATH = Path("data/universe/backtest_full.json")
BACKTEST_PER_IPO_PATH = Path("data/universe/backtest_rule_v1_per_ipo.json")


def _get_universe():
    global _universe
    if _universe is None:
        from ipo_analyzer.data_sources.universe_loader import load_universe
        _universe = load_universe()
        logger.info("Universe loaded: %d records", len(_universe))
    return _universe


def _get_strategy():
    global _strategy
    if _strategy is None:
        from ipo_analyzer.strategy.rule_based import make_rule_strategy
        _strategy = make_rule_strategy()
    return _strategy


def _get_backtest_full() -> dict:
    global _backtest_full
    if _backtest_full is None:
        if BACKTEST_FULL_PATH.exists():
            with open(BACKTEST_FULL_PATH) as f:
                _backtest_full = json.load(f)
        else:
            _backtest_full = {}
    return _backtest_full


def _get_backtest_per_ipo() -> list:
    global _backtest_per_ipo
    if _backtest_per_ipo is None:
        if BACKTEST_PER_IPO_PATH.exists():
            with open(BACKTEST_PER_IPO_PATH) as f:
                _backtest_per_ipo = json.load(f)
        else:
            _backtest_per_ipo = []
    return _backtest_per_ipo


def _build_analysis_features(ipo) -> dict:
    """Build features for one IPO — market data joined if available."""
    features = ipo.as_feature_dict()
    mkt_path = Path("data/market/market_features_daily.csv")
    if mkt_path.exists() and ipo.listing_date:
        try:
            import pandas as pd
            from ipo_analyzer.data_sources.market_data import get_market_snapshot_for_date
            mkt_df = pd.read_csv(mkt_path)
            snap = get_market_snapshot_for_date(mkt_df, ipo.listing_date)
            if snap:
                features["market_regime"] = snap.market_regime
                features["market_india_vix_close"] = snap.india_vix_close
                features["market_nifty_return_20d"] = snap.nifty_return_20d
                features["market_nifty_return_5d"] = snap.nifty_return_5d
        except Exception:
            pass
    return features


# ---------------------------------------------------------------------------
# Response models
# ---------------------------------------------------------------------------

class IPOSummary(BaseModel):
    ipo_id: str
    company_name: str
    nse_symbol: str
    listing_date: Optional[str]
    issue_price: Optional[float]
    lot_size: Optional[int]
    listing_open_price: Optional[float]
    listing_return_pct: Optional[float]
    listing_open_quality: str
    subscription_qib_x: Optional[float]
    subscription_nii_x: Optional[float]
    subscription_retail_x: Optional[float]
    subscription_total_x: Optional[float]
    year: Optional[int]


class IPOAnalysisResponse(BaseModel):
    ipo_id: str
    company_name: str
    nse_symbol: str
    issue_price: Optional[float]
    lot_size: Optional[int]
    listing_date: Optional[str]
    listing_open_price: Optional[float]
    listing_return_pct: Optional[float]
    listing_open_quality: str

    # Subscription
    subscription_qib_x: Optional[float]
    subscription_nii_x: Optional[float]
    subscription_retail_x: Optional[float]
    subscription_total_x: Optional[float]

    # Decision
    recommendation: str
    confidence: str
    p_positive: Optional[float]
    expected_return_pct: Optional[float]
    p_allotment: Optional[float]
    expected_profit_per_application: Optional[float]
    capital_required_per_lot: Optional[float]
    reason_lines: list[str]

    # Market context
    market_regime: Optional[str]
    market_india_vix_close: Optional[float]
    market_nifty_return_20d: Optional[float]
    market_nifty_return_5d: Optional[float]

    # Issue structure
    issue_size_cr: Optional[float]
    ofs_cr: Optional[float]
    ofs_pct: Optional[float]


class CapitalRequest(BaseModel):
    available_capital: float
    skip_watch: bool = False


class CapitalLine(BaseModel):
    ipo_id: str
    company_name: str
    recommendation: str
    lots_to_apply: int
    capital_required: float
    expected_profit: Optional[float]
    allotment_probability: Optional[float]
    expected_return_pct: Optional[float]


class CapitalResponse(BaseModel):
    available_capital: float
    total_capital_deployed: float
    remaining_capital: float
    n_ipos: int
    lines: list[CapitalLine]
    skipped: list[str]


class StrategyStats(BaseModel):
    n: int
    positive: Optional[int]
    negative: Optional[int]
    hit_rate_pct: Optional[float]
    mean_pct: Optional[float]
    median_pct: Optional[float]
    max_gain_pct: Optional[float]
    max_loss_pct: Optional[float]
    std_pct: Optional[float]


class StrategyResult(BaseModel):
    strategy_name: str
    n_total: int
    n_apply: int
    n_skip: int
    n_watch: int
    apply_rate_pct: float
    applied: dict
    yearly: dict


class BacktestSummary(BaseModel):
    strategies: list[StrategyResult]
    generated_at: Optional[str]
    dataset_note: str = (
        "IN-SAMPLE on 318 Mainboard IPOs 2018-2024. "
        "Subscription data is ex-post. Results cannot be used as future performance evidence."
    )


class PerIpoRecord(BaseModel):
    ipo_id: str
    company: str
    year: Optional[int]
    nse_symbol: Optional[str]
    listing_date: Optional[str]
    issue_price: Optional[float]
    listing_open_price: Optional[float]
    listing_open_quality: Optional[str]
    rec: str
    p_pos: Optional[float]
    return_pct: Optional[float]
    positive: Optional[bool]
    subscription_total_x: Optional[float]
    subscription_qib_x: Optional[float]
    subscription_nii_x: Optional[float]
    subscription_retail_x: Optional[float]
    market_regime: Optional[str]
    reason: Optional[str]


# ---------------------------------------------------------------------------
# Startup — trigger initial live data refresh in background
# ---------------------------------------------------------------------------

@app.on_event("startup")
async def _startup_refresh() -> None:
    """Kick off an initial live data fetch without blocking server startup."""
    def _bg():
        try:
            from ipo_analyzer.live.runner import refresh_live_ipos
            global _live_last_refreshed
            with _live_refresh_lock:
                refresh_live_ipos()
                from datetime import datetime, timezone
                _live_last_refreshed = datetime.now(timezone.utc).isoformat()
        except Exception as e:
            logger.warning("Startup live refresh failed (non-fatal): %s", e)
    t = threading.Thread(target=_bg, daemon=True)
    t.start()


# ---------------------------------------------------------------------------
# Routes — Health
# ---------------------------------------------------------------------------

@app.get("/health")
def health():
    return {
        "status": "ok",
        "version": "0.2.0",
        "universe_loaded": _universe is not None,
        "note": "All recommendations are RULE_ESTIMATE",
    }


@app.get("/ipos", response_model=list[IPOSummary])
def list_ipos(
    year: Optional[int] = Query(None),
    search: Optional[str] = Query(None, description="Company name substring"),
    min_quality: str = Query("SECONDARY_VERIFIED"),
    limit: int = Query(100, le=500),
    offset: int = Query(0, ge=0),
):
    ipos = _get_universe()
    if year:
        ipos = [r for r in ipos if r.year == year]
    if search:
        s = search.lower()
        ipos = [r for r in ipos if s in r.company_name.lower() or s in r.nse_symbol.lower()]
    ipos = ipos[offset: offset + limit]
    return [
        IPOSummary(
            ipo_id=r.ipo_id,
            company_name=r.company_name,
            nse_symbol=r.nse_symbol,
            listing_date=r.listing_date.isoformat() if r.listing_date else None,
            issue_price=float(r.issue_price) if r.issue_price else None,
            lot_size=r.lot_size,
            listing_open_price=float(r.listing_open_price) if r.listing_open_price else None,
            listing_return_pct=round(float(r.listing_return()) * 100, 2) if r.listing_return() else None,
            listing_open_quality=r.listing_open_quality,
            subscription_qib_x=r.subscription_qib_x,
            subscription_nii_x=r.subscription_nii_x,
            subscription_retail_x=r.subscription_retail_x,
            subscription_total_x=r.subscription_total_x,
            year=r.year,
        )
        for r in ipos
    ]


@app.get("/ipos/{ipo_id}", response_model=IPOSummary)
def get_ipo(ipo_id: str):
    ipos = _get_universe()
    match = next((r for r in ipos if r.ipo_id == ipo_id), None)
    if not match:
        raise HTTPException(404, f"IPO {ipo_id} not found")
    return IPOSummary(
        ipo_id=match.ipo_id,
        company_name=match.company_name,
        nse_symbol=match.nse_symbol,
        listing_date=match.listing_date.isoformat() if match.listing_date else None,
        issue_price=float(match.issue_price) if match.issue_price else None,
        lot_size=match.lot_size,
        listing_open_price=float(match.listing_open_price) if match.listing_open_price else None,
        listing_return_pct=round(float(match.listing_return()) * 100, 2) if match.listing_return() else None,
        listing_open_quality=match.listing_open_quality,
        subscription_qib_x=match.subscription_qib_x,
        subscription_nii_x=match.subscription_nii_x,
        subscription_retail_x=match.subscription_retail_x,
        subscription_total_x=match.subscription_total_x,
        year=match.year,
    )


@app.get("/ipos/{ipo_id}/analysis", response_model=IPOAnalysisResponse)
def analyse_ipo(ipo_id: str):
    from decimal import Decimal
    from ipo_analyzer.backtest.decision_engine import DecisionEngine

    ipos = _get_universe()
    match = next((r for r in ipos if r.ipo_id == ipo_id), None)
    if not match:
        raise HTTPException(404, f"IPO {ipo_id} not found")

    features = _build_analysis_features(match)
    engine = DecisionEngine(strategy_fn=_get_strategy())
    retail_x = Decimal(str(match.subscription_retail_x)) if match.subscription_retail_x else None
    analysis = engine.analyse(
        ipo_id=match.ipo_id,
        company_name=match.company_name,
        features=features,
        issue_price=match.issue_price,
        lot_size=match.lot_size,
        retail_subscription_x=retail_x,
    )

    return IPOAnalysisResponse(
        ipo_id=match.ipo_id,
        company_name=match.company_name,
        nse_symbol=match.nse_symbol,
        issue_price=float(match.issue_price) if match.issue_price else None,
        lot_size=match.lot_size,
        listing_date=match.listing_date.isoformat() if match.listing_date else None,
        listing_open_price=float(match.listing_open_price) if match.listing_open_price else None,
        listing_return_pct=round(float(match.listing_return()) * 100, 2) if match.listing_return() else None,
        listing_open_quality=match.listing_open_quality,
        subscription_qib_x=match.subscription_qib_x,
        subscription_nii_x=match.subscription_nii_x,
        subscription_retail_x=match.subscription_retail_x,
        subscription_total_x=match.subscription_total_x,
        recommendation=analysis.recommendation,
        confidence=analysis.confidence,
        p_positive=analysis.p_positive,
        expected_return_pct=analysis.expected_return_pct,
        p_allotment=analysis.p_allotment,
        expected_profit_per_application=(
            float(analysis.expected_profit_per_application)
            if analysis.expected_profit_per_application else None
        ),
        capital_required_per_lot=(
            float(analysis.capital_required_per_lot)
            if analysis.capital_required_per_lot else None
        ),
        reason_lines=analysis.reason_lines,
        market_regime=features.get("market_regime"),
        market_india_vix_close=features.get("market_india_vix_close"),
        market_nifty_return_20d=features.get("market_nifty_return_20d"),
        market_nifty_return_5d=features.get("market_nifty_return_5d"),
        issue_size_cr=match.issue_size_cr,
        ofs_cr=match.ofs_cr,
        ofs_pct=match.ofs_ratio,
    )


@app.post("/capital/recommendation", response_model=CapitalResponse)
def capital_recommendation(request: CapitalRequest):
    from decimal import Decimal
    from ipo_analyzer.backtest.capital_allocator import allocate_capital
    from ipo_analyzer.backtest.decision_engine import DecisionEngine

    ipos = _get_universe()
    engine = DecisionEngine(strategy_fn=_get_strategy())

    analyses = []
    for r in ipos:
        if not r.is_usable():
            continue
        features = _build_analysis_features(r)
        retail_x = Decimal(str(r.subscription_retail_x)) if r.subscription_retail_x else None
        analysis = engine.analyse(
            ipo_id=r.ipo_id,
            company_name=r.company_name,
            features=features,
            issue_price=r.issue_price,
            lot_size=r.lot_size,
            retail_subscription_x=retail_x,
        )
        analyses.append(analysis)

    plan = allocate_capital(
        available_capital=request.available_capital,
        analyses=analyses,
        skip_watch=request.skip_watch,
    )

    return CapitalResponse(
        available_capital=float(plan.available_capital),
        total_capital_deployed=float(plan.total_capital_deployed),
        remaining_capital=float(plan.remaining_capital),
        n_ipos=len(plan.lines),
        lines=[
            CapitalLine(
                ipo_id=ln.ipo_id,
                company_name=ln.company_name,
                recommendation=ln.recommendation,
                lots_to_apply=ln.lots_to_apply,
                capital_required=float(ln.capital_required),
                expected_profit=float(ln.expected_profit) if ln.expected_profit else None,
                allotment_probability=ln.allotment_probability,
                expected_return_pct=ln.expected_return_pct,
            )
            for ln in plan.lines
        ],
        skipped=plan.skipped_ipos,
    )


@app.get("/backtests/summary")
def backtest_summary():
    """Returns the three-strategy comparison from the pre-run backtest file."""
    data = _get_backtest_full()
    if not data:
        raise HTTPException(404, "Backtest results not found. Run scripts/full_backtest.py first.")

    strategies = []
    for name, result in data.items():
        strategies.append(StrategyResult(
            strategy_name=result.get("strategy_name", name),
            n_total=result.get("n_total", 0),
            n_apply=result.get("n_apply", 0),
            n_skip=result.get("n_skip", 0),
            n_watch=result.get("n_watch", 0),
            apply_rate_pct=result.get("apply_rate_pct", 0),
            applied=result.get("applied", {}),
            yearly={str(k): v for k, v in result.get("yearly", {}).items()},
        ))

    return {
        "strategies": [s.model_dump() for s in strategies],
        "dataset_note": (
            "IN-SAMPLE on 318 Mainboard IPOs 2018-2024. "
            "Subscription data is observed ex-post. "
            "Results cannot be used as future performance evidence."
        ),
        "primary_verified": 244,
        "secondary_verified": 74,
    }


@app.get("/backtests/per-ipo", response_model=list[PerIpoRecord])
def backtest_per_ipo(
    year: Optional[int] = Query(None),
    rec: Optional[str] = Query(None, description="Filter by recommendation: APPLY/SKIP/WATCH"),
    limit: int = Query(200, le=500),
    offset: int = Query(0, ge=0),
):
    """Rule-V1 per-IPO backtest records for the performance table."""
    records = _get_backtest_per_ipo()
    if year:
        records = [r for r in records if r.get("year") == year]
    if rec:
        records = [r for r in records if r.get("rec") == rec.upper()]
    records = records[offset: offset + limit]
    return [PerIpoRecord(**r) for r in records]


@app.get("/backtests/baseline")
def baseline():
    """Apply-Every-IPO statistics from the real 318-record dataset."""
    from ipo_analyzer.data_sources.universe_loader import compute_base_rate
    ipos = _get_universe()
    result = compute_base_rate(ipos)
    return {
        **result,
        "dataset_note": "Historical in-sample. PRIMARY_VERIFIED=244, SECONDARY_VERIFIED=74.",
    }


# ---------------------------------------------------------------------------
# Routes — Live IPO Data  (Phase E)
# ---------------------------------------------------------------------------

@app.get("/live/ipos")
def live_ipos(status: Optional[str] = Query(None, description="Filter: OPEN/UPCOMING/CLOSED")):
    """
    Return all currently tracked live IPOs with their latest observations.
    Data is sourced from Chittorgarh live subscription page.
    All recommendations are RULE_ESTIMATE.
    """
    from ipo_analyzer.live.store import load_all_live_ipos
    from ipo_analyzer.live.runner import run_live_decision

    ipos = load_all_live_ipos()
    if status:
        ipos = [i for i in ipos if i.status == status.upper()]

    result = []
    for ipo in ipos:
        decision = run_live_decision(ipo)
        result.append({
            "ipo_id": ipo.ipo_id,
            "company_name": ipo.company_name,
            "nse_symbol": ipo.nse_symbol,
            "status": ipo.status,
            "segment": ipo.segment,
            "open_date": ipo.open_date,
            "close_date": ipo.close_date,
            "listing_date": ipo.listing_date,
            "issue_price": ipo.issue_price,
            "price_band_low": ipo.price_band_low,
            "price_band_high": ipo.price_band_high,
            "lot_size": ipo.lot_size,
            "issue_size_cr": ipo.issue_size_cr,
            "subscription_qib_x": ipo.subscription_qib_x,
            "subscription_nii_x": ipo.subscription_nii_x,
            "subscription_retail_x": ipo.subscription_retail_x,
            "subscription_total_x": ipo.subscription_total_x,
            "subscription_is_final": ipo.subscription_is_final,
            "gmp_inr": ipo.gmp_inr,
            "gmp_pct": ipo.gmp_pct,
            "recommendation": decision.recommendation,
            "confidence": decision.confidence,
            "p_positive": decision.p_positive,
            "expected_return_pct": decision.expected_return_pct,
            "data_quality": decision.data_quality,
            "observed_at": ipo.observed_at,
            "retrieved_at": ipo.retrieved_at,
            "source": ipo.source,
        })

    return {
        "count": len(result),
        "last_refreshed": _live_last_refreshed,
        "note": "All recommendations are RULE_ESTIMATE. Data from Chittorgarh.",
        "ipos": result,
    }


@app.get("/live/ipos/{ipo_id}/analysis")
def live_ipo_analysis(ipo_id: str):
    """
    Full rule-strategy analysis for a single live IPO.
    Includes signal breakdown and reason lines.
    """
    from ipo_analyzer.live.store import load_live_ipo
    from ipo_analyzer.live.runner import run_live_decision

    ipo = load_live_ipo(ipo_id)
    if not ipo:
        raise HTTPException(404, f"Live IPO {ipo_id!r} not found. Try POST /live/refresh first.")

    decision = run_live_decision(ipo)

    return {
        "ipo_id": ipo.ipo_id,
        "company_name": ipo.company_name,
        "nse_symbol": ipo.nse_symbol,
        "status": ipo.status,
        "open_date": ipo.open_date,
        "close_date": ipo.close_date,
        "listing_date": ipo.listing_date,
        "issue_price": ipo.issue_price,
        "lot_size": ipo.lot_size,
        "issue_size_cr": ipo.issue_size_cr,
        "subscription_qib_x": ipo.subscription_qib_x,
        "subscription_nii_x": ipo.subscription_nii_x,
        "subscription_retail_x": ipo.subscription_retail_x,
        "subscription_total_x": ipo.subscription_total_x,
        "gmp_inr": ipo.gmp_inr,
        "gmp_pct": ipo.gmp_pct,
        "recommendation": decision.recommendation,
        "confidence": decision.confidence,
        "p_positive": decision.p_positive,
        "expected_return_pct": decision.expected_return_pct,
        "reason_lines": decision.reason_lines,
        "data_quality": decision.data_quality,
        "missing_fields": decision.missing_fields,
        "decision_at": decision.decision_at,
        "source": ipo.source,
        "observed_at": ipo.observed_at,
    }


@app.get("/live/ipos/{ipo_id}/snapshots")
def live_ipo_snapshots(
    ipo_id: str,
    field: Optional[str] = Query(None, description="Filter by field name"),
    limit: int = Query(100, le=500),
):
    """
    Return the raw time-series observation log for a live IPO.
    This is the prospective dataset being built for future model training.
    """
    from ipo_analyzer.live.store import load_observations

    obs = load_observations(ipo_id)
    if not obs:
        raise HTTPException(404, f"No observations found for {ipo_id!r}")

    if field:
        obs = [o for o in obs if o.field_name == field]

    obs = obs[-limit:]  # most recent N

    return {
        "ipo_id": ipo_id,
        "total_observations": len(obs),
        "fields_tracked": list({o.field_name for o in obs}),
        "observations": [
            {
                "field_name": o.field_name,
                "value": o.value,
                "observed_at": o.observed_at,
                "retrieved_at": o.retrieved_at,
                "source": o.source,
                "is_final": o.is_final,
            }
            for o in obs
        ],
    }


@app.post("/live/refresh")
def live_refresh(background_tasks: BackgroundTasks):
    """
    Trigger a live data refresh from Chittorgarh.
    Refresh runs in background — returns immediately.
    Check GET /live/ipos for updated data.
    """
    def _do_refresh():
        global _live_last_refreshed
        with _live_refresh_lock:
            from ipo_analyzer.live.runner import refresh_live_ipos
            refresh_live_ipos()
            from datetime import datetime, timezone
            _live_last_refreshed = datetime.now(timezone.utc).isoformat()

    background_tasks.add_task(_do_refresh)
    return {
        "status": "refresh_queued",
        "message": "Live data refresh started in background. Check /live/ipos shortly.",
    }
