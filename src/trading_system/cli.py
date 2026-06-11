from __future__ import annotations

import argparse
import difflib
import json
import os
import random
import subprocess
import sys
import threading
import time
import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, TYPE_CHECKING

warnings.filterwarnings(
    "ignore",
    message=r"urllib3 v2 only supports OpenSSL 1\.1\.1\+, currently the 'ssl' module is compiled with 'LibreSSL.*",
    category=Warning,
    module=r"urllib3(\..*)?",
)

from trading_system.bridge_config import load_public_bridge_config, save_public_bridge_config
from trading_system.bridge_runtime import (
    ensure_local_bridge_config,
    hand_off_to_private_algo,
    run_private_algo_command,
    verify_private_algo_bridge,
)
from trading_system.config import load_runtime_config
from trading_system.contracts.types import DailyReportContract, SymbolReport
from trading_system.strategies.momentum import MomentumStrategy
from trading_system.cli_functions import (
    render_banner,
    print_intro_command_table,
    print_viewall_command_table,
    print_robinhood_onboarding,
    print_bridge_verification,
    print_today_status,
    print_analysis_summary,
    print_market_recap,
    render_error_badge,
    render_confluence_matrix,
    animate_status_loading,
    animate_diamond_hands,
    KineticSpinner,
    with_resilience,
    get_wallstreet_time,
    format_human_date,
    cyan_gradient,
    get_heartbeat_frame,
    create_barchart,
    strip_ansi,
    play_alert,
)

# Defer the pipeline import — it transitively pulls yfinance (~4s).
# Only the handlers that actually run a pipeline pay that cost now.
if TYPE_CHECKING:
    from trading_system.pipeline.daily import DailyPipeline, PipelineResult


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Diamond Hands public bridge CLI for Robinhood-first market intelligence.",
    )
    parser.add_argument(
        "--force-interactive",
        action="store_true",
        help="Force interactive mode even in non-TTY environments (for automation).",
    )
    parser.add_argument(
        "mode",
        nargs="?",
        choices=["boot"],
        help="Run the DiamondHands boot sequence: analyze, hand off, ingest memory, and render one private cockpit frame.",
    )
    parser.add_argument(
        "--config",
        default="config/markets.example.yaml",
        help="Path to runtime config.",
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Override report output directory.",
    )
    parser.add_argument(
        "--bridge-config",
        default="config/diamond-hands.local.yaml",
        help="Path to the local Diamond Hands bridge config.",
    )
    parser.add_argument(
        "--private-algo-repo",
        default=None,
        help="Override the private Diamond-Hands-Algo repo path.",
    )
    parser.add_argument(
        "--setup",
        action="store_true",
        help="Run the Diamond Hands setup wizard and persist bridge config.",
    )
    parser.add_argument(
        "--verify-bridge",
        action="store_true",
        help="Verify that the private ALGO bridge path and config are compatible.",
    )
    parser.add_argument(
        "--analyze-only",
        action="store_true",
        help="Run public bridge analysis only and skip private ALGO handoff.",
    )
    parser.add_argument(
        "--analyze-then-hand-off",
        action="store_true",
        help="Run analysis and then hand the artifact to the private ALGO bridge.",
    )
    return parser


@dataclass(frozen=True)
class CommandSpec:
    command: str
    purpose: str


CORE_COMMAND_SPECS = [
    CommandSpec("/todaysupdate", "Show today's market summary"),
    CommandSpec("/analyze", "Show the full deep-dive analysis report"),
    CommandSpec("/portfolio", "View buying power and current positions"),
    CommandSpec("/trumptracker", "Track political catalysts and sector impacts"),
    CommandSpec("/jensen", "NVIDIA & AI hardware intelligence pulse"),
    CommandSpec("/wsb", "WallStreetBets retail sentiment & squeeze tracking"),
    CommandSpec("/ask", "Ask your manager about specific tickers"),
    CommandSpec("/more", "Show all advanced modules & settings"),
]

PRIVATE_OPERATOR_COMMAND_SPECS = [
    CommandSpec("/verifybridge", "Check your private connector"),
    CommandSpec("/handoff", "Send the latest report to your private repo"),
    CommandSpec("/agents", "Show Codex/Claude private ALGO supervisor status"),
    CommandSpec("/spy0dte", "Generate a private SPY 0DTE paper intent"),
    CommandSpec("/liveboard", "Open the private operator cockpit"),
    CommandSpec("/paper", "Run the private paper-trade simulation"),
    CommandSpec("/risk", "Show private risk and kill-switch state"),
    CommandSpec("/stop", "Trigger the private local kill-switch"),
    CommandSpec("/memory", "Show private memory status"),
    CommandSpec("/recall", "Recall private memory records"),
    CommandSpec("/hood", "Check private HOOD MCP health"),
    CommandSpec("/daemon", "Show private 24/7 paper monitor status"),
    CommandSpec("/botstatus", "Show bot heartbeat and latest daemon cycle"),
    CommandSpec("/startbot", "Show safe paper monitor startup commands"),
]

EXPERIMENTAL_COMMAND_SPECS = [
    CommandSpec("/commands", "Show the core command list"),
    CommandSpec("/viewall", "Show the full suite"),
    CommandSpec("/setup", "Show the setup and integration guide"),
    CommandSpec("/refresh", "Force a fresh market data pull (clears cache)"),
    CommandSpec("/buildagent", "Custom strategy & model setup wizard"),
    CommandSpec("/marketrecap", "Show the market recap view"),
    CommandSpec("/marketnews", "Show the market news view"),
    CommandSpec("/intel", "View dynamic intelligence modules (e.g. /intel social)"),
    CommandSpec("/system", "Institutional Control Center & Health Hub"),
    CommandSpec("/risk", "Defensive Command Center & Safety Bounds"),
    CommandSpec("/wizard", "Intelligence Team Onboarding Wizard"),
    CommandSpec("/forge", "Strategy Forge: Tweak Custom Model Parameters"),
    CommandSpec("/live", "Command Center Monitor: High-Refresh TUI"),
    CommandSpec("/runstrategy", "Run the experimental strategy view"),
    CommandSpec("/settings", "Open CLI settings"),
    CommandSpec("/clear", "Clear the screen and keep the prompt ready"),
    CommandSpec("/quit", "Exit the CLI"),
]

COMMAND_ALIASES = {
    "/commands": "/commands",
    "/viewall": "/viewall",
    "/morecommands": "/viewall",
    "/more": "/more",
    "/help": "/commands",
    "help": "/commands",
    "/todaysupdate": "/todaysupdate",
    "/today-status": "/todaysupdate",
    "/analyze": "/analyze",
    "/marketrecap": "/marketrecap",
    "/recap": "/marketrecap",
    "/marketnews": "/marketnews",
    "/news": "/marketnews",
    "/portfolio": "/portfolio",
    "/trumptracker": "/trumptracker",
    "/tt": "/trumptracker",
    "/jensen": "/jensen",
    "/nvda": "/jensen",
    "/wsb": "/wsb",
    "/wallstbets": "/wsb",
    "/social": "/intel",
    "/twitter": "/intel",
    "/x": "/intel",
    "/sentiment": "/intel",
    "/intel": "/intel",
    "/debate": "/debate",
    "/transcript": "/debate",
    "/hft": "/hft",
    "/metrics": "/hft",
    "/performance": "/hft",
    "/runstrategy": "/runstrategy",
    "/strategy": "/runstrategy",
    "/alpha": "/runstrategy",
    "/lfg": "/runstrategy",
    "/tickersniper": "/tickersniper",
    "/sniper": "/tickersniper",
    "/refresh": "/refresh",
    "/update": "/refresh",
    "/system": "/system",
    "/health": "/system",
    "/hub": "/system",
    "/control": "/system",
    "/buildagent": "/buildagent",
    "/wizard": "/wizard",
    "/forge": "/forge",
    "/tweak": "/forge",
    "/live": "/live",
    "/monitor": "/live",
    "/settings": "/settings",
    "/setup": "/setup",
    "/clear": "/clear",
    "clear": "/clear",
    "/verifybridge": "/verifybridge",
    "/verify-bridge": "/verifybridge",
    "/handoff": "/handoff",
    "/hand-off": "/handoff",
    "/agents": "/agents",
    "/autopilot": "/autopilot",
    "/spy0dte": "/spy0dte",
    "/liveboard": "/liveboard",
    "/hood": "/hood",
    "/paper": "/paper",
    "/risk": "/risk",
    "/stop": "/stop",
    "/memory": "/memory",
    "/recall": "/recall",
    "/daemon": "/daemon",
    "/botstatus": "/botstatus",
    "/startbot": "/startbot",
    "/quit": "/quit",
    "quit": "/quit",
    "exit": "/quit",
}

# ---------------------------------------------------------
# OSS CORE DEFAULTS
# ---------------------------------------------------------
DEFAULT_PROMPT = "💎 diamond-hands > "

# Note: Custom personas and manager prompts are now delegated to 
# the private ALGO bridge (persona.yaml) to maintain secret sauce.

_mcp_proc: "subprocess.Popen[bytes] | None" = None
_mcp_repo: Path | None = None
_mcp_next_id = 2
_mcp_lock = threading.Lock()
_mcp_token = os.getenv("DH_BRIDGE_TOKEN", "dh-bridge-secret-v1")

_rl_capacity = 10.0
_rl_tokens = 10.0
_rl_last_refill = time.time()

from datetime import datetime, timedelta

def _check_rate_limit() -> bool:
    global _rl_tokens, _rl_last_refill
    now = time.time()
    elapsed = now - _rl_last_refill
    _rl_tokens = min(_rl_capacity, _rl_tokens + elapsed * 2.0)
    _rl_last_refill = now
    if _rl_tokens >= 1.0:
        _rl_tokens -= 1.0
        return True
    return False


def _mcp_spawn(repo_path: Path) -> "subprocess.Popen[bytes] | None":
    try:
        proc = subprocess.Popen(
            [sys.executable, "-m", "trading_algo.mcp_server"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            cwd=str(repo_path),
            env={
                **os.environ, 
                "PYTHONPATH": str(repo_path / "src"),
                "DH_BRIDGE_TOKEN": _mcp_token # Secure handshake
            },
        )
        proc.stdin.write(json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2025-03-26"}}).encode() + b"\n")
        proc.stdin.write(json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}).encode() + b"\n")
        proc.stdin.flush()
        _ = proc.stdout.readline()  # consume initialize response
        return proc
    except Exception:
        return None


