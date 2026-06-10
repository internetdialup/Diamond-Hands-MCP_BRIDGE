from __future__ import annotations
import sys
import time
import random
import re
import subprocess
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from trading_system.pipeline.daily import PipelineResult
    from trading_system.contracts.types import DailyReportContract, SymbolReport
    from trading_system.cli import PersonaManager, CommandSpec

def strip_ansi(text: str) -> str:
    return re.sub(r'\033\[[0-9;]*m', '', text)

def mask_ticker(ticker: str) -> str:
    """Masks ticker symbols for public logs (e.g. SPY -> S**)."""
    if len(ticker) <= 1: return ticker
    return ticker[0] + "*" * (len(ticker) - 1)

def get_wallstreet_time() -> str:
    utc_now = datetime.utcnow()
    edt_now = utc_now - timedelta(hours=4)
    return edt_now.strftime("%-I:%M:%S %p EST")

def format_human_date(iso_string: str) -> str:
    try:
        clean_iso = iso_string.replace("Z", "+00:00")
        dt = datetime.fromisoformat(clean_iso)
        return dt.strftime("%b %d, %Y, %-I%p")
    except Exception:
        return iso_string

def is_market_holiday(dt: datetime) -> bool:
    holidays = {(1, 1), (7, 4), (12, 25)}
    return (dt.month, dt.day) in holidays

def cyan_gradient(text: str) -> str:
    if not sys.stdout.isatty(): return text
    out = ""
    steps = max(1, len(text) - 1)
    for i, char in enumerate(text):
        # Nightshade Spec: Green 180->255, Blue 255->180
        g = min(255, int(180 + (75 * (i / steps))))
        b = max(180, int(255 - (75 * (i / steps))))
        out += f"\033[38;2;0;{g};{b}m{char}"
    return out + "\033[0m"

def create_barchart(value: float, max_val: float = 1.0, width: int = 10) -> str:
    if not sys.stdout.isatty(): return f"{value:.2f}"
    filled = max(0, min(width, int((value / max_val) * width)))
    empty = width - filled
    color = "\033[32m" if value >= 0.7 else "\033[33m" if value >= 0.4 else "\033[31m"
    return f"{color}{'█' * filled}\033[0m\033[90m{'░' * empty}\033[0m"

def get_tomorrow_schedule() -> tuple[list[str], list[str], str]:
    now = datetime.utcnow()
    tomorrow = now + timedelta(days=1)
    day_name = tomorrow.strftime("%A")
    events = ["Consumer Sentiment"] if day_name == "Friday" else ["Market Prep"]
    earnings = ["$TSLA"] if day_name == "Monday" else ["none"]
    return events, earnings, day_name

def play_alert(message: str) -> None:
    if sys.platform == "darwin":
        try: subprocess.run(["say", "-v", "Samantha", message], check=False)
        except Exception: pass

def animate_status_loading(message: str, duration: float = 1.0, voice: bool = False) -> None:
    if voice:
        play_alert(message)
    if not sys.stdout.isatty():
        print(f"💎 {message}...")
        return
    chars = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
    bold, reset, cyan, green = "\033[1m", "\033[0m", "\033[36m", "\033[32m"
    end_time = time.time() + duration
    i = 0
    while time.time() < end_time:
        sys.stdout.write(f"\r  {cyan}{chars[i % len(chars)]}{reset} {bold}{message}...{reset}")
        sys.stdout.flush()
        time.sleep(0.08)
        i += 1
    sys.stdout.write(f"\r  {green}✅{reset} {bold}{message} done.{reset}\n")
    sys.stdout.flush()

def get_heartbeat_frame() -> str:
    """Returns a pulsing frame for the CLI heartbeat."""
    frames = ["❤️ ", "💖", "💗", "💓", "💞"]
    return frames[int(time.time() * 2) % len(frames)]

