"""FUEL-1 A1 (`.agent/build-sheet-FUEL-1.md` §4.1): fuel-cost-2 over real persisted inputs, the consequence store's new
columns, migration 0053's CHECKs, and its downgrade/upgrade.

The S4-02b PowerSite (five 20 kW means of 5 minutes in Candidate time [08:05, 08:30)) is built with its demo generator
values plus a declared no-load fuel rate of 3.3 L/h, basis GENERIC_DEFAULT, so its Foundation revision selects
fuel-cost-2 through the store's real `load_input`.
"""

from __future__ import annotations

import copy
import os
from dataclasses import replace
from decimal import Decimal
from fractions import Fraction

import pytest

URL = os.environ.get("ASSETOPS_TEST_DATABASE_URL")

pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

if URL:
    import pg_harness
    from pg_harness import alembic_head
    from sqlalchemy import text
    from sqlalchemy.exc import DBAPIError
    from test_s1_bindings_postgres import _alembic, engine, store  # noqa: F401
    from test_s4_consequence_store_postgres import POWER_DAY, PowerSite, _release_connections, site  # noqa: F401
    from test_w203_cold_migration_postgres import head

    from assetops_backend.financials import consequence_read as cr
    from assetops_backend.financials import fuel_cost as fc
    from assetops_backend.financials import fuel_cost_v2 as fc2
    from assetops_backend.financials.recompute import derive

MIGRATION, PREVIOUS = "0053_fuel_cost_2", "0052_verification_plan_domain"
NO_LOAD = [{"property_key": "generator-no-load-fuel-rate", "value": 3.3, "unit": "L/h", "source": "SITE",
            "source_version": 1},
           {"property_key": "generator-no-load-fuel-rate-basis", "value": "GENERIC_DEFAULT", "unit": "state",
            "source": "SITE", "source_version": 1}]


@pytest.fixture()
def v2site(store, engine, capsys, monkeypatch):  # noqa: F811
    import test_s4_finding_store_postgres as finding_cases

    demo = copy.deepcopy(finding_cases.DEMO)
    demo["component_properties"]["properties"] += copy.deepcopy(NO_LOAD)
    monkeypatch.setattr(finding_cases, "DEMO", demo)
    s = PowerSite(store, engine, capsys)
    yield s
    s.prices.dispose()
    s.store.dispose()


def _derive(site, rev):
    return derive(site.store, site.prices, site.tenant, site.site, rev["finding_id"], rev["id"])


def _row(site):
    rows = site.store.rows(site.tenant, site.site)
    return rows, rows["financial_consequence_revision"]


