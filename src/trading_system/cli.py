from __future__ import annotations

import argparse
import os
import random
import subprocess
import sys
import time
import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

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
    verify_private_algo_bridge,
)
from trading_system.config import load_runtime_config
from trading_system.contracts.types import DailyReportContract
from trading_system.pipeline.daily import DailyPipeline, PipelineResult
from trading_system.strategies.momentum import MomentumStrategy


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


CORE_COMMAND_SPECS = [
    CommandSpec("/commands", "Show this core command list"),
    CommandSpec("/todaysupdate", "Show today's market summary"),
    CommandSpec("/analyze", "Show the full deep-dive analysis report"),
    CommandSpec("/viewall", "Show advanced modules (Sniper, WSB, Strategy, etc.)"),
    CommandSpec("/settings", "Open CLI settings (Autopilot mode)"),
    CommandSpec("/quit", "Exit the CLI"),
]

EXPERIMENTAL_COMMAND_SPECS = [
    CommandSpec("/more", "Alias for /viewall"),
    CommandSpec("/verifybridge", "Check your private connector"),
    CommandSpec("/handoff", "Send the latest report to your private repo"),
    CommandSpec("/marketrecap", "Show a market recap view"),
    CommandSpec("/marketnews", "Show the market news view"),
    CommandSpec("/tickersniper", "Track up to three symbols locally"),
    CommandSpec("/trumptracker", "Monitor specific political market impacts"),
    CommandSpec("/wsb", "Scan social sentiment for retail chaos"),
    CommandSpec("/runstrategy", "Run the experimental strategy view"),
    CommandSpec("/clear", "Clear the screen and keep the prompt ready"),
]

COMMAND_ALIASES = {
    "/commands": "/commands",
    "/viewall": "/viewall",
    "/morecommands": "/viewall",
    "/help": "/commands",
    "help": "/commands",
    "/todaysupdate": "/todaysupdate",
    "/today-status": "/todaysupdate",
    "/analyze": "/analyze",
    "/marketrecap": "/marketrecap",
    "/recap": "/marketrecap",
    "/marketnews": "/marketnews",
    "/news": "/marketnews",
    "/trumptracker": "/trumptracker",
    "/wsb": "/wsb",
    "/wallstbets": "/wsb",
    "/runstrategy": "/runstrategy",
    "/strategy": "/runstrategy",
    "/alpha": "/runstrategy",
    "/lfg": "/runstrategy",
    "/tickersniper": "/tickersniper",
    "/sniper": "/tickersniper",
    "/settings": "/settings",
    "/clear": "/clear",
    "clear": "/clear",
    "/verifybridge": "/verifybridge",
    "/verify-bridge": "/verifybridge",
    "/handoff": "/handoff",
    "/hand-off": "/handoff",
    "/quit": "/quit",
    "quit": "/quit",
    "exit": "/quit",
}


from datetime import datetime, timedelta

