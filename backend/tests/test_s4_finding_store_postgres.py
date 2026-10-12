"""S4-01 phase 1: Finding store and `s4-finding-cases-v1` (PostgreSQL).

Each case of the committed specification (`conversions/s4-finding-cases-v1.json`)
runs through real Batch V2 ingestion, the S3 recompute worker and the selected
dispatch read, then the Finding matcher; every expectation is checked against
a fresh reload of the stored rows. F07 (model upgrade) is test-scoped: no
reviewed later dispatch-3.x exists, so a clearly labelled test model version
proves the path and no live upgraded claim is produced.
Requires ASSETOPS_TEST_DATABASE_URL (backend/README-db.md).
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

URL = os.environ.get("ASSETOPS_TEST_DATABASE_URL")

pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

if URL:
    from sqlalchemy import text
    from sqlalchemy.exc import DBAPIError
    from test_s1_bindings_postgres import Clock, engine, store  # noqa: F401
    from test_s2_evidence_ledger_postgres import Kit, _z, converted_enabled

    from assetops_backend.analytics import dispatch_v3
    from assetops_backend.analytics.adapters.postgres_assessment_store import PostgresAssessmentStore
    from assetops_backend.analytics.adapters.postgres_finding_store import FindingFenceMoved, PostgresFindingStore
    from assetops_backend.analytics.assessment_worker import DispatchAssessmentWorker
    from assetops_backend.analytics.finding_service import FindingMatcher
    from assetops_backend.evidence.adapters.postgres_evidence_ledger import PostgresEvidenceLedger
    from assetops_backend.evidence.ledger_service import BatchIngestionService
    from assetops_backend.sites.binding_service import BindingService
    from assetops_backend.sites.demo_configuration import apply_demo_configuration
    from assetops_backend.sites.foundation_service import FoundationService

BACKEND = Path(__file__).resolve().parents[1]
SPEC = json.loads((BACKEND / "conversions" / "s4-finding-cases-v1.json").read_text(encoding="utf-8"))
DEMO = json.loads((BACKEND / "conversions" / "kobo-001-s3-dispatch-demo-config.json").read_text(encoding="utf-8"))
SETUP_AT = datetime(2026, 10, 29, 12, tzinfo=timezone.utc)
TEST_UPGRADE_VERSION = "dispatch-3.1-s4-test-upgrade"


def _t(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def block_rows(block: dict, rules: dict) -> list[tuple]:
    step = timedelta(minutes=rules["step_minutes"])
    sig = rules["signals"]
    only = set(block.get("only") or ("state", "load", "pv", "dis", "soc"))
    rows = []
    start, end = _t(block["from"]), _t(block["to"])
    if block.get("stop_before"):
        rows.append((*sig["state"], start - step, "STOPPED"))
    t = start
    while t <= end:
        if "state" in only:
            rows.append((*sig["state"], t, "RUNNING"))
        if "load" in only:
            rows += [(f, None, t, rules["feeder_kw"]) for f in rules["feeders"]]
        for key in ("pv", "dis", "soc"):
            if key in only and key in block:
                rows.append((*sig[key], t, block[key]))
        t += step
    if block.get("stop_after"):
        rows.append((*sig["state"], end + step, "STOPPED"))
    return rows


class CaseRunner:
    """Executes specification steps through the S2 ingestion service, the S3 worker and the matcher."""

    def __init__(self, store, engine, model=dispatch_v3) -> None:
        result, outcome = converted_enabled(store, engine)
        clock = Clock(SETUP_AT)
        apply_demo_configuration(store, FoundationService(store, "demo", clock), BindingService(store, clock),
                                 result.tenant, result.site, DEMO)
        with engine.connect() as c:
            set_id = c.execute(text("SELECT id FROM signal_binding_set_revision WHERE site_id = :s "
                                    "ORDER BY valid_from DESC, recorded_at DESC LIMIT 1"),
                               {"s": result.site.id}).scalar_one()
        self.kit = Kit(engine, set_id)
        self.seq: dict[tuple, int] = {}
        self.held: dict[str, list[tuple[str, str]]] = {}
        self.store, self.engine, self.result, self.model = store, engine, result, model
        self.tenant, self.site = self.kit.principal.tenant_id, self.kit.principal.site_id
        self.now = SETUP_AT
        self.findings = PostgresFindingStore(URL)
        for step in SPEC["setup"]:
            self.step(step)

    def seal(self, rows, epoch):
        """Sequence every row in source-time order (a gateway numbers readings as it takes them); a
        held row keeps its earlier sequence but is delivered later (late central acceptance)."""
        now, later = [], []
        for (device, signal, when, value), held in rows:
            source = self.kit.binding(device, signal)["source_id"]
            self.seq[(source, epoch)] = self.seq.get((source, epoch), 0) + 1
            text_ = self.kit.envelope(device, self.seq[(source, epoch)], 0, value, source_time=_z(when),
                                      epoch=epoch, bound_signal=signal)
            if held:
                later.append((held, (device, text_)))
            else:
                now.append((device, text_))
        return now, later

    def submit(self, envelopes, decided_at):
        service = BatchIngestionService(PostgresEvidenceLedger(URL), Clock(decided_at))
        by_device: dict[str, list[str]] = {}
        for device, text_ in envelopes:
            by_device.setdefault(device, []).append(text_)
        for device, texts in by_device.items():
            answer = service.submit(self.kit.principal, self.kit.seal(texts, device_id=device).encode("utf-8"))
            assert answer.status == 200 and answer.receipt.status == "COMPLETED", answer

    def tick(self, at: str | None = None) -> datetime:
        self.now = max(self.now + timedelta(minutes=1), _t(at) if at else self.now)
        return self.now

    def step(self, step: dict) -> dict | None:
        do = step["do"]
        if do == "deliver":
            rules, epoch = SPEC["reading_rules"], step.get("epoch", "epoch-1")
            rows = [(r, False) for b in step["blocks"] for r in block_rows(b, rules)]
            rows += [(r, name) for name, blocks in step.get("held", {}).items() for b in blocks
                     for r in block_rows(b, rules)]
            now, later = self.seal(sorted(rows, key=lambda x: x[0][2]), epoch)
            for name, envelope in later:
                self.held.setdefault(name, []).append(envelope)
            self.submit(now, self.tick(step["decided"]))
        elif do == "release":
            self.submit(self.held.pop(step["name"]), self.tick(step["decided"]))
        elif do == "assess":
            for outcome in DispatchAssessmentWorker(PostgresAssessmentStore(URL), model=self.model,
                                                    clock=Clock(self.tick())).run_pending():
                assert outcome.status == "DONE", outcome.error
        elif do in ("reserve", "runtime"):
            service = FoundationService(self.store, "demo", Clock(self.tick(step.get("decided"))))
            note = f"{SPEC['label']}: labelled fixture control"
            if do == "reserve":
                service.publish_battery_reserve(self.result.tenant, self.result.site, asset_code="battery",
                                                value=float(step["value"]),
                                                effective_from=_t(step["effective_from"]), note=note)
            else:
                service.publish_component_properties(
                    self.result.tenant, self.result.site, asset_code="generator",
                    properties=[{"property_key": "minimum-runtime", "value": step["value"], "unit": "min",
                                 "source": "TEMPLATE", "source_version": 2}],
                    effective_from=_t(step["effective_from"]), note=note)
        elif do == "match":
            return self.match()
        return None

    def match(self):
        matcher = FindingMatcher(PostgresAssessmentStore(URL), self.findings, model=self.model,
                                 now=lambda: self.tick(), fence_moved=FindingFenceMoved)
        return matcher.match(self.tenant, self.site)

    def reload(self) -> dict:
        return PostgresFindingStore(URL).rows(self.tenant, self.site)


def check(runner: CaseRunner, outcome, expect: list[dict], case_id: str, collateral: bool = False) -> None:
    rows = runner.reload()
    by_anchor = {f["anchor_start"]: f for f in rows["findings"]}
    by_id = {f["id"]: f for f in rows["findings"]}
    new_revisions = [r for r in rows["revisions"] if str(r["id"]) in outcome.revision_ids]
    if collateral:
        # A backdated control splits the open Foundation revision, so every later window selects a new
        # control revision ID: unchanged episodes append SUPPORT_CHANGED with the same bounds and minutes.
        named = {_t(e["anchor"]) for e in expect if e["anchor"] != "SPLIT_PART"}
        anchors = {f["id"]: f["anchor_start"] for f in rows["findings"]}
        for r in [r for r in new_revisions if anchors[r["finding_id"]] not in named]:
            [prior] = [p for p in rows["revisions"] if p["finding_id"] == r["finding_id"]
                       and p["revision_no"] == r["revision_no"] - 1]
            assert r["transition"] == "SUPPORT_CHANGED" and r["lifecycle"] == prior["lifecycle"], (case_id, r)
            assert (r["episode_start"], r["episode_end"], r["candidate_minutes"]) == (
                prior["episode_start"], prior["episode_end"], prior["candidate_minutes"]), (case_id, r)
            assert r["assessment_revision_id"] != prior["assessment_revision_id"]
            new_revisions.remove(r)
    assert len(new_revisions) == len(expect), (case_id, [(r["transition"], r["episode_start"]) for r in new_revisions])
    for e in expect:
        if e["anchor"] == "SPLIT_PART":
            finding = next(by_id[r["finding_id"]] for r in new_revisions
                           if by_id[r["finding_id"]]["split_from_finding_id"] is not None)
        else:
            assert _t(e["anchor"]) in by_anchor, (case_id, e["anchor"], sorted(map(str, by_anchor)),
                                                  [(r["transition"], str(r["episode_start"]), str(r["episode_end"]),
                                                    r["claim"]) for r in new_revisions])
            finding = by_anchor[_t(e["anchor"])]
        [rev] = [r for r in new_revisions if r["finding_id"] == finding["id"]]
        assert rev["transition"] == e["transition"], (case_id, e, rev["transition"])
        assert (str(finding["id"]) in outcome.finding_ids) == bool(e.get("new")), (case_id, e)
        for key, column in (("lifecycle", "lifecycle"), ("revision_no", "revision_no")):
            if key in e:
                assert rev[column] == e[key], (case_id, key, rev[column])
        if "episode" in e:
            assert [rev["episode_start"], rev["episode_end"]] == [_t(x) for x in e["episode"]], (case_id, rev)
        if "necessary_minutes_gt" in e:
            assert rev["necessary_minutes"] > e["necessary_minutes_gt"] and rev["candidate_minutes"] > 0
        if "interval_citations" in e:
            cites = [a for a in rows["assessments"] if a["finding_revision_id"] == rev["id"] and a["scope"] == "INTERVAL"]
            assert len(cites) == e["interval_citations"], (case_id, cites)
        for key, column in (("recurs_after", "recurs_after_finding_id"), ("split_from", "split_from_finding_id")):
            if key in e:
                want = None if e[key] is None else by_anchor[_t(e[key])]["id"]
                assert finding[column] == want, (case_id, key)
        if "merged_into" in e:
            [merge] = [m for m in rows["merges"] if m["superseded_finding_id"] == finding["id"]]
            assert merge["canonical_finding_id"] == by_anchor[_t(e["merged_into"])]["id"]
        if rev["lifecycle"] == "SUPPORTED":
            cited = [x for x in rows["evidence"] if x["finding_revision_id"] == rev["id"]]
            assert cited, (case_id, "a supported revision cites accepted evidence")


@pytest.fixture()
def runner(store, engine):
    return CaseRunner(store, engine)


def run_case(runner: CaseRunner, case: dict) -> None:
    for step in case["steps"]:
        outcome = runner.step(step)
        if step["do"] == "match":
            check(runner, outcome, step["expect"], case["case_id"], bool(step.get("collateral")))


class TestFindingCases:
    def test_every_specified_case_in_one_site_and_reload(self, runner) -> None:
        """F01-F06 and F08 in order, in one Site, as the producer runs them."""
        for case in SPEC["cases"]:
            run_case(runner, case)
        rows = runner.reload()
        # every old revision stays addressable and unchanged; no Finding is lost
        assert len({r["id"] for r in rows["revisions"]}) == len(rows["revisions"])
        f04 = next(f for f in rows["findings"] if f["anchor_start"] == _t("2026-10-13T08:30:00Z"))
        revs = [r for r in rows["revisions"] if r["finding_id"] == f04["id"]]
        assert [r["revision_no"] for r in revs][:2] == [1, 2]  # 3 is F05's documented collateral
        assert revs[0]["assessment_revision_id"] != revs[1]["assessment_revision_id"]
        assert revs[0]["episode_start"] == _t("2026-10-13T08:30:00Z")
        # a replay of the whole basis plans nothing
        assert runner.match().revision_ids == ()

    def test_stale_window_neither_creates_nor_closes(self, runner) -> None:
        f01 = SPEC["cases"][0]
        run_case(runner, f01)
        runner.step({"do": "deliver", "decided": "2026-10-31T08:00:00Z", "blocks": [
            {"from": "2026-10-06T08:25:00Z", "to": "2026-10-06T08:30:00Z", "pv": "41", "only": ["pv"]}]})
        outcome = runner.match()
        assert outcome.revision_ids == () and outcome.window_statuses["2026-10-06"] == "STALE_PROJECTION"

    def test_f07_test_scoped_model_upgrade_appends_a_revision(self, store, engine, monkeypatch) -> None:
        """TEST-SCOPED: `dispatch-3.1-s4-test-upgrade` is a labelled test version of the same rules, not a
        reviewed dispatch-3.x; it exists only inside this test, so no live upgraded claim is produced."""
        runner = CaseRunner(store, engine)
        run_case(runner, SPEC["cases"][0])
        old = runner.reload()["revisions"]
        monkeypatch.setattr(dispatch_v3, "MODEL_VERSION", TEST_UPGRADE_VERSION)
        upgraded = DispatchAssessmentWorker(PostgresAssessmentStore(URL), clock=Clock(runner.tick()))
        assert upgraded.reconcile(runner.tenant, runner.site)
        outcomes = upgraded.run_pending()
        assert outcomes and all(o.status == "DONE" for o in outcomes), [(o.status, o.error) for o in outcomes]
        outcome = runner.match()
        rows = runner.reload()
        [new] = [r for r in rows["revisions"] if str(r["id"]) in outcome.revision_ids]
        assert new["transition"] == "MODEL_REEVALUATED" and new["model_version"] == TEST_UPGRADE_VERSION
        assert new["revision_no"] == 2 and new["finding_id"] == old[0]["finding_id"]
        assert new["assessment_revision_id"] != old[0]["assessment_revision_id"]
        assert [r for r in rows["revisions"] if r["id"] == old[0]["id"]][0] == old[0]
        # back on the real version the test-version selections are not CURRENT: nothing is refreshed from them
        monkeypatch.setattr(dispatch_v3, "MODEL_VERSION", "dispatch-3.1")
        assert runner.match().revision_ids == ()

    def test_finding_rows_are_append_only(self, runner) -> None:
        run_case(runner, SPEC["cases"][0])
        for sql in ("UPDATE finding SET finding_key = 'x'", "DELETE FROM finding_revision",
                    "UPDATE finding_revision SET lifecycle = 'MERGED'", "DELETE FROM finding_revision_evidence",
                    "DELETE FROM finding_revision_assessment"):
            with pytest.raises(DBAPIError, match="append-only"):
                with runner.engine.begin() as c:
                    c.execute(text(sql))

    def test_a_moved_fence_writes_nothing(self, runner) -> None:
        run_case(runner, {**SPEC["cases"][0], "steps": SPEC["cases"][0]["steps"][:2]})
        stale = runner.findings.fence(runner.tenant, runner.site, "dispatch")
        runner.step({"do": "deliver", "decided": "2026-10-31T09:00:00Z", "blocks": [
            {"from": "2026-10-06T10:00:00Z", "to": "2026-10-06T10:00:00Z", "soc": "70", "only": ["soc"]}]})
        with pytest.raises(FindingFenceMoved):
            runner.findings.apply(runner.tenant, runner.site, "dispatch", [], stale, runner.tick())
        assert runner.reload()["revisions"] == []
