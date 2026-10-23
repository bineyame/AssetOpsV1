"""W5-02a K1c item 29: the test-only cold generated-scenario producer (build rulings (K1c) 2 and 3).

`.agent/W5-02-build-spec.md` "W5-02a build rulings (K1c)". The registered `config/scenarios/cold-backup-failed.yaml`
is loaded into memory, given a unique `cold-...` scenario ID and moved by one delta so its source interval is
`[D+16h, D+17h)` with `D = floorUTCday(R) - 1 day` for the DB time `R` of the run. Every absolute instant moves
(`start`, `end`, `forcings[].at`, `observations[].at`, `observations[].release_at`), as do the W2 test helper's
run-request interval, Site Evidence window and scheduled late-publication instant. The result is parsed by the
unchanged `parse_cold_scenario_document` (its `site_code == "COLD-LAB-001"` check included).

Nothing here registers a scenario anywhere: the caller (`backend/tests/test_w502_cold_scenario_producer.py`)
passes the definition only to its test `FakeScenarios`, shared by `RunSetupService` and `host.cold_lab.
StoreColdInputs`, in a fresh private `*_test` database where `install_cold_lab` imported COLD-LAB-001. The public
`/cold-scenarios` catalog stays the six fixed IDs.

Mode inputs (ruling 3), each a separate test-only scenario document:
- `ordinary`: the shifted document, observations unchanged (none).
- `pending`: one chamber probe report HELD and released at the shifted late-publication instant, so a later
  accepted reading enqueues a `cold_chain` recompute job after the first selection.
- `stale`: the wider 90-minute evidence/assessment window `[start, start+90min)` (the W5-01 stale route); the
  closing-boundary probe at `end` is then 30 minutes before the window's `to`. The extra DROP rows over the
  final 15 minutes before `end` remain input only.
- `no-probe`: every droppable chamber probe report (`start <= at < end`) is DROPPED; the closing-boundary report
  at `end` still publishes (the parser admits no fault there), so UNKNOWN needs the test's seeded selection.

`validate_foundation` rejects a frozen registered basis whose Site/Foundation/binding contract is not the cold one
before replay; `corroborate_k0` reads `K0` and fails if accepted IDs, window, revision or binding disagree.
"""

from __future__ import annotations

import copy
import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Mapping

import yaml

ROOT = Path(__file__).resolve().parents[1]
BASE_SCENARIO = ROOT / "config" / "scenarios" / "cold-backup-failed.yaml"
SITE_CODE = "COLD-LAB-001"
SITE_TYPE = "COLDCHAIN"
TIMEZONE = "Africa/Addis_Ababa"
ROLE_SET = "cold-roles-1"
#: The shipped document's source start; the W2 helper's window/late instants are fixed offsets from it.
BASE_START = datetime(2026, 10, 6, 19, 0, tzinfo=timezone.utc)
BASE_RELEASE = datetime(2026, 10, 6, 20, 10, tzinfo=timezone.utc)  # W2 helper scheduled late publication
BASE_ATTEST_FROM = datetime(2026, 10, 6, 0, 0, tzinfo=timezone.utc)  # W2-03 simulated clock attestation
BASE_ATTEST_TO = datetime(2026, 10, 8, 0, 0, tzinfo=timezone.utc)
MODES = ("ordinary", "pending", "stale", "no-probe")
STALE_SUPPRESSED = timedelta(minutes=15)  # extra input only; never the cause of the state (run-5 ruling 2)
#: The explicit evidence/assessment window per mode (run-5 STALE/UNKNOWN rulings 1, 2, 4): the W2 helper's
#: 65-minute `[start, end+5min)` window, except STALE_SOURCE's W5-01 wider route `[start, start+90min)`, whose
#: `to` is more than 10 minutes after the closing-boundary probe at `end`.
WINDOW_MINUTES = {"ordinary": 65, "pending": 65, "stale": 90, "no-probe": 65}
PROBE = "probe-1"
_FMT = "%Y-%m-%dT%H:%M:%SZ"


