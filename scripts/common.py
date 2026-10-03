"""Shared helpers for long-mission scripts."""
from __future__ import annotations

import json
from pathlib import Path


def load_state(mission: Path) -> dict:
    path = mission / "state.json"
    if not path.exists():
        raise SystemExit(f"missing state.json: {mission}")
    return json.loads(path.read_text(encoding="utf-8"))


def save_state(mission: Path, state: dict) -> None:
    tmp = mission / "state.json.tmp"
    tmp.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp.replace(mission / "state.json")
