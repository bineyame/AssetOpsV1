"""DD3c part 5 (D-DD.114): Kobo published under `minigrid-roles-4` and under `minigrid-roles-5` computes the same.

Two fresh clones (`clone_database`), each dropped in `finally`. In each, `onboard_operator apply` publishes
lakeside-power through the real path: the roles-5 state with `backend/conversions/world` as it stands, the roles-4
state with a copy whose only change is KOBO-001's `role_set` (never both sets on one Site, D-DD.108). Both states load
the same deterministic SIMULATED rows for all twelve of Kobo's world bindings (one local day, 2026-10-06, Africa/Nairobi,
and the next morning, so the fuel-balance night of 2026-10-06 is complete) through `BulkEvidenceLoad`, then run the
dispatch worker, the mini-depth worker, `FuelBalanceService.assess_night` and the October litres month.

Compared, each serialised with `sort_keys`, every UUID replaced by `uuid-<n>` in first-appearance order and the
role-set name by `<role-set>` (D-DD.45's normaliser), then byte-equal:
  - mini-depth revisions: domain, model_version, window, result (figures, states, reasons, limits);
  - dispatch: each `assessment_revision` (analytic, model, key, revision_no, window, claim_level, result,
    evidence_ids) and each `analytic_run` (analytic, model, window, cohort_status, cohort, role_coverage,
    selection, status, the source_time and published_at watermarks);
  - fuel balance: every `fuel_balance_window` column but id/recorded_at/input_sha256;
  - the litres month (`month_litres` over `StoreLitreInputs.read`), as its dataclass tree. With one and a half days
    of readings in October it is the all-absent month (note RUNNING_RECORD_GAP), pinned below; a valued month needs
    a whole October of readings and the dips, which this test does not load.
Wall-clock values are never compared: created_at/recorded_at/started_at/completed_at columns, the runs' and
revisions' `knowledge_cutoff` (each job's cutoff is the database's now at enqueue) and the received_at/accepted_at
watermarks are not selected; inside a result the `committed_watermark` key (mini-depth `basis`) reads `<wall-clock>`.

One step before D-DD.45's normaliser (`_named`): accepted-evidence ids are uuid4 in each database and the product
sorts evidence-id lists by id, so the same readings would number differently in the two states. Each accepted
evidence id is therefore written as its reading, `evidence:<device>/<signal>#<sequence>` (unique per Site, asserted),
and a list made only of those is sorted. Membership is still compared exactly; only the id-dependent order goes.

Stored digests, and how each is compared:
  - directly: none. Every stored digest embeds ids or the role-set name, so each is covered by its normalised
    inputs instead and is not selected:
      mini_depth_revision.input_sha256 (foundation, binding-set, evidence and property revision ids; the cutoff);
      analytic_run.input_sha256 (the input set: readings' ids, binding-set revision ids, role set);
      analytic_run.cohort_sha256 (the cohort members' source ids);
      analytic_run.configuration_sha256 (bindings with their ids, the role sets);
      assessment_revision.basis_sha256 (the input digest and evidence ids);
      fuel_balance_window.input_sha256 (tank and generator asset ids, evidence ids).

Added to the onboarding copy used in BOTH states (so the compared fuel balance is a real assessment, not
NOT_ASSESSED NO_SENSOR_ACCURACY): KOBO-001's `fuel-tank` gets `fuel-level-sensor-accuracy` 10 L and
`fuel-level-sensor-accuracy-basis` GENERIC_DEFAULT (the values the Kisiwa demo config declares). Nothing else.

Requires ASSETOPS_TEST_DATABASE_URL on a routed run (`tools/run-host-tests.ps1`, under `tools/heavy-slot.sh --db`).
"""

from __future__ import annotations

import dataclasses
import enum
import json
import math
import os
import re
import shutil
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from fractions import Fraction
from pathlib import Path
from uuid import UUID

import pytest

import pg_harness

