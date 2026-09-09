"""Optional InvestorGain live IPO adapter.

The adapter follows the public data shape used by ipotrackr, but emits our
canonical ``LiveIPO`` model and fails closed when the provider is unavailable.
It is intentionally not a source of historical listing outcomes or strategy
features.
"""

from __future__ import annotations

import json
import logging
import os
import re
from datetime import date, datetime, timezone
from typing import Any, Optional
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from ipo_analyzer.live.chittorgarh_live import determine_status
from ipo_analyzer.live.models import LiveIPO

logger = logging.getLogger(__name__)

DEFAULT_REPORT_URL = (
    "https://webnodejs.investorgain.com/cloud/report/data-read/331/1/6/"
    "{year}/{financial_year}/0/all"
)


def _number(value: Any) -> Optional[float]:
    if value is None or value == "":
        return None
    match = re.search(r"-?\d+(?:\.\d+)?", str(value).replace(",", ""))
    return float(match.group(0)) if match else None


def _date(value: Any) -> Optional[date]:
    if not value:
        return None
    text = str(value).strip()
    for fmt in ("%Y-%m-%d", "%d %b %Y", "%d-%b-%Y"):
        try:
            return datetime.strptime(text[:11], fmt).date()
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00")).date()
    except ValueError:
        return None


def _name(row: dict) -> str:
    plain = str(row.get("~ipo_name") or "").strip()
    if plain:
        return plain
    markup = str(row.get("Name") or "")
    match = re.search(r'title="([^"]+)"', markup)
    return match.group(1).strip() if match else ""


def _gmp(value: Any) -> Optional[float]:
    return _number(value)


def parse_report_payload(
    payload: dict,
    now: Optional[datetime] = None,
    source_url: str = "INVESTORGAIN_REPORT",
) -> list[LiveIPO]:
    """Parse InvestorGain's reportTableData without turning missing values into zero."""
    now = now or datetime.now(timezone.utc)
    records: list[LiveIPO] = []
    for row in payload.get("reportTableData") or []:
        if not isinstance(row, dict):
            continue
        name = _name(row)
        if not name:
            continue
        open_date = _date(row.get("~Srt_Open") or row.get("Open"))
        close_date = _date(row.get("~Srt_Close") or row.get("Close"))
        listing_date = _date(row.get("~Str_Listing") or row.get("Listing"))
        symbol = str(row.get("symbol") or row.get("~symbol") or "").strip() or None
        provider_id = str(row.get("~id") or name).strip()
        records.append(
            LiveIPO(
                ipo_id=f"IG-{provider_id}",
                company_name=name,
                nse_symbol=symbol,
                segment="MAINBOARD",
                open_date=open_date.isoformat() if open_date else None,
                close_date=close_date.isoformat() if close_date else None,
                listing_date=listing_date.isoformat() if listing_date else None,
                issue_price=_number(row.get("Price (₹)")),
                price_band_high=_number(row.get("Price (₹)")),
                lot_size=int(_number(row.get("Lot"))) if _number(row.get("Lot")) is not None else None,
                issue_size_cr=_number(row.get("IPO Size (₹ in cr)")),
                subscription_qib_x=_number(row.get("qib")),
                subscription_nii_x=_number(row.get("nii")),
                subscription_retail_x=_number(row.get("rii")),
                subscription_total_x=_number(row.get("total")),
                gmp_inr=_gmp(row.get("GMP")),
                gmp_pct=_number(row.get("~gmp_percent_calc")),
                status=determine_status(open_date, close_date, listing_date, now),
                source="INVESTORGAIN",
                source_url=source_url,
                observed_at=now.isoformat(),
                retrieved_at=now.isoformat(),
            )
        )
    return records


def fetch_investorgain_ipos(now: Optional[datetime] = None) -> list[LiveIPO]:
    """Fetch optional InvestorGain data; network/provider failure returns an empty list."""
    now = now or datetime.now(timezone.utc)
    year = now.year
    financial_year = f"{year}-{str(year + 1)[-2:]}"
    base = os.getenv("INVESTORGAIN_REPORT_URL", DEFAULT_REPORT_URL).format(
        year=year,
        financial_year=financial_year,
    )
    url = f"{base}?{urlencode({'search': '', 'v': int(now.timestamp())})}"
    request = Request(url, headers={"Accept": "application/json", "User-Agent": "IPO-Terminal/1.0"})
    try:
        with urlopen(request, timeout=20) as response:
            payload = json.load(response)
        return parse_report_payload(payload, now=now, source_url=url)
    except Exception as exc:
        logger.warning("InvestorGain live source unavailable: %s", exc)
        return []
