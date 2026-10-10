import json
import subprocess
import sys
from pathlib import Path


SKILL = Path(__file__).resolve().parents[1]
SCRIPTS = SKILL / "scripts"


def write_state(mission: Path, **updates):
    state = {
        "mission_id": "test-mission",
        "status": "active",
        "iteration": 0,
        "max_iterations": 2,
        "objective": "test",
        "next_action": "test",
        "deliverables": [],
        "verified_outputs": [],
        "open_questions": [],
        "acceptance_checks": [],
        "verification_gates": [],
        "acceptance_profile": "standard",
        "report_path": "MISSION-REPORT.md",
        "user_confirmation": "confirmed",
        "confirmation_receipt": {"source": "test"},
        "runner": {"required": False, "status": "not_started", "pid": None},
    }
    state.update(updates)
    (mission / "state.json").write_text(json.dumps(state), encoding="utf-8")


def test_runner_respects_total_iteration_budget(tmp_path):
    mission = tmp_path / "mission"
    mission.mkdir()
    (mission / "MISSION-REPORT.md").write_text("## English\n## 中文\n", encoding="utf-8")
    marker = mission / "ran.txt"
    (mission / "worker.py").write_text(
        "from pathlib import Path\n"
        "Path('ran.txt').write_text('ran', encoding='utf-8')\n",
        encoding="utf-8",
    )
    write_state(mission, iteration=2, max_iterations=2)

    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPTS / "mission_runner.py"),
            str(mission),
            "--command",
            "python3 worker.py {prompt}",
        ],
        cwd=mission,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    assert not marker.exists()
    state = json.loads((mission / "state.json").read_text(encoding="utf-8"))
    assert state["iteration"] == 2
    assert state["runner"]["status"] == "budget_exhausted"


def test_mission_log_does_not_double_count_reserved_runner_iteration(tmp_path):
    mission = tmp_path / "mission"
    mission.mkdir()
    write_state(
        mission,
        iteration=1,
        runner={"required": True, "status": "running", "iteration": 1, "pid": 123},
    )

    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPTS / "mission_log.py"),
            str(mission),
            "--action",
            "test",
            "--result",
            "ok",
            "--next-action",
            "next",
        ],
        cwd=mission,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    state = json.loads((mission / "state.json").read_text(encoding="utf-8"))
    assert state["iteration"] == 1


def test_mission_check_preserves_acceptance_gate_failure(tmp_path):
    mission = tmp_path / "mission"
    mission.mkdir()
    (mission / "MISSION-REPORT.md").write_text("## English\n## 中文\n", encoding="utf-8")
    write_state(mission)

    result = subprocess.run(
        [sys.executable, str(SCRIPTS / "mission_check.py"), str(mission)],
        cwd=mission,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    assert "INCOMPLETE" in result.stdout
    assert "OK: no_progress_count=0" in result.stdout


def test_new_mission_uses_adaptive_budget_by_default(tmp_path):
    mission = tmp_path / "mission"
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPTS / "mission_init.py"),
            str(mission),
            "--objective",
            "test",
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    state = json.loads((mission / "state.json").read_text(encoding="utf-8"))
    assert state["max_iterations"] is None
    assert state["iteration_policy"] == {
        "mode": "adaptive",
        "safety_cap": 20,
        "max_no_progress": 3,
    }


def test_continuation_prompt_explains_adaptive_budget(tmp_path):
    mission = tmp_path / "mission"
    mission.mkdir()
    write_state(mission, max_iterations=None)
    state_path = mission / "state.json"
    state = json.loads(state_path.read_text(encoding="utf-8"))
    state["iteration_policy"] = {"mode": "adaptive", "safety_cap": 20, "max_no_progress": 3}
    state_path.write_text(json.dumps(state), encoding="utf-8")

    result = subprocess.run(
        [sys.executable, str(SCRIPTS / "continuation_prompt.py"), str(mission)],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "adaptive" in result.stdout
    assert "safety cap 20" in result.stdout


def test_runner_uses_adaptive_safety_cap_when_no_explicit_limit(tmp_path):
    mission = tmp_path / "mission"
    mission.mkdir()
    (mission / "MISSION-REPORT.md").write_text("## English\n## 中文\n", encoding="utf-8")
    marker = mission / "ran.txt"
    (mission / "worker.py").write_text(
        "from pathlib import Path\n"
        "Path('ran.txt').write_text('ran', encoding='utf-8')\n",
        encoding="utf-8",
    )
    write_state(
        mission,
        max_iterations=None,
        iteration_policy={"mode": "adaptive", "safety_cap": 1, "max_no_progress": 3},
    )

    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPTS / "mission_runner.py"),
            str(mission),
            "--command",
            "python3 worker.py {prompt}",
        ],
        cwd=mission,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    assert marker.exists()
    state = json.loads((mission / "state.json").read_text(encoding="utf-8"))
    assert state["iteration"] == 1
    assert state["runner"]["status"] == "budget_exhausted"


def test_runner_stops_for_replan_after_repeated_no_progress(tmp_path):
    mission = tmp_path / "mission"
    mission.mkdir()
    (mission / "MISSION-REPORT.md").write_text("## English\n## 中文\n", encoding="utf-8")
    marker = mission / "runs.txt"
    (mission / "worker.py").write_text(
        "from pathlib import Path\n"
        "p=Path('runs.txt')\n"
        "p.write_text(p.read_text()+'x' if p.exists() else 'x', encoding='utf-8')\n",
        encoding="utf-8",
    )
    write_state(
        mission,
        max_iterations=None,
        no_progress_count=4,
        iteration_policy={"mode": "adaptive", "safety_cap": 5, "max_no_progress": 3},
    )

    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPTS / "mission_runner.py"),
            str(mission),
            "--command",
            "python3 worker.py {prompt}",
        ],
        cwd=mission,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    assert marker.read_text(encoding="utf-8") == "x"
    state = json.loads((mission / "state.json").read_text(encoding="utf-8"))
    assert state["runner"]["status"] == "replan_required"
    assert "replan" in state["next_action"].lower()