URL = os.environ.get("ASSETOPS_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

if URL:
    from sqlalchemy import create_engine, text
    from test_s2_evidence_ledger_postgres import Kit, _z

    from assetops_backend import onboard_operator as command
    from assetops_backend.actions.adapters.postgres_action_store import PostgresActionStore
    from assetops_backend.analytics.adapters.postgres_assessment_store import PostgresAssessmentStore
    from assetops_backend.analytics.assessment_worker import DispatchAssessmentWorker
    from assetops_backend.chain.ports import SiteRef
    from assetops_backend.database_target import PG_TARGET_ENV
    from assetops_backend.evidence.adapters.postgres_evidence_ledger import PostgresEvidenceLedger
    from assetops_backend.evidence.bulk_load import BulkEvidenceLoad
    from assetops_backend.fuel_balance.adapters.postgres_fuel_balance_store import PostgresFuelBalanceStore
    from assetops_backend.fuel_balance.service import FuelBalanceService
    from assetops_backend.mini_depth.store import PostgresMiniDepthStore
    from assetops_backend.mini_depth.worker import MiniDepthWorker
    from assetops_backend.structure.litres.composition import build_litre_inputs
    from assetops_backend.structure.litres.rules import month_litres
    from assetops_backend.structure.litres.source import FILLED_BY
    from assetops_backend.work.adapters.postgres_fuel_records import select_fuel_records

BACKEND = Path(__file__).resolve().parent.parent
LAKESIDE = BACKEND / "tests" / "fixtures" / "on1" / "lakeside-power.onboarding.json"
WORLD = BACKEND / "conversions" / "world"
CODE = "KOBO-001"
NIGHT = date(2026, 10, 6)
LOCAL = timezone(timedelta(hours=3))  # Africa/Nairobi, no DST
FIRST = datetime(2026, 10, 6, 0, 0, tzinfo=LOCAL)  # the local day ...
LAST = datetime(2026, 10, 7, 14, 0, tzinfo=LOCAL)  # ... and the next morning past the night's 12:00 close
ROLE_SETS = ("minigrid-roles-4", "minigrid-roles-5")
_UUID = re.compile(r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}")
_ROLE_SET = re.compile("|".join(ROLE_SETS))


# --- the normaliser (D-DD.45) ----------------------------------------------------------------------------------------

def _plain(value):
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return {f.name: _plain(getattr(value, f.name)) for f in dataclasses.fields(value)}
    if isinstance(value, enum.Enum):
        return _plain(value.value)
    if isinstance(value, dict) or hasattr(value, "items") and callable(value.items):
        return {str(k): _plain(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, frozenset, set)):
        items = [_plain(v) for v in value]
        return sorted(items, key=json.dumps) if isinstance(value, (set, frozenset)) else items
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, (Decimal, Fraction, UUID)):
        return str(value)
    if isinstance(value, float) and not math.isfinite(value):
        return repr(value)
    return value


#: JSON keys whose values are wall-clock instants (the database's now when the row was written), never compared.
WALL_CLOCK_KEYS = frozenset({"committed_watermark"})


def _named(value, evidence: dict[str, str]):
    """Accepted-evidence ids as their reading (`evidence:<device>/<signal>#<sequence>`), lists of them sorted;
    wall-clock keys masked. The ids are uuid4 per database and the product sorts these lists by id, so without
    this step the same readings number differently in the two states (see the module docstring)."""
    if isinstance(value, dict):
        return {k: "<wall-clock>" if k in WALL_CLOCK_KEYS else _named(v, evidence) for k, v in value.items()}
    if isinstance(value, list):
        items = [_named(v, evidence) for v in value]
        if items and all(isinstance(i, str) and i.startswith("evidence:") for i in items):
            return sorted(items)
        return items
    if isinstance(value, str):
        return evidence.get(value.lower(), value)
    return value


def normalised(value, evidence: dict[str, str]) -> str:
    """`sort_keys` JSON, UUIDs as `uuid-<n>` in first-appearance order, the role-set name as `<role-set>`
    (D-DD.45), after `_named`."""
    body = json.dumps(_named(_plain(value), evidence), sort_keys=True)
    seen: dict[str, str] = {}
    body = _UUID.sub(lambda m: seen.setdefault(m.group(0).lower(), f"uuid-{len(seen) + 1}"), body)
    return _ROLE_SET.sub("<role-set>", body)


