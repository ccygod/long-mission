#!/usr/bin/env python3
"""Independent gate for the visual/UI long-mission loop.

The agent records each real-surface check in state.json.  This gate does not
pretend that unit tests or a stale headless DOM prove what a user sees.
"""
from __future__ import annotations

import argparse
from pathlib import Path

from common import load_state


ALLOWED_VERIFIERS = {"computer_use", "real_screenshot", "browser_screenshot"}


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate visual/UI evidence and attempt budget.")
    parser.add_argument("mission_dir", type=Path)
    args = parser.parse_args()
    mission = args.mission_dir.expanduser().resolve()
    state = load_state(mission)
    if state.get("acceptance_profile") != "visual_ui":
        print("SKIP: visual_ui profile not enabled")
        return 0

    loop = state.get("visual_loop")
    problems: list[str] = []
    if not isinstance(loop, dict) or not loop.get("enabled"):
        problems.append("visual_loop is not enabled")
        loop = {}
    max_attempts = int(loop.get("max_attempts", 10))
    attempts = loop.get("attempts", [])
    if not isinstance(attempts, list):
        problems.append("visual_loop.attempts must be a list")
        attempts = []
    if len(attempts) > max_attempts:
        problems.append(f"visual attempt budget exceeded: {len(attempts)} > {max_attempts}")
    if not attempts:
        problems.append("no post-change real-surface visual evidence recorded")
    passed = False
    for index, attempt in enumerate(attempts, 1):
        if not isinstance(attempt, dict):
            problems.append(f"visual attempt {index} is not an object")
            continue
        verifier = attempt.get("verifier")
        if verifier not in ALLOWED_VERIFIERS:
            problems.append(f"visual attempt {index} has invalid verifier: {verifier}")
        if attempt.get("settled") is not True:
            problems.append(f"visual attempt {index} was not recorded after async settling")
        if not attempt.get("interaction"):
            problems.append(f"visual attempt {index} lacks representative interaction evidence")
        evidence = attempt.get("evidence")
        evidence_paths = evidence if isinstance(evidence, list) else [evidence]
        if not evidence_paths or any(not isinstance(item, str) or not item for item in evidence_paths):
            problems.append(f"visual attempt {index} lacks screenshot evidence")
        else:
            for item in evidence_paths:
                path = Path(item).expanduser()
                if not path.is_absolute():
                    path = mission / path
                if not path.is_file():
                    problems.append(f"missing visual evidence for attempt {index}: {item}")
        if attempt.get("status") == "pass":
            passed = True
    if not passed:
        problems.append("no visual attempt has status=pass")
    variants = state.get("visual_variants", [])
    if variants:
        if not isinstance(variants, list):
            problems.append("visual_variants must be a list")
        else:
            for index, variant in enumerate(variants, 1):
                if not isinstance(variant, dict):
                    problems.append(f"visual variant {index} is not an object")
                    continue
                for field in ("id", "url", "evidence", "status"):
                    if not variant.get(field):
                        problems.append(f"visual variant {index} missing {field}")
                evidence = variant.get("evidence") if isinstance(variant.get("evidence"), list) else [variant.get("evidence")]
                for item in evidence:
                    if not isinstance(item, str) or not item:
                        problems.append(f"visual variant {index} has invalid evidence")
                        continue
                    path = Path(item).expanduser()
                    if not path.is_absolute():
                        path = mission / path
                    if not path.is_file():
                        problems.append(f"missing evidence for visual variant {variant.get('id')}: {item}")
                if variant.get("status") != "pass":
                    problems.append(f"visual variant not passed: {variant.get('id')}")
    if problems:
        print("INCOMPLETE")
        print("未完成")
        for problem in problems:
            print(f"- {problem}")
        return 1
    print("PASSED: visual UI evidence gate")
    print("视觉 UI 证据门：通过")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
