from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from trading_system.utils.simple_yaml import load_yaml_like


PUBLIC_BRIDGE_VERSION = "diamond-hands-bridge/v1"
DEFAULT_ROBINHOOD_MCP_URL = "https://agent.robinhood.com/mcp/trading"


@dataclass
class PrivateAlgoConfig:
    repo_path: Path | None
    bridge_config_path: Path
    expected_preview_json: Path


@dataclass
class RobinhoodConfig:
    mcp_url: str
    onboarding_completed: bool


@dataclass
class PublicBridgeConfig:
    version: str
    first_run_completed: bool
    private_algo: PrivateAlgoConfig
    public_artifact_json: Path
    robinhood: RobinhoodConfig
    config_path: Path


def _as_bool(value: Any, default: bool) -> bool:
    if value is None:
        return default
    return bool(value)


def _resolve_optional_path(value: Any) -> Path | None:
    if value in (None, "", "null"):
        return None
    return Path(str(value))


def detect_default_private_algo_repo() -> Path | None:
    candidate = (Path.cwd() / "../Trading-MCP-Algo").resolve()
    if candidate.exists():
        return candidate
    return None


def default_public_bridge_config(config_path: Path) -> PublicBridgeConfig:
    return PublicBridgeConfig(
        version=PUBLIC_BRIDGE_VERSION,
        first_run_completed=False,
        private_algo=PrivateAlgoConfig(
            repo_path=detect_default_private_algo_repo(),
            bridge_config_path=Path("config/bridge.example.yaml"),
            expected_preview_json=Path("outputs/bridge/execution_preview.json"),
        ),
        public_artifact_json=Path("outputs/daily/daily_report.json"),
        robinhood=RobinhoodConfig(
            mcp_url=DEFAULT_ROBINHOOD_MCP_URL,
            onboarding_completed=False,
        ),
        config_path=config_path,
    )


def load_public_bridge_config(config_path: Path) -> PublicBridgeConfig:
    if not config_path.exists():
        return default_public_bridge_config(config_path)

    payload = load_yaml_like(config_path)
    private_payload = payload.get("private_algo", {})
    robinhood_payload = payload.get("robinhood", {})

    return PublicBridgeConfig(
        version=str(payload.get("version", PUBLIC_BRIDGE_VERSION)),
        first_run_completed=_as_bool(payload.get("first_run_completed"), False),
        private_algo=PrivateAlgoConfig(
            repo_path=_resolve_optional_path(private_payload.get("repo_path")),
            bridge_config_path=Path(
                str(private_payload.get("bridge_config_path", "config/bridge.example.yaml"))
            ),
            expected_preview_json=Path(
                str(private_payload.get("expected_preview_json", "outputs/bridge/execution_preview.json"))
            ),
        ),
        public_artifact_json=Path(str(payload.get("public_artifact_json", "outputs/daily/daily_report.json"))),
        robinhood=RobinhoodConfig(
            mcp_url=str(robinhood_payload.get("mcp_url", DEFAULT_ROBINHOOD_MCP_URL)),
            onboarding_completed=_as_bool(robinhood_payload.get("onboarding_completed"), False),
        ),
        config_path=config_path,
    )


def save_public_bridge_config(config: PublicBridgeConfig) -> None:
    config.config_path.parent.mkdir(parents=True, exist_ok=True)
    repo_path = "" if config.private_algo.repo_path is None else str(config.private_algo.repo_path)
    content = "\n".join(
        [
            f"version: {config.version}",
            f"first_run_completed: {'true' if config.first_run_completed else 'false'}",
            f"public_artifact_json: {config.public_artifact_json}",
            "private_algo:",
            f"  repo_path: {repo_path}",
            f"  bridge_config_path: {config.private_algo.bridge_config_path}",
            f"  expected_preview_json: {config.private_algo.expected_preview_json}",
            "robinhood:",
            f"  mcp_url: {config.robinhood.mcp_url}",
            f"  onboarding_completed: {'true' if config.robinhood.onboarding_completed else 'false'}",
            "",
        ]
    )
    config.config_path.write_text(content, encoding="utf-8")

