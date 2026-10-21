"""W4-02 unit 4 step 3: pure projection of an assessed hour into the revision `result` (`mini_depth/projection.py`)."""

from __future__ import annotations

import json
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from uuid import UUID, uuid4

from assetops_backend.mini_depth import projection, rules
from assetops_backend.mini_depth.inputs import HourInputs, SelectedRow
from assetops_backend.mini_depth.rules import FuelInputs, LoadAsset, Observation, Reading, RenewableInputs, Window

NOON = datetime(2026, 10, 6, 9, 0, tzinfo=timezone.utc)
HOUR = Window(NOON, NOON + timedelta(hours=1))
SRC = uuid4()
GEN, TANK, CRIT, FEED = (uuid4() for _ in range(4))
SFC = rules.SfcValue(uuid4(), Decimal("0.3"), NOON - timedelta(days=30), None)


def rd(role: str, value: str, lo: float, hi: float | None, asset: UUID | None, unit: str = "kW") -> Reading:
    s = NOON + timedelta(minutes=lo)
    e = None if hi is None else NOON + timedelta(minutes=hi)
    return Reading(uuid4(), SRC, role, asset, s, s if e else None, e, "GOOD", Decimal(value), unit)


def per_minute(role: str, value: str, asset: UUID | None, lo: int = 0, hi: int = 60) -> list[Reading]:
    return [rd(role, value, m, m + 1, asset) for m in range(lo, hi)]


def ob(role: str, minute: float, *, src: UUID = SRC, quality: str = "GOOD", **kw: str) -> Observation:
    return Observation(uuid4(), src, role, NOON + timedelta(minutes=minute), quality, kw.get("state"), kw.get("kind"),
                       kw.get("outcome"), kw.get("corr"))


def base_readings() -> list[Reading]:
    return [
        *per_minute("generator_power", "0", GEN, 0, 11), *per_minute("generator_power", "15", GEN, 11, 40),
        *per_minute("generator_power", "0", GEN, 40, 60),
        *per_minute("critical_load_requested_power", "4", CRIT),
        *per_minute("critical_load_delivered_power", "4", CRIT, 0, 10),
        *per_minute("critical_load_delivered_power", "0", CRIT, 10, 12),
        *per_minute("critical_load_delivered_power", "4", CRIT, 12, 60),
        *per_minute("feeder_demand", "8", FEED),
        rd("fuel_level", "180", 0, None, TANK, "L"), rd("fuel_level", "176", 59, None, TANK, "L"),
    ]


def base_observations() -> list[Observation]:
    return [
        ob("site_supply_state", -5, state="ENERGIZED"), ob("site_supply_state", 10, state="LOST"),
        ob("mini_backup_start_event", 10.5, kind="START_REQUEST", outcome="REQUESTED", corr="c-1"),
        ob("mini_backup_start_event", 11, kind="START_RESULT", outcome="SUCCEEDED", corr="c-1"),
        ob("mini_backup_bus_state", 11.5, state="ENERGIZED"), ob("site_supply_state", 40, state="ENERGIZED"),
    ]


def hour_inputs(*, target: Decimal | None = Decimal("5"), readings: list[Reading] | None = None,
                observations: list[Observation] | None = None,
                sfc: tuple[rules.SfcValue, ...] = (SFC,)) -> HourInputs:
    readings = base_readings() if readings is None else readings
    observations = base_observations() if observations is None else observations
    selected = [SelectedRow(r.evidence_id, r.role, r.asset_id, NOON + timedelta(hours=2), False) for r in readings]
    selected += [SelectedRow(o.evidence_id, o.role, None, NOON + timedelta(hours=3), o.source_time < NOON)
                 for o in observations]
    return HourInputs(
        tenant_id=uuid4(), site_id=uuid4(), window=HOUR, local_day=date(2026, 10, 6), site_timezone="Africa/Nairobi",
        knowledge_cutoff=NOON + timedelta(hours=4), foundation_revision_id=uuid4(), binding_set_revision_id=uuid4(),
        readings=tuple(readings), observations=tuple(observations), selected=tuple(selected),
        renewable=RenewableInputs(pv_uncertainty_kw=Decimal("1"), retained_margin_kw=Decimal("3"),
                                  feeder_asset_ids=(FEED,), critical_asset_id=CRIT),
        loads=(LoadAsset(CRIT, "CLINIC", "Clinic", True, False), LoadAsset(FEED, "FEED-A", "Feeder A", False, False)),
        fuel=FuelInputs(sfc=sfc, upper_multiplier=Decimal("1.10")), generator_asset_id=GEN, tank_asset_id=TANK,
        critical_asset_id=CRIT, recovery_target_min=target, property_revision_ids={},
    )


