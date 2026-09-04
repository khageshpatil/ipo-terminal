"""
Tests for the research CSV loader.

Covers:
- Valid rows load correctly
- Missing required fields cause per-row failure (not crash)
- Malformed values produce warnings, not crashes
- Duplicate ipo_id is detected and skipped
- The 35-record real sample loads without hard failures
- Approximate values (~485) are parsed correctly
- Return percentage values (+29.3%) are parsed correctly
"""

from __future__ import annotations

import csv
import textwrap
from pathlib import Path

import pytest

from ipo_analyzer.data_sources.research_csv import (
    LoadReport,
    ResearchDataset,
    _parse_decimal,
    load_research_csv,
)
from ipo_analyzer.domain.quality import DataQuality

# Path to the real research CSV (relative to repo root, works when pytest run from root)
REAL_CSV = Path("data/research/ipo_universe_confirmed_sample.csv")


# ---------------------------------------------------------------------------
# Unit tests for helper parsers
# ---------------------------------------------------------------------------


class TestParseDecimal:
    def test_plain_number(self) -> None:
        from decimal import Decimal
        assert _parse_decimal("485", "f") == Decimal("485")

    def test_approx_prefix(self) -> None:
        from decimal import Decimal
        assert _parse_decimal("~485", "f") == Decimal("485")

    def test_positive_pct(self) -> None:
        from decimal import Decimal
        val = _parse_decimal("+29.3%", "f")
        assert val is not None
        assert abs(val - Decimal("0.293")) < Decimal("0.0001")

    def test_negative_pct(self) -> None:
        from decimal import Decimal
        val = _parse_decimal("-3.8%", "f")
        assert val is not None
        assert abs(val - Decimal("-0.038")) < Decimal("0.0001")

    def test_missing_sentinel_returns_none(self) -> None:
        assert _parse_decimal("UNKNOWN", "f") is None
        assert _parse_decimal("NOT_CONFIRMED", "f") is None
        assert _parse_decimal("", "f") is None

    def test_invalid_string_returns_none(self) -> None:
        assert _parse_decimal("not_a_number", "f") is None


# ---------------------------------------------------------------------------
# CSV loader tests using synthetic CSVs
# ---------------------------------------------------------------------------


def _write_csv(tmp_path: Path, rows: list[dict]) -> Path:
    """Write a minimal CSV with the required columns for testing."""
    headers = [
        "ipo_id", "company_name", "nse_symbol_approx", "exchange", "year",
        "open_date_approx", "close_date_approx", "listing_date",
        "issue_price_inr", "listing_open_inr_approx", "listing_return_pct_approx",
        "issue_size_type", "sebi_nii_regime", "timeline_regime",
        "source_issue_price", "source_listing_price",
        "data_quality_issue_price", "data_quality_listing_price", "notes",
    ]
    path = tmp_path / "test.csv"
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        for row in rows:
            # Fill missing columns with UNKNOWN
            full_row = {h: row.get(h, "UNKNOWN") for h in headers}
            writer.writerow(full_row)
    return path


def _valid_row(ipo_id: str = "1") -> dict:
    return {
        "ipo_id": str(ipo_id),
        "company_name": f"Test Company {ipo_id}",
        "nse_symbol_approx": f"TEST{ipo_id}",
        "exchange": "NSE+BSE",
        "year": "2021",
        "close_date_approx": "2021-07-16",
        "listing_date": "2021-07-23",
        "issue_price_inr": "100",
        "listing_open_inr_approx": "130",
        "listing_return_pct_approx": "+30.0%",
        "sebi_nii_regime": "PRE_2022",
        "timeline_regime": "T6",
        "data_quality_issue_price": "SECONDARY_VERIFIED",
        "data_quality_listing_price": "SECONDARY_VERIFIED",
        "notes": "",
    }


class TestValidRows:
    def test_single_valid_row(self, tmp_path: Path) -> None:
        path = _write_csv(tmp_path, [_valid_row("A")])
        ds = load_research_csv(path)
        assert ds.n_ipos == 1
        assert ds.n_with_outcome == 1
        assert ds.report.rows_succeeded == 1
        assert ds.report.rows_failed == 0

    def test_listing_return_computed_from_prices(self, tmp_path: Path) -> None:
        path = _write_csv(tmp_path, [_valid_row("A")])
        ds = load_research_csv(path)
        outcome = ds.outcomes[0]
        # issue=100, listing=130 → return=0.30
        from decimal import Decimal
        assert abs(outcome.listing_return - Decimal("0.30")) < Decimal("0.001")

    def test_positive_listing_flag(self, tmp_path: Path) -> None:
        path = _write_csv(tmp_path, [_valid_row("A")])
        ds = load_research_csv(path)
        assert ds.outcomes[0].positive_listing is True

    def test_listing_quality_is_secondary(self, tmp_path: Path) -> None:
        path = _write_csv(tmp_path, [_valid_row("A")])
        ds = load_research_csv(path)
        assert ds.outcomes[0].listing_price_quality == DataQuality.SECONDARY_VERIFIED