def instant(value: str) -> datetime:
    return datetime.strptime(value, _FMT).replace(tzinfo=timezone.utc)


def text_of(value: datetime) -> str:
    return value.astimezone(timezone.utc).strftime(_FMT)


def target_delta(db_now: datetime) -> timedelta:
    """`D = floorUTCday(R) - 1 day`; the delta that moves the shipped start onto `D + 16h`."""
    r = db_now.astimezone(timezone.utc)
    day = r.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=1)
    return (day + timedelta(hours=16)) - BASE_START


@dataclass(frozen=True)
class ShiftedCase:
    """One shifted test-only scenario input and the W2 helper instants moved by the same delta."""

    mode: str
    scenario_id: str
    delta: timedelta
    document: dict[str, Any]
    start: datetime
    end: datetime
    window_end: datetime
    release: datetime
    attest_from: datetime
    attest_to: datetime

    def definition(self):
        from assetops_backend.scenarios.cold_parsing import parse_cold_scenario_document

        return parse_cold_scenario_document(copy.deepcopy(self.document))

    def request(self, **overrides) -> dict[str, Any]:
        """The W2 helper's cold run request (`test_w202_cold_run_identity.cold_request`) for this case."""
        request = {
            "site_id": SITE_CODE, "foundation_version": 1, "scenario_id": self.scenario_id, "scenario_version": 1,
            "interval": {"start_time": text_of(self.start), "end_time": text_of(self.end)},
            "timestep_minutes": 1, "seed": self.document["seed"],
            "model_profile": {"profile_id": "cold-thermal", "profile_version": 1},
            "publication_profile": {"profile_id": "cold-publication", "profile_version": 1},
            "run_inputs": [],
        }
        request.update(overrides)
        return request

    def evidence_window(self) -> dict[str, Any]:
        return {"start": text_of(self.start), "end": text_of(self.window_end), "end_exclusive": True}


def _probe_rows(at_values, action: str, release: datetime | None = None) -> list[dict[str, Any]]:
    return [{"at": text_of(at), "kind": "PROBE_REPORT", "device_id": PROBE, "action": action, "outcome": None,
             "release_at": None if release is None else text_of(release)} for at in at_values]


def shifted_case(db_now: datetime, mode: str, tag: str) -> ShiftedCase:
    """The shifted test-only document for `mode`; `tag` makes the `cold-...` scenario ID unique."""
    if mode not in MODES:
        raise ValueError(f"unknown mode {mode!r}")
    delta = target_delta(db_now)
    document = yaml.safe_load(BASE_SCENARIO.read_text(encoding="utf-8"))
    move = (lambda value: text_of(instant(value) + delta))
    document["scenario_id"] = f"cold-w502-{mode}-{tag}".lower()
    document["start"], document["end"] = move(document["start"]), move(document["end"])
    for row in document["forcings"]:
        row["at"] = move(row["at"])
    for row in document["observations"]:
        row["at"] = move(row["at"])
        if row.get("release_at") is not None:
            row["release_at"] = move(row["release_at"])
    start, end = instant(document["start"]), instant(document["end"])
    release = BASE_RELEASE + delta
    # The parser admits observation rows only in [start, end): the inclusive end boundary report always publishes.
    minutes = [start + timedelta(minutes=m) for m in range(int((end - start) / timedelta(minutes=1)))]
    if document["observations"] and mode != "ordinary":
        raise ValueError("the base scenario's own observation rows would collide with a mode input")
    if mode == "pending":
        document["observations"] = _probe_rows([start + timedelta(minutes=50)], "HOLD", release)
    elif mode == "stale":
        document["observations"] = _probe_rows([m for m in minutes if m >= end - STALE_SUPPRESSED], "DROP")
    elif mode == "no-probe":
        document["observations"] = _probe_rows(minutes, "DROP")
    return ShiftedCase(mode=mode, scenario_id=document["scenario_id"], delta=delta, document=document,
                       start=start, end=end, window_end=start + timedelta(minutes=WINDOW_MINUTES[mode]), release=release,
                       attest_from=BASE_ATTEST_FROM + delta, attest_to=BASE_ATTEST_TO + delta)


