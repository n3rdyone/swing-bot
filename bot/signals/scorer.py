import logging

import pandas as pd

logger = logging.getLogger("swing_bot.scorer")


def score_tickers(
    tech_scores: dict[str, float],
    sentiment_scores: dict[str, float],
    config: dict,
) -> pd.DataFrame:
    scoring_cfg = config.get("scoring", {})
    tech_weight = scoring_cfg.get("technical_weight", 0.55)
    sent_weight = scoring_cfg.get("sentiment_weight", 0.45)
    min_score = scoring_cfg.get("min_composite_score", 0.35)

    tickers = set(tech_scores) | set(sentiment_scores)
    rows = []

    for ticker in tickers:
        tech = tech_scores.get(ticker, 0.0)
        sent = sentiment_scores.get(ticker, 0.0)
        composite = tech * tech_weight + sent * sent_weight

        if composite >= min_score:
            signal = "BUY"
        elif composite <= -min_score:
            signal = "SELL"
        else:
            signal = "HOLD"

        rows.append({
            "ticker": ticker,
            "tech_score": round(tech, 4),
            "sentiment_score": round(sent, 4),
            "composite_score": round(composite, 4),
            "signal": signal,
        })

    df = pd.DataFrame(rows)
    if df.empty:
        return df

    return df.sort_values("composite_score", ascending=False).reset_index(drop=True)
