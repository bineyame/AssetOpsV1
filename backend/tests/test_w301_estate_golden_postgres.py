"""W3-01 commit 2: the structural `w301-estate-golden/2` manifest replayed through the public estate router.

Spec: `.agent/W3-01-build-spec.md` "Run 9 rulings (q9)" item 1, with the Finding wire `estate-finding-index-2`
(Run 8 rulings 3 and 5). One manifest, separate `mini_grid`, `cold`, `ev` and `mixed` branches; each branch runs in
its own private test DB (a parametrized replay of the one test); the `mixed` branch builds all four Sites in that one
DB (q10 ruling 1). Every expected body is the whole normalized
response: literal counts, nulls, states, classifications and row order, with markers only at dynamic leaves:

* `{"$public": name}` - a replay-local UUID or opaque value, resolved from *other* authenticated estate public reads
  of the same replay (the scope read for Site IDs; the unpaged, unfiltered reference read of the same root, window
  and cutoff for Finding/Action IDs, links and provenance), never from the response under test.
* `{"$derive": rule, "from": name}` - a URL or DB-clock time derived from a public name or the frozen test clock.
* `{"$digest": "estate-selection/2" | "estate-access/1"}` - rebuilt independently here from the full selected
  basis (canonical sorted compact JSON, SHA-256), never by calling the estate token builder.

A changed-cursor case replays an earlier case's cursor after a basis change; its expected is the literal refusal
`{"refusal": {"code": ..., "status": ...}}` (q10 reading). Every cursor is decoded and checked (basis, cutoff,
token, `after`) and its page two is read against the full set at the cursor cutoff.

The `mixed` branch (q10 ruling 1) calls `pg_harness.fresh_database()` once and test-scope suppresses the later calls
made by the cold and EV `Chain.open()`, so the cold, EV and S4 mini-grid chains and the empty test Site share one
private DB and the one `demo` tenant. The STALE, LEASED and FAILED states are unit proof in
`test_w301_estate_coverage.py`, not persisted replay coverage (q10 ruling 2). Needs ASSETOPS_TEST_DATABASE_URL.
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable

import pytest

URL = os.environ.get("ASSETOPS_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

MANIFEST = Path(__file__).resolve().parent / "fixtures" / "w3" / "w301-estate-golden.json"
REPO = Path(__file__).resolve().parents[2]
SCHEMA = "w301-estate-golden/2"
BRANCHES = ("mini_grid", "cold", "ev", "mixed")
REPLAYED = ("mini_grid", "cold", "ev", "mixed")
MIXED_FROM = datetime(2026, 10, 6, tzinfo=timezone.utc)  # the cold/EV replay day through the S4 F03 day
REQUEST_KEYS = {"root", "from", "to", "known_at", "lens", "state_filter", "limit", "cursor"}
ROOTS = {"scope": "estate-scope-1", "findings": "estate-finding-index-2", "actions": "estate-action-index-1"}
# Leaves whose value is replay-local: a marker is legal only here (q9: UUIDs, URLs with UUIDs, DB-clock times,
# digests/cursors). Counts, lifecycle, coverage states and money are never markers.
DYNAMIC_LEAVES = {"tenant_id", "site_id", "selection_id", "committed_watermark", "known_at", "as_of",
                  "access_basis", "selection_token", "next_cursor", "finding_id", "finding_revision_id",
                  "source_revision_id", "source_ids", "evidence_ids", "basis_sha256", "finding", "action",
                  "source", "action_id", "selected_event_id", "source_finding_id", "source_finding_revision_id",
                  "created_at", "cursor", "finding_label", "accepted_evidence_ids"}
UUID = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")
TOKEN_ARRAYS = ("selected_finding_revision_ids", "selected_action_event_ids", "selected_assessment_revision_ids",
                "selected_consequence_revision_ids", "selected_assumption_revision_ids",
                "cited_accepted_evidence_ids")
COLD_DAY = datetime(2026, 10, 6, tzinfo=timezone.utc)

if URL:
    from sqlalchemy import create_engine, text

    import pg_harness
    import test_w202_cold_replay_postgres as w202
    import test_w205b_ev_replay_postgres as w205b
    from test_s1_bindings_postgres import engine, store  # noqa: F401 - the S4 mini-grid fixtures
    from test_s4_finding_store_postgres import CaseRunner, run_case
    from test_s6_action_store_postgres import CASES as S4_CASES
    from test_w203_cold_replay_postgres import opened, run
    from test_w206_ev_store_postgres import run_worker
    from test_w301_estate_index_postgres import Estate, add_empty_site, db_now, imported_before, iso, pin_read_at

    from assetops_backend.estate.adapters import postgres_estate_read
    from assetops_backend.sites.adapters.postgres_foundation_store import PostgresFoundationStore

    @pytest.fixture()
    def cold_chain(tmp_path, monkeypatch):
        """The W2-02 cold replay factory (`test_w202_cold_replay_postgres.chain`), under a distinct name."""
        made: list = []

        def make(case: str):
            w202.hold_uuids(monkeypatch, w202.CASES.index(case) + 1)
            built = w202.Chain(case, tmp_path / case)
            made.append(built)
            return built.open()

        yield make
        for built in made:
            built.close()

    @pytest.fixture()
    def ev_chain(tmp_path, monkeypatch):
        """The W2-05b EV replay factory (`test_w205b_ev_replay_postgres.chain`), under a distinct name."""
        made: list = []

        def make(case: str):
            w205b.hold_uuids(monkeypatch, 0x0500 + w205b.CASES.index(case) + 1)
            built = w205b.Chain(case, tmp_path / case)
            made.append(built)
            return built.open()

        yield make
        for built in made:
            built.close()


# --- manifest schema ---------------------------------------------------------------------------------------

def load_manifest() -> dict:
    # The blob is LF; a Windows core.autocrlf checkout may write CRLF, so compare the committed text form.
    raw = MANIFEST.read_bytes().decode("utf-8").replace("\r\n", "\n")
    document = json.loads(raw)
    assert raw == json.dumps(document, sort_keys=True, indent=2, ensure_ascii=False) + "\n", \
        "the manifest is sorted-key, two-space UTF-8 JSON with one final LF"
    return document


def is_marker(value: Any) -> bool:
    if not isinstance(value, dict):
        return False
    keys = set(value)
    return keys in ({"$public"}, {"$derive", "from"}, {"$digest"})


def check_markers(value: Any, leaf: str | None, where: str) -> None:
    if is_marker(value):
        assert leaf in DYNAMIC_LEAVES, f"{where}: a marker is not legal at {leaf!r}"
        if "$digest" in value:
            assert value["$digest"] in ("estate-selection/2", "estate-access/1"), where
            assert leaf in ("selection_token", "access_basis"), where
        return
    if isinstance(value, dict):
        assert not any(k.startswith("$") for k in value), f"{where}: unknown marker {sorted(value)}"
        for key, item in value.items():
            check_markers(item, key, f"{where}.{key}")
    elif isinstance(value, list):
        for i, item in enumerate(value):
            check_markers(item, leaf, f"{where}[{i}]")


def validate(document: dict) -> None:
    assert set(document) == {"schema", "branches"} and document["schema"] == SCHEMA
    assert tuple(sorted(document["branches"])) == tuple(sorted(BRANCHES))
    for name, branch in document["branches"].items():
        assert set(branch) == {"replay_paths", "site_codes", "cases"}, name
        for path in branch["replay_paths"]:
            assert not Path(path).is_absolute() and (REPO / path).is_file(), f"{name}: {path}"
        assert branch["site_codes"] and len(set(branch["site_codes"])) == len(branch["site_codes"])
        assert branch["cases"], f"{name}: every branch, mixed included, has cases (q10 ruling 1)"
        names = [case["name"] for case in branch["cases"]]
        assert len(names) == len(set(names)), f"{name}: case names are unique"
        for case in branch["cases"]:
            where = f"{name}/{case['name']}"
            assert set(case) == {"name", "setup", "request", "expected"}, where
            req = case["request"]
            assert set(req) == REQUEST_KEYS and req["root"] in ROOTS, where
            assert isinstance(req["limit"], int) and 1 <= req["limit"] <= 100, where
            for key in ("from", "to"):
                assert req[key].endswith("Z") and len(req[key]) == 20, f"{where}: {key} is a UTC second"
            for key in ("known_at", "cursor"):
                check_markers(req[key], key, f"{where}.request.{key}")
            expected = case["expected"]
            if set(expected) == {"refusal"}:
                assert req["cursor"] is not None and set(expected["refusal"]) == {"status", "code"}, where
                continue
            assert expected["schema_version"] == ROOTS[req["root"]], where
            check_markers(expected, None, where + ".expected")


# --- replay contexts ---------------------------------------------------------------------------------------

class Replay:
    """One branch's private-DB replay: the estate router over its engine, a frozen read clock, named clocks and
    named setup steps (run once, in manifest order)."""

    def __init__(self, engine, tenant_id, read_clock: Callable[[], datetime]) -> None:
        self.engine, self.tenant_id = engine, tenant_id
        self.estate = Estate(engine, tenant_id)
        self.read_clock = read_clock
        self.clocks: dict[str, datetime] = {}
        self.steps: dict[str, Callable[[], None]] = {}
        self.done: list[str] = []
        self.cursors: dict[str, str] = {}
        self.domains: dict[str, str] = {}  # Site code -> estate domain (the empty test Site copies its source)
        self.tenants: set = set()  # mixed: the tenant of every chain built in the one DB

    def setup(self, name: str) -> None:
        if name in self.done:
            assert self.done[-1] == name, f"setup {name!r} is cumulative and must be the latest step"
            return
        self.steps[name]()
        self.done.append(name)
        self.clocks[name] = self.read_clock()

    def snapshot(self, work):
        return self.estate.read.read(work)


def pin_clock(monkeypatch, present: Callable[[], datetime]) -> None:
    """TEST-SCOPED frozen read clock for the cold/EV replays: the estate snapshot's `read_at` is the frozen
    `present()`, so a default cutoff is a known full-precision instant (every query, cutoff and rule stays real)."""
    real = postgres_estate_read.EstateSnapshot

    class Pinned(real):
        def __init__(self, owner, c, read_at) -> None:
            super().__init__(owner, c, present())

    monkeypatch.setattr(postgres_estate_read, "EstateSnapshot", Pinned)


def mini_grid_replay(request, monkeypatch) -> Replay:
    eng = request.getfixturevalue("engine")
    runner = CaseRunner(request.getfixturevalue("store"), eng)
    request.addfinalizer(lambda: pg_harness.dispose(runner.findings))
    pin_read_at(monkeypatch, lambda: runner.now + timedelta(minutes=1))
    imported_before(eng, runner.tenant, runner.site, datetime(2026, 10, 1, tzinfo=timezone.utc))
    replay = Replay(eng, runner.tenant, lambda: runner.now + timedelta(minutes=1))
    replay.domains = {"KOBO-001": "mini_grid", "W301-EMPTY-001": "mini_grid"}
    replay.steps.update({
        "kobo-s4-F03-recurrence": lambda: run_case(runner, S4_CASES["F03"]),
        "kobo-s4-F05-withdrawal": lambda: run_case(runner, S4_CASES["F05"]),
        "kobo-late-accepted-delivery": lambda: runner.step({
            "do": "deliver", "decided": "2026-10-30T16:00:00Z",
            "blocks": [{"from": "2026-10-21T10:00:00Z", "to": "2026-10-21T10:00:00Z", "soc": "50",
                        "only": ["soc"]}]}),
        "add-empty-site-W301-EMPTY-001": lambda: add_empty_site(eng, runner.site, "W301-EMPTY-001"),
    })
    return replay


def windowed_replay(built, monkeypatch, day: datetime, code: str, domain: str) -> Replay:
    imported_before(built.engine, built.tenant_id, built.site_id, day - timedelta(days=1))
    frozen = {"at": db_now(built.engine)}
    pin_clock(monkeypatch, lambda: frozen["at"])
    replay = Replay(built.engine, built.tenant_id, lambda: frozen["at"])
    replay.domains = {code: domain, "W301-EMPTY-001": domain}

    def advance() -> None:
        frozen["at"] = db_now(built.engine)

    def empty_site() -> None:
        add_empty_site(built.engine, built.site_id, "W301-EMPTY-001")
        advance()

    replay.steps.update({"clock-advance": advance, "add-empty-site-W301-EMPTY-001": empty_site})
    return replay


def cold_replay(request, monkeypatch, case: str) -> Replay:
    built = opened(case, request.getfixturevalue("cold_chain"))
    run(built)
    replay = windowed_replay(built, monkeypatch, COLD_DAY, "COLD-LAB-001", "cold_chain")
    replay.steps[f"cold-{case}-settled"] = lambda: None
    return replay


def ev_replay(request, monkeypatch, case: str) -> Replay:
    built = request.getfixturevalue("ev_chain")(case)
    built.start_release_upload()
    run_worker(built)
    with built.engine.connect() as c:
        first = c.execute(text("SELECT min(window_start) FROM analytic_run_selection WHERE site_id = :s"),
                          {"s": built.site_id}).scalar_one()
    day = datetime(first.year, first.month, first.day, tzinfo=timezone.utc)
    replay = windowed_replay(built, monkeypatch, day, "EV-LAB-001", "ev_charging")
    replay.steps[f"ev-{case}-settled"] = lambda: None
    return replay


def mixed_replay(request, monkeypatch) -> Replay:
    """q10 ruling 1: the cold `normal` and EV `complete` chains settled, one S4 Finding case and the empty test
    Site, all in one private DB and the one `demo` tenant. Only the cold/EV `Chain.open()` database reset is
    suppressed (test-scoped); every chain, ingestion path and worker runs as in its own branch."""
    fresh = pg_harness.fresh_database()
    monkeypatch.setattr(pg_harness, "fresh_database", lambda: fresh)
    cold = opened("normal", request.getfixturevalue("cold_chain"))
    run(cold)
    ev = request.getfixturevalue("ev_chain")("complete")
    ev.start_release_upload()
    run_worker(ev)
    # The S4 runner on the same DB with a directly owned store: the `store` fixture would empty the tables.
    store = PostgresFoundationStore(URL)
    eng = create_engine(URL)
    request.addfinalizer(lambda: pg_harness.dispose(store, eng))
    runner = CaseRunner(store, eng)
    request.addfinalizer(lambda: pg_harness.dispose(runner.findings))
    run_case(runner, S4_CASES["F03"])
    empty = add_empty_site(eng, runner.site, "W301-EMPTY-001")
    for site_id in (cold.site_id, ev.site_id, runner.site, empty):
        imported_before(eng, runner.tenant, site_id, MIXED_FROM - timedelta(days=1))
    # One frozen read clock after every chain's decisions: the S4 fixture clock (ahead of the DB clock), or the
    # DB clock should that ever be later.
    frozen = max(runner.now + timedelta(minutes=1), db_now(eng))
    pin_read_at(monkeypatch, lambda: frozen)
    replay = Replay(eng, runner.tenant, lambda: frozen)
    replay.domains = {"KOBO-001": "mini_grid", "COLD-LAB-001": "cold_chain", "EV-LAB-001": "ev_charging",
                      "W301-EMPTY-001": "mini_grid"}
    replay.tenants = {cold.tenant_id, ev.tenant_id, runner.tenant}
    replay.steps["mixed-settled"] = lambda: None
    return replay


def assert_mixed(replay: Replay, branch: dict) -> None:
    """q10 ruling 1: one authenticated scope over all four Sites of one tenant; Findings coverage counts and the
    Action-root `NOT_APPLICABLE` rule over the same estate."""
    assert len(replay.tenants) == 1
    window = {"from": wire_second(MIXED_FROM), "to": branch["cases"][0]["request"]["to"]}
    scope = replay.estate.ok("scope", **window)
    assert sorted(s["site_code"] for s in scope["sites"]) == sorted(branch["site_codes"])
    findings = replay.estate.ok("findings", **window)
    assert findings["scope"]["tenant_id"] == str(next(iter(replay.tenants))).lower()
    states = [s["state"] for s in findings["coverage"]["sites"]]
    assert findings["scope"]["authorized_site_count"] == 4
    assert findings["scope"]["covered_site_count"] == sum(x in ("CURRENT", "HISTORICAL") for x in states)
    actions = replay.estate.ok("actions", **window)
    code_of = {s["site_id"]: s["site_code"] for s in scope["sites"]}
    by_code = {code_of[s["site_id"]]: s["state"] for s in actions["coverage"]["sites"]}
    assert by_code["COLD-LAB-001"] == by_code["EV-LAB-001"] == "NOT_APPLICABLE"
    assert actions["scope"]["covered_site_count"] == sum(
        x in ("CURRENT", "HISTORICAL", "NOT_APPLICABLE") for x in by_code.values())


# --- public resolution -------------------------------------------------------------------------------------

def parse(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def wire_second(at: datetime) -> str:
    return at.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def six(at: datetime | None) -> str | None:
    return None if at is None else at.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def is_uuid_leaf(value: Any) -> bool:
    items = value if isinstance(value, list) else [value]
    return bool(items) and all(isinstance(x, str) and UUID.match(x) for x in items)


def row_key(row: dict, rows: list[dict], root: str) -> str:
    """A stable public name for a row of the reference read: Site code, episode/creation instant and the ordinal
    among same-instant rows ordered by title (titles are literal, IDs are not)."""
    at = row["episode_start"] if root == "findings" else row["created_at"]
    label = "title" if root == "findings" else "action_code"
    peers = sorted((r for r in rows if r["site_code"] == row["site_code"] and
                    (r["episode_start"] if root == "findings" else r["created_at"]) == at),
                   key=lambda r: str(r[label]))
    titles = [str(r[label]) for r in peers]
    assert len(titles) == len(set(titles)), f"ambiguous same-instant rows at {row['site_code']} {at}"
    return f"{row['site_code']}@{at}#{titles.index(str(row[label]))}"


class Resolver:
    """Public names for one case, from other estate public reads of the same replay."""

    def __init__(self, replay: Replay, req: dict, known: datetime | None) -> None:
        self.replay, self.values = replay, {}
        params = {"from": req["from"], "to": req["to"]}
        if known is not None:
            params["known_at"] = six(known)
        scope = replay.estate.ok("scope", **params)
        self.code_of = {s["site_id"]: s["site_code"] for s in scope["sites"]}
        for s in scope["sites"]:
            self.values[f"site:{s['site_code']}"] = s["site_id"]
        self.reference = None
        if req["root"] != "scope":
            ref = replay.estate.ok(req["root"], **params, limit=100)
            assert ref["next_cursor"] is None, "the reference read is the whole selected set"
            self.reference = ref
            self.values["tenant"] = ref["scope"]["tenant_id"]
            for site in ref["coverage"]["sites"]:
                code = self.code_of[site["site_id"]]
                self.values[f"selection:{code}"] = site["selection_id"]
            for row in ref["rows"]:
                key = row_key(row, ref["rows"], req["root"])
                for field, value in row.items():
                    if field == "source_provenance":
                        for sub in ("source_ids", "evidence_ids", "basis_sha256"):
                            self.values[f"{key}.provenance.{sub}"] = value[sub]
                        for i, reason in enumerate(value["reasons"]):
                            for sub, item in reason.items():
                                if is_uuid_leaf(item):
                                    self.values[f"{key}.provenance.reasons[{i}].{sub}"] = item
                    elif field == "consequence":
                        self.values[f"{key}.consequence"] = value["source_revision_id"]
                    elif field != "links":
                        self.values[f"{key}.{field}"] = value
        for code in self.code_of.values():
            self.values[f"watermark:{code}"] = self.watermark(code, known)

    def watermark(self, code: str, known: datetime | None) -> datetime | None:
        site_id = next(i for i, c in self.code_of.items() if c == code)
        k = known or self.replay.read_clock()
        return self.replay.snapshot(lambda snap: snap.evidence_cutoff(self.replay.tenant_id, site_id, k))

    def clock(self, name: str) -> datetime:
        if name == "clock.read":
            return self.replay.read_clock()
        return self.replay.clocks[name.removeprefix("clock.")]

    def derive(self, rule: str, source: str) -> Any:
        if rule == "wire_second":
            at = self.clock(source) if source.startswith("clock.") else self.values[source]
            return None if at is None else wire_second(at)
        if rule == "six_digit_utc":
            return six(self.clock(source))
        if rule == "finding_label":
            return f"Finding {self.values[f'{source}.finding_id'][:8]}"
        if rule == "finding_link":
            code = source.split("@")[0]
            fid, frid = self.values[f"{source}.finding_id"], self.values[f"{source}.finding_revision_id"]
            return f"/sites/{code}/findings/{fid}?revision_id={frid}"
        if rule == "action_link":
            code = source.split("@")[0]
            return (f"/sites/{code}/actions/{self.values[f'{source}.action_id']}?event_id="
                    f"{self.values[f'{source}.selected_event_id']}")
        if rule == "action_source_link":
            code = source.split("@")[0]
            return (f"/sites/{code}/findings/{self.values[f'{source}.source_finding_id']}?revision_id="
                    f"{self.values[f'{source}.source_finding_revision_id']}")
        if rule == "page_two_cursor":
            return self.replay.cursors[source]
        if rule == "checked_cursor":
            return self.values[source]
        raise AssertionError(f"unknown derive rule {rule!r}")

    def resolve(self, value: Any, digests: dict[str, str]) -> Any:
        if is_marker(value):
            if "$public" in value:
                assert value["$public"] in self.values, f"no public value named {value['$public']!r}"
                return self.values[value["$public"]]
            if "$derive" in value:
                return self.derive(value["$derive"], value["from"])
            return digests[value["$digest"]]
        if isinstance(value, dict):
            return {k: self.resolve(v, digests) for k, v in value.items()}
        if isinstance(value, list):
            return [self.resolve(v, digests) for v in value]
        return value


# --- independent digest rebuild ----------------------------------------------------------------------------

def digest(obj: Any) -> str:
    raw = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def ids(values) -> list[str]:
    return sorted({str(v).lower() for v in values if v is not None})


def site_basis(replay: Replay, root: str, code: str, site_id: str, cov: dict, ref_rows: list[dict],
               req: dict, known: datetime) -> dict:
    """One Site's full selected basis for the token, from the full (unpaged, lens/state `all`) public rows and the
    estate snapshot's selected-window/lineage/consequence/basis reads at the same cutoff."""
    t = replay.tenant_id
    lo, hi = parse(req["from"]), parse(req["to"])
    domain = "actions" if root == "actions" else replay.domains[code]
    item = {"site_id": site_id.lower(), "domain": domain, "match_state": cov["match_state"],
            "job_state": cov["job_state"], "source_freshness": cov["source_freshness"],
            "selection_id": None if cov["selection_id"] is None else cov["selection_id"].lower(),
            "watermark": None, **{k: [] for k in TOKEN_ARRAYS}}
    mine = [r for r in ref_rows if r["site_id"] == site_id]
    if root == "actions":
        if cov["state"] == "NOT_APPLICABLE":
            return item
        basis = replay.snapshot(lambda snap: snap.action_basis(t, site_id, [r["action_id"] for r in mine])) \
            if mine else {}
        item["selected_action_event_ids"] = ids(r["selected_event_id"] for r in mine)
        item["selected_finding_revision_ids"] = ids(r["source_finding_revision_id"] for r in mine)
        item["selected_assessment_revision_ids"] = ids(
            x for b in basis.values() for x in (b.get("primary"), *(b.get("assessments") or ())))
        item["cited_accepted_evidence_ids"] = ids(
            x for b in basis.values() for x in (*(b.get("evidence") or ()), *(b.get("origin_evidence") or ())))
        return item
    if cov["state"] == "NOT_APPLICABLE":
        return item

    def work(snap):
        snap.historical = known < snap.read_at
        cutoff = snap.evidence_cutoff(t, site_id, known)
        out = {"watermark": cutoff}
        if domain == "mini_grid":
            days = [d for d in snap.dispatch_days(t, site_id, lo, hi, known)
                    if d.get("available") and d.get("selection") is not None]
            out["assessments"] = {str(x) for d in days for x in (d.get("assessment_revision_ids") or ())} | {
                str(d["window_assessment_revision_id"]) for d in days if d.get("window_assessment_revision_id")}
            frids = [r["finding_revision_id"] for r in mine]
            lineage = snap.finding_lineage(t, site_id, frids, known) if frids else {}
            out["assessments"] |= {str(r["assessment_revision_id"]) for r in lineage.get("assessments") or ()}
            out["cited"] = {str(r["evidence_id"]) for r in lineage.get("evidence") or ()}
            out["assumptions"], out["consequences"] = set(), set()
            for frid in frids:
                selected = snap.consequence(t, site_id, frid, known)
                if selected.get("consequence_revision_id") is None:
                    continue
                cited = selected.get("cited") or {}
                out["consequences"].add(str(selected["consequence_revision_id"]))
                out["assumptions"] |= {str(x) for x in cited.get("assumption_revision_ids") or ()}
                out["cited"] |= {str(x) for x in cited.get("power_evidence_ids") or ()}
        elif cutoff is not None:
            windows = snap.selected_windows(t, site_id, domain, lo, hi, cutoff, known)
            selected = {r["finding_revision_id"] for r in mine}
            out["assessments"] = {str(x) for w in windows for x in w["assessment_revision_ids"]}
            out["cited"] = {str(x) for w in windows for x in w["evidence_ids"]} | {
                str(x) for w in windows for f in w["findings"] if f["finding_revision_id"] in selected
                for x in f["evidence_ids"]}
            out["consequences"] = {str(f["consequence_revision_id"]) for w in windows for f in w["findings"]
                                   if f["finding_revision_id"] in selected and f.get("consequence_revision_id")}
            out["assumptions"] = set()
        return out

    basis = replay.snapshot(work)
    item["watermark"] = six(basis["watermark"])
    if domain == "mini_grid" or basis["watermark"] is not None:
        item["selected_assessment_revision_ids"] = ids(basis.get("assessments") or ())
        item["selected_finding_revision_ids"] = ids(r["finding_revision_id"] for r in mine)
        item["cited_accepted_evidence_ids"] = ids(basis.get("cited") or ())
        item["selected_consequence_revision_ids"] = ids(basis.get("consequences") or ())
        item["selected_assumption_revision_ids"] = ids(basis.get("assumptions") or ())
    return item