class TestStoreRoundTrip:
    def test_declared_rate_selects_fuel_cost_2_and_round_trips(self, v2site) -> None:
        site = v2site
        site.publish("v1", "v2", "v3")
        rev = site.on(POWER_DAY)
        f = site.store.load_input(site.tenant, site.site, rev["finding_id"], rev["id"])
        assert {(x.no_load, x.no_load_basis) for x in f.foundations} == {((("3.3", "L/h"),), ("GENERIC_DEFAULT",))}
        c = _derive(site, rev)
        q = c.quantity
        assert fc2.is_v2(q) and q.state == "AVAILABLE", (q.reason, q.detail)
        # Loaded only: the same 2.75 L as fuel-cost-1 (25/3 kWh x 0.3 L/kWh x 1.10), no idle seconds.
        assert q.high_exact == Fraction(11, 10) * 5 * 20 * Fraction(5, 60) * Fraction(3, 10) == fc.quantify(f).high_exact
        assert (q.idle_seconds, q.no_load_l_per_h, q.no_load_basis) == (0, Decimal("3.3"), "GENERIC_DEFAULT")
        appended = site.store.append(c)
        assert appended.revision_no == 1 and not appended.replayed
        replay = site.store.append(_derive(site, rev))
        assert replay.replayed and replay.consequence_revision_id == appended.consequence_revision_id
        _, (row,) = _row(site)
        assert (row["model_id"], row["formula_version"], row["parameter_version"], row["parameter_sha256"]) == (
            "fuel-cost-2", fc2.FORMULA_VERSION, "fuel-cost-2/sfc-upper-multiplier-and-no-load/v1", fc2.PARAMETER_SHA256)
        assert (row["no_load_fuel_rate_l_per_h"], row["no_load_fuel_rate_basis"], row["idle_seconds"]) == (
            Decimal("3.3"), "GENERIC_DEFAULT", 0)
        assert row["quantity_high_exact"] == "11/4" and list(row["limitations"]) == list(fc2.LIMITATIONS)
        model = cr.dto(row, {"intervals": {}, "assessments": {}, "assumptions": {}})["model"]
        assert model["model_id"] == "fuel-cost-2" and model["parameter_is_reviewed"] is True
        assert (model["no_load_fuel_rate_l_per_h"], model["no_load_fuel_rate_basis"], model["idle_seconds"]) == (
            "3.3", "GENERIC_DEFAULT", 0)

    def test_stored_fuel_cost_2_head_reads_current(self, v2site, engine) -> None:  # noqa: F811
        """A1 review L1 (closed in A2): a stored fuel-cost-2 head re-derives to the same basis through both
        `ConsequenceReadService` currentness paths (`read` and `select_consequence_on`), so it reads CURRENT, not
        STALE / TECHNICAL_INPUT_CHANGED. Reverting either path to `fuel_cost.quantify` fails this test."""
        from money_gate_stub import AUTHORED, ELIGIBLE

        site = v2site
        site.publish("v1", "v2", "v3")
        rev = site.on(POWER_DAY)
        c = _derive(site, rev)
        assert fc2.is_v2(c.quantity)
        site.store.append(c)
        reads = cr.ConsequenceReadService(site.store, site.prices, eligibility=ELIGIBLE, provenance=AUTHORED)
        body = reads.read(site.tenant, site.site, rev["finding_id"], rev["id"], finding_revision_is_latest=True,
                          source_open=True)
        assert (body["currentness"]["state"], body["currentness"]["reasons"]) == ("CURRENT", [])
        assert body["consequence"]["model"]["model_id"] == "fuel-cost-2"
        with engine.connect() as conn:
            known_at = conn.execute(text("SELECT clock_timestamp()")).scalar_one()
            on = reads.select_consequence_on(conn, site.tenant, site.site, rev["id"], known_at)
        assert on["currentness"] == {"state": "CURRENT", "reasons": []}

    def test_idle_intervals_are_counted_at_the_declared_rate(self, v2site) -> None:
        """The same persisted Finding, with two of its five counted means read as 0 kW in memory, so the store
        writes an idle fuel-cost-2 consequence: 3 x 20 kW x 5 min x 0.3 + 2 x 5 min x 3.3, all x 1.10."""
        site = v2site
        site.publish("v1", "v2", "v3")
        rev = site.on(POWER_DAY)
        f = site.store.load_input(site.tenant, site.site, rev["finding_id"], rev["id"])
        counted = [x.evidence_id for x in fc.quantify(f).intervals]
        idle = set(counted[:2])
        f0 = replace(f, readings=tuple(replace(r, value_text="0") if r.evidence_id in idle else r
                                       for r in f.readings))
        q = fc2.quantify(f0)
        expect = Fraction(11, 10) * (3 * 20 * Fraction(5, 60) * Fraction(3, 10) + 2 * Fraction(5, 60) * Fraction(33, 10))
        assert q.state == "AVAILABLE" and q.high_exact == expect and q.idle_seconds == 600
        price = fc.PriceSelection("UNPRICED", "NO_PRICE")
        site.store.append(fc2.consequence(f0, q, price))
        rows, (row,) = _row(site)
        assert (row["model_id"], row["state"], row["idle_seconds"]) == ("fuel-cost-2", "UNPRICED", 600)
        assert sorted(x["mean_kw"] for x in rows["financial_consequence_power_interval"]) == [0, 0, 20, 20, 20]

    def test_no_rate_stays_fuel_cost_1_with_null_columns(self, site) -> None:
        site.publish("v1", "v2", "v3")
        c = _derive(site, site.on(POWER_DAY))
        assert not fc2.is_v2(c.quantity) and type(c) is fc.Consequence
        site.store.append(c)
        _, (row,) = _row(site)
        assert row["model_id"] == "fuel-cost-1" and row["parameter_sha256"] == fc.PARAMETER_SHA256
        assert (row["no_load_fuel_rate_l_per_h"], row["no_load_fuel_rate_basis"], row["idle_seconds"]) == (
            None, None, None)
        model = cr.dto(row, {"intervals": {}, "assessments": {}, "assumptions": {}})["model"]
        assert set(model) == {"model_id", "formula_version", "parameter_version", "parameter_sha256",
                              "sfc_upper_multiplier", "parameter_is_reviewed"} and model["parameter_is_reviewed"]


