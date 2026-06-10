from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

from trading_system.contracts.types import DailyReportContract, SymbolReport

@dataclass
class StrategySignal:
    ticker: str
    action: str  # CALL, PUT, HOLD
    reason: str
    confidence: float

class MomentumStrategy:
    """
    A basic momentum strategy inspired by the private Diamond-Hands-Algo repo.
    Evaluates SPY and QQQ based on technical posture and confidence scores.
    """
    
    def __init__(self):
        self.name = "DH Momentum Alpha"

    def evaluate(self, report: DailyReportContract) -> Dict[str, StrategySignal]:
        signals = {}
        for symbol in report.symbols:
            if symbol.ticker in ["SPY", "QQQ"]:
                action = "HOLD"
                reason = "Neutral signals."
                
                feat = symbol.supporting_features
                sweep = feat.get("liquidity_sweep", "none")
                
                # Enhanced logic using sweeps
                if sweep == "bullish_sweep":
                    action = "CALL"
                    reason = "Institutional liquidity sweep detected at range lows. Reversal likely."
                elif sweep == "bearish_sweep":
                    action = "PUT"
                    reason = "Institutional liquidity sweep detected at range highs. Rejection likely."
                elif symbol.confidence >= 0.75 and symbol.direction_bias == "bullish":
                    action = "CALL"
                    reason = f"High confidence {symbol.technical_posture} with bullish flow."
                elif symbol.confidence >= 0.75 and symbol.direction_bias == "bearish":
                    action = "PUT"
                    reason = f"High confidence bearish reversal detected."
                elif symbol.no_trade:
                    action = "HOLD"
                    reason = "Risk filters triggered (high vol or overbought)."

                signals[symbol.ticker] = StrategySignal(
                    ticker=symbol.ticker,
                    action=action,
                    reason=reason,
                    confidence=symbol.confidence
                )
        return signals
