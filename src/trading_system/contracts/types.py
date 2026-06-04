from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class SentimentContract:
    symbol: str
    score: float
    mention_delta: int
    source_breakdown: dict[str, float]


@dataclass
class FlowContract:
    symbol: str
    score: float
    put_call_ratio: float
    gamma_exposure: float
    dealer_positioning: str


@dataclass
class PatternContract:
    symbol: str
    setup_class: str
    probabilities: dict[str, float]


@dataclass
class HandoffContract:
    ticker: str
    setup_class: str
    direction_bias: str
    confidence: float
    regime: str
    risk_flags: list[str]
    supporting_features: dict[str, float]


@dataclass
class SymbolReport:
    ticker: str
    direction_bias: str
    setup_class: str
    confidence: float
    regime: str
    technical_posture: str
    no_trade: bool
    risk_flags: list[str] = field(default_factory=list)
    supporting_features: dict[str, float] = field(default_factory=dict)
    sentiment: SentimentContract | None = None
    flow: FlowContract | None = None
    pattern: PatternContract | None = None


@dataclass
class MarketRegimeContract:
    name: str
    score: float
    summary: str
    drivers: list[str]


@dataclass
class DailyReportContract:
    generated_at: str
    benchmark: str
    market_regime: MarketRegimeContract
    top_setup: str | None
    no_trade_flags: list[str]
    confidence_drivers: list[str]
    symbols: list[SymbolReport]
    downstream_handoff: list[HandoffContract]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def validate_daily_report_payload(payload: dict[str, Any]) -> None:
    required_top_level = {
        "generated_at",
        "benchmark",
        "market_regime",
        "top_setup",
        "no_trade_flags",
        "confidence_drivers",
        "symbols",
        "downstream_handoff",
    }
    missing = sorted(required_top_level.difference(payload))
    if missing:
        raise ValueError(f"Daily report missing keys: {missing}")

    regime = payload["market_regime"]
    for key in ("name", "score", "summary", "drivers"):
        if key not in regime:
            raise ValueError(f"Market regime missing key: {key}")

    for symbol_payload in payload["symbols"]:
        for key in (
            "ticker",
            "direction_bias",
            "setup_class",
            "confidence",
            "regime",
            "technical_posture",
            "no_trade",
            "risk_flags",
            "supporting_features",
        ):
            if key not in symbol_payload:
                raise ValueError(f"Symbol report missing key: {key}")
