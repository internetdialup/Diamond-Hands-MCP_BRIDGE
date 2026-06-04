# Robinhood Agentic Trading

The current public Diamond Hands bridge is Robinhood-first.

## MCP Endpoint

- `https://agent.robinhood.com/mcp/trading`

## Current Connection Notes

Robinhood’s public setup instructions currently point users to connect the MCP server from their agent surface. For Codex CLI, the displayed command is:

```bash
codex mcp add robinhood-trading --url https://agent.robinhood.com/mcp/trading
```

Robinhood also surfaces MCP connection paths for Codex, Claude, Cursor, ChatGPT, and other agent environments that support Streamable HTTP or MCP server setup.

## Product Model

Robinhood Agentic Trading currently uses a dedicated agentic trading account rather than the user’s main portfolio account. Robinhood’s published materials also emphasize:

- activity monitoring
- push notifications
- a separate blast-radius-limited account
- the ability to disconnect or pause the agent

## What Diamond Hands Does

The public Diamond Hands bridge does not replace Robinhood’s MCP connection flow.
It helps the user:

- analyze market conditions
- verify their private ALGO bridge attachment
- generate handoff artifacts
- keep the public research layer separate from private execution
