#!/usr/bin/env python3
"""Small outer-loop adapter for commands that accept a prompt argument.

Use {prompt} in --command tokens. The runner never claims success itself; the
independent acceptance gate decides whether another iteration is required.
"""
from __future__ import annotations

import argparse
import json
import shlex
import subprocess
import sys
from pathlib import Path

from common import load_state, save_state


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a bounded, resumable mission loop.")
    parser.add_argument("mission_dir", type=Path)
    parser.add_argument("--command", required=True, help="command template; use {prompt}")
    parser.add_argument("--max-iterations", type=int, default=None)
    args = parser.parse_args()
    mission = args.mission_dir.expanduser().resolve()
    state = load_state(mission)
    limit = args.max_iterations or int(state.get("max_iterations", 10))
    log_dir = mission / "runs"
    log_dir.mkdir(exist_ok=True)
    for _ in range(limit):
        state = load_state(mission)
        if state.get("status") == "complete":
            gate = subprocess.run(
                ["python3", str(Path(__file__).with_name("acceptance_gate.py")), str(mission)],
                text=True,
                capture_output=True,
            )
            if gate.returncode == 0 and isinstance(load_state(mission).get("completion_receipt"), dict):
                print("COMPLETE: recorded completion receipt and independent gate passed")
                return 0
            print("INCOMPLETE: stale complete status without a valid completion receipt", file=sys.stderr)
            return 1
        prompt = (
            f"Continue mission {state.get('mission_id')}. Objective: {state.get('objective')}. "
            f"Next action: {state.get('next_action')}. Read the mission ledger and do not claim completion without the gate."
        )
        argv = [token.replace("{prompt}", prompt) for token in shlex.split(args.command)]
        run_no = int(state.get("iteration", 0)) + 1
        guard = subprocess.run(
            ["python3", str(Path(__file__).with_name("guard_command.py")), json.dumps(argv)],
            text=True,
            capture_output=True,
        )
        if guard.returncode != 0:
            state = load_state(mission)
            state["status"] = "blocked"
            state.setdefault("blockers", []).append(guard.stdout.strip() or "command guard rejected argv")
            save_state(mission, state)
            print("BLOCKED: command guard rejected the proposed command")
            return 1
        result = subprocess.run(argv, cwd=mission, text=True, capture_output=True)
        (log_dir / f"iteration-{run_no}.stdout").write_text(result.stdout, encoding="utf-8")
        (log_dir / f"iteration-{run_no}.stderr").write_text(result.stderr, encoding="utf-8")
        gate = subprocess.run(
            ["python3", str(Path(__file__).with_name("acceptance_gate.py")), str(mission)],
            text=True,
            capture_output=True,
        )
        if gate.returncode == 0:
            state = load_state(mission)
            state["iteration"] = max(int(state.get("iteration", 0)), run_no)
            save_state(mission, state)
            close = subprocess.run(
                ["python3", str(Path(__file__).with_name("mission_close.py")), str(mission)],
                text=True,
                capture_output=True,
            )
            if close.returncode == 0:
                print(close.stdout.strip())
                return 0
            print("INCOMPLETE: gate passed but mission_close failed", file=sys.stderr)
            return 1
        if result.returncode != 0:
            state = load_state(mission)
            state["status"] = "failed"
            state.setdefault("blockers", []).append(f"agent command exit {result.returncode}; see runs/iteration-{run_no}.*")
            save_state(mission, state)
            print("INCOMPLETE: agent command failed; inspect the run log")
            return 1
    print("INCOMPLETE: iteration budget exhausted; resume from the mission ledger")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
