import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"


def run(script, *args):
    return subprocess.run(
        [sys.executable, str(SCRIPTS / script), *map(str, args)],
        text=True,
        capture_output=True,
    )


def add_report(mission):
    result = run("mission_report.py", mission)
    assert result.returncode == 0, result.stderr


def test_init_creates_durable_mission(tmp_path):
    mission = tmp_path / "demo"
    result = run(
        "mission_init.py",
        mission,
        "--objective",
        "ship a safe feature",
        "--deliverable",
        "README.md",
        "--acceptance",
        "tests pass",
    )
    assert result.returncode == 0, result.stderr
    assert (mission / "MISSION.md").exists()
    assert (mission / "PROGRESS.md").exists()
    state = json.loads((mission / "state.json").read_text())
    assert state["status"] == "active"
    assert state["deliverables"] == ["README.md"]
    assert state["acceptance"][0] == "tests pass"


def test_gate_rejects_claim_without_evidence(tmp_path):
    mission = tmp_path / "demo"
    assert run("mission_init.py", mission, "--objective", "demo").returncode == 0
    result = run("acceptance_gate.py", mission)
    assert result.returncode != 0
    assert "incomplete" in result.stdout.lower()


def test_gate_accepts_only_explicit_verified_state(tmp_path):
    mission = tmp_path / "demo"
    assert run("mission_init.py", mission, "--objective", "demo").returncode == 0
    (mission / "README.md").write_text("done\n")
    state_path = mission / "state.json"
    state = json.loads(state_path.read_text())
    state["deliverables"] = ["README.md"]
    state["verified_outputs"] = ["README.md"]
    state["open_questions"] = []
    state["acceptance_checks"] = [{"name": "smoke", "command": [sys.executable, "-c", "print('ok')"]}]
    state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2))
    add_report(mission)
    result = run("acceptance_gate.py", mission)
    assert result.returncode == 0, result.stderr + result.stdout
    assert "passed" in result.stdout.lower()


def test_gate_rejects_malformed_acceptance_check_without_traceback(tmp_path):
    mission = tmp_path / "demo"
    assert run("mission_init.py", mission, "--objective", "demo").returncode == 0
    state_path = mission / "state.json"
    state = json.loads(state_path.read_text())
    state["acceptance_checks"] = ["python -m pytest"]
    state["open_questions"] = []
    state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2))
    result = run("acceptance_gate.py", mission)
    assert result.returncode != 0
    assert "expected object" in result.stdout.lower()
    assert "traceback" not in result.stdout.lower()


def test_gate_runs_declared_verification_gate_and_checks_evidence(tmp_path):
    mission = tmp_path / "demo"
    assert run("mission_init.py", mission, "--objective", "demo").returncode == 0
    evidence = mission / "evidence.txt"
    evidence.write_text("observed\n", encoding="utf-8")
    deliverable = mission / "README.md"
    deliverable.write_text("done\n", encoding="utf-8")
    state_path = mission / "state.json"
    state = json.loads(state_path.read_text())
    state["deliverables"] = [str(deliverable)]
    state["verified_outputs"] = [str(deliverable)]
    state["open_questions"] = []
    state["verification_gates"] = [{
        "id": "artifact_parity",
        "required": True,
        "checks": [{"name": "parity", "command": [sys.executable, "-c", "print('match')"]}],
        "evidence": ["evidence.txt"],
    }]
    state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2))
    add_report(mission)
    result = run("acceptance_gate.py", mission)
    assert result.returncode == 0, result.stderr + result.stdout


def test_gate_allows_gate_evidence_without_verified_outputs(tmp_path):
    mission = tmp_path / "demo"
    assert run("mission_init.py", mission, "--objective", "demo").returncode == 0
    evidence = mission / "evidence.txt"
    evidence.write_text("observed\n", encoding="utf-8")
    state_path = mission / "state.json"
    state = json.loads(state_path.read_text())
    state["open_questions"] = []
    state["verification_gates"] = [{
        "id": "contract",
        "required": True,
        "checks": [{"name": "smoke", "command": [sys.executable, "-c", "print('ok')"]}],
        "evidence": ["evidence.txt"],
    }]
    state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2))
    add_report(mission)
    result = run("acceptance_gate.py", mission)
    assert result.returncode == 0, result.stderr + result.stdout


