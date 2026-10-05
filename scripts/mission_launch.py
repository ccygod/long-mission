#!/usr/bin/env python3
"""Launch the bounded mission runner as the execution owner.

The model may propose the next action, but this supervisor owns continuation and
does not trust an agent's self-reported completion.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from common import load_state, save_state


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def main() -> int:
    parser = argparse.ArgumentParser(description="Launch a resumable long-mission runner.")
    parser.add_argument("mission_dir", type=Path)
    parser.add_argument("--command", required=True, help="bounded agent command template containing {prompt}")
    parser.add_argument("--max-iterations", type=int, default=None)
    parser.add_argument("--command-timeout", type=int, default=900, help="seconds allowed for one bounded command")
    args = parser.parse_args()
    mission = args.mission_dir.expanduser().resolve()
    state = load_state(mission)
    if state.get("user_confirmation") != "confirmed" or not isinstance(state.get("confirmation_receipt"), dict):
        raise SystemExit("user confirmation receipt is missing; display the mission contract and wait for explicit confirmation before launch")
    log_dir = mission / "runs"
    log_dir.mkdir(exist_ok=True)
    stdout = (log_dir / "supervisor.stdout").open("a", encoding="utf-8")
    stderr = (log_dir / "supervisor.stderr").open("a", encoding="utf-8")
    argv = [sys.executable, str(Path(__file__).with_name("mission_runner.py")), str(mission), "--command", args.command]
    if args.max_iterations is not None:
        argv += ["--max-iterations", str(args.max_iterations)]
    argv += ["--command-timeout", str(args.command_timeout)]
    process = subprocess.Popen(argv, cwd=mission, stdout=stdout, stderr=stderr, start_new_session=True)
    state["runner"] = {"required": True, "status": "running", "pid": process.pid, "started_at": now(), "command_template": args.command}
    state["next_action"] = "Supervisor runner owns continuation; inspect its ledger and gate output."
    state["updated_at"] = now()
    save_state(mission, state)
    print(json.dumps({"status": "running", "pid": process.pid, "mission": str(mission)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