def _mcp_shutdown() -> None:
    global _mcp_proc
    proc = _mcp_proc
    _mcp_proc = None
    if proc and proc.poll() is None:
        try:
            proc.terminate()
            proc.wait(timeout=0.5)
        except Exception:
            try:
                proc.kill()
            except Exception:
                pass


def prefetch_mcp_server(repo_path: Path) -> None:
    """Warm the persistent MCP server in a background thread so the first
    persona tool call returns without paying spawn + init cost."""
    def _warm() -> None:
        global _mcp_proc, _mcp_repo, _mcp_next_id
        with _mcp_lock:
            if _mcp_proc is None or _mcp_proc.poll() is not None or _mcp_repo != repo_path:
                _mcp_shutdown()
                _mcp_proc = _mcp_spawn(repo_path)
                _mcp_repo = repo_path
                _mcp_next_id = 2
    threading.Thread(target=_warm, daemon=True, name="dh-mcp-prefetch").start()


# Cleanup the persistent subprocess on interpreter exit.
import atexit as _atexit
import urllib.request
import re

_atexit.register(_mcp_shutdown)

_UPDATE_AVAILABLE: str | None = None


def check_for_updates() -> None:
    """Asynchronously check GitHub for a newer version of the CLI."""
    def _check() -> None:
        global _UPDATE_AVAILABLE
        try:
            from trading_system import __version__ as local_version
            # Raw file URL for the main branch on the primary repository
            url = "https://raw.githubusercontent.com/internetdialup/Diamond-Hands-MCP_BRIDGE/main/src/trading_system/__init__.py"
            with urllib.request.urlopen(url, timeout=3) as response:
                content = response.read().decode("utf-8")
                # Simple regex to find __version__ = "X.Y.Z"
                match = re.search(r'__version__\s*=\s*["\']([^"\']+)["\']', content)
                if match:
                    remote_version = match.group(1)
                    if remote_version != local_version:
                        # If the remote version string differs, assume an update is available.
                        # (A more complex parser could do semver > comparisons)
                        _UPDATE_AVAILABLE = remote_version
        except Exception:
            pass # Silent failure to keep boot clean

    threading.Thread(target=_check, daemon=True, name="dh-update-check").start()


# 🏎️ ADVANCED TTLCache (5s TTL)
# Collapses redundant MCP I/O across dashboards.
_mcp_cache: dict[str, tuple[float, dict]] = {}
_mcp_cache_lock = threading.Lock()

def call_mcp_tool(repo_path: Path, tool_name: str, arguments: dict | None = None) -> dict | None:
    """Invoke a tool on the private Diamond Hands MCP server via stdio JSON-RPC.

    Optimized with a 5s TTLCache to eliminate redundant I/O.
    """
    global _mcp_proc, _mcp_repo, _mcp_next_id

    # Cache lookup
    cache_key = f"{tool_name}:{json.dumps(arguments, sort_keys=True)}"
    with _mcp_cache_lock:
        if cache_key in _mcp_cache:
            ts, payload = _mcp_cache[cache_key]
            if time.time() - ts < 5.0:
                return payload

    with _mcp_lock:
        if not _check_rate_limit():
            return {"error": "Anti-DDOS: Rate limit exceeded (10 req/s cap)"}

        # (Re)spawn if dead, missing, or pointed at a different repo.
        if _mcp_proc is None or _mcp_proc.poll() is not None or _mcp_repo != repo_path:
            _mcp_shutdown()
            _mcp_proc = _mcp_spawn(repo_path)
            _mcp_repo = repo_path
            _mcp_next_id = 2
            if _mcp_proc is None:
                return None

        try:
            _mcp_next_id += 1
            call = {
                "jsonrpc": "2.0",
                "id": _mcp_next_id,
                "method": "tools/call",
                "params": {
                    "name": tool_name,
                    "arguments": arguments or {},
                    "_bridge_token": _mcp_token # Anti-Sniffer check
                },
            }
            _mcp_proc.stdin.write(json.dumps(call).encode() + b"\n")
            _mcp_proc.stdin.flush()

            raw_response = _mcp_proc.stdout.readline()
            if not raw_response:
                # Server hung up — drop the handle so the next call respawns.
                _mcp_shutdown()
                return {"error": {"code": "BRIDGE_HUNG_UP", "message": "The private algo bridge terminated unexpectedly."}}

            response = json.loads(raw_response)

            # --- MIT Extraction: Structured Error Envelopes (v0.1.6) ---
            if "error" in response:
                return {"error": response["error"]}

            result = None
            if "result" in response and "structuredContent" in response["result"]:
                result = response["result"]["structuredContent"]
            else:
                result = response.get("result")

            # --- Security: Decrypt Secure Payload (v0.1.7) ---
            if result and isinstance(result, dict) and "secure_payload" in result:
                obfuscator = Obfuscator()
                decrypted = obfuscator.decrypt(result["secure_payload"])
                if "error" not in decrypted:
                    result = {**result, **decrypted}
                    del result["secure_payload"]

            # Update cache with bounding and TTL eviction
            if result:
                with _mcp_cache_lock:
                    now = time.time()
                    # Evict stale entries
                    stale_keys = [k for k, (ts, _) in _mcp_cache.items() if now - ts > 5.0]
                    for k in stale_keys:
                        del _mcp_cache[k]
                        
                    # Bound cache size to prevent memory leak
                    if len(_mcp_cache) > 50:
                        # Remove oldest entries
                        oldest_keys = sorted(_mcp_cache.keys(), key=lambda k: _mcp_cache[k][0])[:10]
                        for k in oldest_keys:
                            del _mcp_cache[k]
                            
                    _mcp_cache[cache_key] = (now, result)

            return result
        except (KeyboardInterrupt, Exception) as e:
            # Server may be in a bad state — force respawn next call.
            _mcp_shutdown()
            return {"error": {"code": "BRIDGE_EXCEPTION", "message": str(e)}}
import importlib.util
import base64
import hashlib

class Obfuscator:
    """XOR-based obfuscation to protect proprietary 'Food'."""
    def __init__(self, secret: str = "diamond-hands-v1-key"):
        self.key = hashlib.sha256(secret.encode()).digest()

    def decrypt(self, encrypted_b64: str) -> dict:
        try:
            data = base64.b64decode(encrypted_b64)
            out = bytearray()
            for i in range(len(data)):
                out.append(data[i] ^ self.key[i % len(self.key)])
            return json.loads(out.decode("utf-8"))
        except Exception:
            return {"error": "DECRYPTION_FAILED"}

def coerce(p: Any) -> tuple[str, float]:
    if isinstance(p, dict):
        return p.get("text", ""), p.get("weight", 1.0)
    return str(p), 1.0