class TestMissingRequiredFields:
    def test_missing_ipo_id_fails_row(self, tmp_path: Path) -> None:
        row = _valid_row("A")
        row["ipo_id"] = ""
        path = _write_csv(tmp_path, [row])
        ds = load_research_csv(path)
        assert ds.n_ipos == 0
        assert ds.report.rows_failed == 1

    def test_missing_company_name_fails_row(self, tmp_path: Path) -> None:
        row = _valid_row("A")
        row["company_name"] = ""
        path = _write_csv(tmp_path, [row])
        ds = load_research_csv(path)
        assert ds.n_ipos == 0
        assert ds.report.rows_failed == 1

    def test_missing_issue_price_fails_row(self, tmp_path: Path) -> None:
        row = _valid_row("A")
        row["issue_price_inr"] = "UNKNOWN"
        path = _write_csv(tmp_path, [row])
        ds = load_research_csv(path)
        assert ds.n_ipos == 0

    def test_missing_listing_date_fails_row(self, tmp_path: Path) -> None:
        row = _valid_row("A")
        row["listing_date"] = "UNKNOWN"
        path = _write_csv(tmp_path, [row])
        ds = load_research_csv(path)
        assert ds.n_ipos == 0

    def test_missing_listing_price_gives_ipo_without_outcome(self, tmp_path: Path) -> None:
        row = _valid_row("A")
        row["listing_open_inr_approx"] = "UNKNOWN"
        path = _write_csv(tmp_path, [row])
        ds = load_research_csv(path)
        # IPO should load; just no ListingOutcome
        assert ds.n_ipos == 1
        assert ds.n_with_outcome == 0


class TestDuplicateDetection:
    def test_duplicate_ipo_id_skipped(self, tmp_path: Path) -> None:
        rows = [_valid_row("SAME"), _valid_row("SAME")]
        path = _write_csv(tmp_path, rows)
        ds = load_research_csv(path)
        assert ds.n_ipos == 1  # only first loaded
        assert ds.report.rows_skipped_duplicate == 1

    def test_different_ids_both_load(self, tmp_path: Path) -> None:
        rows = [_valid_row("A"), _valid_row("B")]
        path = _write_csv(tmp_path, rows)
        ds = load_research_csv(path)
        assert ds.n_ipos == 2


class TestApproximateValueParsing:
    def test_approx_listing_price_parsed(self, tmp_path: Path) -> None:
        row = _valid_row("A")
        row["listing_open_inr_approx"] = "~130"
        path = _write_csv(tmp_path, [row])
        ds = load_research_csv(path)
        from decimal import Decimal
        assert ds.outcomes[0].listing_price == Decimal("130")

    def test_pct_return_column_is_informational_only(self, tmp_path: Path) -> None:
        """The listing_return_pct_approx column is informational.
        Even if it disagrees with the price, the price is always used."""
        row = _valid_row("A")
        row["listing_open_inr_approx"] = "130"
        row["listing_return_pct_approx"] = "+99.0%"  # disagrees with price
        path = _write_csv(tmp_path, [row])
        ds = load_research_csv(path)
        # Should still load; return computed from price (130/100 - 1 = 0.30)
        assert ds.n_ipos == 1
        assert ds.n_with_outcome == 1
        from decimal import Decimal
        assert abs(ds.outcomes[0].listing_return - Decimal("0.30")) < Decimal("0.001")



class TestFileNotFound:
    def test_missing_file_raises(self) -> None:
        with pytest.raises(FileNotFoundError):
            load_research_csv(Path("/nonexistent/path/file.csv"))


class TestRealSample:
    """Regression tests against the actual 35-record research CSV."""

    @pytest.mark.skipif(
        not REAL_CSV.exists(),
        reason="Real research CSV not present (run from repo root)",
    )
    def test_real_csv_loads_without_hard_failures(self) -> None:
        ds = load_research_csv(REAL_CSV)
        assert ds.n_ipos > 0, "Expected at least 1 IPO from real CSV"
        # The confirmed sample CSV has ~10 rows with UNKNOWN issue_price or
        # listing_date (rows 25-36 represent named examples without confirmed
        # prices). These produce row-level errors (expected), not system crashes.
        # Verify the loader handles them gracefully.
        assert ds.report.rows_attempted == 35
        assert ds.report.rows_succeeded + ds.report.rows_failed == ds.report.rows_attempted
        assert ds.n_ipos == ds.report.rows_succeeded
        # All errors should be data-quality related (not code bugs)
        for err in ds.report.errors:
            assert err.field in ("issue_price_inr", "listing_date", "IssueTerms", "IPO", "ipo_id", "company_name"), (
                f"Unexpected error field: {err.field}: {err.message}"
            )


    @pytest.mark.skipif(
        not REAL_CSV.exists(),
        reason="Real research CSV not present (run from repo root)",
    )
    def test_real_csv_has_expected_count(self) -> None:
        ds = load_research_csv(REAL_CSV)
        # 35 records built; rows 25-28 have UNKNOWN issue_price (named examples
        # without confirmed prices); rows 29-36 have UNKNOWN listing_date.
        # These legitimately fail validation. Expect at least 20 to load.
        assert ds.n_ipos >= 20, f"Expected ≥20 IPOs, got {ds.n_ipos}"

    @pytest.mark.skipif(
        not REAL_CSV.exists(),
        reason="Real research CSV not present (run from repo root)",
    )
    def test_real_csv_outcomes_are_deterministic(self) -> None:
        """Loading twice must produce identical outcomes."""
        ds1 = load_research_csv(REAL_CSV)
        ds2 = load_research_csv(REAL_CSV)
        returns1 = sorted(float(o.listing_return) for o in ds1.outcomes)
        returns2 = sorted(float(o.listing_return) for o in ds2.outcomes)
        assert returns1 == returns2, "Non-deterministic output detected"
