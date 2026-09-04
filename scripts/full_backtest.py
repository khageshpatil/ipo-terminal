"""
full_backtest.py — Complete three-strategy backtest on the 318-IPO universe.

Strategies compared:
  1. Apply-Every-IPO (baseline)
  2. Subscription-Only (total_sub >= threshold, no market filter)
  3. Rule-V1 (subscription + market regime + issue structure)

Output:
  data/universe/backtest_full.json   — all metrics for API + UI consumption
  Console: full comparison table
"""

from __future__ import annotations

import json
import logging
import statistics as stats
import sys
from collections import defaultdict
from decimal import Decimal
from pathlib import Path
from typing import Callable, Optional

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ipo_analyzer.backtest.engine import Decision, Recommendation
from ipo_analyzer.data_sources.universe_loader import UniverseIPO, load_universe
from ipo_analyzer.strategy.rule_based import RuleConfig, make_rule_strategy

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s", datefmt="%H:%M:%S")
logger = logging.getLogger("full_backtest")

OUT_DIR = Path("data/universe")
MKT_CSV = Path("data/market/market_features_daily.csv")


# ---------------------------------------------------------------------------
# Market features loader
# ---------------------------------------------------------------------------

def load_market_df():
    if MKT_CSV.exists():
        import pandas as pd
        return pd.read_csv(MKT_CSV)
    return None


def get_market_features(ipo: UniverseIPO, mkt_df) -> dict:
    features: dict = {}
    if mkt_df is None or ipo.listing_date is None:
        return features
    try:
        from ipo_analyzer.data_sources.market_data import get_market_snapshot_for_date
        # Use listing_date as proxy for close_date (we don't have close_date)
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
# Strategy 1: Apply-Every-IPO
# ---------------------------------------------------------------------------

def apply_every_ipo(ipo_id: str, features: dict) -> Decision:
    return Decision(
        ipo_id=ipo_id,
        recommendation=Recommendation.APPLY,
        p_positive=0.73,        # Historical base rate
        expected_return_pct=23.9,
        confidence="RULE_ESTIMATE",
        reason_lines=["Apply to every IPO (baseline strategy)"],
    )


# ---------------------------------------------------------------------------
# Strategy 2: Subscription-Only
# ---------------------------------------------------------------------------

def make_subscription_only(total_threshold: float = 10.0) -> Callable:
    """APPLY if total subscription >= threshold. Ignores market and structure."""
    def _fn(ipo_id: str, features: dict) -> Decision:
        total = features.get("subscription_total_x")
        if total is None:
            return Decision(
                ipo_id=ipo_id, recommendation=Recommendation.WATCH,
                confidence="RULE_ESTIMATE",
                reason_lines=["No subscription data"],
            )
        if total >= total_threshold:
            return Decision(
                ipo_id=ipo_id, recommendation=Recommendation.APPLY,
                p_positive=0.80 if total >= 50 else 0.70,
                expected_return_pct=20.0,
                confidence="RULE_ESTIMATE",
                reason_lines=[f"Total sub {total:.1f}x >= {total_threshold}x threshold"],
            )
        return Decision(
            ipo_id=ipo_id, recommendation=Recommendation.SKIP,
            p_positive=0.40,
            expected_return_pct=-2.0,
            confidence="RULE_ESTIMATE",
            reason_lines=[f"Total sub {total:.1f}x < {total_threshold}x threshold"],
        )
    return _fn


# ---------------------------------------------------------------------------
# Core backtest runner
# ---------------------------------------------------------------------------

