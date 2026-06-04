#!/usr/bin/env python3
"""
Small teaching script for the Diamond Hands CLI.

Edit this file when you want to learn how banner strings, command labels,
and simple terminal animations are assembled without touching the production
CLI first.
"""

from __future__ import annotations

import sys
import time


# This list is the blue diamond banner. Each string is one printed row.
# If you want to reshape the diamond, edit the text below line by line.
BANNER_LINES = [
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
]


# This is the command desk the user sees when the CLI starts.
# Each tuple is: (slash command, short explanation).
COMMAND_ROWS = [
    ("/todaysupdate", "Show the market desk and top 10 events"),
    ("/analyze", "Run the full daily analysis"),
    ("/verifybridge", "Check private ALGO bridge compatibility"),
    ("/handoff", "Send the artifact to the private ALGO repo"),
    ("/quit", "Exit the DH CLI session"),
]


# Aliases let one command name map to another.
# Example: typing /today-status will be treated like /todaysupdate.
COMMAND_ALIASES = {
    "/today-status": "/todaysupdate",
    "/verify-bridge": "/verifybridge",
    "/hand-off": "/handoff",
    "/help": "/commands",
}


def cyan(text: str) -> str:
    """Apply the Diamond Hands cyan tone when running in a real terminal."""
    if not sys.stdout.isatty():
        return text
    return f"\033[38;2;0;180;255m{text}\033[0m"


def render_banner() -> None:
    """Print the diamond, title, and byline."""
    print()
    for line in BANNER_LINES:
        print(cyan(line))
    print(cyan("  DIAMOND HANDS"))
    print(cyan("    MCP BRIDGE"))
    print("      💎🤝")
    print(cyan("  by: internetdialup"))
    print()


def thinking_animation(label: str) -> None:
    """A tiny loading animation built from a few text frames."""
    frames = ["...", ".💎.", "..💎", "💎.."]
    if not sys.stdout.isatty():
        print(f"{label} ...")
        return

    for frame in frames:
        sys.stdout.write(f"\r{label} {frame}")
        sys.stdout.flush()
        time.sleep(0.12)
    sys.stdout.write("\r" + " " * (len(label) + 6) + "\r")
    sys.stdout.flush()


def print_command_table() -> None:
    """Print a simple terminal table from COMMAND_ROWS."""
    width = max(len(command) for command, _ in COMMAND_ROWS)
    print("Type /commands to reopen this desk.\n")
    print(f"{'Command'.ljust(width)}  Purpose")
    print(f"{'-' * width}  {'-' * 36}")
    for command, purpose in COMMAND_ROWS:
        print(f"{command.ljust(width)}  {purpose}")
        if sys.stdout.isatty():
            time.sleep(0.06)
    print()


def explain_aliases() -> None:
    """Show how compatibility aliases work."""
    print("Alias map:")
    for source, target in COMMAND_ALIASES.items():
        print(f"  {source} -> {target}")
    print()


def main() -> None:
    render_banner()
    thinking_animation("DH boot sequence")
    print_command_table()
    explain_aliases()
    print("Edit BANNER_LINES, COMMAND_ROWS, or COMMAND_ALIASES above to learn the CLI shape.")


if __name__ == "__main__":
    main()
