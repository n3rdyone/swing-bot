import logging
from dataclasses import dataclass

import numpy as np
import pandas as pd

from bot.data.historical_data import fetch_ohlcv
from bot.signals.technical import compute_score as tech_score

logger = logging.getLogger("swing_bot.backtest")


@dataclass
class BacktestResult:
    ticker: str
    total_return_pct: float
    sharpe_ratio: float
    max_drawdown_pct: float
    win_rate: float
    num_trades: int
    equity_curve: list[float]


def run(ticker: str, config: dict) -> BacktestResult | None:
    bt_cfg = config.get("backtest", {})
    initial_capital = bt_cfg.get("initial_capital", 100_000.0)
    start = bt_cfg.get("start_date", "2022-01-01")
    end = bt_cfg.get("end_date", "2024-12-31")

    import yfinance as yf
    df = yf.download(ticker, start=start, end=end, progress=False, auto_adjust=True)
    if df.empty or len(df) < 60:
        logger.warning(f"Not enough data to backtest {ticker}")
        return None

    df.columns = [c.lower() for c in df.columns]

    lookback = config.get("technical", {}).get("historical_bars", 90)
    min_score = config.get("scoring", {}).get("min_composite_score", 0.35)

    cash = initial_capital
    shares = 0.0
    equity_curve = []
    trades = []

    for i in range(lookback, len(df)):
        window = df.iloc[i - lookback:i]
        score = tech_score(window, config)
        price = df["close"].iloc[i]
        equity = cash + shares * price
        equity_curve.append(equity)

        if score >= min_score and shares == 0 and cash > price:
            shares = cash // price
            cash -= shares * price
            trades.append(("BUY", price))
        elif score <= -min_score and shares > 0:
            cash += shares * price
            trades.append(("SELL", price))
            shares = 0

    if shares > 0:
        cash += shares * df["close"].iloc[-1]
        equity_curve[-1] = cash

    total_return = (cash - initial_capital) / initial_capital * 100

    eq = np.array(equity_curve)
    daily_returns = np.diff(eq) / eq[:-1]
    sharpe = (daily_returns.mean() / daily_returns.std() * np.sqrt(252)) if daily_returns.std() > 0 else 0.0

    peak = np.maximum.accumulate(eq)
    drawdown = (peak - eq) / peak
    max_dd = float(drawdown.max() * 100)

    buy_prices = [p for sig, p in trades if sig == "BUY"]
    sell_prices = [p for sig, p in trades if sig == "SELL"]
    wins = sum(1 for b, s in zip(buy_prices, sell_prices) if s > b)
    num_pairs = min(len(buy_prices), len(sell_prices))
    win_rate = wins / num_pairs if num_pairs > 0 else 0.0

    return BacktestResult(
        ticker=ticker,
        total_return_pct=round(total_return, 2),
        sharpe_ratio=round(sharpe, 4),
        max_drawdown_pct=round(max_dd, 2),
        win_rate=round(win_rate, 4),
        num_trades=len(trades),
        equity_curve=equity_curve,
    )
