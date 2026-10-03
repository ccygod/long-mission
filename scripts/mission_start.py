#!/usr/bin/env python3
"""Interactive readiness gate for a new long mission.

It asks only for the contract fields that cannot be safely inferred. Passing
flags makes it suitable for automation and CI; no question is mandatory when
the caller already supplied that field.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def ask(label: str, default: str = "") -> str:
    suffix = f" [{default}]" if default else ""
    value = input(f"{label}{suffix}: ").strip()
    return value or default


def main() -> int:
    parser = argparse.ArgumentParser(description="Collect a minimal mission contract before execution.")
    parser.add_argument("mission_dir", type=Path)
    parser.add_argument("--objective")
    parser.add_argument("--deliverable", action="append", default=[])
    parser.add_argument("--acceptance", action="append", default=[])
    parser.add_argument("--scope")
    parser.add_argument("--risk")
    parser.add_argument("--limits")
    parser.add_argument("--profile", choices=["standard", "reference_ui", "capability_sensitive"], default="standard")
    parser.add_argument("--non-interactive", action="store_true")
    args = parser.parse_args()

    interactive = not args.non_interactive and sys.stdin.isatty()
    objective = args.objective or (ask("What outcome must be true when this mission is complete") if interactive else "")
    if not objective:
        raise SystemExit("objective is required; pass --objective or run in an interactive terminal")
    deliverables = list(args.deliverable)
    if not deliverables and interactive:
        raw = ask("Which artifacts must be produced (comma-separated)")
        deliverables = [item.strip() for item in raw.split(",") if item.strip()]
    acceptance = list(args.acceptance)
    if not acceptance and interactive:
        raw = ask("What observable checks prove completion (comma-separated)")
        acceptance = [item.strip() for item in raw.split(",") if item.strip()]
    scope = args.scope or (ask("What is explicitly out of scope", "none") if interactive else "unspecified")
    risk = args.risk or (ask("Which external, destructive, publishing, or permission actions require confirmation", "none") if interactive else "unspecified")
    limits = args.limits or (ask("What time/iteration/cost limit should stop the loop", "use mission defaults") if interactive else "use mission defaults")

    mission = args.mission_dir.expanduser().resolve()
    init = [sys.executable, str(Path(__file__).with_name("mission_init.py")), str(mission), "--objective", objective]
    init.extend(["--profile", args.profile])
    for item in deliverables: init.extend(["--deliverable", item])
    for item in acceptance: init.extend(["--acceptance", item])
    result = subprocess.run(init, text=True)
    if result.returncode != 0:
        return result.returncode
    contract = mission / "MISSION.md"
    with contract.open("a", encoding="utf-8") as handle:
        handle.write(
            f"\n## Readiness Answers\n## 就绪检查答案\n"
            f"- Out of scope: {scope}\n- 范围外：{scope}\n"
            f"- Confirmation boundary: {risk}\n- 需确认的边界：{risk}\n"
            f"- Stop limits: {limits}\n- 停止限制：{limits}\n"
        )
    print(f"readiness gate recorded: {mission}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
