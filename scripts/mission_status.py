#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from common import load_state


def main() -> int:
    parser = argparse.ArgumentParser(description="Show compact durable mission status.")
    parser.add_argument("mission_dir", type=Path)
    args = parser.parse_args()
    state = load_state(args.mission_dir.expanduser().resolve())
    print(json.dumps({
        "mission_id": state.get("mission_id"),
        "status": state.get("status"),
        "iteration": state.get("iteration"),
        "max_iterations": state.get("max_iterations"),
        "no_progress_count": state.get("no_progress_count"),
        "next_action": state.get("next_action"),
        "blockers": state.get("blockers", []),
        "open_questions": state.get("open_questions", []),
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
