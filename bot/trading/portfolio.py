import json
import logging
from pathlib import Path

from bot.trading import broker

logger = logging.getLogger("swing_bot.portfolio")

_LEDGER_PATH = Path("data/trades.json")


def get_summary() -> dict:
    account = broker.get_account()
    positions = broker.get_open_positions()
    total_pl = sum(p["unrealized_pl"] for p in positions)
    return {
        "account": account,
        "open_positions": positions,
        "total_unrealized_pl": round(total_pl, 2),
        "position_count": len(positions),
    }


def record_trade(trade: dict) -> None:
    ledger = []
    if _LEDGER_PATH.exists():
        try:
            ledger = json.loads(_LEDGER_PATH.read_text())
        except Exception:
            ledger = []
    ledger.append(trade)
    _LEDGER_PATH.parent.mkdir(parents=True, exist_ok=True)
    _LEDGER_PATH.write_text(json.dumps(ledger, indent=2))
    logger.info(f"Trade recorded: {trade}")


def load_ledger() -> list[dict]:
    if not _LEDGER_PATH.exists():
        return []
    try:
        return json.loads(_LEDGER_PATH.read_text())
    except Exception:
        return []
