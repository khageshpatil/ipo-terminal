"""
G7 RHP PDF Parsing Prototype.

A minimal, reproducible prototype for extracting structured fundamental data
from Indian Mainboard IPO Red Herring Prospectus (RHP) PDF documents.

Objective: Determine whether programmatic extraction is feasible at scale,
not to build a production pipeline.

Usage:
    uv run python scripts/g7_rhp_prototype.py <path_to_rhp.pdf>

Output:
    - Console summary of extracted fields
    - JSON file with extraction results + confidence scores
"""

from __future__ import annotations

import json
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Optional


# ---------------------------------------------------------------------------
# Extraction targets and confidence levels
# ---------------------------------------------------------------------------

class Confidence:
    HIGH = "HIGH"       # Extracted with exact pattern match from structured text
    MEDIUM = "MEDIUM"   # Extracted with heuristic, needs spot-check
    LOW = "LOW"         # Fragile extraction, likely needs manual review
    FAILED = "FAILED"   # Could not extract


@dataclass
class ExtractionResult:
    """Result for a single extracted field."""
    field_name: str
    value: Optional[str]
    raw_snippet: Optional[str]   # The surrounding text from which value was extracted
    page_hint: Optional[int]     # Page number (1-indexed) where found
    confidence: str
    method: str                  # 'regex', 'table', 'keyword_proximity', 'manual'
    notes: Optional[str] = None


@dataclass
class RHPExtractionReport:
    """Full extraction report for one RHP document."""
    document_path: str
    company_name: Optional[str]
    ipo_year: Optional[int]

    fields: list[ExtractionResult] = field(default_factory=list)
    total_pages: int = 0
    is_text_searchable: bool = True
    extraction_errors: list[str] = field(default_factory=list)

    @property
    def success_rate(self) -> float:
        if not self.fields:
            return 0.0
        succeeded = sum(1 for f in self.fields if f.confidence != Confidence.FAILED)
        return succeeded / len(self.fields)

    @property
    def high_confidence_rate(self) -> float:
        if not self.fields:
            return 0.0
        high = sum(1 for f in self.fields if f.confidence == Confidence.HIGH)
        return high / len(self.fields)


# ---------------------------------------------------------------------------
# Number normalizer for Indian numeric format
# ---------------------------------------------------------------------------

def _normalize_indian_number(text: str) -> Optional[float]:
    """
    Convert Indian number format to float.
    Handles: '1,23,456.78', '₹ 9,375.00 Cr', '(1,234.56)' (negative)
    Returns None if cannot parse.
    """
    if not text:
        return None

    # Remove currency symbol and common units
    text = re.sub(r'[₹$\s]', '', text)
    text = re.sub(r'\s*(Cr|cr|Crore|crore|Lakh|lakh|Mn|mn|Million|million)\s*', '', text)

    # Handle parentheses as negative
    negative = False
    if text.startswith('(') and text.endswith(')'):
        negative = True
        text = text[1:-1]

    # Remove commas (Indian: 1,00,000)
    text = text.replace(',', '')

    try:
        val = float(text)
        return -val if negative else val
    except ValueError:
        return None


# ---------------------------------------------------------------------------
# Text extraction
# ---------------------------------------------------------------------------

def extract_text_pymupdf(pdf_path: Path) -> tuple[list[str], int]:
    """
    Extract page-by-page text using PyMuPDF.
    Returns (list_of_page_texts, total_pages).
    Raises ImportError if pymupdf not installed.
    """
    import pymupdf  # noqa: F401 — PyMuPDF 1.24+

    doc = pymupdf.open(str(pdf_path))
    pages = []
    for page in doc:
        pages.append(page.get_text("text"))
    doc.close()
    return pages, len(pages)


def is_text_searchable(pages: list[str], sample_pages: int = 5) -> bool:
    """Heuristic: if average chars per page < 100, likely scanned."""
    sample = pages[:sample_pages]
    avg_chars = sum(len(p) for p in sample) / max(len(sample), 1)
    return avg_chars > 200


# ---------------------------------------------------------------------------
# Field extractors
# ---------------------------------------------------------------------------

_ISSUE_SIZE_PATTERNS = [
    r'(?:total\s+issue\s+size|issue\s+size)[^\d]*?([\d,]+\.?\d*)\s*(?:cr|crore)',
    r'aggregating\s+(?:up\s+to\s+)?(?:Rs\.?\s*|₹\s*)?([\d,]+\.?\d*)\s*(?:cr|crore)',
    r'(?:Rs\.?|₹)\s*([\d,]+\.?\d*)\s*crores?\s+(?:comprising|consisting)',
]

_FRESH_ISSUE_PATTERNS = [
    r'fresh\s+issue[^\d]*?([\d,]+\.?\d*)\s*(?:cr|crore)',
    r'fresh\s+issue\s+of[^\d]*?([\d,]+\.?\d*)\s*(?:cr|crore)',
]

_OFS_PATTERNS = [
    r'offer\s+for\s+sale[^\d]*?([\d,]+\.?\d*)\s*(?:cr|crore)',
    r'(?:ofs)[^\d]*?([\d,]+\.?\d*)\s*(?:cr|crore)',
]

_REVENUE_PATTERNS = [
    r'(?:revenue\s+from\s+operations|net\s+revenue)[^\d]{0,30}([\d,]+\.?\d*)',
    r'total\s+income[^\d]{0,20}([\d,]+\.?\d*)',
]

