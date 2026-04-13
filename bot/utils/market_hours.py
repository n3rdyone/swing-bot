from datetime import datetime
import pandas_market_calendars as mcal
import pytz


_nyse = mcal.get_calendar("NYSE")


def is_trading_day(date: datetime | None = None) -> bool:
    if date is None:
        date = datetime.now(pytz.timezone("America/New_York"))
    schedule = _nyse.schedule(
        start_date=date.strftime("%Y-%m-%d"),
        end_date=date.strftime("%Y-%m-%d"),
    )
    return not schedule.empty


def is_market_open() -> bool:
    now = datetime.now(pytz.timezone("America/New_York"))
    if not is_trading_day(now):
        return False
    schedule = _nyse.schedule(
        start_date=now.strftime("%Y-%m-%d"),
        end_date=now.strftime("%Y-%m-%d"),
    )
    market_open = schedule.iloc[0]["market_open"].to_pydatetime()
    market_close = schedule.iloc[0]["market_close"].to_pydatetime()
    return market_open <= now <= market_close
