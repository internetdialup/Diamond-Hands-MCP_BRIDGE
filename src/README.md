# src

Reusable analysis code belongs here.

Use this folder for ingestion helpers, transforms, indicator calculations, labeling logic, and evaluation utilities that should be shared across multiple studies.

Current package layout:

- `trading_system/data/` for provider adapters and market snapshots
- `trading_system/features/` for technical, sentiment, flow, and regime features
- `trading_system/models/` for setup classification and confidence fusion
- `trading_system/pipeline/` for the daily report orchestration
- `trading_system/contracts/` for downstream JSON-friendly payloads
- `trading_system/backtesting/` for labeling and walk-forward scaffolding