def rebuild(replay: Replay, req: dict, body: dict, ref: dict | None, known: datetime) -> dict[str, str]:
    root = req["root"]
    tenant = str(replay.tenant_id).lower()
    if root == "scope":
        site_ids = [s["site_id"] for s in body["sites"]]
    else:
        site_ids = [s["site_id"] for s in body["coverage"]["sites"]]
    out = {"estate-access/1": digest({"version": "estate-access/1", "tenant_id": tenant,
                                      "authorized_site_ids": ids(site_ids)})}
    if root == "scope":
        return out
    scope = replay.estate.ok("scope", **{"from": req["from"], "to": req["to"], "known_at": six(known)})
    code_of = {s["site_id"]: s["site_code"] for s in scope["sites"]}
    sites = [site_basis(replay, root, code_of[s["site_id"]], s["site_id"], s, ref["rows"], req, known)
             for s in ref["coverage"]["sites"]]
    sites.sort(key=lambda x: (x["site_id"], x["domain"]))
    lens = (req["lens"] or "all") if root == "findings" else None
    state = (req["state_filter"] or "all") if root == "findings" else None
    out["estate-selection/2"] = digest({
        "version": "estate-selection/2", "tenant_id": tenant, "authorized_site_ids": ids(site_ids),
        "from": six(parse(req["from"])), "to": six(parse(req["to"])), "known_at": six(known),
        "lens": lens, "state_filter": state, "sites": sites})
    return out


