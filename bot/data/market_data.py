import logging
import os

from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockLatestQuoteRequest, StockBarsRequest
from alpaca.data.timeframe import TimeFrame

logger = logging.getLogger("swing_bot.market_data")


def _client() -> StockHistoricalDataClient:
    return StockHistoricalDataClient(
        api_key=os.environ["ALPACA_API_KEY"],
        secret_key=os.environ["ALPACA_SECRET_KEY"],
    )


def get_latest_quotes(tickers: list[str]) -> dict:
    try:
        client = _client()
        req = StockLatestQuoteRequest(symbol_or_symbols=tickers)
        quotes = client.get_stock_latest_quote(req)
        return {sym: q for sym, q in quotes.items()}
    except Exception as e:
        logger.error(f"Failed to fetch latest quotes: {e}")
        return {}


def get_recent_bars(tickers: list[str], days: int = 5) -> dict:
    from datetime import datetime, timedelta
    try:
        client = _client()
        req = StockBarsRequest(
            symbol_or_symbols=tickers,
            timeframe=TimeFrame.Day,
            start=datetime.now() - timedelta(days=days),
        )
        bars = client.get_stock_bars(req)
        return bars.df if hasattr(bars, "df") else {}
    except Exception as e:
        logger.error(f"Failed to fetch recent bars: {e}")
        return {}
