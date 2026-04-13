import logging
import re
from datetime import datetime, timezone

import feedparser

logger = logging.getLogger("swing_bot.rss_feeds")

_seen_guids: set[str] = set()


def fetch_articles(tickers: list[str], config: dict) -> dict[str, list[dict]]:
    feeds = config.get("news", {}).get("rss_feeds", [])
    max_per_ticker = config.get("news", {}).get("max_articles_per_ticker", 20)
    results: dict[str, list[dict]] = {t: [] for t in tickers}

    for feed_cfg in feeds:
        url = feed_cfg.get("url", "")
        source = feed_cfg.get("source", "rss")
        try:
            parsed = feedparser.parse(url)
        except Exception as e:
            logger.warning(f"Failed to parse RSS feed {url}: {e}")
            continue

        for entry in parsed.entries:
            guid = entry.get("id", entry.get("link", ""))
            if guid in _seen_guids:
                continue
            _seen_guids.add(guid)

            title = entry.get("title", "")
            summary = entry.get("summary", "")
            text = f"{title} {summary}"
            published = entry.get("published", "")

            for ticker in tickers:
                if re.search(rf"\b{re.escape(ticker)}\b", text, re.IGNORECASE):
                    if len(results[ticker]) < max_per_ticker:
                        results[ticker].append({
                            "headline": title,
                            "source": source,
                            "published": published,
                        })

    return results