def run_strategy(
    ipos: list[UniverseIPO],
    strategy_fn: Callable,
    strategy_name: str,
    mkt_df=None,
) -> dict:
    n_apply = n_skip = n_watch = 0
    applied_returns: list[float] = []
    skipped_returns: list[float] = []
    watch_returns: list[float] = []
    all_returns: list[float] = []
    by_year_applied: dict = defaultdict(list)
    per_ipo_records: list[dict] = []

    for ipo in ipos:
        # Build features
        features = ipo.as_feature_dict()
        mkt_f = get_market_features(ipo, mkt_df)
        features.update(mkt_f)

        decision = strategy_fn(ipo.ipo_id, features)
        ret = float(ipo.listing_return()) * 100 if ipo.listing_return() is not None else None
        positive = ipo.positive_listing()

        if ret is not None:
            all_returns.append(ret)

        rec = decision.recommendation
        if rec == Recommendation.APPLY:
            n_apply += 1
            if ret is not None:
                applied_returns.append(ret)
                if ipo.year:
                    by_year_applied[ipo.year].append(ret)
        elif rec == Recommendation.SKIP:
            n_skip += 1
            if ret is not None:
                skipped_returns.append(ret)
        else:
            n_watch += 1
            if ret is not None:
                watch_returns.append(ret)

        # Per-IPO record for API
        per_ipo_records.append({
            "ipo_id": ipo.ipo_id,
            "company": ipo.company_name,
            "year": ipo.year,
            "nse_symbol": ipo.nse_symbol,
            "listing_date": ipo.listing_date.isoformat() if ipo.listing_date else None,
            "issue_price": float(ipo.issue_price) if ipo.issue_price else None,
            "listing_open_price": float(ipo.listing_open_price) if ipo.listing_open_price else None,
            "listing_open_quality": ipo.listing_open_quality,
            "rec": rec,
            "p_pos": decision.p_positive,
            "return_pct": round(ret, 2) if ret is not None else None,
            "positive": positive,
            "subscription_total_x": ipo.subscription_total_x,
            "subscription_qib_x": ipo.subscription_qib_x,
            "subscription_nii_x": ipo.subscription_nii_x,
            "subscription_retail_x": ipo.subscription_retail_x,
            "market_regime": mkt_f.get("market_regime"),
            "reason": decision.reason_lines[-1] if decision.reason_lines else "",
        })

    def _stats(rets: list[float]) -> dict:
        if not rets:
            return {"n": 0}
        pos = sum(1 for r in rets if r > 0)
        neg = len(rets) - pos
        # Cumulative return = product of (1 + r/100) - 1, per application
        cumret = 1.0
        for r in rets:
            cumret *= (1 + r / 100)
        cumret = (cumret - 1) * 100
        return {
            "n": len(rets),
            "positive": pos,
            "negative": neg,
            "hit_rate_pct": round(pos / len(rets) * 100, 1),
            "mean_pct": round(stats.mean(rets), 2),
            "median_pct": round(stats.median(rets), 2),
            "max_gain_pct": round(max(rets), 2),
            "max_loss_pct": round(min(rets), 2),
            "std_pct": round(stats.stdev(rets), 2) if len(rets) > 1 else 0.0,
            "cumulative_pct": round(cumret, 2),
        }

    # Yearly breakdown
    yearly = {}
    for y in sorted(by_year_applied):
        rets = by_year_applied[y]
        pos = sum(1 for r in rets if r > 0)
        yearly[y] = {
            "n": len(rets),
            "positive": pos,
            "hit_rate_pct": round(pos / len(rets) * 100, 1),
            "mean_pct": round(stats.mean(rets), 2),
            "median_pct": round(stats.median(rets), 2),
        }

    n_total = len(ipos)
    return {
        "strategy_name": strategy_name,
        "n_total": n_total,
        "n_apply": n_apply,
        "n_skip": n_skip,
        "n_watch": n_watch,
        "apply_rate_pct": round(n_apply / n_total * 100, 1) if n_total else 0,
        "coverage_pct": round((n_apply + n_watch) / n_total * 100, 1) if n_total else 0,
        "applied": _stats(applied_returns),
        "skipped": _stats(skipped_returns),
        "watched": _stats(watch_returns),
        "all_baseline": _stats(all_returns),
        "yearly": yearly,
        "per_ipo": per_ipo_records,
    }


def _delta(strategy_hit: float, baseline_hit: float) -> str:
    d = strategy_hit - baseline_hit
    return f"{d:+.1f}pp"


