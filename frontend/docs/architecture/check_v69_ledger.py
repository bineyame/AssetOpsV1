"""Check the planning overlays against the v6.9 screen manifest.

Run from any directory: python frontend/docs/architecture/check_v69_ledger.py
"""

from __future__ import annotations

import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
MANIFEST = HERE.parent.parent / "mockups" / "v69" / "screen-manifest.json"
SCREENS = HERE / "v69-screen-ledger.json"
MODELS = HERE / "v69-model-homes.json"
RENDERED_PANELS = HERE / "v69-rendered-panels.json"
PANEL_CONTRACTS = HERE / "v69-panel-contracts.json"
TIERS = {"Real", "Real with honest gaps", "Deferred", "Dropped"}


def read(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def exact_ids(expected: list[str], actual: list[str], label: str) -> None:
    if len(actual) != len(set(actual)):
        raise SystemExit(f"{label}: duplicate identifiers")
    if set(expected) != set(actual):
        missing = sorted(set(expected) - set(actual))
        extra = sorted(set(actual) - set(expected))
        raise SystemExit(f"{label}: missing={missing}; extra={extra}")


def main() -> None:
    manifest = read(MANIFEST)
    screen_ledger = read(SCREENS)["screens"]
    model_homes = read(MODELS)["models"]
    rendered_panels = read(RENDERED_PANELS)["panels"]
    panel_contracts = read(PANEL_CONTRACTS)["panels"]

    exact_ids([row["id"] for row in manifest], [row["id"] for row in screen_ledger], "screens")
    expected_models = sorted({name for row in manifest for name in row["models"]})
    exact_ids(expected_models, [row["model"] for row in model_homes], "models")

    for row in screen_ledger:
        identifier = row["id"]
        if row["mock_route"] != f"#/{identifier}" or row["visual_reference"] != f"index.html#/{identifier}":
            raise SystemExit(f"{identifier}: mock route/reference mismatch")
        for key in ("product_destination", "coverage", "data_owner", "supported_claim", "interaction", "unknown_or_empty"):
            if not row.get(key):
                raise SystemExit(f"{identifier}: missing {key}")
        if row.get("proposed_fidelity_tier") not in TIERS or row.get("tier_approval") != "pending owner review":
            raise SystemExit(f"{identifier}: fidelity tier proposal/approval is invalid")
        if row["coverage"] == "deferred":
            if not row.get("follow_on") or row.get("task"):
                raise SystemExit(f"{identifier}: deferred routing is incomplete")
        elif not row.get("task"):
            raise SystemExit(f"{identifier}: bounded/partial routing lacks task")

    for row in model_homes:
        actual_screens = [screen["id"] for screen in manifest if row["model"] in screen["models"]]
        if actual_screens != row["manifest_screens"]:
            raise SystemExit(f"{row['model']}: screen usage changed")
        if row["status"].endswith("decision_required") and not row.get("decision_gate"):
            raise SystemExit(f"{row['model']}: missing decision gate")

    expected_panels = [(identifier, panel["index"], panel["title"])
                       for identifier, panels in rendered_panels.items() for panel in panels]
    actual_panels = [(row["screen_id"], row["panel_index"], row["panel_title"])
                     for row in panel_contracts]
    screen_tiers = {row["id"]: row["proposed_fidelity_tier"] for row in screen_ledger}
    if len(actual_panels) != len(set(actual_panels)) or set(actual_panels) != set(expected_panels):
        raise SystemExit("Panel contracts do not match rendered mock panels")
    for row in panel_contracts:
        identifier = row["screen_id"]
        if identifier not in {screen["id"] for screen in manifest}:
            raise SystemExit(f"Unknown panel screen {identifier}")
        if row["visual_reference"] != f"index.html#/{identifier}":
            raise SystemExit(f"{identifier}: panel visual reference mismatch")
        for key in ("read_model", "read_model_status", "domain_object", "evidence_roles_or_analytic", "owning_table_or_gap", "claim_limit", "task_or_lane"):
            if not row.get(key):
                raise SystemExit(f"{identifier} panel {row['panel_index']}: missing {key}")
        if row.get("proposed_fidelity_tier") not in TIERS or row.get("tier_approval") != "pending owner review":
            raise SystemExit(f"{identifier} panel {row['panel_index']}: invalid tier/approval")
        if row["proposed_fidelity_tier"] != screen_tiers[identifier]:
            raise SystemExit(f"{identifier} panel {row['panel_index']}: screen tier mismatch")
        if row["read_model_status"].startswith("manifest candidate") and not row["owning_table_or_gap"].startswith("GAP"):
            raise SystemExit(f"{identifier} panel {row['panel_index']}: unreviewed mapping claims a table")

    print(f"v6.9 ledger valid: {len(screen_ledger)} screens, {len(model_homes)} distinct models, {len(panel_contracts)} panels")


if __name__ == "__main__":
    main()
