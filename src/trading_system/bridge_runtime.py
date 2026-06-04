from __future__ import annotations

import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from trading_system.bridge_config import PublicBridgeConfig, save_public_bridge_config


@dataclass
class BridgeVerification:
    repo_exists: bool
    main_exists: bool
    bridge_config_exists: bool
    compatible: bool
    notes: list[str]


def resolve_private_algo_repo(config: PublicBridgeConfig) -> Path | None:
    repo_path = config.private_algo.repo_path
    if repo_path is None:
        return None
    if repo_path.is_absolute():
        return repo_path
    return (Path.cwd() / repo_path).resolve()


def verify_private_algo_bridge(config: PublicBridgeConfig) -> BridgeVerification:
    notes: list[str] = []
    repo_path = resolve_private_algo_repo(config)
    if repo_path is None:
        notes.append("No private Diamond-Hands-Algo repo configured yet.")
        return BridgeVerification(False, False, False, False, notes)

    repo_exists = repo_path.exists()
    main_exists = (repo_path / "main.py").exists()
    bridge_config_exists = (repo_path / config.private_algo.bridge_config_path).exists()
    pyproject_exists = (repo_path / "pyproject.toml").exists()
    src_exists = (repo_path / "src").exists()

    if repo_exists:
        notes.append(f"Private ALGO repo found at {repo_path}")
    else:
        notes.append(f"Private ALGO repo missing at {repo_path}")
    
    if main_exists:
        notes.append("Private ALGO CLI entrypoint detected.")
    else:
        notes.append("Private ALGO main.py missing.")
        
    if bridge_config_exists:
        notes.append("Private ALGO bridge config detected.")
    else:
        notes.append("Private ALGO bridge config missing.")

    if pyproject_exists:
        notes.append("Private ALGO pyproject.toml detected.")
    
    if src_exists:
        notes.append("Private ALGO src/ directory detected.")
    else:
        notes.append("Private ALGO src/ directory missing (likely broken).")

    compatible = repo_exists and main_exists and bridge_config_exists and src_exists
    if compatible:
        notes.append("Bridge compatibility check passed.")
    else:
        notes.append("Bridge compatibility check failed.")
    return BridgeVerification(repo_exists, main_exists, bridge_config_exists, compatible, notes)


def ensure_local_bridge_config(
    config: PublicBridgeConfig,
    private_algo_repo_override: str | None,
    prompt_user: bool,
) -> tuple[PublicBridgeConfig, bool]:
    created_or_updated = False
    if private_algo_repo_override:
        config.private_algo.repo_path = Path(private_algo_repo_override)
        created_or_updated = True
    elif config.private_algo.repo_path is None and prompt_user:
        suggested = "../Trading-MCP-Algo"
        try:
            response = input(
                f"Private Diamond-Hands-Algo repo path [{suggested}]: "
            ).strip()
        except EOFError:
            response = ""
        if response:
            config.private_algo.repo_path = Path(response)
        else:
            config.private_algo.repo_path = Path(suggested)
        created_or_updated = True

    if not config.config_path.exists():
        created_or_updated = True

    if created_or_updated:
        save_public_bridge_config(config)
    return config, created_or_updated


def hand_off_to_private_algo(
    config: PublicBridgeConfig,
    artifact_path: Path,
) -> subprocess.CompletedProcess[str]:
    repo_path = resolve_private_algo_repo(config)
    if repo_path is None:
        raise FileNotFoundError("No private Diamond-Hands-Algo repo configured.")

    bridge_config_path = repo_path / config.private_algo.bridge_config_path
    if not bridge_config_path.exists():
        raise FileNotFoundError(f"Private ALGO bridge config missing: {bridge_config_path}")

    return subprocess.run(
        [
            sys.executable,
            "main.py",
            "--config",
            str(bridge_config_path),
            "--artifact",
            str(artifact_path),
        ],
        cwd=repo_path,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env={**os.environ, "PYTHONPATH": str(repo_path / "src")},
    )
