"""S2-01a phase 1 - registered Lab basis against a disposable PostgreSQL database.

Needs `ASSETOPS_TEST_DATABASE_URL` naming a `*_test` database; skipped (never
passed) without it. Proves the selection reads the S1 registry and the pinned
`snapshot_canonical` bytes the database holds, that a historical basis
survives an allowed current registration identity edit while the current one
refuses, and that an unreachable store fails closed with no Draft.

Decision: D-2026-10-08-s2-lab-snapshot-selection-and-run-boundary.
"""

from __future__ import annotations

import os
from datetime import timedelta

import pytest

URL = os.environ.get("ASSETOPS_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(
    not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)"
)

if URL:
    from run_fixtures import FakeRuns, FakeScenarios, FakeSites
    from sqlalchemy import text
    from test_s1_bindings_postgres import CHANGE_FROM, NOW, Clock, converted, engine, store  # noqa: F401
    from test_s2_registered_basis import SCENARIO, request

    from assetops_backend.runs.adapters.yaml_run_store import YamlRunStore
    from assetops_backend.runs.profiles import DAYTIME_MINI_GRID_MODEL, LAB_PUBLICATION_PROFILE
    from assetops_backend.runs.refusals import RunSetupRefused
    from assetops_backend.runs.registered_basis import RegisteredLabBasis
    from assetops_backend.runs.service import RunSetupService
    from assetops_backend.sites.adapters.postgres_foundation_store import PostgresFoundationStore
    from assetops_backend.sites.cutover import ImportedSiteRegistry
    from assetops_backend.sites.foundation_service import FoundationService
    from assetops_backend.sites.ports import SiteStoreUnavailable

LATER = {"start_time": "2026-10-05T03:00:00Z", "end_time": "2026-10-05T15:00:00Z"}


def service(store, runs=None):
    return RunSetupService(
        runs if runs is not None else FakeRuns(),
        FakeSites(()),
        FakeScenarios((SCENARIO,)),
        model_profiles=(DAYTIME_MINI_GRID_MODEL,),
        publication_profiles=(LAB_PUBLICATION_PROFILE,),
        now=lambda: NOW.strftime("%Y-%m-%dT%H:%M:%SZ"),
        registered_bases=RegisteredLabBasis(
            ImportedSiteRegistry(FoundationService(store, "demo", Clock(NOW)))
        ),
    )


def stored_bytes(engine, binding_set_revision_id: str) -> bytes:
    with engine.connect() as connection:
        return bytes(connection.execute(
            text("SELECT snapshot_canonical FROM signal_binding_set_revision WHERE id = :id"),
            {"id": binding_set_revision_id},
        ).scalar_one())


def publish_reserve(store, result) -> None:
    FoundationService(store, "demo", Clock(NOW)).publish_battery_reserve(
        result.tenant, result.site, asset_code="battery", value=40.0, effective_from=CHANGE_FROM, note=None
    )


class TestRegisteredBasisInPostgres:
    def test_the_draft_freezes_the_stored_bytes_and_reloads_them(self, store, engine, tmp_path) -> None:
        result, outcome = converted(store)
        runs = YamlRunStore(tmp_path / "runs")
        record = service(store, runs).create_draft_run(request())
        basis = record.registered_basis
        assert basis.binding_set_revision_id == str(outcome.published.changed.id)
        assert basis.snapshot_canonical.encode("utf-8") == stored_bytes(engine, basis.binding_set_revision_id)
        assert YamlRunStore(tmp_path / "runs").get_run(record.run_id).registered_basis == basis

    def test_historical_selection_survives_a_registration_identity_edit(self, store, engine) -> None:
        result, outcome = converted(store)
        knowledge = (NOW - timedelta(minutes=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
        publish_reserve(store, result)
        with engine.begin() as connection:
            # A name edit the schema still permits on a current row
            # (carry m4). Every source is held by a binding foreign key.
            connection.execute(text(
                "UPDATE gateway SET gateway_external_id = 'renamed-gateway' WHERE site_id = :s"
            ), {"s": result.site.id})
        historical = service(store).create_draft_run(request(knowledge_at=knowledge)).registered_basis
        assert historical.selection == "HISTORICAL"
        assert historical.binding_set_revision_id == str(outcome.published.changed.id)
        assert historical.snapshot_canonical.encode("utf-8") == stored_bytes(engine, historical.binding_set_revision_id)
        assert "renamed-gateway" not in historical.snapshot_canonical
        current = service(store).create_draft_run(request(interval=LATER, foundation_version=4)).registered_basis
        assert current.selection == "CURRENT" and "renamed-gateway" not in current.snapshot_canonical

    def test_a_site_row_the_parser_refuses_is_a_typed_refusal_not_a_substitute(self, store, engine) -> None:
        result, _ = converted(store)
        with engine.begin() as connection:
            connection.execute(text("UPDATE site SET name = ' ' WHERE id = :s"), {"s": result.site.id})
        runs = FakeRuns()
        with pytest.raises(RunSetupRefused) as caught:
            service(store, runs).create_draft_run(request())
        assert caught.value.kind == "REGISTERED_BASIS_UNAVAILABLE"
        assert caught.value.reason_code == "ACQUISITION_SNAPSHOT_UNAVAILABLE"  # current basis: the gap refuses first
        assert runs.list_runs() == ()

    def test_a_later_publication_selects_a_new_basis_for_a_new_draft_only(self, store, engine, tmp_path) -> None:
        result, _ = converted(store)
        runs = YamlRunStore(tmp_path / "runs")
        first = service(store, runs).create_draft_run(request())
        publish_reserve(store, result)
        second = service(store, runs).create_draft_run(request(interval=LATER, foundation_version=4))
        assert second.registered_basis.snapshot_sha256 != first.registered_basis.snapshot_sha256
        assert YamlRunStore(tmp_path / "runs").get_run(first.run_id).registered_basis == first.registered_basis
        with pytest.raises(RunSetupRefused) as caught:
            service(store, runs).create_draft_run(request(
                interval={"start_time": "2026-10-04T12:00:00Z", "end_time": "2026-10-05T00:00:00Z"},
                foundation_version=3,
            ))
        assert caught.value.kind == "REGISTERED_BASIS_BOUNDARY"
        assert len(runs.list_runs()) == 2

    def test_an_unreachable_database_fails_closed_with_no_draft(self, store) -> None:
        converted(store)
        # The same server, a database that does not exist: refused at once,
        # where a closed port can spend minutes in connection retries.
        unreachable = PostgresFoundationStore(URL.rsplit("/", 1)[0] + "/assetops_absent_test")
        runs = FakeRuns()
        with pytest.raises(SiteStoreUnavailable):
            service(unreachable, runs).create_draft_run(request())
        assert runs.list_runs() == ()
