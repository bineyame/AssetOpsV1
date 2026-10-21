"""T028 AC18/AC19: the presentation profile against the backend declaration.

The profile (`frontend/src/sites/presentationProfiles.json`) may only label,
order, group and emphasise capability ids the backend declares. Rule 2: a
profile id the backend does not serve renders nothing in the UI (tested in
`frontend/src/shell/__tests__/overviewDispatchAssessment.test.tsx`), and this
test flags it here, unless it is a planned id listed below with its owning
slice. Each analytic slice removes its id from the list when it lands.
"""

from __future__ import annotations

import json
from pathlib import Path

from assetops_backend.analytics.declaration import DECLARATIONS, applicable
from assetops_backend.analytics.service import AssessmentService

PROFILES = Path(__file__).resolve().parents[2] / "frontend" / "src" / "sites" / "presentationProfiles.json"

#: Planned profile capability ids no analytic declares yet, per Site type, with
#: the slice that owns each. W4-02 (S6): the four mini-depth tabs are served by
#: `/performance/mini/capabilities`, not by an AnalyticDeclaration.
EXPECTED_ORPHANS: dict[str, dict[str, str]] = {
    "MINIGRID": {"service": "W4-02", "fuel": "W4-02", "renewable": "W4-02", "backup": "W4-02"},
}

CAPABILITY_KEYS = {"id", "label", "order", "group", "emphasis"}


def _profiles() -> dict:
    return json.loads(PROFILES.read_text(encoding="utf-8"))


def _orphans(site_type: str, profile: dict) -> set[str]:
    served = {d.analytic_id for d in applicable(site_type)}
    return {entry["id"] for entry in profile.get("capabilities", [])} - served


def test_capability_entries_are_presentation_only() -> None:
    for profile in _profiles().values():
        for entry in profile.get("capabilities", []):
            assert set(entry) == CAPABILITY_KEYS, entry
            assert entry["emphasis"] in {"primary", "default"}


def test_no_unexpected_orphan_capability_ids() -> None:
    for site_type, profile in _profiles().items():
        orphans = _orphans(site_type, profile)
        expected = set(EXPECTED_ORPHANS.get(site_type, {}))
        assert orphans - expected == set(), (
            f"{site_type}: profile capability ids no analytic declares: "
            f"{sorted(orphans - expected)}. Declare the analytic, or list the id "
            "with its owning slice in EXPECTED_ORPHANS."
        )
        assert expected - orphans == set(), (
            f"{site_type}: EXPECTED_ORPHANS lists ids that are now served or "
            f"no longer in the profile: {sorted(expected - orphans)}; remove them."
        )


def test_the_orphan_check_flags_an_unserved_id() -> None:
    profile = {"capabilities": [{"id": "dispatch"}, {"id": "renewable"}]}
    assert _orphans("MINIGRID", profile) == {"renewable"}
    assert _orphans("NO_SUCH_TYPE", profile) == {"dispatch", "renewable"}


def test_the_card_slot_names_a_declared_capability() -> None:
    declared = {d.analytic_id for d in DECLARATIONS}
    profiled = {
        entry["id"]
        for profile in _profiles().values()
        for entry in profile.get("capabilities", [])
    }
    assert "dispatch" in declared
    assert "dispatch" in profiled
    # The Overview card slot is filled from the service, which names the
    # declaration's id, never a profile id.
    source = Path(AssessmentService.card_assessments.__code__.co_filename).read_text(encoding="utf-8")
    assert '"capability_id": DISPATCH.analytic_id' in source


# --- T028 phase 2: Finding types (AC18 rule 2, AC19) ---------------------------

#: Planned profile Finding type ids no analytic emits yet, per Site type, with
#: the owning slice. Empty: the profile names only the dispatch Finding type.
EXPECTED_ORPHAN_FINDING_TYPES: dict[str, dict[str, str]] = {"MINIGRID": {}}

FINDING_TYPE_KEYS = {"id", "label"}


def _orphan_finding_types(site_type: str, profile: dict) -> set[str]:
    served = {d.finding_type for d in applicable(site_type)}
    return {entry["id"] for entry in profile.get("finding_types", [])} - served


def test_finding_type_entries_are_presentation_only() -> None:
    for profile in _profiles().values():
        for entry in profile.get("finding_types", []):
            assert set(entry) == FINDING_TYPE_KEYS, entry


def test_no_unexpected_orphan_finding_types() -> None:
    for site_type, profile in _profiles().items():
        orphans = _orphan_finding_types(site_type, profile)
        expected = set(EXPECTED_ORPHAN_FINDING_TYPES.get(site_type, {}))
        assert orphans - expected == set(), (
            f"{site_type}: profile Finding types no analytic emits: "
            f"{sorted(orphans - expected)}. Declare the analytic, or list the id "
            "with its owning slice in EXPECTED_ORPHAN_FINDING_TYPES."
        )
        assert expected - orphans == set(), sorted(expected - orphans)


def test_a_listed_planned_id_passes_and_an_unlisted_one_fails() -> None:
    """AC19: the expected-orphan list is what separates planned from drift."""
    profile = {"capabilities": [{"id": "dispatch"}, {"id": "renewable"}]}
    orphans = _orphans("MINIGRID", profile)
    assert orphans - {"renewable"} == set()  # listed (e.g. Renewable, T031): passes
    assert orphans - set() == {"renewable"}  # unlisted: flagged
    types = {"finding_types": [{"id": "generator-dispatch-interval"}, {"id": "fuel-residual"}]}
    assert _orphan_finding_types("MINIGRID", types) == {"fuel-residual"}
