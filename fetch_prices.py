"""
fetch_prices.py

Connects to a locally running MetaTrader5 terminal and downloads the last
6 months of OHLCV price data (H1 bars) for one or more symbols, then saves
each symbol's data to a CSV file.

Usage
-----
    python fetch_prices.py                        # default symbol list
    python fetch_prices.py EURUSD GBPUSD XAUUSD  # custom symbol list

Requirements
------------
    MetaTrader5 terminal must be installed, running, and already logged in.
    Install Python dependencies:
        pip install -r requirements.txt
"""

from __future__ import annotations

import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

import pandas as pd

try:
    import MetaTrader5 as mt5
except ImportError as exc:  # pragma: no cover
    raise ImportError(
        "MetaTrader5 package is not installed. "
        "Run: pip install -r requirements.txt"
    ) from exc


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DEFAULT_SYMBOLS = ["EURUSD", "GBPUSD", "XAUUSD"]
TIMEFRAME = mt5.TIMEFRAME_H1   # 1-hour bars
MONTHS_BACK = 6
OUTPUT_DIR = Path("data")


# ---------------------------------------------------------------------------
# Core helpers
# ---------------------------------------------------------------------------

def connect() -> None:
    """Initialise a connection to the local MetaTrader5 terminal.

    Raises
    ------
    RuntimeError
        If the terminal cannot be reached or initialisation fails.
    """
    if not mt5.initialize():
        error = mt5.last_error()
        raise RuntimeError(
            f"MetaTrader5 initialize() failed – error code: {error}"
        )
    info = mt5.terminal_info()
    print(f"Connected to MetaTrader5 terminal: {info.name}  build {info.build}")


def disconnect() -> None:
    """Shut down the MetaTrader5 connection."""
    mt5.shutdown()
    print("Disconnected from MetaTrader5.")


def fetch_last_six_months(symbol: str, timeframe: int = TIMEFRAME) -> pd.DataFrame:
    """Download the last 6 months of OHLCV bars for *symbol*.

    Parameters
    ----------
    symbol:
        Instrument name as it appears in MetaTrader5 (e.g. ``"EURUSD"``).
    timeframe:
        A ``mt5.TIMEFRAME_*`` constant.  Defaults to ``TIMEFRAME_H1``.

    Returns
    -------
    pd.DataFrame
        DataFrame with columns ``time, open, high, low, close, tick_volume,
        spread, real_volume``.  The ``time`` column is UTC-aware.

    Raises
    ------
    ValueError
        If the symbol is not available in the terminal or no data is returned.
    """
    now_utc = datetime.now(timezone.utc)
    date_from = now_utc - timedelta(days=MONTHS_BACK * 30)

    rates = mt5.copy_rates_range(symbol, timeframe, date_from, now_utc)

    if rates is None or len(rates) == 0:
        error = mt5.last_error()
        raise ValueError(
            f"No data returned for {symbol}. MT5 error: {error}. "
            "Make sure the symbol is available and the terminal is connected."
        )

    df = pd.DataFrame(rates)
    df["time"] = pd.to_datetime(df["time"], unit="s", utc=True)
    df.set_index("time", inplace=True)
    return df


def save_to_csv(df: pd.DataFrame, symbol: str, output_dir: Path = OUTPUT_DIR) -> Path:
    """Save *df* to ``<output_dir>/<symbol>_6m.csv``.

    Parameters
    ----------
    df:
        Price DataFrame as returned by :func:`fetch_last_six_months`.
    symbol:
        Used to build the output filename.
    output_dir:
        Directory to write the file into (created if it does not exist).

    Returns
    -------
    Path
        Absolute path of the written CSV file.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"{symbol}_6m.csv"
    df.to_csv(path)
    return path.resolve()


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def run(symbols: list[str] | None = None) -> dict[str, pd.DataFrame]:
    """Connect, download data, save CSVs, disconnect.

    Parameters
    ----------
    symbols:
        List of instrument names.  Defaults to :data:`DEFAULT_SYMBOLS`.

    Returns
    -------
    dict[str, pd.DataFrame]
        Mapping of symbol → DataFrame for all successfully fetched symbols.
    """
    if symbols is None:
        symbols = DEFAULT_SYMBOLS

    connect()
    results: dict[str, pd.DataFrame] = {}
    try:
        for symbol in symbols:
            print(f"Fetching {MONTHS_BACK} months of H1 data for {symbol} …", end=" ")
            try:
                df = fetch_last_six_months(symbol)
                path = save_to_csv(df, symbol)
                print(f"{len(df):,} bars  →  {path}")
                results[symbol] = df
            except ValueError as exc:
                print(f"SKIPPED – {exc}")
    finally:
        disconnect()

    return results


if __name__ == "__main__":
    cli_symbols = sys.argv[1:] if len(sys.argv) > 1 else None
    run(cli_symbols)
