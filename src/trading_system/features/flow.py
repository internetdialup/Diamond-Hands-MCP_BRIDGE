from __future__ import annotations

from trading_system.contracts.types import FlowContract
from trading_system.data.models import FlowPoint


def build_flow_contract(symbol: str, flow: FlowPoint | None) -> FlowContract:
    if flow is None:
        return FlowContract(
            symbol=symbol,
            score=0.0,
            put_call_ratio=1.0,
            gamma_exposure=0.0,
            dealer_positioning="unknown",
        )

    score = 0.0
    if flow.put_call_ratio < 0.9:
        score += 0.15
    elif flow.put_call_ratio > 1.1:
        score -= 0.15

    score += max(min(flow.gamma_exposure, 1.0), -1.0) * 0.35
    score += min(flow.unusual_volume_ratio - 1.0, 1.0) * 0.2
    if flow.dealer_positioning in {"supportive", "long_gamma"}:
        score += 0.1
    elif flow.dealer_positioning in {"fragile", "short_gamma"}:
        score -= 0.1

    return FlowContract(
        symbol=symbol,
        score=round(max(min(score, 1.0), -1.0), 4),
        put_call_ratio=flow.put_call_ratio,
        gamma_exposure=flow.gamma_exposure,
        dealer_positioning=flow.dealer_positioning,
    )
