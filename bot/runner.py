import logging
from datetime import datetime, timezone

from bot.data.historical_data import fetch_ohlcv
from bot.data.watchlist import load_watchlist
from bot.news import finnhub_ws, rss_feeds
from bot.signals import sentiment, technical
from bot.signals.scorer import score_tickers
from bot.trading import broker, portfolio, risk

logger = logging.getLogger("swing_bot.runner")

_start_equity: float = 0.0


def initialize(config: dict) -> None:
    global _start_equity
    tickers = load_watchlist(config)
    finnhub_ws.start(tickers, config)
    account = broker.get_account()
    _start_equity = account.get("equity", 0.0)
    logger.info(f"Runner initialized. Watching {len(tickers)} tickers. Equity: ${_start_equity:,.2f}")


def run_cycle(config: dict) -> None:
    logger.info("--- Starting scan cycle ---")

    tickers = load_watchlist(config)
    account = broker.get_account()
    open_positions = broker.get_open_positions()
    open_tickers = {p["ticker"] for p in open_positions}

    if risk.check_daily_halt(account, config, _start_equity):
        logger.warning("Daily halt active. Skipping trade execution.")
        return

    # Fetch OHLCV and compute technical scores
    tech_scores: dict[str, float] = {}
    ohlcv_data: dict = {}
    hist_days = config.get("technical", {}).get("historical_bars", 90)

    for ticker in tickers:
        df = fetch_ohlcv(ticker, days=hist_days)
        if not df.empty:
            ohlcv_data[ticker] = df
            tech_scores[ticker] = technical.compute_score(df, config)

    # Fetch news and compute sentiment scores
    rss_articles = rss_feeds.fetch_articles(tickers, config)
    sentiment_scores: dict[str, float] = {}

    lookback_hours = config.get("scoring", {}).get("sentiment_lookback_hours", 24)
    for ticker in tickers:
        ws_articles = finnhub_ws.drain(ticker, max_articles=config.get("news", {}).get("max_articles_per_ticker", 20))
        all_articles = ws_articles + rss_articles.get(ticker, [])
        sentiment_scores[ticker] = sentiment.compute_score(all_articles, config)

    # Score and rank
    scores_df = score_tickers(tech_scores, sentiment_scores, config)
    logger.info(f"\n{scores_df.to_string(index=False)}")

    # Execute trades
    for _, row in scores_df.iterrows():
        ticker = row["ticker"]
        signal = row["signal"]

        if signal == "BUY" and ticker not in open_tickers:
            if not risk.within_position_limit(open_positions, config):
                logger.info("Max open positions reached. Skipping further buys.")
                break
            df = ohlcv_data.get(ticker)
            if df is None:
                continue
            qty = risk.position_size(ticker, df, account, config)
            if qty < 1:
                continue
            order = broker.submit_market_order(ticker, qty, "BUY")
            if order:
                portfolio.record_trade({**order, "timestamp": datetime.now(timezone.utc).isoformat()})
                open_positions.append({"ticker": ticker})

        elif signal == "SELL" and ticker in open_tickers:
            if broker.close_position(ticker):
                portfolio.record_trade({
                    "ticker": ticker,
                    "side": "SELL",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                })

    summary = portfolio.get_summary()
    logger.info(
        f"Cycle complete. Positions: {summary['position_count']} | "
        f"Unrealized P&L: ${summary['total_unrealized_pl']:,.2f}"
    )
