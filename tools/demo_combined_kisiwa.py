"""DIESEL-1 K1 (ruling DIESEL-1-R3c §9c.1): the Kisiwa (KISIWA-001) Site, registered the way the combined demo
prepare will register it. K7 (ruling DIESEL-1-R3l §9l.3) adds the story part below the registration.

    python tools/demo_combined_kisiwa.py register <database-url> <work> <import-at ISO> <install-at ISO>
    python tools/demo_combined_kisiwa.py build <database-url> <work>
    python tools/demo_combined_kisiwa.py check <database-url> <work>
    python tools/demo_combined_kisiwa.py preflight <database-url> <work>
    python tools/demo_combined_kisiwa.py add-day <database-url> <work> <night-json>
    python tools/demo_combined_kisiwa.py verify-day <database-url> <work> <night-json>

OWN-G1 (`preflight`, `add-day`, `verify-day`): the nights `tools/demo_combined.py add-dates` adds after the story,
fed through the gateway path and the G3a entry route at DB now (build sheet OWN-GAPS §4.5, Revision 2 R2-G1).

Steps, in order (modelled on `tools/demo_combined_kobo.py` `build` and `configure_at`):
1. import the Site from `backend/tests/fixtures/s1/kisiwa-001.yaml` (the shipped `kisiwa-diesel-hybrid-60kw`
   template rendered for KISIWA-001) at `import_at`;
2. convert its bindings with `backend/conversions/kisiwa-001-bindings.json` (12 rows, minigrid-roles-2) at
   `install_at`;
3. as known at install + 30 min: the three supply uses and the generator's generic no-load fuel rate at
   install + 25 min, then the labelled roles-4 demo configuration (the fuel level sensor's generic accuracy and the
   three roles-4 bindings) at install + 27 min.
`register` (Postgres only) also enables the Site's gateway and source as Kobo's build does and publishes diesel price
v1 at install + 1 h. Kisiwa has no productive load, so no productive-use price is published.

The no-load rate and the sensor accuracy are Site-declared data; their "generic" label travels in their basis
property, never in product copy.

K7 story (`build`, a child of `tools/demo_combined.py prepare --sites ...,kisiwa`): the F0 world (DIESEL-1 §8.3)
moved by a whole number of days onto the story calendar `backend/conversions/demo-kisiwa-story-v1.json`, resolved
against the prepare's one story day S (`resolve`). The shipped log `kisiwa-001-operational-actions-v1.yaml` is never
edited: each prepare writes a derived log `<work>/operational-actions/kisiwa-001-story-{yyyymmdd}-v1.yaml` (every
`at` moved by `delta_days`, nothing else) that K0 freezes into every Kisiwa run. Start states, dip values and the
expected nights come from the day handover `backend/conversions/kisiwa-day-handover-v1.json` (written by
`tools/probe_kisiwa_fuel.py --handover`). Every stamp is a story instant, set through the stores' test-only clocks.
K7-F (DIESEL-1-R3m §9m.5): after the Action's case link, the fuel plan freezes at `plan.freeze_at` and is judged at
`evaluate_at` through K6b's `build_fuel_verification_service`; the verdict is recorded as computed in `kisiwa.json`.
"""

from __future__ import annotations

import contextlib
import copy
import hashlib
import io
import json
import os
import sys
from datetime import date, datetime, time as dtime, timedelta, timezone
from fractions import Fraction
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from demo_combined import StoryClockError, _resolve, at, iso

ROOT = Path(__file__).resolve().parents[1]
CONVERSIONS = ROOT / "backend" / "conversions"

SITE_CODE = "KISIWA-001"
SITE_SOURCE = ROOT / "backend" / "tests" / "fixtures" / "s1" / "kisiwa-001.yaml"
IMPORT_PATH = "var/sites/kisiwa-001.yaml"
BINDINGS = json.loads((CONVERSIONS / "kisiwa-001-bindings.json").read_text(encoding="utf-8"))
ROLES4 = json.loads((CONVERSIONS / "kisiwa-001-minigrid-roles-demo-config.json").read_text(encoding="utf-8"))
FIXTURE_PRICES = CONVERSIONS / "demo-diesel-price-publications.json"

CONFIG_OFFSETS = {"uses": timedelta(minutes=25), "roles4": timedelta(minutes=27), "known": timedelta(minutes=30),
                  "price": timedelta(hours=1)}
#: DIESEL-1 §2.2: what each Kisiwa feeder supplies (load-clinic is the cold store, load-mill the water pump).
SUPPLY_USES = {"load-clinic": "ESSENTIAL_SERVICE", "load-res": "HOUSEHOLD", "load-mill": "HOUSEHOLD"}
SUPPLY_USE_NOTE = "Demonstration supply use declared at commissioning"
NO_LOAD = [
    {"property_key": "generator-no-load-fuel-rate", "value": 4.9, "unit": "L/h", "source": "SITE",
     "source_version": 1},
    {"property_key": "generator-no-load-fuel-rate-basis", "value": "GENERIC_DEFAULT", "unit": "state",
     "source": "SITE", "source_version": 1},
]
NO_LOAD_NOTE = ("Generic no-load fuel rate for a 60 kW diesel set (common design-software default, about 0.08 L/h "
                "per kW of rating); not this generator's datasheet. Owner decision 2026-11-07 (generic, labelled).")
#: The model pin: Kisiwa runs only on mini-grid v7 (K1a). Kobo stays on v6 (`d-verification-window-v3.json`).
RUN_PROFILE = {"model_profile": {"profile_id": "mini-grid", "profile_version": 7},
               "publication_profile": {"profile_id": "registered-kobo-publication", "profile_version": 5},
               "timestep_minutes": 5, "seed": 20260929}


class Clock:
    def __init__(self, now: datetime) -> None:
        self.now = now

    def __call__(self) -> datetime:
        return self.now


def import_source():
    """The import record and the sha256 of the fixture file's bytes."""
    from assetops_backend.sites.adapters.import_files import read_import_source
    from assetops_backend.sites.foundation_service import ImportSource

    read = read_import_source(str(SITE_SOURCE))
    return ImportSource(path=IMPORT_PATH, sha256=read.sha256, record=read.record)


def declare_supply_uses(foundation, imported, effective_from: datetime) -> None:
    for code, use in SUPPLY_USES.items():
        foundation.publish_component_properties(
            imported.tenant, imported.site, asset_code=code, effective_from=effective_from, note=SUPPLY_USE_NOTE,
            properties=[{"property_key": "supply-use", "value": use, "unit": "state", "source": "SITE",
                         "source_version": 1}])


def declare_no_load_rate(foundation, imported, effective_from: datetime) -> None:
    foundation.publish_component_properties(
        imported.tenant, imported.site, asset_code="generator", effective_from=effective_from, note=NO_LOAD_NOTE,
        properties=copy.deepcopy(NO_LOAD))


def configure_roles4(store, foundation, bindings, imported, effective_from: datetime):
    from assetops_backend.sites.demo_configuration import apply_demo_configuration

    doc = copy.deepcopy(ROLES4)
    doc["component_properties"]["effective_from"] = iso(effective_from)
    doc["bindings"]["effective_from"] = iso(effective_from)
    assert doc["status"].startswith("SIMULATED DEMO CONFIGURATION"), doc["status"]
    applied = apply_demo_configuration(store, foundation, bindings, imported.tenant, imported.site, doc)
    assert applied.periods[-1]["role_set"] == "minigrid-roles-4", applied.periods
    return applied


def register_in(store, import_at: datetime, install_at: datetime) -> dict:
    """Import, convert and configure KISIWA-001 in `store` (Postgres or an in-memory Foundation store)."""
    from assetops_backend.sites.binding_conversion import convert
    from assetops_backend.sites.binding_service import BindingService
    from assetops_backend.sites.foundation_service import FoundationService, import_site

    imported = import_site(store, tenant_slug="demo", configured_tenant_slug="demo", source=import_source(),
                           legacy_documents=(), clock=Clock(import_at))
    convert(store, BindingService(store, Clock(install_at)), imported.tenant, imported.site, BINDINGS)
    clock = Clock(install_at + CONFIG_OFFSETS["known"])
    foundation, bindings = FoundationService(store, "demo", clock), BindingService(store, clock)
    declare_supply_uses(foundation, imported, install_at + CONFIG_OFFSETS["uses"])
    declare_no_load_rate(foundation, imported, install_at + CONFIG_OFFSETS["uses"])
    applied = configure_roles4(store, foundation, bindings, imported, install_at + CONFIG_OFFSETS["roles4"])
    return {"site_code": SITE_CODE, "tenant_id": str(imported.tenant.id), "site_id": str(imported.site.id),
            "import_at": iso(import_at), "install_at": iso(install_at),
            "supply_uses_effective_from": iso(install_at + CONFIG_OFFSETS["uses"]),
            "no_load_effective_from": iso(install_at + CONFIG_OFFSETS["uses"]),
            "roles4_effective_from": iso(install_at + CONFIG_OFFSETS["roles4"]),
            "recorded_at": iso(install_at + CONFIG_OFFSETS["known"]),
            "periods": [dict(p) for p in applied.periods]}


def publish_price(url: str, recorded_at: datetime) -> None:
    """Diesel price v1 only, recorded at `recorded_at` through the test-only recorded-time seam (Kobo's pattern)."""
    from assetops_backend.financials.adapters.postgres_assumption_store import PostgresAssumptionStore
    from assetops_backend.publish_assumption import main as publish
    import pg_harness

    store = PostgresAssumptionStore(url, test_recorded_clock_override=lambda: recorded_at)
    try:
        code = publish(["fixture", "--site", SITE_CODE, "--file", str(FIXTURE_PRICES), "--step", "v1"], store=store)
        if code != 0:
            raise SystemExit(f"diesel price v1 publication failed ({code})")
    finally:
        pg_harness.dispose(store)