def render_error_badge(error: dict) -> str:
    """Renders a beautiful status badge for structured errors (MIT pattern)."""
    red, yellow, reset, bold = "\033[31m", "\033[33m", "\033[0m", "\033[1m"
    code = error.get("code", "UNKNOWN")
    msg = error.get("message", "")
    
    if "THROTTLED" in code or "RATE" in code:
        return f"{yellow}[🚦 API THROTTLED]{reset} {msg}"
    if "HUNG_UP" in code or "OFFLINE" in code:
        return f"{red}[👻 BRIDGE OFFLINE]{reset} {msg}"
    return f"{red}[🛑 ERROR: {code}]{reset} {msg}"

def render_confluence_matrix(data: dict) -> None:
    """Renders a high-fidelity Timeframe Confluence Matrix (MIT pattern)."""
    green, yellow, red, grey, reset, bold = "\033[32m", "\033[33m", "\033[31m", "\033[90m", "\033[0m", "\033[1m"
    tframes = data.get("timeframes", ["1m", "5m", "15m", "1h", "4h", "1D", "1W"])
    indicators = data.get("indicators", ["RSI", "MACD", "EMA", "SUPER"])
    matrix = data.get("matrix", {}) # { "Indicator": { "1m": "BUY", ... } }
    
    print(f"  {bold}Timeframe Confluence Matrix:{reset}")
    header = f"{'Indicator':<12} │ " + " │ ".join([f"{tf:<5}" for tf in tframes])
    print(f"  {grey}{header}{reset}")
    print(f"  {grey}{'─' * len(header)}{reset}")
    
    for ind in indicators:
        row = f"  {bold}{ind:<12}{reset} │ "
        scores = []
        for tf in tframes:
            val = matrix.get(ind, {}).get(tf, "WAIT")
            color = green if "BUY" in val else red if "SELL" in val else yellow
            scores.append(f"{color}{val:<5}{reset}")
        print(row + " │ ".join(scores))
    print()

from trading_system import MOTD

def render_banner(connected: bool | None = None, rh_connected: bool | None = None, animate: bool = True, persona: PersonaManager | None = None) -> None:
    if persona and persona.banner_renderer:
        try: persona.banner_renderer(); return
        except Exception: pass
    
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
    
    banner_block = MOTD.BANNER_BLOCK
    subtitle = MOTD.SUBTITLE
    emoji_line, byline = MOTD.EMOJI_LINE, MOTD.BYLINE
    divider = MOTD.DIVIDER
    tagline = MOTD.TAGLINE
    manager_tag = f"  {bold}{green}{MOTD.MANAGER_TAG_RAW}{reset}"
    disclaimer = f"  {yellow}{MOTD.DISCLAIMER_RAW}{reset}"
    if connected is True: status_dot = f"\033[32;5m●\033[0m {green}connected to your private ALGO repo{reset}"
    elif connected is False: status_dot = f"\033[31;5m●\033[0m {red}disconnected from private ALGO repo{reset}"
    else: status_dot = f"\033[33;5m●\033[0m connecting to private ALGO repo..."
    if rh_connected is True: rh_status = f"{green}🍃 connected to Robinhood MCP Bridge{reset}"
    elif rh_connected is False: rh_status = f"{red}🍂 disconnected from Robinhood MCP Bridge{reset}"
    else: rh_status = f"{yellow}🍃 connecting to Robinhood MCP Bridge...{reset}"
    from trading_system import __version__
    ver_status = f"  {cyan}📦 version: v{__version__}{reset}"
    print()
    if animate and sys.stdout.isatty():
        for line in banner_block:
            print(cyan_gradient(line))
            sys.stdout.write("\a"); sys.stdout.flush(); time.sleep(0.06)
    else:
        for line in banner_block: print(cyan_gradient(line))
    print(f"\n{bold}{cyan_gradient(subtitle)}{reset}\n{cyan_bright}{divider}{reset}\n{emoji_line}\n{cyan}{byline}{reset}\n\n{tagline}\n{manager_tag}\n{disclaimer}\n  {status_dot}\n  {rh_status}\n{ver_status}\n")

def render_command_table(command_specs: list[CommandSpec], title: str) -> list[str]:
    bold, reset = "\033[1m", "\033[0m"
    w = max(len(spec.command) for spec in command_specs)
    lines = [f"{bold}{title}{reset}", f"{'Command'.ljust(w)}  Purpose", f"{'-' * w}  {'-' * 38}"]
    for spec in command_specs: lines.append(f"{spec.command.ljust(w)}  {spec.purpose}")
    return lines

