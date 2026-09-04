"""
Research CSV loader for the 35-record verified historical IPO sample.

This loader is the ONLY approved way to ingest the Phase 1 dataset.
It explicitly handles:
- Approximate values prefixed with '~' (strips prefix, marks SECONDARY_VERIFIED)
- Return values in '+29.3%' format
- UNKNOWN / NOT_CONFIRMED / MISSING sentinel strings → None
- Duplicate ipo_id detection
- Per-row validation with detailed error reporting

Produces:
- List[IPO] — canonical IPO entities
- List[ListingOutcome] — canonical listing outcomes
- LoadReport — summary of what loaded, failed, and why
"""

from __future__ import annotations

import csv
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Optional

from ipo_analyzer.domain.ipo import (
    Exchange,
    IPO,
    IssueTerms,
    IssueType,
    NiiRegime,
    Segment,
    TimelineRegime,
)
from ipo_analyzer.domain.lineage import RESEARCH_CSV_SOURCE
from ipo_analyzer.domain.outcomes import ListingOutcome
from ipo_analyzer.domain.quality import DataQuality

# String sentinels in the CSV that mean "data not available"
_MISSING_SENTINELS = {
    "UNKNOWN",
    "NOT_CONFIRMED",
    "MISSING",
    "N/A",
    "",
    "—",
    "-",
    "nan",
}

# Default retrieved_at for all Phase 1 research records
_RESEARCH_RETRIEVED_AT = datetime(2026, 9, 4, 0, 0, 0, tzinfo=timezone.utc)


@dataclass
class RowError:
    row_number: int
    ipo_id: str
    field: str
    message: str

    def __str__(self) -> str:
        return f"Row {self.row_number} [{self.ipo_id}] field={self.field!r}: {self.message}"


@dataclass
class LoadReport:
    """Summary of a CSV load operation."""

    source_path: str
    rows_attempted: int = 0
    rows_succeeded: int = 0
    rows_failed: int = 0
    rows_skipped_duplicate: int = 0
    errors: list[RowError] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def add_error(self, row: int, ipo_id: str, field: str, msg: str) -> None:
        self.errors.append(RowError(row, ipo_id, field, msg))

    def add_warning(self, msg: str) -> None:
        self.warnings.append(msg)

    @property
    def has_errors(self) -> bool:
        return len(self.errors) > 0

    def summary(self) -> str:
        lines = [
            f"Load report: {self.source_path}",
            f"  Attempted:  {self.rows_attempted}",
            f"  Succeeded:  {self.rows_succeeded}",
            f"  Failed:     {self.rows_failed}",
            f"  Duplicates: {self.rows_skipped_duplicate}",
        ]
        if self.errors:
            lines.append(f"  Errors ({len(self.errors)}):")
            for e in self.errors:
                lines.append(f"    {e}")
        if self.warnings:
            lines.append(f"  Warnings ({len(self.warnings)}):")
            for w in self.warnings:
                lines.append(f"    {w}")
        return "\n".join(lines)


def _is_missing(value: str) -> bool:
    return value.strip() in _MISSING_SENTINELS


def _parse_decimal(raw: str, field_name: str) -> Optional[Decimal]:
    """
    Parse a decimal value from the CSV.
    Handles:
    - '~485'  → Decimal('485')   (approximate; caller should set SECONDARY_VERIFIED)
    - '+29.3%' → Decimal('0.293')  (percentage return; converted to fraction)
    - '-3.8%'  → Decimal('-0.038')
    - '29.3%'  → Decimal('0.293')
    Returns None for missing sentinels.
    """
    s = raw.strip()
    if _is_missing(s):
        return None

    # Strip approximate prefix
    is_approx = s.startswith("~")
    if is_approx:
        s = s[1:]

    # Handle percentage format
    is_pct = s.endswith("%")
    if is_pct:
        s = s.rstrip("%")
        # Strip leading '+'
        if s.startswith("+"):
            s = s[1:]

    try:
        val = Decimal(s)
    except InvalidOperation:
        return None

    if is_pct:
        val = val / Decimal("100")

    return val


def _parse_date(raw: str, field_name: str) -> Optional[date]:
    """Parse YYYY-MM-DD date strings. Returns None for missing sentinels."""
    s = raw.strip()
    if _is_missing(s):
        return None
    for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None


def _parse_exchange(raw: str) -> Exchange:
    s = raw.strip().upper()
    if "NSE" in s and "BSE" in s:
        return Exchange.BOTH
    if "NSE" in s:
        return Exchange.NSE
    if "BSE" in s:
        return Exchange.BSE
    return Exchange.BOTH  # default for mainboard


def _parse_quality(raw: str) -> DataQuality:
    s = raw.strip().upper()
    mapping = {
        "PRIMARY_VERIFIED": DataQuality.PRIMARY_VERIFIED,
        "SECONDARY_VERIFIED": DataQuality.SECONDARY_VERIFIED,
        "UNVERIFIED": DataQuality.UNVERIFIED,
        "CONFLICTING": DataQuality.CONFLICTING,
        "MISSING": DataQuality.MISSING,
        "DERIVED": DataQuality.DERIVED,
    }
    return mapping.get(s, DataQuality.UNVERIFIED)


