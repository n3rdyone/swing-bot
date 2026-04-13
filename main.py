#!/usr/bin/env python3
"""
swing-bot — Daily swing trading bot using news sentiment and technical analysis.
Paper trading only via Alpaca.
"""

import os
from pathlib import Path

import yaml
from dotenv import load_dotenv

load_dotenv()

import logging
from bot.utils.logger import setup_logger


def load_config() -> dict:
    path = Path(__file__).parent / "config.yaml"
    with open(path) as f:
        return yaml.safe_load(f)


def main():
    config = load_config()
    logger = setup_logger(config)
    logger.info("swing-bot starting up...")

    from bot.runner import initialize, run_cycle
    initialize(config)

    import sys
    if "--run-once" in sys.argv:
        logger.info("Running single cycle (--run-once)")
        run_cycle(config)
    else:
        from bot.scheduler import start
        start(config, run_cycle)


if __name__ == "__main__":
    main()
