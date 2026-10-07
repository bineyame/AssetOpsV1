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
REGISTRY = HERE / "v69-dependency-registry-pilot.json"
TIERS = {"Real", "Real with honest gaps", "Deferred", "Dropped"}
APPROVALS = {"pending owner review", "owner approved"}


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
    screen_document = read(SCREENS)
    if screen_document.get("schema") != "assetops.v69.screen-ledger.v2":
        raise SystemExit("Screen ledger schema must be v2 with promotion dependencies")
    screen_ledger = screen_document["screens"]
    model_homes = read(MODELS)["models"]
    rendered_panels = read(RENDERED_PANELS)["panels"]
    panel_contracts = read(PANEL_CONTRACTS)["panels"]
    registry = read(REGISTRY)
    if registry.get("schema") != "assetops.v69.dependency-registry.pilot.v2":
        raise SystemExit("Dependency registry pilot schema must be v2")
    pilot_panels: dict[str, list[dict]] = {}
    for panel in registry["panels"]:
        pilot_panels.setdefault(panel["screen_id"], []).append(panel)
    area_for_screen: dict[str, str] = {}
    for panel in registry["panels"]:
        screen_id = panel["screen_id"]
        if screen_id in area_for_screen and area_for_screen[screen_id] != panel["area"]:
            raise SystemExit(f"{screen_id}: panels span product areas")
        area_for_screen[screen_id] = panel["area"]
    area_defaults: dict[str, str] = {}
    screen_overrides: dict[str, str] = {}
    for node in registry["nodes"]:
        if node["kind"] == "product":
            if node["scope"] == "area":
                for area in node["governs_areas"]:
                    if area in area_defaults:
                        raise SystemExit(f"{area}: multiple product defaults")
                    area_defaults[area] = node["id"]
            elif node["scope"] == "screens":
                for screen_id in node["governs"]:
                    if screen_id in screen_overrides or area_for_screen.get(screen_id) != node["area"]:
                        raise SystemExit(f"{screen_id}: invalid product override")
                    screen_overrides[screen_id] = node["id"]
            else:
                raise SystemExit(f"{node['id']}: invalid product scope")
    product_for_screen = {screen_id: screen_overrides.get(screen_id, area_defaults.get(area))
                          for screen_id, area in area_for_screen.items()}
    if any(product_id is None for product_id in product_for_screen.values()):
        raise SystemExit("Pilot screen lacks an area product default")

    exact_ids([row["id"] for row in manifest], [row["id"] for row in screen_ledger], "screens")
    expected_models = sorted({name for row in manifest for name in row["models"]})
    exact_ids(expected_models, [row["model"] for row in model_homes], "models")

    model_by_name = {row["model"]: row for row in model_homes}
    manifest_by_id = {row["id"]: row for row in manifest}
    panel_gaps: dict[str, list[str]] = {}
    for panel in panel_contracts:
        if any(str(panel[key]).startswith("GAP") for key in (
            "domain_object", "evidence_roles_or_analytic", "owning_table_or_gap"
        )):
            panel_gaps.setdefault(panel["screen_id"], []).append(panel["panel_title"])

    for row in screen_ledger:
        identifier = row["id"]
        registry_link = row.get("registry_dependencies")
        if identifier in pilot_panels:
            expected_nodes = list(dict.fromkeys(node_id for panel in pilot_panels[identifier]
                                                for node_id in panel["requires"]))
            if not registry_link or registry_link.get("product_node_id") != product_for_screen.get(identifier) or \
                    registry_link.get("node_ids") != expected_nodes:
                raise SystemExit(f"{identifier}: registry dependency IDs diverge from pilot panels")
        elif registry_link is not None:
            raise SystemExit(f"{identifier}: registry link has no pilot panels")
        if row["mock_route"] != f"#/{identifier}" or row["visual_reference"] != f"index.html#/{identifier}":
            raise SystemExit(f"{identifier}: mock route/reference mismatch")
        for key in ("product_destination", "coverage", "data_owner", "supported_claim", "interaction", "unknown_or_empty"):
            if not row.get(key):
                raise SystemExit(f"{identifier}: missing {key}")
        if row.get("proposed_fidelity_tier") not in TIERS or row.get("tier_approval") not in APPROVALS:
            raise SystemExit(f"{identifier}: fidelity tier proposal/approval is invalid")
        if row["proposed_fidelity_tier"] == "Dropped" and row["tier_approval"] != "owner approved":
            raise SystemExit(f"{identifier}: Dropped requires owner approval")
        if row["coverage"] == "deferred":
            if not row.get("follow_on") or row.get("task"):
                raise SystemExit(f"{identifier}: deferred routing is incomplete")
        elif not row.get("task"):
            raise SystemExit(f"{identifier}: bounded/partial routing lacks task")
        dependencies = row.get("promotion_dependencies")
        if not isinstance(dependencies, dict) or set(dependencies) != {"to_candidate", "to_real"}:
            raise SystemExit(f"{identifier}: missing promotion dependencies")
        candidate = dependencies["to_candidate"]
        if row["coverage"] == "deferred":
            if not isinstance(candidate, dict) or set(candidate) != {
                "architecture_decisions", "projection_contracts", "fixture_or_record_gate", "task_gate"
            } or not candidate["fixture_or_record_gate"] or not candidate["task_gate"]:
                raise SystemExit(f"{identifier}: incomplete candidate gate")
            declared = manifest_by_id[identifier]["models"]
            expected_decisions = [name for name in declared if "decision_required" in model_by_name[name]["status"]]
            expected_projections = [name for name in declared if model_by_name[name]["status"] == "projection_contract_needed"]
            if candidate["architecture_decisions"] != expected_decisions or candidate["projection_contracts"] != expected_projections:
                raise SystemExit(f"{identifier}: candidate models differ from model-home inventory")
        elif candidate is not None:
            raise SystemExit(f"{identifier}: S-task screen should have null candidate gate")
        real = dependencies["to_real"]
        if not isinstance(real, dict) or set(real) != {"unresolved_panels", "remaining_work", "acceptance"}:
            raise SystemExit(f"{identifier}: incomplete Real gate")
        if real["unresolved_panels"] != panel_gaps.get(identifier, []) or not real["remaining_work"] or not real["acceptance"]:
            raise SystemExit(f"{identifier}: Real gate does not reflect panel gaps")
        if row["proposed_fidelity_tier"] == "Real" and real["unresolved_panels"]:
            raise SystemExit(f"{identifier}: Real tier still has unresolved panels")

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
    screen_approvals = {row["id"]: row["tier_approval"] for row in screen_ledger}
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
        if row.get("proposed_fidelity_tier") not in TIERS or row.get("tier_approval") not in APPROVALS:
            raise SystemExit(f"{identifier} panel {row['panel_index']}: invalid tier/approval")
        if row["proposed_fidelity_tier"] != screen_tiers[identifier]:
            raise SystemExit(f"{identifier} panel {row['panel_index']}: screen tier mismatch")
        if row["tier_approval"] != screen_approvals[identifier]:
            raise SystemExit(f"{identifier} panel {row['panel_index']}: screen approval mismatch")
        if row["read_model_status"].startswith("manifest candidate") and not row["owning_table_or_gap"].startswith("GAP"):
            raise SystemExit(f"{identifier} panel {row['panel_index']}: unreviewed mapping claims a table")

    print(f"v6.9 ledger valid: {len(screen_ledger)} screens, {len(model_homes)} distinct models, {len(panel_contracts)} panels")


if __name__ == "__main__":
    main()
