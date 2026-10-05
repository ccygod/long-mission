#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a durable long-task mission ledger.")
    parser.add_argument("mission_dir", type=Path)
    parser.add_argument("--objective", required=True)
    parser.add_argument("--deliverable", action="append", default=[])
    parser.add_argument("--acceptance", action="append", default=[])
    parser.add_argument("--profile", choices=["standard", "visual_ui", "reference_ui", "capability_sensitive"], default="standard")
    parser.add_argument("--prd", type=Path, default=None, help="optional PRD/specification path")
    parser.add_argument("--max-iterations", type=int, default=10)
    args = parser.parse_args()
    mission = args.mission_dir.expanduser().resolve()
    if (mission / "state.json").exists():
        raise SystemExit(f"refusing to overwrite existing mission: {mission}")
    mission.mkdir(parents=True, exist_ok=True)
    verification_gates = []
    if args.profile in {"visual_ui", "reference_ui", "capability_sensitive"}:
        verification_gates = [
            {"id": "real_user_surface", "required": True, "checks": [], "evidence": []},
            {"id": "artifact_parity", "required": True, "checks": [], "evidence": []},
        ]
    state = {
        "schema_version": 1,
        "mission_id": mission.name,
        "status": "active",
        "objective": args.objective,
        "prd_path": str(args.prd.expanduser().resolve()) if args.prd else None,
        "prd_interpretation": {
            "outcome_goals": [],
            "hard_constraints": [],
            "soft_route_hints": [],
            "open_decisions": [],
            "status": "pending" if args.prd else "not_applicable",
        },
        "deliverables": args.deliverable,
        "acceptance": args.acceptance,
        "acceptance_profile": args.profile,
        "plan": {
            "status": "hypothesis",
            "version": 1,
            "alternatives": [],
            "replans": [],
            "selected_route": None,
        },
        "exploration": {
            "status": "open",
            "probe_budget": 3,
            "probes_used": 0,
            "decision": None,
        },
        "acceptance_checks": [],
        "acceptance_matrix": [],
        "verification_gates": verification_gates,
        "visual_loop": {
            "enabled": args.profile == "visual_ui",
            "max_attempts": None,
            "safety_cap": 20,
            "max_no_improvement": 2,
            "stop_policy": "pass_or_replan_or_block_or_safety_cap",
            "attempts": [],
            "required_evidence": ["real_user_surface_screenshot", "settled_state", "representative_interaction"],
            "status": "pending" if args.profile == "visual_ui" else "not_applicable",
        },
        "completion_receipt": None,
        "report_path": "MISSION-REPORT.md",
        "capability_probe": {"status": "pending", "attempts": [], "ceiling": None, "next_action": "run a minimal representative feasibility probe"} if args.profile != "standard" else {"status": "not_applicable"},
        "attempts": [],
        "verified_outputs": [],
        "open_questions": args.acceptance.copy(),
        "iteration": 0,
        "max_iterations": args.max_iterations,
        "no_progress_count": 0,
        "last_progress_at": now(),
        "next_action": "Inspect the mission contract, then complete one bounded action.",
        "runner": {"required": False, "status": "not_started", "pid": None},
        "blockers": [],
        "evidence": [],
        "research_evidence": [],
        "failure_research": {"required": False, "reason": None, "last_attempt": None},
        "created_at": now(),
        "updated_at": now(),
    }
    (mission / "state.json").write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (mission / "MISSION.md").write_text(
        "# Mission Contract\n# 任务契约\n\n"
        f"## Objective\n## 目标\n{args.objective}\n\n"
        "## Scope\nComplete the objective and its listed deliverables. Do not silently expand scope.\n"
        "## 范围\n完成目标及列出的交付物，不得悄悄扩大范围。\n\n"
        "## Deliverables\n## 交付物\n" + "\n".join(f"- [ ] {x}" for x in args.deliverable) + "\n\n"
        "## Done when\n## 完成条件\n" + "\n".join(f"- [ ] {x}" for x in args.acceptance) + "\n\n"
        "## Stop rules\nOnly stop as complete when acceptance_gate.py exits 0. A blocker, budget limit, or unavailable user decision is incomplete/paused, never success.\n"
        "## 停止规则\n只有 acceptance_gate.py 返回 0 才能标记完成；阻塞、预算限制或能力不可用都应标记为未完成/暂停。\n",
        encoding="utf-8",
    )
    (mission / "PROGRESS.md").write_text(
        f"# Progress Ledger\n# 进度账本\n\nCreated {now()}\n创建时间：{now()}\n\n"
        "Append one entry after every meaningful action. Include evidence, result, and next action.\n"
        "每次有实质行动后追加一条记录，必须包含证据、结果和下一步。\n",
        encoding="utf-8",
    )
    if args.prd:
        (mission / "PRD-INTERPRETATION.md").write_text(
            "# PRD Interpretation\n# PRD 解读\n\n"
            "## English\n\n"
            "### Outcome goals\n\n- Extract the user-visible/product outcomes from the PRD.\n\n"
            "### Hard constraints and invariants\n\n- Record explicit compatibility, safety, data, API, and non-regression constraints.\n\n"
            "### Soft implementation hints\n\n- Record proposed technologies and routes without treating them as mandatory.\n\n"
            "### Open decisions\n\n- Record ambiguities and material choices that need a probe or user decision.\n\n"
            "## 中文\n\n"
            "### 结果目标\n\n- 提取 PRD 要求最终实现的用户可见结果。\n\n"
            "### 硬性约束与不变量\n\n- 记录兼容性、安全、数据、API 和不可回归约束。\n\n"
            "### 可替换的实现建议\n\n- 记录 PRD 提议的技术路线，但不要默认锁定。\n\n"
            "### 待决事项\n\n- 记录歧义和需要探针或用户确认的重大选择。\n",
            encoding="utf-8",
        )
    (mission / "events.jsonl").write_text("", encoding="utf-8")
    (mission / "feedback.jsonl").write_text("", encoding="utf-8")
    (mission / "research.jsonl").write_text("", encoding="utf-8")
    if args.profile != "standard":
        (mission / "reference-contract.json").write_text(json.dumps({"schema": "long-mission.reference-contract.v1", "source": None, "required_structure": [], "required_relationships": [], "interaction": [], "responsive_viewports": [], "allowed_deviation": {}, "critical_requirements": [], "degradable_requirements": []}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        (mission / "capability-probe.json").write_text(json.dumps({"schema": "long-mission.capability-probe.v1", "status": "pending", "tested_capabilities": [], "attempts": [], "bottleneck": None, "fallbacks": []}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        (mission / "acceptance-matrix.json").write_text(json.dumps({"schema": "long-mission.acceptance-matrix.v1", "items": []}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"created mission: {mission}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