def test_gate_rejects_required_verification_gate_without_evidence(tmp_path):
    mission = tmp_path / "demo"
    assert run("mission_init.py", mission, "--objective", "demo").returncode == 0
    state_path = mission / "state.json"
    state = json.loads(state_path.read_text())
    state["open_questions"] = []
    state["verification_gates"] = [{"id": "real_user_surface", "required": True, "checks": []}]
    state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2))
    result = run("acceptance_gate.py", mission)
    assert result.returncode != 0
    assert "no checks" in result.stdout.lower()
    assert "no evidence" in result.stdout.lower()


def test_gate_accepts_omitted_conditional_gates(tmp_path):
    mission = tmp_path / "demo"
    assert run("mission_init.py", mission, "--objective", "demo").returncode == 0
    deliverable = mission / "README.md"
    deliverable.write_text("done\n", encoding="utf-8")
    state_path = mission / "state.json"
    state = json.loads(state_path.read_text())
    state["deliverables"] = [str(deliverable)]
    state["verified_outputs"] = [str(deliverable)]
    state["open_questions"] = []
    state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2))
    add_report(mission)
    result = run("acceptance_gate.py", mission)
    assert result.returncode == 0, result.stderr + result.stdout


def test_mission_schema_declares_verification_gates():
    schema = json.loads((ROOT / "mission.schema.json").read_text(encoding="utf-8"))
    gates = schema["properties"]["verification_gates"]
    assert gates["type"] == "array"
    assert "id" in gates["items"]["required"]
    assert "checks" in gates["items"]["required"]
    assert "evidence" in gates["items"]["required"]


def test_stall_detector_distinguishes_progress(tmp_path):
    mission = tmp_path / "demo"
    assert run("mission_init.py", mission, "--objective", "demo").returncode == 0
    state_path = mission / "state.json"
    state = json.loads(state_path.read_text())
    state["no_progress_count"] = 3
    state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2))
    result = run("stall_detector.py", mission, "--max-no-progress", "2")
    assert result.returncode != 0
    assert "stall" in result.stdout.lower()


def test_continuation_prompt_is_actionable(tmp_path):
    mission = tmp_path / "demo"
    assert run("mission_init.py", mission, "--objective", "demo").returncode == 0
    result = run("continuation_prompt.py", mission)
    assert result.returncode == 0
    assert "do not claim completion" in result.stdout.lower()


def test_skill_does_not_encode_project_specific_workarounds():
    skill = (ROOT / "SKILL.md").read_text(encoding="utf-8").lower()
    for forbidden in ("evolving-profile", "next.js", "qwen", "9999", "i18n"):
        assert forbidden not in skill
    assert "generalization boundary" in skill
    assert "counterexamples" in skill


def test_skill_invocation_boundary_is_explicit_and_short_tasks_are_excluded():
    skill = (ROOT / "SKILL.md").read_text(encoding="utf-8").lower()
    assert "explicitly asks for long-mission/long-task execution" in skill
    assert "do not use for ordinary short tasks" in skill
    assert "do not invoke it merely because a task has several steps" in skill
    assert "real user-surface gate" in skill
    assert "source/build/runtime parity gate" in skill
    assert "conditional process-memory gate" in skill


def test_readiness_gate_collects_contract_non_interactively(tmp_path):
    mission = tmp_path / "ready"
    result = run(
        "mission_start.py",
        mission,
        "--non-interactive",
        "--objective",
        "ship a safe change",
        "--deliverable",
        "artifact.txt",
        "--acceptance",
        "smoke passes",
        "--scope",
        "no release",
        "--risk",
        "publish requires confirmation",
        "--limits",
        "10 iterations",
    )
    assert result.returncode == 0, result.stderr
    contract = (mission / "MISSION.md").read_text(encoding="utf-8")
    assert "publish requires confirmation" in contract
    assert "10 iterations" in contract


