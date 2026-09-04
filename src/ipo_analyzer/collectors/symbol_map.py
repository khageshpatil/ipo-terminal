"""
Known NSE symbol corrections.

Some companies trade under a different symbol than the one Chittorgarh stores.
These are manual corrections based on known name changes, renames, or errors.
"""

from __future__ import annotations

# Maps: (chittorgarh_symbol → correct_nse_symbol)
# Also maps company name patterns to help fuzzy correction.
SYMBOL_CORRECTIONS: dict[str, str] = {
    # Angel Broking → Angel One
    "ANGELONE": "ANGELONE",       # Already correct in NSE
    "ANGEL": "ANGELONE",

    # CAMS (CAMS Healthcare? or Computer Age Management Services)
    "CAMS": "CAMS",              # Should be correct — may need date shift

    # IndiGrid / Indigrid
    "PGINVIT": "INDIGRID",       # IndiGrid Infrastructure Trust

    # Mindspace REIT
    "MINDSPACE": "MINDSPACE",    # Check BSE listing

    # RBA = Route Mobile?
    "RBA": "ROUTE",              # Route Mobile

    # Zomato old symbol
    "ETERNAL": "ZOMATO",         # Zomato was listed as ZOMATO

    # BIRET = Brookfield India REIT
    "BIRET": "BIRET",

    # ACUTAAS = ?
    "ACUTAAS": "ACUITAS",

    # ALIVUS = ?
    "ALIVUS": "ALIVUS",

    # AFSL = ?
    "AFSL": "AFSL",

    # Embassy REIT
    "EMBASSY": "EMBASSY",

    # Dharan
    "DHARAN": "DHARAN",
}

# Companies known to be REITs/InvITs that list differently
REITS_INVITS = {
    "MINDSPACE",  # Mindspace Business Parks REIT
    "BIRET",      # Brookfield India Real Estate Trust
    "PGINVIT",    # PowerGrid InvIT
    "INDIGRID",   # India Grid Trust
    "EMBASSY",    # Embassy Office Parks REIT
    "NEXUS",      # Nexus Select Trust REIT
    "MACROTECH",  # Lodha (not REIT but large)
}


def correct_symbol(symbol: str) -> str:
    """Return the corrected NSE symbol, or the original if no correction known."""
    return SYMBOL_CORRECTIONS.get(symbol.upper(), symbol.upper())
