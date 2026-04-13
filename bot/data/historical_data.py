import logging
from datetime import datetime, timedelta

import pandas as pd
import yfinance as yf

from bot.utils.cache import TTLCache

logger = logging.getLogger("swing_bot.historical_data")
_cache = TTLCache(ttl_seconds=3600)


def fetch_ohlcv(ticker: str, days: int = 90) -> pd.DataFrame:
    cached = _cache.get(f"{ticker}_{days}")
    if cached is not None:
        return cached

    end = datetime.today()
    start = end - timedelta(days=days)
    try:
        df = yf.download(
            ticker,
            start=start.strftime("%Y-%m-%d"),
            end=end.strftime("%Y-%m-%d"),
            progress=False,
            auto_adjust=True,
        )
        if df.empty:
            logger.warning(f"No historical data returned for {ticker}")
            return pd.DataFrame()
        df.columns = [c.lower() for c in df.columns]
        _cache.set(f"{ticker}_{days}", df)
        return df
    except Exception as e:
        logger.error(f"Failed to fetch historical data for {ticker}: {e}")
        return pd.DataFrame()


def fetch_ohlcv_bulk(tickers: list[str], days: int = 90) -> dict[str, pd.DataFrame]:
    result = {}
    for ticker in tickers:
        df = fetch_ohlcv(ticker, days)
        if not df.empty:
            result[ticker] = df
    return result