# --- readings --------------------------------------------------------------------------------------------------------

def _f(x: float) -> str:
    """A canonical decimal string (no trailing zeros, no negative zero)."""
    text_ = f"{x:.2f}".rstrip("0").rstrip(".")
    return "0" if text_ in ("-0", "") else text_


def kobo_rows():
    """Every 15 minutes FIRST..LAST, all twelve bindings (the generator every 5 minutes): PV 06:00-18:00 local, the generator RUNNING 19:00-23:00
    local on the night with the tank falling 2 L a quarter hour while it runs, the battery covering the night."""
    rows, level, soc = [], 1500.0, 80.0
    t = FIRST
    while t <= LAST:
        h = t.hour + t.minute / 60
        sun = max(0.0, math.sin(math.pi * (h - 6) / 12)) if 6 <= h <= 18 else 0.0
        running = t.date() == NIGHT and 19 <= h < 23
        night = not sun
        rows += [("pv-inverter-controller", "ac-power", t, _f(40 * sun)),
                 ("pv-inverter-controller", "available-power", t, _f(45 * sun)),
                 ("pv-irradiance-sensor", "irradiance", t, _f(950 * sun)),
                 ("battery-pcs-controller", "ac-power", t, _f(6.0 if night and not running else -8 * sun)),
                 ("battery-pcs-controller", "state-of-charge", t, _f(soc)),
                 ("battery-pcs-controller", "discharge-capability", t, _f(30.0)),
                 ("fuel-level-sensor", "fuel-level", t, _f(level)),
                 ("residential-meter", "active-power", t, _f(3.0 if sun else 6.0)),
                 ("clinic-meter", "active-power", t, _f(2.0)),
                 ("mill-meter", "active-power", t, _f(8.0 if sun else 0.0))]
        for k in range(3):  # the generator every 5 minutes: its state, and its power as a 5-minute interval mean
            at = t + timedelta(minutes=5 * k)  # (A2's slot rule reads power only from interval means)
            on = at.date() == NIGHT and 19 <= at.hour < 23
            if at < LAST:
                rows += [("generator-controller", "status", at, "RUNNING" if on else "STOPPED"),
                         ("generator-controller", "ac-power", at + timedelta(minutes=5), _f(25.0 if on else 0.0), at)]
        if running:
            level -= 2.0
        soc = min(90.0, soc + 1.0) if sun else (soc if running else max(40.0, soc - 0.5))
        t += timedelta(minutes=15)
    return rows


def sealed(kit, rows) -> list[bytes]:
    """SIMULATED batches per source, at most 96 envelopes each (the v2 cap is 256), sequences per source as
    `test_ds3_bulk_load_postgres.seal_rows` numbers them."""
    sequences: dict = {}
    by_source: dict[tuple[str, str], list[str]] = {}
    for device, signal, when, value, *start in rows:
        source = kit.binding(device, signal)["source_id"]
        sequences[source] = sequences.get(source, 0) + 1
        by_source.setdefault((device, source), []).append(kit.envelope(
            device, sequences[source], 0, value, source_time=_z(when), bound_signal=signal,
            interval_start=_z(start[0]) if start else None))
    return [kit.seal(texts[i:i + 96], device_id=device, source_id=source).encode("utf-8")
            for (device, source), texts in by_source.items() for i in range(0, len(texts), 96)]


# --- one state ------------------------------------------------------------------------------------------------------

def _onboarding(tmp_path: Path) -> Path:
    document = json.loads(LAKESIDE.read_text(encoding="utf-8"))
    site = next(s for s in document["sites"] if s["code"] == CODE)
    tank = next(c for c in site["components"] if c["id"] == "fuel-tank")
    tank["properties"] += [
        {"property_key": "fuel-level-sensor-accuracy", "value": 10, "unit": "L", "source": "SITE", "source_version": 1},
        {"property_key": "fuel-level-sensor-accuracy-basis", "value": "GENERIC_DEFAULT", "unit": "state",
         "source": "SITE", "source_version": 1}]
    out = tmp_path / "lakeside-power.onboarding.json"
    out.write_text(json.dumps(document, indent=2), encoding="utf-8")
    return out


