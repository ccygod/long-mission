#!/usr/bin/env python3
"""Run the acceptance and stall checks without masking the gate result."""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Run mission acceptance and stall checks safely.")
    parser.add_argument("mission_dir", type=Path)
    args = parser.parse_args()
    mission = args.mission_dir.expanduser().resolve()
    scripts = Path(__file__).resolve().parent
    gate = subprocess.run(
        [sys.executable, str(scripts / "acceptance_gate.py"), str(mission)],
        text=True,
    )
    stall = subprocess.run(
        [sys.executable, str(scripts / "stall_detector.py"), str(mission)],
        text=True,
    )
    if gate.returncode != 0:
        return gate.returncode
    return stall.returncode


if __name__ == "__main__":
    raise SystemExit(main())
