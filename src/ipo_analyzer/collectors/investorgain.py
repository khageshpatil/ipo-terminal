"""
InvestorGain scraper — historical IPO performance data.

URL: https://www.investorgain.com/report/ipo-performance-history/ipo_performance.asp
     (supports ?year=YYYY or paginated)

The performance history table has:
  Company | Type | Size | Issue Price | Listing Open | Return% | QIB | NII | Retail | Total
"""

from __future__ import annotations

import logging
import re
import time
from datetime import date, datetime, timezone
from typing import Optional

from bs4 import BeautifulSoup

from .models import CollectionReport, RawIPORecord

logger = logging.getLogger(__name__)

_BASE_URL = "https://www.investorgain.com/report/ipo-performance-history/ipo_performance.asp"
_DETAIL_BASE = "https://www.investorgain.com"

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.investorgain.com/",
}


def _get_session():
    """Return a requests-like session with browser impersonation."""
    try:
        from curl_cffi import requests as cffi_requests
        session = cffi_requests.Session(impersonate="chrome124")
        return session, "curl_cffi"
    except Exception:
        import requests
        session = requests.Session()
        session.headers.update(_HEADERS)
        return session, "requests"


def _parse_float(s: str) -> Optional[float]:
    if not s:
        return None
    s = s.strip().replace(",", "").replace("₹", "").replace("%", "").replace("x", "").strip()
    if s in ("-", "—", "N/A", "NA", ""):
        return None
    # Handle parentheses as negative
    if s.startswith("(") and s.endswith(")"):
        s = "-" + s[1:-1]
    try:
        return float(s)
    except ValueError:
        return None


