# Binance Futures Testnet Trading Bot (CLI)

A production-ready, CLI-based trading bot for Binance USDT-M Futures Testnet. It supports Market and Limit orders (BUY/SELL), includes robust validation, structured logging (bot.log), graceful error handling with retries, and modular design. Optional advanced strategies include TWAP, Grid, and a simulated OCO.

## Features
- USDT-M Futures Testnet client with configurable base URL
- Market and Limit orders (BUY/SELL)
- Argument validation (symbol, side, quantity, price, etc.)
- Console output of order details
- Structured logging to `bot.log` with timestamps and responses
- Graceful API error handling with retries
- Modular architecture
- Bonus strategies: TWAP, Grid, Simulated OCO

## Project Structure
```
[project_root]/  
├── src/  
│   ├── market_orders.py  
│   ├── limit_orders.py  
│   ├── cli.py  
│   ├── common.py  
│   ├── logger_setup.py  
│   └── advanced/  
│       ├── oco.py  
│       ├── twap.py  
│       └── grid.py  
├── bot.log  
├── requirements.txt  
├── README.md  
└── report.pdf  
```

## Requirements
- Python 3.8+
- Dependencies: see `requirements.txt`

## Installation
```bash
python -m venv .venv
. .venv/Scripts/activate    # Windows PowerShell
pip install -r requirements.txt
```

## API Keys (Testnet)
Create Futures Testnet API keys on https://testnet.binancefuture.com and fund your testnet wallet. Set credentials as environment variables or pass via CLI:
- `BINANCE_API_KEY`
- `BINANCE_API_SECRET`

## Usage
Run commands from project root.

- Market:
```bash
python src/cli.py market --symbol BTCUSDT --side BUY --quantity 0.001
```

- Limit:
```bash
python src/cli.py limit --symbol BTCUSDT --side SELL --quantity 0.001 --price 50000
```

- TWAP:
```bash
python src/cli.py twap --symbol BTCUSDT --side BUY --total-qty 0.01 --slices 5 --interval 2 --use-market
```

- Grid:
```bash
python src/cli.py grid --symbol BTCUSDT --side SELL --lower 48000 --upper 52000 --steps 4 --order-qty 0.001
```

- Simulated OCO (TP + SL):
```bash
python src/cli.py oco --symbol BTCUSDT --side SELL --quantity 0.001 --tp 52000 --sl 45000
```

### Options
Common options:
- `--api-key`, `--api-secret`: override env vars
- `--base-url`: defaults to Testnet
- `--log-level`: DEBUG/INFO/WARNING/ERROR

## Logging
- All actions and responses are logged to `bot.log` with rotating file handler.
- Console outputs are minimal and human-readable.

## Error Handling
- Retries on transient errors (e.g., rate limits, timeouts) with exponential backoff.
- Clear errors printed to console and logged.

## Report
A concise PDF report (`report.pdf`) describing design choices, example CLI screenshots, and logs can be generated using:
```bash
python generate_report.py
```

## Packaging
Create a zip archive:
```powershell
Compress-Archive -Path src, requirements.txt, bot.log, README.md, report.pdf -DestinationPath binance-bot.zip -Force
```

## Notes
- Ensure you have sufficient testnet balance and correct symbol filters (min qty/price tick) to avoid rejections.
- For advanced automation (e.g., auto-cancel in OCO), integrate the user data stream for order/trade updates.
