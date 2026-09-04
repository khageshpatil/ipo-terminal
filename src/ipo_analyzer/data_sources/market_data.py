"""
G5 Market Data ingestion module.

Downloads and normalises historical daily market data for use as
market-regime features in the IPO listing-gain model.

Phase 1 scope:
  - NIFTY 50 daily OHLCV (^NSEI via yfinance)
  - India VIX daily close (^INDIAVIX via yfinance)
  - Derived features: 20d / 5d returns, VIX level, market regime label

Point-in-time note:
  All market features for an IPO that closes on date D must use
  market data observed on or before D (inclusive).
  Data on D+1 or later is NEVER eligible as a feature for that IPO.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

import pandas as pd

logger = logging.getLogger(__name__)

UTC = timezone.utc

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

NIFTY_TICKER = "^NSEI"
VIX_TICKER = "^INDIAVIX"

# Data coverage confirmed via yfinance probing:
NIFTY_COVERAGE_START = date(1999, 11, 3)   # yfinance earliest confirmed for ^NSEI
VIX_COVERAGE_START = date(2009, 3, 2)       # India VIX launched Mar 2009 (NSE)

# Paths (relative to repo root; caller should resolve)
DEFAULT_NIFTY_CSV = Path("data/market/nifty50_daily.csv")
DEFAULT_VIX_CSV = Path("data/market/india_vix_daily.csv")
DEFAULT_COMBINED_CSV = Path("data/market/market_features_daily.csv")


# ---------------------------------------------------------------------------
# Dataclass for a single day's market snapshot
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class DailyMarketSnapshot:
    """
    One calendar day's market data.
    All fields are as-of market close on `date`.
    """

    date: date

    nifty_close: Optional[float]
    nifty_open: Optional[float]
    nifty_high: Optional[float]
    nifty_low: Optional[float]
    nifty_volume: Optional[float]

    india_vix_close: Optional[float]

    # Derived — computed from trailing window
    nifty_return_5d: Optional[float]   # (close / close[t-5]) - 1
    nifty_return_20d: Optional[float]  # (close / close[t-20]) - 1
    vix_level_label: Optional[str]     # 'LOW' (<15), 'MID' (15-20), 'HIGH' (>20)
    market_regime: Optional[str]       # 'BULL', 'NEUTRAL', 'BEAR' (based on 20d return)


# ---------------------------------------------------------------------------
# Download functions
# ---------------------------------------------------------------------------


def download_nifty(
    start: date = date(2017, 1, 1),
    end: Optional[date] = None,
    output_path: Optional[Path] = None,
) -> pd.DataFrame:
    """
    Download NIFTY 50 daily OHLCV from Yahoo Finance.

    Parameters
    ----------
    start : date
        Start date (inclusive). Default 2017-01-01 gives 1yr buffer before 2018.
    end : date, optional
        End date (inclusive). Defaults to today.
    output_path : Path, optional
        If provided, save the raw CSV here.

    Returns
    -------
    pd.DataFrame
        Columns: Date, Open, High, Low, Close, Volume
        Index: RangeIndex (Date stored as column, not index)
    """
    import yfinance as yf

    end = end or date.today()
    logger.info("Downloading NIFTY 50 (%s to %s)...", start, end)

    df = yf.download(
        NIFTY_TICKER,
        start=str(start),
        end=str(end + timedelta(days=1)),  # yfinance end is exclusive
        interval="1d",
        progress=False,
        auto_adjust=True,
    )

    if df.empty:
        raise RuntimeError(f"yfinance returned empty DataFrame for {NIFTY_TICKER}")

    # Flatten MultiIndex columns if present
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [c[0] for c in df.columns]

    df = df.reset_index()
    df.rename(columns={"index": "Date", "Datetime": "Date"}, inplace=True)
    df["Date"] = pd.to_datetime(df["Date"]).dt.date

    # Drop rows with NaN close
    n_before = len(df)
    df = df.dropna(subset=["Close"])
    n_dropped = n_before - len(df)
    if n_dropped > 0:
        logger.warning("NIFTY: dropped %d rows with NaN Close", n_dropped)

    df = df.sort_values("Date").reset_index(drop=True)
    logger.info("NIFTY: %d trading days loaded (%s to %s)", len(df), df["Date"].iloc[0], df["Date"].iloc[-1])

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_path, index=False)
        logger.info("NIFTY CSV saved: %s", output_path)

    return df


def download_vix(
    start: date = date(2017, 1, 1),
    end: Optional[date] = None,
    output_path: Optional[Path] = None,
) -> pd.DataFrame:
    """
    Download India VIX daily close from Yahoo Finance.

    Note: yfinance provides VIX close only (no intraday OHLCV for ^INDIAVIX).
    Coverage starts March 2009 (NSE launch). Data before 2010 may be sparse.

    Returns
    -------
    pd.DataFrame
        Columns: Date, VIX_Close
    """
    import yfinance as yf

    end = end or date.today()
    logger.info("Downloading India VIX (%s to %s)...", start, end)

    df = yf.download(
        VIX_TICKER,
        start=str(start),
        end=str(end + timedelta(days=1)),
        interval="1d",
        progress=False,
        auto_adjust=True,
    )

    if df.empty:
        logger.warning("yfinance returned empty DataFrame for %s — VIX data may not be available", VIX_TICKER)
        return pd.DataFrame(columns=["Date", "VIX_Close"])

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [c[0] for c in df.columns]

    df = df.reset_index()
    df.rename(columns={"index": "Date", "Datetime": "Date"}, inplace=True)
    df["Date"] = pd.to_datetime(df["Date"]).dt.date

    # VIX: use Close column
    df = df[["Date", "Close"]].rename(columns={"Close": "VIX_Close"})
    df = df.dropna(subset=["VIX_Close"])
    df = df.sort_values("Date").reset_index(drop=True)

    logger.info("VIX: %d days loaded (%s to %s)", len(df), df["Date"].iloc[0], df["Date"].iloc[-1])

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_path, index=False)
        logger.info("VIX CSV saved: %s", output_path)

    return df


# ---------------------------------------------------------------------------
# Feature derivation
# ---------------------------------------------------------------------------


def _vix_label(vix: float) -> str:
    if vix < 15:
        return "LOW"
    if vix < 20:
        return "MID"
    return "HIGH"


def _market_regime(ret_20d: float) -> str:
    if ret_20d > 0.03:
        return "BULL"
    if ret_20d < -0.03:
        return "BEAR"
    return "NEUTRAL"


def build_market_features(
    nifty_df: pd.DataFrame,
    vix_df: pd.DataFrame,
    output_path: Optional[Path] = None,
) -> pd.DataFrame:
    """
    Merge NIFTY and VIX data and compute derived market-regime features.

    Returns a DataFrame with columns:
      Date, nifty_close, nifty_return_5d, nifty_return_20d,
      india_vix_close, vix_level_label, market_regime

    Point-in-time safe: all values are available at market close on Date.
    """
    # Merge on Date (left join from NIFTY — VIX may have gaps)
    merged = pd.merge(
        nifty_df[["Date", "Open", "High", "Low", "Close", "Volume"]].rename(
            columns={
                "Open": "nifty_open",
                "High": "nifty_high",
                "Low": "nifty_low",
                "Close": "nifty_close",
                "Volume": "nifty_volume",
            }
        ),
        vix_df[["Date", "VIX_Close"]].rename(columns={"VIX_Close": "india_vix_close"}),
        on="Date",
        how="left",
    )

    merged = merged.sort_values("Date").reset_index(drop=True)

    # Trailing returns
    merged["nifty_return_5d"] = (
        merged["nifty_close"] / merged["nifty_close"].shift(5) - 1
    )
    merged["nifty_return_20d"] = (
        merged["nifty_close"] / merged["nifty_close"].shift(20) - 1
    )

    # Labels (only where data is available)
    merged["vix_level_label"] = merged["india_vix_close"].apply(
        lambda v: _vix_label(v) if pd.notna(v) else None
    )
    merged["market_regime"] = merged["nifty_return_20d"].apply(
        lambda r: _market_regime(r) if pd.notna(r) else None
    )

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        merged.to_csv(output_path, index=False)
        logger.info("Market features CSV saved: %s", output_path)

    return merged


def get_market_snapshot_for_date(
    features_df: pd.DataFrame,
    target_date: date,
) -> Optional[DailyMarketSnapshot]:
    """
    Get the market snapshot for a given date (or the most recent prior trading day).

    This is the safe point-in-time lookup for feature generation:
    always returns data available as of market close on or before target_date.

    Parameters
    ----------
    features_df : pd.DataFrame
        Output of build_market_features().
    target_date : date
        The decision date (e.g., subscription close date).

    Returns
    -------
    DailyMarketSnapshot or None if no data is available before target_date.
    """
    eligible = features_df[features_df["Date"] <= target_date]
    if eligible.empty:
        return None

    row = eligible.iloc[-1]

    def _f(col: str) -> Optional[float]:
        v = row.get(col)
        return float(v) if pd.notna(v) else None

    def _s(col: str) -> Optional[str]:
        v = row.get(col)
        return str(v) if pd.notna(v) else None

    return DailyMarketSnapshot(
        date=row["Date"],
        nifty_close=_f("nifty_close"),
        nifty_open=_f("nifty_open"),
        nifty_high=_f("nifty_high"),
        nifty_low=_f("nifty_low"),
        nifty_volume=_f("nifty_volume"),
        india_vix_close=_f("india_vix_close"),
        nifty_return_5d=_f("nifty_return_5d"),
        nifty_return_20d=_f("nifty_return_20d"),
        vix_level_label=_s("vix_level_label"),
        market_regime=_s("market_regime"),
    )


# ---------------------------------------------------------------------------
# Top-level convenience function
# ---------------------------------------------------------------------------


def fetch_and_save_market_data(
    start: date = date(2017, 1, 1),
    end: Optional[date] = None,
    data_dir: Path = Path("data/market"),
) -> pd.DataFrame:
    """
    Download NIFTY + VIX, compute features, save all CSVs.

    Usage:
        from ipo_analyzer.data_sources.market_data import fetch_and_save_market_data
        df = fetch_and_save_market_data()
        print(df.tail())

    Returns the combined features DataFrame.
    """
    data_dir.mkdir(parents=True, exist_ok=True)

    nifty = download_nifty(start=start, end=end, output_path=data_dir / "nifty50_daily.csv")
    vix = download_vix(start=start, end=end, output_path=data_dir / "india_vix_daily.csv")
    features = build_market_features(nifty, vix, output_path=data_dir / "market_features_daily.csv")

    logger.info(
        "Market data ready: %d trading days from %s to %s",
        len(features),
        features["Date"].iloc[0],
        features["Date"].iloc[-1],
    )
    return features
