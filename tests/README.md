# tests

Validation for the analysis stack belongs here.

Prioritize tests for data normalization, feature calculations, labeling rules, and any evaluation logic that could silently drift.

The current test suite covers:

- technical feature stability
- setup labeling and walk-forward splits
- daily report contract generation
- scenario-level runs for VIX spike, gamma pin, and sentiment spike conditions
