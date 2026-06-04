from __future__ import annotations

from trading_system.contracts.types import SentimentContract
from trading_system.data.models import SentimentPoint


def build_sentiment_contract(symbol: str, sentiment: SentimentPoint | None) -> SentimentContract:
    if sentiment is None:
        return SentimentContract(
            symbol=symbol,
            score=0.0,
            mention_delta=0,
            source_breakdown={},
        )

    mention_delta = sentiment.mentions_today - sentiment.mentions_yesterday
    intensity = mention_delta / max(sentiment.mentions_yesterday, 1)
    score = max(min(sentiment.score + intensity * 0.1, 1.0), -1.0)

    return SentimentContract(
        symbol=symbol,
        score=round(score, 4),
        mention_delta=mention_delta,
        source_breakdown=sentiment.sources,
    )
