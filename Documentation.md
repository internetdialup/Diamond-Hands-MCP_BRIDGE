# Documentation.md

The local operating spec for `Diamond-Hands-MCP_BRIDGE`.

This repository is the public market-intelligence and onboarding bridge for a Robinhood-first trading workflow. It analyzes market data and emits handoff artifacts, but it does not own proprietary execution logic or broker credentials.

## Purpose

Use this repo for:

- public market research and signal analysis
- branded CLI onboarding for Robinhood Agentic Trading
- bridge verification to a user-owned private ALGO repo
- adherence to the **Bamboo Framework** for context management (see [BAMBOO.md](BAMBOO.md))
- public strategy logic and report generation
- machine-readable handoff artifacts for downstream private execution systems

Do not use this repo for:

- proprietary execution transforms
- broker secrets or credentials
- private risk overrides
- final live trade execution

Those concerns belong in the private `Diamond-Hands-Algo` repo.

## Required Repo Contract

This repo should always keep:

- `README.md` for product identity and the public/private split
- `AGENT.md` for cold-start routing
- `Documentation.md` for bridge doctrine and repo boundaries
- `docs/context-orientation.md` for current state and recent changes
- `docs/robinhood-agentic-trading.md` for Robinhood MCP onboarding
- `docs/private-algo-bridge.md` for attaching the private ALGO repo

## Document Roles

- `Documentation.md`: public bridge rules and product boundary
- `README.md`: human-facing overview of Diamond Hands
- `AGENT.md`: short route into the bridge docs and runtime
- `docs/context-orientation.md`: newest-first state log
- `docs/robinhood-agentic-trading.md`: Robinhood-first onboarding instructions
- `docs/private-algo-bridge.md`: how forks attach a private ALGO repo
- `docs/research-standards.md`: public research and experiment standards

## Working Folders

- `src/`: public bridge runtime and analysis stack
- `config/`: public analysis config plus local bridge config shape
- `research/`: public studies and analysis artifacts
- `tests/`: validation for analysis, bridge setup, and handoff compatibility
- `data/`: local non-secret datasets and storage conventions

The current implementation uses these internal modules inside `src/trading_system/`:

- `data/`: provider-agnostic market snapshot schemas and adapters
- `features/`: regime, technical, sentiment, and flow feature builders
- `models/`: setup classification and confidence fusion
- `pipeline/`: public analysis and report generation
- `contracts/`: typed public handoff payloads
- `backtesting/`: initial labeling and walk-forward scaffolding
- `bridge_config.py` and `bridge_runtime.py`: public-to-private bridge setup and handoff logic

## Mandatory Rules

- Treat this repo as the single public CLI surface.
- Keep Robinhood Agentic Trading as the first-class onboarding path in the current product.
- Explain clearly that execution requires a user-owned private ALGO repo.
- Keep the public handoff contract compatible with the private ALGO mirrored schema unless a deliberate contract migration is performed.
- Do not store broker secrets, private thresholds, or proprietary execution doctrine here.
- Keep user-facing product naming on the Diamond Hands brand even while local repo and package names remain temporarily unchanged.

## Current CLI

Run the public bridge with:

```bash
diamondhands
```

Bridge-specific modes:

```bash
diamondhands --setup
diamondhands --verify-bridge
diamondhands --analyze-only
diamondhands --analyze-then-hand-off
diamondhands boot
```

The local bridge state is persisted in `config/diamond-hands.local.yaml` and is not committed.

Use `PYTHONPATH=src python3 main.py ...` only as a legacy local fallback when the editable package entrypoint is unavailable.
