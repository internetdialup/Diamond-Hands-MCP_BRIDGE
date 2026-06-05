# Diamond-Hands-MCP_BRIDGE

Public Robinhood-first bridge CLI for market intelligence and private connector handoff.

DMNDHNDS is not Financial Advice. Use at your own Risk. Don't end up being the exit liquidity. Paper trade your algos, back-test, use this to build and strengthen your alpha and MCP connectors.

## What This Repo does 

This repository is the public `Diamond Hands` bridge product. It reviews market structure, sentiment, flow, and setup quality, then writes artifacts that a user-owned private repo can consume.

It is not the final execution engine. This is only meant as a connector to your private repo's to build a stronger edge.

## Public and Private Split

- `Diamond-Hands-MCP_BRIDGE` is public and forkable.
- `Diamond-Hands-Algo` is private and execution-side.
- The public bridge helps users review the market, verify their setup, and hand off artifacts.
- The private repo owns proprietary filters, risk rules, and eventual Robinhood trade execution.

## Robinhood-First Workflow

The bridge is currently centered on Robinhood Agentic Trading and its MCP endpoint:

- `https://agent.robinhood.com/mcp/trading`

The public CLI explains the Robinhood onboarding path and then helps the user attach their own private ALGO repo.

## Quick Start

Install the editable package from the repo root:

```bash
python3 -m pip install --user -e .
```

Launch the CLI:

```bash
diamondhands
```

Not financial advice.

You can also use:

```bash
npm run diamondhands
```

If you need the direct Python legacy fallback:

```bash
PYTHONPATH=src python3 main.py
```

## Starter Commands

When the shell opens, type `/commands` to show the starter command list again.

Core commands:

```text
/commands      Show the command desk
/todaysupdate  Show today's market summary
/analyze       Show the full analysis report
/verifybridge  Check your private connector
/handoff       Send the latest artifact to Diamond-Hands-Algo
/quit          Exit the CLI
```

Extended commands stay available behind:

```text
/viewall
```

Use `/clear` to clear old CLI output without replaying the full startup screen.

Compatibility aliases:

```text
/help           -> /commands
/morecommands   -> /viewall
/today-status   -> /todaysupdate
/verify-bridge  -> /verifybridge
/hand-off       -> /handoff
quit            -> /quit
exit            -> /quit
```

## Typical Flow

1. Start the CLI with `diamondhands`.
2. Run `/todaysupdate` for the current market summary.
3. Run `/analyze` if you want the full report.
4. Run `/verifybridge` to check your private connector.
5. Run `/handoff` to send the latest artifact to your private repo.
6. Run `/liveboard`, `/memory`, `/risk`, or `/stop` to route into the private `trading-algo` engine when the private repo is connected.

Not financial advice.

## macOS Notes

On some Macs, `pip` is not available as a command even when `python3` is installed. Use `python3 -m pip` instead.

If `python3 -m pip install --user -e .` succeeds but `diamondhands` still says `command not found`, the installed script is likely not on your shell `PATH` yet. Add your user Python bin directory to `~/.zshrc`:

```bash
echo 'export PATH="$HOME/Library/Python/3.9/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

Useful direct modes:

```bash
diamondhands --setup
diamondhands --verify-bridge
diamondhands --analyze-only
diamondhands --analyze-then-hand-off
diamondhands boot
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

## ELI5

Imagine you have two robots working together to bake cookies:

1.  **The Recipe Robot (This Project):** This robot's only job is to look at the ingredients in the pantry (market data), read the cookbook (technical indicators), and figure out the perfect recipe for today. It writes the recipe down on a card and hands it off. It *never* touches the oven.
2.  **The Chef Robot (Your Private Repo):** This robot takes that recipe card, checks if it's safe (risk rules), and then actually puts the cookies in the oven (makes the trades on Robinhood).

By keeping the **Recipe Robot** public, you can share the analysis layer without exposing secrets or private execution rules.

## Key Docs

- `Documentation.md` for the bridge contract and product boundary
- `docs/robinhood-agentic-trading.md` for Robinhood MCP onboarding
- `docs/private-algo-bridge.md` for attaching the user’s private ALGO repo
- `docs/context-orientation.md` for the latest state of the bridge
- `scripts/learn_diamondhands_cli.py` for a commented demo of the CLI strings, animation, and command map
