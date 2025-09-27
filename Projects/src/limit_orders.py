from typing import Any, Dict, Optional
import logging

from common import retry_api_call, print_order_result


def place_limit_order(
    client,
    symbol: str,
    side: str,
    quantity: float,
    price: float,
    time_in_force: str = "GTC",
    reduce_only: Optional[bool] = None,
    position_side: Optional[str] = None,
    recv_window: Optional[int] = 5000,
    logger: Optional[logging.Logger] = None,
) -> Dict[str, Any]:
    payload = {
        "symbol": symbol,
        "side": side,
        "type": "LIMIT",
        "timeInForce": time_in_force,
        "quantity": quantity,
        "price": price,
    }
    if reduce_only is not None:
        payload["reduceOnly"] = reduce_only
    if position_side:
        payload["positionSide"] = position_side
    if recv_window:
        payload["recvWindow"] = recv_window

    if logger:
        logger.info(f"Submitting LIMIT order: {payload}")

    result = retry_api_call(client.new_order, logger=logger, **payload)

    if logger:
        logger.info(f"Order response: {result}")
    print_order_result(result)
    return result