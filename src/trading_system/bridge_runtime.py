from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from trading_system.bridge_config import PublicBridgeConfig, save_public_bridge_config


@dataclass
class BridgeVerification:
    repo_exists: bool
    cli_exists: bool
    bridge_config_exists: bool
    compatible: bool
    notes: list[str]
    training_mode: str | None = None


def resolve_private_algo_repo(config: PublicBridgeConfig) -> Path | None:
    repo_path = config.private_algo.repo_path
    if repo_path is None:
        return None
    if repo_path.is_absolute():
        return repo_path
    return (Path.cwd() / repo_path).resolve()


def verify_private_algo_bridge(config: PublicBridgeConfig, with_ping: bool = True) -> BridgeVerification:
    notes: list[str] = []
    repo_path = resolve_private_algo_repo(config)
    if repo_path is None:
        notes.append("No private Diamond-Hands-Algo repo configured yet.")
        return BridgeVerification(False, False, False, False, notes)

    repo_exists = repo_path.exists()
    bridge_config_exists = (repo_path / config.private_algo.bridge_config_path).exists()
    pyproject_exists = (repo_path / "pyproject.toml").exists()
    package_exists = (repo_path / "src/trading_algo").exists()
    installed_cli_exists = shutil.which("trading-algo") is not None
    module_cli_exists = (repo_path / "src/trading_algo/cli.py").exists()
    cli_exists = installed_cli_exists or module_cli_exists

    if repo_exists:
        notes.append(f"Private ALGO repo found at {repo_path}")
    else:
        notes.append(f"Private ALGO repo missing at {repo_path}")
    
    if cli_exists:
        notes.append("Private ALGO trading-algo CLI detected.")
    else:
        notes.append("Private ALGO trading-algo CLI missing.")
        
    if bridge_config_exists:
        notes.append("Private ALGO bridge config detected.")
    else:
        notes.append("Private ALGO bridge config missing.")

    if pyproject_exists:
        notes.append("Private ALGO pyproject.toml detected.")
    else:
        notes.append("Private ALGO pyproject.toml missing.")
    
    if package_exists:
        notes.append("Private ALGO src/trading_algo package detected.")
    else:
        notes.append("Private ALGO src/trading_algo package missing (likely broken).")

    # Nightshade Alignment (v0.2.4): Permissive verification
    compatible = repo_exists and pyproject_exists
    training_mode = None
    
    if compatible:
        notes.append("Bridge compatibility check passed (Found Repo + Specs).")
        # Add warnings for missing non-critical items
        if not cli_exists: notes.append("⚠️ Warning: 'trading-algo' CLI not found; using module fallback.")
        if not bridge_config_exists: notes.append("⚠️ Warning: Private bridge config missing.")
        if not package_exists: notes.append("⚠️ Warning: src/trading_algo package not found.")
        
        if with_ping:
            try:
                # Pre-flight ping (v0.3.0 contract)
                ping_res = run_private_algo_command(config, ["ping"], capture=True)
                ping_data = json.loads(ping_res.stdout)
                if ping_data.get("ok"):
                    training_mode = ping_data.get("training_mode")
                    ver = ping_data.get("version", "unknown")
                    notes.append(f"Private ALGO probe successful (v{ver}, mode={training_mode})")
            except Exception as e:
                notes.append(f"Private ALGO probe failed/legacy: {e}")
    else:
        notes.append("Bridge compatibility check failed.")
        
    return BridgeVerification(repo_exists, cli_exists, bridge_config_exists, compatible, notes, training_mode)


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

    return run_private_algo_command(
        config,
        ["bridge", "run", "--config", str(bridge_config_path), "--artifact", str(artifact_path)],
        capture=True,
    )


def run_private_algo_command(
    config: PublicBridgeConfig,
    command_args: list[str],
    capture: bool = True,
) -> subprocess.CompletedProcess[str]:
    repo_path = resolve_private_algo_repo(config)
    if repo_path is None:
        raise FileNotFoundError("No private Diamond-Hands-Algo repo configured.")

    executable = shutil.which("trading-algo")
    if executable:
        command = [executable, *command_args]
        env = os.environ.copy()
    else:
        command = [sys.executable, "-m", "trading_algo", *command_args]
        env = {**os.environ, "PYTHONPATH": str(repo_path / "src")}

    return subprocess.run(
        command,
        cwd=repo_path,
        check=True,
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.PIPE if capture else None,
        text=True,
        env=env,
    )
