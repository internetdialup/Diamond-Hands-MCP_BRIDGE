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


@dataclass
class StatusEvent:
    label: str
    summary: str
    priority: int


@dataclass(frozen=True)
class CommandSpec:
    command: str
    purpose: str


COMMAND_SPECS = [
    CommandSpec("/todaysupdate", "Show the market desk and top 10 events"),
    CommandSpec("/analyze", "Run the full Diamond Hands daily analysis"),
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
        time.sleep(0.15)
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


def build_status_events(report: DailyReportContract) -> list[StatusEvent]:
    events: list[StatusEvent] = [
        StatusEvent(
            label="Market Regime",
            summary=f"{report.market_regime.name} | {report.market_regime.summary}",
            priority=100,
        ),
        StatusEvent(
            label="Benchmark",
            summary=f"{report.benchmark} | score {report.market_regime.score}",
            priority=95,
        ),
    ]

    if report.top_setup:
        events.append(
            StatusEvent(
                label="Top Setup",
                summary=report.top_setup,
                priority=90,
            )
        )

    for driver in report.market_regime.drivers[:2]:
        events.append(StatusEvent(label="Regime Driver", summary=driver, priority=85))

    for symbol in sorted(report.symbols, key=lambda item: item.confidence, reverse=True)[:3]:
        risk_suffix = ""
        if symbol.risk_flags:
            risk_suffix = f" | risks: {', '.join(symbol.risk_flags[:2])}"
        elif symbol.no_trade:
            risk_suffix = " | no-trade"
        events.append(
            StatusEvent(
                label=symbol.ticker,
                summary=(
                    f"{symbol.setup_class} | {symbol.technical_posture} | "
                    f"confidence {symbol.confidence:.2f}{risk_suffix}"
                ),
                priority=80,
            )
        )

    reserved_topics = {"Market Regime", f"Benchmark: {report.benchmark}"}
    for item in report.top_12_news:
        if len(events) >= 10:
            break
        if item.topic in reserved_topics:
            continue
        events.append(
            StatusEvent(
                label=item.topic,
                summary=item.summary,
                priority=70,
            )
        )

    for flag in report.no_trade_flags:
        if len(events) >= 10:
            break
        events.append(StatusEvent(label="Risk Gate", summary=flag, priority=60))

    unique_events: list[StatusEvent] = []
    seen: set[tuple[str, str]] = set()
    for event in sorted(events, key=lambda item: item.priority, reverse=True):
        key = (event.label, event.summary)
        if key in seen:
            continue
        seen.add(key)
        unique_events.append(event)
        if len(unique_events) == 10:
            break
    return unique_events


def print_today_status(result: PipelineResult) -> None:
    report = result.report
    print("Today's Status")
    print(f"Generated: {report.generated_at}")
    print()
    for index, event in enumerate(build_status_events(report), start=1):
        print(f"{index:02d}. {event.label} :: {event.summary}")
    print()
    print("Next: analyze today's data, verify bridge, hand off, or quit.")
    print()


def print_analysis_summary(result: PipelineResult) -> None:
    print("Diamond Hands Bridge Report")
    print(f"- Markdown report: {result.markdown_path}")
    print(f"- JSON artifact: {result.json_path}")
    print(f"- Market regime: {result.report.market_regime.name}")
    print(f"- Top setup: {result.report.top_setup or 'none'}")
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
