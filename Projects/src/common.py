import os
import time
import logging
from typing import Any, Callable, Dict, Optional

from binance.um_futures import UMFutures
from binance.error import ClientError, ServerError

TESTNET_BASE_URL = "https://testnet.binancefuture.com"


def create_um_futures_client(
    api_key: Optional[str] = None,
    api_secret: Optional[str] = None,
    base_url: str = TESTNET_BASE_URL,
    timeout: Optional[int] = 10,
    logger: Optional[logging.Logger] = None,
) -> UMFutures:
    """Create a USDT-M Futures client configured for Testnet by default."""
    key = api_key or os.getenv("BINANCE_API_KEY")
    secret = api_secret or os.getenv("BINANCE_API_SECRET")
    if not key or not secret:
        raise RuntimeError(
            "API credentials not provided. Set BINANCE_API_KEY and BINANCE_API_SECRET env vars or pass via CLI."
        )
    client = UMFutures(key=key, secret=secret, base_url=base_url, timeout=timeout)
    # attach simple logger proxy if provided
    if logger:
        client_logger = logging.getLogger("binance_client")
        client_logger.setLevel(logger.level)
    return client


def validate_symbol(symbol: str) -> str:
    if not symbol or not symbol.isalnum():
        raise ValueError("Symbol must be an alphanumeric string, e.g., BTCUSDT")
    return symbol.upper()


def validate_side(side: str) -> str:
    s = side.upper()
    if s not in {"BUY", "SELL"}:
        raise ValueError("Side must be BUY or SELL")
    return s


def validate_positive_float(name: str, value: Any) -> float:
    try:
        v = float(value)
    except Exception:
        raise ValueError(f"{name} must be a number")
    if v <= 0:
        raise ValueError(f"{name} must be greater than 0")
    return v


def retry_api_call(
    func: Callable[..., Dict[str, Any]],
    *args,
    max_retries: int = 3,
    initial_delay: float = 0.7,
    backoff: float = 2.0,
    logger: Optional[logging.Logger] = None,
    **kwargs,
) -> Dict[str, Any]:
    """Retry wrapper for Binance API calls, backing off on transient errors and rate limits."""
    attempt = 0
    delay = initial_delay
    while True:
        try:
            return func(*args, **kwargs)
        except ClientError as e:
            if logger:
                logger.error(
                    f"ClientError(status={e.status_code}, code={getattr(e, 'error_code', '?')}, msg={getattr(e, 'error_message', e)})"
                )
            # Retry on rate limit and timeout style client errors
            if getattr(e, "status_code", 0) in {408, 429}:
                attempt += 1
                if attempt > max_retries:
                    raise
                if logger:
                    logger.info(f"Retrying in {delay:.2f}s (attempt {attempt}/{max_retries})...")
                time.sleep(delay)
                delay *= backoff
            else:
                raise
        except ServerError as e:
            if logger:
                logger.error(f"ServerError: {e}")
            attempt += 1
            if attempt > max_retries:
                raise
            if logger:
                logger.info(f"Retrying in {delay:.2f}s (attempt {attempt}/{max_retries})...")
            time.sleep(delay)
            delay *= backoff


def print_order_result(result: Dict[str, Any]) -> None:
    """Pretty-print key order info to console."""
    keys = [
        "symbol",
        "side",
        "type",
        "status",
        "orderId",
        "clientOrderId",
        "price",
        "avgPrice",
        "origQty",
        "executedQty",
        "cumQuote",
        "timeInForce",
        "reduceOnly",
        "positionSide",
        "updateTime",
    ]
    print("Order Result:")
    for k in keys:
        if k in result:
            print(f"  {k}: {result.get(k)}")