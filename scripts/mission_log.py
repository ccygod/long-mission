#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from common import load_state, save_state


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def main() -> int:
    parser = argparse.ArgumentParser(description="Record one bounded mission iteration.")
    parser.add_argument("mission_dir", type=Path)
    parser.add_argument("--action", required=True)
    parser.add_argument("--result", required=True)
    parser.add_argument("--evidence", action="append", default=[])
    parser.add_argument("--next-action", required=True)
    parser.add_argument("--no-progress", action="store_true")
    args = parser.parse_args()
    mission = args.mission_dir.expanduser().resolve()
    state = load_state(mission)
    state["iteration"] = int(state.get("iteration", 0)) + 1
    state["no_progress_count"] = int(state.get("no_progress_count", 0)) + (1 if args.no_progress else 0)
    if not args.no_progress:
        state["no_progress_count"] = 0
        state["last_progress_at"] = now()
    state["next_action"] = args.next_action
    state["updated_at"] = now()
    state.setdefault("evidence", []).extend(args.evidence)
    save_state(mission, state)
    entry = {
        "at": now(),
        "iteration": state["iteration"],
        "action": args.action,
        "result": args.result,
        "evidence": args.evidence,
        "next_action": args.next_action,
        "no_progress": args.no_progress,
    }
    with (mission / "events.jsonl").open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=False) + "\n")
    with (mission / "PROGRESS.md").open("a", encoding="utf-8") as handle:
        handle.write(
            f"\n## Iteration {state['iteration']} — {entry['at']}\n"
            f"- Action: {args.action}\n- Evidence: {', '.join(args.evidence) or 'none'}\n"
            f"- Result: {args.result}\n- Next action: {args.next_action}\n"
        )
    print(f"logged iteration {state['iteration']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
