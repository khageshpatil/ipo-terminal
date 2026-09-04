"""
run_backtest.py — Phase 4/5: Run the rule-based strategy backtest on real historical data.

Usage:
    uv run python scripts/run_backtest.py
    uv run python scripts/run_backtest.py --strategy rule --total-min 20

Outputs:
    data/universe/backtest_rule_v1.json   — full results JSON
    Console summary
"""

from __future__ import annotations

import json
import logging
import sys
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ipo_analyzer.data_sources.universe_loader import compute_base_rate, load_universe
from ipo_analyzer.strategy.rule_based import RuleConfig, make_rule_strategy

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("run_backtest")

OUT_DIR = Path("data/universe")
MKT_CSV = Path("data/market/market_features_daily.csv")


def load_market_features():
    if MKT_CSV.exists():
        import pandas as pd
        return pd.read_csv(MKT_CSV)
    return None


def build_features(ipo, mkt_df) -> dict:
    """Build the feature dict for one IPO — point-in-time safe."""
    features = ipo.as_feature_dict()

    if mkt_df is not None and ipo.close_date:
        from ipo_analyzer.data_sources.market_data import get_market_snapshot_for_date
        snap = get_market_snapshot_for_date(mkt_df, ipo.close_date)
        if snap:
            features["market_regime"] = snap.market_regime
            features["market_india_vix_close"] = snap.india_vix_close
            features["market_nifty_return_20d"] = snap.nifty_return_20d
            features["market_nifty_return_5d"] = snap.nifty_return_5d
            features["market_vix_label"] = snap.vix_level_label

    return features


def run(config: RuleConfig, strategy_name: str) -> dict:
    ipos = load_universe()
    usable = [r for r in ipos if r.is_usable()]
    logger.info("Usable IPOs: %d", len(usable))

    mkt_df = load_market_features()
    strategy_fn = make_rule_strategy(config)

    n_total = len(usable)
    n_apply = 0
    n_skip = 0
    n_watch = 0

    applied_returns: list[float] = []
    all_returns: list[float] = []
    skipped_returns: list[float] = []

    per_ipo: list[dict] = []

    for ipo in usable:
        features = build_features(ipo, mkt_df)
        decision = strategy_fn(ipo.ipo_id, features)
        ret = float(ipo.listing_return()) * 100 if ipo.listing_return() else None
        positive = ipo.positive_listing()

        if ret is not None:
            all_returns.append(ret)

        if decision.recommendation == "APPLY":
            n_apply += 1
            if ret is not None:
                applied_returns.append(ret)
        elif decision.recommendation == "SKIP":
            n_skip += 1
            if ret is not None:
                skipped_returns.append(ret)
        else:
            n_watch += 1

        per_ipo.append({
            "ipo_id": ipo.ipo_id,
            "company": ipo.company_name,
            "year": ipo.year,
            "rec": decision.recommendation,
            "p_pos": decision.p_positive,
            "return_pct": ret,
            "positive": positive,
            "total_sub": ipo.subscription_total_x,
            "market_regime": features.get("market_regime"),
        })

    import statistics as stats

    def _stats(rets: list[float]) -> dict:
        if not rets:
            return {}
        pos = sum(1 for r in rets if r > 0)
        return {
            "n": len(rets),
            "positive": pos,
            "hit_rate_pct": round(pos / len(rets) * 100, 1),
            "mean_pct": round(stats.mean(rets), 2),
            "median_pct": round(stats.median(rets), 2),
            "max_gain_pct": round(max(rets), 2),
            "max_loss_pct": round(min(rets), 2),
            "std_pct": round(stats.stdev(rets), 2) if len(rets) > 1 else 0.0,
        }

    # Year breakdown for applied
    from collections import defaultdict
    by_year: dict = defaultdict(list)
    for r in per_ipo:
        if r["rec"] == "APPLY" and r["return_pct"] is not None and r["year"]:
            by_year[r["year"]].append(r["return_pct"])

    yearly = {}
    for y in sorted(by_year):
        rets = by_year[y]
        pos = sum(1 for r in rets if r > 0)
        yearly[y] = {
            "n": len(rets),
            "positive": pos,
            "hit_rate_pct": round(pos / len(rets) * 100, 1),
            "mean_pct": round(stats.mean(rets), 2),
        }

    result = {
        "strategy": strategy_name,
        "n_total": n_total,
        "n_apply": n_apply,
        "n_skip": n_skip,
        "n_watch": n_watch,
        "apply_rate_pct": round(n_apply / n_total * 100, 1) if n_total else 0,
        "applied": _stats(applied_returns),
        "skipped": _stats(skipped_returns),
        "all_ipos_baseline": _stats(all_returns),
        "yearly": yearly,
        "per_ipo": per_ipo,
    }
    return result


def print_results(result: dict) -> None:
    s = result["applied"]
    b = result["all_ipos_baseline"]
    print(f"\n{'='*68}")
    print(f"BACKTEST: {result['strategy']}")
    print(f"{'='*68}")
    print(f"  Total usable IPOs:   {result['n_total']}")
    print(f"  APPLY decisions:     {result['n_apply']} ({result['apply_rate_pct']:.0f}%)")
    print(f"  SKIP decisions:      {result['n_skip']}")
    print(f"  WATCH decisions:     {result['n_watch']}")
    print()
    if s:
        print(f"  --- APPLIED IPOs ({s['n']}) ---")
        print(f"  Hit rate:           {s['hit_rate_pct']}%")
        print(f"  Mean return:        {s['mean_pct']:+.2f}%")
        print(f"  Median return:      {s['median_pct']:+.2f}%")
        print(f"  Max gain:           {s['max_gain_pct']:+.2f}%")
        print(f"  Max loss:           {s['max_loss_pct']:+.2f}%")
        print(f"  Std dev:            {s['std_pct']:.2f}%")
    print()
    if b:
        delta = s.get("hit_rate_pct", 0) - b.get("hit_rate_pct", 0)
        print(f"  --- Apply-Every-IPO Benchmark ({b['n']}) ---")
        print(f"  Benchmark hit rate: {b['hit_rate_pct']}%")
        print(f"  Strategy advantage: {delta:+.1f}pp")
    print()
    if result.get("yearly"):
        print(f"  {'Year':<6} {'N':>4} {'Pos':>4} {'Rate':>7} {'Mean':>8}")
        print(f"  {'-'*6} {'-'*4} {'-'*4} {'-'*7} {'-'*8}")
        for y, st in result["yearly"].items():
            print(f"  {y:<6} {st['n']:>4} {st['positive']:>4} "
                  f"{st['hit_rate_pct']:>6.1f}% {st['mean_pct']:>+7.2f}%")
    print("=" * 68)


def main() -> None:
    # Parse simple CLI args
    total_min = 10.0
    if "--total-min" in sys.argv:
        idx = sys.argv.index("--total-min")
        total_min = float(sys.argv[idx + 1])

    config = RuleConfig(total_min=total_min)
    strategy_name = f"RuleV1 (total>={total_min}x)"

    logger.info("Running backtest: %s", strategy_name)
    result = run(config, strategy_name)
    print_results(result)

    # Save (without per_ipo detail to keep file small)
    out = {k: v for k, v in result.items() if k != "per_ipo"}
    out_path = OUT_DIR / "backtest_rule_v1.json"
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(out, f, indent=2)
    logger.info("Results saved: %s", out_path)


if __name__ == "__main__":
    main()