def _world(tmp_path: Path, role_set: str) -> Path:
    if role_set == "minigrid-roles-5":
        return WORLD
    out = tmp_path / "world-roles-4"
    shutil.copytree(WORLD, out)
    path = out / f"{CODE}-bindings.json"
    document = json.loads(path.read_text(encoding="utf-8"))
    document["role_set"] = role_set
    path.write_text(json.dumps(document, indent=2), encoding="utf-8")
    return out


def _publish(url, onboarding, world, monkeypatch, capsys, keys: Path) -> None:
    keys.mkdir(mode=0o700, exist_ok=True)
    os.chmod(keys, 0o700)
    for variable in PG_TARGET_ENV:
        monkeypatch.delenv(variable, raising=False)
    monkeypatch.delenv("ASSETOPS_REAL_OPERATOR_DATA", raising=False)
    monkeypatch.setenv("DATABASE_URL", url)
    monkeypatch.setenv("ASSETOPS_TENANT_SLUG", "lakeside-power")
    monkeypatch.setenv("ASSETOPS_PSEUDONYM_KEY_DIR", str(keys))
    capsys.readouterr()
    command.main(["digest", "--file", str(onboarding)])
    digest = capsys.readouterr().out.strip()
    code = command.main(["apply", "--file", str(onboarding), "--confirmed-digest", digest, "--bindings", str(world)])
    _, err = capsys.readouterr()
    assert code == 0, err


def _rows(engine, sql: str, **params) -> list[dict]:
    with engine.connect() as c:
        return [dict(r._mapping) for r in c.execute(text(sql), params)]


def _state(url, role_set, onboarding, tmp_path, monkeypatch, capsys) -> dict:
    """Publish, load, compute; return each output's rows and its normalised form."""
    _publish(url, onboarding, _world(tmp_path, role_set), monkeypatch, capsys, tmp_path / f"keys-{role_set}")
    engine = create_engine(url)
    holders: list = [engine]
    try:
        [site] = _rows(engine, "SELECT r.id AS rev, r.role_set, s.id AS site, s.tenant_id FROM "
                               "signal_binding_set_revision r JOIN site s ON s.id = r.site_id "
                               "WHERE s.site_code = :c AND r.superseded_at IS NULL", c=CODE)
        assert site["role_set"] == role_set
        t, s = site["tenant_id"], site["site"]
        kit = Kit(engine, site["rev"])
        rows = kobo_rows()
        loaded = BulkEvidenceLoad(PostgresEvidenceLedger(url)).load(sealed(kit, rows))
        assert loaded.already_loaded == 0 and loaded.envelopes == len(rows)
        with engine.connect() as c:
            now = c.execute(text("SELECT clock_timestamp()")).scalar_one()
        at = now + timedelta(hours=1)  # every clock after the load

        assessments = PostgresAssessmentStore(url)
        holders.append(assessments)
        dispatch = DispatchAssessmentWorker(assessments, clock=lambda: at)
        outcomes = []
        while (outcome := dispatch.run_once(t, s)) is not None:
            outcomes.append(outcome)
        assert outcomes and all(o.status == "DONE" for o in outcomes), [(o.status, o.error) for o in outcomes]

        jobs = PostgresAssessmentStore(url)
        mini_store = PostgresMiniDepthStore(engine)
        holders.append(jobs)
        mini = MiniDepthWorker(jobs, mini_store, test_lease_clock=lambda: at)
        done = []
        while batch := mini.run_pending(100, t, s):
            done += batch
        assert done and all(o.status == "DONE" for o in done), [(o.status, o.error) for o in done if o.status != "DONE"]

        fb = PostgresFuelBalanceStore(url, actions=(actions := PostgresActionStore(url)),
                                      fuel_records=select_fuel_records, test_db_clock_override=lambda: at)
        holders += [actions, fb]
        FuelBalanceService(fb).assess_night(t, s, NIGHT)

        litres = build_litre_inputs(url)
        try:
            month = month_litres(litres.inputs.read(SiteRef(t, s, CODE, "MINIGRID", "Africa/Nairobi"), "2026-10",
                                                    at + timedelta(minutes=1)), FILLED_BY)
        finally:
            litres.dispose()

        out = {
            "mini_depth": _rows(engine, "SELECT domain, model_version, window_start, window_end, result "
                                        "FROM mini_depth_revision WHERE site_id = :s "
                                        "ORDER BY domain, window_start, window_end, model_version, knowledge_cutoff",
                                s=s),
            "dispatch_revisions": _rows(engine, "SELECT analytic_id, model_version, assessment_key, revision_no, "
                                                "window_start, window_end, claim_level, result, evidence_ids "
                                                "FROM assessment_revision WHERE site_id = :s "
                                                "ORDER BY analytic_id, assessment_key, revision_no", s=s),
            "dispatch_runs": _rows(engine, "SELECT analytic_id, model_version, window_start, window_end, cohort_status, "
                                           "cohort, role_coverage, selection, status, "
                                           "watermarks->'source_time' AS source_time, "
                                           "watermarks->'published_at' AS published_at FROM analytic_run "
                                           "WHERE site_id = :s ORDER BY analytic_id, window_start, window_end, "
                                           "knowledge_cutoff", s=s),
            "fuel_balance": _rows(engine, "SELECT tank_asset_id, generator_asset_id, night_date, window_start, "
                                          "window_end, revision, parameter_version, state, reason, residual_low, "
                                          "residual_high, gap_minutes, gap_spans, limitations, terms, evidence_ids, "
                                          "record_ids FROM fuel_balance_window WHERE site_id = :s "
                                          "ORDER BY night_date, revision", s=s),
            "litres_month": month,
        }
        evidence = {str(r["id"]): f"evidence:{r['device_id']}/{r['signal_id']}#{r['sequence']}"
                    for r in _rows(engine, "SELECT id, device_id, signal_id, sequence FROM accepted_evidence "
                                           "WHERE site_id = :s", s=s)}
        assert len(set(evidence.values())) == len(evidence) == len(rows)
        return {"raw": out, "normalised": {k: normalised(v, evidence) for k, v in out.items()}}
    finally:
        pg_harness.dispose(*holders)


