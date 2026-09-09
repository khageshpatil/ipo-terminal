from datetime import datetime, timezone

from ipo_analyzer.data_sources.investorgain import parse_report_payload


def test_investorgain_payload_normalizes_dates_and_status():
    payload = {
        "reportTableData": [{
            "~id": 2514,
            "~ipo_name": "Steamhouse India",
            "~Srt_Open": "2026-09-09",
            "~Srt_Close": "2026-09-11",
            "~Str_Listing": "2026-09-17",
            "Price (₹)": "81",
            "Lot": "185",
            "GMP": "₹12 (14.81%)",
            "~gmp_percent_calc": "14.81",
            "qib": "2.1",
            "nii": "4.4",
            "rii": "1.8",
            "total": "3.0",
        }]
    }
    result = parse_report_payload(payload, datetime(2026, 9, 9, 5, tzinfo=timezone.utc))
    assert len(result) == 1
    ipo = result[0]
    assert ipo.status == "OPEN"
    assert ipo.open_date == "2026-09-09"
    assert ipo.subscription_total_x == 3.0
    assert ipo.gmp_inr == 12.0
    assert ipo.source == "INVESTORGAIN"


def test_investorgain_missing_values_stay_none():
    result = parse_report_payload({"reportTableData": [{"~id": 1, "~ipo_name": "Unknown IPO"}]})
    ipo = result[0]
    assert ipo.issue_price is None
    assert ipo.subscription_total_x is None
    assert ipo.gmp_inr is None
    assert ipo.status == "UNKNOWN"
