import logging
import math
from functools import lru_cache

logger = logging.getLogger("swing_bot.nlp")

_pipeline = None


def _load_pipeline(config: dict):
    global _pipeline
    if _pipeline is not None:
        return _pipeline

    from transformers import pipeline
    import torch

    nlp_cfg = config.get("nlp", {})
    model = nlp_cfg.get("model", "ProsusAI/finbert")
    device_cfg = nlp_cfg.get("device", "auto")

    if device_cfg == "auto":
        device = 0 if torch.cuda.is_available() else -1
    elif device_cfg == "cuda":
        device = 0
    else:
        device = -1

    logger.info(f"Loading NLP model '{model}' on {'GPU' if device >= 0 else 'CPU'}...")
    _pipeline = pipeline(
        "text-classification",
        model=model,
        tokenizer=model,
        device=device,
        top_k=None,
    )
    logger.info("NLP model loaded.")
    return _pipeline


def score_headlines(headlines: list[str], config: dict) -> float:
    if not headlines:
        return 0.0

    nlp_cfg = config.get("nlp", {})
    batch_size = nlp_cfg.get("batch_size", 16)
    max_length = nlp_cfg.get("max_length", 512)

    pipe = _load_pipeline(config)

    # Truncate headlines to max_length tokens worth of chars
    truncated = [h[:max_length * 4] for h in headlines]

    try:
        results = pipe(truncated, batch_size=batch_size, truncation=True, max_length=max_length)
    except Exception as e:
        logger.error(f"FinBERT inference failed: {e}")
        return 0.0

    scores = []
    for result in results:
        label_scores = {r["label"].lower(): r["score"] for r in result}
        score = label_scores.get("positive", 0.0) - label_scores.get("negative", 0.0)
        scores.append(score)

    return sum(scores) / len(scores) if scores else 0.0
