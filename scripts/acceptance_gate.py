#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
from pathlib import Path
from typing import Any

from common import load_state


def main() -> int:
    parser = argparse.ArgumentParser(description="Independent completion gate.")
    parser.add_argument("mission_dir", type=Path)
    args = parser.parse_args()
    mission = args.mission_dir.expanduser().resolve()
    state = load_state(mission)
    problems: list[str] = []
    if state.get("status") in {"blocked", "paused", "failed"}:
        problems.append(f"status={state['status']}")
    if state.get("status") == "complete" and not isinstance(state.get("completion_receipt"), dict):
        problems.append("complete_without_completion_receipt: use mission_close.py")
    report_path = Path(state.get("report_path", "MISSION-REPORT.md"))
    if not report_path.is_absolute():
        report_path = args.mission_dir.expanduser().resolve() / report_path
    if not report_path.is_file():
        problems.append(f"missing bilingual mission report: {report_path.name}")
    else:
        report_text = report_path.read_text(encoding="utf-8")
        required_headings = ("## English", "## 中文")
        for heading in required_headings:
            if heading not in report_text:
                problems.append(f"mission report missing heading: {heading}")
    if state.get("prd_path"):
        interpretation = args.mission_dir.expanduser().resolve() / "PRD-INTERPRETATION.md"
        if not interpretation.is_file():
            problems.append("missing PRD-INTERPRETATION.md")
        else:
            interpretation_text = interpretation.read_text(encoding="utf-8")
            for heading in ("## English", "## 中文", "Outcome goals", "Hard constraints and invariants", "Soft implementation hints"):
                if heading not in interpretation_text:
                    problems.append(f"PRD interpretation missing section: {heading}")
    missing = [p for p in state.get("deliverables", []) if not (mission / p).exists()]
    if missing:
        problems.append("missing deliverables: " + ", ".join(missing))
    verified = set(state.get("verified_outputs", []))
    missing_verified = [p for p in state.get("deliverables", []) if p not in verified]
    if missing_verified:
        problems.append("unverified deliverables: " + ", ".join(missing_verified))
    if state.get("open_questions"):
        problems.append("open questions: " + "; ".join(map(str, state["open_questions"])))

    def check_command(name: str, command: Any, cwd: Path = mission) -> None:
        if not isinstance(command, list) or not command or not all(isinstance(item, str) and item for item in command):
            problems.append(f"invalid acceptance check: {name}")
            return
        try:
            result = subprocess.run(command, cwd=cwd, text=True, capture_output=True)
        except OSError as exc:
            problems.append(f"could not run check: {name} ({exc})")
            return
        if result.returncode != 0:
            problems.append(f"failed check: {name} (exit {result.returncode})")

    checks = state.get("acceptance_checks", [])
    if not isinstance(checks, list):
        problems.append("acceptance_checks must be a list")
        checks = []
    for index, check in enumerate(checks):
        if not isinstance(check, dict):
            problems.append(f"invalid acceptance check at index {index}: expected object")
            continue
        name = check.get("name", f"check-{index + 1}")
        if not isinstance(name, str) or not name.strip():
            problems.append(f"invalid acceptance check name at index {index}")
            continue
        check_command(name, check.get("command"))

    gates = state.get("verification_gates", [])
    if gates is None:
        gates = []
    if not isinstance(gates, list):
        problems.append("verification_gates must be a list")
        gates = []
    if state.get("acceptance_profile", "standard") != "standard" and not gates:
        problems.append("nonstandard mission missing verification_gates")
    for index, gate in enumerate(gates):
        if not isinstance(gate, dict):
            problems.append(f"invalid verification gate at index {index}: expected object")
            continue
        gate_id = gate.get("id")
        if not isinstance(gate_id, str) or not gate_id.strip():
            problems.append(f"verification gate {index + 1} has no id")
            continue
        required = gate.get("required", True)
        if not isinstance(required, bool):
            problems.append(f"verification gate {gate_id} has non-boolean required")
            required = True
        gate_checks = gate.get("checks", [])
        evidence = gate.get("evidence", [])
        if not isinstance(gate_checks, list) or not isinstance(evidence, list):
            problems.append(f"verification gate {gate_id} checks/evidence must be lists")
            continue
        if required and not gate_checks:
            problems.append(f"required verification gate has no checks: {gate_id}")
        if required and not evidence:
            problems.append(f"required verification gate has no evidence: {gate_id}")
        for check_index, check in enumerate(gate_checks):
            if not isinstance(check, dict):
                problems.append(f"invalid check in verification gate {gate_id} at index {check_index}")
                continue
            name = check.get("name", f"{gate_id}-check-{check_index + 1}")
            check_command(f"{gate_id}/{name}", check.get("command"))
        for evidence_path in evidence:
            if not isinstance(evidence_path, str) or not evidence_path:
                problems.append(f"invalid evidence path in verification gate: {gate_id}")
                continue
            path = Path(evidence_path).expanduser()
            if not path.is_absolute():
                path = mission / path
            if not path.exists() or not path.is_file():
                problems.append(f"missing verification evidence for {gate_id}: {evidence_path}")

    matrix = state.get("acceptance_matrix", [])
    if matrix:
        if not isinstance(matrix, list):
            problems.append("acceptance_matrix must be a list when provided")
        else:
            for index, item in enumerate(matrix):
                if not isinstance(item, dict) or not item.get("id") or not item.get("category"):
                    problems.append(f"acceptance_matrix item {index + 1} is incomplete")
                    continue
                status = item.get("status", "pending")
                if status == "pending":
                    problems.append(f"acceptance_matrix item pending: {item['id']}")
                if item.get("critical") and status in {"failed", "blocked", "degraded"}:
                    problems.append(f"critical acceptance_matrix item not passed: {item['id']} ({status})")
    gate_evidence_declared = any(
        isinstance(gate, dict) and isinstance(gate.get("evidence"), list) and bool(gate.get("evidence"))
        for gate in gates
    )
    if not verified and not checks and not gate_evidence_declared:
        problems.append("no independently verified evidence")
    if state.get("acceptance_profile", "standard") != "standard":
        reference_gate = Path(__file__).with_name("reference_gate.py")
        result = subprocess.run([str(reference_gate), str(mission)], cwd=mission, text=True, capture_output=True)
        if result.returncode != 0:
            problems.append("reference capability/acceptance gate failed")
            problems.extend(line[2:] for line in result.stdout.splitlines() if line.startswith("- "))
    if state.get("acceptance_profile") == "visual_ui":
        visual_gate = Path(__file__).with_name("visual_gate.py")
        result = subprocess.run([str(visual_gate), str(mission)], cwd=mission, text=True, capture_output=True)
        if result.returncode != 0:
            problems.append("visual UI gate failed")
            problems.extend(line[2:] for line in result.stdout.splitlines() if line.startswith("- "))
    if problems:
        print("INCOMPLETE")
        print("未完成")
        for problem in problems:
            print(f"- {problem}")
        return 1
    print("PASSED: independent acceptance gate")
    print("独立验收门：通过")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
