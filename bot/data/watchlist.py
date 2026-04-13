import re
from pathlib import Path


def load_watchlist(config: dict) -> list[str]:
    path = Path(config["watchlist"]["path"])
    max_tickers = config["watchlist"].get("max_tickers", 50)

    if not path.exists():
        raise FileNotFoundError(f"Watchlist not found: {path}")

    tickers = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        ticker = line.upper().split()[0]
        if re.match(r"^[A-Z]{1,5}$", ticker):
            tickers.append(ticker)

    return tickers[:max_tickers]