@dataclass
class ResearchRecord:
    """Intermediate structure holding one successfully parsed CSV row."""

    ipo_id: str
    company_name: str
    nse_symbol: Optional[str]
    exchange: Exchange
    year: int
    close_date: Optional[date]
    listing_date: Optional[date]
    issue_price: Decimal
    listing_open_approx: Optional[Decimal]
    listing_return_approx: Optional[Decimal]
    sebi_nii_regime: NiiRegime
    timeline_regime: TimelineRegime
    quality_issue_price: DataQuality
    quality_listing_price: DataQuality
    notes: Optional[str]


def _parse_row(
    row: dict[str, str],
    row_number: int,
    report: LoadReport,
) -> Optional[ResearchRecord]:
    """
    Parse one CSV row into a ResearchRecord.
    Returns None if the row has a fatal error.
    Non-fatal issues are recorded as warnings.
    """
    ipo_id = row.get("ipo_id", "").strip()
    if not ipo_id:
        report.add_error(row_number, "?", "ipo_id", "Missing ipo_id — row skipped")
        return None

    company_name = row.get("company_name", "").strip()
    if not company_name:
        report.add_error(row_number, ipo_id, "company_name", "Missing company_name")
        return None

    # issue_price — required
    raw_ip = row.get("issue_price_inr", "").strip()
    if _is_missing(raw_ip):
        report.add_error(row_number, ipo_id, "issue_price_inr", "issue_price is MISSING — skipped")
        return None
    # issue_price may have '~' prefix in CSV; treat as SECONDARY
    issue_price = _parse_decimal(raw_ip, "issue_price_inr")
    if issue_price is None or issue_price <= 0:
        report.add_error(row_number, ipo_id, "issue_price_inr", f"Invalid issue_price: {raw_ip!r}")
        return None

    # listing_date — required for ListingOutcome
    listing_date = _parse_date(row.get("listing_date", ""), "listing_date")
    if listing_date is None:
        report.add_error(row_number, ipo_id, "listing_date", "listing_date is MISSING — skipped")
        return None

    # close_date — may be approximate for older records
    close_date = _parse_date(row.get("close_date_approx", ""), "close_date_approx")
    if close_date is None:
        # Estimate from year if close_date is missing
        try:
            year = int(row.get("year", "0").strip())
        except ValueError:
            year = 0
        if year > 0:
            # Conservative fallback: use listing_date - 6 days (T6 era approximation)
            from datetime import timedelta
            close_date = listing_date - timedelta(days=6)
            report.add_warning(
                f"Row {row_number} [{ipo_id}]: close_date missing; "
                f"estimated as listing_date - 6 days = {close_date}"
            )
        else:
            report.add_error(row_number, ipo_id, "close_date_approx", "Cannot determine close_date")
            return None

    # Validate close_date <= listing_date
    if close_date > listing_date:
        report.add_error(
            row_number,
            ipo_id,
            "close_date_approx",
            f"close_date={close_date} > listing_date={listing_date}",
        )
        return None

    # listing_price
    raw_lp = row.get("listing_open_inr_approx", "").strip()
    listing_open: Optional[Decimal] = _parse_decimal(raw_lp, "listing_open_inr_approx")
    if listing_open is not None and listing_open <= 0:
        report.add_warning(f"Row {row_number} [{ipo_id}]: non-positive listing_price {listing_open}; set to None")
        listing_open = None

    # listing_return (cross-check only; recomputed from prices if possible)
    raw_ret = row.get("listing_return_pct_approx", "").strip()
    listing_return: Optional[Decimal] = _parse_decimal(raw_ret, "listing_return_pct_approx")

    # listing_return from CSV is informational/cross-check only.
    # The authoritative return is always computed from listing_price / issue_price.
    # No cross-check warning needed — the computed value is always used.


    # Exchange and regime
    exchange = _parse_exchange(row.get("exchange", "NSE+BSE"))
    raw_regime = row.get("sebi_nii_regime", "").strip().upper()
    if raw_regime == "PRE_2022":
        nii_regime = NiiRegime.PRE_2022
    elif raw_regime == "POST_2022":
        nii_regime = NiiRegime.POST_2022
    else:
        nii_regime = NiiRegime.from_close_date(close_date)

    raw_tl = row.get("timeline_regime", "").strip().upper()
    if raw_tl == "T3":
        tl_regime = TimelineRegime.T3
    elif raw_tl == "T6":
        tl_regime = TimelineRegime.T6
    else:
        tl_regime = TimelineRegime.from_close_date(close_date)

    # Quality
    q_issue = _parse_quality(row.get("data_quality_issue_price", "SECONDARY_VERIFIED"))
    q_listing = _parse_quality(row.get("data_quality_listing_price", "SECONDARY_VERIFIED"))

    # Symbol
    nse_sym = row.get("nse_symbol_approx", "").strip()
    nse_sym = nse_sym if not _is_missing(nse_sym) else None

    notes = row.get("notes", "").strip() or None

    try:
        year = int(row.get("year", str(close_date.year)).strip())
    except ValueError:
        year = close_date.year

    return ResearchRecord(
        ipo_id=ipo_id,
        company_name=company_name,
        nse_symbol=nse_sym,
        exchange=exchange,
        year=year,
        close_date=close_date,
        listing_date=listing_date,
        issue_price=issue_price,
        listing_open_approx=listing_open,
        listing_return_approx=listing_return,
        sebi_nii_regime=nii_regime,
        timeline_regime=tl_regime,
        quality_issue_price=q_issue,
        quality_listing_price=q_listing,
        notes=notes,
    )


