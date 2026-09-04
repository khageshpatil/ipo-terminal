"""
run_baseline.py — Phase 3: Apply-Every-IPO baseline on real data.

Loads the universe CSV, computes:
  - Real base rate (positive listing rate)
  - Apply-Every-IPO benchmark stats
  - Year-by-year breakdown

Usage:
    uv run python scripts/run_baseline.py
    uv run python scripts/run_baseline.py --quality PRIMARY_VERIFIED
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ipo_analyzer.data_sources.universe_loader import compute_base_rate, load_universe

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s: %(message)s",
    datefmt="%H:%M:%S",
)

OUT_DIR = Path("data/universe")


def main() -> None:
    quality = "SECONDARY_VERIFIED"
    if "--quality" in sys.argv:
        idx = sys.argv.index("--quality")
        quality = sys.argv[idx + 1] if idx + 1 < len(sys.argv) else quality

    print(f"\nLoading universe (min quality: {quality})...")
    ipos = load_universe(min_quality=quality)

    if not ipos:
        print("No records loaded. Run scripts/build_universe.py first.")
        sys.exit(1)

    result = compute_base_rate(ipos)

    print("\n" + "=" * 64)
    print("APPLY-EVERY-IPO BASELINE — REAL HISTORICAL DATA")
    print("[!] Source: Chittorgarh RSC data + NSE Bhav Copy listing prices")
    print("[!] This is historical in-sample analysis — not out-of-sample backtest")
    print("=" * 64)
    print(f"  Total IPOs in universe:        {result['total_ipos']}")
    print(f"  Usable (price + date + close): {result['usable_ipos']}")
    print(f"  Positive listings:             {result['positive_listings']}")
    print(f"  Negative listings:             {result['negative_listings']}")
    print(f"  Positive rate:                 {result['positive_rate_pct']}%")
    print(f"  Mean listing return:           {result['mean_return_pct']:+.2f}%")
    print(f"  Median listing return:         {result['median_return_pct']:+.2f}%")
    print(f"  Max gain:                      {result['max_gain_pct']:+.2f}%")
    print(f"  Max loss:                      {result['max_loss_pct']:+.2f}%")
    print(f"  Std dev of returns:            {result['std_return_pct']:.2f}%")
    print()
    print("  Year-by-year breakdown:")
    print(f"  {'Year':<6} {'N':>4} {'Pos':>4} {'Rate':>7} {'Mean Ret':>10}")
    print(f"  {'-'*6} {'-'*4} {'-'*4} {'-'*7} {'-'*10}")
    for y, stats in result.get("by_year", {}).items():
        print(f"  {y:<6} {stats['n']:>4} {stats['positive']:>4} "
              f"{stats['positive_rate_pct']:>6.1f}% {stats['mean_return_pct']:>+9.2f}%")
    print("=" * 64)

    # Save
    out_path = OUT_DIR / "baseline_results.json"
    with open(out_path, "w") as f:
        json.dump(result, f, indent=2)
    print(f"\nResults saved: {out_path}")

    # Coverage by quality
    pv = sum(1 for r in ipos if r.listing_open_quality == "PRIMARY_VERIFIED")
    sv = sum(1 for r in ipos if r.listing_open_quality == "SECONDARY_VERIFIED")
    miss = sum(1 for r in ipos if r.listing_open_quality == "MISSING")
    print(f"\nData quality coverage:")
    print(f"  PRIMARY_VERIFIED:   {pv}")
    print(f"  SECONDARY_VERIFIED: {sv}")
    print(f"  MISSING:            {miss}")


if __name__ == "__main__":
    main()
