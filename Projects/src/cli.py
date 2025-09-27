import argparse
import logging
import os
import sys
from typing import Optional

from logger_setup import setup_logger
from common import (
    create_um_futures_client,
    validate_symbol,
    validate_side,
    validate_positive_float,
    TESTNET_BASE_URL,
)
from market_orders import place_market_order
from limit_orders import place_limit_order
from advanced.twap import execute_twap
from advanced.grid import place_grid
from advanced.oco import place_simulated_oco

try:
    from dotenv import load_dotenv  # type: ignore
except Exception:
    load_dotenv = None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="CLI-based Binance USDT-M Futures Testnet Trading Bot",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "--api-key",
        dest="api_key",
        type=str,
        default=None,
        help="Binance API Key (overrides BINANCE_API_KEY env var)",
    )
    parser.add_argument(
        "--api-secret",
        dest="api_secret",
        type=str,
        default=None,
        help="Binance API Secret (overrides BINANCE_API_SECRET env var)",
    )
    parser.add_argument(
        "--base-url",
        dest="base_url",
        type=str,
        default=TESTNET_BASE_URL,
        help="Futures REST base URL",
    )
    parser.add_argument(
        "--log-level",
        dest="log_level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # Market order
    p_market = subparsers.add_parser("market", help="Place a market order")
    p_market.add_argument("--symbol", required=True, type=str)
    p_market.add_argument("--side", required=True, type=str, choices=["BUY", "SELL"])
    p_market.add_argument("--quantity", required=True, type=float)
    p_market.add_argument("--reduce-only", dest="reduce_only", action="store_true")
    p_market.add_argument("--position-side", dest="position_side", type=str, default=None)
    p_market.add_argument("--recv-window", dest="recv_window", type=int, default=5000)

    # Limit order
    p_limit = subparsers.add_parser("limit", help="Place a limit order")
    p_limit.add_argument("--symbol", required=True, type=str)
    p_limit.add_argument("--side", required=True, type=str, choices=["BUY", "SELL"])
    p_limit.add_argument("--quantity", required=True, type=float)
    p_limit.add_argument("--price", required=True, type=float)
    p_limit.add_argument("--time-in-force", dest="tif", type=str, default="GTC")
    p_limit.add_argument("--reduce-only", dest="reduce_only", action="store_true")
    p_limit.add_argument("--position-side", dest="position_side", type=str, default=None)
    p_limit.add_argument("--recv-window", dest="recv_window", type=int, default=5000)

    # TWAP
    p_twap = subparsers.add_parser("twap", help="Execute a TWAP strategy")
    p_twap.add_argument("--symbol", required=True, type=str)
    p_twap.add_argument("--side", required=True, type=str, choices=["BUY", "SELL"])
    p_twap.add_argument("--total-qty", required=True, type=float)
    p_twap.add_argument("--slices", type=int, default=5)
    p_twap.add_argument("--interval", dest="interval", type=float, default=2.0)
    p_twap.add_argument("--use-market", dest="use_market", action="store_true")
    p_twap.add_argument("--limit-price", dest="limit_price", type=float, default=None)
    p_twap.add_argument("--time-in-force", dest="tif", type=str, default="GTC")
    p_twap.add_argument("--recv-window", dest="recv_window", type=int, default=5000)

    # Grid
    p_grid = subparsers.add_parser("grid", help="Place a price grid of limit orders")
    p_grid.add_argument("--symbol", required=True, type=str)
    p_grid.add_argument("--side", required=True, type=str, choices=["BUY", "SELL"])
    p_grid.add_argument("--lower", dest="lower", required=True, type=float)
    p_grid.add_argument("--upper", dest="upper", required=True, type=float)
    p_grid.add_argument("--steps", dest="steps", required=True, type=int)
    p_grid.add_argument("--order-qty", dest="order_qty", required=True, type=float)
    p_grid.add_argument("--time-in-force", dest="tif", type=str, default="GTC")
    p_grid.add_argument("--recv-window", dest="recv_window", type=int, default=5000)

    # OCO (simulated)
    p_oco = subparsers.add_parser("oco", help="Simulate an OCO with TP and SL")
    p_oco.add_argument("--symbol", required=True, type=str)
    p_oco.add_argument("--side", required=True, type=str, choices=["BUY", "SELL"])
    p_oco.add_argument("--quantity", required=True, type=float)
    p_oco.add_argument("--tp", dest="tp", required=True, type=float, help="Take profit price")
    p_oco.add_argument("--sl", dest="sl", required=True, type=float, help="Stop price")
    p_oco.add_argument("--recv-window", dest="recv_window", type=int, default=5000)

    # Account balance
    p_balance = subparsers.add_parser("balance", help="Show account balance")
    # No extra arguments needed

    # Position risk subcommand
    position_risk_parser = subparsers.add_parser("position-risk", help="Show position risk information")
    position_risk_parser.set_defaults(func=handle_position_risk)

    # User trades subcommand
    user_trades_parser = subparsers.add_parser("user-trades", help="Show recent user trades")
    user_trades_parser.add_argument("--symbol", required=True, type=str, help="Trading symbol, e.g. BTCUSDT")
    user_trades_parser.set_defaults(func=handle_user_trades)

    # Set leverage subcommand
    set_leverage_parser = subparsers.add_parser("set-leverage", help="Set leverage for a symbol")
    set_leverage_parser.add_argument("--symbol", required=True, type=str, help="Trading symbol, e.g. BTCUSDT")
    set_leverage_parser.add_argument("--leverage", required=True, type=int, help="Leverage value (1-125)")
    set_leverage_parser.set_defaults(func=handle_set_leverage)

    # WebSocket streaming subcommand
    ws_stream_parser = subparsers.add_parser("ws-stream", help="Stream real-time trades or order book updates")
    ws_stream_parser.add_argument("--symbol", required=True, type=str, help="Trading symbol, e.g. BTCUSDT")
    ws_stream_parser.add_argument("--stream-type", required=True, choices=["trades", "orderbook"], help="Type of stream: trades or orderbook")
    ws_stream_parser.set_defaults(func=handle_ws_stream)

    return parser


def main(argv: Optional[list] = None) -> int:
    if load_dotenv:
        load_dotenv()

    parser = build_parser()
    args = parser.parse_args(argv)

    logger = setup_logger()
    logger.setLevel(getattr(logging, args.log_level))

    # Validation
    try:
        symbol = validate_symbol(args.symbol) if hasattr(args, "symbol") else None
        side = validate_side(args.side) if hasattr(args, "side") else None
    except Exception as e:
        logger.error(f"Validation error: {e}")
        print(f"Error: {e}")
        return 2

    # Create client
    try:
        client = create_um_futures_client(
            api_key=args.api_key,
            api_secret=args.api_secret,
            base_url=args.base_url,
            logger=logger,
        )
    except Exception as e:
        logger.error(f"Failed to create client: {e}")
        print(f"Error: {e}")
        return 2

    try:
        if args.command == "market":
            qty = validate_positive_float("quantity", args.quantity)
            result = place_market_order(
                client,
                symbol=symbol,
                side=side,
                quantity=qty,
                reduce_only=getattr(args, "reduce_only", None),
                position_side=getattr(args, "position_side", None),
                recv_window=getattr(args, "recv_window", 5000),
                logger=logger,
            )
        elif args.command == "limit":
            qty = validate_positive_float("quantity", args.quantity)
            price = validate_positive_float("price", args.price)
            result = place_limit_order(
                client,
                symbol=symbol,
                side=side,
                quantity=qty,
                price=price,
                time_in_force=args.tif,
                reduce_only=getattr(args, "reduce_only", None),
                position_side=getattr(args, "position_side", None),
                recv_window=getattr(args, "recv_window", 5000),
                logger=logger,
            )
        elif args.command == "twap":
            total_qty = validate_positive_float("total-qty", args.total_qty)
            slices = int(args.slices)
            interval = float(args.interval)
            result = execute_twap(
                client,
                symbol=symbol,
                side=side,
                total_qty=total_qty,
                slices=slices,
                interval_sec=interval,
                use_market=args.use_market,
                limit_price=getattr(args, "limit_price", None),
                time_in_force=args.tif,
                recv_window=getattr(args, "recv_window", 5000),
                logger=logger,
            )
        elif args.command == "grid":
            lower = validate_positive_float("lower", args.lower)
            upper = validate_positive_float("upper", args.upper)
            steps = int(args.steps)
            order_qty = validate_positive_float("order-qty", args.order_qty)
            result = place_grid(
                client,
                symbol=symbol,
                side=side,
                lower_price=lower,
                upper_price=upper,
                steps=steps,
                order_qty=order_qty,
                time_in_force=args.tif,
                recv_window=getattr(args, "recv_window", 5000),
                logger=logger,
            )
        elif args.command == "oco":
            qty = validate_positive_float("quantity", args.quantity)
            tp = validate_positive_float("tp", args.tp)
            sl = validate_positive_float("sl", args.sl)
            result = place_simulated_oco(
                client,
                symbol=symbol,
                side=side,
                quantity=qty,
                take_profit_price=tp,
                stop_price=sl,
                recv_window=getattr(args, "recv_window", 5000),
                logger=logger,
            )
        elif args.command == "balance":
            result = client.balance()
            logger.info(f"Account balance response: {result}")
            print("Account Balance:")
            for entry in result:
                print(f"  Asset: {entry['asset']}, Balance: {entry['balance']}, Available: {entry['availableBalance']}")
        else:
            parser.print_help()
            return 1
    except Exception as e:
        logger.error(f"Execution error: {e}")
        print(f"Error: {e}")
        return 1

    logger.info("Done.")
    return 0


def handle_position_risk(args):
    from binance.um_futures import UMFutures
    import logging
    client = UMFutures(key=args.api_key, secret=args.api_secret, base_url=args.base_url)
    response = client.get_position_risk()
    logging.info(f"Position risk response: {response}")
    print("Position Risk:")
    for pos in response:
        print(f"  Symbol: {pos['symbol']}, PositionAmt: {pos['positionAmt']}, EntryPrice: {pos['entryPrice']}, UnrealizedPnL: {pos['unRealizedProfit']}, Leverage: {pos['leverage']}")
    print("Done.")


def handle_user_trades(args):
    from binance.um_futures import UMFutures
    import logging
    client = UMFutures(key=args.api_key, secret=args.api_secret, base_url=args.base_url)
    response = client.sign_request("GET", "/fapi/v1/userTrades", params={"symbol": args.symbol})
    logging.info(f"User trades response: {response}")
    print(f"User Trades for {args.symbol}:")
    for trade in response:
        print(f"  Id: {trade['id']}, OrderId: {trade['orderId']}, Price: {trade['price']}, Qty: {trade['qty']}, RealizedPnL: {trade['realizedPnl']}, Side: {'BUY' if trade['side'] == 'BUY' else 'SELL'}")
    print("Done.")


def handle_set_leverage(args):
    from binance.um_futures import UMFutures
    import logging
    client = UMFutures(key=args.api_key, secret=args.api_secret, base_url=args.base_url)
    response = client.set_leverage(symbol=args.symbol, leverage=args.leverage)
    logging.info(f"Set leverage response: {response}")
    print(f"Leverage for {args.symbol} set to {args.leverage}.")
    print("Done.")


def handle_ws_stream(args):
    import threading
    from binance.um_futures.websocket import UMFuturesWebsocketClient
    import time
    symbol = args.symbol.lower()
    stream_type = args.stream_type
    ws_client = UMFuturesWebsocketClient()
    def print_trades(msg):
        print(f"Trade: Price={msg['p']}, Qty={msg['q']}, Side={'BUY' if msg['m'] == False else 'SELL'}, Time={msg['T']}")
    def print_orderbook(msg):
        print(f"OrderBook: Bids={msg['b']}, Asks={msg['a']}, Time={msg['E']}")
    if stream_type == "trades":
        ws_client.trade_stream(symbol=symbol, callback=print_trades)
    elif stream_type == "orderbook":
        ws_client.book_ticker_stream(symbol=symbol, callback=print_orderbook)
    print(f"Streaming {stream_type} for {args.symbol}. Press Ctrl+C to exit.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        ws_client.stop()
        print("WebSocket stream stopped.")

    logger.info("Done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())