def register(url: str, work: Path, import_at: datetime, install_at: datetime) -> dict:
    """`register_in` on Postgres, the Site's gateway and source enabled, diesel price v1; writes
    `<work>/kisiwa-register.json`."""
    import pg_harness
    from sqlalchemy import create_engine, text
    from assetops_backend.sites.adapters.postgres_foundation_store import PostgresFoundationStore

    store = PostgresFoundationStore(url)
    engine = create_engine(url)
    try:
        result = register_in(store, import_at, install_at)
        # DIESEL-1-R3r (q12-6): the import carries no legacy documents (`legacy_documents=()` above), so record the
        # explicit NO_LEGACY_EVIDENCE cutover basis with it (w402_demo.py's pattern). Never a comparison; idempotent.
        from uuid import UUID

        store.record_no_legacy_evidence_basis(UUID(result["tenant_id"]), UUID(result["site_id"]), now=import_at)
        with engine.begin() as c:
            c.execute(text("UPDATE gateway SET disabled_at = NULL WHERE site_id = :s"), {"s": result["site_id"]})
            c.execute(text("UPDATE source SET disabled_at = NULL WHERE site_id = :s"), {"s": result["site_id"]})
    finally:
        engine.dispose()
        pg_harness.dispose(store)
    publish_price(url, install_at + CONFIG_OFFSETS["price"])
    result["price_recorded_at"] = iso(install_at + CONFIG_OFFSETS["price"])
    work.mkdir(parents=True, exist_ok=True)
    (work / "kisiwa-register.json").write_text(json.dumps(result, indent=2, sort_keys=True, default=str) + "\n",
                                               encoding="utf-8")
    return result


# ---- K7: the story calendar (DIESEL-1-R3l §9l.3) -------------------------------------------------------------------

STORY_FILE = CONVERSIONS / "demo-kisiwa-story-v1.json"
HANDOVER_FILE = CONVERSIONS / "kisiwa-day-handover-v1.json"
BASE_LOG = ROOT / "config" / "operational-actions" / "kisiwa-001-operational-actions-v1.yaml"
ZONE = "Africa/Dar_es_Salaam"
DAY = timedelta(days=1)
#: The owner's night window (`owner-diesel-night-window-2026-11-07.md`): 6 pm to noon, Site-local.
NIGHT_OPENS_LOCAL = dtime(18, 0)
EFFECT_BEARING = ("FUEL_DELIVERY", "FUEL_REMOVAL_UNRECORDED")
HISTORY_PREFIX = "OPERATIONAL_ACTION"
#: Record literals (§9l.3 step 3), verbatim.
DELIVERY_BODY = "Fuel delivery of {volume_l} L received, ticket {reference}."
TICKET_TEXT = "Fuel delivery ticket {reference}, {volume_l} L"
DIP_BODY = "Tank dip at the {hhmm} round: {dip_l} L."
SITE_VISIT_KEY = "kisiwa-kis-sealed-1"
LOG_HEADER = (
    "# Kisiwa story operational-action log (DIESEL-1-R3l).\n"
    "# Derived by tools/demo_combined_kisiwa.py from config/operational-actions/kisiwa-001-operational-actions-v1.yaml\n"
    "# (sha256 {sha256}) by a move of {days} whole days; no other change.\n"
    "# Lab-private: the product never reads this file. Never edit by hand.\n"
)
#: D-E5.30 (DATA-1): Kisiwa's one recording session. Every night, the story's and every added one, is published on
#: this one sequence epoch through one persistent gateway state (`gateway_dir`, DD1a1-R5; the Kobo pattern
#: `tools/demo_combined_kobo.py` `gateway_dir`), so the sequence continues across nights and across processes. A
#: fresh epoch per night split every 18:00-12:00 night's calendar days across two epochs, and the dispatch cohort
#: (`cohort.py` `_multi_epoch`) refused them as AMBIGUOUS.
KISIWA_EPOCH = "kisiwa-gw-1"


def kisiwa_gateway(work: Path) -> Path:
    """D-E5.30: the Site's one gateway state, under the prepare's `work`, shared by `build` and `add-day`."""
    return work / "kisiwa-gateway"


def after_previous_night(previous_end: datetime | None):
    """D-E5.30 seam rule (Kobo's `keep`, `demo_story_days.DayRun.keep`): on the one session, a night after the
    session's first sends only the instants after the previous night's end. Consecutive nights share their boundary
    instant (night k ends where night k+1 starts), and two readings of one channel at one instant on one epoch are a
    `REPORTS_OVERLAP` (`cohort.py` `series_limits`), which `dispatch_v3` answers `AMBIGUOUS_SERIES`. The previous
    night keeps the boundary reading. None (the session's first night) sends everything."""
    if previous_end is None:
        return None
    bound = previous_end.astimezone(timezone.utc)

    def keep(source_time: str) -> bool:
        return datetime.fromisoformat(source_time.replace("Z", "+00:00")) > bound
    return keep


def story_previous_end(kisiwa: dict, k: int) -> datetime | None:
    """The end of story run k-1 (None for run 1, the session's first night): `publish_night`'s `previous_end`."""
    return at(kisiwa["runs"][k - 2]["end"]) if k > 1 else None


def publish_night(rp, tmp: Path, work: Path, run, received_at: datetime, previous_end: datetime | None) -> dict:
    """D-E5.30: one night's readings through the real gateway on Kisiwa's one session (`KISIWA_EPOCH`, reopening
    `kisiwa_gateway(work)`); `tmp` keeps the night's own host and replay files. `previous_end`: the end of the
    night published before it on the session (None for the session's first), see `after_previous_night`.
    DATA-5: the gateway's diagnostics are stored through the product ingestion, so Kisiwa Health has a report."""
    return rp._publish_and_accept(tmp, run, KISIWA_EPOCH, received_at, gateway_dir=kisiwa_gateway(work),
                                  keep=after_previous_night(previous_end), diagnostics=True)


def wire(value: datetime) -> str:
    """The Work API's instant form (microseconds, Z), as `tools/demo_combined_mill.py` `wire`."""
    return value.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


#: The night with the unexplained fuel (run 4); K4a raises its Finding and no other night's.
INCIDENT_K = 4


def load_story_doc(path: Path = STORY_FILE) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def load_handover(path: Path = HANDOVER_FILE) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def local_date(instant: datetime) -> date:
    return instant.astimezone(ZoneInfo(ZONE)).date()


def night_opens(night: date) -> datetime:
    return datetime.combine(night, NIGHT_OPENS_LOCAL, tzinfo=ZoneInfo(ZONE)).astimezone(timezone.utc)


def log_instant(value: datetime) -> str:
    return value.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def resolve(S: datetime, doc: dict | None = None) -> dict:
    """The Kisiwa block of `story.json`: every calendar instant resolved against S, the whole-day move, the runs and
    their receive/assess/raise instants. Raises `STORY_SHIFT_NOT_WHOLE_DAYS` (S-1) and `STORY_CLOCK_ORDER` (S-2)."""
    doc = doc if doc is not None else load_story_doc()
    r = _resolve(doc, S)
    run1, base = at(r["run1_start"]), at(doc["base_run1_start"])
    shift = run1 - base
    if shift % DAY:
        raise StoryClockError(f"STORY_SHIFT_NOT_WHOLE_DAYS: run 1 starts at {iso(run1)}, {shift} after the F0 world's "
                              f"{iso(base)}; only a whole number of days keeps F0's readings")
    received, assessed, raised = (timedelta(minutes=doc[f"{n}_after_run_end_minutes"])
                                  for n in ("received", "assess", "raise"))
    runs = []
    for k in range(1, doc["runs"] + 1):
        start = run1 + (k - 1) * DAY
        end = start + DAY
        runs.append({"k": k, "start": iso(start), "end": iso(end), "night_date": local_date(start).isoformat(),
                     "received_at": iso(end + received), "assessed_at": iso(end + assessed),
                     "raised_at": iso(end + raised)})
    action = r["action"]
    out = {"schema": doc["schema"], "label": doc["label"], "base_log": doc["base_log"],
           "base_run1_start": doc["base_run1_start"], "delta_days": shift // DAY,
           "story_log_id": doc["story_log_id_prefix"] + local_date(run1).strftime("%Y%m%d"), "log_version": 1,
           "import_at": r["import_at"], "install_at": r["install_at"], "setup_at": r["setup_at"],
           "run1_start": iso(run1), "runs": runs,
           "dip_recorded_after_minutes": doc["dip_recorded_after_minutes"],
           "site_visit_recorded_at": iso(at(action["site_visit"]["occurred_at"])
                                         + timedelta(minutes=doc["site_visit_recorded_after_minutes"])),
           "action": action, "plan": r["plan"], "evaluate_at": r["evaluate_at"]}
    check_order(order_chain(out))
    check_equalities(out)
    return out


def order_chain(k: dict) -> list[tuple[str, datetime]]:
    """§9l.3's order check, in order: each instant must come before the next (stop S-2)."""
    runs, a = k["runs"], k["action"]
    return [("night 4 raise", at(runs[3]["raised_at"])), ("action.raised_at", at(a["raised_at"])),
            ("action.request.occurred_at", at(a["request"]["occurred_at"])), ("action.assign_at", at(a["assign_at"])),
            ("action.record.occurred_at", at(a["record"]["occurred_at"])), ("action.complete_at", at(a["complete_at"])),
            ("action.change_recorded_from", at(a["change_recorded_from"])),
            ("site visit recorded", at(k["site_visit_recorded_at"])), ("action.case_link_at", at(a["case_link_at"])),
            ("plan.freeze_at", at(k["plan"]["freeze_at"])),
            ("night 6 window start", night_opens(date.fromisoformat(runs[5]["night_date"]))),
            ("night 8 assessed", at(runs[7]["assessed_at"])), ("evaluate_at", at(k["evaluate_at"])),
            ("run 10 received", at(runs[9]["received_at"]))]