def print_intro_command_table(connected: bool = False, core_specs: list[CommandSpec] = None, private_specs: list[CommandSpec] = None) -> None:
    bold, reset = "\033[1m", "\033[0m"
    print("════════════════════════════════════════════════════════════")
    print(f"{bold}Welcome back. Type /commands to see our core arsenal.{reset}\n")
    lines = render_command_table(core_specs or [], "Diamond Hands Core Commands")
    private_lines = render_command_table(private_specs or [], "Private Safe Ops")
    for line in lines: print(line)
    if connected:
        print()
        for line in private_lines: print(line)
    print()

def print_viewall_command_table(core_specs: list[CommandSpec], private_specs: list[CommandSpec], experimental_specs: list[CommandSpec]) -> None:
    bold, reset = "\033[1m", "\033[0m"
    print("════════════════════════════════════════════════════════════")
    print(f"{bold}Full Diamond Hands Suite{reset}\n")
    all_specs = core_specs + private_specs + experimental_specs
    lines = render_command_table(all_specs, "Extended Intelligence Commands")
    for line in lines: print(line)
    print()

def print_robinhood_onboarding(mcp_url: str, completed: bool) -> None:
    print(f"Robinhood Agentic Trading\n- MCP URL: {mcp_url}\n- Codex CLI: codex mcp add robinhood-trading --url {mcp_url}\n- Codex app: Settings -> MCP servers -> Streamable HTTP -> add the MCP URL\n- Robinhood uses a dedicated agentic trading account with activity monitoring and a kill switch.\n- Onboarding recorded: {'yes' if completed else 'no'}\n")

def print_bridge_verification(notes: list[str]) -> None:
    print("Private Bridge Verification")
    for note in notes: print(f"- {note}")
    print()

def print_premarket_brief(report: DailyReportContract) -> None:
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
    
    spy_report = next((s for s in report.symbols if s.ticker == "SPY"), None)
    if not spy_report: return
    sent = spy_report.sentiment.score if spy_report.sentiment else 0
    flow = spy_report.flow.dealer_positioning if spy_report.flow else "neutral"
    wallstreet_now = datetime.utcnow() - timedelta(hours=4)
    week_num = wallstreet_now.isocalendar()[1]
    date_str = wallstreet_now.strftime("%b %d, %Y")
    hour = wallstreet_now.hour
    time_phrase = "Morning" if hour < 12 else "Midday" if hour < 14 else "End of day" if hour < 16 else "After-hours"
    halt_triggered = report.market_regime.name == "Freefall" or "circuit_breaker" in spy_report.risk_flags
    if halt_triggered: brief = f"{red}🚨 CIRCUIT BREAKER FLIPPED. Market is HALTED.{reset}"
    elif is_market_holiday(wallstreet_now): brief = f"{yellow}Markets are closed for the holiday Boss. Go enjoy your life. 🌴🌤️{reset}"
    elif wallstreet_now.weekday() == 5 or (wallstreet_now.weekday() == 6 and wallstreet_now.hour < 18):
        brief = f"{yellow}It's the weekend Boss. Touch grass, the market is closed. 🌴🌤️{reset}"
    elif report.market_regime.score <= -0.1 or sent < -0.1:
        suffix = "Positioning for tomorrow's open Boss" if time_phrase == "After-hours" else "Watch your stops Boss"
        brief = f"{red}{time_phrase} is looking RED. Dealers are {flow} and sentiment is dumping. {suffix}.{reset}"
    elif report.market_regime.score >= 0.3 and sent > 0.1:
        suffix = "Setting up for tomorrow Boss" if time_phrase == "After-hours" else "Ride the wave Boss"
        brief = f"{green}{time_phrase} looks GREEN. Momentum is strong and dealers are {flow}. {suffix}.{reset}"
    else:
        suffix = "Watch the gaps Boss" if time_phrase == "After-hours" else "Stay picky Boss"
        brief = f"{yellow}{time_phrase} is looking MIXED. Market is rangebound. {suffix}.{reset}"
    print(f"{grey}║{reset}  {bold}📅 Week {week_num} ({date_str}){reset}{' ' * (80 - len(strip_ansi(f'📅 Week {week_num} ({date_str})')))} {grey}║{reset}")
    print(f"{grey}╟──────────────────────────────────────────────────────────────────────────────────╢{reset}")
    words = brief.split(' ')
    current_row = ""
    for word in words:
        potential_row = (current_row + " " + word).strip()
        if len(strip_ansi(potential_row)) <= 80: current_row = potential_row
        else:
            print(f"{grey}║{reset}  {current_row}{' ' * (80 - len(strip_ansi(current_row)))} {grey}║{reset}")
            current_row = word
    print(f"{grey}║{reset}  {current_row}{' ' * (80 - len(strip_ansi(current_row)))} {grey}║{reset}")
    print(f"{grey}╟──────────────────────────────────────────────────────────────────────────────────╢{reset}")

