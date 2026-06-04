from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from trading_system.config import RuntimeConfig
from trading_system.contracts.types import (
    DailyReportContract,
    FlowContract,
    HandoffContract,
    MarketRegimeContract,
    NewsItem,
    TimeseriesPoint,
    SymbolReport,
)
from trading_system.data.providers import build_data_provider
from trading_system.features.flow import build_flow_contract
from trading_system.features.regime import classify_market_regime
from trading_system.features.sentiment import build_sentiment_contract
from trading_system.features.technical import atr, bollinger_pct_b, macd, momentum_score, realized_volatility, rsi
from trading_system.models.fusion import direction_bias_from_pattern, fuse_confidence, technical_posture_from_scores
from trading_system.models.pattern import classify_pattern


@dataclass
class PipelineResult:
    report: DailyReportContract
    markdown_path: Path
    json_path: Path


class DailyPipeline:
    def __init__(self, config: RuntimeConfig):
        self.config = config

    def run(self) -> PipelineResult:
        provider = build_data_provider(self.config)
        snapshot = provider.load_snapshot(self.config)
        regime = classify_market_regime(snapshot)

        symbol_reports: list[SymbolReport] = []
        handoff: list[HandoffContract] = []
        confidence_drivers: list[str] = []
        no_trade_flags: list[str] = []

        
        market_timeseries: dict[str, list[TimeseriesPoint]] = {}
        # Collect benchmark timeseries
        market_timeseries[self.config.universe.benchmark] = [
            TimeseriesPoint(date=f'D{i}', close=b.close) 
            for i, b in enumerate(snapshot.benchmark_bars[-20:])
        ]

        for symbol in self.config.universe.symbols:
            symbol_snapshot = snapshot.symbols[symbol]
            sentiment_contract = build_sentiment_contract(symbol, symbol_snapshot.sentiment)
            flow_contract = build_flow_contract(symbol, symbol_snapshot.flow)
            pattern_contract = classify_pattern(symbol_snapshot)

            current_rsi = rsi(symbol_snapshot.bars)
            bb_pct_b = bollinger_pct_b(symbol_snapshot.bars)
            _, macd_histogram = macd(symbol_snapshot.bars)
            momentum = momentum_score(symbol_snapshot.bars)
            technical_score = max(min(momentum * 8 + macd_histogram * 0.2, 1.0), -1.0)
            technical_posture = technical_posture_from_scores(momentum, current_rsi, macd_histogram)
            confidence = fuse_confidence(
                regime_score=regime.score,
                technical_score=technical_score,
                sentiment=sentiment_contract,
                flow=flow_contract,
                pattern=pattern_contract,
            )

            risk_flags: list[str] = []
            if symbol_snapshot.earnings_within_days is not None and symbol_snapshot.earnings_within_days <= 3:
                risk_flags.append("earnings_near")
            if abs(flow_contract.gamma_exposure) >= 0.7:
                risk_flags.append("gamma_extreme")
            if current_rsi >= 75:
                risk_flags.append("overbought")
            if current_rsi <= 30:
                risk_flags.append("oversold")
            if bb_pct_b >= 1.0:
                risk_flags.append("bollinger_upper_break")
            if bb_pct_b <= 0.0:
                risk_flags.append("bollinger_lower_break")

            no_trade = confidence < 0.6 or regime.name == "Risk Off"
            if no_trade:
                no_trade_flags.append(f"{symbol}: confidence or regime filter")

            direction_bias = direction_bias_from_pattern(pattern_contract.setup_class)
            supporting_features = {
                "rsi": round(current_rsi, 4),
                "bollinger_pct_b": round(bb_pct_b, 4),
                "macd_histogram": round(macd_histogram, 4),
                "atr": round(atr(symbol_snapshot.bars), 4),
                "realized_volatility": round(realized_volatility(symbol_snapshot.bars), 4),
                "momentum": round(momentum, 4),
                "sentiment_score": sentiment_contract.score,
                "flow_score": flow_contract.score,
                "fear_greed": snapshot.fear_greed_index,
            }

            symbol_report = SymbolReport(
                ticker=symbol,
                direction_bias=direction_bias,
                setup_class=pattern_contract.setup_class,
                confidence=confidence,
                regime=regime.name,
                technical_posture=technical_posture,
                no_trade=no_trade,
                risk_flags=risk_flags,
                supporting_features=supporting_features,
                sentiment=sentiment_contract,
                flow=flow_contract,
                pattern=pattern_contract,
            )
            
            market_timeseries[symbol] = [
                TimeseriesPoint(date=f'D{i}', close=b.close) 
                for i, b in enumerate(symbol_snapshot.bars[-20:])
            ]

            symbol_reports.append(symbol_report)
            confidence_drivers.append(
                f"{symbol}: {technical_posture}, sentiment delta {sentiment_contract.mention_delta}, flow {flow_contract.dealer_positioning}"
            )
            handoff.append(
                HandoffContract(
                    ticker=symbol,
                    setup_class=pattern_contract.setup_class,
                    direction_bias=direction_bias,
                    confidence=confidence,
                    regime=regime.name,
                    risk_flags=risk_flags,
                    supporting_features=supporting_features,
                )
            )

        top_symbol = max(symbol_reports, key=lambda item: item.confidence)
        # Generate News (Mocking top 12)
        top_12_news = [
            NewsItem(topic='Market Regime', sentiment_score=regime.score, summary=regime.summary),
            NewsItem(topic=f'Benchmark: {self.config.universe.benchmark}', sentiment_score=0.1, summary='Tracking core index performance.'),
        ]
        for symbol in symbol_reports[:10]:
            top_12_news.append(
                NewsItem(
                    topic=f'Symbol: {symbol.ticker}', 
                    sentiment_score=symbol.sentiment.score if symbol.sentiment else 0.0, 
                    summary=f'{symbol.technical_posture} posture with {symbol.setup_class} setup.'
                )
            )
        while len(top_12_news) < 12:
            top_12_news.append(NewsItem(topic='Macro Update', sentiment_score=0.0, summary='Steady state macro flow.'))

        report = DailyReportContract(
            generated_at=snapshot.generated_at,
            benchmark=self.config.universe.benchmark,
            market_regime=MarketRegimeContract(
                name=regime.name,
                score=round(regime.score, 4),
                summary=regime.summary,
                drivers=regime.drivers,
            ),
            top_setup=f"{top_symbol.ticker} {top_symbol.setup_class}",
            no_trade_flags=no_trade_flags,
            confidence_drivers=confidence_drivers,
            symbols=symbol_reports,
            downstream_handoff=handoff,
            top_12_news=top_12_news,
            market_timeseries=market_timeseries,
        )

        output_dir = self.config.reporting.output_dir
        output_dir.mkdir(parents=True, exist_ok=True)
        markdown_path = output_dir / "daily_report.md"
        json_path = output_dir / "daily_report.json"
        markdown_path.write_text(self._render_markdown(report), encoding="utf-8")
        json_path.write_text(json.dumps(report.to_dict(), indent=2), encoding="utf-8")

        return PipelineResult(
            report=report,
            markdown_path=markdown_path,
            json_path=json_path,
        )

    def _render_markdown(self, report: DailyReportContract) -> str:
        lines = [
            "# Diamond Hands Market Bridge Report",
            "",
            f"Generated: {report.generated_at}",
            f"Benchmark: {report.benchmark}",
            "",
            "## Market Regime",
            f"- Regime: {report.market_regime.name}",
            f"- Score: {report.market_regime.score}",
            f"- Summary: {report.market_regime.summary}",
            "",
            "## Regime Drivers",
        ]
        for driver in report.market_regime.drivers:
            lines.append(f"- {driver}")
        lines.extend(["", "## Symbol Summaries"])
        for symbol in report.symbols:
            lines.extend(
                [
                    f"### {symbol.ticker}",
                    f"- Technical Posture: {symbol.technical_posture}",
                    f"- Setup Class: {symbol.setup_class}",
                    f"- Direction Bias: {symbol.direction_bias}",
                    f"- Confidence: {symbol.confidence}",
                    f"- No Trade: {symbol.no_trade}",
                    f"- Risk Flags: {', '.join(symbol.risk_flags) if symbol.risk_flags else 'none'}",
                ]
            )
        lines.extend(
            [
                "",
                "## Top Setup",
                f"- {report.top_setup}",
                "",
                "## No-Trade Flags",
            ]
        )
        if report.no_trade_flags:
            lines.extend(f"- {flag}" for flag in report.no_trade_flags)
        else:
            lines.append("- none")
        lines.extend(["", "## Confidence Drivers"])
        lines.extend(f"- {driver}" for driver in report.confidence_drivers)
        return "\n".join(lines) + "\n"
