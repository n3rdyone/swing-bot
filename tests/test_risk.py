import pandas as pd
import numpy as np
import pytest

from bot.trading.risk import check_daily_halt, within_position_limit, position_size


CONFIG = {
    "risk": {
        "max_position_pct": 0.05,
        "max_open_positions": 3,
        "daily_loss_halt_pct": 0.02,
        "atr_multiplier": 1.5,
        "use_atr_sizing": False,
    }
}


def _make_df(n=30, price=100.0):
    close = np.full(n, price)
    high = close * 1.01
    low = close * 0.99
    return pd.DataFrame({"open": close, "high": high, "low": low, "close": close, "volume": np.ones(n) * 1e6})


def test_halt_triggered():
    account = {"equity": 97000.0}
    assert check_daily_halt(account, CONFIG, start_equity=100000.0) is True


def test_halt_not_triggered():
    account = {"equity": 99500.0}
    assert check_daily_halt(account, CONFIG, start_equity=100000.0) is False


def test_within_position_limit_true():
    positions = [{"ticker": "AAPL"}, {"ticker": "MSFT"}]
    assert within_position_limit(positions, CONFIG) is True


def test_within_position_limit_false():
    positions = [{"ticker": "AAPL"}, {"ticker": "MSFT"}, {"ticker": "TSLA"}]
    assert within_position_limit(positions, CONFIG) is False


def test_position_size_nonzero():
    df = _make_df(price=50.0)
    account = {"portfolio_value": 100000.0}
    qty = position_size("AAPL", df, account, CONFIG)
    assert qty >= 1.0


def test_position_size_zero_portfolio():
    df = _make_df()
    account = {"portfolio_value": 0.0}
    qty = position_size("AAPL", df, account, CONFIG)
    assert qty == 0.0
