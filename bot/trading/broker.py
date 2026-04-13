import logging
import os

from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce

logger = logging.getLogger("swing_bot.broker")

_PAPER = os.environ.get("ALPACA_PAPER", "true").lower()
if _PAPER != "true":
    raise RuntimeError(
        "ALPACA_PAPER must be 'true'. Remove this check explicitly when ready for live trading."
    )


def _client() -> TradingClient:
    return TradingClient(
        api_key=os.environ["ALPACA_API_KEY"],
        secret_key=os.environ["ALPACA_SECRET_KEY"],
        paper=True,
    )


def get_account() -> dict:
    try:
        account = _client().get_account()
        return {
            "equity": float(account.equity),
            "cash": float(account.cash),
            "buying_power": float(account.buying_power),
            "portfolio_value": float(account.portfolio_value),
        }
    except Exception as e:
        logger.error(f"Failed to fetch account: {e}")
        return {}


def get_open_positions() -> list[dict]:
    try:
        positions = _client().get_all_positions()
        return [
            {
                "ticker": p.symbol,
                "qty": float(p.qty),
                "market_value": float(p.market_value),
                "unrealized_pl": float(p.unrealized_pl),
                "avg_entry_price": float(p.avg_entry_price),
            }
            for p in positions
        ]
    except Exception as e:
        logger.error(f"Failed to fetch positions: {e}")
        return []


def submit_market_order(ticker: str, qty: float, side: str) -> dict | None:
    order_side = OrderSide.BUY if side.upper() == "BUY" else OrderSide.SELL
    req = MarketOrderRequest(
        symbol=ticker,
        qty=qty,
        side=order_side,
        time_in_force=TimeInForce.DAY,
    )
    try:
        logger.info(f"Submitting {side} order: {qty} shares of {ticker} (paper)")
        order = _client().submit_order(req)
        return {"id": str(order.id), "ticker": ticker, "qty": qty, "side": side}
    except Exception as e:
        logger.error(f"Order failed for {ticker}: {e}")
        return None


def close_position(ticker: str) -> bool:
    try:
        logger.info(f"Closing position: {ticker} (paper)")
        _client().close_position(ticker)
        return True
    except Exception as e:
        logger.error(f"Failed to close position {ticker}: {e}")
        return False