def _parse_date_str(s: str) -> Optional[date]:
    """Parse dates in formats: 'DD-Mon-YYYY', 'DD/MM/YYYY', 'YYYY-MM-DD'."""
    if not s:
        return None
    s = s.strip()
    for fmt in ("%d-%b-%Y", "%d/%m/%Y", "%Y-%m-%d", "%b %d, %Y", "%d %b %Y"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None


def _fetch_page(session, url: str, params: Optional[dict] = None) -> Optional[str]:
    """Fetch a page, return HTML text or None on failure."""
    try:
        resp = session.get(url, params=params, timeout=30)
        if resp.status_code == 200:
            return resp.text
        logger.warning("HTTP %d for %s", resp.status_code, url)
        return None
    except Exception as e:
        logger.error("Fetch error for %s: %s", url, e)
        return None


def _parse_investorgain_table(html: str, year: int, report: CollectionReport) -> list[RawIPORecord]:
    """Parse the main performance history table from InvestorGain HTML."""
    soup = BeautifulSoup(html, "lxml")
    records: list[RawIPORecord] = []

    # Find all tables — look for one with relevant headers
    tables = soup.find_all("table")
    target_table = None
    for tbl in tables:
        headers_text = tbl.get_text().lower()
        if "issue price" in headers_text and ("listing" in headers_text or "gain" in headers_text):
            target_table = tbl
            break

    if not target_table:
        # Try looking for a div/section with tabular data
        report.add_warning(f"Year {year}: no table found in InvestorGain response")
        return records

    rows = target_table.find_all("tr")
    header_row = None
    col_map: dict[str, int] = {}

    for row in rows:
        cells = row.find_all(["th", "td"])
        cell_texts = [c.get_text(strip=True).lower() for c in cells]
        # Detect header row
        if any("issue price" in t for t in cell_texts):
            header_row = cells
            for i, txt in enumerate(cell_texts):
                if "company" in txt or "name" in txt:
                    col_map["name"] = i
                elif "issue price" in txt:
                    col_map["issue_price"] = i
                elif "listing" in txt and "open" in txt:
                    col_map["listing_open"] = i
                elif "listing" in txt and ("price" in txt or "gain" in txt or "return" in txt):
                    col_map.setdefault("listing_open", i)
                elif "gain" in txt or "return" in txt:
                    col_map["return_pct"] = i
                elif "qib" in txt:
                    col_map["qib"] = i
                elif "nii" in txt or "hni" in txt:
                    col_map["nii"] = i
                elif "retail" in txt:
                    col_map["retail"] = i
                elif "total" in txt:
                    col_map["total"] = i
                elif "type" in txt:
                    col_map["type"] = i
                elif "size" in txt or "amount" in txt:
                    col_map["size"] = i
                elif "open" in txt and "date" in txt:
                    col_map["open_date"] = i
                elif "close" in txt and "date" in txt:
                    col_map["close_date"] = i
                elif "listing" in txt and "date" in txt:
                    col_map["listing_date"] = i
                elif "symbol" in txt:
                    col_map["symbol"] = i
                elif "lot" in txt:
                    col_map["lot_size"] = i
            continue  # skip header row

        if not col_map or not cells:
            continue

        # Try to extract data row
        def _cell(key: str) -> str:
            idx = col_map.get(key)
            if idx is None or idx >= len(cells):
                return ""
            return cells[idx].get_text(strip=True)

        name = _cell("name")
        if not name or name.lower() in ("", "company", "ipo name", "-"):
            continue

        # Filter: only Mainboard (skip SME)
        ipo_type = _cell("type").upper()
        if ipo_type and "SME" in ipo_type:
            continue

        scraped_at = datetime.now(timezone.utc).isoformat()

        rec = RawIPORecord(
            company_name=name,
            nse_symbol=_cell("symbol") or None,
            issue_price=_parse_float(_cell("issue_price")),
            listing_open_approx=_parse_float(_cell("listing_open")),
            listing_return_pct=_parse_float(_cell("return_pct")),
            subscription_qib_x=_parse_float(_cell("qib")),
            subscription_nii_x=_parse_float(_cell("nii")),
            subscription_retail_x=_parse_float(_cell("retail")),
            subscription_total_x=_parse_float(_cell("total")),
            issue_size_cr=_parse_float(_cell("size")),
            lot_size=int(_parse_float(_cell("lot_size")) or 0) or None,
            open_date=_parse_date_str(_cell("open_date")),
            close_date=_parse_date_str(_cell("close_date")),
            listing_date=_parse_date_str(_cell("listing_date")),
            source="INVESTORGAIN",
            source_url=f"{_BASE_URL}?year={year}",
            scraped_at=scraped_at,
        )
        records.append(rec)

    return records


def scrape_investorgain(
    years: list[int],
    delay_seconds: float = 2.0,
) -> tuple[list[RawIPORecord], CollectionReport]:
    """
    Scrape InvestorGain IPO performance history for the given years.

    Parameters
    ----------
    years : list[int]
        List of years to scrape, e.g. [2018, 2019, 2020, 2021, 2022, 2023, 2024]
    delay_seconds : float
        Delay between requests (be polite).

    Returns
    -------
    (list of RawIPORecord, CollectionReport)
    """
    session, session_type = _get_session()
    report = CollectionReport(source="INVESTORGAIN", years_requested=years)
    logger.info("InvestorGain scraper using %s", session_type)

    all_records: list[RawIPORecord] = []

    for year in years:
        logger.info("Fetching InvestorGain year %d...", year)
        html = _fetch_page(session, _BASE_URL, params={"year": str(year)})
        if not html:
            # Try without year param (get all, filter by year from dates)
            html = _fetch_page(session, _BASE_URL)
        if not html:
            report.add_error(f"Year {year}: failed to fetch page")
            report.records_failed += 1
            continue

        records = _parse_investorgain_table(html, year, report)

        if not records:
            # Try alternative: fetch with 'rtype' param or other filters
            html2 = _fetch_page(session, _BASE_URL, params={"year": str(year), "rtype": "mainboard"})
            if html2:
                records = _parse_investorgain_table(html2, year, report)

        if records:
            logger.info("Year %d: collected %d records", year, len(records))
            report.records_collected += len(records)
            all_records.extend(records)
        else:
            report.add_warning(f"Year {year}: zero records parsed (page may require JS rendering)")
            report.records_failed += 1

        time.sleep(delay_seconds)

    logger.info(
        "InvestorGain total: %d records across %d years",
        report.records_collected,
        len(years),
    )
    return all_records, report
