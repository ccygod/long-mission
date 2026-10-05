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
    parser.add_argument("--command-timeout", type=int, default=900, help="seconds allowed for one bounded command")
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
            state = load_state(mission); state.setdefault("runner", {})["status"] = "failed"; save_state(mission, state)
            return 1
        state.setdefault("runner", {})["status"] = "running"
        save_state(mission, state)
        research_hint = " If the previous iteration failed or the acceptance gate failed, first use WebSearch for the exact error, official documentation, and relevant best practices (unless it is a clearly deterministic one-line typo); record the consulted URLs and how they changed the next attempt."
        prompt = (
            f"Continue mission {state.get('mission_id')}. Objective: {state.get('objective')}. "
            f"Next action: {state.get('next_action')}. Read the mission ledger and do not claim completion without the gate."
            + (research_hint if (state.get("failure_research") or {}).get("required") else "")
        )
        argv = [token.replace("{prompt}", prompt) for token in shlex.split(args.command)]
        run_no = int(state.get("iteration", 0)) + 1
        state["iteration"] = run_no
        save_state(mission, state)
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
        try:
            result = subprocess.run(argv, cwd=mission, text=True, capture_output=True, timeout=args.command_timeout)
        except subprocess.TimeoutExpired as exc:
            result = subprocess.CompletedProcess(argv, -124, exc.stdout or "", (exc.stderr or "") + f"\ncommand timeout after {args.command_timeout}s\n")
        (log_dir / f"iteration-{run_no}.stdout").write_text(result.stdout, encoding="utf-8")
        (log_dir / f"iteration-{run_no}.stderr").write_text(result.stderr, encoding="utf-8")
        gate = subprocess.run(
            ["python3", str(Path(__file__).with_name("acceptance_gate.py")), str(mission), "--runner-finalizing"],
            text=True,
            capture_output=True,
        )
        state = load_state(mission)
        raw_feedback = (result.stdout or result.stderr or "iteration completed").strip().splitlines()
        feedback_text = raw_feedback[-1][-500:] if raw_feedback else "iteration completed"
        feedback_status = "passed" if gate.returncode == 0 else ("failed" if result.returncode != 0 else "needs_next_iteration")
        feedback_entry = {"at": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(), "iteration": run_no, "status": feedback_status, "feedback": feedback_text, "next_action": state.get("next_action")}
        with (mission / "feedback.jsonl").open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(feedback_entry, ensure_ascii=False) + "\n")
        state["last_feedback"] = feedback_entry
        save_state(mission, state)
        print(f"ITERATION_FEEDBACK {json.dumps(feedback_entry, ensure_ascii=False)}")
        print(f"第 {run_no} 轮过程反馈：{feedback_text}")
        if gate.returncode == 0:
            state = load_state(mission)
            state["iteration"] = max(int(state.get("iteration", 0)), run_no)
            save_state(mission, state)
            close = subprocess.run(
                ["python3", str(Path(__file__).with_name("mission_close.py")), str(mission), "--runner-finalizing"],
                text=True,
                capture_output=True,
            )
            if close.returncode == 0:
                print(close.stdout.strip())
                state = load_state(mission); state.setdefault("runner", {})["status"] = "complete"; save_state(mission, state)
                return 0
            print("INCOMPLETE: gate passed but mission_close failed", file=sys.stderr)
            state = load_state(mission); state.setdefault("runner", {})["status"] = "failed"; save_state(mission, state)
            return 1
        if result.returncode != 0:
            state = load_state(mission)
            state["status"] = "active"
            state["failure_research"] = {"required": True, "reason": f"iteration {run_no} command exit {result.returncode}", "last_attempt": run_no}
            state["iteration"] = max(int(state.get("iteration", 0)), run_no)
            state.setdefault("blockers", []).append(f"iteration {run_no}: agent command exit {result.returncode}; see runs/iteration-{run_no}.*")
            state["next_action"] = "Retry the bounded command with the next ledger action; do not claim completion from the failed attempt."
            save_state(mission, state)
            print("RETRY: agent command failed; recorded evidence and continuing the supervised loop")
            continue
        if gate.returncode != 0:
            state = load_state(mission)
            state["failure_research"] = {"required": True, "reason": f"iteration {run_no} acceptance gate failed", "last_attempt": run_no}
            save_state(mission, state)
    state = load_state(mission); state.setdefault("runner", {})["status"] = "budget_exhausted"; save_state(mission, state)
    print("INCOMPLETE: iteration budget exhausted; resume from the mission ledger")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