def _binding_contract(rows) -> set[tuple[str, str, str]]:
    return {(str(r["device_id"]), str(r["signal_id"]), str(r["role"])) for r in rows}


def expected_binding_contract() -> set[tuple[str, str, str]]:
    """The registered COLD-LAB-001 channel contract (`sites/cold_lab.py` conversion fixture, read only)."""
    from assetops_backend.sites.cold_lab import conversion_fixture

    fixture = conversion_fixture()
    if fixture["role_set"] != ROLE_SET or fixture["site_code"] != SITE_CODE:
        raise AssertionError("the registered cold conversion fixture is not cold-roles-1 for COLD-LAB-001")
    return _binding_contract(fixture["bindings"])


def validate_foundation(run, site, revision, case: ShiftedCase) -> None:
    """Reject a frozen registered basis that is not the cold contract, before replay.

    `site` is the imported Site record, `revision` the exact stored Foundation revision the run froze."""
    basis = run.registered_basis
    problems: list[str] = []
    if basis is None:
        raise AssertionError("the cold run has no registered basis")
    if getattr(site, "site_code", SITE_CODE) != SITE_CODE:
        problems.append(f"site_code {site.site_code!r}")
    if site.site_type != SITE_TYPE:
        problems.append(f"site_type {site.site_type!r}")
    if site.timezone != TIMEZONE:
        problems.append(f"timezone {site.timezone!r}")
    if revision is None or str(revision.id) != basis.foundation_revision_id:
        problems.append("the frozen Foundation revision is not stored")
    else:
        types = sorted(c.get("component_type") for c in revision.content.get("components") or ())
        if types.count("TEMPERATURE_PROBE") < 1 or "COLD_ROOM" not in types or "GENERATOR" not in types:
            problems.append(f"Foundation components {types}")
    snapshot = json.loads(basis.snapshot_canonical)
    if hashlib.sha256(basis.snapshot_canonical.encode("utf-8")).hexdigest() != basis.snapshot_sha256:
        problems.append("snapshot SHA")
    if _binding_contract(snapshot.get("bindings") or ()) != expected_binding_contract():
        problems.append("binding device/channel/role contract")
    role_sets = {v for v in _find(snapshot, "role_set")}
    if role_sets != {ROLE_SET}:
        problems.append(f"role_set {sorted(role_sets)}")
    # The imported Foundation and v4 binding valid-from instants precede the shifted window and stay effective.
    for name, valid_from, valid_to in (
            ("Foundation", basis.foundation_valid_from, basis.foundation_valid_to),
            ("binding", basis.binding_valid_from, basis.binding_valid_to)):
        if not instant(valid_from[:19] + "Z") <= case.start:
            problems.append(f"{name} valid_from {valid_from} follows the window")
        if valid_to is not None and instant(valid_to[:19] + "Z") < case.window_end:
            problems.append(f"{name} valid_to {valid_to} ends inside the window")
    if problems:
        raise AssertionError("the registered Foundation is not the cold test contract: " + "; ".join(problems))


def _find(value: Any, key: str):
    if isinstance(value, Mapping):
        for k, v in value.items():
            if k == key:
                yield v
            yield from _find(v, key)
    elif isinstance(value, list):
        for v in value:
            yield from _find(v, key)


@dataclass(frozen=True)
class K0:
    known_at: datetime
    accepted_ids: tuple[str, ...]
    finding_revision_id: str
    assessment_revision_id: str
    window: tuple[datetime, datetime]


