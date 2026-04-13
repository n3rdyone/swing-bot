import logging

import pandas as pd
import pandas_ta as ta

logger = logging.getLogger("swing_bot.risk")


def position_size(
    ticker: str,
    df: pd.DataFrame,
    account: dict,
    config: dict,
) -> float:
    risk_cfg = config.get("risk", {})
    max_pct = risk_cfg.get("max_position_pct", 0.05)
    use_atr = risk_cfg.get("use_atr_sizing", True)
    atr_mult = risk_cfg.get("atr_multiplier", 1.5)

    portfolio_value = account.get("portfolio_value", 0.0)
    if portfolio_value <= 0:
        return 0.0

    max_dollars = portfolio_value * max_pct

    if use_atr and not df.empty and len(df) >= 14:
        try:
            atr = ta.atr(df["high"], df["low"], df["close"], length=14)
            if atr is not None and not atr.empty:
                atr_val = atr.iloc[-1]
                price = df["close"].iloc[-1]
                risk_per_share = atr_val * atr_mult
                if risk_per_share > 0:
                    atr_shares = max_dollars / risk_per_share
                    price_shares = max_dollars / price if price > 0 else 0
                    shares = min(atr_shares, price_shares)
                    return max(1.0, round(shares, 0))
        except Exception as e:
            logger.warning(f"ATR sizing failed for {ticker}: {e}")

    price = df["close"].iloc[-1] if not df.empty else 0
    if price <= 0:
        return 0.0
    return max(1.0, round(max_dollars / price, 0))


def check_daily_halt(account: dict, config: dict, start_equity: float) -> bool:
    risk_cfg = config.get("risk", {})
    halt_pct = risk_cfg.get("daily_loss_halt_pct", 0.02)
    current_equity = account.get("equity", start_equity)
    loss_pct = (start_equity - current_equity) / start_equity if start_equity > 0 else 0
    if loss_pct >= halt_pct:
        logger.warning(f"Daily loss threshold reached ({loss_pct:.2%}). Halting trades.")
        return True
    return False


def within_position_limit(open_positions: list[dict], config: dict) -> bool:
    max_pos = config.get("risk", {}).get("max_open_positions", 10)
    return len(open_positions) < max_pos
