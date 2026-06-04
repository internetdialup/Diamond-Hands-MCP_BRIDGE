from __future__ import annotations

import argparse
import sys
from pathlib import Path

from trading_system.bridge_config import load_public_bridge_config, save_public_bridge_config
from trading_system.bridge_runtime import (
    ensure_local_bridge_config,
    hand_off_to_private_algo,
    verify_private_algo_bridge,
)
from trading_system.config import load_runtime_config
from trading_system.pipeline.daily import DailyPipeline


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


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    render_banner()

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

    print_robinhood_onboarding(bridge_config.robinhood.mcp_url, bridge_config.robinhood.onboarding_completed)
    verification = verify_private_algo_bridge(bridge_config)
    print_bridge_verification(verification.notes)

    if args.setup and not (args.verify_bridge or args.analyze_only or args.analyze_then_hand_off):
        return 0

    if args.verify_bridge:
        return 0 if verification.compatible else 1

    config = load_runtime_config(Path(args.config))
    if args.output_dir:
        config.reporting.output_dir = Path(args.output_dir)

    pipeline = DailyPipeline(config)
    result = pipeline.run()

    print("Diamond Hands Bridge Report")
    print(f"- Markdown report: {result.markdown_path}")
    print(f"- JSON artifact: {result.json_path}")
    print(f"- Market regime: {result.report.market_regime.name}")
    print(f"- Top setup: {result.report.top_setup or 'none'}")
    print()

    if args.analyze_then_hand_off:
        if not verification.compatible:
            print("Private ALGO bridge is not compatible. Handoff skipped.")
            return 1
        handoff = hand_off_to_private_algo(bridge_config, result.json_path)
        print("Diamond Hands private handoff completed.")
        if handoff.stdout.strip():
            print(handoff.stdout.strip())
        return 0

    if not args.analyze_only:
        print("Public bridge run completed. Use --analyze-then-hand-off to push the fresh artifact into your private Diamond-Hands-Algo repo.")
    return 0