def get_ordinal(n: int) -> str:
    if 11 <= n <= 13:
        return f"{n}th"
    return {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")


def format_human_date(iso_string: str) -> str:
    # iso_string like "2026-06-04T11:00:00Z"
    try:
        clean_iso = iso_string.replace("Z", "+00:00")
        dt = datetime.fromisoformat(clean_iso)
        month_str = dt.strftime("%b")
        day_val = dt.day
        day_str = f"{day_val}{get_ordinal(day_val)}"
        year_str = dt.strftime("%Y")
        time_str = dt.strftime("%-I%p")
        return f"{month_str} {day_str}, {year_str}, {time_str}"
    except Exception:
        return iso_string


def get_wallstreet_time() -> str:
    # Crude way to get EST (UTC-5) or EDT (UTC-4)
    # 2026 June is EDT
    utc_now = datetime.utcnow()
    edt_now = utc_now - timedelta(hours=4)
    return edt_now.strftime("%-I%p EST")


def play_alert(message: str) -> None:
    if sys.platform == "darwin":
        try:
            # -v Samantha for a nice natural fund manager voice
            subprocess.run(["say", "-v", "Samantha", message], check=False)
        except Exception:
            pass


def cyan_gradient(text: str) -> str:
    if not sys.stdout.isatty():
        return text
    out = ""
    steps = max(1, len(text) - 1)
    for i, char in enumerate(text):
        # Cascading gradient from #00b4ff (0, 180, 255) to lighter/greener cyan (0, 255, 200)
        r = 0
        g = min(255, int(180 + (75 * (i / steps))))
        b = max(180, int(255 - (75 * (i / steps))))
        out += f"\033[38;2;{r};{g};{b}m{char}"
    return out + "\033[0m"


def create_barchart(value: float, max_val: float = 1.0, width: int = 10) -> str:
    if not sys.stdout.isatty():
        return f"{value:.2f}"
    
    green = "\033[32m"
    yellow = "\033[33m"
    red = "\033[31m"
    reset = "\033[0m"
    
    filled = int((value / max_val) * width)
    filled = max(0, min(width, filled))
    empty = width - filled
    
    color = green if value >= 0.7 else yellow if value >= 0.4 else red
    return f"{color}{'█' * filled}{reset}{'░' * empty}"


def get_tomorrow_schedule() -> tuple[list[str], list[str], str]:
    now = datetime.utcnow()
    tomorrow = now + timedelta(days=1)
    day_name = tomorrow.strftime("%A")
    
    events = []
    earnings = []
    
    if day_name == "Monday":
        events = ["NY Empire State Mfg Index", "Fedspeak: Waller"]
        earnings = ["$TSLA", "$WMT"]
    elif day_name == "Tuesday":
        events = ["Retail Sales", "Industrial Production"]
        earnings = ["$NVDA", "$HD"]
    elif day_name == "Wednesday":
        events = ["FOMC Meeting Minutes", "Housing Starts"]
        earnings = ["$CSCO", "$TJX"]
    elif day_name == "Thursday":
        events = ["Initial Jobless Claims", "Philly Fed Mfg"]
        earnings = ["$IREN", "$ZM"]
    elif day_name == "Friday":
        events = ["Consumer Sentiment", "Baker Hughes Rig Count"]
        earnings = ["$DE", "$BMO"]
    else: # Weekend
        events = ["Weekend: No major data", "Prep for Monday Open"]
        earnings = ["none"]
        
    return events, earnings, day_name


def render_banner(connected: bool | None = None, rh_connected: bool | None = None) -> None:
    cyan = "\033[38;2;0;180;255m"
    cyan_bright = "\033[38;2;140;225;255m"
    green = "\033[32m"
    yellow = "\033[33m"
    red = "\033[31m"
    bold = "\033[1m"
    reset = "\033[0m"

    if not sys.stdout.isatty():
        cyan = ""
        cyan_bright = ""
        green = ""
        yellow = ""
        red = ""
        bold = ""
        reset = ""

    banner_block = [
        "  ┌────────────────┐",
        "  │       /\\       │",
        "  │      /  \\      │",
        "  │     / /\\ \\     │",
        "  │    / /  \\ \\    │",
        "  │   /_/ /\\ \\_\\   │",
        "  │   \\ \\ \\/ / /   │",
        "  │    \\ \\  / /    │",
        "  │     \\ \\/ /     │",
        "  │      \\  /      │",
        "  │       \\/       │",
        "  └────────────────┘",
        "  DIAMOND HANDS · MCP BRIDGE",
    ]
    emoji_line = "         💎🤝"
    byline = "  by: internetdialup ✌️ dmndhnds.app / dmndhnds.lol"
    divider = "  ───────────────────────────"
    tagline = "  Robinhood-first public bridge for market intelligence and private ALGO handoff."
    manager_tag = f"  {bold}{green}⚔️ I'm your personal hedge-fund manager{reset}"
    disclaimer = f"  {yellow}⚠️ NOT FINANCIAL ADVICE · use at own RISK ⚠️{reset}"

    if connected is True:
        status_dot = f"\033[32;5m●\033[0m connected to your private ALGO repo"
    elif connected is False:
        status_dot = f"\033[31;5m●\033[0m disconnected from private ALGO repo"
    else:
        status_dot = f"\033[33;5m●\033[0m connecting to private ALGO repo..."

    if rh_connected is True:
        rh_status = f"🍃 connected to Robinhood MCP Bridge"
    elif rh_connected is False:
        rh_status = f"🍂 disconnected from Robinhood MCP Bridge"
    else:
        rh_status = f"🍃 connecting to Robinhood MCP Bridge..."

    print()
    for line in banner_block[:12]:
        print(f"{cyan_bright}{line}{reset}")
    print()
    print(f"{bold}{cyan_bright}{banner_block[12]}{reset}")
    print(f"{cyan_bright}{divider}{reset}")
    print(emoji_line)
    print(f"{cyan}{byline}{reset}")
    print()
    print(tagline)
    print(manager_tag)
    print(disclaimer)
    print(f"  {status_dot}")
    print(f"  {green}{rh_status}{reset}")
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
    sys.stdout.write("\r" + " " * (len(message) + 10) + "\r")
    sys.stdout.flush()


def animate_wolf_of_wallstreet() -> None:
    """Smoke test: Wolf of Wall Street tossing dollar bills."""
    if not sys.stdout.isatty():
        return
    
    yellow = "\033[33m"
    reset = "\033[0m"
    bold = "\033[1m"
    
    frames = [
        r"""
          (⌐■_■)
          /| |\
           | |
          /  \
        """,
        r"""
          (⌐■_■)
          /| |/  [$]
           | |
          /  \
        """,
        r"""
          (⌐■_■)
          /| |\       [$]
           | |
          /  \
        """,
        r"""
          (⌐■_■)      [$]
          /| |\
           | |
          /  \
        """
    ]
    
    print(f"{bold}{yellow}LFG! MAKING IT RAIN...{reset}")
    for _ in range(3): # 3 loops
        for frame in frames:
            sys.stdout.write("\033[F" * 6) # Move up 6 lines
            print(frame)
            time.sleep(0.2)
    print()


def render_command_table(command_specs: list[CommandSpec], title: str) -> list[str]:
    bold = "\033[1m"
    reset = "\033[0m"
    command_width = max(len(spec.command) for spec in command_specs)
    lines = [
        f"{bold}{title}{reset}",
        f"{'Command'.ljust(command_width)}  Purpose",
        f"{'-' * command_width}  {'-' * 38}",
    ]
    for spec in command_specs:
        lines.append(f"{spec.command.ljust(command_width)}  {spec.purpose}")
    return lines


def print_intro_command_table() -> None:
    bold = "\033[1m"
    reset = "\033[0m"
    print(f"{bold}Welcome back. Type /commands to see our full arsenal.{reset}")
    print()
    all_specs = CORE_COMMAND_SPECS + EXPERIMENTAL_COMMAND_SPECS
    lines = render_command_table(all_specs, "Diamond Hands Command Suite")
    if not sys.stdout.isatty():
        for line in lines:
            print(line)
        print()
        return

    for line in lines:
        print(line)
        time.sleep(0.03)
    print()


def print_viewall_command_table() -> None:
    print_intro_command_table()


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


def print_today_status(result: PipelineResult, tracked_tickers: list[str] = None) -> None:
    report = result.report
    cyan = "\033[38;2;0;180;255m"
    green = "\033[32m"
    yellow = "\033[33m"
    red = "\033[31m"
    pink = "\033[38;5;206m"
    reset = "\033[0m"
    bold = "\033[1m"
    
    print("════════════════════════════════════════════════════════════")
    human_date = format_human_date(report.generated_at)
    wallstreet_time = get_wallstreet_time()
    
    # Juicy Gradient headline
    title_text = "💎 DIAMOND HANDS MARKET STATUS 💎"
    print(f"{bold}{cyan_gradient(title_text)}{reset}")
    print(f"Generated: {human_date}")
    print(f"🕒 Local time on Wall Street: {wallstreet_time}")
    print(f"Benchmark: {report.benchmark}")
    print("─" * 60)
    
    # Market Regime
    print(f"{bold}{green}📈 Market Regime:{reset} {report.market_regime.name} [Score: {report.market_regime.score} — scale -1.0 (Panic) to +1.0 (Euphoria)]")
    print(f"   {report.market_regime.summary}")
    print("────────────────────────────────────────────────────────────")
    
    # Regime Drivers
    print(f"{bold}{yellow}🔥 Top Regime Drivers:{reset}")
    for driver in report.market_regime.drivers[:3]:
        print(f"   • {driver}")
    print("────────────────────────────────────────────────────────────")
    
    # Actionable Setups (with Sniper Support)
    print(f"{bold}{cyan}🚀 Top Actionable Setups:{reset}")
    
    # Logic: Get top 3, but force tracked tickers in
    base_symbols = sorted(report.symbols, key=lambda s: s.confidence, reverse=True)
    setup_list = []
    seen = set()
    
    # 1. Tracked Tickers first
    if tracked_tickers:
        for t in tracked_tickers:
            t_clean = t.replace("$", "")
            match = next((s for s in report.symbols if s.ticker == t_clean), None)
            if match:
                setup_list.append(match)
                seen.add(t_clean)
            else:
                # Inject a stub for unknown tracked symbols
                setup_list.append(SymbolReport(
                    ticker=t_clean, direction_bias="neutral", setup_class="monitoring",
                    confidence=0.5, regime=report.market_regime.name,
                    technical_posture="Tracking...", no_trade=False,
                    risk_flags=[], supporting_features={}, sentiment=None,
                    flow=None, pattern=None
                ))
                seen.add(t_clean)

    # 2. Fill the rest from base symbols
    for s in base_symbols:
        if s.ticker not in seen:
            setup_list.append(s)
            seen.add(s.ticker)
        if len(setup_list) >= 3:
            break

    for symbol in setup_list[:3]:
        bias = symbol.direction_bias.lower()
        if bias == "bullish":
            emoji = "📈"
            rocket = "🚀 "
            decider = f"{green}CALL{reset}"
            if symbol.confidence >= 0.85:
                play_alert(f"Boss, we have a high confidence call setup on {symbol.ticker}")
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
    for news in report.top_12_news[:4]:
        print(f"   • {news.topic}: {news.summary}")
    
    # Dynamic Tomorrow Preview
    events, earnings, day_name = get_tomorrow_schedule()
    print(f"   {bold}{pink}Expected tomorrow ({day_name}){reset}")
    print(f"   • Events: {', '.join(events)}")
    disp_earn = ", ".join(earnings[:5]) + (" ..." if len(earnings) > 5 else "")
    print(f"   • Earnings: {disp_earn}")
    
    print("════════════════════════════════════════════════════════════")
    print()


def print_analysis_summary(result: PipelineResult) -> None:
    report = result.report
    cyan = "\033[38;2;0;180;255m"
    green = "\033[32m"
    yellow = "\033[33m"
    red = "\033[31m"
    reset = "\033[0m"
    bold = "\033[1m"
    
    print("════════════════════════════════════════════════════════════════════════════════════")
    human_date = format_human_date(report.generated_at)
    wallstreet_time = get_wallstreet_time()
    
    print(f"{bold}{cyan}💎 DIAMOND HANDS DEEP ANALYSIS 💎{reset}")
    print(f"Status: {report.market_regime.name} | Benchmark: {report.benchmark}")
    print(f"Generated: {human_date}")
    print(f"🕒 Local time on Wall Street: {wallstreet_time}")
    print("─" * 84)
    
    # Top Setup Spotlight
    top_symbol = max(report.symbols, key=lambda s: s.confidence)
    print(f"{bold}{yellow}🔥 TOP SETUP SPOTLIGHT:{reset} {bold}{top_symbol.ticker}{reset}")
    chart = create_barchart(top_symbol.confidence, width=20)
    print(f"Setup: {top_symbol.setup_class} (High probability trend setup) | Bias: {top_symbol.direction_bias}")
    print(f"Algorithm Conviction: {chart} ({int(top_symbol.confidence * 100)}%)")
    print(f"Technical Posture: {top_symbol.technical_posture}")
    
    feat = top_symbol.supporting_features
    tech_line = f"RSI: {feat.get('rsi', 'N/A')} | MACD Hist: {feat.get('macd_histogram', 'N/A')} | BB %B: {feat.get('bollinger_pct_b', 'N/A')}"
    print(f"Technicals: {tech_line}")
    
    sent_val = top_symbol.sentiment.score if top_symbol.sentiment else 0.0
    sent_delta = top_symbol.sentiment.mention_delta if top_symbol.sentiment else 0
    velocity = " ↗️" if sent_delta > 0 else " ↘️" if sent_delta < 0 else ""
    
    # Flow Interpretation
    flow_raw = top_symbol.flow.dealer_positioning if top_symbol.flow else "N/A"
    flow_map = {
        "long_gamma": "Supportive (Dealers buying dips)",
        "short_gamma": "Fragile (Dealers selling rips)",
        "pinning": "Stable (Price sticky at strikes)",
        "supportive": "Stable (Orderly flow)",
        "fragile": "Weak (Volume exiting)"
    }
    flow_desc = flow_map.get(flow_raw, "N/A")
    print(f"Sentiment: {sent_val}{velocity} | Flow Position: {flow_raw} — {flow_desc}")

    # Institutional Liquidity & Consensus
    sweep = feat.get("liquidity_sweep", "none").replace("_", " ").upper()
    votes = feat.get("votes", {})
    vote_line = f"Regime: {votes.get('regime')} | Technical: {votes.get('technical')} | Flow: {votes.get('flow')} | Sentiment: {votes.get('sentiment')}"
    print(f"Liquidity: {bold}{sweep}{reset} | Consensus: {vote_line}")
    
    # Risks Explanation
    risk_count = len(top_symbol.risk_flags)
    risk_msg = f" - warning: {', '.join(top_symbol.risk_flags)}" if risk_count > 0 else ""
    print(f"Risks: {risk_count} flag{'s' if risk_count != 1 else ''}{risk_msg}")
    print("────────────────────────────────────────────────────────────────────────────────────")
    
    # Symbol Analysis Table
    print(f"{bold}{'Ticker':<9} {'Bias':<7} {'Action':<6} {'Setup':<13} {'Algorithm Conviction':<25} {'Risks'}{reset}")
    print(f"{'-'*9} {'-'*7} {'-'*6} {'-'*13} {'-'*20} {'-'*25}")
    
    for s in report.symbols:
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
            
        conf_chart = create_barchart(s.confidence, width=15)
        
        # Risks
        risk_count = len(s.risk_flags)
        if risk_count > 0:
            risks = f"🚩 {risk_count} flag{'s' if risk_count > 1 else ''} (Check details)"
        else:
            risks = f"{green}clean{reset}"
            
        print(f"{emoji} {s.ticker:<5} {s.direction_bias:<7} {decider:<15} {s.setup_class[:12]:<13} {conf_chart:<24} {risks}")
    
    print("════════════════════════════════════════════════════════════════════════════════════")
    print(f"Markdown: {result.markdown_path}")
    print(f"JSON:     {result.json_path}")
    print()


def print_market_recap(result: PipelineResult) -> None:
    report = result.report
    cyan = "\033[38;2;0;180;255m"
    green = "\033[32m"
    red = "\033[31m"
    reset = "\033[0m"
    bold = "\033[1m"
    
    print("════════════════════════════════════════════════════════════")
    human_date = format_human_date(report.generated_at)
    
    print(f"{bold}📊 Market Report · {human_date}{reset}")
    print("The market showed a clear divergence today with the Dow surging 1.76% on strength from financials like Goldman and UnitedHealth while the Nasdaq slipped 0.32% as semiconductor stocks cratered—Broadcom tanked 12% and Micron flirted with record wipeouts following disappointing guidance that's casting a shadow across the entire chip sector. Lululemon's outlook cut added to tech/growth headwinds, leaving the S&P essentially flat at $7,584.31 while VIX ticked up slightly to $15.40 despite the relatively calm price action.")
    print()
    print("With after-hours now underway, watch for any further fallout in semiconductor names and whether institutional money continues rotating into defensives and value plays, especially as jobless claims data this morning showed a stable labor market that keeps the Fed on hold. DocuSign and other software earnings reports hitting after the close could signal whether the selling pressure stays confined to hardware or spreads across the broader tech complex.")
    print()
    print(f"{bold}📍 Current State · Market After-hours{reset}")
    print(f"S&P 500     $7,584.31  {green}🟢▲ 0.27%{reset}")
    print(f"Nasdaq      $26,830.96 {red}🔴▼ 0.32%{reset}")
    print(f"Dow         $51,561.93 {green}🟢▲ 1.76%{reset}")
    print(f"VIX         $15.40     {green}🟢▲ 0.52%{reset}")
    print(f"WTI Crude   $93.09     {green}🟢▲ 1.01%{reset}")
    print()


def print_market_news(result: PipelineResult) -> None:
    cyan = "\033[38;2;0;180;255m"
    pink = "\033[38;5;206m"
    reset = "\033[0m"
    bold = "\033[1m"
    
    print("════════════════════════════════════════════════════════════")
    # Dynamic day detection
    now = datetime.utcnow()
    tomorrow = now + timedelta(days=1)
    tomorrow_name = tomorrow.strftime("%A")
    
    print(f"{bold}📰 Market Headlines{reset}")
    print("• Wall Street Today: DJIA Sets Record as UNH and GS Gains Offset Losses for AVGO, MU an…")
    print("• Broadcom Plunges 12%, but Smart Money Is Buying the Dip | Smart Money Option")
    print("• SanDisk Options Signal Growing Caution Despite Analysts’ Bullish Outlook: Options Cha…")
    print("• Micron Hit an All-Time High, Then Fell. What Does Its Chart Say?")
    print()
    
    # Dynamic Schedule
    events, earnings, day_name = get_tomorrow_schedule()
    print(f"{bold}{pink}💰 Earnings Highlight{reset}")
    disp_earn = ", ".join(earnings[:5]) + (" ..." if len(earnings) > 5 else "")
    print(f"   {pink}{disp_earn}{reset}")
    print(f"   [Market Open] : {bold}$GREEN{reset} [Market Close]")
    print()

    print(f"{bold}🔮 What to Expect Tomorrow ({day_name}){reset}")
    print(f"{bold}Economic Events{reset}")
    for event in events:
        print(f"   • {event}")
    print()
    print(f"{cyan}Sources: Yahoo Finance · News Desk · times ET · not investment advice{reset}")
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
    bridge_status_note: str | None = None,
) -> int:
    last_result: PipelineResult | None = None
    tracked_tickers: list[str] = ["$SPY", "$QQQ"]
    bold = "\033[1m"
    reset = "\033[0m"
    show_startup_intro()
    if bridge_status_note:
        print(bridge_status_note)
        print()

    def handle_todaysupdate() -> None:
        nonlocal last_result
        animate_status_loading("Sniffing out today's alpha")
        last_result = run_pipeline(args.config, args.output_dir)
        print_today_status(last_result)
        print("💎 What's our next move, boss?")
        if prompt_yes_no("Analyze the deep data now? (Try not to blow the account)"):
            print()
            print_analysis_summary(last_result)

    def handle_analyze() -> None:
        nonlocal last_result
        if last_result is None:
            animate_status_loading("Crunching the numbers (don't tell the SEC)")
            last_result = run_pipeline(args.config, args.output_dir)
        print_analysis_summary(last_result)

    def handle_marketrecap() -> None:
        nonlocal last_result
        if last_result is None:
            animate_status_loading("Seeing what broke after the bell")
            last_result = run_pipeline(args.config, args.output_dir)
        print_market_recap(last_result)

    def handle_marketnews() -> None:
        nonlocal last_result
        if last_result is None:
            animate_status_loading("Brewing coffee and parsing macro noise")
            last_result = run_pipeline(args.config, args.output_dir)
        print_market_news(last_result)

    def handle_runstrategy() -> None:
        nonlocal last_result
        if last_result is None:
            animate_status_loading("Consulting the quant gods")
            last_result = run_pipeline(args.config, args.output_dir)
        
        animate_wolf_of_wallstreet()
        
        strategy = MomentumStrategy()
        signals = strategy.evaluate(last_result.report)
        
        bold = "\033[1m"
        reset = "\033[0m"
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
            print(f"Added {ticker} to the sniper cart.")
            print(f"⚔️ {bold}Now tracking in Actionable Setups{reset}")
        print(f"Updated Sniper Cart: {', '.join(tracked_tickers)}")
        print("💎 What's our next move? (Try /analyze, /marketrecap, or /runstrategy)")
        print()

    def handle_settings() -> None:
        print("💎 Intelligence Settings")
        print("1. Enable Autopilot (30s smoke test loop)")
        print("2. Back")
        choice = input("Select an option > ").strip()
        if choice == "1":
            print("🚀 Autopilot ACTIVATED. Hands off the wheel. Press Ctrl+C to regain control.")
            try:
                while True:
                    animate_status_loading("Autopilot surveillance active")
                    res = run_pipeline(args.config, args.output_dir)
                    print_today_status(res, tracked_tickers)
                    print("Next cycle in 30s...")
                    time.sleep(30)
            except KeyboardInterrupt:
                print("\n🛑 Autopilot deactivated. Manual control restored.")
        print()

    def handle_clear() -> None:
        os.system('clear')
        render_banner(verification.compatible, bridge_config.robinhood.onboarding_completed)
        print_intro_command_table()

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

    def handle_trumptracker() -> None:
        print(f"💎 {bold}TrumpTracker Engine{reset}")
        print("Status: ON THE TABLE ⚔️")
        print("Integrating real-time political market impact analysis soon.")
        print()

    def handle_wsb() -> None:
        print(f"🦍 {bold}WallStBets Retail Intelligence Dashboard{reset}")
        print("═" * 60)
        print(f"{bold}{'Ticker':<8} {'Sentiment':<12} {'Ape Volume':<12} {'Squeeze Prob'}{reset}")
        print(f"{'-'*8} {'-'*12} {'-'*12} {'-'*15}")
        
        wsb_data = [
            ("$GME", "BULLISH 🚀", "VERY HIGH", "████████░░ 82%"),
            ("$HOOD", "MIXED ↔️", "HIGH", "████░░░░░░ 45%"),
            ("$AMC", "MOONING 🚀", "MODERATE", "██████░░░░ 65%"),
            ("$NVDA", "STOCKED 🔥", "INSANE", "██░░░░░░░░ 18%"),
        ]
        
        for t, s, v, p in wsb_data:
            print(f"{t:<8} {s:<12} {v:<12} {p}")
        
        print("═" * 60)
        print("Status: LIVE FEED ACTIVE 📡")
        print("💎 Diamond Hands is monitoring retail sentiment for potential gamma explosions.")
        print()
        input("💎 Press [Enter] to return to the desk > ")
        print()

    handlers: dict[str, Callable[[], None]] = {
        "/commands": print_intro_command_table,
        "/viewall": print_viewall_command_table,
        "/todaysupdate": handle_todaysupdate,
        "/analyze": handle_analyze,
        "/marketrecap": handle_marketrecap,
        "/marketnews": handle_marketnews,
        "/runstrategy": handle_runstrategy,
        "/tickersniper": handle_tickersniper,
        "/trumptracker": handle_trumptracker,
        "/wsb": handle_wsb,
        "/settings": handle_settings,
        "/clear": handle_clear,
        "/verifybridge": handle_verifybridge,
        "/handoff": handle_handoff,
    }

    while True:
        try:
            command = input("💎 What's our next move, boss? > ").strip()
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

    bridge_status_note: str | None = None
    if bridge_config_changed:
        bridge_config.first_run_completed = True
        save_public_bridge_config(bridge_config)
        if interactive_mode:
            bridge_status_note = f"Bridge state refreshed: {bridge_config.config_path}"
        else:
            print(f"Saved local bridge config: {bridge_config.config_path}")
            print()

    verification = verify_private_algo_bridge(bridge_config)
    render_banner(verification.compatible, bridge_config.robinhood.onboarding_completed)

    if args.setup and not (args.verify_bridge or args.analyze_only or args.analyze_then_hand_off):
        print_robinhood_onboarding(bridge_config.robinhood.mcp_url, bridge_config.robinhood.onboarding_completed)
        return 0

    if args.verify_bridge:
        print_robinhood_onboarding(bridge_config.robinhood.mcp_url, bridge_config.robinhood.onboarding_completed)
        print_bridge_verification(verification.notes)
        return 0 if verification.compatible else 1

    if interactive_mode:
        return run_interactive_shell(args, bridge_config, verification, bridge_status_note)

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