_PAT_PATTERNS = [
    r'(?:profit\s+(?:after|for)\s+(?:the\s+)?(?:year|period)|PAT)[^\d]{0,30}([\(\d,]+\.?\d*[\)]?)',
    r'net\s+profit[^\d]{0,30}([\(\d,]+\.?\d*[\)]?)',
]

_PROMOTER_PATTERNS = [
    r'promoter[s\']?\s+(?:hold|own|stake)[^\d]{0,30}([\d.]+)\s*%',
    r'([\d.]+)\s*%\s+(?:of\s+)?(?:the\s+)?post[- ](?:offer|issue|ipo)\s+paid[- ]up\s+(?:equity\s+)?share\s+capital',
]


def _extract_pattern(
    pages: list[str],
    patterns: list[str],
    field_name: str,
    case_insensitive: bool = True,
) -> ExtractionResult:
    """Try each regex pattern across all pages, return first match."""
    flags = re.IGNORECASE if case_insensitive else 0

    for page_idx, text in enumerate(pages):
        for pattern in patterns:
            m = re.search(pattern, text, flags)
            if m:
                raw = text[max(0, m.start() - 40):m.end() + 40].replace('\n', ' ')
                val_str = m.group(1).strip()
                val = _normalize_indian_number(val_str)
                return ExtractionResult(
                    field_name=field_name,
                    value=str(val) if val is not None else val_str,
                    raw_snippet=raw.strip(),
                    page_hint=page_idx + 1,
                    confidence=Confidence.MEDIUM,
                    method="regex",
                )

    return ExtractionResult(
        field_name=field_name,
        value=None,
        raw_snippet=None,
        page_hint=None,
        confidence=Confidence.FAILED,
        method="regex",
        notes="No pattern matched across all pages",
    )


# ---------------------------------------------------------------------------
# Main extraction function
# ---------------------------------------------------------------------------

TARGET_FIELDS = [
    # Issue structure (highest reliability)
    ("issue_size_cr", _ISSUE_SIZE_PATTERNS),
    ("fresh_issue_cr", _FRESH_ISSUE_PATTERNS),
    ("ofs_cr", _OFS_PATTERNS),
    # Financials (medium reliability — depends on table layout)
    ("revenue_cr", _REVENUE_PATTERNS),
    ("pat_cr", _PAT_PATTERNS),
    # Promoter (medium — usually in cover section)
    ("promoter_post_issue_pct", _PROMOTER_PATTERNS),
]


def extract_rhp(pdf_path: Path, company_name: str = "", ipo_year: Optional[int] = None) -> RHPExtractionReport:
    """
    Extract key fundamentals from a single RHP PDF.

    Parameters
    ----------
    pdf_path : Path
        Local path to the RHP PDF.
    company_name : str
        For labelling in the report.
    ipo_year : int, optional
        For labelling in the report.
    """
    report = RHPExtractionReport(
        document_path=str(pdf_path),
        company_name=company_name or pdf_path.stem,
        ipo_year=ipo_year,
    )

    # Try PyMuPDF extraction
    try:
        pages, total_pages = extract_text_pymupdf(pdf_path)
        report.total_pages = total_pages
        report.is_text_searchable = is_text_searchable(pages)
    except Exception as e:
        report.extraction_errors.append(f"Text extraction failed: {e}")
        return report

    if not report.is_text_searchable:
        report.extraction_errors.append(
            "Document appears to be scanned (low text density). OCR required."
        )
        # Add all fields as FAILED
        for field_name, _ in TARGET_FIELDS:
            report.fields.append(ExtractionResult(
                field_name=field_name,
                value=None,
                raw_snippet=None,
                page_hint=None,
                confidence=Confidence.FAILED,
                method="n/a",
                notes="Scanned PDF — OCR required",
            ))
        return report

    # Extract each field
    for field_name, patterns in TARGET_FIELDS:
        result = _extract_pattern(pages, patterns, field_name)
        report.fields.append(result)

    return report


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python g7_rhp_prototype.py <rhp.pdf> [company_name] [year]")
        sys.exit(1)

    pdf_path = Path(sys.argv[1])
    company = sys.argv[2] if len(sys.argv) > 2 else ""
    year = int(sys.argv[3]) if len(sys.argv) > 3 else None

    if not pdf_path.exists():
        print(f"File not found: {pdf_path}")
        sys.exit(1)

    report = extract_rhp(pdf_path, company, year)

    print(f"\n{'='*60}")
    print(f"RHP Extraction Report: {report.company_name}")
    print(f"Pages: {report.total_pages} | Text-searchable: {report.is_text_searchable}")
    print(f"Success rate: {report.success_rate:.0%} | High confidence: {report.high_confidence_rate:.0%}")
    print(f"{'='*60}")

    for f in report.fields:
        status = f"[{f.confidence}]"
        val = f.value or "—"
        snippet = f"  snippet: ...{f.raw_snippet[:60]}..." if f.raw_snippet else ""
        print(f"  {f.field_name:<30} {status:<10} {val}{snippet}")

    if report.extraction_errors:
        print("\nErrors:")
        for e in report.extraction_errors:
            print(f"  {e}")

    # Save JSON
    out_path = pdf_path.with_suffix(".extraction.json")
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(asdict(report), fh, indent=2, default=str)
    print(f"\nJSON saved: {out_path}")


if __name__ == "__main__":
    main()
