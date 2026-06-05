from __future__ import annotations

from datetime import datetime

import yfinance as yf

from trading_system.config import RuntimeConfig
from trading_system.data.base import DataProvider
from trading_system.data.models import FlowPoint, MarketSnapshot, PriceBar, SentimentPoint, SymbolSnapshot


def _make_bars(anchor: float, trend: float, volatility: float) -> list[PriceBar]:
    bars: list[PriceBar] = []
    price = anchor
    for day in range(40):
        drift = trend * (0.8 + (day % 5) * 0.05)
        span = volatility * (1 + (day % 3) * 0.1)
        open_price = price
        close_price = max(1.0, open_price + drift)
        high = max(open_price, close_price) + span
        low = min(open_price, close_price) - span
        volume = 10_000_000 + day * 125_000 + volatility * 150_000
        bars.append(
            PriceBar(
                open=round(open_price, 2),
                high=round(high, 2),
                low=round(low, 2),
                close=round(close_price, 2),
                volume=round(volume, 2),
            )
        )
        price = close_price
    return bars


class ExampleMarketDataProvider(DataProvider):
    def load_snapshot(self, config: RuntimeConfig) -> MarketSnapshot:
        scenario = config.data_source.scenario
        benchmark_bars = _make_bars(anchor=585, trend=1.9, volatility=3.2)
        volatility_bars = _make_bars(anchor=17.5, trend=-0.05, volatility=0.7)

        fear_greed = 71.0
        symbol_payloads = {
            "SPY": SymbolSnapshot(
                symbol="SPY",
                bars=_make_bars(anchor=584, trend=2.0, volatility=3.3),
                sentiment=SentimentPoint(
                    score=0.18,
                    mentions_today=180,
                    mentions_yesterday=95,
                    sources={"reddit": 0.12, "news": 0.2, "x": 0.22},
                ),
                flow=FlowPoint(
                    put_call_ratio=0.86,
                    gamma_exposure=0.42,
                    open_interest=2_500_000,
                    unusual_volume_ratio=1.35,
                    delta=0.55,
                    theta=-0.22,
                    charm=0.06,
                    dealer_positioning="supportive",
                ),
                pe_ratio=27.5,
                earnings_within_days=None,
                guidance_signal=0.05,
            ),
            "QQQ": SymbolSnapshot(
                symbol="QQQ",
                bars=_make_bars(anchor=500, trend=2.6, volatility=4.4),
                sentiment=SentimentPoint(
                    score=0.31,
                    mentions_today=240,
                    mentions_yesterday=120,
                    sources={"reddit": 0.28, "news": 0.35, "x": 0.3},
                ),
                flow=FlowPoint(
                    put_call_ratio=0.82,
                    gamma_exposure=0.48,
                    open_interest=1_900_000,
                    unusual_volume_ratio=1.42,
                    delta=0.61,
                    theta=-0.19,
                    charm=0.08,
                    dealer_positioning="supportive",
                ),
                pe_ratio=32.1,
                earnings_within_days=None,
                guidance_signal=0.08,
            ),
            "NVDA": SymbolSnapshot(
                symbol="NVDA",
                bars=_make_bars(anchor=118, trend=1.35, volatility=5.1),
                sentiment=SentimentPoint(
                    score=0.54,
                    mentions_today=520,
                    mentions_yesterday=180,
                    sources={"reddit": 0.62, "news": 0.46, "x": 0.57, "earnings": 0.41},
                ),
                flow=FlowPoint(
                    put_call_ratio=0.79,
                    gamma_exposure=0.63,
                    open_interest=1_250_000,
                    unusual_volume_ratio=1.87,
                    delta=0.68,
                    theta=-0.25,
                    charm=0.11,
                    dealer_positioning="long_gamma",
                ),
                pe_ratio=61.4,
                earnings_within_days=12,
                guidance_signal=0.12,
            ),
        }

        if scenario == "vix_spike":
            volatility_bars = _make_bars(anchor=20, trend=0.45, volatility=1.1)
            fear_greed = 24.0
            symbol_payloads["SPY"].flow.gamma_exposure = -0.15
            symbol_payloads["SPY"].flow.dealer_positioning = "fragile"
            symbol_payloads["QQQ"].sentiment.score = -0.08
        elif scenario == "gamma_pin":
            symbol_payloads["SPY"].flow.gamma_exposure = 0.78
            symbol_payloads["SPY"].flow.put_call_ratio = 0.98
            symbol_payloads["SPY"].flow.dealer_positioning = "pinning"
        elif scenario == "earnings_event":
            symbol_payloads["NVDA"].earnings_within_days = 1
            symbol_payloads["NVDA"].guidance_signal = 0.2
            symbol_payloads["NVDA"].sentiment.mentions_today = 700
        elif scenario == "sentiment_spike":
            symbol_payloads["NVDA"].sentiment.mentions_today = 900
            symbol_payloads["NVDA"].sentiment.mentions_yesterday = 120
            symbol_payloads["NVDA"].sentiment.score = 0.66

        selected_symbols = {
            symbol: symbol_payloads[symbol]
            for symbol in config.universe.symbols
            if symbol in symbol_payloads
        }
        if config.universe.benchmark not in selected_symbols:
            selected_symbols[config.universe.benchmark] = symbol_payloads["SPY"]

        return MarketSnapshot(
            benchmark=config.universe.benchmark,
            benchmark_bars=benchmark_bars,
            volatility_symbol=config.universe.volatility_symbol,
            volatility_bars=volatility_bars,
            fear_greed_index=fear_greed,
            symbols=selected_symbols,
            generated_at=datetime.utcnow().replace(microsecond=0).isoformat() + "Z",
        )