def test_projection_wire_keys_basis_and_null_outage_count() -> None:
    inputs = hour_inputs()
    revs = {d: projection.project(d, inputs) for d in ("renewable", "service", "fuel", "backup")}
    for d, rev in revs.items():
        assert (rev.domain, rev.model_version, rev.knowledge_cutoff) == (d, f"mini-{d}/1", inputs.knowledge_cutoff)
        assert rev.input_sha256 == inputs.input_sha256 and tuple(rev.evidence_ids) == inputs.evidence_ids
        assert json.loads(json.dumps(rev.result)) == rev.result  # plain JSON: numbers, strings, null
        basis = rev.result["basis"]
        assert basis["accepted_evidence_ids"] == sorted(str(i) for i in inputs.evidence_ids)
        assert basis["committed_watermark"] == "2026-10-06T12:00:00.000000Z"
        assert (basis["model_version"], basis["site_timezone"]) == (f"mini-{d}/1", "Africa/Nairobi")
        assert basis["foundation_revision_ids"] == [str(inputs.foundation_revision_id)]
        assert list(basis["role_coverage"]) == sorted(basis["role_coverage"])
        for row in rev.result["rows"]:
            assert row["evidence_ids"] == sorted(row["evidence_ids"])

    backup = revs["backup"].result
    # q3 ruling 8: a SUPPORTED observed outage still projects a null outage count.
    assert backup["status"] == "SUPPORTED" and backup["cards"]["outage_count"] is None
    assert backup["cards"]["critical_recovery"] == {"seconds": 180, "target_seconds": 300}
    assert set(backup["cards"]) == {"outage_count", "start_success_count", "last_witnessed_test_at",
                                    "critical_recovery"}
    (chain,) = backup["rows"]
    assert [s["code"] for s in chain["steps"]] == list(rules.BACKUP_STEPS)
    assert (chain["result"], chain["service_outcome"], chain["outage_start"]) == ("PASS", "RECOVERED",
                                                                                 "2026-10-06T09:10:00.000000Z")
    # Instant supply reports never make the basis CURRENT.
    assert backup["basis"]["source_freshness"] == "UNKNOWN"

    fuel = revs["fuel"].result
    assert [r["term"] for r in fuel["rows"]] == list(rules.FUEL_TERMS)
    assert fuel["cards"]["expected_use_l"] == {"low": 0, "high": 2.3925} and fuel["cards"]["residual_l"] is None
    assert fuel["basis"]["specific_fuel_consumption_property_revision_id"] == str(SFC.property_revision_id)
    gen_ids = sorted(str(r.evidence_id) for r in inputs.readings if r.role == "generator_power")
    assert fuel["basis"]["generator_power_evidence_ids"] == gen_ids
    assert "specific_fuel_consumption_property_revision_id" not in backup["basis"]

    service = revs["service"].result
    assert [r["role"] for r in service["rows"]] == ["CRITICAL", "UNCLASSIFIED"]
    assert set(service["rows"][0]) == {"asset_id", "asset_code", "load_label", "role", "delivered_kw",
                                       "requested_evidence_state", "assessment", "coverage", "evidence_ids"}

    renewable = revs["renewable"].result
    assert "status" not in renewable and "cards" not in renewable  # composed by the read over selected days
    (day,) = renewable["rows"]
    assert (day["day"], day["from"]) == ("2026-10-06", "2026-10-06T09:00:00.000000Z")
    assert set(day) == {"day", "from", "to", "opportunity_kwh", "constraints", "decision", "coverage",
                        "evidence_ids"}


def test_projection_without_target_and_unknown_domain() -> None:
    backup = projection.project("backup", hour_inputs(target=None)).result
    assert backup["cards"]["critical_recovery"] is None and backup["cards"]["outage_count"] is None
    assert "RECOVERY_TARGET_MISSING" in [l["code"] for l in backup["limitations"]]
    try:
        projection.project("dispatch", hour_inputs())
    except ValueError:
        pass
    else:
        raise AssertionError("an unknown domain must be refused")


