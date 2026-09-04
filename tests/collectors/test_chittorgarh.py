"""Tests for the Chittorgarh RSC extractor (offline unit tests — no network)."""
from __future__ import annotations

import json
import pytest

# Minimal synthetic RSC payload that mimics the real Chittorgarh structure
_FAKE_RSC_PAYLOAD = (
    '{"response":{"msg":1,"redis_cache_key":"ipoperf/list-read::mainline:2024",'
    '"performancesDetails":['
    '{"ipo_id":1000,"ipo_company_name":"Test Corp Ltd.","ipo_issue_category":"Mainline",'
    '"ipo_issue_type":"IPO","ipo_issue_price_final":500.0,'
    '"il_ipo_listing_date":"2024-06-15T00:00:00.000Z",'
    '"il_nse_script_symbol":"TESTCORP","il_bse_script_code":543000,'
    '"ildt_open_price":650.0,"ildt_close_price":680.0,'
    '"ipo_issue_size_in_amt":5000000000,'
    '"qib":45.2,"nii":120.5,"rii":8.3,"total":62.1},'
    '{"ipo_id":1001,"ipo_company_name":"SME Firm","ipo_issue_category":"SME",'
    '"ipo_issue_type":"IPO","ipo_issue_price_final":100.0,'
    '"il_ipo_listing_date":"2024-07-01T00:00:00.000Z",'
    '"il_nse_script_symbol":"SMEFIRM","il_bse_script_code":999,'
    '"ildt_open_price":90.0,"ildt_close_price":88.0,'
    '"ipo_issue_size_in_amt":100000000,'
    '"qib":0.5,"nii":0.3,"rii":0.8,"total":0.7}'
    ']}}'
)


def _make_html_with_rsc(json_payload: str) -> str:
    """Wrap a JSON payload in a minimal Next.js RSC script tag."""
    import json as _json
    # JSON-encode the payload string as it would appear in self.__next_f.push
    encoded = _json.dumps(json_payload)[1:-1]  # remove outer quotes
    return f"""<!DOCTYPE html>
<html><head></head><body>
<script>self.__next_f=[]; self.__next_f.push([1,"{encoded}"])</script>
</body></html>"""


class TestRSCExtractor:
    def test_extract_rsc_text_finds_payload(self) -> None:
        from ipo_analyzer.collectors.chittorgarh import _extract_rsc_text
        html = _make_html_with_rsc(_FAKE_RSC_PAYLOAD)
        text = _extract_rsc_text(html)
        assert '"performancesDetails"' in text
        assert "Test Corp Ltd." in text

    def test_extracts_mainboard_records(self) -> None:
        """Test _parse_performances directly with known input."""
        from ipo_analyzer.collectors.chittorgarh import _parse_performances

        perf_list = [
            {
                "ipo_id": 1000,
                "ipo_company_name": "Test Corp Ltd.",
                "ipo_issue_category": "Mainline",
                "ipo_issue_type": "IPO",
                "ipo_issue_price_final": 500.0,
                "il_ipo_listing_date": "2024-06-15T00:00:00.000Z",
                "il_nse_script_symbol": "TESTCORP",
                "il_bse_script_code": 543000,
                "ildt_open_price": 650.0,
                "ildt_close_price": 680.0,
                "ipo_issue_size_in_amt": 5_000_000_000,
                "qib": 45.2, "nii": 120.5, "rii": 8.3, "total": 62.1,
            },
            {
                "ipo_id": 1001,
                "ipo_company_name": "SME Firm",
                "ipo_issue_category": "SME",
                "ipo_issue_type": "IPO",
                "ipo_issue_price_final": 100.0,
                "il_ipo_listing_date": "2024-07-01T00:00:00.000Z",
                "il_nse_script_symbol": "SMEFIRM",
                "il_bse_script_code": 999,
                "ildt_open_price": 90.0,
            },
        ]

        records = _parse_performances(perf_list, 2024, "http://test")
        # SME should be filtered
        assert len(records) == 1
        r = records[0]
        assert r.company_name == "Test Corp Ltd."
        assert r.nse_symbol == "TESTCORP"
        assert r.issue_price == 500.0
        assert r.listing_open_approx == 650.0
        assert r.subscription_total_x == 62.1
        assert r.subscription_qib_x == 45.2

    def test_listing_return_computed(self) -> None:
        from ipo_analyzer.collectors.chittorgarh import _parse_performances
        perf_list = [{
            "ipo_company_name": "Gain Co.",
            "ipo_issue_category": "Mainline",
            "ipo_issue_type": "IPO",
            "ipo_issue_price_final": 100.0,
            "il_ipo_listing_date": "2022-03-10T00:00:00.000Z",
            "il_nse_script_symbol": "GAINCOL",
            "ildt_open_price": 120.0,
            "qib": 10.0, "nii": 15.0, "rii": 2.0, "total": 12.0,
        }]
        records = _parse_performances(perf_list, 2022, "http://test")
        assert records[0].listing_return_pct == pytest.approx(20.0, abs=0.01)

    def test_sme_filtered(self) -> None:
        from ipo_analyzer.collectors.chittorgarh import _parse_performances
        perf_list = [{
            "ipo_company_name": "SME Co.",
            "ipo_issue_category": "SME",
            "ipo_issue_type": "IPO",
            "ipo_issue_price_final": 50.0,
            "il_ipo_listing_date": "2022-03-10T00:00:00.000Z",
            "il_nse_script_symbol": "SMECO",
            "ildt_open_price": 60.0,
        }]
        records = _parse_performances(perf_list, 2022, "http://test")
        assert len(records) == 0

    def test_missing_price_handled(self) -> None:
        from ipo_analyzer.collectors.chittorgarh import _parse_performances
        perf_list = [{
            "ipo_company_name": "No Price Co.",
            "ipo_issue_category": "Mainline",
            "ipo_issue_type": "IPO",
            "ipo_issue_price_final": None,
            "il_ipo_listing_date": "2021-08-20T00:00:00.000Z",
            "il_nse_script_symbol": "NOPRICE",
            "ildt_open_price": None,
        }]
        records = _parse_performances(perf_list, 2021, "http://test")
        assert len(records) == 1
        assert records[0].issue_price is None
        assert records[0].listing_open_approx is None
        assert records[0].listing_return_pct is None