def test_reference_profile_creates_capability_contract(tmp_path):
    mission = tmp_path / "reference"
    result = run(
        "mission_init.py", mission, "--profile", "reference_ui",
        "--objective", "match a reference", "--deliverable", "artifact.html",
        "--acceptance", "visual and interaction checks pass",
    )
    assert result.returncode == 0, result.stderr
    state = json.loads((mission / "state.json").read_text())
    assert state["acceptance_profile"] == "reference_ui"
    assert state["capability_probe"]["status"] == "pending"
    assert (mission / "reference-contract.json").exists()
    assert (mission / "capability-probe.json").exists()
    assert (mission / "acceptance-matrix.json").exists()


def test_reference_gate_rejects_pending_probe(tmp_path):
    mission = tmp_path / "reference"
    assert run("mission_init.py", mission, "--profile", "reference_ui", "--objective", "match a reference").returncode == 0
    result = run("reference_gate.py", mission)
    assert result.returncode != 0
    assert "capability probe" in result.stdout.lower()


def test_reference_gate_accepts_degraded_noncritical_result(tmp_path):
    mission = tmp_path / "reference"
    assert run("mission_init.py", mission, "--profile", "reference_ui", "--objective", "match a reference").returncode == 0
    (mission / "reference-contract.json").write_text(json.dumps({"source": "reference.png", "required_structure": ["spine"], "required_relationships": ["parallel"], "interaction": ["click"], "responsive_viewports": ["desktop"], "critical_requirements": ["structure", "interaction", "evidence"], "degradable_requirements": ["animation"]}))
    (mission / "capability-probe.json").write_text(json.dumps({"status": "degraded_pass", "attempts": [{"hypothesis": "use css grid", "result": {"improved": True}}], "bottleneck": "animation engine", "fallbacks": ["static transitions"]}))
    (mission / "acceptance-matrix.json").write_text(json.dumps({"items": [
        {"id": "s", "category": "structure", "status": "passed", "critical": True},
        {"id": "r", "category": "relationship", "status": "passed", "critical": True},
        {"id": "i", "category": "interaction", "status": "passed", "critical": True},
        {"id": "v", "category": "visual", "status": "degraded", "deviation": "animation omitted"},
        {"id": "e", "category": "evidence", "status": "passed", "critical": True},
        {"id": "a", "category": "responsive", "status": "passed"},
    ]}))
    state_path = mission / "state.json"
    state = json.loads(state_path.read_text()); state["capability_probe"] = {"status": "degraded_pass"}; state_path.write_text(json.dumps(state))
    result = run("reference_gate.py", mission)
    assert result.returncode == 0, result.stderr + result.stdout


def test_stall_detector_catches_capability_no_improvement(tmp_path):
    mission = tmp_path / "reference"
    assert run("mission_init.py", mission, "--profile", "reference_ui", "--objective", "match a reference").returncode == 0
    (mission / "capability-probe.json").write_text(json.dumps({"attempts": [
        {"hypothesis": "route one", "result": {"improved": False}},
        {"hypothesis": "route two", "result": {"improved": False}},
    ]}))
    result = run("stall_detector.py", mission)
    assert result.returncode != 0
    assert "capability probe" in result.stdout.lower()


def test_generated_ledger_is_bilingual_english_then_chinese(tmp_path):
    mission = tmp_path / "bilingual"
    assert run("mission_init.py", mission, "--objective", "demo", "--acceptance", "tests pass").returncode == 0
    contract = (mission / "MISSION.md").read_text(encoding="utf-8")
    progress = (mission / "PROGRESS.md").read_text(encoding="utf-8")
    assert "# Mission Contract\n# 任务契约" in contract
    assert "## Stop rules" in contract and "## 停止规则" in contract
    assert "# Progress Ledger\n# 进度账本" in progress
    assert "每次有实质行动后追加一条记录" in progress


def test_continuation_prompt_is_bilingual(tmp_path):
    mission = tmp_path / "bilingual"
    assert run("mission_init.py", mission, "--objective", "demo").returncode == 0
    result = run("continuation_prompt.py", mission)
    assert result.returncode == 0
    assert "Continue the active long-task mission" in result.stdout
    assert "从持久化账本继续当前长任务" in result.stdout
