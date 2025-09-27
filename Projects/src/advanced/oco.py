from typing import Any, Dict, Optional
import logging

from common import retry_api_call, print_order_result


def place_simulated_oco(
    client,
    symbol: str,
    side: str,
    quantity: float,
    take_profit_price: float,
    stop_price: float,
    recv_window: Optional[int] = 5000,
    logger: Optional[logging.Logger] = None,
) -> Dict[str, Any]:
    """
    Simulate OCO in Futures by placing a TAKE_PROFIT limit and a STOP_MARKET order.
    When one is filled, user should cancel the other (can be automated with user data stream).
    """
    tp_payload = {
        "symbol": symbol,
        "side": side,
        "type": "TAKE_PROFIT",
        "timeInForce": "GTC",
        "quantity": quantity,
        "price": take_profit_price,
        "stopPrice": take_profit_price,
    }
    sl_payload = {
        "symbol": symbol,
        "side": side,
        "type": "STOP_MARKET",
        "quantity": quantity,
        "stopPrice": stop_price,
    }
    if recv_window:
        tp_payload["recvWindow"] = recv_window
        sl_payload["recvWindow"] = recv_window

    if logger:
        logger.info(f"Submitting TAKE_PROFIT: {tp_payload}")
    tp_result = retry_api_call(client.new_order, logger=logger, **tp_payload)
    if logger:
        logger.info(f"TAKE_PROFIT response: {tp_result}")
    print_order_result(tp_result)

    if logger:
        logger.info(f"Submitting STOP_MARKET: {sl_payload}")
    sl_result = retry_api_call(client.new_order, logger=logger, **sl_payload)
    if logger:
        logger.info(f"STOP_MARKET response: {sl_result}")
    print_order_result(sl_result)

    return {"take_profit": tp_result, "stop_market": sl_result}