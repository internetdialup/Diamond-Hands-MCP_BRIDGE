# Private ALGO Bridge

Forks of `Diamond-Hands-MCP_BRIDGE` are expected to create or attach a private `Diamond-Hands-Algo` repo.

## Default Local Shape

```text
Git/
├── Trading-MCP-Analyzer
└── Trading-MCP-Algo
```

The public bridge keeps the local folder names for now, but the product identity is:

- public: `Diamond-Hands-MCP_BRIDGE`
- private: `Diamond-Hands-Algo`

## What The Public Bridge Stores

The local bridge state is persisted in:

- `config/diamond-hands.local.yaml`

It records:

- private ALGO repo path
- private bridge config path
- expected preview artifact path
- Robinhood MCP onboarding status
- first-run completion status

## Verification Rules

The public bridge checks:

- whether the private ALGO repo exists
- whether `main.py` exists in that repo
- whether the private bridge config exists
- whether the public handoff path can be used for the private bridge

## Handoff Rule

The public bridge may generate the analysis artifact and then invoke the private ALGO CLI with the fresh JSON artifact path, but the private repo remains the owner of strict risk gating and eventual execution.
