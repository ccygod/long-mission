#!/usr/bin/env python3
"""Grant completion only after the independent acceptance gate passes."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from common import load_state, save_state


def main() -> int:
    parser = argparse.ArgumentParser(description="Close a long-mission after its gate passes.")
    parser.add_argument("mission_dir", type=Path)
    parser.add_argument("--runner-finalizing", action="store_true", help="internal supervisor close path")
    args = parser.parse_args()
    mission = args.mission_dir.expanduser().resolve()
    state = load_state(mission)
    if state.get("status") in {"blocked", "paused"}:
        print(f"refusing to close mission with status={state['status']}", file=sys.stderr)
        return 2

    gate = Path(__file__).with_name("acceptance_gate.py")
    gate_args = [sys.executable, str(gate), str(mission)]
    if args.runner_finalizing:
        gate_args.append("--runner-finalizing")
    result = subprocess.run(gate_args, text=True)
    if result.returncode != 0:
        print("mission remains incomplete: acceptance gate failed", file=sys.stderr)
        return result.returncode

    state["status"] = "complete"
    state["completion_receipt"] = {
        "schema": "long-mission.completion-receipt.v1",
        "closed_at": datetime.now(timezone.utc).isoformat(),
        "gate": "acceptance_gate.py",
        "gate_exit_code": 0,
        "mission_id": state.get("mission_id", mission.name),
        "report_path": state.get("report_path", "MISSION-REPORT.md"),
    }
    state["updated_at"] = datetime.now(timezone.utc).isoformat()
    save_state(mission, state)
    print("mission closed: acceptance gate passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