def corroborate_k0(conn, tenant_id, site_id, finding_revision_id: str, case: ShiftedCase,
                   binding_set_revision_id: str, selection: Mapping[str, Any]) -> K0:
    """`K0 = max(ingestion_disposition.decided_at)` of this Site's accepted envelopes at the selected W5-01 evidence
    cutoff, corroborated against the selected cold Finding revision and the W5-01 selection's source provenance
    (`selection` = the read's `selection` object). Any disagreement fails."""
    from sqlalchemy import text

    p = {"t": tenant_id, "s": site_id}
    k0 = conn.execute(text("SELECT max(decided_at) FROM ingestion_disposition WHERE tenant_id = :t AND site_id = :s "
                           "AND decision = 'ACCEPTED'"), p).scalar_one()
    accepted = {str(v) for v in conn.execute(text(
        "SELECT accepted_evidence_id FROM ingestion_disposition WHERE tenant_id = :t AND site_id = :s "
        "AND decision = 'ACCEPTED' AND decided_at <= :k"), {**p, "k": k0}).scalars()}
    fr = conn.execute(text(
        "SELECT CAST(fr.assessment_revision_id AS text) AS ar, ar.window_start, ar.window_end, r.knowledge_cutoff, "
        "CAST(r.binding_set_revision_ids AS text) AS bindings FROM finding_revision fr "
        "JOIN assessment_revision ar ON ar.id = fr.assessment_revision_id JOIN analytic_run r ON r.id = ar.analytic_run_id "
        "WHERE fr.tenant_id = :t AND fr.site_id = :s AND fr.id = :f AND fr.domain = 'cold_chain'"),
        {**p, "f": finding_revision_id}).one()
    cited = {str(v) for v in conn.execute(text(
        "SELECT evidence_id FROM finding_revision_evidence WHERE finding_revision_id = :f"),
        {"f": finding_revision_id}).scalars()}
    bound = {str(v) for v in conn.execute(text(
        "SELECT DISTINCT CAST(binding_set_revision_id AS text) FROM accepted_evidence WHERE tenant_id = :t "
        "AND site_id = :s AND id = ANY(CAST(:ids AS uuid[]))"), {**p, "ids": sorted(accepted)}).scalars()}
    cited_bindings = {str(v) for v in conn.execute(text(
        "SELECT DISTINCT CAST(binding_revision_id AS text) FROM accepted_evidence WHERE tenant_id = :t "
        "AND site_id = :s AND id = ANY(CAST(:ids AS uuid[]))"), {**p, "ids": sorted(cited)}).scalars()}
    run_bindings = set(json.loads(fr.bindings or "[]"))
    problems = []
    if k0 is None or not accepted:
        problems.append("no accepted envelope")
    if fr.knowledge_cutoff != k0:
        problems.append(f"run knowledge_cutoff {fr.knowledge_cutoff} != K0 {k0}")
    if (fr.window_start, fr.window_end) != (case.start, case.window_end):
        problems.append(f"window {fr.window_start}..{fr.window_end}")
    if not cited or not cited <= accepted:
        problems.append("cited evidence is not accepted by K0")
    if fr.ar not in [str(x) for x in selection.get("assessment_revision_ids") or ()]:
        problems.append("the Finding's assessment revision is not the W5-01 selection")
    if not set(selection.get("accepted_evidence_ids") or ()) <= accepted or not cited <= set(
            selection.get("accepted_evidence_ids") or ()):
        problems.append("W5-01 source provenance IDs disagree")
    if bound != {binding_set_revision_id}:
        problems.append(f"accepted envelopes bind {sorted(bound)}, not the frozen binding set revision")
    if not cited_bindings or not cited_bindings <= run_bindings:
        problems.append("the cited evidence's binding revisions are not the selected run's")
    if problems:
        raise AssertionError("K0 corroboration failed: " + "; ".join(problems))
    return K0(known_at=k0, accepted_ids=tuple(sorted(accepted)), finding_revision_id=finding_revision_id,
              assessment_revision_id=fr.ar, window=(fr.window_start, fr.window_end))
