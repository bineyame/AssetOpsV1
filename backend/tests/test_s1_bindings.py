"""S1-02 bindings, Readiness and snapshot - default suite, no database.

Runs over `InMemoryFoundationStore`. PostgreSQL's own guarantees (exclusion
constraints, same-Site foreign keys, immutability triggers, migration 0002)
are tested in `test_s1_bindings_postgres.py`.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import replace
from uuid import uuid4
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from foundation_fakes import InMemoryFoundationStore
from test_s1_cutover import NOW, Clock, app_for, do_import, legacy_root  # noqa: F401

from assetops_backend.sites.adapters.import_files import read_import_source
from assetops_backend.sites.binding_conversion import ConversionConflict, convert
from assetops_backend.sites.binding_service import BindingService
from assetops_backend.sites.foundation_records import (
    BindingOverlap,
    ConfigurationPlan,
)

BACKEND = Path(__file__).resolve().parents[1]
FIXTURE = json.loads((BACKEND / "conversions" / "kobo-001-bindings.json").read_text(encoding="utf-8"))
ORIGINAL_FROM = datetime(2026, 9, 29, 11, 57, 49, tzinfo=timezone.utc)
CONVERTED_AT = NOW - timedelta(minutes=30)
REMOVED_FROM = "2026-10-05T00:00:00Z"
BEFORE_REMOVAL = "2026-10-04T00:00:00Z"
REQUIRED = {"generator_state", "generator_power", "feeder_demand", "battery_soc", "battery_reserve"}


def converted(store=None, fixture=FIXTURE):
    store = store or InMemoryFoundationStore()
    result = do_import(store)
    service = BindingService(store, Clock(CONVERTED_AT))
    outcome = convert(store, service, result.tenant, result.site, fixture)
    return store, result, outcome


def wire(mappings, drop=()):
    return [
        {
            "device_id": m["device_id"], "signal_id": m["signal_id"], "asset_id": m["asset_id"],
            "role": m["role"], "source_unit": m["source_unit"], "canonical_unit": m["canonical_unit"],
            "conversion": m["conversion"],
        }
        for m in mappings
        if (m["device_id"], m["signal_id"]) not in drop
    ]


def snapshot_hash(client, **query):
    response = client.get("/api/sites/KOBO-001/foundation/snapshot", params=query)
    assert response.status_code == 200, response.text
    assert hashlib.sha256(response.content).hexdigest() == response.headers["X-AssetOps-Snapshot-SHA256"]
    return response.headers["X-AssetOps-Snapshot-SHA256"], response.json()


class TestBeforeConversion:
    def test_no_binding_set_is_unknown_and_unbound_with_no_snapshot(self, legacy_root) -> None:
        store = InMemoryFoundationStore()
        do_import(store)
        client = app_for(store, legacy_root)
        body = client.get("/api/sites/KOBO-001/foundation").json()
        assert body["bindings"]["state"] == "NONE" and body["bindings"]["mappings"] == []
        assert body["readiness"]["state"] == "UNKNOWN"
        statuses = {r["role"]: r["status"] for r in body["readiness"]["roles"]}
        assert statuses["generator_state"] == "UNBOUND" and statuses["battery_soc"] == "UNBOUND"
        assert statuses["battery_reserve"] == "CONFIGURED"  # the Foundation control (Q3 proposal)
        assert all(c["status"] == "UNBOUND" for c in body["readiness"]["channels"])
        assert body["acquisition_snapshot"]["available"] is False
        refused = client.get("/api/sites/KOBO-001/foundation/snapshot")
        assert refused.status_code == 409
        assert refused.json()["detail"]["code"] == "ACQUISITION_SNAPSHOT_UNAVAILABLE"
        text = json.dumps(body["readiness"]).lower()
        assert "healthy" not in text.replace("not mean any device is connected, reporting or healthy", "")


class TestConversion:
    def test_first_conversion_is_one_atomic_foundation_plus_binding_publish(self) -> None:
        store, result, outcome = converted()
        assert outcome.created
        plan = outcome.published.plan
        # The generator status signal is declared jointly with its binding.
        assert [r.version for r in plan.revision_inserts] == [2]
        assert plan.supersede_revision_ids == (result.revision.id,)
        assert any(
            s["signal_id"] == "status"
            for d in plan.revision_inserts[0].content["devices"] if d["device_id"] == "generator-controller"
            for s in d["signals"]
        )
        changed = outcome.published.changed
        assert (changed.version, changed.origin, changed.valid_from, changed.valid_to) == (
            1, "CONVERSION", ORIGINAL_FROM, None
        )
        assert len(changed.bindings) == 10
        # The legacy mappings remain in Foundation content as comparison data.
        assert len(plan.revision_inserts[0].content["signal_mappings"]) == 9

    def test_a_rerun_writes_nothing(self) -> None:
        store, result, _ = converted()
        before = (len(store.rows[result.site.id]), len(store.sets[result.site.id]))
        again = convert(store, BindingService(store, Clock(NOW)), result.tenant, result.site, FIXTURE)
        assert again.created is False
        assert (len(store.rows[result.site.id]), len(store.sets[result.site.id])) == before

    def test_an_unconverted_legacy_mapping_is_refused(self) -> None:
        fixture = {**FIXTURE, "bindings": [b for b in FIXTURE["bindings"] if b["legacy_mapping_id"] != "fuel-tank-level"]}
        store = InMemoryFoundationStore()
        result = do_import(store)
        with pytest.raises(ConversionConflict, match="fuel-tank-level"):
            convert(store, BindingService(store, Clock(CONVERTED_AT)), result.tenant, result.site, fixture)
        assert store.sets.get(result.site.id, []) == []

    def test_a_refused_binding_writes_no_joint_foundation_change_either(self) -> None:
        bad = [dict(b) for b in FIXTURE["bindings"]]
        bad[3] = {**bad[3], "canonical_unit": "fraction"}  # battery SOC
        store = InMemoryFoundationStore()
        result = do_import(store)
        with pytest.raises(ConversionConflict, match="BINDING_UNIT_MISMATCH"):
            convert(store, BindingService(store, Clock(CONVERTED_AT)), result.tenant, result.site,
                    {**FIXTURE, "bindings": bad})
        assert [r.version for r in store.rows[result.site.id]] == [1]
        assert store.rows[result.site.id][0].superseded_at is None


class TestReadAndTrace:
    def test_generator_status_and_battery_soc_trace_to_source_asset_role_and_revisions(self, legacy_root) -> None:
        store, result, outcome = converted()
        client = app_for(store, legacy_root)
        body = client.get("/api/sites/KOBO-001/foundation").json()
        assert body["readiness"]["state"] == "READY_TO_REPORT"
        assert body["readiness"]["missing_roles"] == []
        assert {r["role"] for r in body["readiness"]["roles"] if r["required"] and r["status"] == "CONFIGURED"} == REQUIRED
        sources = {s["source_external_id"]: s["source_id"] for s in body["sources"]}
        assets = {a["asset_code"]: a["asset_id"] for a in body["assets"]}
        by_channel = {(m["device_id"], m["signal_id"]): m for m in body["bindings"]["mappings"]}
        status = by_channel[("generator-controller", "status")]
        soc = by_channel[("battery-pcs-controller", "state-of-charge")]
        assert (status["role"], status["source_unit"], status["canonical_unit"]) == ("generator_state", "state", "state")
        assert status["source_id"] == sources["generator-controller"]
        assert status["asset_id"] == assets["generator"]
        assert (soc["role"], soc["asset_code"], soc["source_unit"]) == ("battery_soc", "battery", "%")
        assert soc["source_id"] == sources["battery-pcs-controller"]
        assert body["bindings"]["binding_set"]["binding_set_revision_id"] == str(outcome.published.changed.id)
        assert body["revision"]["version"] == 2
        assert body["acquisition_snapshot"]["available"] is True
        sha, document = snapshot_hash(client)
        assert sha == body["acquisition_snapshot"]["sha256"]
        assert document["foundation"]["revision_id"] == body["revision"]["revision_id"]
        snap = {(b["device_id"], b["signal_id"]): b for b in document["bindings"]}
        assert snap[("generator-controller", "status")]["binding_revision_id"] == status["binding_revision_id"]
        # Reload gives the same bytes.
        assert snapshot_hash(client)[0] == sha

    def test_versions_list_names_binding_set_versions(self, legacy_root) -> None:
        store, _, _ = converted()
        body = app_for(store, legacy_root).get("/api/sites/KOBO-001/foundation/versions").json()
        assert [(b["version"], b["origin"]) for b in body["binding_sets"]] == [(1, "CONVERSION")]


class TestBindingChange:
    def test_removing_a_required_binding_names_the_role_and_history_is_recoverable(self, legacy_root) -> None:
        store, _, _ = converted()
        client = app_for(store, legacy_root)
        before = client.get("/api/sites/KOBO-001/foundation").json()
        old_sha, _ = snapshot_hash(client, at=BEFORE_REMOVAL)
        response = client.post(
            "/api/sites/KOBO-001/foundation/bindings",
            json={
                "valid_from": REMOVED_FROM,
                "bindings": wire(before["bindings"]["mappings"], drop={("battery-pcs-controller", "state-of-charge")}),
                "note": "SOC channel removed",
            },
        )
        assert response.status_code == 201, response.text
        published = response.json()
        assert [b["origin"] for b in published["inserted_binding_sets"]] == ["SPLIT", "PUBLISH"]
        now = client.get("/api/sites/KOBO-001/foundation").json()
        assert now["readiness"]["state"] == "INCOMPLETE"
        assert now["readiness"]["missing_roles"] == ["Battery state of charge"]
        soc_channel = next(
            c for c in now["readiness"]["channels"]
            if (c["device_id"], c["signal_id"]) == ("battery-pcs-controller", "state-of-charge")
        )
        assert soc_channel["status"] == "UNBOUND"
        # An earlier time still shows the old mapping (from the split copy).
        earlier = client.get("/api/sites/KOBO-001/foundation", params={"at": BEFORE_REMOVAL}).json()
        assert earlier["readiness"]["state"] == "READY_TO_REPORT"
        # The original basis and snapshot hash are recovered at the earlier knowledge time.
        knowledge = (NOW - timedelta(minutes=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
        recovered, _ = snapshot_hash(client, at=BEFORE_REMOVAL, knowledge_at=knowledge)
        assert recovered == old_sha
        versions = client.get("/api/sites/KOBO-001/foundation/versions").json()["binding_sets"]
        assert [(b["version"], b["recorded_state"]) for b in versions] == [
            (1, "SUPERSEDED"), (2, "CURRENT"), (3, "CURRENT")
        ]


class TestRefusals:
    def _post(self, client, bindings):
        return client.post(
            "/api/sites/KOBO-001/foundation/bindings", json={"valid_from": REMOVED_FROM, "bindings": bindings}
        )

    def _current(self, client):
        return client.get("/api/sites/KOBO-001/foundation").json()["bindings"]["mappings"]

    @pytest.mark.parametrize(
        "change, code",
        [
            (lambda rows: rows[0].update(canonical_unit="W") or rows, "BINDING_UNIT_MISMATCH"),
            (lambda rows: rows[0].update(source_unit="W") or rows, "BINDING_UNIT_MISMATCH"),
            (lambda rows: rows + [dict(rows[0])], "BINDING_CHANNEL_OVERLAP"),
            (lambda rows: rows[0].update(role="no_such_role") or rows, "BINDING_ROLE_UNKNOWN"),
            (lambda rows: rows[0].update(device_id="unregistered-meter") or rows, "BINDING_SOURCE_UNKNOWN"),
        ],
    )
    def test_each_refusal_is_atomic(self, legacy_root, change, code) -> None:
        store, result, _ = converted()
        client = app_for(store, legacy_root)
        sets_before = list(store.sets[result.site.id])
        response = self._post(client, change(wire(self._current(client))))
        assert response.status_code == 422
        assert response.json()["detail"]["code"] == code
        assert store.sets[result.site.id] == sets_before

    def test_another_sites_asset_is_refused(self, legacy_root, tmp_path) -> None:
        store, result, _ = converted()
        other_file = tmp_path / "kobo-002.yaml"
        other_file.write_text(
            (BACKEND / "tests" / "fixtures" / "s1" / "kobo-001.yaml").read_text(encoding="utf-8")
            .replace("site_id: KOBO-001", "site_id: KOBO-002"),
            encoding="utf-8",
        )
        other = do_import(store, read_import_source(str(other_file)))
        foreign = next(a for a in other.registrations.assets if a.asset_code == "battery")
        client = app_for(store, legacy_root)
        rows = wire(self._current(client))
        soc = next(r for r in rows if r["role"] == "battery_soc")
        soc["asset_id"] = str(foreign.id)
        sets_before = list(store.sets[result.site.id])
        response = self._post(client, rows)
        assert response.status_code == 422
        assert response.json()["detail"]["code"] == "BINDING_ASSET_UNKNOWN"
        assert store.sets[result.site.id] == sets_before

    def test_an_overlapping_current_set_is_refused_by_the_store(self) -> None:
        store, result, outcome = converted()
        current = outcome.published.changed

        def planner(state):
            # A second current set revision over the same period: the schema's
            # exclusion constraint refuses it, and so does the fake.
            return ConfigurationPlan(NOW, (), (), (), (replace(current, id=uuid4()),))

        with pytest.raises(BindingOverlap):
            store.publish_configuration(result.tenant.id, result.site.id, planner)

    def test_gap_fixture_has_no_snapshot_even_when_bound(self, tmp_path) -> None:
        text_ = (BACKEND / "tests" / "fixtures" / "s1" / "kobo-001.yaml").read_text(encoding="utf-8")
        start = text_.index("    - property_key: reserve-state-of-charge")
        end = text_.index("  - component_id: battery-pcs")
        gap_file = tmp_path / "kobo-gap-001.yaml"
        gap_file.write_text((text_[:start] + text_[end:]).replace("site_id: KOBO-001", "site_id: KOBO-GAP-001"), encoding="utf-8"
        )
        store = InMemoryFoundationStore()
        result = do_import(store, read_import_source(str(gap_file)))
        convert(store, BindingService(store, Clock(CONVERTED_AT)), result.tenant, result.site,
                {**FIXTURE, "site_code": "KOBO-GAP-001"})
        body = app_for(store, tmp_path, legacy_documents=lambda: ()).get("/api/sites/KOBO-GAP-001/foundation").json()
        assert body["readiness"]["missing_roles"] == ["Battery reserve"]
        assert body["readiness"]["state"] == "INCOMPLETE"
        assert [g["code"] for g in body["readiness"]["foundation_gaps"]] == ["BATTERY_RESERVE_MISSING"]
        assert body["acquisition_snapshot"]["available"] is False
        assert "BATTERY_RESERVE_MISSING" in body["acquisition_snapshot"]["reason"]


# --- decision D-2026-10-08-s1-bindings-roles-and-snapshot -----------------------


class TestDecisionQ4Conversions:
    def test_linear_is_refused_at_publication(self, legacy_root) -> None:
        store, result, _ = converted()
        client = app_for(store, legacy_root)
        rows = wire(client.get("/api/sites/KOBO-001/foundation").json()["bindings"]["mappings"])
        power = next(r for r in rows if r["role"] == "generator_power")
        power["conversion"] = {"kind": "LINEAR", "parameters": {"scale": "1", "offset": "0"}}
        sets_before = list(store.sets[result.site.id])
        response = client.post(
            "/api/sites/KOBO-001/foundation/bindings", json={"valid_from": REMOVED_FROM, "bindings": rows}
        )
        assert response.status_code == 422
        assert response.json()["detail"]["code"] == "BINDING_CONVERSION_INVALID"
        assert "only IDENTITY and ENUM" in response.json()["detail"]["message"]
        assert store.sets[result.site.id] == sets_before


class TestDecisionQ5AlignedPeriods:
    def _reserve(self, client, value, valid_from):
        response = client.post(
            "/api/sites/KOBO-001/foundation/revisions",
            json={"asset_code": "battery", "property_key": "reserve-state-of-charge", "unit": "%",
                  "value": value, "valid_from": valid_from},
        )
        assert response.status_code == 201, response.text

    def test_conversion_publishes_one_binding_set_per_foundation_period(self, legacy_root) -> None:
        store = InMemoryFoundationStore()
        result = do_import(store)
        # A scheduled reserve change before conversion: two Foundation periods.
        self._reserve(app_for(store, legacy_root, clock=Clock(NOW - timedelta(minutes=45))), 25, "2026-10-10T00:00:00Z")
        outcome = convert(store, BindingService(store, Clock(CONVERTED_AT)), result.tenant, result.site, FIXTURE)
        pieces = outcome.published.published
        assert [(p.valid_from, p.valid_to) for p in pieces] == [
            (ORIGINAL_FROM, datetime(2026, 10, 10, tzinfo=timezone.utc)),
            (datetime(2026, 10, 10, tzinfo=timezone.utc), None),
        ]
        current = {r.id: r for r in store.rows[result.site.id] if r.superseded_at is None}
        for piece in pieces:
            anchor = current[piece.foundation_revision_id]
            assert anchor.valid_from <= piece.valid_from
            assert any(s["signal_id"] == "status" for d in anchor.content["devices"] for s in d["signals"])
        assert len({p.snapshot_sha256 for p in pieces}) == 2

    def test_a_later_reserve_change_realigns_bindings_and_keeps_the_old_snapshot(self, legacy_root) -> None:
        store, result, outcome = converted()
        client = app_for(store, legacy_root)
        old_sha, _ = snapshot_hash(client, at=BEFORE_REMOVAL)
        knowledge = (NOW - timedelta(minutes=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
        self._reserve(client, 40, REMOVED_FROM)
        current_sets = [s for s in store.sets[result.site.id] if s.superseded_at is None]
        current_rows = {r.id: r for r in store.rows[result.site.id] if r.superseded_at is None}
        assert len(current_sets) == 2
        assert all(s.foundation_revision_id in current_rows for s in current_sets)
        assert all(s.origin == "SPLIT" for s in current_sets)
        later = client.get("/api/sites/KOBO-001/foundation").json()
        assert later["readiness"]["state"] == "READY_TO_REPORT"
        assert later["acquisition_snapshot"]["foundation_revision_id"] == later["revision"]["revision_id"]
        recovered, _ = snapshot_hash(client, at=BEFORE_REMOVAL, knowledge_at=knowledge)
        assert recovered == old_sha

    def test_before_conversion_knowledge_reads_the_foundation_only_basis(self, legacy_root) -> None:
        store, _, _ = converted()
        client = app_for(store, legacy_root)
        knowledge = (CONVERTED_AT - timedelta(minutes=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
        before = client.get("/api/sites/KOBO-001/foundation", params={"knowledge_at": knowledge}).json()
        assert before["bindings"]["state"] == "NONE"
        assert before["readiness"]["state"] == "UNKNOWN"
        assert before["revision"]["version"] == 1


class TestDecisionQ6PinnedSnapshot:
    def test_the_published_hash_is_persisted_and_the_download_verifies_it(self, legacy_root) -> None:
        store, result, outcome = converted()
        pinned = outcome.published.changed
        assert pinned.snapshot_schema == "assetops.acquisition-snapshot/1"
        client = app_for(store, legacy_root)
        response = client.get("/api/sites/KOBO-001/foundation/snapshot")
        assert response.headers["X-AssetOps-Snapshot-SHA256"] == pinned.snapshot_sha256
        assert hashlib.sha256(response.content).hexdigest() == pinned.snapshot_sha256
        assert response.headers["X-AssetOps-Snapshot-Schema"] == "assetops.acquisition-snapshot/1"
        assert response.headers["X-AssetOps-Access"] == "development-tenant; gateway-authentication-pending"
        document = response.json()
        assert document["tenant_id"] == str(result.tenant.id)
        assert document["mapping"]["binding_set_revision_id"] == str(pinned.id)
        assert "recorded_at" not in json.dumps(document) and "superseded_at" not in json.dumps(document)
        summary = client.get("/api/sites/KOBO-001/foundation").json()["acquisition_snapshot"]
        assert "gateway authentication is pending" in summary["access"].lower()

    def test_a_stored_hash_that_the_bytes_do_not_reproduce_is_refused(self, legacy_root) -> None:
        store, result, outcome = converted()
        store.sets[result.site.id] = [
            replace(s, snapshot_sha256="0" * 64) if s.id == outcome.published.changed.id else s
            for s in store.sets[result.site.id]
        ]
        response = app_for(store, legacy_root).get("/api/sites/KOBO-001/foundation/snapshot")
        assert response.status_code == 500
        assert response.json()["detail"]["code"] == "ACQUISITION_SNAPSHOT_HASH_MISMATCH"


# --- S1-02 fix round (Codex review) ----------------------------------------------


def _with_gateway(store, site_id, **changes):
    regs = store.registered[site_id]
    store.registered[site_id] = replace(regs, gateways=tuple(replace(g, **changes) for g in regs.gateways))


class TestReviewM1HistoricalBytes:
    """The download serves the bytes kept at publication, not a rebuild from registrations."""

    def _download(self, client, **query):
        response = client.get("/api/sites/KOBO-001/foundation/snapshot", params=query)
        assert response.status_code == 200, response.text
        return response.content, response.headers["X-AssetOps-Snapshot-SHA256"]

    def test_the_published_bytes_are_kept_on_the_row(self) -> None:
        _, _, outcome = converted()
        pinned = outcome.published.changed
        assert pinned.snapshot_canonical
        assert hashlib.sha256(pinned.snapshot_canonical).hexdigest() == pinned.snapshot_sha256

    def test_an_operational_registration_update_keeps_bytes_and_hash(self, legacy_root) -> None:
        store, result, outcome = converted()
        client = app_for(store, legacy_root)
        body, sha = self._download(client)
        _with_gateway(store, result.site.id, credential_ref="vault://rotated", disabled_at=NOW)
        assert self._download(client) == (body, sha)
        assert sha == outcome.published.changed.snapshot_sha256

    def test_an_identity_registration_update_does_not_change_an_old_download(self, legacy_root) -> None:
        store, result, outcome = converted()
        client = app_for(store, legacy_root)
        body, sha = self._download(client)
        _with_gateway(store, result.site.id, gateway_external_id="renamed-gateway", mode="LIVE")
        again, again_sha = self._download(client)
        # Same bytes, and the hash is the one stored at publication - never recomputed.
        assert (again, again_sha) == (body, sha) == (
            outcome.published.changed.snapshot_canonical, outcome.published.changed.snapshot_sha256
        )
        assert b"renamed-gateway" not in again

    def test_stored_bytes_that_do_not_hash_to_the_pinned_value_are_refused(self, legacy_root) -> None:
        store, result, outcome = converted()
        store.sets[result.site.id] = [
            replace(s, snapshot_canonical=s.snapshot_canonical + b" ") if s.id == outcome.published.changed.id else s
            for s in store.sets[result.site.id]
        ]
        response = app_for(store, legacy_root).get("/api/sites/KOBO-001/foundation/snapshot")
        assert response.status_code == 500
        assert response.json()["detail"]["code"] == "ACQUISITION_SNAPSHOT_HASH_MISMATCH"


KOBO_YAML = BACKEND / "tests" / "fixtures" / "s1" / "kobo-001.yaml"


def _block(text_, start_marker, end_marker):
    start = text_.index(start_marker)
    return text_[start:text_.index(end_marker, start)]


def variant(tmp_path, code, edit):
    """The Kobo import fixture under another Site code, edited, and strictly parsed on import."""
    text_ = edit(KOBO_YAML.read_text(encoding="utf-8")).replace("site_id: KOBO-001", f"site_id: {code}")
    path = tmp_path / f"{code.lower()}.yaml"
    path.write_text(text_, encoding="utf-8")
    store = InMemoryFoundationStore()
    result = do_import(store, read_import_source(str(path)))
    return store, result


def _second(text_, component, before, node_role, link_to, medium):
    """Clone `component` as `<component>-2`, give it a topology node and a connection to `link_to`."""
    block = _block(text_, f"  - component_id: {component}\n", f"  - component_id: {before}\n")
    clone = block.replace(f"component_id: {component}\n", f"component_id: {component}-2\n", 1)
    text_ = text_.replace(block, block + clone, 1)
    node = f"    - node_id: {component}\n      component_id: {component}\n      node_role: {node_role}\n"
    assert node in text_
    text_ = text_.replace(
        node,
        node + f"    - node_id: {component}-2\n      component_id: {component}-2\n      node_role: {node_role}\n",
        1,
    )
    connection = "    - connection_id: bus-to-residential\n"
    return text_.replace(
        connection,
        f"    - connection_id: {component}-2-link\n      from_node: {component}-2\n      to_node: {link_to}\n"
        f"      medium: {medium}\n" + connection,
        1,
    )


class TestReviewM2Ambiguity:
    """ONE roles never choose among several eligible assets (decision Q1)."""

    def test_a_valid_two_generator_foundation_is_refused_at_binding_publication(self, tmp_path) -> None:
        def two_generators(text_):
            text_ = _second(text_, "generator", "fuel-tank", "GENERATION", "ac-bus", "AC")
            return text_.replace("    - battery\n    - generator\n", "    - battery\n    - generator\n    - generator-2\n", 1)

        store, result = variant(tmp_path, "KOBO-TWO-GEN", two_generators)
        components = [c["component_id"] for c in result.revision.content["components"]]
        assert {"generator", "generator-2"} <= set(components)  # the strict parser accepted it
        with pytest.raises(ConversionConflict, match="BINDING_ROLE_AMBIGUOUS") as refused:
            convert(store, BindingService(store, Clock(CONVERTED_AT)), result.tenant, result.site,
                    {**FIXTURE, "site_code": "KOBO-TWO-GEN"})
        assert "Generator state" in str(refused.value) and "generator, generator-2" in str(refused.value)
        assert store.sets.get(result.site.id, []) == []
        assert len(store.rows[result.site.id]) == 1  # no joint Foundation change either

    def test_two_batteries_are_refused_for_both_the_soc_and_the_reserve(self, tmp_path) -> None:
        def two_batteries(text_):
            text_ = _second(text_, "battery", "battery-pcs", "STORAGE", "battery-pcs", "DC")
            return text_.replace("    - battery\n    - generator\n", "    - battery\n    - battery-2\n    - generator\n", 1)

        store, result = variant(tmp_path, "KOBO-TWO-BAT", two_batteries)
        with pytest.raises(ConversionConflict, match="BINDING_ROLE_AMBIGUOUS") as refused:
            convert(store, BindingService(store, Clock(CONVERTED_AT)), result.tenant, result.site,
                    {**FIXTURE, "site_code": "KOBO-TWO-BAT"})
        message = str(refused.value)
        assert "Battery state of charge is one per Site" in message
        assert "Battery reserve is one per Site" in message
        assert store.sets.get(result.site.id, []) == []

    def test_the_soc_must_name_the_battery_that_carries_the_reserve(self, legacy_root) -> None:
        store, result, _ = converted()
        regs = store.registered[result.site.id]
        battery = next(a for a in regs.assets if a.asset_code == "battery")
        other = replace(battery, id=uuid4(), asset_code="battery-spare")
        store.registered[result.site.id] = replace(regs, assets=regs.assets + (other,))
        client = app_for(store, legacy_root)
        rows = wire(client.get("/api/sites/KOBO-001/foundation").json()["bindings"]["mappings"])
        next(r for r in rows if r["role"] == "battery_soc")["asset_id"] = str(other.id)
        sets_before = list(store.sets[result.site.id])
        response = client.post(
            "/api/sites/KOBO-001/foundation/bindings", json={"valid_from": REMOVED_FROM, "bindings": rows}
        )
        assert response.status_code == 422, response.text
        assert response.json()["detail"]["code"] == "BINDING_BATTERY_MISMATCH"
        assert "configured on battery" in response.json()["detail"]["message"]
        assert store.sets[result.site.id] == sets_before


class TestReviewM3ReadinessWithFoundationGaps:
    """Aggregate configuration readiness is incomplete while the Foundation has a gap."""

    def test_a_missing_generator_rating_makes_complete_bindings_incomplete(self, tmp_path) -> None:
        def no_generator_rating(text_):
            block = _block(text_, "  - component_id: generator\n", "  - component_id: fuel-tank\n")
            assert "    rating:\n      value: 40.0\n      unit: kW\n" in block
            return text_.replace(block, block.replace("    rating:\n      value: 40.0\n      unit: kW\n",
                                                      "    rating: null\n", 1), 1)

        store, result = variant(tmp_path, "KOBO-NO-RATING", no_generator_rating)
        convert(store, BindingService(store, Clock(CONVERTED_AT)), result.tenant, result.site,
                {**FIXTURE, "site_code": "KOBO-NO-RATING"})
        body = app_for(store, tmp_path, legacy_documents=lambda: ()).get(
            "/api/sites/KOBO-NO-RATING/foundation"
        ).json()
        ready = body["readiness"]
        # Every channel role and the reserve control are covered ...
        assert ready["missing_roles"] == []
        assert all(r["status"] == "CONFIGURED" for r in ready["roles"] if r["required"])
        # ... but the Foundation gap keeps configuration readiness incomplete, named apart from roles.
        assert ready["state"] == "INCOMPLETE"
        assert [(g["code"], g["subject"]) for g in ready["foundation_gaps"]] == [
            ("COMPONENT_RATING_MISSING", "generator")
        ]
        assert ready["foundation_gaps"] == [
            g for g in body["configuration_gaps"] if g["code"] == "COMPONENT_RATING_MISSING"
        ]
        assert body["acquisition_snapshot"]["available"] is False

    def test_the_converted_kobo_foundation_has_no_gap_and_is_ready(self, legacy_root) -> None:
        store, _, _ = converted()
        ready = app_for(store, legacy_root).get("/api/sites/KOBO-001/foundation").json()["readiness"]
        assert (ready["state"], ready["foundation_gaps"], ready["missing_roles"]) == ("READY_TO_REPORT", [], [])
