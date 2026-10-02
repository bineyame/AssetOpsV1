"""T025g AC6b: the run is the only join, proved in process on the shipped v2.

`D-2026-10-01-run-binds-scenario-to-site`. The shipped
`kobo-mini-grid-prolonged` v2 names no site. With the shipped mini-grid v2
model profile it:

- reaches READY on a site built from the current Kobo template, named
  GONDAR-01 here to show nothing ties the scenario to KOBO-001;
- reaches BLOCKED on a site holding the pre-T025a Kobo content, with a named
  reason for each missing generator property; the missing status source is
  recorded in the frozen identity (no `generator-status` mapping) but is not a
  blocking reason in this build (packet, Known Deviations);
- refuses a request for v1, which the store no longer holds, with the existing
  version check.

The pre-T025a site is the current template minus exactly what T025a/T025b
added (`git diff c0f49ce 0dc42c0 -- config/site-templates/kobo-mini-grid-60kw.yaml`):
four generator properties, the generator-controller's `status` signal and its
`generator-status` mapping. It records template version 1, as KOBO-001 does.
Nothing here reads `var/`.
"""

from __future__ import annotations

from typing import Any

import pytest

from assetops_backend.runs.refusals import RunSetupRefused
from kobo import component, kobo_document, kobo_draft, remove_property

PROLONGED = "kobo-mini-grid-prolonged"
START = "2026-09-22T03:00:00Z"  # 06:00 in Africa/Addis_Ababa
END = "2026-09-22T11:00:00Z"  # 14:00

#: What T025a and T025b added to the generator, each now on the current template.
T025A_GENERATOR_PROPERTIES = (
    "start-soc-threshold",
    "stop-soc-threshold",
    "start-delay",
    "generator-rated-power",
)


def current_kobo(document: dict[str, Any]) -> None:
    """A site built from the current template, under a different identity."""
    document["site_id"] = "GONDAR-01"


def pre_t025a_kobo(document: dict[str, Any]) -> None:
    """The Kobo content a site created before T025a holds."""
    for key in T025A_GENERATOR_PROPERTIES:
        remove_property(document, "generator", key)
    foundation = document["foundation"]
    for device in foundation["devices"]:
        if device["device_id"] == "generator-controller":
            device["signals"] = [
                signal for signal in device["signals"] if signal["signal_id"] != "status"
            ]
    foundation["signal_mappings"] = [
        mapping
        for mapping in foundation["signal_mappings"]
        if mapping["mapping_id"] != "generator-status"
    ]
    document["template"]["template_version"] = 1


def prolonged(site_edit, **kwargs):
    return kobo_draft(
        PROLONGED,
        site_edit=site_edit,
        model_profile="mini-grid",
        model_profile_version=2,
        timestep_minutes=5,
        start_time=START,
        end_time=END,
        **kwargs,
    )


def test_the_shipped_prolonged_scenario_is_v2_and_names_no_site() -> None:
    document = kobo_document(PROLONGED)
    assert document["version"]["scenario_version"] == 2
    assert "target_site" not in document


def test_the_pre_t025a_fixture_differs_only_in_what_t025a_added() -> None:
    """The BLOCKED proof is only as good as this fixture, so pin its shape."""
    from kobo import kobo_site
    from assetops_backend.sites.site_parsing import render_site_document

    old = render_site_document(kobo_site(pre_t025a_kobo))
    new = render_site_document(kobo_site())
    old_keys = {p["property_key"] for p in component(old, "generator")["properties"]}
    new_keys = {p["property_key"] for p in component(new, "generator")["properties"]}
    assert new_keys - old_keys == set(T025A_GENERATOR_PROPERTIES)
    assert old_keys <= new_keys
    assert len(new["foundation"]["signal_mappings"]) - len(
        old["foundation"]["signal_mappings"]
    ) == 1


