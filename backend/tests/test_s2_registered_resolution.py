"""S2-01b phase 3a: `registered-kobo-publication` v1 at run setup.

`D-2026-10-08-s2-simulated-device-resolution-and-delay-boundary`: a new,
explicitly selected publication profile declares a 0.000001 simulated device
resolution on each numeric signal in its source unit. Run setup freezes those
resolutions into the Draft's identity, refuses them for a Site with no
registered basis and refuses a declared unit the registered binding does not
publish. Earlier profiles and the Drafts frozen against them are unchanged.
"""

from __future__ import annotations

from dataclasses import replace

import pytest
from run_fixtures import FakeRuns, FakeScenarios, FakeSites
from test_s1_cutover import Clock
from test_s2_registered_basis import NOW, SCENARIO, converted, request, text

from assetops_backend.runs.parsing import parse_run_document, render_run_document
from assetops_backend.runs.ports import RunConfigurationInvalid
from assetops_backend.runs.profiles import (
    DAYTIME_MINI_GRID_MODEL,
    LAB_PUBLICATION_PROFILE,
    LAB_PUBLICATION_PROFILE_V4,
    LAB_PUBLICATION_PROFILE_V5,
    PUBLICATION_PROFILES,
    REGISTERED_KOBO_PUBLICATION_PROFILE,
    find_publication_profile,
)
from assetops_backend.runs.refusals import RunSetupRefused
from assetops_backend.runs.registered_basis import RegisteredLabBasis
from assetops_backend.runs.service import RunSetupService
from assetops_backend.sites.cutover import ImportedSiteRegistry
from assetops_backend.sites.foundation_service import FoundationService

PROFILE = REGISTERED_KOBO_PUBLICATION_PROFILE
SELECTED = {
    "publication_profile": {
        "profile_id": PROFILE.publication_profile_id,
        "profile_version": PROFILE.publication_profile_version,
    }
}


def setup_service(store, publication=PROFILE, runs=None) -> RunSetupService:
    registry = ImportedSiteRegistry(FoundationService(store, "demo", Clock(NOW)))
    return RunSetupService(
        runs if runs is not None else FakeRuns(),
        FakeSites(()),
        FakeScenarios((SCENARIO,)),
        model_profiles=(DAYTIME_MINI_GRID_MODEL,),
        publication_profiles=(LAB_PUBLICATION_PROFILE, publication),
        now=lambda: text(NOW),
        registered_bases=RegisteredLabBasis(registry),
    )


def registered_draft(publication=PROFILE):
    store, _, _ = converted()
    return setup_service(store, publication).create_draft_run(
        request(
            publication_profile={
                "profile_id": publication.publication_profile_id,
                "profile_version": publication.publication_profile_version,
            }
        )
    )


def unit_mismatch_refusal() -> RunSetupRefused:
    """A profile stating the state of charge in a unit the binding does not publish."""
    mismatched = replace(
        PROFILE,
        device_signals=tuple(
            replace(d, canonical_unit="ratio")
            if d.signal_key == ("battery-pcs-controller", "state-of-charge")
            else d
            for d in PROFILE.device_signals
        ),
    )
    store, _, _ = converted()
    runs = FakeRuns()
    with pytest.raises(RunSetupRefused) as caught:
        setup_service(store, mismatched, runs).create_draft_run(request(**SELECTED))
    assert runs.list_runs() == (), "a refused setup allocated a Draft"
    return caught.value


def legacy_site_refusal() -> RunSetupRefused:
    """The profile selected against a legacy YAML Site, which has no binding to check."""
    from test_run_setup import refuse, setup_request

    return refuse(
        setup_request(
            publication_profile={
                "profile_id": PROFILE.publication_profile_id,
                "profile_version": PROFILE.publication_profile_version,
            }
        ),
        publication=PROFILE,
    )[0]


