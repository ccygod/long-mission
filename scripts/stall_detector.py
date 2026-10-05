#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from common import load_state


def main() -> int:
    parser = argparse.ArgumentParser(description="Detect repeated iterations without evidence of progress.")
    parser.add_argument("mission_dir", type=Path)
    parser.add_argument("--max-no-progress", type=int, default=3)
    parser.add_argument("--max-no-improvement", type=int, default=2)
    args = parser.parse_args()
    mission = args.mission_dir.expanduser().resolve()
    state = load_state(mission)
    count = int(state.get("no_progress_count", 0))
    if count > args.max_no_progress:
        print(f"STALL: no_progress_count={count} > limit={args.max_no_progress}")
        print("状态：停滞")
        return 1
    probe_path = mission / "capability-probe.json"
    if probe_path.exists():
        try:
            attempts = json.loads(probe_path.read_text(encoding="utf-8")).get("attempts", [])
        except (OSError, json.JSONDecodeError):
            attempts = []
        tail = []
        for attempt in reversed(attempts):
            if not isinstance(attempt, dict):
                break
            result = attempt.get("result", {})
            improved = result.get("improved") if isinstance(result, dict) else None
            if improved is None:
                break
            tail.append(bool(improved))
        if len(tail) >= args.max_no_improvement and not any(tail[: args.max_no_improvement]):
            print(f"STALL: capability probe has {args.max_no_improvement} consecutive attempts without improvement")
            print("状态：能力探测停滞")
            return 1
    state_loop = state.get("visual_loop", {})
    if isinstance(state_loop, dict) and state_loop.get("enabled"):
        attempts = state_loop.get("attempts", [])
        limit = int(state_loop.get("max_no_improvement", args.max_no_improvement))
        tail = []
        for attempt in reversed(attempts if isinstance(attempts, list) else []):
            if not isinstance(attempt, dict) or "improved" not in attempt:
                break
            tail.append(bool(attempt.get("improved")))
        if len(tail) >= limit and not any(tail[:limit]):
            print(f"STALL: visual loop has {limit} consecutive attempts without improvement; replan required")
            print("状态：视觉循环连续无改善，必须重规划")
            return 1
    print(f"OK: no_progress_count={count}")
    print("状态：正常")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
