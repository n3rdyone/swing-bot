import pandas as pd
import numpy as np
import pytest

from bot.signals.technical import compute_score


def _make_df(n=60, trend="up"):
    dates = pd.date_range("2024-01-01", periods=n)
    if trend == "up":
        close = np.linspace(100, 150, n)
    elif trend == "down":
        close = np.linspace(150, 100, n)
    else:
        close = np.random.uniform(90, 110, n)
    high = close * 1.01
    low = close * 0.99
    volume = np.random.randint(1_000_000, 5_000_000, n).astype(float)
    return pd.DataFrame({"open": close, "high": high, "low": low, "close": close, "volume": volume}, index=dates)


CONFIG = {
    "technical": {
        "indicators": {
            "rsi": {"period": 14, "weight": 0.20},
            "macd": {"fast": 12, "slow": 26, "signal": 9, "weight": 0.25},
            "ema_cross": {"fast": 9, "slow": 21, "weight": 0.20},
            "adx": {"period": 14, "threshold": 25, "weight": 0.15},
            "bbands": {"period": 20, "std": 2.0, "weight": 0.20},
        }
    }
}


def test_returns_float():
    df = _make_df()
    score = compute_score(df, CONFIG)
    assert isinstance(score, float)


def test_score_range():
    df = _make_df()
    score = compute_score(df, CONFIG)
    assert -1.0 <= score <= 1.0


def test_uptrend_positive_score():
    df = _make_df(trend="up")
    score = compute_score(df, CONFIG)
    assert score > 0


def test_downtrend_negative_score():
    df = _make_df(trend="down")
    score = compute_score(df, CONFIG)
    assert score < 0


def test_empty_df_returns_zero():
    score = compute_score(pd.DataFrame(), CONFIG)
    assert score == 0.0


def test_insufficient_data_returns_zero():
    df = _make_df(n=10)
    score = compute_score(df, CONFIG)
    assert score == 0.0
