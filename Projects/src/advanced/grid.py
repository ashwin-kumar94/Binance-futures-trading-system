from typing import Dict, Optional
import logging

from limit_orders import place_limit_order


def place_grid(
    client,
    symbol: str,
    side: str,
    lower_price: float,
    upper_price: float,
    steps: int,
    order_qty: float,
    time_in_force: str = "GTC",
    recv_window: Optional[int] = 5000,
    logger: Optional[logging.Logger] = None,
) -> Dict[str, Dict]:
    if steps < 1:
        raise ValueError("steps must be >= 1")
    if lower_price >= upper_price:
        raise ValueError("lower_price must be less than upper_price")
    gap = (upper_price - lower_price) / steps
    results = {}
    for i in range(steps + 1):
        price = round(lower_price + gap * i, 8)
        if logger:
            logger.info(f"Grid order {i+1}/{steps+1} at price {price}")
        res = place_limit_order(
            client,
            symbol=symbol,
            side=side,
            quantity=order_qty,
            price=price,
            time_in_force=time_in_force,
            recv_window=recv_window,
            logger=logger,
        )
        results[f"order_{i+1}"] = res
    return results