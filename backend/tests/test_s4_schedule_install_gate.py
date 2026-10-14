"""S4-02d phase 2: the schedule installation gate (`tools/schedule-install-gate.py`) and its templates.

The gate installs nothing; it reads the delivery registry. Owner-visible hosts stay closed until
`I-late-reading-series-and-money-limit` is resolved (D-2026-10-14-s402d-schedule-storage-and-install-gate)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GATE = ROOT / "tools" / "schedule-install-gate.py"
F1 = "I-late-reading-series-and-money-limit"


def run(tmp_path, host_class, nodes, pilot=()) -> tuple[int, str]:
    registry = tmp_path / "registry.json"
    registry.write_text(json.dumps({"nodes": [{"id": k, "status": v} for k, v in nodes.items()],
                                    "real_pilot_requires": list(pilot)}), encoding="utf-8")
    out = subprocess.run([sys.executable, str(GATE), "--host-class", host_class, "--registry", str(registry)],
                         capture_output=True, text=True)
    return out.returncode, out.stdout


def test_owner_visible_hosts_stay_closed_until_the_f1_node_is_resolved(tmp_path) -> None:
    code, out = run(tmp_path, "demo", {F1: "open"})
    assert code == 2 and out.startswith("CLOSED") and F1 in out
    code, out = run(tmp_path, "demo", {F1: "resolved"})
    assert code == 0 and out.startswith("OPEN")
    code, out = run(tmp_path, "pilot", {F1: "resolved", "I-other": "open"}, pilot=[F1, "I-other"])
    assert code == 2 and "I-other" in out
    assert run(tmp_path, "walkthrough", {F1: "resolved"})[0] == 2  # explicit ticks only, never a timer
    assert run(tmp_path, "private", {F1: "open"})[0] == 0


def test_the_real_registry_keeps_the_demo_host_closed_today() -> None:
    out = subprocess.run([sys.executable, str(GATE), "--host-class", "demo"], capture_output=True, text=True)
    registry = json.loads((ROOT / "frontend/docs/architecture/v69-dependency-registry-pilot.json").read_text(
        encoding="utf-8"))
    resolved = {n["id"]: n.get("status") for n in registry["nodes"]}[F1] == "resolved"
    assert out.returncode == (0 if resolved else 2)


def test_the_templates_name_the_gate_and_the_tick_command() -> None:
    service = (ROOT / "backend/deploy/schedule/assetops-schedule-tick@.service").read_text(encoding="utf-8")
    timer = (ROOT / "backend/deploy/schedule/assetops-schedule-tick@.timer").read_text(encoding="utf-8")
    assert "DO NOT INSTALL" in service and F1 in service and "schedule-install-gate.py" in service
    assert "-m assetops_backend.scheduling.run tick --environment %i" in service
    assert "OnCalendar=*-*-* *:*:00" in timer