class TestMigration0053:
    def _insert_copy(self, engine, row_id, **changes):  # noqa: F811
        """Re-insert a stored row as its next revision (new id) with `changes`, inside a rolled-back
        transaction, so only the CHECK under test can refuse it."""
        cols = ", ".join(f"{k} = :{k}" for k in changes)
        with engine.connect() as c:
            tx = c.begin()
            try:
                c.execute(text("CREATE TEMP TABLE probe ON COMMIT DROP AS SELECT * FROM financial_consequence_revision "
                               "WHERE id = :i"), {"i": row_id})
                c.execute(text("UPDATE probe SET id = gen_random_uuid(), revision_no = revision_no + 1,"
                               "prior_consequence_revision_id = id, consequence_basis_sha256 = repeat('e', 64)"
                               + (", " + cols if cols else "")), changes)
                c.execute(text("INSERT INTO financial_consequence_revision SELECT * FROM probe"))
            finally:
                tx.rollback()

    def test_checks(self, v2site, engine) -> None:  # noqa: F811
        site = v2site
        site.publish("v1", "v2", "v3")
        site.store.append(_derive(site, site.on(POWER_DAY)))
        _, (row,) = _row(site)
        self._insert_copy(engine, row["id"])  # the probe itself is admitted
        for changes, name in [
            ({"model_id": "fuel-cost-1"}, "financial_consequence_revision_fuel_cost_1_no_idle"),
            ({"model_id": "fuel-cost-3"}, "financial_consequence_revision_model_id_check"),
            ({"no_load_fuel_rate_l_per_h": 0}, "financial_consequence_revision_no_load_rate_check"),
            ({"no_load_fuel_rate_basis": "GUESS"}, "financial_consequence_revision_no_load_basis_check"),
            ({"idle_seconds": -1}, "financial_consequence_revision_idle_seconds_check"),
        ]:
            with pytest.raises(DBAPIError, match=name):
                self._insert_copy(engine, row["id"], **changes)

    def test_single_head_and_trial_checks(self, engine) -> None:  # noqa: F811
        from alembic.script import ScriptDirectory

        script = ScriptDirectory.from_config(_alembic())
        assert script.get_heads() == [MIGRATION] == [alembic_head()] and head(engine) == MIGRATION
        assert script.get_revision(MIGRATION).down_revision == PREVIOUS
        with engine.connect() as c:
            defs = dict(c.execute(text(
                "SELECT conname, pg_get_constraintdef(oid) FROM pg_constraint WHERE conrelid = "
                "'trial_cost_comparison_revision'::regclass AND conname IN ("
                "'trial_cost_comparison_revision_formula_check', 'trial_cost_comparison_revision_reason_check')")).all())
        assert "trial-fuel-comparison/2" in defs["trial_cost_comparison_revision_formula_check"]
        assert all(v in defs["trial_cost_comparison_revision_reason_check"]
                   for v in ("IDLE_SECONDS_UNKNOWN", "NO_LOAD_RATE_DIFFERS", "SFC_DIFFERS", "PRICE_BASIS_DIFFERS"))

    def test_downgrade_refuses_with_v2_rows_then_round_trips_empty(self, v2site, engine) -> None:  # noqa: F811
        from alembic import command

        site = v2site
        site.publish("v1", "v2", "v3")
        site.store.append(_derive(site, site.on(POWER_DAY)))
        site.store.dispose()
        site.prices.dispose()
        config = _alembic()
        engine.dispose()
        with pytest.raises(Exception, match="0053 downgrade refused: fuel-cost-2"):
            command.downgrade(config, PREVIOUS)
        assert head(engine) == MIGRATION

    def test_empty_downgrade_restores_0011_and_0037(self, store, engine) -> None:  # noqa: F811
        from alembic import command

        pg_harness.dispose(store)  # `store` emptied the tables; release its pool before the DDL lock

        def shape():
            with engine.connect() as c:
                cols = set(c.execute(text(
                    "SELECT column_name FROM information_schema.columns WHERE table_name = "
                    "'financial_consequence_revision'")).scalars())
                defs = dict(c.execute(text(
                    "SELECT conname, pg_get_constraintdef(oid) FROM pg_constraint WHERE conname IN ("
                    "'financial_consequence_revision_model_id_check', 'trial_cost_comparison_revision_formula_check', "
                    "'trial_cost_comparison_revision_reason_check')")).all())
            return cols, defs

        config = _alembic()
        cols_up, defs_up = shape()
        assert {"no_load_fuel_rate_l_per_h", "no_load_fuel_rate_basis", "idle_seconds"} <= cols_up
        engine.dispose()
        try:
            command.downgrade(config, PREVIOUS)
            assert head(engine) == PREVIOUS
            cols_down, defs_down = shape()
            assert cols_up - cols_down == {"no_load_fuel_rate_l_per_h", "no_load_fuel_rate_basis", "idle_seconds"}
            assert "fuel-cost-2" not in defs_down["financial_consequence_revision_model_id_check"]
            assert "trial-fuel-comparison/2" not in defs_down["trial_cost_comparison_revision_formula_check"]
            assert "NO_LOAD_RATE_DIFFERS" not in defs_down["trial_cost_comparison_revision_reason_check"]
            command.upgrade(config, "head")
        finally:
            if head(engine) != MIGRATION:
                command.upgrade(config, "head")
        assert shape() == (cols_up, defs_up)
