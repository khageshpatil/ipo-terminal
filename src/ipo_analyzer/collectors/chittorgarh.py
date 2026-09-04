"""
Chittorgarh IPO data collector using RSC (React Server Components) payload extraction.

Chittorgarh embeds all IPO data server-side in <script> tags as
self.__next_f.push([1, "...json..."]) payloads. No API key or JS rendering needed.

URL: https://www.chittorgarh.com/ipo/ipo_perf_tracker.asp?year={YYYY}

The response JSON has structure:
  "response": {
    "performancesDetails": [
      {
        "ipo_id": 1942,
        "ipo_company_name": "Unimech Aerospace & Manufacturing Ltd.",
        "ipo_issue_category": "Mainline",
        "ipo_issue_price_final": 785,
        "il_ipo_listing_date": "2024-12-31T00:00:00.000Z",
        "il_nse_script_symbol": "UNIMECH",
        "ildt_open_price": 900.0,       <- LISTING DAY OPEN PRICE
        "ildt_close_price": 1376.25,
        "ipo_issue_size_in_amt": ...,
        "qib": 1.9,
        "nii": 0.88,
        "rii": 1.29,
        "total": 1.68,
        "il_bse_script_code": 544322,
        ...
      },
      ...
    ]
  }
"""

from __future__ import annotations

import json
import logging
import re
import time
from datetime import date, datetime, timezone
from typing import Optional

from bs4 import BeautifulSoup

from .models import CollectionReport, RawIPORecord

logger = logging.getLogger(__name__)

_BASE_URL = "https://www.chittorgarh.com/ipo/ipo_perf_tracker.asp"
_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.chittorgarh.com/",
}


def _get_session():
    try:
        from curl_cffi import requests as cffi_requests
        session = cffi_requests.Session(impersonate="chrome124")
        return session, "curl_cffi"
    except Exception:
        import requests
        s = requests.Session()
        s.headers.update(_HEADERS)
        return s, "requests"


def _extract_rsc_text(html: str) -> str:
    """
    Extract and concatenate all self.__next_f.push([1,"..."]) payloads from the HTML.
    These payloads contain the server-side rendered data.
    """
    soup = BeautifulSoup(html, "lxml")
    combined = []
    for script in soup.find_all("script"):
        txt = script.string or ""
        if "self.__next_f.push" not in txt:
            continue
        m = re.search(r'self\.__next_f\.push\(\[1,"(.+?)"\]\)', txt, re.DOTALL)
        if m:
            try:
                inner = json.loads('"' + m.group(1) + '"')
                combined.append(inner)
            except (json.JSONDecodeError, ValueError):
                pass
    return "".join(combined)


def _parse_ipo_date(s: Optional[str]) -> Optional[date]:
    if not s:
        return None
    # Format: "2024-12-31T00:00:00.000Z"
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00")).date()
    except (ValueError, AttributeError):
        pass
    return None


def _safe_float(v) -> Optional[float]:
    if v is None:
        return None
    try:
        f = float(v)
        return f if f != 0 else None
    except (ValueError, TypeError):
        return None


def _parse_performances(perf_list: list[dict], year: int, source_url: str) -> list[RawIPORecord]:
    """Convert raw performancesDetails records to RawIPORecord objects."""
    records: list[RawIPORecord] = []
    scraped_at = datetime.now(timezone.utc).isoformat()

    for item in perf_list:
        # Skip SME
        category = str(item.get("ipo_issue_category", "")).upper()
        if "SME" in category:
            continue

        issue_type = str(item.get("ipo_issue_type", "")).upper()
        if issue_type not in ("IPO", "FPO", ""):
            # Skip OFS-only, rights issues, etc. at this stage
            pass

        issue_price = _safe_float(item.get("ipo_issue_price_final"))
        listing_date = _parse_ipo_date(item.get("il_ipo_listing_date"))
        listing_open = _safe_float(item.get("ildt_open_price"))

        # Issue size: stored as total amount in INR (not crores) — convert
        issue_size_raw = _safe_float(item.get("ipo_issue_size_in_amt"))
        issue_size_cr = round(issue_size_raw / 1e7, 2) if issue_size_raw else None  # convert paise→Cr? actually INR→Cr

        # Compute listing return
        listing_return_pct: Optional[float] = None
        if issue_price and listing_open and issue_price > 0:
            listing_return_pct = round((listing_open - issue_price) / issue_price * 100, 2)

        rec = RawIPORecord(
            company_name=str(item.get("ipo_company_name", "")).strip(),
            nse_symbol=str(item.get("il_nse_script_symbol", "")).strip() or None,
            bse_code=str(item.get("il_bse_script_code", "")).strip() or None,
            listing_date=listing_date,
            issue_price=issue_price,
            listing_open_approx=listing_open,
            listing_return_pct=listing_return_pct,
            subscription_qib_x=_safe_float(item.get("qib")),
            subscription_nii_x=_safe_float(item.get("nii")),
            subscription_retail_x=_safe_float(item.get("rii")),
            subscription_total_x=_safe_float(item.get("total")),
            issue_size_cr=issue_size_cr,
            source="CHITTORGARH",
            source_url=source_url,
            scraped_at=scraped_at,
        )
        records.append(rec)

    return records


