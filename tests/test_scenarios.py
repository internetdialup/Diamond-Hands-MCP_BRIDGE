from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class ScenarioTests(unittest.TestCase):
    def run_cli(self, scenario: str) -> dict:
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "scenario.yaml"
            bridge_config = Path(temp_dir) / "diamond-hands.local.yaml"
            config_path.write_text(
                "\n".join(
                    [
                        "universe:",
                        "  symbols:",
                        "    - SPY",
                        "    - QQQ",
                        "    - NVDA",
                        "  benchmark: SPY",
                        "  volatility_symbol: VIX",
                        "timeframes:",
                        "  primary: 1d",
                        "  secondary:",
                        "    - 1h",
                        "data_source:",
                        "  provider: example_vendor",
                        f"  scenario: {scenario}",
                        "  timezone: America/Chicago",
                        "  adjusted_prices: true",
                        "reporting:",
                        f"  output_dir: {temp_dir}",
                        "engines:",
                        "  enabled:",
                        "    - regime",
                        "    - sentiment",
                        "    - flow",
                        "    - pattern",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            subprocess.run(
                [
                    sys.executable,
                    "main.py",
                    "--config",
                    str(config_path),
                    "--output-dir",
                    temp_dir,
                    "--bridge-config",
                    str(bridge_config),
                    "--analyze-only",
                ],
                cwd=ROOT,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            return json.loads((Path(temp_dir) / "daily_report.json").read_text(encoding="utf-8"))

    def test_vix_spike_produces_interpretable_regime(self) -> None:
        payload = self.run_cli("vix_spike")
        self.assertIn(payload["market_regime"]["name"], {"Risk Off", "Transitional"})

    def test_gamma_pin_day_mentions_spy_in_no_trade_or_drivers(self) -> None:
        payload = self.run_cli("gamma_pin")
        text = " ".join(payload["confidence_drivers"] + payload["no_trade_flags"])
        self.assertIn("SPY", text)

    def test_sentiment_spike_increases_nvidia_mentions(self) -> None:
        payload = self.run_cli("sentiment_spike")
        nvda = next(item for item in payload["symbols"] if item["ticker"] == "NVDA")
        self.assertGreater(nvda["sentiment"]["mention_delta"], 500)


if __name__ == "__main__":
    unittest.main()
