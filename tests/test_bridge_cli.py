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
            args=["trading-algo", "bridge", "run"],
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

    def test_shared_private_command_aliases_resolve(self) -> None:
        from trading_system.cli import normalize_command

        self.assertEqual(normalize_command("/liveboard"), "/liveboard")
        self.assertEqual(normalize_command("/hood"), "/hood")
        self.assertEqual(normalize_command("/paper"), "/paper")
        self.assertEqual(normalize_command("/agents"), "/agents")
        self.assertEqual(normalize_command("/spy0dte"), "/spy0dte")
        self.assertEqual(normalize_command("/memory"), "/memory")
        self.assertEqual(normalize_command("/recall"), "/recall")
        self.assertEqual(normalize_command("/risk"), "/risk")
        self.assertEqual(normalize_command("/stop"), "/stop")
        self.assertEqual(normalize_command("/daemon"), "/daemon")
        self.assertEqual(normalize_command("/botstatus"), "/botstatus")
        self.assertEqual(normalize_command("/startbot"), "/startbot")
        self.assertIsNone(normalize_command("/train"))
        self.assertIsNone(normalize_command("/rank"))

    def test_command_menus_are_curated_for_operator_surface(self) -> None:
        from trading_system.cli import CORE_COMMAND_SPECS, PRIVATE_OPERATOR_COMMAND_SPECS, EXPERIMENTAL_COMMAND_SPECS

        visible = {spec.command for spec in CORE_COMMAND_SPECS + PRIVATE_OPERATOR_COMMAND_SPECS + EXPERIMENTAL_COMMAND_SPECS}
        for command in {"/agents", "/spy0dte", "/liveboard", "/paper", "/risk", "/stop", "/memory", "/recall", "/hood", "/daemon", "/botstatus", "/startbot"}:
            self.assertIn(command, visible)
        self.assertNotIn("/train", visible)
        self.assertNotIn("/rank", visible)

    @unittest.mock.patch("trading_system.bridge_runtime.shutil.which", return_value="/usr/local/bin/trading-algo")
    @unittest.mock.patch("trading_system.bridge_runtime.subprocess.run")
    def test_handoff_invokes_trading_algo_bridge_run(
        self, mock_run: unittest.mock.MagicMock, _mock_which: unittest.mock.MagicMock
    ) -> None:
        from trading_system.bridge_config import PrivateAlgoConfig, PublicBridgeConfig, RobinhoodConfig
        from trading_system.bridge_runtime import hand_off_to_private_algo

        mock_run.return_value = subprocess.CompletedProcess(args=[], returncode=0, stdout="", stderr="")
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            config_path = root / "config/bridge.example.yaml"
            config_path.parent.mkdir(parents=True)
            config_path.write_text("bridge: {}\n", encoding="utf-8")
            config = PublicBridgeConfig(
                version="diamond-hands-bridge/v1",
                first_run_completed=True,
                private_algo=PrivateAlgoConfig(root, Path("config/bridge.example.yaml"), Path("outputs/bridge/execution_preview.json")),
                public_artifact_json=Path("outputs/daily/daily_report.json"),
                robinhood=RobinhoodConfig("https://agent.robinhood.com/mcp/trading", False),
                config_path=root / "diamond-hands.local.yaml",
            )

            hand_off_to_private_algo(config, root / "daily_report.json")

        args = mock_run.call_args.args[0]
        self.assertEqual(args[:3], ["/usr/local/bin/trading-algo", "bridge", "run"])
        self.assertIn("--artifact", args)

    @unittest.mock.patch("trading_system.cli.run_private_algo_command")
    @unittest.mock.patch("trading_system.cli.hand_off_to_private_algo")
    @unittest.mock.patch("trading_system.cli.verify_private_algo_bridge")
    def test_boot_runs_handoff_memory_and_cockpit(
        self,
        mock_verify: unittest.mock.MagicMock,
        mock_handoff: unittest.mock.MagicMock,
        mock_private: unittest.mock.MagicMock,
    ) -> None:
        from trading_system.bridge_runtime import BridgeVerification
        from trading_system.cli import main as cli_main

        mock_verify.return_value = BridgeVerification(True, True, True, True, ["Bridge compatibility check passed."])
        mock_handoff.return_value = subprocess.CompletedProcess(args=[], returncode=0, stdout="handoff ok", stderr="")
        mock_private.return_value = subprocess.CompletedProcess(args=[], returncode=0, stdout="private ok", stderr="")

        with tempfile.TemporaryDirectory() as temp_dir:
            bridge_config = Path(temp_dir) / "diamond-hands.local.yaml"
            output_dir = Path(temp_dir) / "public-output"
            with unittest.mock.patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
                with unittest.mock.patch("sys.stdin.isatty", return_value=False):
                    exit_code = cli_main(
                        [
                            "boot",
                            "--bridge-config",
                            str(bridge_config),
                            "--private-algo-repo",
                            str(PRIVATE_ALGO),
                            "--output-dir",
                            str(output_dir),
                        ]
                    )
            stdout = mock_stdout.getvalue()

        self.assertEqual(exit_code, 0)
        self.assertIn("Diamond Hands private handoff completed.", stdout)
        self.assertEqual(
            [call.args[1] for call in mock_private.call_args_list],
            [["memory", "ingest"], ["memory", "ingest-docs"], ["session", "watch", "--watch-once"]],
        )

    @unittest.mock.patch("trading_system.cli.run_private_algo_command")
    @unittest.mock.patch("trading_system.cli.verify_private_algo_bridge")
    def test_curated_private_routes_invoke_expected_trading_algo_args(
        self,
        mock_verify: unittest.mock.MagicMock,
        mock_private: unittest.mock.MagicMock,
    ) -> None:
        from trading_system.bridge_runtime import BridgeVerification
        from trading_system.cli import run_interactive_shell
        from trading_system.bridge_config import PrivateAlgoConfig, PublicBridgeConfig, RobinhoodConfig

        mock_verify.return_value = BridgeVerification(True, True, True, True, ["Bridge compatibility check passed."])
        mock_private.return_value = subprocess.CompletedProcess(args=[], returncode=0, stdout="private ok", stderr="")
        bridge_config = PublicBridgeConfig(
            version="diamond-hands-bridge/v1",
            first_run_completed=True,
            private_algo=PrivateAlgoConfig(PRIVATE_ALGO, Path("config/bridge.example.yaml"), Path("outputs/bridge/execution_preview.json")),
            public_artifact_json=Path("outputs/daily/daily_report.json"),
            robinhood=RobinhoodConfig("https://agent.robinhood.com/mcp/trading", False),
            config_path=Path("config/diamond-hands.local.yaml"),
        )
        args = unittest.mock.Mock(config="config/markets.example.yaml", output_dir=None)

        commands = iter(["/agents", "/spy0dte", "/paper", "/risk", "/stop", "/memory", "/recall", "/hood", "/daemon", "/botstatus", "/quit"])
        with unittest.mock.patch("builtins.input", side_effect=lambda *_: next(commands)):
            with unittest.mock.patch("sys.stdout", new_callable=io.StringIO):
                code = run_interactive_shell(args, bridge_config, mock_verify.return_value)

        self.assertEqual(code, 0)
        self.assertEqual(
            [call.args[1] for call in mock_private.call_args_list],
            [
                ["agents", "status"],
                ["options", "spy-0dte"],
                ["session", "paper-trade"],
                ["session", "risk"],
                ["session", "stop"],
                ["memory", "status"],
                ["memory", "recall"],
                ["hood", "check"],
                ["daemon", "status"],
                ["daemon", "status"],
            ],
        )

    def test_startbot_prints_safe_daemon_guidance(self) -> None:
        from trading_system.bridge_config import PrivateAlgoConfig, PublicBridgeConfig, RobinhoodConfig
        from trading_system.bridge_runtime import BridgeVerification
        from trading_system.cli import run_interactive_shell

        bridge_config = PublicBridgeConfig(
            version="diamond-hands-bridge/v1",
            first_run_completed=True,
            private_algo=PrivateAlgoConfig(PRIVATE_ALGO, Path("config/bridge.example.yaml"), Path("outputs/bridge/execution_preview.json")),
            public_artifact_json=Path("outputs/daily/daily_report.json"),
            robinhood=RobinhoodConfig("https://agent.robinhood.com/mcp/trading", False),
            config_path=Path("config/diamond-hands.local.yaml"),
        )
        args = unittest.mock.Mock(config="config/markets.example.yaml", output_dir=None)
        verification = BridgeVerification(True, True, True, True, ["Bridge compatibility check passed."])

        commands = iter(["/startbot", "/quit"])
        with unittest.mock.patch("builtins.input", side_effect=lambda *_: next(commands)):
            with unittest.mock.patch("sys.stdout", new_callable=io.StringIO) as stdout:
                code = run_interactive_shell(args, bridge_config, verification)

        self.assertEqual(code, 0)
        output = stdout.getvalue()
        self.assertIn("trading-algo daemon run", output)
        self.assertIn("make daemon-start", output)
        self.assertIn("paper-intent/dry-run only", output)


if __name__ == "__main__":
    unittest.main()
