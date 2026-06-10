from __future__ import annotations

import math
from statistics import mean, pstdev

from trading_system.data.models import PriceBar


def closes(bars: list[PriceBar]) -> list[float]:
    return [bar.close for bar in bars]


def ema(values: list[float], span: int) -> float:
    if not values:
        return 0.0
    multiplier = 2 / (span + 1)
    result = values[0]
    for value in values[1:]:
        result = (value - result) * multiplier + result
    return result


def rsi(bars: list[PriceBar], window: int = 14) -> float:
    if len(bars) < window + 1:
        return 50.0
    gains: list[float] = []
    losses: list[float] = []
    values = closes(bars)
    for previous, current in zip(values[-window - 1 : -1], values[-window:]):
        change = current - previous
        gains.append(max(change, 0))
        losses.append(abs(min(change, 0)))
    avg_gain = mean(gains) if gains else 0.0
    avg_loss = mean(losses) if losses else 0.0
    if avg_loss == 0:
        return 100.0
    relative_strength = avg_gain / avg_loss
    return 100 - (100 / (1 + relative_strength))


def macd(bars: list[PriceBar]) -> tuple[float, float]:
    values = closes(bars)
    if not values:
        return 0.0, 0.0
    macd_series: list[float] = []
    for index in range(1, len(values) + 1):
        window = values[:index]
        macd_series.append(ema(window, 12) - ema(window, 26))
    macd_line = macd_series[-1]
    signal_line = ema(macd_series[-9:] if len(macd_series) >= 9 else macd_series, 9)
    return macd_line, macd_line - signal_line


def atr(bars: list[PriceBar], window: int = 14) -> float:
    if len(bars) < 2:
        return 0.0
    true_ranges: list[float] = []
    relevant = bars[-window:]
    previous_close = bars[-window - 1].close if len(bars) > window else bars[0].close
    for bar in relevant:
        tr = max(
            bar.high - bar.low,
            abs(bar.high - previous_close),
            abs(bar.low - previous_close),
        )
        true_ranges.append(tr)
        previous_close = bar.close
    return mean(true_ranges) if true_ranges else 0.0


def realized_volatility(bars: list[PriceBar], window: int = 20) -> float:
    values = closes(bars)
    if len(values) < window + 1:
        return 0.0
    returns = []
    for previous, current in zip(values[-window - 1 : -1], values[-window:]):
        returns.append(math.log(current / previous))
    if len(returns) < 2:
        return 0.0
    return pstdev(returns) * math.sqrt(252)


def momentum_score(bars: list[PriceBar], window: int = 10) -> float:
    values = closes(bars)
    if len(values) <= window:
        return 0.0
    start = values[-window - 1]
    end = values[-1]
    return (end - start) / start


def bollinger_bands(bars: list[PriceBar], window: int = 20, num_std: float = 2.0) -> tuple[float, float, float]:
    values = closes(bars)
    if len(values) < window:
        last = values[-1] if values else 0.0
        return last, last, last
    window_values = values[-window:]
    middle = mean(window_values)
    std = pstdev(window_values)
    upper = middle + (num_std * std)
    lower = middle - (num_std * std)
    return upper, middle, lower


def bollinger_pct_b(bars: list[PriceBar], window: int = 20, num_std: float = 2.0) -> float:
    upper, _, lower = bollinger_bands(bars, window, num_std)
    width = upper - lower
    if width == 0:
        return 0.5
    return (bars[-1].close - lower) / width


def breakout_score(bars: list[PriceBar], window: int = 20) -> float:
    if len(bars) <= window:
        return 0.0
    latest_close = bars[-1].close
    prior_high = max(bar.high for bar in bars[-window - 1 : -1])
    prior_low = min(bar.low for bar in bars[-window - 1 : -1])
    range_width = max(prior_high - prior_low, 1e-6)
    return (latest_close - prior_high) / range_width


def mean_reversion_score(bars: list[PriceBar], window: int = 20) -> float:
    values = closes(bars)
    if len(values) < window:
        return 0.0
    window_values = values[-window:]
    average = mean(window_values)
    deviation = pstdev(window_values) or 1e-6
    return (average - values[-1]) / deviation


def liquidity_sweep(bars: list[PriceBar], window: int = 20) -> str:
    if len(bars) < window + 1:
        return "none"
    
    # Previous range high/low
    prior_bars = bars[-window-1:-1]
    range_high = max(b.high for b in prior_bars)
    range_low = min(b.low for b in prior_bars)
    
    current = bars[-1]
    
    # Bearish Sweep: Price takes range high, but closes back below it
    if current.high > range_high and current.close < range_high:
        return "bearish_sweep"
    
    # Bullish Sweep: Price takes range low, but closes back above it
    if current.low < range_low and current.close > range_low:
        return "bullish_sweep"
        
    return "none"
