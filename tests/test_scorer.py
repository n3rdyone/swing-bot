import pytest
from bot.signals.scorer import score_tickers


CONFIG = {
    "scoring": {
        "technical_weight": 0.55,
        "sentiment_weight": 0.45,
        "min_composite_score": 0.35,
    }
}


def test_buy_signal():
    df = score_tickers({"AAPL": 0.8}, {"AAPL": 0.7}, CONFIG)
    assert df.iloc[0]["signal"] == "BUY"


def test_sell_signal():
    df = score_tickers({"AAPL": -0.8}, {"AAPL": -0.7}, CONFIG)
    assert df.iloc[0]["signal"] == "SELL"


def test_hold_signal():
    df = score_tickers({"AAPL": 0.1}, {"AAPL": 0.0}, CONFIG)
    assert df.iloc[0]["signal"] == "HOLD"


def test_sorted_by_composite_score():
    tech = {"AAPL": 0.9, "MSFT": 0.3, "TSLA": 0.6}
    sent = {"AAPL": 0.8, "MSFT": 0.2, "TSLA": 0.5}
    df = score_tickers(tech, sent, CONFIG)
    scores = df["composite_score"].tolist()
    assert scores == sorted(scores, reverse=True)


def test_empty_inputs_returns_empty_df():
    df = score_tickers({}, {}, CONFIG)
    assert df.empty


def test_columns_present():
    df = score_tickers({"AAPL": 0.5}, {"AAPL": 0.4}, CONFIG)
    for col in ["ticker", "tech_score", "sentiment_score", "composite_score", "signal"]:
        assert col in df.columns