def print_today_status(result: PipelineResult, tracked_tickers: list[str] = None, persona: PersonaManager | None = None) -> None:
    report = result.report
    # Nightshade Visual Spec
    bold = "\033[1m"
    reset = "\033[0m"
    cyan_bright = "\033[38;2;140;225;255m"
    cyan = "\033[38;2;0;180;255m"
    green = "\033[32m"
    red = "\033[31m"
    yellow = "\033[33m"
    grey = "\033[90m"
    pink = "\033[38;5;206m"
    
    wallstreet_time = get_wallstreet_time()
    f_color = red if report.market_regime.score < 0 else green
    v_color = green if report.market_regime.score < 0 else red
    f_sign, v_sign = ("" if report.market_regime.score < 0 else "+"), ("+" if report.market_regime.score < 0 else "-")
    futures_line = f"/NQ {f_color}{f_sign}-0.4%{reset} | VIX {v_color}{v_sign}2.1%{reset} | NIKKEI {f_color}{f_sign}-1.1%{reset}"
    print(f"{grey}╔══════════════════════════════════════════════════════════════════════════════════╗{reset}")
    print(f"{grey}║{reset}  {bold}{cyan_gradient('DIAMOND HANDS COMMAND CENTER')} {reset} {grey}║{reset} {bold}{wallstreet_time}{reset} {grey}║{reset}")
    print(f"{grey}╠══════════════════════════════════════════════════════════════════════════════════╣{reset}")
    
    # --- Motive Force & Trend Alignment (v0.17.22) ---
    motive = report.market_regime.drivers[0] if report.market_regime.drivers else "Neutral"
    trend_val = report.market_regime.score # Use score as proxy for trend alignment
    trend_aligned = abs(trend_val) > 0.5
    trend_color = green if trend_aligned else yellow
    trend_text = "ALIGNED" if trend_aligned else "CONVERGING"
    
    print(f"{grey}║{reset}  {bold}Regime:{reset} {report.market_regime.name:<12} ({report.market_regime.score:>+5.2f})  {grey}│{reset} {bold}Futures:{reset} {futures_line:<25} {grey}║{reset}")
    print(f"{grey}║{reset}  {bold}Force :{reset} {cyan}{motive:<12}{reset}           {grey}│{reset} {bold}Trend  :{reset} {trend_color}{trend_text:<25}{reset} {grey}║{reset}")
    
    spy_open, spy_prev_close, spy_live = 740.49, 733.22, 735.12 + (random.random() * 2 - 1)
    print(f"{grey}║{reset}  {bold}Benchmark:{reset} {bold}{yellow}$SPY{reset} - ${spy_open:.2f} Opening, ${spy_prev_close:.2f} Closing {grey}│{reset} {bold}Live:{reset} {green}${spy_live:.2f}{reset}  {grey}║{reset}")
    
    # --- Miller's Bootcamp: Training Pulse (v0.17.18) ---
    if persona and persona.repo_path:
        import json as _json
        hb_path = persona.repo_path / "outputs" / "status" / "training_heartbeat.json"
        if hb_path.exists():
            try:
                with hb_path.open("r") as f:
                    hb = _json.load(f)
                p_name = hb.get("persona", "Agent")
                state = hb.get("state", "IDLE")
                count = hb.get("permutation_count", 0)
                drill = hb.get("current_drill", "Standard Drill")
                
                # --- Security: Scrub Private Terms (v0.1.7) ---
                drill = drill.replace("UMADA", "[REDACTED]")
                
                if state == "TRAINING":
                    pulse = f"{bold}{pink}● {state}{reset} | {bold}{p_name}:{reset} {drill} (#{count})"
                    padding = 80 - len(strip_ansi(pulse))
                    print(f"{grey}║{reset}  {pulse}{' ' * max(0, padding)} {grey}║{reset}")
            except: pass

    print(f"{grey}╠══════════════════════════════════════════════════════════════════════════════════╣{reset}")
    print_premarket_brief(report)
    if persona and persona.repo_path:
        alpha = persona.get_institutional_alpha()
        if alpha:
            # --- Security: Scrub Private Terms ---
            headline = alpha.get('headline', '')[:52].replace("UMADA", "[REDACTED]")
            alpha_head = f"{bold}🕵️ Institutional Alpha:{reset} {headline}"
            padding = 80 - len(strip_ansi(alpha_head))
            print(f"{grey}║{reset}  {alpha_head}{' ' * max(0, padding)} {grey}║{reset}")
            print(f"{grey}╟──────────────────────────────────────────────────────────────────────────────────╢{reset}")
    print(f"{grey}║{reset}  {bold}{cyan}🚀 MARKET SNAPSHOT{reset}{' ':<63} {grey}║{reset}")
    print(f"{grey}║{reset}  {bold}{'TICKER':<10} {'PRICE':<10} {'CHG %':<10} {'BIAS':<10} {'CONVICTION':<18} {'SETUP'}{reset}  {grey}║{reset}")
    print(f"{grey}║{reset}  {grey}{'-'*10} {'-'*10} {'-'*10} {'-'*10} {'-'*18} {'-'*15}{reset}  {grey}║{reset}")
    base_symbols = sorted(report.symbols, key=lambda s: s.confidence, reverse=True)
    setup_list, seen = [], set()
    if tracked_tickers:
        for t in tracked_tickers:
            t_clean = t.replace("$", "")
            match = next((s for s in report.symbols if s.ticker == t_clean), None)
            if match: setup_list.append(match); seen.add(t_clean)
    for s in base_symbols:
        if s.ticker not in seen: setup_list.append(s); seen.add(s.ticker)
        if len(setup_list) >= 4: break
    for s in setup_list:
        bias = s.direction_bias.lower()
        bias_color = green if bias == "bullish" else red if bias == "bearish" else yellow
        # --- Security Obfuscation (v0.17.19) ---
        display_ticker = s.ticker if s.ticker in ["SPY", "QQQ", "IWM", "VIX"] else mask_ticker(s.ticker)
        
        price, chg = ("735.12" if s.ticker == "SPY" else "224.12" if s.ticker == "QQQ" else "124.50"), ("+0.12%" if bias == "bullish" else "-0.45%" if bias == "bearish" else "+0.00%")
        chg_color = green if "+" in chg else red if "-" in chg else yellow
        conf_chart = create_barchart(s.confidence, width=15)
        row_content = f"{display_ticker:<10} {price:<10} {chg_color}{chg:<10}{reset} {bias_color}{s.direction_bias.upper():<10}{reset} {conf_chart} ({int(s.confidence*100):>2}%) {s.setup_class[:14]:<14}"
        # Force static length 80
        padding = 80 - len(strip_ansi(row_content))
        print(f"{grey}║{reset}  {row_content}{' ' * max(0, padding)} {grey}║{reset}")
    print(f"{grey}╟──────────────────────────────────────────────────────────────────────────────────╢{reset}")
    print(f"{grey}║{reset}  {bold}{green}📰 MACRO CATALYSTS{reset}{' ':<61} {grey}║{reset}")
    
    # --- Deduplicate News Symbols ---
    news_seen = set()
    news_count = 0
    for news in report.top_12_news:
        if news_count >= 5: break
        if news.topic in news_seen: continue
        news_seen.add(news.topic)
        news_count += 1
        
        topic, summary = news.topic[:8], news.summary[:65] if len(news.summary) <= 65 else news.summary[:62] + "..."
        line = f" • {bold}{topic:<8}{reset} │ {summary}"
        padding = 80 - len(strip_ansi(line))
        print(f"{grey}║{reset}  {line}{' ' * max(0, padding)} {grey}║{reset}")
        
    events, earnings, day_name = get_tomorrow_schedule()
    print(f"{grey}║{reset}{' ':<82}{grey}║{reset}")
    print(f"{grey}║{reset}  {bold}{pink}📅 EXPECTED TOMORROW ({day_name.upper()}){reset}{' ' * (80 - len(strip_ansi(f'📅 EXPECTED TOMORROW ({day_name.upper()})')))} {grey}║{reset}")
    
    # --- Refine ECONOMY Lane (Phase 16.C logic) ---
    econ_line = f" • {bold}ECONOMY {reset} │ {', '.join(events)[:65]}"
    padding = 80 - len(strip_ansi(econ_line))
    print(f"{grey}║{reset}  {econ_line}{' ' * max(0, padding)} {grey}║{reset}")
    
    if earnings and earnings[0].lower() != "none":
        disp_earn = ", ".join(earnings[:5]) + (" …" if len(earnings) > 5 else "")
        earn_line = f" • {bold}EARN    {reset} │ {disp_earn[:65]}"
        padding = 80 - len(strip_ansi(earn_line))
        print(f"{grey}║{reset}  {earn_line}{' ' * max(0, padding)} {grey}║{reset}")
    else:
        # Static row for zero earnings
        none_line = f" • {bold}EARN    {reset} │ none"
        padding = 80 - len(strip_ansi(none_line))
        print(f"{grey}║{reset}  {none_line}{' ' * max(0, padding)} {grey}║{reset}")
        
    print(f"{grey}╚══════════════════════════════════════════════════════════════════════════════════╝{reset}\n")