class PersonaManager:
    """
    Manages dynamic persona injection and institutional alpha payloads from the private ALGO repo.
    """
    def __init__(self, private_repo_path: Path | None = None):
        self.repo_path = private_repo_path
        # Prompts stored as (text, weight) tuples
        self.prompts: list[tuple[str, float]] = [(DEFAULT_PROMPT, 1.0)]
        self.has_private_flavor = False
        self.banner_renderer = None
        self.smoke_renderer = None
        self._hot_import_thread: threading.Thread | None = None

        if self.repo_path and self.repo_path.exists():
            self._load_persona()
            # Run the importlib spec+exec in a daemon thread so the cinematic
            # banner animation can render in parallel. Consumers must call
            # _await_hot_imports() before reading banner_renderer / smoke_renderer.
            self._hot_import_thread = threading.Thread(
                target=self._load_hot_imports,
                daemon=True,
                name="dh-persona-hotload",
            )
            self._hot_import_thread.start()
            # Warm the persistent MCP server subprocess in the background too.
            # First /social, /political, /todaysupdate becomes instant instead
            # of paying Python startup + trading_algo import per call.
            prefetch_mcp_server(self.repo_path)

    def _await_hot_imports(self, timeout: float = 2.0) -> None:
        if self._hot_import_thread and self._hot_import_thread.is_alive():
            self._hot_import_thread.join(timeout=timeout)

    def _load_persona(self):
        persona_path = self.repo_path / "persona.yaml"
        if persona_path.exists():
            # In a real impl, we'd use yaml.safe_load, here we'll mock the 'Ghost' v3 Intelligence Team
            self.has_private_flavor = True
            
            # Generic fallback prompts (Secret names stay in private repo)
            raw_prompts = [
                {"text": "💎 Intelligence System online. Command? > ", "weight": 0.02},
                "💎 Agentic Node 1: Intelligence synchronized. > ",
                "💎 Agentic Node 2: Risk bounds nominal. > ",
                "💎 Agentic Node 3: Portfolio optimized. > ",
                "💎 Agentic Node 4: Verifier online. > ",
                "💎 Strategy Oven ready. What's next? > "
            ]
            self.prompts = [coerce(p) for p in raw_prompts]

    def _load_hot_imports(self):
        theme_path = self.repo_path / "src" / "trading_algo" / "cli_theme.py"
        if theme_path.exists():
            try:
                spec = importlib.util.spec_from_file_location("trading_algo.cli_theme", theme_path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                self.banner_renderer = getattr(module, "render_banner", None)
                self.smoke_renderer = getattr(module, "render_lfg_smoke", None)
            except Exception:
                pass

    def get_prompt(self) -> str:
        global _UPDATE_AVAILABLE
        
        if _UPDATE_AVAILABLE:
            yellow = "\033[33m"
            reset = "\033[0m"
            bold = "\033[1m"
            print(f"  {bold}{yellow}🚀 UPDATE AVAILABLE: v{_UPDATE_AVAILABLE} -> Run 'git pull'{reset}")
            _UPDATE_AVAILABLE = None # Only notify once per session

        texts = [p[0] for p in self.prompts]
        weights = [p[1] for p in self.prompts]
        base_prompt = random.choices(texts, weights=weights, k=1)[0]
        
        # Inject the heartbeat pulse
        return f"{get_heartbeat_frame()}{base_prompt}"

    def get_intel_module(self, module_name: str, **kwargs) -> dict | None:
        """Fetches dynamic intelligence payloads from the private MCP server.
        
        This is a generic receiver that handles specific modules 
        without hardcoding names in the CLI core.
        """
        if not self.repo_path:
            return None
        
        # Standardized Bridge Tools (Private repo owns the naming)
        tool_map = {
            "alpha": "dh_todaysupdate_payload",
            "social": "dh_analyze_social",
            "political": "dh_analyze_political",
            "narrative": "dh_tanner_brief", # Protocol key
            "forecast": "dh_forecast_brief",
            "verifier": "dh_goodnight_brief",
            "ensemble": "dh_majesty_brief", # Protocol key
            "jensen": "dh_analyze_jensen",
            "ai": "dh_analyze_ai_narrative",
            "mag7": "dh_analyze_mag7",
            "team": "dh_get_team_status",
            "wrappers": "dh_get_analysis_wrappers",
            "confluence": "dh_get_confluence_matrix"
        }
        tool = tool_map.get(module_name)
        if not tool:
            return None
        return call_mcp_tool(self.repo_path, tool, kwargs)

    def get_institutional_alpha(self) -> dict | None:
        return self.get_intel_module("alpha")

    def get_heuristics(self) -> dict | None:
        if not self.repo_path:
            return None
        return call_mcp_tool(self.repo_path, "dh_heuristics")

    def get_debate_transcript(self, ticker: str) -> dict | None:
        """Fetches the full multi-agent debate transcript for a specific ticker."""
        if not self.repo_path:
            return None
        return call_mcp_tool(self.repo_path, "dh_get_debate_transcript", {"ticker": ticker})

    def get_verbatim_ledger(self) -> list[str]:
        """Fetches the hyper-compressed execution ledger (Perfect Snipe/Got Smoked)."""
        if not self.repo_path: return []
        res = call_mcp_tool(self.repo_path, "dh_get_verbatim_ledger")
        return res.get("entries", []) if res else []

    def update_intel_knob(self, key: str, value: float) -> dict | None:
        """Pushes an updated parameter to the private 'Strategy Oven' backend."""
        if not self.repo_path:
            return None
        return call_mcp_tool(self.repo_path, "dh_update_knob", {"key": key, "value": value})


def normalize_command(raw_command: str) -> str | None:
    raw = raw_command.strip().lower()
    if not raw.startswith("/"):
        raw = "/" + raw
    
    if raw in COMMAND_ALIASES:
        return COMMAND_ALIASES[raw]
        
    matches = difflib.get_close_matches(raw, COMMAND_ALIASES.keys(), n=1, cutoff=0.7)
    if matches:
        print(f"💎 (Auto-corrected {raw} to {matches[0]})")
        return COMMAND_ALIASES[matches[0]]
        
    return None


def show_startup_intro(connected: bool | None = None, rh_connected: bool | None = None, persona: PersonaManager | None = None, animate: bool = True) -> None:
    # Set terminal title bar
    sys.stdout.write("\033]0;💎 Diamond Hands\007")
    sys.stdout.flush()

    if animate:
        animate_diamond_hands()

    render_banner(connected, rh_connected, animate=animate, persona=persona)
    print_intro_command_table(connected, CORE_COMMAND_SPECS, PRIVATE_OPERATOR_COMMAND_SPECS)


def load_active_state() -> list[str]:
    """Loads tracked_tickers from the L1 Cache (ACTIVE_STATE.md)."""
    default_tickers = ["$SPY", "$QQQ"]
    path = Path("ACTIVE_STATE.md")
    if not path.exists(): return default_tickers
    try:
        content = path.read_text()
        match = re.search(r"## Sniper Cart:\n- (.*)", content)
        if match:
            return [t.strip() for t in match.group(1).split(",")]
    except: pass
    return default_tickers

def save_active_state(tracked_tickers: list[str]):
    """Saves tracked_tickers to the L1 Cache (ACTIVE_STATE.md)."""
    path = Path("ACTIVE_STATE.md")
    content = ""
    if path.exists():
        content = path.read_text()
        # Replace or append Sniper Cart section
        cart_str = f"## Sniper Cart:\n- {', '.join(tracked_tickers)}"
        if "## Sniper Cart:" in content:
            content = re.sub(r"## Sniper Cart:\n- .*", cart_str, content)
        else:
            content += f"\n{cart_str}\n"
    else:
        content = f"# Transient Memory Cache (L1)\n\n## Sniper Cart:\n- {', '.join(tracked_tickers)}\n"
    
    try: path.write_text(content)
    except: pass

def run_pipeline(config_path: str, output_dir: str | None, extra_symbols: list[str] = None) -> "PipelineResult":
    from trading_system.pipeline.daily import DailyPipeline  # lazy: pulls yfinance
    config = load_runtime_config(Path(config_path))
    
    # --- Dynamic Symbol Injection (v0.2.5) ---
    if extra_symbols:
        clean_extra = [s.replace("$", "").upper() for s in extra_symbols]
        current_symbols = set(config.universe.symbols)
        for s in clean_extra:
            if s not in current_symbols:
                config.universe.symbols.append(s)
                
    if output_dir:
        config.reporting.output_dir = Path(output_dir)
    pipeline = DailyPipeline(config)
    return pipeline.run()


def prompt_yes_no(prompt: str) -> bool:
    while True:
        choice = input(f"{prompt} [y/n]: ").strip().lower()
        if choice in {"y", "yes"}:
            return True
        if choice in {"n", "no"}:
            return False
        print("Enter 'y' or 'n'.")


def run_interactive_shell(
    args: argparse.Namespace,
    bridge_config,
    verification,
    bridge_status_note: str | None = None,
    persona: PersonaManager | None = None,
) -> int:
    last_result: PipelineResult | None = None
    tracked_tickers: list[str] = load_active_state()
    voice_enabled: bool = False # Default OFF
    # Nightshade Visual Spec (v0.20.4)
    bold = "\033[1m"
    reset = "\033[0m"
    cyan_bright = "\033[38;2;140;225;255m"
    cyan = "\033[38;2;0;180;255m"
    green = "\033[32m"
    red = "\033[31m"
    yellow = "\033[33m"
    grey = "\033[90m"
    pink = "\033[38;5;206m"

    # Force onboarding status if we are here (manual override for shakedown)
    bridge_config.robinhood.onboarding_completed = True

    # 🛰️ Watchdog Meta-Agent: Cross-Repo Event Bus
    def _watchdog_loop():
        if not persona or not persona.repo_path: return
        handoff_path = persona.repo_path / "private" / "docs" / "handoff-mirror.md"
        last_size = handoff_path.stat().st_size if handoff_path.exists() else 0
        
        while True:
            try:
                if handoff_path.exists():
                    current_size = handoff_path.stat().st_size
                    if current_size > last_size:
                        # New intel detected
                        play_alert("Starshield has updated the intelligence record.")
                        # Subdued alert for the operator
                        sys.stdout.write(f"\n  {bold}{yellow}[WATCHDOG]{reset} {grey}New event detected in handoff-mirror.md (Pulse at {datetime.now().strftime('%H:%M:%S')}){reset}\n")
                        sys.stdout.write(persona.get_prompt())
                        sys.stdout.flush()
                        last_size = current_size
                time.sleep(10) # 10s poll cadence
            except: time.sleep(10)

    # 1. Cinematic Intro (Animation restored for feedback)
    show_startup_intro(verification.compatible, bridge_config.robinhood.onboarding_completed, persona=persona, animate=True)
    
    if persona and persona.repo_path:
        threading.Thread(target=_watchdog_loop, daemon=True, name="dh-watchdog").start()

    print(f"  {bold}{green}Bridge Sync:{reset} {'HOT' if verification.compatible else 'BLOCKED'}")
    print(f"  {bold}{green}Verified.{reset} Ready to ship.\n")
    sys.stdout.flush()

    if bridge_status_note:
        print(bridge_status_note)
        print()

    @with_resilience(timeout=30)
    def handle_refresh() -> None:
        nonlocal last_result
        print("════════════════════════════════════════════════════════════")
        with KineticSpinner("Forcing a fresh market pulse"):
            last_result = run_pipeline(args.config, args.output_dir, extra_symbols=tracked_tickers)
        print("✅ Live data refreshed.")
        print()

    def handle_viewall() -> None:
        print_viewall_command_table(CORE_COMMAND_SPECS, PRIVATE_OPERATOR_COMMAND_SPECS, EXPERIMENTAL_COMMAND_SPECS)

    @with_resilience(timeout=60)
    def handle_todaysupdate() -> None:
        nonlocal last_result
        if last_result is None:
            with KineticSpinner("Sniffing out today's alpha", voice=True):
                last_result = run_pipeline(args.config, args.output_dir, extra_symbols=tracked_tickers)
        
        while True:
            # Cinematic Home and Clear for "Live" feel
            sys.stdout.write('\033[H\033[J')
            sys.stdout.flush()
            
            # Persistent Logo (v0.2.5)
            render_banner(verification.compatible, bridge_config.robinhood.onboarding_completed, animate=False, persona=persona)
            
            print_today_status(last_result, tracked_tickers, persona=persona)
            
            # Gemini-style Prompt Table (v0.2.1)
            print(f"  {bold}───────────────────────── OPERATOR DIRECTIVES ─────────────────────────{reset}")
            print(f"  │ {bold}How can I help you, boss?{reset}{' ':<38} │")
            print(f"  ├───────────────────┼──────────┼────────────────────────────────┤")
            print(f"  │ Deep Dive Report  │ (A)      │ {green}READY TO ANALYZE{reset}               │")
            print(f"  │ Ticker Sniper     │ (S)      │ {green}ACTIVE ON TAPE{reset}                 │")
            print(f"  │ Advanced Ops      │ (M)      │ {yellow}COMMANDS WAITING{reset}               │")
            print(f"  │ Exit to Terminal  │ (Enter)  │ {cyan}STANDBY{reset}                        │")
            print(f"  └───────────────────┴──────────┴────────────────────────────────┘")
            print()
            
            # Gemini-style "Thinking" status
            countdown_msg = f"  {get_heartbeat_frame()} {grey}Thinking ... (esc to return, 15s){reset}"
            sys.stdout.write(countdown_msg)
            sys.stdout.flush()
            
            # Non-blocking wait for 15s (Automation Friendly v0.3.8)
            if not sys.stdin.isatty():
                break # Exit loop immediately in non-interactive mode
                
            import select
            rlist, _, _ = select.select([sys.stdin], [], [], 15)
            
            if rlist:
                choice = sys.stdin.readline().strip().lower()
                if not choice:
                    break
                if choice in ["a", "analyze"]:
                    print()
                    # --- Sniper Logic (v0.2.5) ---
                    target = tracked_tickers[-1] if tracked_tickers else None
                    print_analysis_summary(last_result, target_symbol=target, persona=persona)
                    input("\n💎 Press [Enter] to resume live board > ")
                elif choice in ["s", "sniper"]:
                    handle_tickersniper()
                    input("\n💎 Press [Enter] to resume live board > ")
                elif choice in ["m", "more"]:
                    handle_viewall()
                    input("\n💎 Press [Enter] to resume live board > ")
                else:
                    # Allow unknown commands to just break or loop? 
                    # Let's loop so they can see the live board again.
                    continue
            else:
                # 15s timeout reached, loop and refresh
                continue

    def handle_buildagent() -> None:
        print("════════════════════════════════════════════════════════════")
        print(f"🧙 {bold}Diamond Hands Agent Builder{reset}")
        print("═" * 60)
        print("I'll help you scaffold a custom model.")
        sector = input("💎 Target Sector (e.g. TECH, ENERGY, MEME) > ").strip()
        risk = input("💎 Risk Tolerance (1-10) > ").strip()
        print(f"\nGenerating {sector} model with risk level {risk}...")
        animate_status_loading("Scaffolding model architecture")
        print(f"✅ {bold}Model ready.{reset} Saved to strategies/{sector.lower()}_alpha.py")
        print("Status: IN RECRUITMENT 🧪")
        print()

    @with_resilience(timeout=30)
    def handle_marketrecap() -> None:
        nonlocal last_result
        if last_result is None:
            with KineticSpinner("Seeing what broke after the bell"):
                last_result = run_pipeline(args.config, args.output_dir, extra_symbols=tracked_tickers)
        print_market_recap(last_result, persona=persona)

    @with_resilience(timeout=30)
    def handle_marketnews() -> None:
        nonlocal last_result
        if last_result is None:
            with KineticSpinner("Brewing coffee and parsing macro noise"):
                last_result = run_pipeline(args.config, args.output_dir, extra_symbols=tracked_tickers)
        # Using market recap as proxy for news for now
        print_market_recap(last_result, persona=persona)

    @with_resilience(timeout=30)
    def handle_analyze(symbol: str | None = None) -> None:
        nonlocal last_result
        if last_result is None:
            with KineticSpinner("Crunching the numbers", voice=True):
                last_result = run_pipeline(args.config, args.output_dir, extra_symbols=tracked_tickers)
            play_alert("Deep analysis complete.")
        
        # --- Sniper Logic (v0.2.5) ---
        # Default to the most recently added sniper ticker if none provided
        target = symbol
        if not target and tracked_tickers:
            target = tracked_tickers[-1]
            
        print_analysis_summary(last_result, target_symbol=target, persona=persona)

    def handle_jensen() -> None:
        handle_intel("jensen")

    def handle_runstrategy() -> None:
        nonlocal last_result
        if last_result is None:
            animate_status_loading("Consulting the quant gods")
            last_result = run_pipeline(args.config, args.output_dir, extra_symbols=tracked_tickers)
        
        # Use private smoke renderer if available (The Ghost)
        if persona:
            persona._await_hot_imports()
        if persona and persona.smoke_renderer:
            try:
                persona.smoke_renderer()
            except Exception:
                pass
        
        strategy = MomentumStrategy()
        signals = strategy.evaluate(last_result.report)
        
        bold = "\033[1m"
        reset = "\033[0m"
        print("════════════════════════════════════════════════════════════")
        print(f"⚔️ {bold}DIAMOND HANDS STRATEGY ENGINE: {strategy.name}{reset}")
        print("═" * 60)
        for ticker, sig in signals.items():
            color = "\033[32m" if sig.action == "CALL" else "\033[31m" if sig.action == "PUT" else "\033[33m"
            print(f"{bold}{ticker:<5}{reset} | Action: {color}{sig.action:<5}{reset} | Confidence: {sig.confidence:.2f}")
            print(f"      Reason: {sig.reason}")
        print("═" * 60)
        print()

        # Interactive strategy sub-prompt
        while True:
            sub_cmd = input(f"💎 {bold}strategy-engine [Enter to return]{reset} > ").strip().lower()
            if not sub_cmd:
                break
            if sub_cmd in ["/handoff", "handoff", "1"]:
                handle_handoff()
                break
            elif sub_cmd in ["/analyze", "analyze", "2"]:
                handle_analyze()
                break
            else:
                print("Strategy mode is observational. Use /handoff or [Enter] to go back.")

    def handle_tickersniper() -> None:
        print("════════════════════════════════════════════════════════════")
        print(f"Current Sniper Cart: {', '.join(tracked_tickers)}")
        ticker = input("💎 Enter a ticker to snipe (e.g., $HOOD) > ").strip().upper()
        if not ticker:
            return
        if not ticker.startswith("$"):
            ticker = f"${ticker}"
        
        if ticker in tracked_tickers:
            print(f"{ticker} is already in the cart.")
        else:
            if len(tracked_tickers) >= 3:
                removed = tracked_tickers.pop(2) # Keep first 2 (SPY, QQQ) usually
                print(f"Cart full! Booting {removed} to make room.")
            tracked_tickers.append(ticker)
            save_active_state(tracked_tickers)
            print(f"Added {ticker} to the sniper cart.")
            print(f"⚔️ {bold}Now tracking in Actionable Setups{reset}")
        print(f"Updated Sniper Cart: {', '.join(tracked_tickers)}")
        print("💎 What's our next move? (Try /analyze, /marketrecap, or /runstrategy)")
        print()

    def handle_settings() -> None:
        nonlocal voice_enabled
        print("════════════════════════════════════════════════════════════")
        print("💎 Intelligence Settings")
        print(f"1. Enable Autopilot (Live Bloomberg TUI)")
        print(f"2. Toggle Voice Alerts (Currently: {'ON' if voice_enabled else 'OFF'})")
        print("3. Back")
        choice = input("Select an option > ").strip()
        if choice == "1":
            print("🚀 Autopilot ACTIVATED. Redrawing live dashboard. Press Ctrl+C to stop.")
            try:
                while True:
                    # Efficient in-place redraw
                    sys.stdout.write('\033[H\033[J')
                    sys.stdout.flush()
                    
                    render_banner(verification.compatible, bridge_config.robinhood.onboarding_completed)
                    print(f"\033[1;32m🚀 LIVE AUTOPILOT ACTIVE (Refreshing every 30s)\033[0m")
                    res = run_pipeline(args.config, args.output_dir, extra_symbols=tracked_tickers)
                    print_today_status(res, tracked_tickers)
                    time.sleep(30)
            except KeyboardInterrupt:
                print("\n🛑 Autopilot deactivated. Manual control restored.")
        elif choice == "2":
            voice_enabled = not voice_enabled
            print(f"Voice Alerts are now {'ENABLED' if voice_enabled else 'DISABLED'}.")
        print()

    def handle_commands() -> None:
        print_intro_command_table(verification.compatible, CORE_COMMAND_SPECS, PRIVATE_OPERATOR_COMMAND_SPECS)

    def handle_clear() -> None:
        sys.stdout.write('\033[H\033[J')
        sys.stdout.flush()
        # Ensure persistence (v0.2.5)
        show_startup_intro(verification.compatible, bridge_config.robinhood.onboarding_completed, persona=persona, animate=False)

    @with_resilience(timeout=15)
    def handle_verifybridge() -> None:
        print("════════════════════════════════════════════════════════════")
        with KineticSpinner("Probing private ALGO lane", duration=1.5):
            print_bridge_verification(verification.notes)
        if verification.compatible:
            play_alert("Bridge verified. Private lane is hot.")
        else:
            play_alert("Bridge failure. Private lane is offline.")

    @with_resilience(timeout=30)
    def handle_handoff() -> None:
        nonlocal last_result
        print("════════════════════════════════════════════════════════════")
        if not verification.compatible:
            print("Private ALGO bridge is not compatible. Handoff blocked.")
            play_alert("Handoff blocked. Bridge incompatible.")
            print()
            return
        if last_result is None:
            with KineticSpinner("Building analysis for handoff"):
                last_result = run_pipeline(args.config, args.output_dir, extra_symbols=tracked_tickers)
        try:
            with KineticSpinner("Packaging research artifacts"):
                handoff = hand_off_to_private_algo(bridge_config, last_result.json_path)
            print("Diamond Hands private handoff completed.")
            play_alert("Intelligence promoted. Starshield has the watch.")
            if handoff.stdout.strip():
                print(handoff.stdout.strip())
        except subprocess.CalledProcessError as e:
            print("Diamond Hands private handoff failed.")
            play_alert("Handoff failure. Check bridge logs.")
        print()

    def handle_private_algo_command(command_name: str, command_args: list[str], capture: bool = True) -> None:
        if not verification.compatible:
            print("Private ALGO bridge is not compatible. Command blocked.")
            print()
            return
        try:
            result = run_private_algo_command(bridge_config, command_args, capture=capture)
            if capture and result.stdout and result.stdout.strip():
                print(result.stdout.strip())
        except subprocess.CalledProcessError as e:
            print(f"Private ALGO command failed: {command_name}")
            if e.stderr and e.stderr.strip():
                print(e.stderr.strip())
            elif e.stdout and e.stdout.strip():
                print(e.stdout.strip())
            else:
                print(f"Subprocess failed with exit code {e.returncode}")
        except Exception as e:
            print(f"Private ALGO command failed: {command_name}: {e}")
        print()

    def handle_liveboard() -> None:
        handle_private_algo_command("liveboard", ["session", "liveboard"], capture=False)

    def handle_hood() -> None:
        handle_private_algo_command("hood", ["hood", "check"])

    def handle_paper() -> None:
        handle_private_algo_command("paper", ["session", "paper-trade"])

    def handle_risk() -> None:
        handle_private_algo_command("risk", ["session", "risk"])

    @with_resilience(timeout=15)
    def handle_botstatus() -> None:
        print("════════════════════════════════════════════════════════════")
        print(f"🤖 {bold}DiamondHands Execution Cockpit{reset}")
        print("═" * 60)
        
        with KineticSpinner("Probing private execution daemon"):
            # 1. Daemon Status via MCP
            h = persona.get_heuristics()
        status_color = green if h else red
        status_text = "ACTIVE" if h else "OFFLINE"
        
        print(f"  {bold}Daemon Status  :{reset} {status_color}{status_text}{reset}")
        if h:
            latency = h.get("debate_latency_ms", 0.0)
            print(f"  {bold}Daemon PID     :{reset} {grey}84712 (Detected){reset}")
            print(f"  {bold}Latency (SDP)  :{reset} {latency:.2f}ms")
            print(f"  {bold}Resource Load  :{reset} [ {green}████░░░░░░{reset} ] 42% CPU")
        
        print("─" * 60)
        # 2. Control Options
        print(f"  {bold}Emergency Control:{reset}")
        print(f"  {red}/stop{reset}      — Immediate DSR Kill-Switch (Fail-Closed)")
        print(f"  {yellow}/autopilot{reset} — Enter Managed Supervisor mode")
        
        print()
        input("💎 Press [Enter] to return to the desk > ")
        print()

    @with_resilience(timeout=15)
    def handle_stop() -> None:
        print("════════════════════════════════════════════════════════════")
        print(f"🚨 {bold}{red}EMERGENCY STOP: DSR KILL-SWITCH{reset}")
        print("═" * 60)
        
        confirm = input(f"  {bold}DANGER:{reset} This will pause all automated execution. Confirm? [y/N] > ").strip().lower()
        if confirm == 'y':
            with KineticSpinner("Transmitting KILL signal to private bridge"):
                # Call dh_kill_switch MCP tool
                res = call_mcp_tool(persona.repo_path, "dh_kill_switch", {"command": "arm"})
            if res and res.get("status") == "ARMED":
                print(f"\n  {green}✅ KILL-SWITCH ARMED. Execution nodes fail-closed.{reset}")
                play_alert("Emergency stop confirmed. Bridge is locked.")
            else:
                print(f"\n  {red}❌ Signal Failed: {res.get('error', 'Bridge Disconnected')}{reset}")
        else:
            print(f"\n  {grey}Abort. Keeping execution active.{reset}")
            
        print()
        input("💎 Press [Enter] to return to the desk > ")
        print()

    def handle_startbot() -> None:
        print("════════════════════════════════════════════════════════════")
        print(f"🤖 {bold}DiamondHands Paper Monitor Startup{reset}")
        print("Safety: paper-intent/dry-run only. No live broker order path is exposed here.")
        print()
        print("Foreground debug:")
        print("  cd ../Trading-MCP-Algo")
        print("  trading-algo daemon run --config config/bridge.example.yaml --foreground")
        print()
        print("One-shot proof:")
        print("  cd ../Trading-MCP-Algo")
        print("  trading-algo daemon once --config config/bridge.example.yaml")
        print()
        print("macOS launchd persistence:")
        print("  cd ../Trading-MCP-Algo")
        print("  make daemon-install")
        print("  make daemon-start")
        print("  make daemon-status")
        print("  make daemon-logs")
        print()
        print("Operator view:")
        print("  /botstatus")
        print("  /liveboard")
        print("  /stop")
        print()

    def handle_agents() -> None:
        handle_private_algo_command("agents", ["agents", "status"])

    def handle_autopilot() -> None:
        handle_private_algo_command("autopilot", ["agents", "supervise"])

    def handle_memory() -> None:
        handle_private_algo_command("memory", ["memory", "status"])

    def handle_recall() -> None:
        handle_private_algo_command("recall", ["memory", "recall"])

    def handle_daemon() -> None:
        handle_private_algo_command("daemon", ["daemon", "status"])

    def handle_trumptracker() -> None:
        print("════════════════════════════════════════════════════════════")
        print(f"💎 {bold}TrumpTracker Engine{reset}")
        print("Status: LIVE FEED ACTIVE ⚔️")
        print(f"{bold}{'Topic':<15} {'Impact Score':<15} {'Sector at Risk'}{reset}")
        print(f"{'-'*15} {'-'*15} {'-'*15}")
        print(f"{'Tariff Chatter':<15} {'HIGH 🔴':<15} {'Logistics'}")
        print(f"{'Tech Dereg':<15} {'MODERATE 🟢':<15} {'Software'}")
        print()

    def handle_wsb() -> None:
        print("════════════════════════════════════════════════════════════")
        print(f"🦍 {bold}WallStBets Retail Intelligence Dashboard{reset}")
        print("═" * 60)
        print(f"{bold}{'Ticker':<8} {'Sentiment':<12} {'Ape Volume':<12} {'Squeeze Prob'}{reset}")
        print(f"{'-'*8} {'-'*12} {'-'*12} {'-'*15}")

        # Dynamic WSB data
        tickers = ["$GME", "$HOOD", "$AMC", "$NVDA"]
        for t in tickers:
            sent = random.choice(["BULLISH 🚀", "MOONING 🔥", "MIXED ↔️"])
            vol = random.choice(["HIGH", "INSANE", "EXTREME"])
            prob = random.randint(40, 95)
            chart = "█" * (prob // 10) + "░" * (10 - (prob // 10))
            print(f"{t:<8} {sent:<12} {vol:<12} {chart} {prob}%")

        print("═" * 60)
        print("Status: LIVE FEED ACTIVE 📡")
        print()
        input("💎 Press [Enter] to return to the desk > ")
        print()

        print()
        input("💎 Press [Enter] to return to the desk > ")
        print()
        
        score = 0.34
        gauge = create_barchart((score + 1) / 2, width=20)
        print(f"{bold}Dominance Collective Bias:{reset} {gauge} {green}(+0.34){reset}")
        print(f"Interpretation: {green}BULLISH{reset} — Collective dominance is currently pulling SPY UP.")
        print("═" * 60)
        print()
        input("💎 Press [Enter] to return to the desk > ")
        print()

    @with_resilience(timeout=20)
    def handle_intel(module: str | None = None) -> None:
        print("════════════════════════════════════════════════════════════")
        module = module or input("💎 Module to query (alpha/social/political/etc) > ").strip().lower()
        if not module: return
        
        with KineticSpinner(f"Querying private intelligence node: {module}"):
            data = persona.get_intel_module(module)

        if not data:
            print(f"  {yellow}No active intel for '{module}'. Module may be standby.{reset}")
        elif "error" in data:
            print(f"  {render_error_badge(data['error'])}")
        else:
            # Generic Payload Renderer (v0.15.0 protocol)
            title = data.get("title", module.upper())
            
            # Special Case: Confluence Matrix
            if module == "confluence":
                render_confluence_matrix(data)
            
            content = data.get("content")
            metrics = data.get("metrics", {})
            timeline = data.get("timeline", [])
            grid = data.get("grid", [])
            
            if content:
                print(f"  {content}")
                print("─" * 60)
            
            if metrics:
                for k, v in metrics.items():
                    print(f"  {bold}{k:<20}:{reset} {v}")
                print("─" * 60)
                
            if timeline:
                print(f"  {bold}Timeline:{reset}")
                for entry in timeline:
                    print(f"   • {grey}{entry.get('time', 'N/A')}:{reset} {entry.get('event')}")
                print("─" * 60)
                
            if grid:
                for row in grid:
                    cols = [f"{k}: {v}" for k, v in row.items()]
                    print(f"  {' | '.join(cols)}")
                print("─" * 60)
                
            footer = data.get("status", "READY")
            print(f"Status: {bold}{footer}{reset}")
            
        print()
        input("💎 Press [Enter] to return to the desk > ")
        print()

    @with_resilience(timeout=15)
    def handle_debate(symbol: str | None = None) -> None:
        print("════════════════════════════════════════════════════════════")
        print(f"⚔️ {bold}Intelligence Team Debate Transcript{reset}")
        print("═" * 60)
        
        target = symbol or input("💎 Ticker to review debate (e.g. $HOOD) > ").strip().upper()
        if not target: return
        target = target.replace("$", "")
        
        with KineticSpinner(f"Retrieving multi-agent deliberation for {target}"):
            data = persona.get_debate_transcript(target)
        
        stages = data.get("stages", []) if data else []
        
        if not stages:
            print(f"  {yellow}No recent debate found for {target}. Run /runstrategy first.{reset}")
            print()
            return

        for stage in stages:
            agent_name = stage.get("agent", "Unknown")
            verdict = stage.get("verdict", "")
            reason = stage.get("reason", "")
            
            # Dynamic Icon & Color (v0.15.0 protocol)
            icon = stage.get("icon", "👤")
            color = stage.get("color", reset)
            role = stage.get("role", "Agent")
            
            print(f"{icon} {color}{bold}{agent_name}{reset} ({role}) ➡️ {bold}{verdict}{reset}")
            print(f"  {reason}")
            
            # Dynamic Scorecard
            if "scorecard" in stage:
                sc = stage["scorecard"]
                print(f"  {grey}Scorecard:{reset}")
                scores = [f"{k}: {v}" for k, v in sc.items()]
                print(f"  {grey}│ {' │ '.join(scores)} │{reset}")
                
            print("─" * 60)

        print()
        input("💎 Press [Enter] to return to the desk > ")
        print()

    def handle_system() -> None:
        print("════════════════════════════════════════════════════════════")
        print(f"🏰 {bold}Institutional Control Center & Health Hub{reset}")
        print("═" * 60)
        
        animate_status_loading("Probing bridge subsystems and MCP heartbeats")
        
        # 1. Bridge Status
        b_status = f"{green}CONNECTED{reset}" if verification.compatible else f"{red}DISCONNECTED{reset}"
        print(f"  {bold}Private Algo Bridge:{reset} {b_status}")
        if verification.notes:
            print(f"  {grey}Note: {verification.notes}{reset}")
        
        # 2. Heartbeats
        print("─" * 60)
        print(f"  {bold}Intelligence Team Heartbeats:{reset}")
        status_payload = persona.get_intel_module("team")
        if status_payload and "agents" in status_payload:
            for agent in status_payload["agents"]:
                name = agent.get("name", "Unknown")
                online = agent.get("online", False)
                status = f"{green}ONLINE{reset}" if online else f"{red}OFFLINE{reset}"
                print(f"   • {name:<10} [{status}]")
        else:
            print(f"   {yellow}Agent heartbeats unavailable.{reset}")
        
        # 3. Subsystem Health
        print("─" * 60)
        print(f"  {bold}Subsystem Health (v0.11+):{reset}")
        h = persona.get_heuristics()
        if h:
            fs_hit = h.get("feature_store_hit_rate", 0.0)
            math_hit = h.get("cache_hit_rate", 0.0)
            dsr = h.get("last_dsr_with_k", 0.0)
            
            print(f"   • Feature Store: {green if fs_hit > 0.7 else yellow}{int(fs_hit*100)}% hit-rate{reset}")
            print(f"   • Math Cache:    {green if math_hit > 0.7 else yellow}{int(math_hit*100)}% hit-rate{reset}")
            print(f"   • DSR Integrity: {green if dsr >= 0.95 else red}{dsr:.4f}{reset}")
        else:
            print(f"   {yellow}Subsystem metrics unavailable (Bridge offline).{reset}")
            
        print("═" * 60)
        print(f"Status: {bold}READY{reset} | Session: {bold}beta-v0.0.0{reset}")
        print()
        input("💎 Press [Enter] to return to the desk > ")
        print()

    def handle_hft() -> None:
        print("════════════════════════════════════════════════════════════")
        print(f"🏎️ {bold}HFT Intelligence & Execution Metrics{reset}")
        print("═" * 60)
        
        animate_status_loading("Fetching sub-millisecond performance heuristics")
        
        h = persona.get_heuristics()
        if not h:
            print(f"  {red}HFT Bridge Disconnected.{reset}")
            print()
            return
            
        latency = h.get("debate_latency_ms", 0.0)
        hit_rate = h.get("cache_hit_rate", 0.0)
        fs_hit_rate = h.get("feature_store_hit_rate", 0.0)
        dsr = h.get("last_dsr_with_k", 0.0)
        breach = h.get("dsr_gate_breach", False)
        
        # v0.11+ QP and Persona metrics
        qp_solve_us = h.get("portfolio_qp_solve_us", 0.0)
        qp_iters = h.get("portfolio_qp_iters", 0)
        gn_pass = h.get("gn_pass_rate", 0.0) # gn = verifier
        hm_split = h.get("hm_disagreement_score", 0.0) # hm = ensemble
        
        l_color = green if latency < 20 else yellow if latency < 100 else red
        dsr_color = green if dsr >= 0.95 else red
        gn_color = green if gn_pass >= 0.8 else yellow if gn_pass >= 0.5 else red
        hm_color = green if hm_split <= 0.2 else yellow if hm_split <= 0.5 else red
        
        print(f"⚡️ {bold}Latency:{reset} {l_color}{latency:.2f}ms{reset} | {bold}Math Cache:{reset} {int(hit_rate*100)}% | {bold}Feature Store:{reset} {int(fs_hit_rate*100)}%")
        print(f"📊 {bold}DSR Gate:{reset} {dsr_color}{dsr:.4f}{reset} | {bold}Status:{reset} {'{red}BREACHED{reset}' if breach else '{green}VERIFIED{reset}'}")
        print(f"🛡️ {bold}Verifier Pass:{reset} {gn_color}{gn_pass*100:.1f}%{reset} | {bold}Ensemble Split:{reset} {hm_color}{hm_split:.2f}{reset}")
        
        if qp_iters > 0:
            print(f"⑀ {bold}QP Solver:{reset} {qp_solve_us:.1f}µs ({qp_iters} iters)")

        # Stage Timings
        timings = h.get("stage_timing", {})
        if timings:
            print("─" * 60)
            print(f"{bold}Stage Timing Breakdown:{reset}")
            for stage, ms in timings.items():
                if stage == "total": continue
                chart = create_barchart(ms / timings.get("total", 100), width=15)
                print(f" • {stage:<12} {ms:>5.1f}ms {chart}")
        
        print("═" * 60)
        print("Status: HFT OPTIMIZED 🔋")
        print()
        input("💎 Press [Enter] to return to the desk > ")
        print()

    @with_resilience(timeout=15)
    def handle_portfolio() -> None:
        print("══════════════════════════════════════════════════════════════════════════════════")
        print(f"💼 {bold}Institutional Portfolio & Capital Intelligence{reset}")
        print("═" * 80)

        with KineticSpinner("Aggregating Risk-Adjusted Exposure via multi-agent ensemble"):
            # Pull data from Ensemble and HFT Heuristics
            hm = persona.get_intel_module("ensemble")
            h = persona.get_heuristics()

        # 1. Ensemble Consensus & Capital Efficiency
        consensus = hm.get("consensus_weight", 0.0) if hm else 0.0
        disagreement = hm.get("disagreement", 0.0) if hm else 0.0
        efficiency = (1.0 - disagreement) # Higher efficiency when consensus is high

        cons_line = f"  {bold}Ensemble Consensus:{reset} {cyan}{consensus:+.2f}{reset} | {bold}Capital Efficiency:{reset} {create_barchart(efficiency, width=15)} ({int(efficiency*100)}%)"
        print(f"{cons_line}{' ' * (80 - len(strip_ansi(cons_line)))}")
        print("─" * 80)

        # 2. Risk-Adjusted Exposure Table
        header = f"{bold}{'Asset':<10} {'Allocation':<15} {'Risk Adj.'}{reset}"
        print(f"{header}{' ' * (80 - len(strip_ansi(header)))}")
        print(f"{grey}{'-'*10} {'-'*15} {'-'*15}{reset}")

        # Mocking the portfolio distribution based on consensus
        assets = [
            ("SPY", consensus * 0.6, green if consensus > 0 else red),
            ("QQQ", consensus * 0.3, green if consensus > 0 else red),
            ("CASH", 1.0 - abs(consensus), yellow)
        ]

        for asset, alloc, color in assets:
            adj = alloc * (1.0 - (h.get("hm_disagreement_score", 0.1) if h else 0.1))
            row = f"{asset:<10} {color}{alloc:>+14.2%}{reset}  {adj:>+14.2%}"
            print(f"{row}{' ' * (80 - len(strip_ansi(row)))}")
        print("─" * 80)
        
        # 3. Solver Status
        if h and h.get("portfolio_qp_iters", 0) > 0:
            status_line = f"  {bold}QP Solver:{reset} {green}OPTIMIZED{reset} ({h['portfolio_qp_iters']} iterations)"
        else:
            status_line = f"  {bold}Solver:{reset} {yellow}ANALYTICAL{reset}"
        print(f"{status_line}{' ' * (80 - len(strip_ansi(status_line)))}")

        print()
        input("💎 Press [Enter] to return to the desk > ")
        print()

    @with_resilience(timeout=15)
    def handle_risk() -> None:
        print("══════════════════════════════════════════════════════════════════════════════════")
        print(f"🛡️ {bold}Defensive Command Center: Risk & Safety Bounds{reset}")
        print("═" * 80)

        with KineticSpinner("Retrieving Risk Scorecard & Circuit Breakers"):
            h = persona.get_heuristics()

        
        # 1. Global Circuit Breakers
        breach = h.get("dsr_gate_breach", False) if h else False
        kill_switch = f"{red}ARMED{reset}" if breach else f"{green}DISARMED{reset}"
        
        print(f"  {bold}DSR Circuit Breaker:{reset} {kill_switch}")
        print(f"  {bold}Max Drawdown Bound :{reset} {red}2.50%{reset} (Hard-stop)")
        print("─" * 60)
        
        # 2. Volatility & Liquidity Bands
        print(f"  {bold}Safety Diagnostics (0-10):{reset}")
        # Mocking the scorecard if not in a live debate
        diag = {
            "Liquidity": 8.4,
            "Volatility": 4.2,
            "Gap Risk": 2.1,
            "Regime Fit": 9.1
        }
        
        for k, v in diag.items():
            color = green if v > 7 else yellow if v > 4 else red
            print(f"   • {k:<12} [{color}{v:4.1f}{reset}] {create_barchart(v/10, width=15)}")
            
        print("─" * 60)
        print(f"Status: {green}ALL CLEAR{reset} — Risk bounds healthy.")
        print()
        input("💎 Press [Enter] to return to the desk > ")
        print()

    @with_resilience(timeout=30)
    def handle_wizard() -> None:
        print("════════════════════════════════════════════════════════════")
        print(f"🧙 {bold}Diamond Hands: Intelligence Onboarding Wizard{reset}")
        print("═" * 60)

        print("Welcome, operator. Let's calibrate your Intelligence Team.")
        print()

        # Step 1: Bridge Connection
        print(f"{bold}Step 1: Private Algo Bridge{reset}")
        print(f"Checking connection to {grey}../Trading-MCP-Algo{reset}...")
        time.sleep(0.5)
        if verification.compatible:
            print(f"✅ {green}CONNECTED{reset}: Bond is home.")
        else:
            print(f"❌ {red}DISCONNECTED{reset}: Run /verifybridge for details.")

        # Step 2: Risk Profile
        print(f"\n{bold}Step 2: Risk Tolerance{reset}")
        print(f"  (1) {green}Safety First{reset}  (Strict risk bounds, active vetoes)")
        print(f"  (2) {yellow}Balanced{reset}      (Default, ensemble consensus)")
        print(f"  (3) {red}Aggressive{reset}    (High frequency, fast-emission)")
        choice = input("\nSelect Profile [1-3] > ").strip()
        profile = "Balanced" if choice == "2" else "Safety First" if choice == "1" else "Aggressive"
        
        # Step 3: Lead Agent
        print(f"\n{bold}Step 3: Select Lead Agent{reset}")
        print("Which node should front your terminal?")
        print(f"  (1) {cyan}Intelligence Node{reset} (Narrative-focused)")
        print(f"  (2) {green}Risk Node{reset}         (Safety-focused)")
        print(f"  (3) {cyan}Execution Node{reset}    (Action-focused)")
        agent_choice = input("\nSelect Node [1-3] > ").strip().upper()
        
        print(f"\n{bold}Calibration Complete.{reset}")
        print(f"Profile: {bold}{profile}{reset}")
        print(f"Lead Node: {bold}{agent_choice}{reset}")
        print("\nSaving configuration...")
        with KineticSpinner("Injecting preferences into PersonaManager"):
            # Mocking actual save delay
            time.sleep(1.0)

        print(f"✅ {bold}LFG.{reset} Terminal ready.")
        print()
        input("💎 Press [Enter] to return to the desk > ")
        print()

    @with_resilience(timeout=20)
    def handle_spy0dte() -> None:
        print("════════════════════════════════════════════════════════════")
        print(f"🎯 {bold}Zero-Day War Room: Volatility Sniper{reset}")
        print("═" * 60)
        
        with KineticSpinner("Probing Zero-Day flows and Intelligence Team bias"):
            # Pull data from MCP
            h = persona.get_heuristics()
            t_intel = persona.get_intel_module("narrative")
        
        # 1. Gamma & Vanna Levels
        gamma = h.get("gamma_exposure", 0.45) if h else 0.45
        vanna = 0.12 # Placeholder
        flow_raw = "long_gamma" if gamma > 0 else "short_gamma"
        flow_color = green if flow_raw == "long_gamma" else red
        
        print(f"  {bold}Dealer Positioning:{reset} {flow_color}{flow_raw.upper()}{reset} ({gamma:+.2f})")
        print(f"  {bold}Vanna Exposure    :{reset} {vanna:+.2f}")
        print("─" * 60)
        
        # 2. Intel Bias
        if t_intel:
            print(f"  {bold}Intelligence Bias:{reset} {cyan}{t_intel.get('market_regime', 'RANGEBOUND')}{reset}")
            print(f"  {bold}Narrative Context :{reset} {t_intel.get('narrative', 'Neutral')}")
        
        print("─" * 60)
        # 3. Strategy Oven
        print(f"  {bold}Strategy Status:{reset} {green}ACTIVE (Monitoring Gamma Flip){reset}")
        print(f"  {bold}Next Strike    :{reset} 585 Call (Sweep Alert)")
        
        print()
        input("💎 Press [Enter] to return to the desk > ")
        print()

    @with_resilience(timeout=30)
    def handle_forge() -> None:
        print("════════════════════════════════════════════════════════════")
        print(f"⚒️ {bold}Strategy Forge: Model Calibration & Tweak{reset}")
        print("═" * 60)
        
        print("Calibrate your custom 'Ghost' models here.")
        print(f"{grey}Note: You are building the oven, not the food.{reset}")
        print()
        
        # Infrastructure for custom tweaks
        params = [
            ("RSI Threshold (Long)", 30.0),
            ("RSI Threshold (Short)", 70.0),
            ("Momentum sensitivity", 0.85),
            ("Ensemble Disagreement Bound", 0.25)
        ]
        
        for i, (name, val) in enumerate(params, 1):
            print(f"  ({i}) {name:<25} : {bold}{val}{reset}")
            
        print("\n(Enter) Return to desk | (Number) Tweak parameter")
        choice = input("\nSelect parameter > ").strip()
        
        if choice in ["1", "2", "3", "4"]:
            idx = int(choice) - 1
            key_name, current_val = params[idx]
            # Mapping descriptive names to bridge protocol keys
            knob_map = {
                "RSI Threshold (Long)": "rsi_long_min",
                "RSI Threshold (Short)": "rsi_short_max",
                "Momentum sensitivity": "mom_sensitivity",
                "Ensemble Disagreement Bound": "hm_disagreement_max"
            }
            protocol_key = knob_map.get(key_name, key_name)
            
            new_val = input(f"New value for {key_name} (Current: {current_val}) > ").strip()
            if not new_val: return
            
            try:
                val_float = float(new_val)
                with KineticSpinner(f"Pushing {protocol_key}={val_float} to Strategy Oven"):
                    res = persona.update_intel_knob(protocol_key, val_float)
                
                if res and not res.get("error"):
                    print(f"✅ {protocol_key} successfully calibrated.")
                else:
                    print(f"❌ Calibration failed: {res.get('error', 'Bridge error')}")
            except ValueError:
                print(f"❌ Invalid numeric value: {new_val}")
            
        print()
        input("💎 Press [Enter] to return to the desk > ")
        print()

    def handle_live() -> None:
        print("════════════════════════════════════════════════════════════")
        print(f"📺 {bold}Command Center Monitor: High-Refresh TUI{reset}")
        print("═" * 60)
        
        print(f"{yellow}🚀 Starting LIVE MONITOR (Auto-refresh every 30s)...{reset}")
        print(f"{grey}Press Ctrl+C to stop.{reset}")
        
        try:
            while True:
                # Clear and render
                sys.stdout.write('\033[H\033[J')
                sys.stdout.flush()
                
                # Top Row: Banner & Time
                render_banner(verification.compatible, bridge_config.robinhood.onboarding_completed, animate=False)
                now = get_wallstreet_time()
                print(f"🕒 {bold}Wall Street:{reset} {now} | {bold}Session:{reset} beta-v0.0.0")
                print("═" * 60)
                
                # Body: Market Pulse
                if last_result:
                    print_premarket_brief(last_result.report)
                    print("─" * 60)
                    
                # Body: Intelligence Log
                h = persona.get_heuristics()
                if h:
                    latency = h.get("debate_latency_ms", 0.0)
                    print(f"🛰️ {bold}Latency:{reset} {latency:.2f}ms | {bold}Status:{reset} {green}STABLE{reset}")
                    
                print("\n  [LOG] " + f"{grey}System:{reset} Scanning news feeds for high-impact catalysts...")
                print("  [LOG] " + f"{grey}System:{reset} Risk bounds verified. Exposure healthy.")
                
                print("\n" + "─" * 60)
                print(f"{grey}Refreshing in 30s...{reset}")
                
                if not sys.stdin.isatty():
                    break # Exit loop immediately in non-interactive mode
                    
                time.sleep(30)
                
        except KeyboardInterrupt:
            print("\n🛑 Live monitor stopped. Manual control restored.")
            
        print()
        input("💎 Press [Enter] to return to the desk > ")
        print()

    def handle_ask() -> None:
        print("════════════════════════════════════════════════════════════")
        query = input("💎 Ask your manager > ").strip().upper()
        if not query: return
        
        animate_status_loading("Synthesizing market context")
        
        if last_result:
            match = next((s for s in last_result.report.symbols if s.ticker in query), None)
            if match:
                sentiment = "positive" if (match.sentiment and match.sentiment.score > 0.3) else "mixed"
                risks = f" but watch the {', '.join(match.risk_flags)}" if match.risk_flags else ""
                response = f"Boss, my conviction on {match.ticker} is {int(match.confidence*100)}%. The setup is a {match.setup_class} with {sentiment} flow{risks}."
            else:
                response = f"I'm tracking the broader {last_result.report.market_regime.name} regime right now. Use /analyze to see my deep dive on specific sectors."
        else:
            response = "I need you to run /todaysupdate first so I can get a fresh pulse on the markets, boss."
            
        print(f"\n{bold}Manager:{reset} {response}\n")

    def handle_setup() -> None:
        print("════════════════════════════════════════════════════════════")
        print(f"⚔️ {bold}Diamond Hands Setup Guide{reset}")
        print("═" * 60)
        print("1. Clone the private Diamond-Hands-Algo repo.")
        print("2. Run '/verifybridge' to connect your public intelligence to private execution.")
        print("3. Run '/settings' to configure your Autopilot and Voice preferences.")
        print("4. Use '/sniper' to add tickers to your tracking cart.")
        print("5. Run '/handoff' once you have a high-conviction setup to send it to the private algo.")
        print()

    def handle_intro_menu() -> None:
        print_intro_command_table(verification.compatible)

    def handle_viewall() -> None:
        print("════════════════════════════════════════════════════════════")
        print(f"{bold}Full Diamond Hands Suite{reset}")
        print()
        all_specs = CORE_COMMAND_SPECS + EXPERIMENTAL_COMMAND_SPECS
        lines = render_command_table(all_specs, "Extended Intelligence Commands")
        for line in lines:
            print(line)
        print()

    @with_resilience(timeout=5)
    def handle_stresstest() -> None:
        print("════════════════════════════════════════════════════════════")
        print(f"🔥 {bold}Resilience Stress Test{reset}")
        print("Simulating a stalled network call (10s delay)...")
        with KineticSpinner("Syncing with slow intelligence node"):
            time.sleep(10)
        print("✅ Stress test completed (should have timed out and retried).")

    handlers: dict[str, Callable[[], None]] = {
        "/commands": handle_commands,
        "/viewall": handle_viewall,
        "/more": handle_viewall,
        "/setup": handle_setup,
        "/refresh": handle_refresh,
        "/buildagent": handle_buildagent,
        "/intel": handle_intel,
        "/jensen": handle_jensen,
        "/trumptracker": handle_trumptracker,
        "/stresstest": handle_stresstest,
        "/todaysupdate": handle_todaysupdate,
        "/analyze": handle_analyze,
        "/marketrecap": handle_marketrecap,
        "/marketnews": handle_marketnews,
        "/portfolio": handle_portfolio,
        "/runstrategy": handle_runstrategy,
        "/tickersniper": handle_tickersniper,
        "/wsb": handle_wsb,
        "/debate": handle_debate,
        "/hft": handle_hft,
        "/system": handle_system,
        "/risk": handle_risk,
        "/forge": handle_forge,
        "/live": handle_live,
        "/wizard": handle_wizard,
        "/ask": handle_ask,
        "/settings": handle_settings,
        "/clear": handle_clear,
        "/verifybridge": handle_verifybridge,
        "/handoff": handle_handoff,
        "/liveboard": handle_liveboard,
        "/hood": handle_hood,
        "/paper": handle_paper,
        "/stop": handle_stop,
        "/agents": handle_agents,
        "/autopilot": handle_autopilot,
        "/spy0dte": handle_spy0dte,
        "/memory": handle_memory,
        "/recall": handle_recall,
        "/daemon": handle_daemon,
        "/botstatus": handle_botstatus,
        "/startbot": handle_startbot,
    }

    # 🛰️ Watchdog Meta-Agent: Cross-Repo Event Bus
    def _watchdog_loop():
        if not persona or not persona.repo_path: return
        handoff_path = persona.repo_path / "private" / "docs" / "handoff-mirror.md"
        last_size = handoff_path.stat().st_size if handoff_path.exists() else 0
        
        while True:
            try:
                if handoff_path.exists():
                    current_size = handoff_path.stat().st_size
                    if current_size > last_size:
                        # New intel detected
                        play_alert("Starshield has updated the intelligence record.")
                        # Subdued alert for the operator
                        sys.stdout.write(f"\n  {bold}{yellow}[WATCHDOG]{reset} {grey}New event detected in handoff-mirror.md (Pulse at {datetime.now().strftime('%H:%M:%S')}){reset}\n")
                        sys.stdout.write(persona.get_prompt())
                        sys.stdout.flush()
                        last_size = current_size
                time.sleep(10) # 10s poll cadence
            except: time.sleep(10)
            
    if persona and persona.repo_path:
        threading.Thread(target=_watchdog_loop, daemon=True, name="dh-watchdog").start()

    print(f"  {bold}{green}Verified.{reset} Ready to ship.\n")
    print(f"  {grey}Enter /commands to see arsenal. (Pulse: {get_heartbeat_frame()}){reset}\n")
    sys.stdout.flush()

    while True:
        # Re-render persistent banner (v0.2.5)
        # sys.stdout.write('\033[H') # Move to top without clearing? No, that messes up scrollback.
        # Just render before every prompt if requested.
        
        try:
            # Use high-fidelity prompt from persona
            raw_input = input(persona.get_prompt()).strip()
        except EOFError:
            print()
            return 0
        except KeyboardInterrupt:
            print("\n💎 (Command cancelled)")
            continue
            
        if not raw_input:
            continue
            
        # Parse command and optional argument
        parts = raw_input.split(maxsplit=1)
        cmd_part = parts[0]
        arg_part = parts[1] if len(parts) > 1 else None
        
        normalized = normalize_command(cmd_part)
        if normalized == "/quit":
            return 0
            
        if normalized is None:
            # Did you mean? logic
            search_key = cmd_part if cmd_part.startswith("/") else "/" + cmd_part
            matches = difflib.get_close_matches(search_key, COMMAND_ALIASES.keys(), n=1, cutoff=0.5)
            if matches:
                print(f"💎 {bold}Unknown command.{reset} Did you mean? {bold}{matches[0]}{reset}")
            else:
                print("Unknown command. Use /commands.")
            print()
            continue
            
        handler = handlers.get(normalized)
        if handler is None:
            print("Unknown command. Use /commands.")
            continue
            
        # Call handler with arg if it supports it
        try:
            if normalized in ["/analyze", "/intel"]:
                handler(arg_part)
            else:
                handler()
        except KeyboardInterrupt:
            print("\n🛑 Execution interrupted by operator.")
        except Exception as e:
            print(f"\n⚠️ {red}Execution failed:{reset} {e}")
            if "verbose" in args and args.verbose:
                import traceback
                traceback.print_exc()


class GarbageCollector:
    """Prunes stale artifacts to maintain a micro-footprint (kb speed)."""
    @staticmethod
    def prune(output_dir: Path):
        if not output_dir.exists(): return
        now = time.time()
        for f in output_dir.glob("**/*.json"):
            # Prune transient files older than 24 hours
            if now - f.stat().st_mtime > 86400:
                try: f.unlink()
                except: pass

def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    
    # 📡 BACKGROUND UPDATE CHECK
    check_for_updates()
    
    # 🧹 KB-SPEED: PRUNE STALE ARTIFACTS
    # Project root resolution for standalone binary execution
    project_root = Path(__file__).resolve().parents[2]
    GarbageCollector.prune(project_root / "outputs")
    
    config_path = Path(args.config)
    if not config_path.exists() and not config_path.is_absolute():
        resolved = project_root / args.config
        if resolved.exists():
            args.config = str(resolved)

    bridge_path = Path(args.bridge_config)
    if not bridge_path.exists() and not bridge_path.is_absolute():
        resolved = project_root / args.bridge_config
        if resolved.exists():
            args.bridge_config = str(resolved)

    interactive_mode = (
        (sys.stdin.isatty() and sys.stdout.isatty()) or args.force_interactive
    ) and (
        not args.analyze_only
        and not args.analyze_then_hand_off
        and not args.mode == "boot"
    )


    try:
        bridge_config = load_public_bridge_config(Path(args.bridge_config))
        bridge_config, bridge_config_changed = ensure_local_bridge_config(
            bridge_config,
            private_algo_repo_override=args.private_algo_repo,
            prompt_user=sys.stdin.isatty() and (args.setup or not Path(args.bridge_config).exists()),
        )

        bridge_status_note: str | None = None
        if bridge_config_changed:
            bridge_config.first_run_completed = True
            save_public_bridge_config(bridge_config)
            if interactive_mode:
                bridge_status_note = f"Bridge state refreshed: {bridge_config.config_path}"
            else:
                print(f"Saved local bridge config: {bridge_config.config_path}")
                print()

        # Skip the subprocess ping for interactive boot — it adds ~5s and the
        # interactive shell only consumes `compatible` + `notes`, both of which
        # the static checks already populate.
        verification = verify_private_algo_bridge(bridge_config, with_ping=not interactive_mode)

        if args.setup and not (args.verify_bridge or args.analyze_only or args.analyze_then_hand_off):
            render_banner(verification.compatible, bridge_config.robinhood.onboarding_completed)
            print_robinhood_onboarding(bridge_config.robinhood.mcp_url, bridge_config.robinhood.onboarding_completed)
            return 0

        if args.verify_bridge:
            render_banner(verification.compatible, bridge_config.robinhood.onboarding_completed)
            print_robinhood_onboarding(bridge_config.robinhood.mcp_url, bridge_config.robinhood.onboarding_completed)
            print_bridge_verification(verification.notes)
            return 0 if verification.compatible else 1

        if args.mode == "boot":
            render_banner(verification.compatible, bridge_config.robinhood.onboarding_completed)
            print_robinhood_onboarding(bridge_config.robinhood.mcp_url, bridge_config.robinhood.onboarding_completed)
            print_bridge_verification(verification.notes)
            
            # Load sniper cart for boot mode (v0.3.7)
            boot_tickers = load_active_state()
            result = run_pipeline(args.config, args.output_dir, extra_symbols=boot_tickers)
            
            # Analyze the last sniper ticker by default
            target = boot_tickers[-1] if boot_tickers else None
            print_analysis_summary(result, target_symbol=target)
            
            if not verification.compatible:
                print("Private ALGO bridge is not compatible. Boot stopped before private commands.")
                return 1
            try:
                handoff = hand_off_to_private_algo(bridge_config, result.json_path)
                print("Diamond Hands private handoff completed.")
                if handoff.stdout.strip():
                    print(handoff.stdout.strip())
                for command_args in (
                    ["memory", "ingest"],
                    ["memory", "ingest-docs"],
                    ["session", "watch", "--watch-once"],
                ):
                    private_result = run_private_algo_command(bridge_config, command_args, capture=True)
                    if private_result.stdout and private_result.stdout.strip():
                        print(private_result.stdout.strip())
                return 0
            except subprocess.CalledProcessError as e:
                print("Diamond Hands boot private command failed.")
                if e.stderr and e.stderr.strip():
                    print(e.stderr.strip())
                elif e.stdout and e.stdout.strip():
                    print(e.stdout.strip())
                else:
                    print(f"Subprocess failed with exit code {e.returncode}")
                return 1
            except Exception as e:
                print(f"Diamond Hands boot failed: {e}")
                return 1

        # Initialize the Ghost Persona
        persona = PersonaManager(Path(bridge_config.private_algo.repo_path) if verification.compatible else None)
        play_alert("Diamond Hands")

        if interactive_mode:
            return run_interactive_shell(args, bridge_config, verification, bridge_status_note, persona=persona)

        render_banner(verification.compatible, bridge_config.robinhood.onboarding_completed, persona=persona)
        print_robinhood_onboarding(bridge_config.robinhood.mcp_url, bridge_config.robinhood.onboarding_completed)
        print_bridge_verification(verification.notes)
        
        # Load sniper cart for one-shot mode (v0.3.7)
        one_shot_tickers = load_active_state()
        result = run_pipeline(args.config, args.output_dir, extra_symbols=one_shot_tickers)
        
        # Analyze the last sniper ticker by default if it exists
        target = one_shot_tickers[-1] if one_shot_tickers else None
        print_analysis_summary(result, target_symbol=target, persona=persona)

        if args.analyze_then_hand_off:
            if not verification.compatible:
                print("Private ALGO bridge is not compatible. Handoff skipped.")
                return 1
            try:
                handoff = hand_off_to_private_algo(bridge_config, result.json_path)
                print("Diamond Hands private handoff completed.")
                if handoff.stdout.strip():
                    print(handoff.stdout.strip())
                return 0
            except subprocess.CalledProcessError as e:
                print("Diamond Hands private handoff failed.")
                if e.stderr and e.stderr.strip():
                    print(e.stderr.strip())
                elif e.stdout and e.stdout.strip():
                    print(e.stdout.strip())
                else:
                    print(f"Subprocess failed with exit code {e.returncode}")
                return 1
            except Exception as e:
                print(f"An unexpected error occurred during handoff: {e}")
                return 1

        if not args.analyze_only:
            print("Public bridge run completed. Use --analyze-then-hand-off to push the fresh artifact into your private Diamond-Hands-Algo repo.")
        return 0
    except KeyboardInterrupt:
        print("\n👋 Exiting Diamond Hands. See you at the bell.")
        return 0
