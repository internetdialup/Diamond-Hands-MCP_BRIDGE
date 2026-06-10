# Diamond Hands Bridge Protocol (v1.0)

This document defines the standardized JSON-RPC contract between the **Public TUI (The Oven)** and your **Private Logic (The Food)**. To build your own "Lego Pieces" for the Diamond Hands ecosystem, your private MCP server must implement these tools and return the specified payloads.

## 1. Intelligence Hub Protocol (`/intel`)

The `/intel` command is a generic renderer. Your backend can dictate any number of modules (e.g., `social`, `political`, `tanner`) by implementing the `dh_get_intel_module` tool.

**Expected Response Shape:**
```json
{
  "title": "NARRATIVE INTEL",
  "content": "A high-level summary of the market narrative.",
  "metrics": {
    "Sentiment Score": 0.85,
    "Volume Intensity": "HIGH"
  },
  "timeline": [
    {"time": "09:30", "event": "Market Open - Gap Up"}
  ],
  "grid": [
    {"Symbol": "SPY", "Bias": "BULLISH", "Conf": "92%"}
  ],
  "status": "READY"
}
```

## 2. Multi-Agent Debate Protocol (`/debate`)

The debate transcript allows you to visualize the "Thinking" process of multiple agents.

**Tool:** `dh_get_debate_transcript`
**Payload Requirements:**
- `agent`: The name of the logic node (e.g. "Risk Node").
- `verdict`: A short string (e.g. "VETO" or "EXECUTE").
- `reason`: The textual rationale.
- `icon`: An emoji representing the node.
- `color`: An ANSI escape code for the TUI (e.g. `\u001b[32m` for green).
- `scorecard` (Optional): A dictionary of 0-10 safety scores.

## 3. High-Fidelity Heuristics (`/hft`, `/system`)

The `/hft` dashboard surfaces performance and health metrics.

**Tool:** `dh_get_heuristics`
**Required Fields:**
- `debate_latency_ms`: Total end-to-end processing time.
- `last_dsr_with_k`: The Deflated Sharpe Ratio of the active strategy.
- `feature_store_hit_rate`: Cache performance of your data store.
- `portfolio_qp_solve_us`: Latency of your allocator in microseconds.

## 4. Strategy Calibration (`/forge`)

The `/forge` command allows the operator to tweak your private logic at runtime.

**Tool:** `dh_update_knob`
**Arguments:** `{"key": "...", "value": 0.0}`
**Note:** The private repo is responsible for persisting these values to your own model configurations.

---

By adhering to this protocol, you can build any trading model—from simple RSI cross-overs to complex RL-driven allocators—and use the Diamond Hands terminal as your professional-grade Command & Control Center.
