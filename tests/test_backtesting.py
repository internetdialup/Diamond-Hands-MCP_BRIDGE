from __future__ import annotations

import unittest

from trading_system.backtesting.labels import label_setup
from trading_system.backtesting.walkforward import generate_walk_forward_splits
from trading_system.data.models import PriceBar


def make_series() -> list[PriceBar]:
    bars = []
    price = 100.0
    for index in range(50):
        close = price + (2.0 if index < 35 else -0.5)
        bars.append(
            PriceBar(
                open=price,
                high=max(price, close) + 0.8,
                low=min(price, close) - 0.8,
                close=close,
                volume=1_500_000,
            )
        )
        price = close
    return bars


class BacktestingScaffoldTests(unittest.TestCase):
    def test_label_setup_is_deterministic(self) -> None:
        bars = make_series()
        self.assertEqual(label_setup(bars), label_setup(list(bars)))

    def test_walk_forward_splits_do_not_overlap_future(self) -> None:
        splits = generate_walk_forward_splits(series_length=120, train_window=60, test_window=15)
        self.assertTrue(splits)
        for split in splits:
            self.assertLessEqual(split.train_end, split.test_start)
            self.assertLess(split.test_start, split.test_end)


if __name__ == "__main__":
    unittest.main()
