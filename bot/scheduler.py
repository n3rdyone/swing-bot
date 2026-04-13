import logging

from apscheduler.schedulers.blocking import BlockingScheduler

from bot.utils.market_hours import is_trading_day

logger = logging.getLogger("swing_bot.scheduler")


def start(config: dict, run_fn) -> None:
    sched_cfg = config.get("scheduler", {})
    run_time = sched_cfg.get("run_time", "09:35")
    eod_time = sched_cfg.get("eod_report_time", "16:05")
    timezone = sched_cfg.get("timezone", "America/New_York")

    run_hour, run_min = map(int, run_time.split(":"))
    eod_hour, eod_min = map(int, eod_time.split(":"))

    scheduler = BlockingScheduler(timezone=timezone)

    def guarded_run():
        if not is_trading_day():
            logger.info("Not a trading day. Skipping.")
            return
        run_fn(config)

    def eod_report():
        from bot.trading.portfolio import get_summary
        if not is_trading_day():
            return
        summary = get_summary()
        logger.info(
            f"EOD Report | Positions: {summary['position_count']} | "
            f"Unrealized P&L: ${summary['total_unrealized_pl']:,.2f} | "
            f"Equity: ${summary['account'].get('equity', 0):,.2f}"
        )

    scheduler.add_job(guarded_run, "cron", hour=run_hour, minute=run_min)
    scheduler.add_job(eod_report, "cron", hour=eod_hour, minute=eod_min)

    logger.info(f"Scheduler started. Run at {run_time}, EOD report at {eod_time} ({timezone})")
    scheduler.start()
