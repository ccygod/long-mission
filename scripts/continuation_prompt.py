#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from common import load_state


def main() -> int:
    parser = argparse.ArgumentParser(description="Print a continuation prompt from durable mission state.")
    parser.add_argument("mission_dir", type=Path)
    args = parser.parse_args()
    state = load_state(args.mission_dir.expanduser().resolve())
    policy = state.get("iteration_policy") if isinstance(state.get("iteration_policy"), dict) else {}
    if state.get("max_iterations") is None:
        budget = (
            f"adaptive (safety cap {policy.get('safety_cap', 20)}, "
            f"max no-progress {policy.get('max_no_progress', 3)})"
        )
    else:
        budget = str(state.get("max_iterations"))
    print(
        "Continue the active long-task mission from the durable ledger.\n"
        "从持久化账本继续当前长任务。\n"
        f"Objective: {state.get('objective')}\n目标：{state.get('objective')}\n"
        f"Iteration: {state.get('iteration')} / {budget}\n迭代：{state.get('iteration')} / {budget}\n"
        f"Next action: {state.get('next_action')}\n下一步：{state.get('next_action')}\n"
        f"Blockers: {state.get('blockers') or 'none'}\n阻塞项：{state.get('blockers') or '无'}\n"
        "Read state.json and PROGRESS.md before acting. Do one bounded action, record evidence, "
        "run the acceptance gate, and continue if it is incomplete. Do not claim completion "
        "without an independent gate pass.\n"
        "执行前读取 state.json 和 PROGRESS.md；每次只做一个有边界的行动并记录证据，运行验收门，未通过就继续。没有独立验收门通过，不得声称完成。\n"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
