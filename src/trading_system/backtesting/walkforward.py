from __future__ import annotations

from dataclasses import dataclass


@dataclass
class WalkForwardSplit:
    train_start: int
    train_end: int
    test_start: int
    test_end: int


def generate_walk_forward_splits(
    series_length: int,
    train_window: int,
    test_window: int,
) -> list[WalkForwardSplit]:
    splits: list[WalkForwardSplit] = []
    cursor = train_window
    while cursor + test_window <= series_length:
        splits.append(
            WalkForwardSplit(
                train_start=0,
                train_end=cursor,
                test_start=cursor,
                test_end=cursor + test_window,
            )
        )
        cursor += test_window
    return splits
