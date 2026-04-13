import asyncio
import json
import logging
import os
import queue
import threading
from collections import deque

import websockets

logger = logging.getLogger("swing_bot.finnhub_ws")

_article_queue: queue.Queue = queue.Queue()
_ws_thread: threading.Thread | None = None


async def _run_ws(tickers: list[str], ws_url: str):
    api_key = os.environ.get("FINNHUB_API_KEY", "")
    uri = f"{ws_url}?token={api_key}"

    while True:
        try:
            async with websockets.connect(uri) as ws:
                logger.info("Finnhub WebSocket connected.")
                for ticker in tickers:
                    await ws.send(json.dumps({"type": "subscribe", "symbol": ticker}))

                async for message in ws:
                    data = json.loads(message)
                    if data.get("type") == "news":
                        for article in data.get("data", []):
                            _article_queue.put(article)
        except Exception as e:
            logger.warning(f"Finnhub WS disconnected: {e}. Reconnecting in 5s...")
            await asyncio.sleep(5)


def start(tickers: list[str], config: dict):
    global _ws_thread
    ws_url = config.get("news", {}).get("finnhub_ws_url", "wss://ws.finnhub.io")

    def _thread_target():
        asyncio.run(_run_ws(tickers, ws_url))

    _ws_thread = threading.Thread(target=_thread_target, daemon=True)
    _ws_thread.start()
    logger.info(f"Finnhub WS thread started for {len(tickers)} tickers.")


def drain(ticker: str, max_articles: int = 20) -> list[dict]:
    articles = []
    buf = []

    while not _article_queue.empty():
        try:
            buf.append(_article_queue.get_nowait())
        except queue.Empty:
            break

    for article in buf:
        related = article.get("related", "")
        if ticker in related.split(","):
            articles.append(article)
        else:
            _article_queue.put(article)

    return articles[:max_articles]
