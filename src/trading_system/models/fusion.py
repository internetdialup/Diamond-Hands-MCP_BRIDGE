from __future__ import annotations

from trading_system.contracts.types import FlowContract, PatternContract, SentimentContract


def direction_bias_from_pattern(setup_class: str) -> str:
    if setup_class in {"momentum_breakout", "trend_continuation"}:
        return "bullish"
    if setup_class == "mean_reversion":
        return "watch_rebound"
    if setup_class == "failed_breakout":
        return "bearish"
    return "neutral"


def technical_posture_from_scores(
    momentum: float,
    current_rsi: float,
    macd_histogram: float,
) -> str:
    if momentum > 0.015 and current_rsi >= 55 and macd_histogram > 0:
        return "Strong Momentum"
    if momentum > 0 and macd_histogram > 0:
        return "Bullish"
    if momentum < -0.01 and macd_histogram < 0:
        return "Weak"
    return "Mixed"


def fuse_confidence(
    regime_score: float,
    technical_score: float,
    sentiment: SentimentContract,
    flow: FlowContract,
    pattern: PatternContract,
) -> float:
    pattern_score = max(pattern.probabilities.values())
    confidence = (
        regime_score * 0.25
        + technical_score * 0.3
        + sentiment.score * 0.15
        + flow.score * 0.15
        + pattern_score * 0.15
    )
    confidence = (confidence + 1.0) / 2.0
    return round(max(min(confidence, 1.0), 0.0), 4)
