"""
tests/test_fetch_prices.py

Unit tests for fetch_prices.py.

MetaTrader5 is mocked so the tests can run on any machine, regardless of
whether the terminal is installed.
"""

from __future__ import annotations

import importlib
import sys
import types
from datetime import datetime, timezone, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest


# ---------------------------------------------------------------------------
# Helpers to build a fake MetaTrader5 module before importing fetch_prices
# ---------------------------------------------------------------------------

def _make_mt5_stub() -> types.ModuleType:
    """Return a minimal fake MetaTrader5 module."""
    stub = types.ModuleType("MetaTrader5")
    stub.TIMEFRAME_H1 = 16385

    # Default: successful initialise / shutdown
    stub.initialize = MagicMock(return_value=True)
    stub.shutdown = MagicMock()
    stub.last_error = MagicMock(return_value=(0, ""))

    # Fake terminal info
    info = MagicMock()
    info.name = "FakeTerminal"
    info.build = 9999
    stub.terminal_info = MagicMock(return_value=info)

    return stub


def _make_rates_array(n: int = 10) -> np.ndarray:
    """Return a structured numpy array that mimics MT5 rate data."""
    now = datetime.now(timezone.utc)
    dtype = [
        ("time", np.int64),
        ("open", np.float64),
        ("high", np.float64),
        ("low", np.float64),
        ("close", np.float64),
        ("tick_volume", np.int64),
        ("spread", np.int32),
        ("real_volume", np.int64),
    ]
    rows = []
    for i in range(n):
        ts = int((now - timedelta(hours=n - i)).timestamp())
        rows.append((ts, 1.1 + i * 0.001, 1.11, 1.09, 1.1 + i * 0.001, 1000, 1, 0))
    return np.array(rows, dtype=dtype)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def patch_mt5(tmp_path, monkeypatch):
    """Inject a fake MetaTrader5 module and redirect CSV output to tmp_path."""
    stub = _make_mt5_stub()
    stub.copy_rates_range = MagicMock(return_value=_make_rates_array(100))

    # Inject before importing the module under test
    monkeypatch.setitem(sys.modules, "MetaTrader5", stub)

    # Force re-import so the module picks up the stub
    if "fetch_prices" in sys.modules:
        del sys.modules["fetch_prices"]
    import fetch_prices  # noqa: PLC0415
    monkeypatch.setattr(fetch_prices, "mt5", stub)
    monkeypatch.setattr(fetch_prices, "OUTPUT_DIR", tmp_path / "data")

    yield stub


@pytest.fixture()
def fp():
    """Return the (re-)imported fetch_prices module."""
    return sys.modules["fetch_prices"]


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestConnect:
    def test_connect_success(self, patch_mt5, fp):
        fp.connect()
        patch_mt5.initialize.assert_called_once()

    def test_connect_failure_raises(self, patch_mt5, fp):
        patch_mt5.initialize.return_value = False
        patch_mt5.last_error.return_value = (5, "No connection")
        with pytest.raises(RuntimeError, match="initialize\\(\\) failed"):
            fp.connect()


class TestDisconnect:
    def test_disconnect_calls_shutdown(self, patch_mt5, fp):
        fp.disconnect()
        patch_mt5.shutdown.assert_called_once()


class TestFetchLastSixMonths:
    def test_returns_dataframe(self, patch_mt5, fp):
        df = fp.fetch_last_six_months("EURUSD")
        assert isinstance(df, pd.DataFrame)

    def test_dataframe_has_expected_columns(self, patch_mt5, fp):
        df = fp.fetch_last_six_months("EURUSD")
        for col in ("open", "high", "low", "close", "tick_volume"):
            assert col in df.columns

    def test_time_index_is_utc_aware(self, patch_mt5, fp):
        df = fp.fetch_last_six_months("EURUSD")
        assert df.index.name == "time"
        assert df.index.tzinfo is not None

    def test_correct_number_of_bars(self, patch_mt5, fp):
        df = fp.fetch_last_six_months("EURUSD")
        assert len(df) == 100

    def test_no_data_raises_value_error(self, patch_mt5, fp):
        patch_mt5.copy_rates_range.return_value = None
        with pytest.raises(ValueError, match="No data returned for EURUSD"):
            fp.fetch_last_six_months("EURUSD")

    def test_empty_array_raises_value_error(self, patch_mt5, fp):
        patch_mt5.copy_rates_range.return_value = np.array([])
        with pytest.raises(ValueError):
            fp.fetch_last_six_months("EURUSD")

    def test_uses_six_month_date_range(self, patch_mt5, fp):
        fp.fetch_last_six_months("EURUSD")
        call_args = patch_mt5.copy_rates_range.call_args
        date_from: datetime = call_args[0][2]
        date_to: datetime = call_args[0][3]
        delta = date_to - date_from
        # Should be approximately 180 days (6 × 30)
        assert 170 < delta.days <= 185


class TestSaveToCsv:
    def test_csv_is_created(self, fp, tmp_path):
        df = fp.fetch_last_six_months("EURUSD")
        path = fp.save_to_csv(df, "EURUSD", tmp_path)
        assert Path(path).exists()

    def test_csv_filename_contains_symbol(self, fp, tmp_path):
        df = fp.fetch_last_six_months("EURUSD")
        path = fp.save_to_csv(df, "EURUSD", tmp_path)
        assert "EURUSD" in Path(path).name

    def test_csv_has_correct_row_count(self, fp, tmp_path):
        df = fp.fetch_last_six_months("EURUSD")
        path = fp.save_to_csv(df, "EURUSD", tmp_path)
        loaded = pd.read_csv(path, index_col="time")
        assert len(loaded) == len(df)

    def test_output_dir_created_if_missing(self, fp, tmp_path):
        new_dir = tmp_path / "nested" / "output"
        assert not new_dir.exists()
        df = fp.fetch_last_six_months("EURUSD")
        fp.save_to_csv(df, "EURUSD", new_dir)
        assert new_dir.exists()


class TestRun:
    def test_run_returns_dict_of_dataframes(self, patch_mt5, fp):
        result = fp.run(["EURUSD", "GBPUSD"])
        assert set(result.keys()) == {"EURUSD", "GBPUSD"}
        for df in result.values():
            assert isinstance(df, pd.DataFrame)

    def test_failed_symbol_is_skipped(self, patch_mt5, fp):
        def side_effect(sym, tf, d_from, d_to):
            if sym == "BADINSTRUMENT":
                return None
            return _make_rates_array(10)

        patch_mt5.copy_rates_range.side_effect = side_effect
        result = fp.run(["EURUSD", "BADINSTRUMENT"])
        assert "EURUSD" in result
        assert "BADINSTRUMENT" not in result

    def test_disconnect_called_on_exception(self, patch_mt5, fp):
        patch_mt5.copy_rates_range.side_effect = Exception("Unexpected")
        with pytest.raises(Exception):
            fp.run(["EURUSD"])
        patch_mt5.shutdown.assert_called_once()

    def test_default_symbols_used_when_none(self, patch_mt5, fp):
        result = fp.run(None)
        for sym in fp.DEFAULT_SYMBOLS:
            assert sym in result
