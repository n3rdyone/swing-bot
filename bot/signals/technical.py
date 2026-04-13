import logging

import pandas as pd
import pandas_ta as ta

logger = logging.getLogger("swing_bot.technical")


def compute_score(df: pd.DataFrame, config: dict) -> float:
    if df.empty or len(df) < 30:
        logger.warning("Insufficient data for technical analysis.")
        return 0.0

    indicators = config.get("technical", {}).get("indicators", {})
    votes = []

    try:
        # RSI
        rsi_cfg = indicators.get("rsi", {})
        rsi = ta.rsi(df["close"], length=rsi_cfg.get("period", 14))
        if rsi is not None and not rsi.empty:
            val = rsi.iloc[-1]
            if val < 30:
                votes.append((1.0, rsi_cfg.get("weight", 0.20)))
            elif val > 70:
                votes.append((-1.0, rsi_cfg.get("weight", 0.20)))
            else:
                votes.append((0.0, rsi_cfg.get("weight", 0.20)))

        # MACD
        macd_cfg = indicators.get("macd", {})
        macd = ta.macd(
            df["close"],
            fast=macd_cfg.get("fast", 12),
            slow=macd_cfg.get("slow", 26),
            signal=macd_cfg.get("signal", 9),
        )
        if macd is not None and not macd.empty:
            hist_col = [c for c in macd.columns if "h" in c.lower()]
            if hist_col:
                hist = macd[hist_col[0]].iloc[-1]
                votes.append((1.0 if hist > 0 else -1.0, macd_cfg.get("weight", 0.25)))

        # EMA cross
        ema_cfg = indicators.get("ema_cross", {})
        fast_ema = ta.ema(df["close"], length=ema_cfg.get("fast", 9))
        slow_ema = ta.ema(df["close"], length=ema_cfg.get("slow", 21))
        if fast_ema is not None and slow_ema is not None:
            diff = fast_ema.iloc[-1] - slow_ema.iloc[-1]
            votes.append((1.0 if diff > 0 else -1.0, ema_cfg.get("weight", 0.20)))

        # ADX (trend strength — only adds signal if trend is strong)
        adx_cfg = indicators.get("adx", {})
        adx = ta.adx(df["high"], df["low"], df["close"], length=adx_cfg.get("period", 14))
        if adx is not None and not adx.empty:
            adx_col = [c for c in adx.columns if c.startswith("ADX_")]
            dmp_col = [c for c in adx.columns if c.startswith("DMP_")]
            dmn_col = [c for c in adx.columns if c.startswith("DMN_")]
            if adx_col and dmp_col and dmn_col:
                adx_val = adx[adx_col[0]].iloc[-1]
                if adx_val >= adx_cfg.get("threshold", 25):
                    direction = 1.0 if adx[dmp_col[0]].iloc[-1] > adx[dmn_col[0]].iloc[-1] else -1.0
                    votes.append((direction, adx_cfg.get("weight", 0.15)))

        # Bollinger Bands
        bb_cfg = indicators.get("bbands", {})
        bb = ta.bbands(df["close"], length=bb_cfg.get("period", 20), std=bb_cfg.get("std", 2.0))
        if bb is not None and not bb.empty:
            lower_col = [c for c in bb.columns if "L_" in c]
            upper_col = [c for c in bb.columns if "U_" in c]
            if lower_col and upper_col:
                price = df["close"].iloc[-1]
                lower = bb[lower_col[0]].iloc[-1]
                upper = bb[upper_col[0]].iloc[-1]
                if price <= lower:
                    votes.append((1.0, bb_cfg.get("weight", 0.20)))
                elif price >= upper:
                    votes.append((-1.0, bb_cfg.get("weight", 0.20)))
                else:
                    votes.append((0.0, bb_cfg.get("weight", 0.20)))

    except Exception as e:
        logger.error(f"Error computing technical indicators: {e}")
        return 0.0

    if not votes:
        return 0.0

    total_weight = sum(w for _, w in votes)
    if total_weight == 0:
        return 0.0

    return sum(v * w for v, w in votes) / total_weight
