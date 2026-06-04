from __future__ import annotations

import argparse
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from trading_system.bridge_config import load_public_bridge_config, save_public_bridge_config
from trading_system.bridge_runtime import (
    ensure_local_bridge_config,
    hand_off_to_private_algo,
    verify_private_algo_bridge,
)
from trading_system.config import load_runtime_config
from trading_system.contracts.types import DailyReportContract
from trading_system.pipeline.daily import DailyPipeline, PipelineResult


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Diamond Hands public bridge CLI for Robinhood-first market intelligence.",
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


COMMAND_SPECS = [
    CommandSpec("/todaysupdate", "Market snapshot and catalyst overview"),
    CommandSpec("/analyze", "Deep technical, sentiment, and flow dashboard"),
    CommandSpec("/verifybridge", "Check private ALGO bridge compatibility"),
    CommandSpec("/handoff", "Send the current artifact to Diamond-Hands-Algo"),
    CommandSpec("/quit", "Exit the DH CLI session"),
]

COMMAND_ALIASES = {
    "/todaysupdate": "/todaysupdate",
    "/today-status": "/todaysupdate",
    "/analyze": "/analyze",
    "/verifybridge": "/verifybridge",
    "/verify-bridge": "/verifybridge",
    "/handoff": "/handoff",
    "/hand-off": "/handoff",
    "/commands": "/commands",
    "/help": "/commands",
    "help": "/commands",
    "/quit": "/quit",
    "quit": "/quit",
    "exit": "/quit",
}


def render_banner() -> None:
    cyan = "\033[38;2;0;180;255m"
    cyan_bright = "\033[38;2;140;225;255m"
    bold = "\033[1m"
    reset = "\033[0m"

    if not sys.stdout.isatty():
        cyan = ""
        cyan_bright = ""
        bold = ""
        reset = ""

    banner_block = [
        "      /\\",
        "     /  \\",
        "    / /\\ \\",
        "   / /  \\ \\",
        "  /_/ /\\ \\_\\",
        "  \\ \\ \\/ / /",
        "   \\ \\  / /",
        "    \\ \\/ /",
        "     \\  /",
        "      \\/",
        "  DIAMOND HANDS",
        "    MCP BRIDGE",
    ]
    emoji_line = "      💎🤝"
    byline = "  by: internetdialup"
    divider = "  ───────────────"
    tagline = "Robinhood-first public bridge for market intelligence and private ALGO handoff."

    print()
    for line in banner_block[:10]:
        print(f"{cyan_bright}{line}{reset}")
    print()
    print(f"{bold}{cyan_bright}{banner_block[10]}{reset}")
    print(f"{bold}{cyan}{banner_block[11]}{reset}")
    print(f"{cyan_bright}{divider}{reset}")
    print(emoji_line)
    print(f"{cyan}{byline}{reset}")
    print()
    print(tagline)
    print()


def animate_status_loading(message: str) -> None:
    if not sys.stdout.isatty():
        print(message)
        return

    frames = ["💎", "💎.", "💎..", "💎..."]
    for frame in frames:
        sys.stdout.write(f"\r{message} {frame}")
        sys.stdout.flush()
        time.sleep(0.5)
    sys.stdout.write("\r" + " " * (len(message) + 6) + "\r")
    sys.stdout.flush()


def render_command_table() -> list[str]:
    command_width = max(len(spec.command) for spec in COMMAND_SPECS)
    lines = [
        "DH command desk",
        f"{'Command'.ljust(command_width)}  Purpose",
        f"{'-' * command_width}  {'-' * 38}",
    ]
    for spec in COMMAND_SPECS:
        lines.append(f"{spec.command.ljust(command_width)}  {spec.purpose}")
    return lines


def print_intro_command_table() -> None:
    print("Type /commands anytime to reopen the desk.")
    print()
    lines = render_command_table()
    if not sys.stdout.isatty():
        for line in lines:
            print(line)
        print()
        return

    for line in lines:
        print(line)
        time.sleep(0.08)
    print()


def print_robinhood_onboarding(mcp_url: str, completed: bool) -> None:
    print("Robinhood Agentic Trading")
    print(f"- MCP URL: {mcp_url}")
    print("- Codex CLI: codex mcp add robinhood-trading --url " + mcp_url)
    print("- Codex app: Settings -> MCP servers -> Streamable HTTP -> add the MCP URL")
    print("- Robinhood uses a dedicated agentic trading account with activity monitoring and a kill switch.")
    print(f"- Onboarding recorded: {'yes' if completed else 'no'}")
    print()


def print_bridge_verification(notes: list[str]) -> None:
    print("Private Bridge Verification")
    for note in notes:
        print(f"- {note}")
    print()