# --- normalization and cursor ------------------------------------------------------------------------------

def normalize(body: dict, code_of: dict[str, str]) -> dict:
    """The whole response; coverage Sites gain `site_code` from the scope read's site_id -> site_code map."""
    out = json.loads(json.dumps(body))
    if "coverage" in out:
        out["coverage"]["sites"] = [{**s, "site_code": code_of[s["site_id"]]} for s in out["coverage"]["sites"]]
    return out


def first_difference(actual: Any, expected: Any, where: str = "$") -> str:
    if isinstance(actual, dict) and isinstance(expected, dict):
        for key in sorted(set(actual) | set(expected)):
            if actual.get(key, "<absent>") != expected.get(key, "<absent>"):
                return first_difference(actual.get(key, "<absent>"), expected.get(key, "<absent>"), f"{where}.{key}")
    if isinstance(actual, list) and isinstance(expected, list) and len(actual) == len(expected):
        for i, (a, e) in enumerate(zip(actual, expected)):
            if a != e:
                return first_difference(a, e, f"{where}[{i}]")
    return f"{where}: actual {actual!r} != expected {expected!r}"


def decode(cursor: str) -> dict:
    return json.loads(base64.urlsafe_b64decode(cursor + "=" * (-len(cursor) % 4)).decode("utf-8"))


