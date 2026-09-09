from ipo_analyzer.live.chittorgarh_live import merge_live_sources
from ipo_analyzer.live.models import LiveIPO


def test_investorgain_primary_is_not_overwritten_by_chittorgarh():
    primary = LiveIPO(
        ipo_id="IG-1",
        company_name="Example India",
        issue_price=100.0,
        subscription_total_x=4.0,
        gmp_inr=12.0,
        status="OPEN",
        source="INVESTORGAIN",
    )
    fallback = LiveIPO(
        ipo_id="CG-1",
        company_name="Example India Ltd.",
        issue_price=98.0,
        subscription_total_x=3.0,
        gmp_inr=9.0,
        lot_size=10,
        status="OPEN",
        source="CHITTORGARH_LIVE",
    )

    result = merge_live_sources([primary], [fallback])

    assert len(result) == 1
    assert result[0].issue_price == 100.0
    assert result[0].subscription_total_x == 4.0
    assert result[0].gmp_inr == 12.0
    assert result[0].lot_size == 10
    assert result[0].source == "INVESTORGAIN+CHITTORGARH"


def test_chittorgarh_is_fallback_when_investorgain_has_no_value():
    primary = LiveIPO(
        ipo_id="IG-2",
        company_name="Example India",
        status="UNKNOWN",
        source="INVESTORGAIN",
    )
    fallback = LiveIPO(
        ipo_id="CG-2",
        company_name="Example India Ltd.",
        issue_price=81.0,
        subscription_total_x=2.5,
        status="OPEN",
        source="CHITTORGARH_LIVE",
    )

    result = merge_live_sources([primary], [fallback])

    assert result[0].issue_price == 81.0
    assert result[0].subscription_total_x == 2.5
    assert result[0].status == "OPEN"
    assert result[0].source == "INVESTORGAIN+CHITTORGARH"


def test_chittorgarh_only_result_survives_investorgain_outage():
    fallback = LiveIPO(
        ipo_id="CG-3",
        company_name="Fallback India",
        status="UPCOMING",
        source="CHITTORGARH_LIVE",
    )

    result = merge_live_sources([], [fallback])

    assert len(result) == 1
    assert result[0].source == "CHITTORGARH_LIVE"
    assert result[0].status == "UPCOMING"
