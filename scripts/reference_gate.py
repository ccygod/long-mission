#!/usr/bin/env python3
"""Validate the capability and acceptance contract for reference-driven missions."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from common import load_state


REQUIRED_CATEGORIES = {"structure", "relationship", "interaction", "visual", "evidence"}


def read_json(path: Path) -> dict:
    if not path.exists():
        raise ValueError(f"missing {path.name}")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON: {path.name}: {exc.msg}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"{path.name} must contain an object")
    return value


def main() -> int:
    parser = argparse.ArgumentParser(description="Check feasibility and acceptance evidence for reference UI missions.")
    parser.add_argument("mission_dir", type=Path)
    args = parser.parse_args()
    mission = args.mission_dir.expanduser().resolve()
    state = load_state(mission)
    if state.get("acceptance_profile", "standard") == "standard":
        print("SKIP: standard mission profile")
        return 0
    problems: list[str] = []
    try:
        contract = read_json(mission / "reference-contract.json")
        probe_file = read_json(mission / "capability-probe.json")
        matrix_file = read_json(mission / "acceptance-matrix.json")
    except ValueError as exc:
        print("INCOMPLETE")
        print("未完成")
        print(f"- {exc}")
        return 1

    if not contract.get("source") and not contract.get("required_structure"):
        problems.append("reference contract has no source or structural target")
    probe = state.get("capability_probe", {})
    probe_status = probe.get("status") or probe_file.get("status")
    if probe_status in {None, "pending", "unknown"}:
        problems.append("capability probe is not complete")
    if probe_status == "blocked_engine" and state.get("status") not in {"blocked_engine", "blocked", "needs_user_decision"}:
        problems.append("engine ceiling detected but mission is not explicitly blocked or awaiting a decision")
    if probe_status not in {"pass", "degraded_pass", "blocked_engine", "blocked", "needs_user_decision"}:
        problems.append(f"unknown capability probe status: {probe_status}")

    items = matrix_file.get("items", [])
    if not isinstance(items, list) or not items:
        problems.append("acceptance matrix is empty")
    else:
        categories = {item.get("category") for item in items if isinstance(item, dict)}
        missing = REQUIRED_CATEGORIES - categories
        if missing:
            problems.append("acceptance matrix missing categories: " + ", ".join(sorted(missing)))
        for item in items:
            if not isinstance(item, dict) or not item.get("id") or not item.get("category"):
                problems.append("acceptance matrix contains an incomplete item")
                continue
            status = item.get("status", "pending")
            critical = bool(item.get("critical", False))
            if status == "pending":
                problems.append(f"acceptance item pending: {item['id']}")
            if critical and status in {"degraded", "blocked", "failed"}:
                problems.append(f"critical acceptance item not passed: {item['id']} ({status})")
            if status == "degraded" and not item.get("deviation"):
                problems.append(f"degraded item lacks deviation record: {item['id']}")
            if status == "blocked" and not item.get("reason"):
                problems.append(f"blocked item lacks reason: {item['id']}")

    attempts = probe_file.get("attempts", [])
    if probe_status in {"pass", "degraded_pass"} and not attempts:
        problems.append("capability probe has no recorded attempt")
    for attempt in attempts:
        if not isinstance(attempt, dict) or not attempt.get("hypothesis") or not attempt.get("result"):
            problems.append("capability probe attempt lacks hypothesis or result")
    if probe_status == "blocked_engine" and not (probe_file.get("bottleneck") or probe_file.get("fallbacks")):
        problems.append("blocked engine result lacks bottleneck or fallback evidence")

    if problems:
        print("INCOMPLETE")
        print("未完成")
        for problem in problems:
            print(f"- {problem}")
        return 1
    print(f"PASSED: reference capability and acceptance gate ({probe_status})")
    print(f"参考图能力与验收门：通过（{probe_status}）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