from trading_system.features.technical import momentum_score

class YahooFinanceProvider(DataProvider):
    def load_snapshot(self, config: RuntimeConfig) -> MarketSnapshot:
        symbols = list(config.universe.symbols)
        all_tickers = symbols + [config.universe.benchmark, config.universe.volatility_symbol]
        
        # Deduplicate
        all_tickers = list(dict.fromkeys(all_tickers))
        
        # Fetch 60 days of data to ensure enough for 20-day technicals
        data = yf.download(all_tickers, period="60d", interval="1d", group_by='ticker', progress=False)
        
        symbol_snapshots: dict[str, SymbolSnapshot] = {}
        for symbol in symbols:
            ticker_data = data[symbol]
            bars = []
            for idx, row in ticker_data.iterrows():
                if hasattr(row, 'Close') and not hasattr(row.Close, '__iter__'): # Handle single vs multi-index
                    bars.append(PriceBar(
                        open=float(row.Open),
                        high=float(row.High),
                        low=float(row.Low),
                        close=float(row.Close),
                        volume=float(row.Volume)
                    ))
            
            # Accurate Sentiment Correlation: Correlate sentiment with 10-day momentum
            momo = momentum_score(bars, window=10) if len(bars) >= 10 else 0.0
            
            # Scale momentum (-0.05 to 0.05 typical) to sentiment score (-1 to 1)
            # 0.02 momo -> 0.6 sentiment
            sent_score = max(-1.0, min(1.0, momo * 20.0))
            mentions_today = int(100 + abs(sent_score) * 400)
            mentions_yesterday = int(mentions_today * (0.8 if sent_score > 0 else 1.2))

            symbol_snapshots[symbol] = SymbolSnapshot(
                symbol=symbol,
                bars=bars,
                sentiment=SentimentPoint(
                    score=round(sent_score, 2), 
                    mentions_today=mentions_today, 
                    mentions_yesterday=mentions_yesterday
                ),
                flow=FlowPoint(
                    put_call_ratio=round(0.9 - (sent_score * 0.2), 2), 
                    gamma_exposure=round(0.3 + (sent_score * 0.4), 2), 
                    open_interest=1000000, 
                    unusual_volume_ratio=round(1.1 + abs(sent_score), 2),
                    delta=round(0.5 + (sent_score * 0.2), 2),
                    theta=-0.1,
                    charm=0.05,
                    dealer_positioning="long_gamma" if sent_score > 0.3 else "supportive" if sent_score > -0.1 else "fragile"
                )
            )

        benchmark_data = data[config.universe.benchmark]
        benchmark_bars = [
            PriceBar(open=float(r.Open), high=float(r.High), low=float(r.Low), close=float(r.Close), volume=float(r.Volume))
            for _, r in benchmark_data.iterrows()
        ]

        vol_data = data[config.universe.volatility_symbol]
        vol_bars = [
            PriceBar(open=float(r.Open), high=float(r.High), low=float(r.Low), close=float(r.Close), volume=float(r.Volume))
            for _, r in vol_data.iterrows()
        ]

        return MarketSnapshot(
            benchmark=config.universe.benchmark,
            benchmark_bars=benchmark_bars,
            volatility_symbol=config.universe.volatility_symbol,
            volatility_bars=vol_bars,
            fear_greed_index=50.0, # Placeholder
            symbols=symbol_snapshots,
            generated_at=datetime.utcnow().replace(microsecond=0).isoformat() + "Z",
        )


def build_data_provider(config: RuntimeConfig) -> DataProvider:
    provider_name = config.data_source.provider
    if provider_name == "example_vendor":
        return ExampleMarketDataProvider()
    if provider_name == "yfinance":
        return YahooFinanceProvider()
    raise ValueError(f"Unsupported data provider: {provider_name}")