def check_cursor(replay: Replay, req: dict, body: dict, known: datetime, digests: dict[str, str]) -> None:
    """Decode the cursor: its basis is this read's tenant, Site set, access basis, window, cutoff, filters and
    rebuilt token; `after` is the last row's sort key. Page two continues the full set at the same token."""
    payload = decode(body["next_cursor"])
    last = body["rows"][-1]
    at, row_id = ((last["episode_start"], last["finding_id"]) if req["root"] == "findings"
                  else (last["created_at"], last["action_id"]))
    expected = {"v": 1, "tenant_id": str(replay.tenant_id).lower(),
                "authorized_site_ids": ids(s["site_id"] for s in body["coverage"]["sites"]),
                "access_basis": digests["estate-access/1"], "from": six(parse(req["from"])),
                "to": six(parse(req["to"])), "known_at": six(known),
                "selection_token": digests["estate-selection/2"]}
    if req["root"] == "findings":
        expected.update(lens=req["lens"] or "all", state_filter=req["state_filter"] or "all")
    else:
        expected["kind"] = "actions"
    after = payload.pop("after")
    assert payload == expected
    assert (after[0][:19] + "Z", after[1]) == (at, row_id)
    params = {"from": req["from"], "to": req["to"], "limit": req["limit"], "cursor": body["next_cursor"]}
    if req["root"] == "findings":
        params.update(lens=req["lens"] or "all", state=req["state_filter"] or "all")
    two = replay.estate.ok(req["root"], **params)
    whole = replay.estate.ok(req["root"], **{k: v for k, v in params.items() if k not in ("cursor", "limit")},
                             known_at=six(known), limit=100)
    n = len(body["rows"])
    assert two["selection_token"] == body["selection_token"] == whole["selection_token"]
    assert [r[("finding_id" if req["root"] == "findings" else "action_id")] for r in two["rows"]] == [
        r[("finding_id" if req["root"] == "findings" else "action_id")] for r in whole["rows"][n:n + req["limit"]]]


