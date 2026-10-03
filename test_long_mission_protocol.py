#!/usr/bin/env python3
"""Protocol-level smoke tests for the long-mission control loop."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SCRIPTS = ROOT / "scripts"


def run_script(name: str, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPTS / name), *args],
        text=True,
        capture_output=True,
        check=check,
    )


class LongMissionProtocolTests(unittest.TestCase):
    def test_reference_profile_has_required_gate_stubs(self):
        with tempfile.TemporaryDirectory() as directory:
            mission = Path(directory) / "reference"
            run_script("mission_init.py", str(mission), "--objective", "reference test", "--profile", "reference_ui")
            state = json.loads((mission / "state.json").read_text())
            self.assertEqual(state["plan"]["status"], "hypothesis")
            self.assertEqual(state["report_path"], "MISSION-REPORT.md")
            self.assertEqual(
                [gate["id"] for gate in state["verification_gates"]],
                ["real_user_surface", "artifact_parity"],
            )

    def test_prd_mode_creates_interpretation_template(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            prd = root / "spec.md"
            prd.write_text("# Approved specification\n", encoding="utf-8")
            mission = root / "prd-mission"
            run_script("mission_init.py", str(mission), "--objective", "prd test", "--prd", str(prd))
            state = json.loads((mission / "state.json").read_text())
            self.assertEqual(state["prd_path"], str(prd.resolve()))
            interpretation = (mission / "PRD-INTERPRETATION.md").read_text()
            self.assertIn("Outcome goals", interpretation)
            self.assertIn("Soft implementation hints", interpretation)
            self.assertIn("## 中文", interpretation)

    def test_replan_preserves_invariants_and_increments_plan(self):
        with tempfile.TemporaryDirectory() as directory:
            mission = Path(directory) / "replan"
            run_script("mission_init.py", str(mission), "--objective", "replan test")
            run_script(
                "mission_replan.py",
                str(mission),
                "--superseded", "marker edge",
                "--observed-failure", "not visible in real screenshot",
                "--new-route", "custom SVG edge",
                "--preserve", "topology",
                "--preserve", "receipt counts",
                "--next-action", "run browser screenshot",
            )
            state = json.loads((mission / "state.json").read_text())
            self.assertEqual(state["plan"]["version"], 2)
            self.assertEqual(state["plan"]["selected_route"], "custom SVG edge")
            self.assertEqual(state["plan"]["replans"][0]["preserved_invariants"], ["topology", "receipt counts"])

    def test_normal_mode_allows_replan_without_prd_interpretation(self):
        with tempfile.TemporaryDirectory() as directory:
            mission = Path(directory) / "normal"
            run_script("mission_init.py", str(mission), "--objective", "normal long task", "--deliverable", "MISSION.md")
            state = json.loads((mission / "state.json").read_text())
            self.assertIsNone(state["prd_path"])
            self.assertEqual(state["prd_interpretation"]["status"], "not_applicable")
            run_script(
                "mission_replan.py", str(mission),
                "--superseded", "first implementation", "--observed-failure", "visual mismatch",
                "--new-route", "alternate implementation", "--preserve", "user-visible outcome",
                "--next-action", "verify alternate route",
            )
            state = json.loads((mission / "state.json").read_text())
            self.assertEqual(state["plan"]["version"], 2)
            self.assertFalse((mission / "PRD-INTERPRETATION.md").exists())

    def test_close_requires_bilingual_report_then_records_receipt(self):
        with tempfile.TemporaryDirectory() as directory:
            mission = Path(directory) / "close"
            run_script("mission_init.py", str(mission), "--objective", "close test", "--deliverable", "MISSION.md")
            state_path = mission / "state.json"
            state = json.loads(state_path.read_text())
            state["verified_outputs"] = ["MISSION.md"]
            state["open_questions"] = []
            state_path.write_text(json.dumps(state))

            failed = run_script("mission_close.py", str(mission), check=False)
            self.assertNotEqual(failed.returncode, 0)
            self.assertIn("acceptance gate failed", failed.stderr)

            run_script("mission_report.py", str(mission))
            closed = run_script("mission_close.py", str(mission))
            self.assertEqual(closed.returncode, 0)
            state = json.loads(state_path.read_text())
            self.assertEqual(state["status"], "complete")
            self.assertEqual(state["completion_receipt"]["gate_exit_code"], 0)

    def test_stale_complete_without_receipt_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            mission = Path(directory) / "stale"
            run_script("mission_init.py", str(mission), "--objective", "stale test")
            state_path = mission / "state.json"
            state = json.loads(state_path.read_text())
            state["status"] = "complete"
            state_path.write_text(json.dumps(state))
            report = mission / "MISSION-REPORT.md"
            report.write_text("# Mission Report\n\n## English\n\n## 中文\n")
            gate = run_script("acceptance_gate.py", str(mission), check=False)
            self.assertNotEqual(gate.returncode, 0)
            self.assertIn("complete_without_completion_receipt", gate.stdout)

    def test_runner_rejects_stale_complete_state(self):
        with tempfile.TemporaryDirectory() as directory:
            mission = Path(directory) / "runner"
            run_script("mission_init.py", str(mission), "--objective", "runner test")
            state_path = mission / "state.json"
            state = json.loads(state_path.read_text())
            state["status"] = "complete"
            state_path.write_text(json.dumps(state))
            result = run_script("mission_runner.py", str(mission), "--command", "echo {prompt}", check=False)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("stale complete status", result.stderr)

    def test_prd_audit_gate_rejects_unresolved_partial_items(self):
        with tempfile.TemporaryDirectory() as directory:
            audit = Path(directory) / "PRD-AUDIT.md"
            audit.write_text("| Deep Audit | Partial | evaluator queue deferred |\n", encoding="utf-8")
            result = run_script("prd_audit_gate.py", str(audit), check=False)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("partial", result.stdout.lower())

    def test_prd_audit_gate_accepts_all_pass(self):
        with tempfile.TemporaryDirectory() as directory:
            audit = Path(directory) / "PRD-AUDIT.md"
            audit.write_text("| Event Contract | Pass | tests |\n| UI | Pass | browser |\n", encoding="utf-8")
            result = run_script("prd_audit_gate.py", str(audit))
            self.assertEqual(result.returncode, 0)

    def test_skill_mentions_runtime_truth_and_positive_negative_fixtures(self):
        skill = (ROOT / "SKILL.md").read_text(encoding="utf-8").lower()
        self.assertIn("runtime truth", skill)
        self.assertIn("positive", skill)
        self.assertIn("negative", skill)

    def test_runtime_truth_checks_url_and_process_working_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            port = 18000 + (hash(directory) % 1000)
            server = subprocess.Popen([sys.executable, "-m", "http.server", str(port)], cwd=directory, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            try:
                time.sleep(0.4)
                result = run_script("runtime_truth.py", "--url", f"http://127.0.0.1:{port}", "--expect", "Directory listing", "--port", str(port), "--working-directory", directory)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertIn('"status": "passed"', result.stdout)
            finally:
                server.terminate(); server.wait(timeout=3)


if __name__ == "__main__":
    unittest.main()
