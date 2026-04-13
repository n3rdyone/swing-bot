import pytest
from unittest.mock import patch
from bot.signals.sentiment import compute_score


CONFIG = {
    "scoring": {
        "sentiment_decay_halflife_hours": 6,
    },
    "nlp": {
        "model": "ProsusAI/finbert",
        "batch_size": 16,
        "max_length": 512,
        "device": "cpu",
    }
}


def test_empty_articles_returns_zero():
    score = compute_score([], CONFIG)
    assert score == 0.0


def test_score_range():
    articles = [{"headline": "Company beats earnings expectations", "published": ""}]
    with patch("bot.signals.sentiment.nlp.score_headlines", return_value=0.7):
        score = compute_score(articles, CONFIG)
        assert -1.0 <= score <= 1.0


def test_positive_news_positive_score():
    articles = [{"headline": "Record profits reported", "published": ""}]
    with patch("bot.signals.sentiment.nlp.score_headlines", return_value=0.8):
        score = compute_score(articles, CONFIG)
        assert score > 0


def test_negative_news_negative_score():
    articles = [{"headline": "Company misses revenue targets", "published": ""}]
    with patch("bot.signals.sentiment.nlp.score_headlines", return_value=-0.6):
        score = compute_score(articles, CONFIG)
        assert score < 0