# --- the replay ------------------------------------------------------------------------------------------------

def request_params(req: dict, resolver_values: Callable[[Any], Any]) -> dict:
    params = {"from": req["from"], "to": req["to"], "limit": req["limit"]}
    for key in ("known_at", "cursor"):
        if req[key] is not None:
            params[key] = resolver_values(req[key])
    if req["root"] == "findings":
        if req["lens"] is not None:
            params["lens"] = req["lens"]
        if req["state_filter"] is not None:
            params["state"] = req["state_filter"]
    return params


def replay_case(replay: Replay, case: dict) -> None:
    req, name = case["request"], case["name"]
    replay.setup(case["setup"])
    plain = Resolver.__new__(Resolver)
    plain.replay, plain.values = replay, {}
    params = request_params(req, lambda v: plain.resolve(v, {}))
    if set(case["expected"]) == {"refusal"}:
        response = replay.estate.get(req["root"], **params)
        got = {"status": response.status_code, "code": response.json()["detail"]["code"]}
        assert got == case["expected"]["refusal"], name
        return
    if req["root"] == "scope":
        params.pop("limit")
    known = parse(params["known_at"]) if "known_at" in params else None
    if "cursor" in params:
        known = parse(decode(params["cursor"])["known_at"])
    body = replay.estate.ok(req["root"], **params)
    resolver = Resolver(replay, req, known)
    k = known or replay.read_clock()
    digests = rebuild(replay, req, body, resolver.reference, k)
    actual = normalize(body, resolver.code_of)
    if body.get("next_cursor"):
        check_cursor(replay, req, body, k, digests)
        replay.cursors[name] = resolver.values["self.next_cursor"] = body["next_cursor"]
    expected = resolver.resolve(case["expected"], digests)
    assert actual == expected, f"{name}: the whole normalized response differs at {first_difference(actual, expected)}"
    for row in actual.get("rows") or ():  # source classifications are literal and every row is attributable
        assert set(row["source_provenance"]) == {"classification", "state", "source_ids", "evidence_ids",
                                                 "basis_sha256", "reasons"}