class TestTheProfileCatalog:
    def test_the_new_profile_is_selectable_by_its_own_identity(self) -> None:
        assert find_publication_profile(PUBLICATION_PROFILES, "registered-kobo-publication", 1) is PROFILE
        assert find_publication_profile(PUBLICATION_PROFILES, "simulator-lab-publication", 6) is None

    def test_every_numeric_signal_declares_the_six_place_resolution(self) -> None:
        numeric = [d for d in PROFILE.device_signals if d.canonical_unit != "state"]
        assert numeric, "the profile declares no numeric signal, so this proves nothing"
        assert {d.resolution for d in numeric} == {"0.000001"}
        # Everything else is v3's, so only the published resolution differs.
        assert [replace(d, resolution=None) for d in PROFILE.device_signals] == list(
            LAB_PUBLICATION_PROFILE.device_signals
        )

    def test_earlier_profiles_declare_no_resolution(self) -> None:
        for profile in (LAB_PUBLICATION_PROFILE, LAB_PUBLICATION_PROFILE_V4, LAB_PUBLICATION_PROFILE_V5):
            assert all(d.resolution is None for d in profile.device_signals)

    def test_an_enum_signal_refuses_a_resolution(self) -> None:
        status = LAB_PUBLICATION_PROFILE_V4.device_signal("generator-controller", "status")
        assert status is not None and status.canonical_unit == "state"
        with pytest.raises(ValueError, match="no device resolution applies"):
            replace(status, resolution="0.000001")

    @pytest.mark.parametrize("bad", ["0", "-0.000001", "1/3", "", "x"])
    def test_a_resolution_is_a_positive_finite_decimal(self, bad) -> None:
        soc = PROFILE.device_signal("battery-pcs-controller", "state-of-charge")
        with pytest.raises(ValueError):
            replace(soc, resolution=bad)


class TestARegisteredDraftFreezesTheResolution:
    def test_the_draft_freezes_one_resolution_per_numeric_signal_in_its_unit(self) -> None:
        run = registered_draft()
        frozen = run.deterministic_identity.signal_resolutions
        assert run.execution_status == "READY"
        assert [(r.device_id, r.signal_id, r.unit, r.resolution) for r in frozen] == [
            (d.device_id, d.signal_id, d.canonical_unit, "0.000001") for d in PROFILE.device_signals
        ]
        assert run.deterministic_identity.profiles.publication_profile_id == "registered-kobo-publication"

    def test_the_frozen_resolution_round_trips_and_is_shown_as_provenance(self) -> None:
        from assetops_backend.runs.provenance import frozen_inputs

        run = registered_draft()
        document = render_run_document(run)
        assert document["deterministic_identity"]["signal_resolutions"][0] == {
            "device_id": "fuel-level-sensor",
            "signal_id": "fuel-level",
            "unit": "L",
            "resolution": "0.000001",
        }
        assert parse_run_document(document, source="test") == run
        rows = [r for r in frozen_inputs(run.deterministic_identity) if r.identity_field == "signal_resolutions"]
        assert len(rows) == len(PROFILE.device_signals)
        assert all(r.answered_by == "PUBLICATION_PROFILE" for r in rows)

    def test_a_v3_registered_draft_freezes_none_and_writes_no_key(self) -> None:
        run = registered_draft(LAB_PUBLICATION_PROFILE)
        assert run.deterministic_identity.signal_resolutions == ()
        document = render_run_document(run)
        assert "signal_resolutions" not in document["deterministic_identity"]
        assert parse_run_document(document, source="test") == run

    def test_a_stored_empty_list_is_not_a_document_this_build_wrote(self) -> None:
        document = render_run_document(registered_draft())
        document["deterministic_identity"]["signal_resolutions"] = []
        with pytest.raises(RunConfigurationInvalid, match="never an empty list"):
            parse_run_document(document, source="test")

    def test_a_stored_resolution_that_is_not_a_positive_decimal_refuses(self) -> None:
        document = render_run_document(registered_draft())
        document["deterministic_identity"]["signal_resolutions"][0]["resolution"] = "1/3"
        with pytest.raises(RunConfigurationInvalid, match="finite decimal"):
            parse_run_document(document, source="test")


class TestSetupRefusesWhatItCannotFreeze:
    def test_a_declared_unit_the_binding_does_not_publish_refuses(self) -> None:
        refused = unit_mismatch_refusal()
        assert refused.kind == "PUBLICATION_UNIT_MISMATCH"
        assert "battery-pcs-controller/state-of-charge declares 'ratio'" in str(refused)
        assert "binding publishes '%'" in str(refused)

    def test_a_legacy_site_cannot_select_the_profile(self) -> None:
        refused = legacy_site_refusal()
        assert refused.kind == "PUBLICATION_PROFILE_REQUIRES_REGISTERED_SITE"
