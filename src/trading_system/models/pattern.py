from __future__ import annotations

from trading_system.contracts.types import PatternContract
from trading_system.data.models import SymbolSnapshot
from trading_system.features.technical import breakout_score, ema, macd, mean_reversion_score, momentum_score, rsi


def classify_pattern(snapshot: SymbolSnapshot) -> PatternContract:
    closes = [bar.close for bar in snapshot.bars]
    short_ema = ema(closes[-10:], 10) if len(closes) >= 10 else 0
    long_ema = ema(closes[-20:], 20) if len(closes) >= 20 else 0
    current_rsi = rsi(snapshot.bars)
    macd_line, macd_histogram = macd(snapshot.bars)
    momentum = momentum_score(snapshot.bars)
    breakout = breakout_score(snapshot.bars)
    mean_revert = mean_reversion_score(snapshot.bars)

    # Default to neutral/transitional to avoid bullish bias
    probabilities = {
        "neutral": 0.25,
        "momentum_breakout": 0.1,
        "failed_breakout": 0.1,
        "mean_reversion": 0.1,
        "trend_continuation": 0.1,
        "trend_breakdown": 0.1,
        "bearish_reversal": 0.1,
    }

    # Bullish Logic
    if breakout > 0.05 and current_rsi >= 55 and macd_histogram > 0:
        probabilities["momentum_breakout"] += 0.4
    if short_ema > long_ema and momentum > 0.01 and macd_line > 0:
        probabilities["trend_continuation"] += 0.4

    # Bearish Logic
    if breakout < -0.05 and current_rsi <= 45 and macd_histogram < 0:
        probabilities["trend_breakdown"] += 0.4
    if (short_ema < long_ema or momentum < -0.01) and macd_histogram < 0:
        probabilities["bearish_reversal"] += 0.4
    if breakout > 0 and current_rsi >= 70 and macd_histogram < 0:
        probabilities["failed_breakout"] += 0.4

    # Over-extended Logic
    if mean_revert > 1.5 and current_rsi <= 32:
        probabilities["mean_reversion"] += 0.6 # Oversold bounce potential
    if mean_revert < -1.5 and current_rsi >= 68:
        probabilities["bearish_reversal"] += 0.6 # Overbought dump potential

    total = sum(probabilities.values())
    normalized = {key: round(value / total, 4) for key, value in probabilities.items()}
    setup = max(normalized, key=normalized.get)

    return PatternContract(
        symbol=snapshot.symbol,
        setup_class=setup,
        probabilities=normalized,
    )
