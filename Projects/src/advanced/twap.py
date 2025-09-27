import time
from typing import Dict, Optional
import logging

from market_orders import place_market_order
from limit_orders import place_limit_order


def execute_twap(
    client,
    symbol: str,
    side: str,
    total_qty: float,
    slices: int = 5,
    interval_sec: float = 2.0,
    use_market: bool = True,
    limit_price: Optional[float] = None,
    time_in_force: str = "GTC",
    recv_window: Optional[int] = 5000,
    logger: Optional[logging.Logger] = None,
) -> Dict[str, Dict]:
    qty_per_slice = total_qty / max(slices, 1)
    results = {}
    for i in range(slices):
        if use_market:
            res = place_market_order(
                client,
                symbol=symbol,
                side=side,
                quantity=qty_per_slice,
                recv_window=recv_window,
                logger=logger,
            )
        else:
            if limit_price is None:
                raise ValueError("limit_price must be provided when use_market=False")
            res = place_limit_order(
                client,
                symbol=symbol,
                side=side,
                quantity=qty_per_slice,
                price=limit_price,
                time_in_force=time_in_force,
                recv_window=recv_window,
                logger=logger,
            )
        results[f"slice_{i+1}"] = res
        if i < slices - 1:
            if logger:
                logger.info(f"TWAP sleeping {interval_sec}s before next slice...")
            time.sleep(interval_sec)
    return results