def test_ready_on_a_site_built_from_the_current_template() -> None:
    run = prolonged(current_kobo)

    assert run.deterministic_identity.site.site_id == "GONDAR-01"
    assert run.execution_status == "READY", [
        (reason.kind, reason.subject) for reason in run.blocking_reasons
    ]
    lineage = run.deterministic_identity.site.template_lineage
    assert lineage is not None
    # T026 bumped the template to 3 (capability signals).
    assert (lineage.template_id, lineage.template_version) == (
        "kobo-mini-grid-60kw",
        3,
    )


def test_blocked_with_named_reasons_on_the_pre_t025a_content() -> None:
    run = prolonged(pre_t025a_kobo)

    assert run.deterministic_identity.site.site_id == "KOBO-001"
    assert run.execution_status == "BLOCKED"
    reasons = {(reason.kind, reason.subject) for reason in run.blocking_reasons}
    # Each missing generator property is named by its address.
    assert reasons == {
        ("INITIAL_VALUE_NOT_RESOLVED", "generator-rated-power@generator"),
        ("INITIAL_VALUE_NOT_RESOLVED", "generator-start-delay@generator"),
        ("INITIAL_VALUE_NOT_RESOLVED", "generator-start-soc-threshold@generator"),
        ("INITIAL_VALUE_NOT_RESOLVED", "generator-stop-soc-threshold@generator"),
    }
    lineage = run.deterministic_identity.site.template_lineage
    assert lineage is not None and lineage.template_version == 1


def test_the_missing_status_source_is_recorded_not_blocking() -> None:
    """Known deviation from AC6b's wording, recorded in the review packet.

    Run setup in this build does not block on a missing status source: the
    `status` reading is a publication-profile declaration that publishes
    nothing where the site maps no such signal, and making it a blocking reason
    would turn READY Drafts BLOCKED, which T025g's no-move contract reading
    does not allow. What the run does record is the absence: the pre-T025a
    Draft freezes no `generator-status` mapping, the current one does.
    """
    from assetops_backend.runs.provenance import frozen_inputs

    def status_rows(run):
        return [
            row
            for row in frozen_inputs(run.deterministic_identity)
            if row.field == "Mapping generator-status"
        ]

    for version in (3, 4):
        assert status_rows(prolonged(pre_t025a_kobo, publication_profile_version=version)) == []
        assert len(status_rows(prolonged(current_kobo, publication_profile_version=version))) == 1


def test_a_v1_request_is_refused_by_the_version_check() -> None:
    document = kobo_document(PROLONGED)
    from kobo import kobo_site
    from assetops_backend.runs.service import RunSetupService
    from assetops_backend.runs.profiles import MINI_GRID_V2_MODEL
    from assetops_backend.scenarios.parsing import parse_scenario_document
    from fixtures import FakeRuns, FakeScenarios, FakeSites, LAB_PUBLICATION_PROFILE

    site = kobo_site(current_kobo)
    setup = RunSetupService(
        FakeRuns(),
        FakeSites((site,)),
        FakeScenarios(
            (parse_scenario_document(document, source="shipped", origin="SHIPPED"),)
        ),
        model_profiles=(MINI_GRID_V2_MODEL,),
        publication_profiles=(LAB_PUBLICATION_PROFILE,),
        now=lambda: "2026-10-01T09:00:00Z",
    )
    with pytest.raises(RunSetupRefused) as refused:
        setup.create_draft_run(
            {
                "site_id": site.site_id,
                "foundation_version": site.foundation.version,
                "scenario_id": PROLONGED,
                "scenario_version": 1,
                "interval": {"start_time": START, "end_time": END},
                "timestep_minutes": 5,
                "seed": 1,
                "model_profile": {"profile_id": "mini-grid", "profile_version": 2},
                "publication_profile": {
                    "profile_id": LAB_PUBLICATION_PROFILE.publication_profile_id,
                    "profile_version": LAB_PUBLICATION_PROFILE.publication_profile_version,
                },
                "run_inputs": [],
            }
        )
    assert refused.value.kind == "VERSION_UNAVAILABLE"
