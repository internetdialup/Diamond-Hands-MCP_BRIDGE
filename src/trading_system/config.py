from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from trading_system.utils.simple_yaml import load_yaml_like


@dataclass
class DataSourceConfig:
    provider: str = "example_vendor"
    timezone: str = "America/Chicago"
    adjusted_prices: bool = True
    scenario: str = "baseline"


@dataclass
class UniverseConfig:
    symbols: list[str]
    benchmark: str
    volatility_symbol: str = "VIX"


@dataclass
class TimeframeConfig:
    primary: str = "1d"
    secondary: list[str] = field(default_factory=list)


@dataclass
class ReportingConfig:
    output_dir: Path = Path("outputs/daily")


@dataclass
class EngineConfig:
    enabled: list[str] = field(
        default_factory=lambda: ["regime", "sentiment", "flow", "pattern"],
    )


@dataclass
class RuntimeConfig:
    universe: UniverseConfig
    timeframes: TimeframeConfig
    data_source: DataSourceConfig
    reporting: ReportingConfig
    engines: EngineConfig


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def load_runtime_config(path: Path) -> RuntimeConfig:
    payload = load_yaml_like(path)

    universe_payload = payload.get("universe", {})
    timeframe_payload = payload.get("timeframes", {})
    source_payload = payload.get("data_source", {})
    reporting_payload = payload.get("reporting", {})
    engine_payload = payload.get("engines", {})

    universe = UniverseConfig(
        symbols=[str(symbol) for symbol in _as_list(universe_payload.get("symbols"))],
        benchmark=str(universe_payload.get("benchmark", "SPY")),
        volatility_symbol=str(universe_payload.get("volatility_symbol", "VIX")),
    )
    timeframes = TimeframeConfig(
        primary=str(timeframe_payload.get("primary", "1d")),
        secondary=[str(item) for item in _as_list(timeframe_payload.get("secondary"))],
    )
    data_source = DataSourceConfig(
        provider=str(source_payload.get("provider", "example_vendor")),
        timezone=str(source_payload.get("timezone", "America/Chicago")),
        adjusted_prices=bool(source_payload.get("adjusted_prices", True)),
        scenario=str(source_payload.get("scenario", "baseline")),
    )
    reporting = ReportingConfig(
        output_dir=Path(str(reporting_payload.get("output_dir", "outputs/daily"))),
    )
    engines = EngineConfig(
        enabled=[str(item) for item in _as_list(engine_payload.get("enabled"))]
        or ["regime", "sentiment", "flow", "pattern"],
    )

    if not universe.symbols:
        raise ValueError("Config must define at least one symbol under universe.symbols")

    return RuntimeConfig(
        universe=universe,
        timeframes=timeframes,
        data_source=data_source,
        reporting=reporting,
        engines=engines,
    )
