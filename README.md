# swing-bot

A daily swing trading bot that combines **news sentiment analysis** (FinBERT) with **technical analysis** (pandas-ta) to generate BUY/SELL/HOLD signals. Executes paper trades via Alpaca with optional Telegram alerts.

> **Status:** Paper trading. Live trading support is planned for a future release.

---

## How It Works

Each morning at 9:35 AM ET (5 minutes after NYSE open), the bot runs a full scan cycle:

1. **News ingestion** — pulls articles from RSS feeds (Yahoo Finance, Reuters) and a live Finnhub WebSocket stream
2. **Sentiment scoring** — runs headlines through FinBERT (`ProsusAI/finbert`) with time-decay weighting (6-hour half-life, 24-hour lookback)
3. **Technical scoring** — computes RSI, MACD, EMA cross, ADX, and Bollinger Bands across 90 days of OHLCV history
4. **Composite scoring** — blends technical (55%) and sentiment (45%) scores into a single signal
5. **Risk checks** — enforces position limits, portfolio caps, and a daily loss halt
6. **Order execution** — submits market orders via Alpaca; ATR-based position sizing controls trade size
7. **EOD report** — logs a portfolio summary at 4:05 PM ET

---

## Project Structure

```
swing-bot/
├── main.py                   # Entry point
├── config.yaml               # All tunable parameters
├── .env.example              # Required API keys
├── data/
│   └── watchlist.txt         # Tickers to scan (one per line, up to 50)
├── bot/
│   ├── runner.py             # Main scan cycle logic
│   ├── scheduler.py          # APScheduler daily job
│   ├── data/
│   │   ├── market_data.py    # Live price fetching
│   │   ├── historical_data.py# OHLCV history via yfinance
│   │   └── watchlist.py      # Watchlist loader
│   ├── news/
│   │   ├── rss_feeds.py      # RSS feed parser
│   │   ├── finnhub_ws.py     # Finnhub WebSocket client
│   │   └── nlp.py            # FinBERT sentiment inference
│   ├── signals/
│   │   ├── technical.py      # TA indicator scoring
│   │   ├── sentiment.py      # Sentiment aggregation & decay
│   │   └── scorer.py         # Composite score + signal generation
│   ├── trading/
│   │   ├── broker.py         # Alpaca order execution
│   │   ├── portfolio.py      # Trade recording & P&L summary
│   │   └── risk.py           # Position sizing, halt logic
│   ├── backtest/
│   │   └── engine.py         # Historical backtesting engine
│   └── utils/
│       ├── logger.py         # Rotating file + console logger
│       ├── cache.py          # Simple in-memory cache
│       └── market_hours.py   # Market calendar helpers
├── tests/
│   ├── test_risk.py
│   ├── test_scorer.py
│   ├── test_sentiment.py
│   └── test_technical.py
└── logs/                     # Auto-created at runtime
```

---

## Setup

### 1. Clone & install dependencies

```bash
git clone https://github.com/n3rdyone/swing-bot.git
cd swing-bot
pip install -r requirements.txt
```

### 2. Configure API keys

```bash
cp .env.example .env
```

Edit `.env` with your credentials:

```env
ALPACA_API_KEY=your_key
ALPACA_SECRET_KEY=your_secret
ALPACA_PAPER=true

FINNHUB_API_KEY=your_key

# Optional — Telegram alerts
TELEGRAM_BOT_TOKEN=your_token
TELEGRAM_CHAT_ID=your_chat_id
```

- **Alpaca** — [alpaca.markets](https://alpaca.markets) — paper trading account required
- **Finnhub** — [finnhub.io](https://finnhub.io) — free tier is sufficient

### 3. Customize your watchlist

Edit `data/watchlist.txt` — one ticker per line, up to 50. Lines starting with `#` are ignored.

```
AAPL
MSFT
NVDA
# add more tickers here
```

### 4. Tune parameters (optional)

All scoring weights, risk limits, and schedule times are in `config.yaml`. Key settings:

| Parameter | Default | Description |
|---|---|---|
| `scoring.technical_weight` | 0.55 | Weight for technical score |
| `scoring.sentiment_weight` | 0.45 | Weight for sentiment score |
| `scoring.min_composite_score` | 0.35 | Minimum score to trigger a signal |
| `risk.max_position_pct` | 0.05 | Max 5% of portfolio per position |
| `risk.max_open_positions` | 10 | Max simultaneous open positions |
| `risk.daily_loss_halt_pct` | 0.02 | Halt all trading at 2% daily drawdown |
| `scheduler.run_time` | `"09:35"` | Daily scan time (ET) |

---

## Usage

### Run on a schedule (default)

```bash
python main.py
```

Starts the scheduler and runs a scan cycle every trading day at 9:35 AM ET.

### Run a single cycle immediately

```bash
python main.py --run-once
```

Useful for testing or manual scans outside market hours.

### Run the test suite

```bash
pytest tests/
```

---

## Backtesting

The backtest engine replays historical data using the technical scoring logic only (sentiment is not replayed). It reports total return, Sharpe ratio, max drawdown, and win rate.

Configure the backtest window in `config.yaml`:

```yaml
backtest:
  start_date: "2022-01-01"
  end_date: "2024-12-31"
  initial_capital: 100000.0
```

Run a backtest programmatically:

```python
from bot.backtest.engine import run
import yaml

with open("config.yaml") as f:
    config = yaml.safe_load(f)

result = run("AAPL", config)
print(result)
```

Example output:

```
BacktestResult(
    ticker='AAPL',
    total_return_pct=34.5,
    sharpe_ratio=1.23,
    max_drawdown_pct=12.4,
    win_rate=0.61,
    num_trades=42,
    ...
)
```

> Note: Backtests use technical signals only. A CLI wrapper for batch backtesting across the full watchlist is planned.

---

## Telegram Alerts

When `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` are set in `.env`, the bot sends real-time trade notifications to your Telegram chat.

To set up:
1. Create a bot via [@BotFather](https://t.me/BotFather) and copy the token
2. Get your chat ID by messaging [@userinfobot](https://t.me/userinfobot)
3. Add both values to `.env`

---

## Signal Logic

| Composite Score | Signal |
|---|---|
| ≥ 0.35 | **BUY** |
| ≤ −0.35 | **SELL** |
| Between | **HOLD** |

Technical indicators and their weights:

| Indicator | Weight |
|---|---|
| MACD | 25% |
| RSI (14) | 20% |
| EMA Cross (9/21) | 20% |
| Bollinger Bands (20) | 20% |
| ADX (14) | 15% |

---

## Risk Management

- **Position sizing** — ATR-based (1.5× ATR multiplier), capped at 5% of portfolio value per ticker
- **Max positions** — 10 simultaneous open positions
- **Daily halt** — all new buys suspended if portfolio drops 2% from open equity
- **Paper only** — `ALPACA_PAPER=true` enforced by default; live trading requires explicit opt-in (not yet implemented)

---

## Roadmap

- [ ] Live trading support (Alpaca)
- [ ] CLI for batch backtesting across full watchlist
- [ ] Sentiment backtesting (historical news replay)
- [ ] Web dashboard for signal monitoring
- [ ] Additional brokers

---

## License

MIT
