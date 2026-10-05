#!/usr/bin/env python3
"""Record an explicit user confirmation for a pending mission contract."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path

from common import load_state, save_state


def main() -> int:
    parser = argparse.ArgumentParser(description="Confirm a displayed long-mission contract.")
    parser.add_argument("mission_dir", type=Path)
    parser.add_argument("--phrase", required=True, help="explicit confirmation phrase from the user")
    args = parser.parse_args()
    phrase = args.phrase.strip()
    if phrase.lower() not in {"confirm", "confirm mission", "confirm execution", "yes", "确认", "确认执行", "确认任务"}:
        raise SystemExit("confirmation phrase not recognized; use an explicit user confirmation")
    mission = args.mission_dir.expanduser().resolve()
    state = load_state(mission)
    state["user_confirmation"] = "confirmed"
    state["confirmation_receipt"] = {"schema": "long-mission.user-confirmation.v1", "source": "explicit_user_confirmation", "phrase": phrase, "at": datetime.now(timezone.utc).isoformat()}
    save_state(mission, state)
    print("CONFIRMED: mission contract recorded")
    print("已确认：任务目标、交付物、验收标准和停止限制已记录")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
