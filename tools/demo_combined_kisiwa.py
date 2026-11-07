"""DIESEL-1 K1 (ruling DIESEL-1-R3c §9c.1): the Kisiwa (KISIWA-001) Site, registered the way the combined demo
prepare will register it. K7 (ruling DIESEL-1-R3l §9l.3) adds the story part below the registration.

    python tools/demo_combined_kisiwa.py register <database-url> <work> <import-at ISO> <install-at ISO>
    python tools/demo_combined_kisiwa.py build <database-url> <work>
    python tools/demo_combined_kisiwa.py check <database-url> <work>

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
"""

from __future__ import annotations

import contextlib
import copy
import hashlib
import io
import json
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
#: The marked final step of K7-D: needs K4a (the unexplained-fuel Finding) merged into this branch.
K4A_PENDING = "K7-D FINAL STEP PENDING: needs K4a (the unexplained-fuel Finding) merged into this branch"


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


def raise_night(url: str, tenant, site, night: str, instant: datetime) -> dict:
    """K4a's `raise_night` at the story instant: night 4 OPENED, every other night NO_FINDING (stop S-6)."""
    raise SystemExit(f"{K4A_PENDING}: raise night {night} at {iso(instant)}")


def record_action(url: str, engine, tenant, site, kisiwa: dict, finding: dict) -> dict:
    """§9l.3 step 5: the Action from the night-4 Finding, its maintenance request, ASSIGN, the change record,
    COMPLETE, the SITE_VISIT record citing the case, and the case link, each at its story instant."""
    raise SystemExit(f"{K4A_PENDING}: the Action and its change")


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
                published = rp._publish_and_accept(work / "kisiwa-replay" / f"r{item:02d}", run, f"epoch-{item}",
                                                   instant)
                out["runs"].append({"k": item, "run_id": run.run_id, "start": r["start"], "end": r["end"],
                                    "received_at": iso(instant), **guards, "published": published,
                                    "seconds": round(clock_time.monotonic() - t0, 1)})
            elif kind == "assess":
                line = assess_night(fb_store, fb_clock, instant, by_k[item]["night_date"])
                out["nights"].append({"k": item, "night_date": by_k[item]["night_date"], "assessed_at": iso(instant),
                                      "line": line})
            else:
                out["nights"][-1]["raise"] = raise_night(url, tenant_id, site_id, by_k[item]["night_date"], instant)
        # 5. the Action and its change; 4. threads (after the Action)
        finding = next(n["raise"] for n in out["nights"] if n["k"] == 4)
        out["action"] = record_action(url, engine, tenant_id, site_id, kisiwa, finding)
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
    """§9l.3 step 6: K4a's raise as known now, night 4 UNCHANGED and the others NO_FINDING (stop S-6)."""
    raise SystemExit(f"{K4A_PENDING}: the raise CLI check")


def check(url: str, work: Path) -> int:
    """KIS-3 and KIS-9 (and KIS-4 once K4a merges) against the database, one JSON line per row."""
    import demo_combined_finish as finish

    ctx = finish.Ctx(client=None, work=work, story=json.loads((work / "story.json").read_text(encoding="utf-8")))
    ctx.url = url
    failed = 0
    for check_id, _, _, fn in finish.CHECKS:
        if not check_id.startswith("KIS-"):
            continue
        try:
            line = {"row": check_id, "status": "pass", "read": fn(ctx)}
        except Exception as exc:  # one line per row; the exit code says whether any failed
            line = {"row": check_id, "status": "fail", "error": f"{type(exc).__name__}: {exc}"[:2000]}
            failed += 1
        print(json.dumps(line, default=str))
    return 1 if failed else 0


def main(argv: list[str]) -> int:
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
