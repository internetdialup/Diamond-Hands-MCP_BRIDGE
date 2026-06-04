from __future__ import annotations

import json
import unittest
from tempfile import TemporaryDirectory

from trading_system.config import load_runtime_config
from trading_system.contracts.types import validate_daily_report_payload
from trading_system.pipeline.daily import DailyPipeline


class ContractTests(unittest.TestCase):
    def test_daily_report_contract_is_valid(self) -> None:
        config = load_runtime_config(__import__("pathlib").Path("config/markets.example.yaml"))
        with TemporaryDirectory() as temp_dir:
            config.reporting.output_dir = __import__("pathlib").Path(temp_dir)
            result = DailyPipeline(config).run()
            payload = json.loads(result.json_path.read_text(encoding="utf-8"))
            validate_daily_report_payload(payload)


if __name__ == "__main__":
    unittest.main()