def print_today_status(result: PipelineResult) -> None:
    report = result.report
    cyan = "\033[38;2;0;180;255m"
    green = "\033[32m"
    yellow = "\033[33m"
    red = "\033[31m"
    reset = "\033[0m"
    bold = "\033[1m"
    
    # Juicy multi-color headline
    print(f"{bold}{cyan}💎 DIAMOND {green}HANDS {yellow}MARKET {cyan}STATUS 💎{reset}")
    print(f"Generated: {report.generated_at} | Benchmark: {report.benchmark}")
    print("════════════════════════════════════════════════════════════")
    
    # Market Regime
    print(f"{bold}{green}📈 Market Regime:{reset} {report.market_regime.name} (Score: {report.market_regime.score})")
    print(f"   {report.market_regime.summary}")
    print("────────────────────────────────────────────────────────────")
    
    # Regime Drivers
    print(f"{bold}{yellow}🔥 Top Regime Drivers:{reset}")
    for driver in report.market_regime.drivers[:3]:
        print(f"   • {driver}")
    print("────────────────────────────────────────────────────────────")
    
    # Top 3 Symbols
    print(f"{bold}{cyan}🚀 Top Actionable Setups:{reset}")
    sorted_symbols = sorted(report.symbols, key=lambda s: s.confidence, reverse=True)
    for symbol in sorted_symbols[:3]:
        bias = symbol.direction_bias.lower()
        if bias == "bullish":
            emoji = "📈"
            rocket = "🚀 "
            decider = f"{green}CALL{reset}"
        elif bias == "bearish":
            emoji = "📉"
            rocket = "   "
            decider = f"{red}PUT {reset}"
        else:
            emoji = "↔️ "
            rocket = "   "
            decider = f"{yellow}HOLD{reset}"
            
        risk_str = f" [🚩 {', '.join(symbol.risk_flags[:2])}]" if symbol.risk_flags else ""
        print(f"   {emoji} {rocket}{bold}{symbol.ticker:<5}{reset} | Conf: {symbol.confidence:.2f} | Setup: {symbol.setup_class} | {decider}{risk_str}")
    print("────────────────────────────────────────────────────────────")
    
    # Macro Themes
    print(f"{bold}{green}📰 Macro Catalysts:{reset}")
    for news in report.top_12_news[:3]:
        print(f"   • {news.topic}: {news.summary}")
    print("════════════════════════════════════════════════════════════")
    print("Next: /analyze for full metrics, /verifybridge, /handoff, or /quit.")
    print()


def print_analysis_summary(result: PipelineResult) -> None:
    report = result.report
    cyan = "\033[38;2;0;180;255m"
    green = "\033[32m"
    yellow = "\033[33m"
    red = "\033[31m"
    reset = "\033[0m"
    bold = "\033[1m"
    
    print(f"{bold}{cyan}💎 DIAMOND {green}HANDS {yellow}DEEP {cyan}ANALYSIS 💎{reset}")
    print(f"Status: {report.market_regime.name} | Benchmark: {report.benchmark}")
    print("════════════════════════════════════════════════════════════════════════════════════")
    
    # Top Setup Spotlight
    top_symbol = max(report.symbols, key=lambda s: s.confidence)
    print(f"{bold}{yellow}🔥 TOP SETUP SPOTLIGHT:{reset} {bold}{top_symbol.ticker}{reset}")
    print(f"Setup: {top_symbol.setup_class} | Bias: {top_symbol.direction_bias} | Confidence: {top_symbol.confidence:.2f}")
    print(f"Technical Posture: {top_symbol.technical_posture}")
    
    feat = top_symbol.supporting_features
    tech_line = f"RSI: {feat.get('rsi', 'N/A')} | MACD Hist: {feat.get('macd_histogram', 'N/A')} | BB %B: {feat.get('bollinger_pct_b', 'N/A')}"
    print(f"Technicals: {tech_line}")
    
    sent_score = top_symbol.sentiment.score if top_symbol.sentiment else "N/A"
    flow_pos = top_symbol.flow.dealer_positioning if top_symbol.flow else "N/A"
    print(f"Sentiment: {sent_score} | Flow Position: {flow_pos}")
    print("────────────────────────────────────────────────────────────────────────────────────")
    
    # Symbol Analysis Table
    print(f"{bold}{'Ticker':<9} {'Bias':<7} {'Action':<6} {'Setup':<13} {'Conf':<5} {'RSI':<5} {'Flow':<6} {'Sent':<6} {'Risks'}{reset}")
    print(f"{'-'*9} {'-'*7} {'-'*6} {'-'*13} {'-'*5} {'-'*5} {'-'*6} {'-'*6} {'-'*15}")
    
    for s in report.symbols:
        f = s.supporting_features
        rsi_val = f"{f.get('rsi', 0.0):.1f}"
        flow_score = f"{s.flow.score if s.flow else 0.0:.2f}"
        sent_score = f"{s.sentiment.score if s.sentiment else 0.0:.2f}"
        
        # Risks
        risk_count = len(s.risk_flags)
        if risk_count > 0:
            risks = f"🚩 {risk_count} flags"
        else:
            risks = f"{green}clean{reset}"
            
        # Action/Decider
        bias = s.direction_bias.lower()
        if bias == "bullish":
            emoji = "📈"
            decider = f"{green}CALL{reset}"
        elif bias == "bearish":
            emoji = "📉"
            decider = f"{red}PUT {reset}"
        else:
            emoji = "↔️ "
            decider = f"{yellow}HOLD{reset}"
            
        print(f"{emoji} {s.ticker:<5} {s.direction_bias:<7} {decider:<15} {s.setup_class[:12]:<13} {s.confidence:<5.2f} {rsi_val:<5} {flow_score:<6} {sent_score:<6} {risks}")
    
    print("════════════════════════════════════════════════════════════════════════════════════")
    print(f"Markdown: {result.markdown_path}")
    print(f"JSON:     {result.json_path}")
    print()


