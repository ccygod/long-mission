#!/usr/bin/env python3
"""Fail a mission when its explicit PRD audit still contains unresolved rows."""
from __future__ import annotations

import argparse
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Check a markdown PRD audit for unresolved statuses.")
    parser.add_argument("audit", type=Path)
    parser.add_argument("--allow-partial", action="store_true", help="allow Partial rows; Blocked rows still fail")
    args = parser.parse_args()
    text = args.audit.read_text(encoding="utf-8")
    lines = [line for line in text.splitlines() if line.lstrip().startswith("|")]
    partial = [line for line in lines if "| partial |" in line.lower() or "| partial" in line.lower()]
    blocked = [line for line in lines if "| blocked |" in line.lower() or "| blocked" in line.lower()]
    if blocked or (partial and not args.allow_partial):
        print("INCOMPLETE")
        print("PRD audit contains unresolved rows:")
        for line in blocked + ([] if args.allow_partial else partial):
            print(f"- {line}")
        return 1
    print("PASSED: PRD audit has no unresolved rows")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
