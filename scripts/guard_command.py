#!/usr/bin/env python3
"""Reject obviously destructive or secret-exfiltrating command argv."""
from __future__ import annotations

import argparse
import json
import re


BLOCKED = [
    re.compile(r"(^|/)rm$"),
    re.compile(r"--force$"),
    re.compile(r"push$"),
    re.compile(r"reset$"),
]
SENSITIVE = re.compile(r"(api[_-]?key|secret|token|password|private[_-]?key)", re.I)


def main() -> int:
    parser = argparse.ArgumentParser(description="Guard a proposed mission command.")
    parser.add_argument("argv_json", help="JSON array of argv tokens")
    args = parser.parse_args()
    try:
        argv = json.loads(args.argv_json)
    except json.JSONDecodeError as exc:
        print(f"BLOCK: invalid argv JSON: {exc}")
        return 2
    if not isinstance(argv, list) or not all(isinstance(x, str) for x in argv):
        print("BLOCK: argv must be a JSON string array")
        return 2
    joined = " ".join(argv)
    if any(pattern.search(token) for token in argv for pattern in BLOCKED):
        print("BLOCK: destructive or externally mutating command requires explicit review")
        return 1
    if SENSITIVE.search(joined) and any(x in joined.lower() for x in ("echo", "cat", "print", "curl", "http")):
        print("BLOCK: possible secret disclosure")
        return 1
    print("OK: command shape allowed; still verify scope and authorization")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
