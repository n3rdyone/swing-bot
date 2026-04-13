import logging
import math
from datetime import datetime, timezone

from bot.news import nlp

logger = logging.getLogger("swing_bot.sentiment")


def compute_score(articles: list[dict], config: dict) -> float:
    if not articles:
        return 0.0

    scoring_cfg = config.get("scoring", {})
    halflife = scoring_cfg.get("sentiment_decay_halflife_hours", 6)
    decay_lambda = math.log(2) / halflife

    now = datetime.now(timezone.utc)
    weighted_headlines = []
    weights = []

    for article in articles:
        headline = article.get("headline", "")
        if not headline:
            continue

        published = article.get("published", "") or article.get("datetime", "")
        age_hours = 0.0
        if published:
            try:
                if isinstance(published, (int, float)):
                    pub_dt = datetime.fromtimestamp(published, tz=timezone.utc)
                else:
                    from email.utils import parsedate_to_datetime
                    pub_dt = parsedate_to_datetime(published)
                    if pub_dt.tzinfo is None:
                        pub_dt = pub_dt.replace(tzinfo=timezone.utc)
                age_hours = (now - pub_dt).total_seconds() / 3600
            except Exception:
                age_hours = 0.0

        weight = math.exp(-decay_lambda * age_hours)
        weighted_headlines.append(headline)
        weights.append(weight)

    if not weighted_headlines:
        return 0.0

    raw_score = nlp.score_headlines(weighted_headlines, config)

    total_weight = sum(weights)
    avg_weight = total_weight / len(weights) if weights else 1.0
    return max(-1.0, min(1.0, raw_score * avg_weight))