def check_order(chain: list[tuple[str, datetime]]) -> None:
    for (n1, t1), (n2, t2) in zip(chain, chain[1:]):
        if not t1 < t2:
            raise StoryClockError(f"STORY_CLOCK_ORDER: {n1} {iso(t1)} is not before {n2} {iso(t2)}")


def check_equalities(k: dict) -> None:
    """The order check's side conditions: the request is recorded no earlier than it occurred and before the
    assignment; the maintenance record occurs at `effective_at`, which is run 6's start."""
    a = k["action"]
    request, recorded_from = at(a["request"]["occurred_at"]), at(a["request_recorded_from"])
    if not request <= recorded_from < at(a["assign_at"]):
        raise StoryClockError(f"STORY_CLOCK_ORDER: request occurs {iso(request)}, recorded from {iso(recorded_from)}, "
                              f"assigned {a['assign_at']}")
    record, effective, run6 = at(a["record"]["occurred_at"]), at(a["effective_at"]), at(k["runs"][5]["start"])
    if not record == effective == run6:
        raise StoryClockError(f"STORY_CLOCK_ORDER: the record occurs {iso(record)}, effective {iso(effective)}, run 6 "
                              f"starts {iso(run6)}; all three must be one instant")


# ---- K7: the derived log and the straddle check ---------------------------------------------------------------------

def lf_sha256(text: str) -> str:
    return hashlib.sha256(text.replace("\r\n", "\n").encode("utf-8")).hexdigest()


def parse_log(text: str) -> dict:
    """A log text through the run adapters' one YAML load point (K0's loader reads the derived JSON unchanged)."""
    from assetops_backend.runs.adapters.yaml_run_documents import load_yaml_text

    return load_yaml_text(text.replace("\r\n", "\n"))


def move_action(action: dict, delta_days: int) -> dict:
    moved = copy.deepcopy(action)
    moved["at"] = log_instant(at(action["at"]) + delta_days * DAY)
    if "sensor_disconnected" in moved:
        moved["sensor_disconnected"]["at"] = log_instant(at(action["sensor_disconnected"]["at"]) + delta_days * DAY)
    return moved


def derived_log(base_text: str, kisiwa: dict) -> tuple[str, dict]:
    """The story log's text and parsed document: v1 with `log_id` the story id and every `at` (and
    `sensor_disconnected.at`) moved by `delta_days`. Stop S-3 when v1's LF hash is not the calendar's."""
    want = kisiwa["base_log"]["sha256"]
    got = lf_sha256(base_text)
    if got != want:
        raise SystemExit(f"BASE_LOG_CHANGED (stop S-3): the shipped log's LF sha256 is {got}, the calendar pins {want}")
    doc = parse_log(base_text)
    moved = {key: value for key, value in doc.items()}
    moved["log_id"] = kisiwa["story_log_id"]
    moved["actions"] = [move_action(a, kisiwa["delta_days"]) for a in doc["actions"]]
    text = LOG_HEADER.format(sha256=want, days=kisiwa["delta_days"]) + json.dumps(moved, indent=2,
                                                                                  ensure_ascii=True) + "\n"
    return text, moved


def write_derived_log(work: Path, text: str, kisiwa: dict) -> Path:
    root = work / "operational-actions"
    root.mkdir(parents=True, exist_ok=True)
    path = root / f"{kisiwa['story_log_id']}-v{kisiwa['log_version']}.yaml"
    path.write_text(text, encoding="utf-8", newline="\n")
    return path


def action_spans(action: dict) -> list[tuple[datetime, datetime | None]]:
    """(start, end) of an action's spans; `end` None for a point action (span `[at, at]`)."""
    start = at(action["at"])
    if action["kind"] != "FUEL_REMOVAL_UNRECORDED":
        return [(start, None)]
    spans = [(start, start + timedelta(minutes=action["duration_minutes"]))]
    sensor = action.get("sensor_disconnected")
    if sensor is not None:
        s = at(sensor["at"])
        spans.append((s, s + timedelta(minutes=sensor["duration_minutes"])))
    return spans


def straddle_check(actions: list[dict], runs: list[tuple[datetime, datetime]]) -> dict[str, int]:
    """K0's residual (§9l.3): every action's spans lie inside exactly one run's `[start, end)`; stop S-4 otherwise.
    Returns action id -> run number (1-based)."""
    placed = {}
    for action in actions:
        spans = action_spans(action)
        inside = [k for k, (lo, hi) in enumerate(runs, start=1)
                  if all(lo <= s < hi if e is None else (lo <= s and e <= hi) for s, e in spans)]
        if len(inside) != 1:
            raise SystemExit(f"ACTION_STRADDLES_RUN (stop S-4): action {action['action_id']} spans "
                             f"{[(iso(s), iso(e) if e else None) for s, e in spans]} and lies inside runs {inside}")
        placed[action["action_id"]] = inside[0]
    return placed


def expected_history(actions: list[dict], placed: dict[str, int], k: int) -> list[str]:
    """Run k's frozen `intervention_history`: its effect-bearing actions, as K0 freezes them (instant, id order)."""
    from assetops_backend.runs.operational_actions import content_sha256

    mine = sorted((a for a in actions if placed[a["action_id"]] == k and a["kind"] in EFFECT_BEARING),
                  key=lambda a: (at(a["at"]), a["action_id"]))
    return [f"{HISTORY_PREFIX}:{a['action_id']}:{content_sha256(a)}" for a in mine]


# ---- K7: the injector (records through K2's Work API) -------------------------------------------------------------

def record_post(action: dict, kisiwa: dict, dips: dict[str, int]) -> dict | None:
    """The Work API record an operational action produces, or None (the removal, the seal and the sensor fix: the
    seal and the sensor fix become the one SITE_VISIT, `site_visit_post`). `oprec` keywords plus `recorded_at`."""
    kind, occurred = action["kind"], at(action["at"])
    if kind == "FUEL_DELIVERY":
        ticket = action["ticket"]
        text = TICKET_TEXT.format(reference=ticket["reference"], volume_l=action["volume_l"])
        return {"key": f"kisiwa-{action['action_id']}", "kind": "FUEL_DELIVERY",
                "body": DELIVERY_BODY.format(volume_l=action["volume_l"], reference=ticket["reference"]),
                "occurred_at": action["at"], "unit": "L", "quantity": str(action["volume_l"]),
                "source_document_sha256": hashlib.sha256(text.encode("ascii")).hexdigest(), "tank": True,
                "recorded_at": iso(occurred + timedelta(minutes=action["recorded_after_minutes"]))}
    if kind == "TANK_DIP":
        litres = str(dips[action["action_id"]])
        hhmm = occurred.astimezone(ZoneInfo(ZONE)).strftime("%H:%M")
        return {"key": f"kisiwa-{action['action_id']}", "kind": "TANK_DIP",
                "body": DIP_BODY.format(hhmm=hhmm, dip_l=litres), "occurred_at": action["at"], "unit": "L",
                "quantity": litres, "source_document_sha256": None, "tank": True,
                "recorded_at": iso(occurred + timedelta(minutes=kisiwa["dip_recorded_after_minutes"]))}
    return None


def site_visit_post(kisiwa: dict, case_id: str | None) -> dict:
    """The one SITE_VISIT covering TANK_SEALED and SENSOR_POWER_PROTECTED; it cites the Action's maintenance case."""
    visit = kisiwa["action"]["site_visit"]
    return {"key": SITE_VISIT_KEY, "kind": "SITE_VISIT", "body": visit["body"], "occurred_at": visit["occurred_at"],
            "unit": None, "quantity": None, "source_document_sha256": None, "tank": False, "case_id": case_id,
            "recorded_at": kisiwa["site_visit_recorded_at"]}


def timeline(kisiwa: dict, posts: list[dict]) -> list[tuple[datetime, int, str, Any]]:
    """One event timeline sorted by instant; ties go record posts, then publish, then assess, then raise."""
    events: list[tuple[datetime, int, str, Any]] = [(at(p["recorded_at"]), 0, "record", p) for p in posts]
    for r in kisiwa["runs"]:
        events += [(at(r["received_at"]), 1, "publish", r["k"]), (at(r["assessed_at"]), 2, "assess", r["k"]),
                   (at(r["raised_at"]), 3, "raise", r["k"])]
    return sorted(events, key=lambda e: (e[0], e[1], str(e[3]) if e[2] == "record" else e[3]))


# ---- K7: build (a child of `tools/demo_combined.py prepare`) --------------------------------------------------------

class SetClock:
    """A store's virtual DB instant: whatever the build last set (the stores' test-only clock seam)."""

    def __init__(self, now: datetime) -> None:
        self.now = now

    def __call__(self) -> datetime:
        return self.now


def story_registered(store, setup_at: str, run1_start: str, actions):
    """`host/tests/kisiwa.py` `KisiwaRegistered`, its basis selected at the story's run 1 (its own constructor
    selects at F0's absolute 2026-10-01, before a story install exists). `draft` and `sim` are unchanged."""
    from kisiwa import SITE_ID, KisiwaRegistered
    from assetops_backend.runs.profiles import MINI_GRID_V7_MODEL
    from assetops_backend.runs.registered_basis import RegisteredLabBasis
    from assetops_backend.sites.cutover import ImportedSiteRegistry
    from assetops_backend.sites.foundation_service import FoundationService
    from assetops_simulator.packs import mini_grid

    reg = KisiwaRegistered.__new__(KisiwaRegistered)
    reg.store, reg.setup_at, reg.actions = store, setup_at, actions
    moment = at(setup_at)
    reg.basis = RegisteredLabBasis(ImportedSiteRegistry(FoundationService(store, "demo", lambda: moment)))
    reg.v7_sim, reg.v7_profile = mini_grid.MINI_GRID_V7_MODEL, MINI_GRID_V7_MODEL
    selection = reg.basis.select(SITE_ID, start_time=run1_start, end_time=iso(at(run1_start) + DAY),
                                 knowledge_at=None)
    reg.foundation_version = selection.basis.foundation_version
    return reg


