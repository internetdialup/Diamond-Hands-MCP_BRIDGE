from __future__ import annotations

import unittest

from trading_system.data.models import PriceBar
from trading_system.features.technical import atr, breakout_score, macd, momentum_score, realized_volatility, rsi


def make_bars() -> list[PriceBar]:
    bars = []
    price = 100.0
    for index in range(30):
        close = price + 1.5
        bars.append(
            PriceBar(
                open=price,
                high=close + 1.0,
                low=price - 1.0,
                close=close,
                volume=1_000_000 + index * 1_000,
            )
        )
        price = close
    return bars


class TechnicalFeatureTests(unittest.TestCase):
    def test_rsi_returns_strong_reading_for_uptrend(self) -> None:
        value = rsi(make_bars())
        self.assertGreaterEqual(value, 70)

    def test_macd_histogram_is_positive_for_uptrend(self) -> None:
        _, histogram = macd(make_bars())
        self.assertGreater(histogram, 0)

    def test_volatility_and_range_metrics_are_non_negative(self) -> None:
        bars = make_bars()
        self.assertGreaterEqual(atr(bars), 0)
        self.assertGreaterEqual(realized_volatility(bars), 0)
        self.assertIsInstance(momentum_score(bars), float)
        self.assertIsInstance(breakout_score(bars), float)


if __name__ == "__main__":
    unittest.main()
