from __future__ import annotations

from abc import ABC, abstractmethod

from trading_system.config import RuntimeConfig
from trading_system.data.models import MarketSnapshot


class DataProvider(ABC):
    @abstractmethod
    def load_snapshot(self, config: RuntimeConfig) -> MarketSnapshot:
        raise NotImplementedError
