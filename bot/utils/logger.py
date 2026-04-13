import logging
import os
from logging.handlers import RotatingFileHandler


def setup_logger(config: dict) -> logging.Logger:
    log_cfg = config.get("logging", {})
    level = getattr(logging, log_cfg.get("level", "INFO").upper(), logging.INFO)
    log_file = log_cfg.get("log_file", "logs/swing_bot.log")
    max_bytes = log_cfg.get("max_bytes", 10 * 1024 * 1024)
    backup_count = log_cfg.get("backup_count", 5)

    os.makedirs(os.path.dirname(log_file), exist_ok=True)

    logger = logging.getLogger("swing_bot")
    logger.setLevel(level)

    if not logger.handlers:
        fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")

        fh = RotatingFileHandler(log_file, maxBytes=max_bytes, backupCount=backup_count)
        fh.setFormatter(fmt)
        logger.addHandler(fh)

        ch = logging.StreamHandler()
        ch.setFormatter(fmt)
        logger.addHandler(ch)

    return logger