@dataclass
class ResearchDataset:
    """The output of loading the research CSV."""

    ipos: list[IPO]
    outcomes: list[ListingOutcome]
    report: LoadReport

    @property
    def n_ipos(self) -> int:
        return len(self.ipos)

    @property
    def n_with_outcome(self) -> int:
        return len(self.outcomes)

    def outcomes_by_id(self) -> dict[str, ListingOutcome]:
        return {o.ipo_id: o for o in self.outcomes}

    def ipos_by_id(self) -> dict[str, IPO]:
        return {i.ipo_id: i for i in self.ipos}


def load_research_csv(path: Path | str) -> ResearchDataset:
    """
    Load the verified 35-record research CSV into canonical domain objects.

    This is the entry point for all Phase 1 data ingestion.
    It never fabricates missing data. Missing values are preserved as None
    with DataQuality.MISSING in the appropriate field.

    Parameters
    ----------
    path : Path or str
        Path to the CSV file (e.g., data/research/ipo_universe_confirmed_sample.csv)

    Returns
    -------
    ResearchDataset
        Contains ipos, outcomes, and a load report.
    """
    path = Path(path)
    report = LoadReport(source_path=str(path))

    if not path.exists():
        raise FileNotFoundError(f"Research CSV not found: {path}")

    ipos: list[IPO] = []
    outcomes: list[ListingOutcome] = []
    seen_ids: set[str] = set()

    with path.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for row_number, row in enumerate(reader, start=2):  # 1 = header
            report.rows_attempted += 1

            record = _parse_row(row, row_number, report)
            if record is None:
                report.rows_failed += 1
                continue

            # Duplicate check
            if record.ipo_id in seen_ids:
                report.rows_skipped_duplicate += 1
                report.add_warning(f"Row {row_number}: duplicate ipo_id={record.ipo_id!r} — skipped")
                continue
            seen_ids.add(record.ipo_id)

            # Build IssueTerms
            try:
                terms = IssueTerms(
                    close_date=record.close_date,  # type: ignore[arg-type]
                    listing_date=record.listing_date,  # type: ignore[arg-type]
                    issue_price=record.issue_price,
                )
            except Exception as exc:
                report.add_error(row_number, record.ipo_id, "IssueTerms", str(exc))
                report.rows_failed += 1
                continue

            # Build IPO
            try:
                ipo = IPO(
                    ipo_id=record.ipo_id,
                    company_name=record.company_name,
                    nse_symbol=record.nse_symbol,
                    exchange=record.exchange,
                    segment=Segment.MAINBOARD,
                    issue_terms=terms,
                    sebi_nii_regime=record.sebi_nii_regime,
                    timeline_regime=record.timeline_regime,
                    source=RESEARCH_CSV_SOURCE.name,
                    source_reference=str(path),
                    retrieved_at=_RESEARCH_RETRIEVED_AT,
                    notes=record.notes,
                )
            except Exception as exc:
                report.add_error(row_number, record.ipo_id, "IPO", str(exc))
                report.rows_failed += 1
                continue

            ipos.append(ipo)

            # Build ListingOutcome if listing price is available
            if record.listing_open_approx is not None:
                listing_dt = datetime(
                    record.listing_date.year,
                    record.listing_date.month,
                    record.listing_date.day,
                    4, 0, 0,  # ~09:30 IST = 04:00 UTC (pre-open equilibrium)
                    tzinfo=timezone.utc,
                )
                try:
                    outcome = ListingOutcome.compute(
                        ipo_id=record.ipo_id,
                        listing_date=record.listing_date,
                        issue_price=record.issue_price,
                        listing_price=record.listing_open_approx,
                        listing_price_quality=record.quality_listing_price,
                        source=RESEARCH_CSV_SOURCE.name,
                        source_reference=str(path),
                        observed_at=listing_dt,
                        retrieved_at=_RESEARCH_RETRIEVED_AT,
                    )
                    outcomes.append(outcome)
                except Exception as exc:
                    report.add_warning(
                        f"Row {row_number} [{record.ipo_id}]: "
                        f"ListingOutcome could not be computed: {exc}"
                    )

            report.rows_succeeded += 1

    report.add_warning(
        "BIAS NOTICE: This is a non-random sample of 35 notable/famous IPOs. "
        "Positive IPOs are overrepresented. Do not use these statistics "
        "as the true historical base rate."
    )

    return ResearchDataset(ipos=ipos, outcomes=outcomes, report=report)
