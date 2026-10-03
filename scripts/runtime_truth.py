#!/usr/bin/env python3
"""Verify that a real URL is served by the expected local process and directory."""
from __future__ import annotations

import argparse
import json
import subprocess
import urllib.request
from pathlib import Path


def listening_pids(port: int) -> list[str]:
    try:
        result = subprocess.run(
            ["lsof", "-nP", f"-iTCP:{port}", "-sTCP:LISTEN", "-Fp"],
            text=True,
            capture_output=True,
            check=False,
        )
    except OSError:
        return []
    return list(dict.fromkeys(line[1:] for line in result.stdout.splitlines() if line.startswith("p") and line[1:].isdigit()))


def process_cwd(pid: str) -> str | None:
    try:
        result = subprocess.run(["lsof", "-a", "-p", pid, "-d", "cwd", "-Fn"], text=True, capture_output=True, check=False)
    except OSError:
        return None
    for line in result.stdout.splitlines():
        if line.startswith("n"):
            return line[1:]
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description="Check URL, listening PID and runtime working directory identity.")
    parser.add_argument("--url", required=True)
    parser.add_argument("--expect", action="append", default=[], help="body marker; may be repeated")
    parser.add_argument("--port", type=int, required=True)
    parser.add_argument("--working-directory", type=Path)
    args = parser.parse_args()

    try:
        body = urllib.request.urlopen(args.url, timeout=5).read().decode("utf-8", "replace")
    except Exception as exc:
        print(json.dumps({"status": "failed", "reason": "url_unavailable", "error": str(exc)}))
        return 1
    missing = [marker for marker in args.expect if marker not in body]
    pids = listening_pids(args.port)
    cwds = {pid: process_cwd(pid) for pid in pids}
    expected = str(args.working_directory.resolve()) if args.working_directory else None
    distinct_cwds = {cwd for cwd in cwds.values() if cwd}
    shadowed = len(distinct_cwds) > 1
    cwd_match = not expected or (len(distinct_cwds) == 1 and expected in distinct_cwds)
    payload = {"status": "passed" if not missing and pids and cwd_match and not shadowed else "failed", "url": args.url, "port": args.port, "pids": pids, "cwds": cwds, "shadowed_listeners": shadowed, "missing_markers": missing, "expected_working_directory": expected}
    print(json.dumps(payload, ensure_ascii=False))
    return 0 if payload["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