def run_guards(run, reg, k: int, handover: dict, actions: list[dict], placed: dict[str, int], log_sha: str,
               kisiwa: dict) -> dict:
    """Stop S-5 guards for run k: history and log hash, physics (end state), dips (rounded tank at each dip)."""
    import probe_kisiwa_fuel as probe
    from execution_adapter import run_to_end

    identity = run.deterministic_identity
    want_history = expected_history(actions, placed, k)
    got_history = list(identity.intervention_history)
    h_ids = [e.split(":")[1] for e in handover["runs"][k - 1]["intervention_history"]]
    if got_history != want_history or [e.split(":")[1] for e in got_history] != h_ids:
        raise SystemExit(f"RUN_GUARD_HISTORY (stop S-5): run {k} froze {got_history}; want {want_history} "
                         f"(F0 ids {h_ids})")
    frozen = identity.operational_action_log
    got_log = None if frozen is None else (frozen.log_id, frozen.log_version, frozen.sha256)
    if got_log != (kisiwa["story_log_id"], 1, log_sha):
        raise SystemExit(f"RUN_GUARD_LOG (stop S-5): run {k} froze log {got_log}; want "
                         f"{(kisiwa['story_log_id'], 1, log_sha)}")
    trajectory = run_to_end(run, reg.sim("v7")).trajectory
    last = dict(trajectory.boundaries[-1].stocks)
    end = handover["runs"][k - 1]["end"]
    got_end, want_end = (last[probe.SOC], last[probe.FUEL]), (Fraction(end["soc"]), Fraction(end["fuel"]))
    if got_end != want_end:
        raise SystemExit(f"RUN_GUARD_PHYSICS (stop S-5): run {k} ends at (soc, tank) {got_end}; F0 {want_end}")
    start = at(handover["base_run1_start"]) + (k - 1) * DAY + kisiwa["delta_days"] * DAY
    dips = []
    want_dips = {d["action_id"]: d["dip_l"] for d in handover["dips"]}
    for action in actions:
        if action["kind"] != "TANK_DIP" or placed[action["action_id"]] != k:
            continue
        offset = int((at(action["at"]) - start).total_seconds()) // 60
        stock = dict(trajectory.boundaries[offset // probe.STEP].stocks)[probe.FUEL]
        litres = probe._round_litre(stock)
        if offset % probe.STEP or litres != want_dips[action["action_id"]]:
            raise SystemExit(f"RUN_GUARD_DIP (stop S-5): run {k} dip {action['action_id']} at offset {offset} reads "
                             f"{litres} L; F0 {want_dips[action['action_id']]} L")
        dips.append({"action_id": action["action_id"], "offset_minutes": offset, "dip_l": litres})
    return {"history": got_history, "log_id": frozen.log_id, "log_sha256": frozen.sha256,
            "physics": {"soc": str(got_end[0]), "fuel": str(got_end[1]), "equal": True}, "dips": dips}


def _cli_lines(call) -> tuple[int, list[dict]]:
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        code = call()
    return code, [json.loads(x) for x in buffer.getvalue().splitlines() if x.startswith("{")]


def assess_night(store, clock: SetClock, instant: datetime, night: str) -> dict:
    """K3's CLI entry point, in process, with the store's clock at the story instant (§9l.1 item 5)."""
    from assetops_backend.fuel_balance.worker import main as fuel_balance_cli

    clock.now = instant
    nxt = (date.fromisoformat(night) + DAY).isoformat()
    code, lines = _cli_lines(lambda: fuel_balance_cli(
        ["assess", "--site", SITE_CODE, "--from", night, "--to", nxt], store=store))
    if code != 0 or len(lines) != 1 or (lines[0]["status"], lines[0]["revision"]) != ("APPENDED", 1):
        raise SystemExit(f"ASSESS_STATUS (stop S-6): night {night} at {iso(instant)} printed {lines} (exit {code}); "
                         "want one APPENDED line, revision 1")
    return lines[0]


def raise_night(url: str, tenant, site, night: str, instant: datetime, k: int) -> dict:
    """K4a's `worker.main(["raise", ...])` in process, its Finding service on the story instant: night 4 OPENED, every
    other night NO_FINDING (stop S-6). Returns the printed line (`finding_id`, `revision_id` are the Finding's)."""
    from assetops_backend.fuel_balance.composition import build_fuel_finding_service
    from assetops_backend.fuel_balance.worker import main as fuel_balance_cli

    want = "OPENED" if k == INCIDENT_K else "NO_FINDING"
    nxt = (date.fromisoformat(night) + DAY).isoformat()
    service = build_fuel_finding_service(url, test_db_clock_override=lambda: instant)
    try:
        code, lines = _cli_lines(lambda: fuel_balance_cli(
            ["raise", "--site", SITE_CODE, "--from", night, "--to", nxt], finding_service=service))
    finally:
        service.dispose()
    if code != 0 or len(lines) != 1 or lines[0]["status"] != want:
        raise SystemExit(f"RAISE_STATUS (stop S-6): night {night} at {iso(instant)} printed {lines} (exit {code}); "
                         f"want one {want} line")
    return lines[0]


def record_action(url: str, engine, tenant, site, kisiwa: dict, finding: dict) -> dict:
    """§9l.3 step 5 with §9m.5's domain: the Action from the night-4 Finding, its maintenance request, ASSIGN, the
    change record, COMPLETE, the SITE_VISIT record citing the case, and the case link, each at its story instant.
    Follows `tools/demo_combined_mill.py` `record_change`. The fuel Action's request link has no page before K6b, so
    nothing in the demo path may follow it."""
    from sqlalchemy import text
    from test_w401_work_service_postgres import ACTOR, PRINCIPAL, oprec

    from assetops_backend.work.composition import build_domain_intent_service, build_work_service
    from demo_story_clock import StepClock

    a = kisiwa["action"]
    domain, work = build_domain_intent_service(url), build_work_service(url)
    try:
        raised = at(a["raised_at"])
        domain._store.test_db_clock_override = lambda: raised
        status, action = domain.create_action(tenant, site, SITE_CODE, {
            "domain": "FUEL_BALANCE", "origin_finding_id": finding["finding_id"],
            "origin_finding_revision_id": finding["revision_id"], "title": a["title"],
            "owner_label": a["owner_label"], "due_at": None, "raised_at": wire(raised), "actor": dict(ACTOR),
            "idempotency_key": "kisiwa-fuel-action"}, PRINCIPAL)
        if status != 201:
            raise SystemExit(f"ACTION_REFUSED (stop S-7; a K6a defect): create_action answered {status}: {action}")
        # the request at its own instant, ASSIGN on a clock at assign_at (its occurred_at is 10 min after the request,
        # beyond the 5 minute future slack of the request's clock)
        work._store.test_db_clock_override = StepClock(at(a["request_recorded_from"]))
        s, case = work.create_case(tenant, site, {
            "kind": "MAINTENANCE_REQUEST", "occurred_at": a["request"]["occurred_at"], "asset_id": None,
            "finding_links": [], "action_links": [], "title": a["request"]["title"],
            "narrative": a["request"]["narrative"], "cited_accepted_evidence_ids": [], "actor": dict(ACTOR),
            "idempotency_key": "kisiwa-fuel-request"}, PRINCIPAL)
        if s != 201:
            raise SystemExit(f"CASE_REFUSED: create_case answered {s}: {case}")
        case_id, rev_id = case["id"], case["revision"]["id"]
        assigned = at(a["assign_at"])
        work._store.test_db_clock_override = StepClock(assigned)
        s, got = work.post_event(tenant, site, case_id, {
            "kind": "ASSIGN", "occurred_at": a["assign_at"], "payload": {"assignee": a["owner_label"]},
            "actor": dict(ACTOR), "idempotency_key": "kisiwa-fuel-assign"}, PRINCIPAL)
        if s != 201:
            raise SystemExit(f"CASE_REFUSED: ASSIGN answered {s}: {got}")
        # the change, on a second clock
        changed = StepClock(at(a["change_recorded_from"]))
        work._store.test_db_clock_override = changed
        s, rec = work.post_record(tenant, site, case_id, {
            "activity": a["record"]["activity"], "outcome_note": None, "occurred_at": a["record"]["occurred_at"],
            "actor": dict(ACTOR), "idempotency_key": "kisiwa-fuel-record"}, PRINCIPAL)
        if s != 201:
            raise SystemExit(f"CASE_REFUSED: post_record answered {s}: {rec}")
        s, done = work.post_event(tenant, site, case_id, {
            "kind": "COMPLETE", "occurred_at": a["complete_at"], "payload": {"maintenance_record_id": rec["id"]},
            "actor": dict(ACTOR), "idempotency_key": "kisiwa-fuel-complete"}, PRINCIPAL)
        if s != 201:
            raise SystemExit(f"CASE_REFUSED: COMPLETE answered {s}: {done}")
        # the one SITE_VISIT citing the case
        post = site_visit_post(kisiwa, case_id)
        visit_at = at(post["recorded_at"])
        if changed.last >= visit_at:
            raise SystemExit(f"STORY_CLOCK_ORDER: last change command {changed.last} is not before the visit {visit_at}")
        work._store.test_db_clock_override = lambda: visit_at
        s, visit = work.post_operational_record(tenant, site, oprec(
            post["key"], kind=post["kind"], body=post["body"], occurred_at=post["occurred_at"], unit=None,
            quantity=None, source_document_sha256=None, case_id=case_id), PRINCIPAL)
        if s != 201:
            raise SystemExit(f"RECORD_REFUSED: {post['key']} answered {s}: {visit}")
        # the link
        link_at = at(a["case_link_at"])
        if visit_at >= link_at:
            raise SystemExit(f"STORY_CLOCK_ORDER: the visit {visit_at} is not before the link {link_at}")
        with engine.connect() as c:
            head = str(c.execute(text("SELECT id FROM work_event WHERE case_id = :c ORDER BY recorded_at DESC, id DESC "
                                      "LIMIT 1"), {"c": case_id}).scalar_one())
        domain._store.test_db_clock_override = lambda: link_at
        s, linked = domain.post_case_link(tenant, site, SITE_CODE, action["id"], {
            "case_id": case_id, "case_revision_id": rev_id, "case_event_id": head, "actor": dict(ACTOR),
            "idempotency_key": "kisiwa-fuel-link"}, PRINCIPAL)
        if s != 201:
            raise SystemExit(f"LINK_REFUSED: post_case_link answered {s}: {linked}")
        return {"id": action["id"], "code": action["action_code"], "recorded_at": action["recorded_at"],
                "case_id": case_id, "case_state": done.get("state"), "case_link_recorded_at": linked["recorded_at"],
                "site_visit_code": visit.get("public_code"), "site_visit_recorded_at": post["recorded_at"],
                "finding_id": finding["finding_id"], "finding_revision_id": finding["revision_id"]}
    finally:
        domain._store.dispose()
        work._store.dispose()


def freeze_and_evaluate(url: str, engine, tenant, site, kisiwa: dict, action: dict) -> dict:
    """K7-F (§9l.3 "The freeze step", exact in §9m.5): freeze the Action's `fuel-residual-within-band-1` plan at
    `plan.freeze_at` and judge it at `evaluate_at`, each through K6b's service on its test-only clock. The asserts are
    stop S-6. The verdict is recorded as computed, never asserted; NOT_JUDGED is stop S-6."""
    from uuid import UUID

    import pg_harness
    from sqlalchemy import text

    from assetops_backend.actions.composition import build_fuel_verification_service

    def service(instant: datetime):
        return build_fuel_verification_service(url, test_clock=lambda: instant)

    def dispose(svc) -> None:
        pg_harness.dispose(svc.store)
        svc.actions.verification_ports.fuel_windows.dispose()

    action_id = UUID(action["id"])
    freeze_at, evaluate_at = at(kisiwa["plan"]["freeze_at"]), at(kisiwa["evaluate_at"])
    svc = service(freeze_at)
    try:
        status, frozen = svc.freeze_fuel_plan(tenant, site, action_id)
    finally:
        dispose(svc)
    plan = frozen.get("plan") or {}
    run4, run6 = kisiwa["runs"][INCIDENT_K - 1], kisiwa["runs"][5]
    with engine.connect() as c:  # night 4's window: its latest revision as stored
        night4 = str(c.execute(text("SELECT id FROM fuel_balance_window WHERE site_id = :s AND night_date = :d "
                                    "ORDER BY revision DESC LIMIT 1"),
                               {"s": site, "d": date.fromisoformat(run4["night_date"])}).scalar_one())
    effective = plan.get("effective_from")
    want = {"status": (status, 201),
            "effective_from": (effective and iso(at(effective)), iso(at(kisiwa["action"]["complete_at"]))),
            "effective_from before night 6": (bool(effective) and at(effective) < night_opens(
                date.fromisoformat(run6["night_date"])), True),
            "candidates.from": ((plan.get("later_selection_rule") or {}).get("candidates", {}).get("from"),
                                run6["night_date"]),
            "baseline window": ((plan.get("baseline_selection") or {}).get("window_id"), night4),
            "recorded_at": (plan.get("recorded_at") and iso(at(plan["recorded_at"])), iso(freeze_at))}
    bad = {k: v for k, v in want.items() if v[0] != v[1]}
    if bad:
        raise SystemExit(f"FREEZE (stop S-6): {bad}; answered {status}: {frozen}")
    svc = service(evaluate_at)
    try:
        judged = svc.evaluate_fuel_plan(tenant, site, action_id)
        summary = svc.fuel_summary(tenant, site, action_id, SITE_CODE)
    finally:
        dispose(svc)
    if judged.get("state") not in ("VERIFIED", "INEFFECTIVE", "INCONCLUSIVE") or not judged.get("stored"):
        raise SystemExit(f"EVALUATE (stop S-6): the evaluation at {iso(evaluate_at)} answered {judged}")
    return {"plan": {"plan_id": plan["plan_id"], "status": status, "recorded_at": plan["recorded_at"],
                     "effective_from": effective, "later_candidates": plan["later_selection_rule"]["candidates"],
                     "baseline_window_id": plan["baseline_selection"]["window_id"]},
            "verdict": {**judged, "evaluated_at": iso(evaluate_at)}, "summary": summary}


def threads(work: Path) -> list[dict]:
    """§9l.3 step 4: the Kisiwa-only chain backfill, as a child process in this tree (no other Site's thread)."""
    import subprocess

    done = subprocess.run([sys.executable, "-m", "assetops_backend.chain.backfill", "--site", SITE_CODE, "--steps",
                           "a,b,c,d"], capture_output=True, text=True, check=False)
    (work / "kisiwa-threads.log").write_text(done.stdout + done.stderr, encoding="utf-8")
    if done.returncode != 0:
        raise SystemExit(f"THREADS_FAILED: chain backfill --site {SITE_CODE} exited {done.returncode}: "
                         f"{(done.stdout + done.stderr)[-2000:]}")
    return [json.loads(x) for x in done.stdout.splitlines() if x.startswith("{")]


def build(url: str, work: Path) -> dict:
    """§9l.3 steps 1-7. Refuses a database `require_prepare_database` does not accept."""
    import time as clock_time

    import pg_harness
    import probe_kisiwa_nights as nights
    import test_s6_verification_replay as rp
    from sqlalchemy import create_engine, text
    from test_w401_work_service_postgres import PRINCIPAL, oprec

    from assetops_backend.fuel_balance.composition import build_fuel_balance_store
    from assetops_backend.prepare_clock import require_prepare_database
    from assetops_backend.runs.adapters.yaml_operational_action_log import YamlOperationalActionLog
    from assetops_backend.sites.adapters.postgres_foundation_store import PostgresFoundationStore
    from assetops_backend.work.composition import build_work_service

    require_prepare_database(url)
    began = clock_time.monotonic()
    # 1. inputs, the derived log, the straddle check
    story = json.loads((work / "story.json").read_text(encoding="utf-8"))
    kisiwa = story["kisiwa"]
    handover = load_handover()
    log_text, log_doc = derived_log(BASE_LOG.read_text(encoding="utf-8"), kisiwa)
    log_path = write_derived_log(work, log_text, kisiwa)
    log_sha = lf_sha256(log_path.read_text(encoding="utf-8"))
    actions = log_doc["actions"]
    runs = [(at(r["start"]), at(r["end"])) for r in kisiwa["runs"]]
    placed = straddle_check(actions, runs)
    out: dict[str, Any] = {"delta_days": kisiwa["delta_days"],
                           "log": {"path": str(log_path), "log_id": kisiwa["story_log_id"], "log_version": 1,
                                   "sha256": log_sha},
                           "placed": placed, "runs": [], "records": [], "nights": [], "cli": {}}
    # 2. register (K1, unchanged)
    t0 = clock_time.monotonic()
    out["register"] = register(url, work, at(kisiwa["import_at"]), at(kisiwa["install_at"]))
    out["register_seconds"] = round(clock_time.monotonic() - t0, 1)
    tenant, site = out["register"]["tenant_id"], out["register"]["site_id"]
    engine = create_engine(url)
    with engine.connect() as c:
        tank = str(c.execute(text("SELECT id FROM asset WHERE site_id = :s AND asset_type = 'FUEL_TANK' "
                                  "AND retired_at IS NULL"), {"s": site}).scalar_one())
    from uuid import UUID

    tenant_id, site_id = UUID(tenant), UUID(site)
    dips = {d["action_id"]: d["dip_l"] for d in handover["dips"]}
    posts = [p for p in (record_post(a, kisiwa, dips) for a in actions) if p is not None]
    foundation = PostgresFoundationStore(url)
    work_service = build_work_service(url)
    fb_clock = SetClock(at(kisiwa["install_at"]))
    fb_store = build_fuel_balance_store(url, test_db_clock_override=fb_clock)
    actions_port = YamlOperationalActionLog(root=log_path.parent)
    by_k = {r["k"]: r for r in kisiwa["runs"]}
    try:
        # 3. the timeline
        for instant, _, kind, item in timeline(kisiwa, posts):
            if kind == "record":
                recorded = at(item["recorded_at"])
                work_service._store.test_db_clock_override = lambda when=recorded: when
                body = oprec(item["key"], kind=item["kind"], body=item["body"], occurred_at=item["occurred_at"],
                             unit=item["unit"], quantity=item["quantity"],
                             source_document_sha256=item["source_document_sha256"], asset_id=tank)
                status, response = work_service.post_operational_record(tenant_id, site_id, body, PRINCIPAL)
                if status != 201:
                    raise SystemExit(f"RECORD_REFUSED: {item['key']} answered {status}: {response}")
                out["records"].append({"code": response.get("public_code"), "kind": item["kind"],
                                       "occurred_at": item["occurred_at"], "recorded_at": item["recorded_at"],
                                       "quantity": item["quantity"], "key": item["key"]})
            elif kind == "publish":
                r, t0 = by_k[item], clock_time.monotonic()
                state = handover["runs"][item - 1]["start"]
                reg = story_registered(foundation, kisiwa["setup_at"], kisiwa["run1_start"], actions_port)
                run = reg.draft(nights.day_document(float(Fraction(state["soc"])), float(Fraction(state["fuel"]))),
                                r["start"], r["end"], "v7",
                                {"log_id": kisiwa["story_log_id"], "log_version": 1})
                if run.execution_status != "READY" or run.registered_basis is None:
                    raise SystemExit(f"RUN_NOT_READY: run {item}: {run.execution_status} "
                                     f"{[(b.kind, b.subject) for b in run.blocking_reasons]}")
                guards = run_guards(run, reg, item, handover, actions, placed, log_sha, kisiwa)
                published = publish_night(rp, work / "kisiwa-replay" / f"r{item:02d}", work, run, instant,
                                          story_previous_end(kisiwa, item))
                out["runs"].append({"k": item, "run_id": run.run_id, "start": r["start"], "end": r["end"],
                                    "received_at": iso(instant), **guards, "published": published,
                                    "seconds": round(clock_time.monotonic() - t0, 1)})
            elif kind == "assess":
                line = assess_night(fb_store, fb_clock, instant, by_k[item]["night_date"])
                out["nights"].append({"k": item, "night_date": by_k[item]["night_date"], "assessed_at": iso(instant),
                                      "line": line})
            else:
                out["nights"][-1]["raise"] = raise_night(url, tenant_id, site_id, by_k[item]["night_date"], instant,
                                                         item)
        # 5. the Action and its change; 4. threads (after the Action)
        finding = next(n["raise"] for n in out["nights"] if n["k"] == 4)
        out["action"] = record_action(url, engine, tenant_id, site_id, kisiwa, finding)
        # K7-F: the plan freeze (S-4d 12:30) and the evaluation (S-1d 13:00), before the threads read the chain
        t0 = clock_time.monotonic()
        out.update(freeze_and_evaluate(url, engine, tenant_id, site_id, kisiwa, out["action"]))
        out["freeze_evaluate_seconds"] = round(clock_time.monotonic() - t0, 1)
        out["threads"] = threads(work)
        # 6. the CLI calls, as known now (stores on the database's own clock)
        out["cli"]["assess"] = cli_assess_check(build_fuel_balance_store(url), kisiwa)
        out["cli"]["raise"] = cli_raise_check(url, kisiwa)
    finally:
        work_service._store.dispose()
        fb_store.dispose()
        engine.dispose()
        pg_harness.dispose(foundation)
    out["wall_seconds"] = round(clock_time.monotonic() - began, 1)
    # 7. kisiwa.json
    (work / "kisiwa.json").write_text(json.dumps(out, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    return out


def cli_assess_check(store, kisiwa: dict) -> list[dict]:
    """§9l.3 step 6: the K3 CLI over nights 1-10 as known now prints ten REUSED lines, revision 1 (stop S-6)."""
    from assetops_backend.fuel_balance.worker import main as fuel_balance_cli

    first = kisiwa["runs"][0]["night_date"]
    after = (date.fromisoformat(kisiwa["runs"][-1]["night_date"]) + DAY).isoformat()
    try:
        code, lines = _cli_lines(lambda: fuel_balance_cli(
            ["assess", "--site", SITE_CODE, "--from", first, "--to", after], store=store))
    finally:
        store.dispose()
    if code != 0 or len(lines) != len(kisiwa["runs"]) or any(
            (x["status"], x["revision"]) != ("REUSED", 1) for x in lines):
        raise SystemExit(f"ASSESS_STATUS (stop S-6): the CLI as known now printed {lines} (exit {code})")
    return lines


def cli_raise_check(url: str, kisiwa: dict) -> list[dict]:
    """§9l.3 step 6: K4a's raise as known now (the Finding service on the database's own clock), night 4 UNCHANGED and
    the others NO_FINDING (stop S-6)."""
    from assetops_backend.fuel_balance.composition import build_fuel_finding_service
    from assetops_backend.fuel_balance.worker import main as fuel_balance_cli

    first = kisiwa["runs"][0]["night_date"]
    after = (date.fromisoformat(kisiwa["runs"][-1]["night_date"]) + DAY).isoformat()
    service = build_fuel_finding_service(url)
    try:
        code, lines = _cli_lines(lambda: fuel_balance_cli(
            ["raise", "--site", SITE_CODE, "--from", first, "--to", after], finding_service=service))
    finally:
        service.dispose()
    incident = kisiwa["runs"][INCIDENT_K - 1]["night_date"]
    bad = [x for x in lines if x["status"] != ("UNCHANGED" if x["night_date"] == incident else "NO_FINDING")]
    if code != 0 or len(lines) != len(kisiwa["runs"]) or bad:
        raise SystemExit(f"RAISE_STATUS (stop S-6): the CLI as known now printed {lines} (exit {code})")
    return lines


def check(url: str, work: Path) -> int:
    """Every KIS row (KIS-3, KIS-4, KIS-9) against the database, one JSON line per row."""
    import demo_combined_finish as finish

    client = finish.app_client(url, work) if (work / "keys.json").exists() else None  # KIS-4 reads the served summary
    ctx = finish.Ctx(client=client, work=work, story=json.loads((work / "story.json").read_text(encoding="utf-8")))
    ctx.url = url
    failed = 0
    for check_id, _, _, fn in finish.CHECKS:
        if not check_id.startswith("KIS-"):
            continue
        try:
            line = {"row": check_id, "status": "pass", "read": fn(ctx)}
        except Exception as exc:  # one line per row; the exit code says whether any failed
            line = {"row": check_id, **finish.demo_rows.failed_result(exc)}
            failed += 1
        print(json.dumps(line, default=str))
    return 1 if failed else 0


# ---- OWN-G1 (build sheet OWN-GAPS §4.5, R2-G1): added nights after the story ----------------------------------------
#
# `preflight` answers the parent's whole-command build checks; `add-day` runs §4.5 steps 1-6 for one night and leaves
# its `kisiwa-days.json` entry PUBLISHED; the parent ticks; `verify-day` runs steps 7-8 and marks it DONE (R2-G1 Q2).
# Nothing here stamps a story instant: readings are received at DB now and records go through the G3a entry route.

DAYS_FILE = "kisiwa-days.json"
ADD_KINDS = ("normal", "delivery")
#: §4.5: below this start level the default kind is `delivery`; an explicit `normal` refuses.
LOW_FUEL_L = Fraction(250)
#: §4.5 `DELIVERY_TANK_FULL`: the fill limit the card names (the tank's template capacity is 1000 L).
TANK_FILL_LIMIT_L = Fraction(950)
DELIVERY_L = 300
#: Minutes from the night's run start (d 15:00 local): dips at 18:00 and 06:00 local, the delivery at 10:00 local.
DIP_OFFSETS = (("1800", 180), ("0600", 900))
DELIVERY_OFFSET = 1140
PAST_MARGIN = timedelta(minutes=5)
#: G2's `QUIET` (R2-G2 crossing G1): a night is first checked once its readings have been quiet this long.
QUIET = timedelta(minutes=5)
WAIT_AFTER_END = timedelta(minutes=30)
WAIT_CAP = timedelta(minutes=8)
WAIT_POLL_SECONDS = 30
#: R2-G1 Q8: G3a refuses a record more than 30 days back; one hour of margin.
RECORD_AGE_LIMIT = timedelta(days=30) - timedelta(hours=1)
ENTRY_ENV = "ASSETOPS_OPERATIONAL_ENTRY"
ENTRY_PATH = f"/api/sites/{SITE_CODE}/work/operational-entries"
ADD_LOG_HEADER = (
    "# Kisiwa added-night operational-action log (OWN-G1, build sheet OWN-GAPS §4.5).\n"
    "# Written by tools/demo_combined_kisiwa.py add-day for one night after the story; the night's actions only.\n"
    "# Lab-private: the product never reads this file. Never edit by hand.\n"
)


def _refuse(code: str, detail: str):
    from demo_story_days import StoryDaysError

    return StoryDaysError(code, detail)


def _ymd(night: date) -> str:
    return night.strftime("%Y%m%d")


def last_story_night(kisiwa: dict) -> date:
    return date.fromisoformat(kisiwa["runs"][-1]["night_date"])


def night_start(kisiwa: dict, night: date) -> datetime:
    """Night d's run start: the story's run cadence carried on (`run1_start` + whole days)."""
    first = date.fromisoformat(kisiwa["runs"][0]["night_date"])
    return at(kisiwa["run1_start"]) + (night - first).days * DAY


def night_end(kisiwa: dict, night: date) -> datetime:
    return night_start(kisiwa, night) + DAY


def latest_finished_night(kisiwa: dict, db_now: datetime) -> date:
    """R2-G1 Q1: the latest night whose run end + 5 min is not after DB now (yesterday after about 15:05 local)."""
    first = date.fromisoformat(kisiwa["runs"][0]["night_date"])
    k = (db_now - PAST_MARGIN - at(kisiwa["run1_start"])) // DAY  # runs fully ended
    return first + timedelta(days=k - 1)


def read_days(work: Path) -> list[dict]:
    path = work / DAYS_FILE
    return json.loads(path.read_text(encoding="utf-8"))["nights"] if path.is_file() else []


def write_days(work: Path, entries: list[dict]) -> None:
    doc = {"schema": {"id": "assetops.demo-kisiwa-added-nights", "version": 1},
           "nights": sorted(entries, key=lambda e: e["night_date"])}
    (work / DAYS_FILE).write_text(json.dumps(doc, indent=2, default=str) + "\n", encoding="utf-8")


def _entry(entries: list[dict], night: date) -> dict | None:
    return next((e for e in entries if e["night_date"] == night.isoformat()), None)


def last_night(kisiwa: dict, entries: list[dict]) -> date:
    """R2-G1 Q5: the later of the last story night and the last DONE / PUBLISHED added night."""
    added = [date.fromisoformat(e["night_date"]) for e in entries if e.get("status") in ("DONE", "PUBLISHED")]
    return max([last_story_night(kisiwa), *added])


def start_state(build: dict, entries: list[dict]) -> tuple[Fraction, Fraction]:
    """§4.5 step 1: the last DONE / PUBLISHED entry's end state, else the story's last run (exact fractions)."""
    chained = [e for e in entries if e.get("status") in ("DONE", "PUBLISHED")]
    state = (max(chained, key=lambda e: e["night_date"])["end_state"] if chained else build["runs"][-1]["physics"])
    return Fraction(state["soc"]), Fraction(state["fuel"])


def choose_kind(kind: str | None, fuel: Fraction) -> str:
    """§4.5: `delivery` by default below 250 L, else `normal`; the explicit-kind refusals."""
    if kind is not None and kind not in ADD_KINDS:
        raise _refuse("UNKNOWN_KIND", f"{SITE_CODE} kind {kind!r} is not one of {list(ADD_KINDS)}")
    if kind is None:
        kind = "delivery" if fuel < LOW_FUEL_L else "normal"
    if kind == "normal" and fuel < LOW_FUEL_L:
        raise _refuse("FUEL_LOW_USE_DELIVERY", f"{SITE_CODE}: the tank starts at {float(fuel):.1f} L, below "
                                               f"{LOW_FUEL_L} L; use --kind delivery")
    if kind == "delivery" and fuel + DELIVERY_L > TANK_FILL_LIMIT_L:
        raise _refuse("DELIVERY_TANK_FULL", f"{SITE_CODE}: the tank starts at {float(fuel):.1f} L; a {DELIVERY_L} L "
                                            f"delivery would pass {TANK_FILL_LIMIT_L} L")
    return kind


def plan_night(kisiwa: dict, build: dict, entries: list[dict], night: date, kind: str | None, db_now: datetime,
               replay_exists: bool = False) -> dict:
    """§4.5 per-night refusals, in order; a PUBLISHED entry for `night` resumes at step 5 (R1 step 9)."""
    if kind is not None and kind not in ADD_KINDS:
        raise _refuse("UNKNOWN_KIND", f"{SITE_CODE} kind {kind!r} is not one of {list(ADD_KINDS)}")
    entry = _entry(entries, night)
    if night <= last_story_night(kisiwa) or (entry is not None and entry.get("status") == "DONE"):
        raise _refuse("DUPLICATE_DAY", f"{SITE_CODE} already has the night {night.isoformat()}")
    stuck = sorted(e["night_date"] for e in entries if e.get("status") == "PUBLISHED" and e["night_date"] < night.isoformat())
    if stuck:  # a night whose own check did not finish is never built on, nor is a later one resumed (L-A)
        raise _refuse("NIGHT_NOT_FINISHED", f"{SITE_CODE} {stuck[0]} was added but its check did not finish; finish it "
                                            f"first with --from {stuck[0]}")
    if entry is not None and entry.get("status") == "PUBLISHED":
        return {"resume": True, **entry}
    if entry is not None or replay_exists:
        # DATA-1 fix L1: the Site's one gateway state may still hold this night's unsent envelopes (they would go out
        # with the next night and break its acceptance count), and a new state restarts KISIWA_EPOCH at sequence 1.
        raise _refuse("PARTIAL_NIGHT", f"{SITE_CODE} {night.isoformat()} was left part-way (no PUBLISHED entry, but "
                                       f"its readings folder or entry exists). It cannot be resumed in place: the "
                                       f"gateway state {kisiwa_gateway(Path('work'))} may still hold its unsent "
                                       f"readings. Do not delete that folder or the night's folder (a new gateway "
                                       f"state restarts {KISIWA_EPOCH} at sequence 1, a MESSAGE_CONFLICT); run a "
                                       f"fresh prepare to add the night, or ask the Architect")
    nxt = last_night(kisiwa, entries) + timedelta(days=1)
    if night != nxt:
        raise _refuse("NOT_NEXT_NIGHT", f"{SITE_CODE} {night.isoformat()} is not the next night ({nxt.isoformat()})")
    start, end = night_start(kisiwa, night), night_end(kisiwa, night)
    if end > db_now - PAST_MARGIN:
        raise _refuse("DAY_NOT_IN_PAST", f"{SITE_CODE} {night.isoformat()} ends {iso(end)}, after DB now - "
                                         f"{PAST_MARGIN} ({iso(db_now)})")
    soc, fuel = start_state(build, entries)
    return {"resume": False, "night_date": night.isoformat(), "kind": choose_kind(kind, fuel), "start": iso(start),
            "end": iso(end), "start_state": {"soc": str(soc), "fuel": str(fuel)}}


def date_too_old(kisiwa: dict, night: date, db_now: datetime) -> bool:
    """R2-G1 Q8: the night's 18:00 dip is more than 30 days - 1 hour before DB now."""
    return night_start(kisiwa, night) + timedelta(minutes=DIP_OFFSETS[0][1]) < db_now - RECORD_AGE_LIMIT


def add_log_id(S_date: str, night: date) -> str:
    return f"kisiwa-001-story-{S_date.replace('-', '')}-add-{_ymd(night)}"


def add_actions(start: datetime, night: date, kind: str) -> list[dict]:
    """§4.5 step 2: this night's actions only, in the shipped log's shape."""
    ymd = _ymd(night)
    actions = [{"action_id": f"kis-add-{ymd}-dip-{hhmm}", "kind": "TANK_DIP",
                "at": log_instant(start + timedelta(minutes=minutes)), "actor": "Shift operator",
                "component_id": "fuel-tank"} for hhmm, minutes in DIP_OFFSETS]
    if kind == "delivery":
        actions.append({"action_id": f"kis-add-{ymd}-delivery", "kind": "FUEL_DELIVERY",
                        "at": log_instant(start + timedelta(minutes=DELIVERY_OFFSET)), "actor": "Fuel supplier",
                        "component_id": "fuel-tank", "volume_l": DELIVERY_L,
                        "ticket": {"reference": f"KIS-DT-{ymd}", "volume_l": DELIVERY_L},
                        "recorded_after_minutes": 30})
    return sorted(actions, key=lambda a: a["at"])


def add_log_text(log_id: str, actions: list[dict]) -> str:
    doc = {"log_id": log_id, "log_version": 1, "site_code": SITE_CODE, "timezone": ZONE, "actions": actions}
    return ADD_LOG_HEADER + json.dumps(doc, indent=2, ensure_ascii=True) + "\n"


def entry_key(S_date: str, night: date, action_id: str) -> str:
    digest = hashlib.sha256(f"kisiwa-add|{S_date}|{night.isoformat()}|{action_id}".encode("utf-8")).hexdigest()
    return "oprec-entry-" + digest[:32]


def taken_at_local(instant: datetime) -> str:
    return instant.astimezone(ZoneInfo(ZONE)).strftime("%Y-%m-%dT%H:%M")


def entry_bodies(S_date: str, night: date, actions: list[dict], dips: dict[str, int]) -> list[dict]:
    """§4.5 step 5: the G3a request bodies (§3.2), one per action, with deterministic idempotency keys."""
    out = []
    for a in actions:
        delivery = a["kind"] == "FUEL_DELIVERY"
        out.append({"entry": a["kind"], "value": str(a["volume_l"] if delivery else dips[a["action_id"]]),
                    "taken_at_local": taken_at_local(at(a["at"])),
                    "ticket_reference": a["ticket"]["reference"] if delivery else None,
                    "idempotency_key": entry_key(S_date, night, a["action_id"])})
    return out


def wait_until(entry: dict) -> datetime:
    """§4.5 step 6: the night is checkable once its run ended 30 min ago and its readings have been quiet 5 min."""
    return max(at(entry["end"]) + WAIT_AFTER_END, at(entry["received_at"]) + QUIET)


def verify_window(window: dict | None, findings: int, stage: dict | None) -> tuple[str, str]:
    """§4.5 step 7 (R2-G1 Q6, late-delivery header): ABSENT when no window is stored yet; DONE when the latest
    revision >= 1 is WITHIN_MARGIN (any limitation set), no fuel Finding cites the night and, when the tick visited
    Kisiwa (`stage` not None), its `fuel_night` code is OK; else UNEXPECTED with the window line."""
    if window is None:
        return "ABSENT", "no stored window for the night yet"
    line = (f"window revision {window['revision']} {window['state']} limitations {window.get('limitations')}; "
            f"fuel Findings {findings}; fuel_night {None if stage is None else stage.get('code')}")
    ok = (int(window["revision"]) >= 1 and window["state"] == "WITHIN_MARGIN" and findings == 0
          and (stage is None or stage.get("code") == "OK"))
    return ("DONE" if ok else "UNEXPECTED"), line


def _db(url: str):
    import psycopg

    return psycopg.connect(url.replace("+psycopg", ""), autocommit=True)


def _db_now(url: str) -> datetime:
    with _db(url) as c:
        return c.execute("SELECT clock_timestamp()").fetchone()[0]


def _site_ids(url: str) -> tuple[str, str]:
    with _db(url) as c:
        row = c.execute("SELECT tenant_id, id FROM site WHERE site_code_key = lower(%s)", (SITE_CODE,)).fetchone()
    if row is None:
        raise _refuse("SITE_NOT_IN_BUILD", f"{SITE_CODE} is not in this build.")
    return str(row[0]), str(row[1])


def _response_code(response) -> str | None:
    try:
        body = response.json()
    except ValueError:
        return None
    if not isinstance(body, dict):
        return None
    detail = body.get("detail")
    return (detail.get("code") if isinstance(detail, dict) else None) or body.get("code")


def preflight(url: str, work: Path) -> dict:
    """R2-G1 Q7: this build's code has the `fuel_night` stage, and an invalid entry body answers the entry route's
    shape refusal (422 `OPREC_ENTRY_INVALID`) rather than 403 (switched off) or 404 (no route). Writes nothing."""
    os.environ[ENTRY_ENV] = "on"  # R2-G3a 6: before the first `lab_app` import
    from assetops_backend.scheduling.tick import STAGE_LIMIT_FIELDS

    import demo_combined_finish as finish

    response = finish.app_client(url, work).post(ENTRY_PATH, json={"probe": True})
    return {"fuel_stage": "fuel_night" in STAGE_LIMIT_FIELDS, "entry_status": response.status_code,
            "entry_code": _response_code(response)}


def add_night(url: str, work: Path, payload: dict) -> dict:
    """§4.5 steps 1-6 for one night (`payload`: `night_date`, `kind` or null). Leaves the entry PUBLISHED."""
    os.environ[ENTRY_ENV] = "on"
    story = json.loads((work / "story.json").read_text(encoding="utf-8"))
    kisiwa = story["kisiwa"]
    build = json.loads((work / "kisiwa.json").read_text(encoding="utf-8"))
    night = date.fromisoformat(payload["night_date"])
    entries = read_days(work)
    replay = work / "kisiwa-replay" / f"add-{_ymd(night)}"
    plan = plan_night(kisiwa, build, entries, night, payload.get("kind"), _db_now(url), replay.exists())
    if not plan["resume"]:
        entry = _publish_night(url, work, story, plan, replay)
        entries = [e for e in read_days(work) if e["night_date"] != entry["night_date"]] + [entry]
        write_days(work, entries)  # Rev 1 step 4: a crash after this point resumes at step 5
    else:
        entry = {k: v for k, v in plan.items() if k != "resume"}
    entry = {**entry, "records": _post_records(url, work, story["S_date"], night, entry)}
    write_days(work, [e for e in read_days(work) if e["night_date"] != entry["night_date"]] + [entry])
    _wait(url, entry)
    return entry


def _publish_night(url: str, work: Path, story: dict, plan: dict, replay: Path) -> dict:
    """§4.5 steps 2-4: the night's log, its registered v7 run from the chained start state, and its readings through
    the gateway path received at DB now."""
    import pg_harness
    import probe_kisiwa_fuel as probe
    import probe_kisiwa_nights as nights
    import test_s6_verification_replay as rp
    from execution_adapter import run_to_end

    from assetops_backend.runs.adapters.yaml_operational_action_log import YamlOperationalActionLog
    from assetops_backend.sites.adapters.postgres_foundation_store import PostgresFoundationStore

    kisiwa, night = story["kisiwa"], date.fromisoformat(plan["night_date"])
    start, end = at(plan["start"]), at(plan["end"])
    log_id = add_log_id(story["S_date"], night)
    actions = add_actions(start, night, plan["kind"])
    root = work / "operational-actions"
    root.mkdir(parents=True, exist_ok=True)
    (root / f"{log_id}-v1.yaml").write_text(add_log_text(log_id, actions), encoding="utf-8", newline="\n")
    port = YamlOperationalActionLog(root=root)
    log_sha = port.read_log(log_id, 1).sha256
    foundation = PostgresFoundationStore(url)
    try:
        reg = story_registered(foundation, kisiwa["setup_at"], kisiwa["run1_start"], port)
        soc, fuel = Fraction(plan["start_state"]["soc"]), Fraction(plan["start_state"]["fuel"])
        run = reg.draft(nights.day_document(float(soc), float(fuel)), plan["start"], plan["end"], "v7",
                        {"log_id": log_id, "log_version": 1})
        if run.execution_status != "READY" or run.registered_basis is None:
            raise _refuse("RUN_NOT_READY", f"{SITE_CODE} {night.isoformat()}: {run.execution_status} "
                                           f"{[(b.kind, b.subject) for b in run.blocking_reasons]}")
        trajectory = run_to_end(run, reg.sim("v7")).trajectory
        last = dict(trajectory.boundaries[-1].stocks)
        dips = {}
        for a in actions:
            if a["kind"] == "TANK_DIP":
                offset = int((at(a["at"]) - start).total_seconds()) // 60
                dips[a["action_id"]] = probe._round_litre(dict(trajectory.boundaries[offset // probe.STEP].stocks)[
                    probe.FUEL])
        received = _db_now(url)
        # D-E5.30: the same session continues after the previous night (a story night or an added one)
        published = publish_night(rp, replay, work, run, received, night_end(kisiwa, night - timedelta(days=1)))
    finally:
        pg_harness.dispose(foundation)
    return {"night_date": night.isoformat(), "kind": plan["kind"], "status": "PUBLISHED", "run_id": run.run_id,
            "start": plan["start"], "end": plan["end"], "received_at": iso(received),
            "start_state": plan["start_state"], "end_state": {"soc": str(last[probe.SOC]), "fuel": str(last[probe.FUEL])},
            "log": {"id": log_id, "sha256": log_sha}, "actions": actions, "dips": dips, "published": published}


def _post_records(url: str, work: Path, S_date: str, night: date, entry: dict) -> list[dict]:
    """§4.5 step 5: the dips (and the delivery) through the G3a entry route; a re-post answers 200."""
    import demo_combined_finish as finish

    client = finish.app_client(url, work)
    out = []
    for body in entry_bodies(S_date, night, entry["actions"], entry["dips"]):
        response = client.post(ENTRY_PATH, json=body)
        if response.status_code not in (200, 201):
            raise _refuse("RECORD_REFUSED", f"{SITE_CODE} {night.isoformat()} {body['entry']} at "
                                            f"{body['taken_at_local']} answered {response.status_code}: "
                                            f"{response.text[:300]}")
        out.append({"code": response.json().get("public_code"), "kind": body["entry"], "quantity": body["value"],
                    "taken_at_local": body["taken_at_local"], "ticket_reference": body["ticket_reference"]})
    return out


def _wait(url: str, entry: dict) -> None:
    import time as clock_time

    until, began = wait_until(entry), clock_time.monotonic()
    while _db_now(url) < until and clock_time.monotonic() - began < WAIT_CAP.total_seconds():
        clock_time.sleep(WAIT_POLL_SECONDS)


def _night_window(url: str, night: date) -> tuple[dict | None, int]:
    _, site = _site_ids(url)
    with _db(url) as c:
        row = c.execute("SELECT id, revision, state, limitations FROM fuel_balance_window WHERE site_id = %s "
                        "AND night_date = %s ORDER BY revision DESC LIMIT 1", (site, night)).fetchone()
        findings = c.execute(
            "SELECT count(*) FROM finding_revision r JOIN fuel_balance_window w "
            "ON w.id::text = r.claim->>'fuel_balance_window_id' WHERE r.site_id = %s AND r.domain = 'fuel_balance' "
            "AND w.night_date = %s", (site, night)).fetchone()[0]
    window = None if row is None else {"id": str(row[0]), "revision": row[1], "state": row[2], "limitations": row[3]}
    return window, int(findings)


def verify_night(url: str, work: Path, payload: dict) -> dict:
    """§4.5 steps 7-8 (`payload`: `night_date`, `fuel_night` = the tick's Kisiwa stage or null when not visited)."""
    night = date.fromisoformat(payload["night_date"])
    entry = _entry(read_days(work), night)
    if entry is None or entry.get("status") not in ("PUBLISHED", "DONE"):
        raise _refuse("PARTIAL_NIGHT", f"{SITE_CODE} {night.isoformat()} has no PUBLISHED entry to verify")
    window, findings = _night_window(url, night)
    state, line = verify_window(window, findings, payload.get("fuel_night"))
    if state == "DONE":
        entry = {**entry, "status": "DONE", "window": {"revision": window["revision"], "state": window["state"],
                                                       "limitations": window["limitations"]}}
        write_days(work, [e for e in read_days(work) if e["night_date"] != entry["night_date"]] + [entry])
    return {"state": state, "line": line, "night_date": night.isoformat(), "entry": entry}


def main(argv: list[str]) -> int:
    if len(argv) == 3 and argv[0] == "preflight":
        print(json.dumps({"preflight": preflight(argv[1], Path(argv[2]))}))
        return 0
    if len(argv) == 4 and argv[0] == "add-day":
        print(json.dumps({"added": add_night(argv[1], Path(argv[2]), json.loads(argv[3]))}, default=str))
        return 0
    if len(argv) == 4 and argv[0] == "verify-day":
        print(json.dumps({"verified": verify_night(argv[1], Path(argv[2]), json.loads(argv[3]))}, default=str))
        return 0
    if len(argv) == 5 and argv[0] == "register":
        _, url, work, import_at, install_at = argv
        result = register(url, Path(work), at(import_at), at(install_at))
        print(json.dumps({"site_code": result["site_code"], "roles4_effective_from": result["roles4_effective_from"]}))
        return 0
    if len(argv) == 3 and argv[0] == "build":
        out = build(argv[1], Path(argv[2]))
        print(json.dumps({"site_code": SITE_CODE, "runs": len(out["runs"]), "nights": len(out["nights"]),
                          "wall_seconds": out["wall_seconds"]}))
        return 0
    if len(argv) == 3 and argv[0] == "check":
        return check(argv[1], Path(argv[2]))
    print(__doc__, file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