def print_analysis_summary(result: PipelineResult, target_symbol: str | None = None, persona: PersonaManager | None = None) -> None:
    report = result.report
    # Nightshade Visual Spec
    bold = "\033[1m"
    reset = "\033[0m"
    cyan_bright = "\033[38;2;140;225;255m"
    cyan = "\033[38;2;0;180;255m"
    green = "\033[32m"
    red = "\033[31m"
    yellow = "\033[33m"
    grey = "\033[90m"
    pink = "\033[38;5;206m"
    
    top_symbol = next((s for s in report.symbols if s.ticker == target_symbol.replace("$","").upper()), None) if target_symbol else sorted(report.symbols, key=lambda s: s.confidence, reverse=True)[0]
    if not top_symbol: top_symbol = sorted(report.symbols, key=lambda s: s.confidence, reverse=True)[0]
    print(f"════════════════════════════════════════════════════════════════════════════════════\n  {bold}{cyan_gradient(f'💎 DEEP ANALYSIS: {top_symbol.ticker}')}{reset}\n  Regime: {report.market_regime.name:<15} │ Confidence: {int(top_symbol.confidence*100)}%\n  Setup : {top_symbol.setup_class:<15} │ Posture   : {top_symbol.technical_posture}\n  ──────────────────────────────────────────────────────────────────────────────────")
    flow = top_symbol.flow
    gamma, vanna, delta = (flow.gamma_exposure if flow else 0.0), (flow.vanna if flow else 0.0), (flow.delta if flow else 0.5)
    def greek_bar(val: float) -> str:
        width = 12
        filled = max(0, min(width, int(((val + 1) / 2) * width)))
        return f"{green if val > 0.2 else red if val < -0.2 else yellow}{'█' * filled}{'░' * (width - filled)}{reset}"
    flow_raw = top_symbol.flow.dealer_positioning if top_symbol.flow else "neutral"
    print(f"  {bold}├────────────────────────────────── GREEK LEVELS ──────────────────────────────────┤{reset}\n  │ {bold}Gamma EX{reset}   │ {greek_bar(gamma)} ({gamma:>+5.2f}) │ {bold}Delta EX{reset}   │ {greek_bar(delta)} ({delta:>+5.2f}) │\n  │ {bold}Vanna EX{reset}   │ {greek_bar(vanna)} ({vanna:>+5.2f}) │ {bold}Dealer Bias{reset}│ {green if flow_raw == 'long_gamma' else red if flow_raw == 'short_gamma' else yellow}{flow_raw.upper():<15}{reset}   │\n  {bold}└──────────────────────────────────────────────────────────────────────────────────┘{reset}")
    
    # --- Reasoning Integrity Meter (v0.17.23) ---
    if persona:
        debate = persona.get_debate_transcript(top_symbol.ticker)
        if debate and "monroe_payload" in debate:
            m = debate["monroe_payload"]
            sfv = m.get("sfv_score", 0.0)
            csct = m.get("csct_score", 0.0)
            cascade = m.get("cascade_prob", 0.0)
            
            c_color = red if cascade > 0.55 else green
            
            print(f"  {bold}├────────────────────────────── REASONING INTEGRITY ──────────────────────────────┤{reset}")
            print(f"  │ {bold}Fact Verifier{reset}  │ {create_barchart(sfv)} ({sfv*100:>3.0f}%) │ {bold}Cascade Prob{reset} │ {c_color}{cascade*100:>3.0f}%{reset} {'[HALT]' if cascade > 0.55 else '[SAFE]'}  │")
            print(f"  │ {bold}Consistency{reset}    │ {create_barchart(csct)} ({csct*100:>3.0f}%) │ {bold}Audit Result{reset} │ {green if sfv > 0.8 else yellow}{'VERIFIED' if sfv > 0.8 else 'SUSPECT':<15}{reset}   │")
            print(f"  {bold}└──────────────────────────────────────────────────────────────────────────────────┘{reset}")

    # 🕵️ DYNAMIC INTELLIGENCE WRAPPERS (v0.15.0 protocol)
    # Allows the private repo to inject any number of agent summaries without hardcoding.
    if persona:
        wrappers = persona.get_intel_module("wrappers", ticker=top_symbol.ticker)
        if wrappers and isinstance(wrappers, list):
            for w in wrappers:
                title = w.get("title", "INTELLIGENCE")
                content = w.get("content", "No data.")
                color = w.get("color", cyan)
                icon = w.get("icon", "🕵️")
                
                # --- Motive Force Leader Highlighting (v0.17.23) ---
                is_leader = "motive leader" in title.lower() or "leader" in content.lower()
                row_bold = bold if is_leader else ""
                row_bg = "\033[44m" if is_leader else "" # Blue background for leader
                
                print(f"  {row_bold}{color}{icon} {title.upper()}:{reset}")
                print(f"  {row_bg}{content}{reset}")
                print(f"{'─' * 84}")
        else:
            print(f"  {grey}Intelligence Team: No specific narrative context for this ticker.{reset}")
            print(f"{'─' * 84}")
    
    print(f"{'═' * 84}\n")

def print_market_recap(result: PipelineResult, persona: PersonaManager | None = None) -> None:
    report = result.report
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

    print(f"════════════════════════════════════════════════════════════════════════════════════\n🌆 {bold}Market Post-Mortem: {report.generated_at}{reset}\n{'═' * 80}")

    for s in report.symbols[:5]:
        bias = s.direction_bias.lower()
        print(f" • {bold}{s.ticker:<5}{reset} │ {green if bias == 'bullish' else red if bias == 'bearish' else yellow}{bias.upper():<10}{reset} │ Confidence: {int(s.confidence*100)}%")
    print(f"{'─' * 60}\nRegime: {report.market_regime.name}")
    
    # --- Verbatim Ledger: Perfect Snipe / Got Smoked (v0.17.18) ---
    if persona:
        ledger = persona.get_verbatim_ledger()
        if ledger:
            print(f"\n{bold}📜 Verbatim Execution Ledger:{reset}")
            for entry in ledger[-5:]: # Show last 5
                time_str = entry[:5]
                text = entry[6:]
                color = green if "Perfect Snipe" in text else red if "Smoked" in text else reset
                print(f"  {grey}{time_str}{reset} {color}{text}{reset}")
    
    print()
