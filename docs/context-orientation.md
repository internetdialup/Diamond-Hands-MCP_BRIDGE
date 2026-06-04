# Trading-MCP-Analyzer — Context Orientation

The running per-Knob log for this repository. Each Bump should add a short, concrete entry with date, timestamp, and what changed in the analysis stack, data model, or research posture. Keep newest entries at the top.

This repository is the research and evaluation side of the trading system. It should stay focused on ingesting data, exploring indicators, validating hypotheses, scoring strategy ideas, and documenting findings before anything moves into execution code.

Use this file to track:

- changes to market data sources, schemas, and collection jobs
- new indicators, feature engineering, and evaluation methods
- research conclusions that affect whether a strategy graduates to the algo repo
- revisions to risk assumptions, labeling rules, or backtest interpretation

---

## Knob: repository bootstrap — Wednesday, June 3, 2026, 08:26 PM CDT

Created the initial cold-start structure for `Trading-MCP-Analyzer` under the shared Git projects folder and aligned it with the `Documentation.md` baseline. Added `AGENT.md`, the core `behavior/`, `skills/`, and `workflows/` folders, plus this repo-specific orientation file and README.

Set the repo contract around research-first work: market data ingestion, indicator analysis, experiment tracking, and evaluation artifacts belong here. Strategy execution, broker integration, and live-trading logic are intentionally separated into `Trading-MCP-Algo`.
