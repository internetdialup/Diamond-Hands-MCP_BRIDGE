from __future__ import annotations

import io
import subprocess
import sys
import tempfile
import unittest
import unittest.mock
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PRIVATE_ALGO = ROOT.parent / "Trading-MCP-Algo"


class DiamondHandsBridgeCliTests(unittest.TestCase):
    def test_setup_writes_local_bridge_config(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            bridge_config = Path(temp_dir) / "diamond-hands.local.yaml"
            subprocess.run(
                [
                    sys.executable,
                    "main.py",
                    "--setup",
                    "--bridge-config",
                    str(bridge_config),
                    "--private-algo-repo",
                    str(PRIVATE_ALGO),
                ],
                cwd=ROOT,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            self.assertTrue(bridge_config.exists())
            text = bridge_config.read_text(encoding="utf-8")
            self.assertIn("diamond-hands-bridge/v1", text)

    def test_verify_bridge_passes_with_valid_private_repo(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            bridge_config = Path(temp_dir) / "diamond-hands.local.yaml"
            proc = subprocess.run(
                [
                    sys.executable,
                    "main.py",
                    "--verify-bridge",
                    "--bridge-config",
                    str(bridge_config),
                    "--private-algo-repo",
                    str(PRIVATE_ALGO),
                ],
                cwd=ROOT,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            self.assertEqual(proc.returncode, 0)
            self.assertIn("Bridge compatibility check passed.", proc.stdout)

    @unittest.mock.patch("trading_system.cli.hand_off_to_private_algo")
    @unittest.mock.patch("trading_system.cli.save_public_bridge_config")
    def test_analyze_then_hand_off_invokes_private_algo(
        self, mock_save: unittest.mock.MagicMock, mock_handoff: unittest.mock.MagicMock
    ) -> None:
        from trading_system.cli import main as cli_main

        # Mock successful handoff
        mock_handoff.return_value = subprocess.CompletedProcess(
            args=["python3", "main.py"],
            returncode=0,
            stdout="Mocked handoff success",
            stderr="",
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            bridge_config = Path(temp_dir) / "diamond-hands.local.yaml"
            output_dir = Path(temp_dir) / "public-output"
            
            # We need to mock sys.stdout to capture output
            with unittest.mock.patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
                with unittest.mock.patch("sys.stdin.isatty", return_value=False):
                    exit_code = cli_main(
                        [
                            "--bridge-config",
                            str(bridge_config),
                            "--private-algo-repo",
                            str(PRIVATE_ALGO),
                            "--output-dir",
                            str(output_dir),
                            "--analyze-then-hand-off",
                        ]
                    )
                    
                    stdout = mock_stdout.getvalue()

            self.assertEqual(exit_code, 0)
            self.assertIn("Diamond Hands private handoff completed.", stdout)
            self.assertIn("Mocked handoff success", stdout)
            self.assertTrue((output_dir / "daily_report.json").exists())


if __name__ == "__main__":
    unittest.main()