def print_comparison(results: dict[str, dict]) -> None:
    names = list(results.keys())
    print(f"\n{'=' * 78}")
    print("FULL BACKTEST COMPARISON — 318 Mainboard IPOs 2018–2024")
    print("[!] All metrics are IN-SAMPLE. Subscription is observed ex-post.")
    print(f"{'=' * 78}")

    header = f"  {'Metric':<32}"
    for n in names:
        header += f" {n[:18]:>18}"
    print(header)
    print(f"  {'-'*32}" + f" {'─'*18}" * len(names))

    def row(label: str, *vals):
        line = f"  {label:<32}"
        for v in vals:
            line += f" {str(v):>18}"
        print(line)

    # Extract metrics
    def g(name, *keys):
        d = results[name]
        for k in keys:
            d = d.get(k, {}) if isinstance(d, dict) else {}
        return d if d != {} else "—"

    row("Total IPOs", *[results[n]["n_total"] for n in names])
    row("APPLY count", *[results[n]["n_apply"] for n in names])
    row("SKIP count", *[results[n]["n_skip"] for n in names])
    row("WATCH count", *[results[n]["n_watch"] for n in names])
    row("Apply rate", *[f"{results[n]['apply_rate_pct']}%" for n in names])
    print()
    row("Hit rate (APPLY)", *[f"{results[n]['applied'].get('hit_rate_pct','—')}%" for n in names])
    row("Mean return (APPLY)", *[f"{results[n]['applied'].get('mean_pct','—'):+}%" if isinstance(results[n]['applied'].get('mean_pct'), float) else "—" for n in names])
    row("Median return (APPLY)", *[f"{results[n]['applied'].get('median_pct','—'):+}%" if isinstance(results[n]['applied'].get('median_pct'), float) else "—" for n in names])
    row("Best return", *[f"{results[n]['applied'].get('max_gain_pct','—'):+}%" if isinstance(results[n]['applied'].get('max_gain_pct'), float) else "—" for n in names])
    row("Worst return", *[f"{results[n]['applied'].get('max_loss_pct','—'):+}%" if isinstance(results[n]['applied'].get('max_loss_pct'), float) else "—" for n in names])
    row("Std dev", *[f"{results[n]['applied'].get('std_pct','—')}%" for n in names])
    row("Cumulative (per app)", *[f"{results[n]['applied'].get('cumulative_pct','—'):+}%" if isinstance(results[n]['applied'].get('cumulative_pct'), float) else "—" for n in names])

    print(f"\n  {'Year breakdown (APPLY)'}")
    all_years = sorted({y for n in names for y in results[n]["yearly"].keys()})
    for y in all_years:
        parts = []
        for n in names:
            yr = results[n]["yearly"].get(y, {})
            if yr:
                parts.append(f"n={yr['n']} {yr['hit_rate_pct']}% mean={yr['mean_pct']:+.1f}%")
            else:
                parts.append("—")
        row(f"  {y}", *parts)

    print(f"{'=' * 78}")


def main() -> None:
    logger.info("Loading universe...")
    ipos = load_universe()
    usable = [r for r in ipos if r.is_usable()]
    logger.info("Usable: %d IPOs", len(usable))

    mkt_df = load_market_df()

    # Run three strategies
    logger.info("Strategy 1: Apply-Every-IPO...")
    r1 = run_strategy(usable, apply_every_ipo, "Apply-Every-IPO", mkt_df)

    logger.info("Strategy 2: Subscription-Only (>=10x)...")
    r2 = run_strategy(usable, make_subscription_only(10.0), "Sub-Only (>=10x)", mkt_df)

    logger.info("Strategy 3: Rule-V1...")
    r3 = run_strategy(usable, make_rule_strategy(RuleConfig()), "Rule-V1", mkt_df)

    results = {
        "Apply-Every-IPO": r1,
        "Sub-Only (>=10x)": r2,
        "Rule-V1": r3,
    }

    print_comparison(results)

    # Save full results (strip per_ipo to keep file manageable)
    for k in results:
        results[k]["per_ipo_count"] = len(results[k].pop("per_ipo"))

    out_path = OUT_DIR / "backtest_full.json"
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)
    logger.info("Saved: %s", out_path)

    # Also save per_ipo for Rule-V1 separately
    logger.info("Re-running Rule-V1 for per-IPO record save...")
    r3_full = run_strategy(usable, make_rule_strategy(RuleConfig()), "Rule-V1", mkt_df)
    with open(OUT_DIR / "backtest_rule_v1_per_ipo.json", "w") as f:
        json.dump(r3_full["per_ipo"], f, indent=2)
    logger.info("Per-IPO records saved.")


if __name__ == "__main__":
    main()