BRANCH_REPLAY = {
    "mini_grid": lambda request, monkeypatch, branch: mini_grid_replay(request, monkeypatch),
    "cold": lambda request, monkeypatch, branch: cold_replay(request, monkeypatch,
                                                             Path(branch["replay_paths"][0]).stem),
    "ev": lambda request, monkeypatch, branch: ev_replay(request, monkeypatch, Path(branch["replay_paths"][0]).stem),
    "mixed": lambda request, monkeypatch, branch: mixed_replay(request, monkeypatch),
}


@pytest.mark.parametrize("branch_name", REPLAYED)
def test_w301_golden_manifest_public_replay(branch_name, request, monkeypatch) -> None:
    """Each branch replays in its own private DB and compares every case's whole normalized response."""
    document = load_manifest()
    validate(document)
    branch = document["branches"][branch_name]
    assert branch["cases"], f"{branch_name} has cases"
    replay = BRANCH_REPLAY[branch_name](request, monkeypatch, branch)
    for case in branch["cases"]:
        replay_case(replay, case)
    scope = replay.estate.ok("scope", **{"from": branch["cases"][0]["request"]["from"],
                                          "to": branch["cases"][0]["request"]["to"]})
    assert {s["site_code"] for s in scope["sites"]} <= set(branch["site_codes"])
    if branch_name == "mixed":
        assert_mixed(replay, branch)
