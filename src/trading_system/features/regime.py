from __future__ import annotations

from dataclasses import dataclass

from trading_system.data.models import MarketSnapshot
from trading_system.features.technical import momentum_score, realized_volatility


@dataclass
class RegimeFeatures:
    score: float
    name: str
    summary: str
    drivers: list[str]


def classify_market_regime(snapshot: MarketSnapshot) -> RegimeFeatures:
    benchmark_momentum = momentum_score(snapshot.benchmark_bars, window=10)
    volatility_momentum = momentum_score(snapshot.volatility_bars, window=10)
    volatility_level = snapshot.volatility_bars[-1].close
    realized_vol = realized_volatility(snapshot.benchmark_bars, window=20)

    score = 0.0
    drivers: list[str] = []
    if benchmark_momentum > 0.02:
        score += 0.35
        drivers.append("The overall market is trending up")
    elif benchmark_momentum < -0.02:
        score -= 0.35
        drivers.append("The overall market is cooling off")

    if snapshot.fear_greed_index >= 60:
        score += 0.2
        drivers.append("Investors are feeling greedy")
    elif snapshot.fear_greed_index <= 40:
        score -= 0.2
        drivers.append("Investors are feeling fearful")

    if volatility_level <= 20 and volatility_momentum <= 0:
        score += 0.2
        drivers.append("Market volatility is low")
    elif volatility_level >= 24 or volatility_momentum > 0.04:
        score -= 0.25
        drivers.append("Market volatility is picking up")

    if realized_vol <= 0.2:
        score += 0.1
        drivers.append("Price action is nice and orderly")
    elif realized_vol >= 0.35:
        score -= 0.1
        drivers.append("Price action is looking stressed")

    if score >= 0.3:
        name = "Risk On"
        summary = "The market is looking strong. It's a good time to ride the trend."
    elif score <= -0.1:
        name = "Risk Off"
        summary = "Things are getting choppy. Time to play defense and protect capital."
    else:
        name = "Transitional"
        summary = "The market can't make up its mind. Be picky with your trades."

    return RegimeFeatures(
        score=max(min(score, 1.0), -1.0),
        name=name,
        summary=summary,
        drivers=drivers,
    )
