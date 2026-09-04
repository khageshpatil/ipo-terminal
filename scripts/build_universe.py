"""
build_universe.py — Phase 2 dataset pipeline entry point.

Usage:
    uv run python scripts/build_universe.py [--years 2018-2024] [--skip-bhav] [--skip-scrape]

Steps:
  1. Scrape InvestorGain (primary) + Chittorgarh (secondary) for IPO universe
  2. Merge, deduplicate, filter to Mainboard 2018-2024
  3. Fetch NSE Bhav Copy listing prices (PRIMARY_VERIFIED)
  4. Write data/universe/ipo_universe_2018_2024.csv
  5. Print quality report
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

# Add src to path for direct execution
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ipo_analyzer.collectors.bhav_copy import fetch_listing_prices
from ipo_analyzer.collectors.chittorgarh import scrape_chittorgarh
from ipo_analyzer.collectors.investorgain import scrape_investorgain
from ipo_analyzer.collectors.universe_builder import (
    build_universe_csv,
    generate_quality_report,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("build_universe")

YEARS = list(range(2018, 2025))   # 2018–2024
OUT_CSV = Path("data/universe/ipo_universe_2018_2024.csv")
REPORT_JSON = Path("data/universe/collection_report.json")


def main() -> None:
    skip_scrape = "--skip-scrape" in sys.argv
    skip_bhav = "--skip-bhav" in sys.argv

    all_records = []

    # -------------------------------------------------------------------------
    # Step 1 — Scrape
    # -------------------------------------------------------------------------
    if not skip_scrape:
        logger.info("=== Step 1: Scraping IPO universe ===")

        # Try InvestorGain first
        logger.info("Trying InvestorGain...")
        ig_records, ig_report = scrape_investorgain(YEARS, delay_seconds=2.0)
        logger.info(
            "InvestorGain: %d records, %d errors",
            ig_report.records_collected,
            len(ig_report.errors),
        )
        if ig_report.errors:
            for e in ig_report.errors[:5]:
                logger.warning("  IG error: %s", e)
        all_records.extend(ig_records)

        # Try Chittorgarh (supplement / cross-validate)
        logger.info("Trying Chittorgarh...")
        cg_records, cg_report = scrape_chittorgarh(YEARS, delay_seconds=2.0)
        logger.info(
            "Chittorgarh: %d records, %d errors",
            cg_report.records_collected,
            len(cg_report.errors),
        )
        if cg_report.errors:
            for e in cg_report.errors[:5]:
                logger.warning("  CG error: %s", e)
        all_records.extend(cg_records)

        logger.info("Total raw records: %d", len(all_records))

        if not all_records:
            logger.error(
                "No records scraped from any source. "
                "Sites may be blocking or requiring JS. "
                "Try running with --skip-scrape and manually placing data."
            )
            sys.exit(1)
    else:
        # Load existing CSV if skipping scrape
        if OUT_CSV.exists():
            import pandas as pd
            logger.info("--skip-scrape: loading existing %s", OUT_CSV)
            # We still need raw records for bhav lookup
            # Convert CSV rows back to RawIPORecord for bhav step
            from ipo_analyzer.collectors.models import RawIPORecord
            from datetime import date
            df = pd.read_csv(OUT_CSV)
            for _, row in df.iterrows():
                def _d(v: str):
                    try:
                        return date.fromisoformat(str(v)) if v and str(v) != "nan" else None
                    except Exception:
                        return None
                def _f(v):
                    try:
                        return float(v) if v and str(v) not in ("nan", "") else None
                    except Exception:
                        return None
                rec = RawIPORecord(
                    company_name=str(row.get("company_name", "")),
                    nse_symbol=str(row["nse_symbol"]) if row.get("nse_symbol") else None,
                    listing_date=_d(row.get("listing_date")),
                    close_date=_d(row.get("close_date")),
                    open_date=_d(row.get("open_date")),
                    issue_price=_f(row.get("issue_price")),
                    source=str(row.get("source", "CSV")),
                )
                bhav_q = str(row.get("listing_open_quality", ""))
                if bhav_q == "PRIMARY_VERIFIED" and row.get("listing_open_price"):
                    rec.bhav_listing_open = _f(row.get("listing_open_price"))
                elif row.get("listing_open_price"):
                    rec.listing_open_approx = _f(row.get("listing_open_price"))
                all_records.append(rec)
        else:
            logger.error("--skip-scrape but no existing CSV found at %s", OUT_CSV)
            sys.exit(1)

    # -------------------------------------------------------------------------
    # Step 2 — Build intermediate universe (needed before Bhav Copy)
    # -------------------------------------------------------------------------
    logger.info("=== Step 2: Building intermediate universe ===")
    df = build_universe_csv(all_records, output_path=OUT_CSV)
    logger.info("Intermediate universe: %d rows", len(df))

    # -------------------------------------------------------------------------
    # Step 3 — Bhav Copy listing prices
    # -------------------------------------------------------------------------
    if not skip_bhav:
        logger.info("=== Step 3: Fetching NSE Bhav Copy listing prices ===")
        # Only fetch for records that don't already have PRIMARY_VERIFIED
        needs_bhav = [
            r for r in all_records
            if r.nse_symbol and r.listing_date and r.bhav_listing_open is None
        ]
        logger.info("%d records need Bhav Copy lookup", len(needs_bhav))

        if needs_bhav:
            fetch_listing_prices(needs_bhav, delay_seconds=1.0, use_cache=True)
            ok = sum(1 for r in needs_bhav if r.bhav_listing_open is not None)
            logger.info("Bhav Copy: %d/%d succeeded", ok, len(needs_bhav))

        # Rebuild CSV with Bhav prices included
        logger.info("=== Step 3b: Rebuilding universe with Bhav prices ===")
        df = build_universe_csv(all_records, output_path=OUT_CSV)
    else:
        logger.info("--skip-bhav: skipping NSE Bhav Copy step")

    # -------------------------------------------------------------------------
    # Step 4 — Quality report
    # -------------------------------------------------------------------------
    logger.info("=== Step 4: Quality report ===")
    report = generate_quality_report(df)

    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    with open(REPORT_JSON, "w") as f:
        json.dump(report, f, indent=2)

    print("\n" + "=" * 60)
    print("DATASET QUALITY REPORT")
    print("=" * 60)
    print(f"  Total IPOs discovered:        {report['total_ipos_discovered']}")
    print(f"  Usable IPOs:                  {report['usable_ipos']}")
    print(f"  PRIMARY_VERIFIED listing:     {report['primary_verified_listing_price']}")
    print(f"  SECONDARY_VERIFIED listing:   {report['secondary_verified_listing_price']}")
    print(f"  Missing listing price:        {report['missing_listing_price']}")
    print(f"  With subscription data:       {report['with_subscription_data']}")
    print(f"  Missing issue price:          {report['missing_issue_price']}")
    print(f"  Missing close date:           {report['missing_close_date']}")
    print("=" * 60)
    if report["usable_ipos"] and report["usable_ipos"] > 0:
        print(f"  Positive listing rate:        {report['positive_listing_rate_pct']}%")
        print(f"  Mean listing return:          {report['mean_listing_return_pct']}%")
    print("=" * 60)
    print(f"\nCSV: {OUT_CSV}")
    print(f"Report: {REPORT_JSON}")


if __name__ == "__main__":
    main()