def renewable_readings() -> list[Reading]:
    return [*base_readings(), *per_minute("pv_available_power", "20", None), *per_minute("pv_power", "18", None),
            *per_minute("storage_charge_requested_power", "0", None)]


COV_KEYS = {"required_seconds", "observed_seconds", "source_count", "gaps"}
WHOLE = [{"from": "2026-10-06T09:00:00.000000Z", "to": "2026-10-06T10:00:00.000000Z"}]


def test_q6_renewable_hour_shape_and_stored_freshness() -> None:
    """q6 rulings 1 and 5 (projection part; the read-time composition and STALE_SOURCE belong to unit 5)."""
    renewable = projection.project("renewable", hour_inputs(readings=renewable_readings())).result
    assert set(renewable) == {"schema_version", "domain", "hour", "rows", "limitations", "coverage", "basis"}
    assert set(renewable["hour"]) == {"capability_kw", "used_kw", "headroom_kw", "decision"}
    assert len(renewable["rows"]) == 1 and "status" not in renewable and "cards" not in renewable
    assert renewable["basis"]["source_freshness"] == "CURRENT"
    # Removing a required role, or adding an unusable required row, stores UNKNOWN.
    no_pv = [r for r in renewable_readings() if r.role != "pv_power"]
    assert projection.project("renewable", hour_inputs(readings=no_pv)).result["basis"]["source_freshness"] == "UNKNOWN"
    bad = rd("feeder_demand", "8", 30, 31, FEED)
    bad = Reading(bad.evidence_id, SRC, bad.role, FEED, bad.source_time, bad.interval_start, bad.interval_end,
                  "SUSPECT", bad.value, "kW")
    stored = projection.project("renewable", hour_inputs(readings=[*renewable_readings(), bad])).result
    assert stored["basis"]["source_freshness"] == "UNKNOWN"
    # A complete fuel model with tank instants and a witnessed backup PASS both store UNKNOWN.
    full = hour_inputs()
    fuel, backup = (projection.project(d, full).result for d in ("fuel", "backup"))
    assert fuel["cards"]["expected_use_l"] is not None and fuel["basis"]["source_freshness"] == "UNKNOWN"
    assert backup["rows"][0]["result"] == "PASS" and backup["basis"]["source_freshness"] == "UNKNOWN"


def test_q6_fuel_and_backup_row_coverage() -> None:
    """q6 ruling 2."""
    fuel = projection.project("fuel", hour_inputs()).result
    assert len(fuel["rows"]) == 5 and all(set(r["coverage"]) == COV_KEYS for r in fuel["rows"])
    rows = {r["term"]: r["coverage"] for r in fuel["rows"]}
    assert rows["OPENING"] == {"required_seconds": 3600, "observed_seconds": 0, "source_count": 1, "gaps": WHOLE}
    assert rows["USE"]["observed_seconds"] == 3600 and rows["USE"]["gaps"] == []
    for term in ("DELIVERIES", "RESIDUAL"):
        assert rows[term] == {"required_seconds": 3600, "observed_seconds": 0, "source_count": 0, "gaps": WHOLE}

    (chain,) = projection.project("backup", hour_inputs()).result["rows"]
    assert set(chain["coverage"]) == COV_KEYS
    # Outage [09:10, 09:40) with complete aligned critical requested/delivered rows.
    assert chain["coverage"] == {"required_seconds": 1800, "observed_seconds": 1800, "source_count": 1, "gaps": []}
    instants_only = [r for r in base_readings() if not r.role.startswith("critical_load")]
    (bare,) = projection.project("backup", hour_inputs(readings=instants_only)).result["rows"]
    assert bare["coverage"] == {"required_seconds": 1800, "observed_seconds": 0, "source_count": 0,
                                "gaps": [{"from": "2026-10-06T09:10:00.000000Z", "to": "2026-10-06T09:40:00.000000Z"}]}


