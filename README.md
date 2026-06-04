# Diamond-Hands-MCP_BRIDGE

Public Robinhood-first bridge CLI for market intelligence and private trading handoff. Welcome to the casino! Where everyone wins and loses! The first's one is free, but the house always wins. So, here's an MCP bridge to help you turn those Diamondhands into tangible liquidity. 💎🤝

## What This Repo does 

This repository is the public `Diamond Hands` bridge product. It analyzes market structure, sentiment, flow, and setup quality, then emits intelligence artifacts that a user-owned private ALGO repo can consume.

It is not the final execution engine. This is only meant as a connector to your private repo's to build a stronger edge. 

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

Run the public Diamond Hands bridge from this repo:

```bash
PYTHONPATH=src python3 main.py --config config/markets.example.yaml
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

## Key Docs

- `Documentation.md` for the bridge contract and product boundary
- `docs/robinhood-agentic-trading.md` for Robinhood MCP onboarding
- `docs/private-algo-bridge.md` for attaching the user’s private ALGO repo
- `docs/context-orientation.md` for the latest state of the bridge
