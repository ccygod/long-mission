#!/usr/bin/env python3
"""Create a bilingual final-report template for a long mission."""
from __future__ import annotations

import argparse
from pathlib import Path

from common import load_state


def main() -> int:
    parser = argparse.ArgumentParser(description="Create the English-first/Chinese-following mission report template.")
    parser.add_argument("mission_dir", type=Path)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    mission = args.mission_dir.expanduser().resolve()
    state = load_state(mission)
    report_path = mission / state.get("report_path", "MISSION-REPORT.md")
    if report_path.exists() and not args.force:
        raise SystemExit(f"report already exists: {report_path}; use --force only to replace it")
    objective = state.get("objective", "")
    acceptance = state.get("acceptance", [])
    evidence = state.get("evidence", [])
    acceptance_lines = "\n".join(f"- {item}" for item in acceptance) or "- To be completed from the mission contract."
    evidence_lines = "\n".join(f"- {item}" for item in evidence) or "- Add commands, screenshots, receipts, and runtime evidence here."
    prd_section = ""
    if state.get("prd_path"):
        prd_section = "### PRD interpretation\n\nRecord which PRD statements were outcome goals, hard constraints, soft implementation hints, and open decisions.\n\n"
    report = f'''# Mission Report: {state.get("mission_id", mission.name)}

## English

### Objective and outcome

{objective}

Final status: `{state.get("status", "incomplete")}`

### Acceptance contract

{acceptance_lines}

{prd_section}### Execution and exploration

### Execution and exploration

Describe the bounded probes, selected route, implementation work, replans, and why the final route was chosen. Do not turn an initial plan into a permanent requirement.

### Verification evidence

{evidence_lines}

Add the final test/build/browser/runtime receipts and source/build/runtime identities.

### Deviations, failures, and unresolved items

Record failed attempts, route changes, known limitations, skipped checks, and anything that remains unknown.

### Artifacts and next actions

List changed files, screenshots, reports, release links, and any follow-up work.

## 中文

### 目标与结果

（用中文说明本次任务要解决什么，最终是否完成，以及完成边界。）

### 验收标准

（逐条说明最终验收标准，不要把具体技术路线误写成验收标准。）

### 执行过程与探索

（说明尝试过哪些路线、哪条路线最终被采用、发生过哪些重规划，以及为什么。）

### 验证证据

（列出测试、构建、真实 UI、Computer Use、运行版本和回执证据。）

### 失败、偏差与未决项

（说明失败尝试、跳过项、已知限制和仍然未知的内容。）

### 产物与后续动作

（列出文件、截图、报告、PR/发布链接和后续工作。）
'''
    report_path.write_text(report, encoding="utf-8")
    print(report_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
