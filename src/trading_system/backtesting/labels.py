from __future__ import annotations

from trading_system.data.models import PriceBar
from trading_system.features.technical import breakout_score, momentum_score, rsi


def label_setup(bars: list[PriceBar]) -> str:
    breakout = breakout_score(bars)
    momentum = momentum_score(bars)
    current_rsi = rsi(bars)

    if breakout > 0.1 and momentum > 0.02:
        return "momentum_breakout"
    if breakout < 0 and current_rsi > 60:
        return "failed_breakout"
    if current_rsi < 42:
        return "mean_reversion"
    return "trend_continuation"