def test_q6_instant_backup_role_source_count() -> None:
    """q6 ruling 3: distinct sources of usable in-hour observations; the prior witness and bad rows do not count."""
    def basis_of(observations: list[Observation]) -> dict:
        return projection.project("backup", hour_inputs(observations=observations)).result["basis"]

    basis = basis_of(base_observations())
    assert basis["role_coverage"]["site_supply_state"] == {
        "required_seconds": 3600, "observed_seconds": 0, "source_count": 1, "gaps": WHOLE}
    other = ob("site_supply_state", 50, src=uuid4(), state="LOST")
    assert basis_of([*base_observations(), other])["role_coverage"]["site_supply_state"]["source_count"] == 2
    suspect = ob("site_supply_state", 55, src=uuid4(), state="ENERGIZED", quality="SUSPECT")
    basis = basis_of([*base_observations(), suspect])
    assert basis["role_coverage"]["site_supply_state"]["source_count"] == 1
    assert basis["role_coverage"]["site_supply_state"]["observed_seconds"] == 0
    assert str(suspect.evidence_id) in basis["accepted_evidence_ids"]
    # A prior witness from its own source is cited but adds no in-hour source.
    prior = ob("site_supply_state", -5, src=uuid4(), state="ENERGIZED")
    basis = basis_of([prior, *base_observations()[1:]])
    assert basis["role_coverage"]["site_supply_state"]["source_count"] == 1
    assert str(prior.evidence_id) in basis["accepted_evidence_ids"]


def test_q6_sfc_revision_ids() -> None:
    """q6 ruling 4: a change of SFC within the hour keeps both revisions; the scalar is null."""
    change = NOON + timedelta(minutes=30)
    a = rules.SfcValue(uuid4(), Decimal("0.3"), NOON - timedelta(days=30), change)
    b = rules.SfcValue(uuid4(), Decimal("0.4"), change, None)
    fuel = projection.project("fuel", hour_inputs(sfc=(a, b))).result
    # 15 kW over 11-30 min at 0.3 L/kWh plus 15 kW over 30-40 min at 0.4 L/kWh = 2.425 L; upper bound x 1.10.
    assert fuel["cards"]["expected_use_l"] == {"low": 0, "high": 2.6675}
    assert fuel["basis"]["specific_fuel_consumption_property_revision_id"] is None
    assert fuel["basis"]["specific_fuel_consumption_property_revision_ids"] == sorted(
        [str(a.property_revision_id), str(b.property_revision_id)])
    one = projection.project("fuel", hour_inputs()).result["basis"]
    assert one["specific_fuel_consumption_property_revision_id"] == str(SFC.property_revision_id)
    assert one["specific_fuel_consumption_property_revision_ids"] == [str(SFC.property_revision_id)]
    none = projection.project("fuel", hour_inputs(sfc=())).result
    assert none["basis"]["specific_fuel_consumption_property_revision_id"] is None
    assert none["basis"]["specific_fuel_consumption_property_revision_ids"] == []
    assert none["cards"]["expected_use_l"] is None


def test_q6_start_success_count() -> None:
    """q6 ruling 6: null without a witnessed request/result pair; failed pairs support 0; conflicts never count."""
    def count(observations: list[Observation]) -> int | None:
        return projection.project("backup", hour_inputs(observations=observations)).result["cards"][
            "start_success_count"]

    loss = [ob("site_supply_state", -5, state="ENERGIZED"), ob("site_supply_state", 10, state="LOST"),
            ob("site_supply_state", 20, state="ENERGIZED")]
    second = [ob("site_supply_state", 30, state="LOST"), ob("site_supply_state", 50, state="ENERGIZED")]

    def pair(minute: float, outcome: str, corr: str, quality: str = "GOOD") -> list[Observation]:
        return [ob("mini_backup_start_event", minute, kind="START_REQUEST", outcome="REQUESTED", corr=corr),
                ob("mini_backup_start_event", minute + 0.5, kind="START_RESULT", outcome=outcome, corr=corr,
                   quality=quality)]

    assert count([ob("site_supply_state", -5, state="ENERGIZED")]) is None  # no chain
    assert count(loss) is None  # generator-only operation: no witnessed request/result pair
    assert count([*loss, *pair(11, "SUCCEEDED", "c-1", quality="SUSPECT")]) is None  # no usable result
    failed = [*loss, *pair(11, "FAILED", "c-1")]
    assert count(failed) == 0
    assert count([*failed, *second, *pair(31, "SUCCEEDED", "c-2")]) == 1
    conflicting = [*failed, *second, *pair(31, "SUCCEEDED", "c-2"),
                   ob("mini_backup_start_event", 31.7, kind="START_RESULT", outcome="FAILED", corr="c-2")]
    assert count(conflicting) == 0
