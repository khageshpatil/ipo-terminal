"""API contract test for the real-data decision vertical slice."""

def test_real_historical_ipo_reaches_strategy_api():
    """A real universe row produces a frontend-consumable RULE_V1 payload."""
    import warnings

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        from ipo_analyzer.api.app import analyse_ipo, list_ipos

    ipo = list_ipos(
        year=None,
        search=None,
        min_quality="SECONDARY_VERIFIED",
        limit=1,
        offset=0,
    )[0].model_dump()
    payload = analyse_ipo(ipo["ipo_id"]).model_dump()

    assert payload["ipo_id"] == ipo["ipo_id"]
    assert payload["strategy_version"] == "RULE_V1"
    assert payload["confidence"] == "RULE_ESTIMATE"
    assert isinstance(payload["drivers"], list)
    assert isinstance(payload["features_snapshot"], dict)
    assert payload["features_snapshot"]["subscription_total_x"] == ipo["subscription_total_x"]
    assert payload["listing_open_price"] == ipo["listing_open_price"]