def run_pipeline(config_path: str, output_dir: str | None) -> PipelineResult:
    config = load_runtime_config(Path(config_path))
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


def normalize_command(raw_command: str) -> str | None:
    return COMMAND_ALIASES.get(raw_command.strip().lower())


def show_startup_intro() -> None:
    animate_status_loading("DH boot sequence")
    print_intro_command_table()


def run_interactive_shell(
    args: argparse.Namespace,
    bridge_config,
    verification,
) -> int:
    last_result: PipelineResult | None = None
    show_startup_intro()

    def handle_todaysupdate() -> None:
        nonlocal last_result
        animate_status_loading("Loading today's market status")
        last_result = run_pipeline(args.config, args.output_dir)
        print_today_status(last_result)
        if prompt_yes_no("Analyze today's data now?"):
            print()
            print_analysis_summary(last_result)

    def handle_analyze() -> None:
        nonlocal last_result
        if last_result is None:
            animate_status_loading("Building analysis")
            last_result = run_pipeline(args.config, args.output_dir)
        print_analysis_summary(last_result)

    def handle_verifybridge() -> None:
        print_bridge_verification(verification.notes)

    def handle_handoff() -> None:
        nonlocal last_result
        if not verification.compatible:
            print("Private ALGO bridge is not compatible. Handoff blocked.")
            print()
            return
        if last_result is None:
            animate_status_loading("Building analysis for handoff")
            last_result = run_pipeline(args.config, args.output_dir)
        try:
            handoff = hand_off_to_private_algo(bridge_config, last_result.json_path)
            print("Diamond Hands private handoff completed.")
            if handoff.stdout.strip():
                print(handoff.stdout.strip())
        except subprocess.CalledProcessError as e:
            print("Diamond Hands private handoff failed.")
            if e.stderr and e.stderr.strip():
                print(e.stderr.strip())
            elif e.stdout and e.stdout.strip():
                print(e.stdout.strip())
            else:
                print(f"Subprocess failed with exit code {e.returncode}")
        print()

    handlers: dict[str, Callable[[], None]] = {
        "/commands": print_intro_command_table,
        "/todaysupdate": handle_todaysupdate,
        "/analyze": handle_analyze,
        "/verifybridge": handle_verifybridge,
        "/handoff": handle_handoff,
    }

    while True:
        try:
            command = input("diamond-hands> ").strip()
        except EOFError:
            print()
            return 0
        if not command:
            continue
        normalized = normalize_command(command)
        if normalized == "/quit":
            return 0
        if normalized is None:
            print("Unknown command. Use /commands.")
            print()
            continue
        handler = handlers.get(normalized)
        if handler is None:
            print("Unknown command. Use /commands.")
            continue
        handler()


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    render_banner()
    interactive_mode = (
        sys.stdin.isatty()
        and sys.stdout.isatty()
        and not args.analyze_only
        and not args.analyze_then_hand_off
        and not args.verify_bridge
    )

    bridge_config = load_public_bridge_config(Path(args.bridge_config))
    bridge_config, bridge_config_changed = ensure_local_bridge_config(
        bridge_config,
        private_algo_repo_override=args.private_algo_repo,
        prompt_user=sys.stdin.isatty() and (args.setup or not Path(args.bridge_config).exists()),
    )

    if bridge_config_changed:
        bridge_config.first_run_completed = True
        save_public_bridge_config(bridge_config)
        print(f"Saved local bridge config: {bridge_config.config_path}")
        print()

    verification = verify_private_algo_bridge(bridge_config)

    if args.setup and not (args.verify_bridge or args.analyze_only or args.analyze_then_hand_off):
        print_robinhood_onboarding(bridge_config.robinhood.mcp_url, bridge_config.robinhood.onboarding_completed)
        return 0

    if args.verify_bridge:
        print_robinhood_onboarding(bridge_config.robinhood.mcp_url, bridge_config.robinhood.onboarding_completed)
        print_bridge_verification(verification.notes)
        return 0 if verification.compatible else 1

    if interactive_mode:
        return run_interactive_shell(args, bridge_config, verification)

    print_robinhood_onboarding(bridge_config.robinhood.mcp_url, bridge_config.robinhood.onboarding_completed)
    print_bridge_verification(verification.notes)
    result = run_pipeline(args.config, args.output_dir)
    print_analysis_summary(result)

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