def test_kobo_under_roles_4_and_roles_5_computes_byte_equal_outputs(tmp_path, monkeypatch, capsys) -> None:
    onboarding = _onboarding(tmp_path)
    states = {}
    for tag, role_set in (("dd3c4", "minigrid-roles-4"), ("dd3c5", "minigrid-roles-5")):
        url = pg_harness.clone_database(tag)
        try:
            states[role_set] = _state(url, role_set, onboarding, tmp_path, monkeypatch, capsys)
        finally:
            pg_harness.drop_database(url)

    four, five = states["minigrid-roles-4"], states["minigrid-roles-5"]
    raw = five["raw"]
    dump = os.environ.get("DD3C_PARITY_DUMP")  # a directory for both normalised states, when diagnosing
    if dump:
        for role_set, state in states.items():
            Path(dump, f"{role_set}.json").write_text(json.dumps(state["normalised"], indent=1), encoding="utf-8")
    # Non-vacuous: every compared set holds something real.
    assert raw["mini_depth"], "no mini-depth revision"
    assert any("interval" in r["assessment_key"] for r in raw["dispatch_revisions"]), \
        [r["assessment_key"] for r in raw["dispatch_revisions"]]
    assert raw["dispatch_runs"], "no dispatch run"
    assert raw["fuel_balance"] and raw["fuel_balance"][-1]["state"] != "NOT_ASSESSED", \
        [(w["state"], w["reason"]) for w in raw["fuel_balance"]]
    assert raw["litres_month"].values, "an empty litres month"
    assert {v.missing.note for v in raw["litres_month"].values.values()} == {"RUNNING_RECORD_GAP"}
    for name in five["normalised"]:
        a, b = four["normalised"][name], five["normalised"][name]
        if a != b:
            at = next((i for i, (x, y) in enumerate(zip(a, b)) if x != y), min(len(a), len(b)))
            pytest.fail(f"{name} differs at byte {at}: roles-4 {a[max(0, at - 120):at + 120]!r} | "
                        f"roles-5 {b[max(0, at - 120):at + 120]!r}")
