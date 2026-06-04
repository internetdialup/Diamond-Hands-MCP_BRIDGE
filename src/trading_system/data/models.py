from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class PriceBar:
    open: float
    high: float
    low: float
    close: float
    volume: float


@dataclass
class SentimentPoint:
    score: float
    mentions_today: int
    mentions_yesterday: int
    sources: dict[str, float] = field(default_factory=dict)


@dataclass
class FlowPoint:
    put_call_ratio: float
    gamma_exposure: float
    open_interest: float
    unusual_volume_ratio: float
    delta: float
    theta: float
    charm: float
    dealer_positioning: str


@dataclass
class SymbolSnapshot:
    symbol: str
    bars: list[PriceBar]
    sentiment: SentimentPoint | None = None
    flow: FlowPoint | None = None
    pe_ratio: float | None = None
    earnings_within_days: int | None = None
    guidance_signal: float | None = None


@dataclass
class MarketSnapshot:
    benchmark: str
    benchmark_bars: list[PriceBar]
    volatility_symbol: str
    volatility_bars: list[PriceBar]
    fear_greed_index: float
    symbols: dict[str, SymbolSnapshot]
    generated_at: str
