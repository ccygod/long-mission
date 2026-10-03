#!/usr/bin/env python3
"""Record a deliberate strategy change without changing the mission outcome contract."""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from common import load_state, save_state


def main() -> int:
    parser = argparse.ArgumentParser(description="Record a long-mission replan.")
    parser.add_argument("mission_dir", type=Path)
    parser.add_argument("--superseded", required=True)
    parser.add_argument("--observed-failure", required=True)
    parser.add_argument("--new-route", required=True)
    parser.add_argument("--preserve", action="append", default=[])
    parser.add_argument("--next-action", required=True)
    args = parser.parse_args()

    mission = args.mission_dir.expanduser().resolve()
    state = load_state(mission)
    plan = dict(state.get("plan") or {})
    version = int(plan.get("version", 1)) + 1
    event = {
        "at": datetime.now(timezone.utc).isoformat(),
        "from_version": int(plan.get("version", 1)),
        "to_version": version,
        "superseded": args.superseded,
        "observed_failure": args.observed_failure,
        "new_route": args.new_route,
        "preserved_invariants": args.preserve,
        "next_action": args.next_action,
    }
    plan.update({"status": "selected", "version": version, "selected_route": args.new_route})
    plan.setdefault("replans", []).append(event)
    state["plan"] = plan
    state["next_action"] = args.next_action
    state["updated_at"] = event["at"]
    save_state(mission, state)
    with (mission / "events.jsonl").open("a", encoding="utf-8") as handle:
        handle.write(json.dumps({"type": "replan", **event}, ensure_ascii=False) + "\n")
    with (mission / "PROGRESS.md").open("a", encoding="utf-8") as handle:
        handle.write(
            f"\n## Replan {version} — {event['at']}\n"
            f"- Superseded: {args.superseded}\n"
            f"- Observed failure: {args.observed_failure}\n"
            f"- New route: {args.new_route}\n"
            f"- Preserved invariants: {', '.join(args.preserve) or 'none'}\n"
            f"- Next action: {args.next_action}\n"
        )
    print(f"recorded replan version {version}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
