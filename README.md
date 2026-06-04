# Diamond-Hands-MCP_BRIDGE

Public Robinhood-first bridge CLI for market intelligence and private trading handoff.

## What This Repo Is

This repository is the public `Diamond Hands` bridge product. It analyzes market structure, sentiment, flow, and setup quality, then emits intelligence artifacts that a user-owned private ALGO repo can consume.

It is not the final execution engine.

## Product Split

- `Diamond-Hands-MCP_BRIDGE` is public and forkable.
- `Diamond-Hands-Algo` is private and execution-side.
- The public bridge helps users analyze, connect, and hand off.
- The private ALGO repo owns proprietary filters, hard risk rules, and eventual Robinhood trade execution.

## Robinhood-First Workflow

The bridge is currently centered on Robinhood Agentic Trading and its MCP endpoint:

- `https://agent.robinhood.com/mcp/trading`

The public CLI explains the Robinhood onboarding path and then helps the user attach their own private ALGO repo.

## Single Public CLI

Use the terminal CLI as the primary way to start Diamond Hands.

From the repo root, install the editable package with `python3 -m pip`:

```bash
python3 -m pip install --user -e .
```

Start the CLI:

```bash
diamondhands
```

This opens the interactive Diamond Hands shell in your terminal. The prompt is:

```text
diamond-hands>
```

### Terminal CLI Walkthrough

When the shell opens, you can type `/commands` at any time to reopen the command desk and see the available slash commands.

Primary interactive commands:

```text
/commands      Show the command desk
/todaysupdate  Show the market desk and top 10 events
/analyze       Run the full Diamond Hands daily analysis
/verifybridge  Check private ALGO bridge compatibility
/handoff       Send the current artifact to Diamond-Hands-Algo
/quit          Exit the DH CLI session
```

Supported aliases:

```text
/help           -> /commands
/today-status   -> /todaysupdate
/verify-bridge  -> /verifybridge
/hand-off       -> /handoff
quit            -> /quit
exit            -> /quit
```

### macOS Notes

On some Macs, `pip` is not available as a command even when `python3` is installed. Use `python3 -m pip` instead.

If `python3 -m pip install --user -e .` succeeds but `diamondhands` still says `command not found`, the installed script is likely not on your shell `PATH` yet. Add your user Python bin directory to `~/.zshrc`:

```bash
echo 'export PATH="$HOME/Library/Python/3.9/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

If you want one command that installs and launches the CLI from the repo, use:

```bash
./scripts/start_diamondhands.sh
```

Alternative entrypoints:

```bash
npm run diamondhands
```

Fallback dev entrypoint:

```bash
PYTHONPATH=src python3 main.py
```

Useful modes:

```bash
PYTHONPATH=src python3 main.py --setup
PYTHONPATH=src python3 main.py --verify-bridge
PYTHONPATH=src python3 main.py --analyze-only
PYTHONPATH=src python3 main.py --analyze-then-hand-off
```

The local bridge state is stored in `config/diamond-hands.local.yaml`, which is intentionally gitignored.

## What The Public Bridge Produces

- a Robinhood-first onboarding and bridge verification flow
- a branded market bridge report
- a machine-readable JSON artifact
- a downstream handoff contract compatible with the private ALGO bridge

## What Forked Users Need

Forking this repo is not enough for execution.

Users are expected to:

1. fork or clone this public bridge repo
2. create or attach their own private `Diamond-Hands-Algo` repo
3. connect their agent to Robinhood Agentic Trading
4. use the public bridge output as the input to their private execution stack

## TL;DR & ELI5 (The "Recipe Robot")

### TL;DR
This project is a **public market intelligence engine**. It analyzes market data and identifies trading setups, then packages its findings into a machine-readable artifact for a **private** repository to execute. It provides the analysis but never manages your money or keys.

### ELI5 (How it Works)
Imagine you have two robots working together to bake cookies:

1.  **The Recipe Robot (This Project):** This robot's only job is to look at the ingredients in the pantry (market data), read the cookbook (technical indicators), and figure out the perfect recipe for today. It writes the recipe down on a card and hands it off. It *never* touches the oven.
2.  **The Chef Robot (Your Private Repo):** This robot takes that recipe card, checks if it's safe (risk rules), and then actually puts the cookies in the oven (makes the trades on Robinhood).

By keeping the **Recipe Robot** public, you can share the "math" with the community without ever risking your secret passwords or personal money rules.

## Key Docs

- `Documentation.md` for the bridge contract and product boundary
- `docs/robinhood-agentic-trading.md` for Robinhood MCP onboarding
- `docs/private-algo-bridge.md` for attaching the user’s private ALGO repo
- `docs/context-orientation.md` for the latest state of the bridge
- `scripts/learn_diamondhands_cli.py` for a commented demo of the CLI strings, animation, and command map