def _fetch_year(session, year: int, report: CollectionReport) -> list[RawIPORecord]:
    url = f"{_BASE_URL}?year={year}"
    try:
        resp = session.get(url, timeout=30)
        if resp.status_code != 200:
            report.add_error(f"Year {year}: HTTP {resp.status_code}")
            return []
    except Exception as e:
        report.add_error(f"Year {year}: fetch error: {e}")
        return []

    rsc_text = _extract_rsc_text(resp.text)
    if not rsc_text:
        report.add_warning(f"Year {year}: no RSC payloads found in response")
        return []

    # Find the response object
    response_match = re.search(r'"response"\s*:\s*(\{.{0,300000}\})', rsc_text, re.DOTALL)
    if not response_match:
        report.add_warning(f"Year {year}: no 'response' object in RSC payload")
        return []

    response_str = response_match.group(1)

    # Find performancesDetails array
    perf_match = re.search(r'"performancesDetails"\s*:\s*(\[.+?\])\s*(?:,"\w|,\}|\})', response_str, re.DOTALL)
    if not perf_match:
        # Try just finding the array from the key position
        perf_match = re.search(r'"performancesDetails"\s*:\s*(\[)', response_str)
        if perf_match:
            # Extract from the opening bracket to a reasonable end
            start = perf_match.start(1)
            bracket_text = response_str[start:start + 200000]
            # Find matching closing bracket
            depth = 0
            end = 0
            for i, ch in enumerate(bracket_text):
                if ch == '[':
                    depth += 1
                elif ch == ']':
                    depth -= 1
                    if depth == 0:
                        end = i + 1
                        break
            if end > 0:
                perf_json = bracket_text[:end]
                try:
                    perf_list = json.loads(perf_json)
                    records = _parse_performances(perf_list, year, url)
                    logger.info("Year %d: %d records (RSC+bracket extractor)", year, len(records))
                    return records
                except json.JSONDecodeError as e:
                    report.add_warning(f"Year {year}: JSON parse error: {e}")
                    return []
        report.add_warning(f"Year {year}: no performancesDetails array found")
        return []

    try:
        perf_list = json.loads(perf_match.group(1))
    except json.JSONDecodeError as e:
        report.add_warning(f"Year {year}: performancesDetails JSON error: {e}")
        return []

    records = _parse_performances(perf_list, year, url)
    logger.info("Year %d: %d records", year, len(records))
    return records


def scrape_chittorgarh(
    years: list[int],
    delay_seconds: float = 2.0,
) -> tuple[list[RawIPORecord], CollectionReport]:
    """
    Scrape Chittorgarh IPO performance tracker for the given years.
    Uses RSC payload extraction — no JS rendering needed.

    Returns (records, report).
    """
    session, session_type = _get_session()
    report = CollectionReport(source="CHITTORGARH", years_requested=years)
    logger.info("Chittorgarh RSC scraper using %s", session_type)

    all_records: list[RawIPORecord] = []

    for year in years:
        logger.info("Fetching Chittorgarh year %d...", year)
        records = _fetch_year(session, year, report)
        if records:
            report.records_collected += len(records)
            all_records.extend(records)
        else:
            report.records_failed += 1
        time.sleep(delay_seconds)

    logger.info("Chittorgarh total: %d records across %d years", len(all_records), len(years))
    return all_records, report
