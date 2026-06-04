from __future__ import annotations

from trading_system.contracts.types import PatternContract
from trading_system.data.models import SymbolSnapshot
from trading_system.features.technical import breakout_score, ema, macd, mean_reversion_score, momentum_score, rsi


def classify_pattern(snapshot: SymbolSnapshot) -> PatternContract:
    closes = [bar.close for bar in snapshot.bars]
    short_ema = ema(closes[-10:], 10)
    long_ema = ema(closes[-20:], 20)
    current_rsi = rsi(snapshot.bars)
    macd_line, macd_histogram = macd(snapshot.bars)
    momentum = momentum_score(snapshot.bars)
    breakout = breakout_score(snapshot.bars)
    mean_revert = mean_reversion_score(snapshot.bars)

    probabilities = {
        "momentum_breakout": 0.2,
        "failed_breakout": 0.15,
        "mean_reversion": 0.15,
        "trend_continuation": 0.2,
    }

    if breakout > 0.1 and current_rsi >= 58 and macd_histogram > 0:
        probabilities["momentum_breakout"] += 0.45
    if breakout < 0 and current_rsi >= 60 and macd_histogram < 0:
        probabilities["failed_breakout"] += 0.4
    if mean_revert > 1.0 and current_rsi <= 45:
        probabilities["mean_reversion"] += 0.5
    if short_ema > long_ema and momentum > 0.015 and macd_line > 0:
        probabilities["trend_continuation"] += 0.45

    total = sum(probabilities.values())
    normalized = {key: round(value / total, 4) for key, value in probabilities.items()}
    setup = max(normalized, key=normalized.get)

    return PatternContract(
        symbol=snapshot.symbol,
        setup_class=setup,
        probabilities=normalized,
    )
