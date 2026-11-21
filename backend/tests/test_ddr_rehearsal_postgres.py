"""DDR (spec §4, tests 1, 3, 4, 5 and 6's Postgres half; D-DDR.10): the rehearsal's twelve steps on one pooled `*_test`
database, each through its command's `main(argv)` with the runbook's settings, and `rehearsal_check` after each.

Needs `ASSETOPS_TEST_DATABASE_URL` naming a `*_test` database (the harness routes the run to its own clone); skipped
otherwise. Run through `tools/heavy-slot.sh --db`. Every case starts from empty tables (`test_s1_bindings_postgres.store`:
`pg_harness.empty_tables` from `tenant`, the closure every rehearsal table hangs from) and fresh temporary folders for
`$DIR` and the key. No test creates or drops a database. Expected values are the hand-written expectation file and
the literals below (W2), never a run's output.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest

URL = os.environ.get("ASSETOPS_TEST_DATABASE_URL")

pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

if URL:
    from sqlalchemy.engine import make_url
    from test_s1_bindings_postgres import engine, store  # noqa: F401
    from test_on1_operator_file import DIGEST, FIXTURE

    from assetops_backend import build_structure_snapshot as snapshot_cmd
    from assetops_backend import load_emulated_exports as loader
    from assetops_backend import onboard_operator as onboard
    from assetops_backend import reconcile_month as reconcile
    from assetops_backend import record_action as action_cmd
    from assetops_backend import rehearsal_check as check
    from assetops_backend import source_profile as profile_cmd
    from assetops_backend.database_target import PG_TARGET_ENV

BACKEND = Path(__file__).resolve().parents[1]
REPO = BACKEND.parent
DDR = BACKEND / "tests" / "fixtures" / "ddr"
MANIFEST = REPO / "Docs" / "demo-sprint" / "product-direction-layer4" / "demo-site-scenario-manifest.yaml"
EXPECT = json.loads((DDR / "lakeside-2026-10.expect.json").read_text(encoding="utf-8"))
SLUG = "lakeside-power"
WANJIRU, JOSEPH = "wanjiru@lakeside-power.example", "joseph@lakeside-power.example"
TITLE = "Lower the generator stop setting at Kobo to 70% battery charge"
STEPS = ("S1", "S2", "S3", "S4", "S5", "S6", "S7", "S8", "S9", "S10", "S11", "S12")
#: D-DDR.14: the base holds 3C2 unit 2 (`StoreAgreedActions` in `deep_dive/composition.py`), so S11 and S12 run whole.
UNIT2 = "StoreAgreedActions" in (BACKEND / "assetops_backend" / "deep_dive" / "composition.py").read_text(
    encoding="utf-8")
#: Test 1 (spec §4): the first failing gate after each step; None is exit 0 and ten PASS lines.
PROGRESS = {"S1": "G2", "S2": "G3", "S3": "G3", "S4": "G5", "S5": "G6", "S6": "G7", "S7": "G7", "S8": "G8",
            "S9": "G10", "S10": "G10", "S11": None, "S12": None}
#: The S7 read (spec §3.4, §4 test 1): World A's standing on the database (5c's Postgres test 9(a) literal).
S7_STANDING = ("Not yet reconciled: October 2026 (the organisation) does not match the management accounts within 1% "
               "(Declared).")
S7_STATUS_TAIL = "Not yet reconciled with the management accounts. Kisiwa mini-grid's budget disagrees with its own lines."


def test_url_is_a_test_database() -> None:
    name = make_url(URL).database
    assert name.endswith("_test") and not name.lower().startswith("assetops_op")


@pytest.fixture()
def rehearsal(store, engine, tmp_path, monkeypatch, capsys):  # noqa: F811 - `store` empties the tenant closure
    keys = tmp_path / "keys"
    keys.mkdir(mode=0o700)
    os.chmod(keys, 0o700)
    for variable in PG_TARGET_ENV:
        monkeypatch.delenv(variable, raising=False)
    monkeypatch.delenv("ASSETOPS_REAL_OPERATOR_DATA", raising=False)
    monkeypatch.setenv("DATABASE_URL", URL)
    monkeypatch.setenv("ASSETOPS_TENANT_SLUG", SLUG)
    monkeypatch.setenv("ASSETOPS_PSEUDONYM_KEY_DIR", str(keys))
    return Rehearsal(keys, tmp_path / "exports", capsys)


class Rehearsal:
    """Spec §1's steps, each the runbook's command through its `main(argv)`."""

    def __init__(self, keys: Path, folder: Path, capsys) -> None:
        self.keys = keys
        self.dir = folder
        self.capsys = capsys
        self.admitted_by: str | None = None
        self.exits: dict[str, int] = {}
        self.errors: dict[str, str] = {}
        self.bodies: dict[str, dict] = {}

    def _main(self, step: str, main, argv: list[str], **kwargs) -> str:
        self.capsys.readouterr()
        code = main(argv, **kwargs)
        out, err = self.capsys.readouterr()
        self.exits[step] = code if self.exits.get(step, 0) == 0 else self.exits[step]
        self.errors[step] = self.errors.get(step, "") + err
        return out

    def s1(self) -> None:
        out = self._main("S1", onboard.main, ["digest", "--file", str(FIXTURE)])
        assert DIGEST in out
        self._main("S1", onboard.main, ["check", "--file", str(FIXTURE), "--key-dir", str(self.keys)])
        self._main("S1", onboard.main, ["apply", "--file", str(FIXTURE), "--key-dir", str(self.keys),
                                        "--confirmed-digest", DIGEST])

    def s2(self, admit_as: str = WANJIRU) -> None:
        self._main("S2", profile_cmd.main, [
            "admit", "--tenant", SLUG, "--profile", str(DDR / "ddr-board-budget.profile.json"),
            "--sample", str(DDR / "ddr-board-budget.xlsx"), "--expected", str(DDR / "ddr-board-budget.expected.json"),
            "--as", admit_as])
        self._list()

    def _list(self) -> None:
        out = self._main("S2", profile_cmd.main, ["list", "--tenant", SLUG])
        rows = [json.loads(line) for line in out.splitlines()]
        found = [r["admitted_by"] for r in rows if r["profile_id"] == "ddr-board-budget"]
        self.admitted_by = found[0] if found else None

    def s3(self, *, replace: bool = True) -> None:
        run = subprocess.run([sys.executable, str(REPO / "tools" / "world_history.py"), "exports", "--manifest",
                              str(MANIFEST), "--out", str(self.dir)], capture_output=True, text=True, timeout=300)
        self.exits["S3"] = run.returncode
        if replace:
            (self.dir / f"{SLUG}.budget.csv").unlink()
            shutil.copyfile(DDR / "ddr-board-budget.xlsx", self.dir / f"{SLUG}.profile.ddr-board-budget.xlsx")

    def s4(self) -> None:
        self._main("S4", loader.main, ["--dir", str(self.dir), "--tenant", SLUG, "--submit-as", WANJIRU,
                                       "--accept-as", JOSEPH])

    def _statement(self, step: str, fuel: str, ref: str) -> None:
        self._main(step, reconcile.main, ["record", "--tenant", SLUG, "--as", JOSEPH, "--period", "2026-10",
                                          "--currency", "USD", "--revenue", "9700.00", "--fuel-cost", fuel,
                                          "--source-ref", ref])

    def s5(self) -> None:
        self._statement("S5", "5100.00", "Management accounts, October 2026, draft")

    def _build(self, step: str, by: str | None = None) -> None:
        if by is None:
            if self.admitted_by is None:  # no S2: the analyst has no id to copy (the runbook's section 6)
                self._list()
            by = f"person:{self.admitted_by}"
        self._main(step, snapshot_cmd.main, ["build", "--tenant", SLUG, "--month", "2026-10", "--by", by])

    def s6(self, by: str | None = None) -> None:
        self._build("S6", by)

    def _read(self, step: str) -> None:
        from fastapi.testclient import TestClient

        from assetops_backend.main import create_app
        # A skip case may leave a month the screen cannot show (packet, product finding PF1): a 500 is recorded as
        # the step's exit, never raised, so the checker still runs.
        response = TestClient(create_app(), raise_server_exceptions=False).get("/api/portfolio/month?month=2026-10")
        self.exits[step] = 0 if response.status_code == 200 else response.status_code
        self.bodies[step] = response.json() if response.status_code == 200 else {}

    def s7(self) -> None:
        self._read("S7")

    def s8(self) -> None:
        self._statement("S8", "5000.00", "Management accounts, October 2026, final")

    def s9(self) -> None:
        self._build("S9")

    def s10(self) -> None:
        self._read("S10")

    def s11(self) -> None:
        self._main("S11", action_cmd.main, [
            "--tenant", SLUG, "--as", "amina@lakeside-power.example", "--title", TITLE,
            "--owner", "peter@lakeside-power.example", "--due", "2026-12-15", "--site", "KOBO-001",
            "--factor", "candidate_l"], clock=lambda: datetime.now(timezone.utc))

    def s12(self) -> None:
        self._read("S12")

    def check(self) -> SimpleNamespace:
        """`rehearsal_check` as the runbook runs it; every line is §2.1's JSON or the stderr code (D-DDR.11)."""
        self.capsys.readouterr()
        code = check.main(["--tenant", SLUG, "--month", "2026-10"])
        out, err = self.capsys.readouterr()
        lines = [json.loads(line) for line in out.splitlines()]
        assert [l["gate"] for l in lines] == list(check.GATES)  # R7: ten lines on every run (plant P5)
        failed = [l for l in lines if l["state"] == "FAIL"]
        assert all(l["code"] is None and l["facts"] == {} for l in lines if l["state"] == "PASS")
        if failed:
            assert (code, err) == (4, f"DDR_GATE_FAILED {failed[0]['gate']} {failed[0]['code']}\n")
        else:
            assert (code, err) == (0, "")
        return SimpleNamespace(code=code, first=failed[0]["gate"] if failed else None,
                               failed={l["gate"]: (l["code"], l["facts"]) for l in failed})

    def run(self, *, skip: str | None = None, **change) -> SimpleNamespace:
        for step in STEPS:
            if step == skip:
                continue
            getattr(self, step.lower())(**change.get(step, {}))
        return self.check()


def money_words(v: dict) -> list:
    """Every `word` of the tiles, the bridge's steps, the cash line and the outcome cards (5c's Postgres test)."""
    return ([t["word"] for t in v["tiles"]] + [s["word"] for g in v["bridge"]["groups"] for s in g["steps"]]
            + [v["cash"]["word"]] + [o["word"] for o in v["outcomes"]])


def figures(v: dict) -> list:
    return ([t["value"] for t in v["tiles"]] + [v["bridge"]["by_site"]["rows"], v["bridge"]["by_site"]["total"],
                                                 v["cash"]["table"]["rows"], v["cash"]["table"]["total"]])


# --- test 1: the rehearsal, with progress (D-DDR.10) -----------------------------------------------------------------

def test_1_the_rehearsal_with_progress(rehearsal) -> None:  # plants P5, P6, P9, P10
    r = rehearsal
    seen = {}
    for step in STEPS:
        getattr(r, step.lower())()
        assert r.exits[step] == 0, (step, r.errors.get(step))
        seen[step] = r.check()
    assert UNIT2, "D-DDR.14: review only from a base holding 3C2 unit 2"
    want = dict(PROGRESS)
    assert {s: c.first for s, c in seen.items()} == want, {s: c.failed for s, c in seen.items()}
    assert seen["S9"].failed["G10"] == ("ACTION_MISSING", {})  # "no S11 -> G10" (D-DDR.10)

    s7, s10, s12 = r.bodies["S7"], r.bodies["S10"], r.bodies["S12"]
    screen = EXPECT["screen"]
    # S7: World A's figures, its standing and status line (after the first sentence), every money word unreconciled.
    assert figures(s7) == figures(screen)
    assert (s7["standing"]["reconciled"], s7["standing"]["reason"], s7["standing"]["text"]) == (
        False, "THIS_MONTH_NOT_MATCHED", S7_STANDING)
    assert s7["status_line"].partition(". ")[2] == S7_STATUS_TAIL
    assert money_words(s7) == [None if w is None else f"{w}, not yet reconciled" for w in money_words(screen)]
    assert s7["notices"] == screen["notices"]  # Kisiwa's budget against its lines (plant P6)
    # S10: reconciled; every compared key is the file's (G9 passed above).
    assert s10["standing"]["reconciled"] is True and money_words(s10) == money_words(screen)
    assert not [w for w in money_words(s10) if w and "not yet reconciled" in w]
    assert s12["actions"]["connected"] is True and s12["actions"]["rows"][0]["title"] == TITLE  # the Action first
    assert s10["actions"]["connected"] is True and s10["actions"]["rows"] == []


# --- test 3: skips (each a fresh case, every step but the one named) --------------------------------------------------

@pytest.mark.parametrize(("skip", "gate", "code"), [
    ("S5", "G5", "STATEMENT_FIELD"), ("S6", "G6", "AFTER_NEXT_STATEMENT"), ("S8", "G7", "STATEMENT_MISSING"),
    ("S9", "G8", "BEFORE_STATEMENT")])
def test_3_a_skipped_step_fails_its_gate(rehearsal, skip, gate, code) -> None:  # plants P2, P3, P4
    c = rehearsal.run(skip=skip)
    assert c.first == gate and c.failed[gate][0] == code, c.failed


def test_3_the_emulated_budget_loaded_fails_g3(rehearsal) -> None:  # plant P7
    c = rehearsal.run(S3={"replace": False})
    assert c.first == "G3" and c.failed["G3"] == ("READER_MISSING", {"reader": "profile.ddr-board-budget.v1"})


def test_3_no_admission_stops_the_load_and_fails_g2(rehearsal) -> None:
    c = rehearsal.run(skip="S2")
    assert rehearsal.exits["S4"] == 2 and rehearsal.errors["S4"].startswith("PROFILE_NOT_ADMITTED")
    assert c.first == "G2" and c.failed["G2"] == ("PROFILE_MISSING", {"profile": "ddr-board-budget"})


# --- test 4: shortcuts ------------------------------------------------------------------------------------------------

def test_4a_records_written_without_an_upload_fail_g3(rehearsal, tmp_path) -> None:  # plant P1
    from assetops_backend.accounts.composition import build_account_service
    from assetops_backend.commercial.composition import build_commercial_reads
    from assetops_backend.commercial.service import CommercialRecords

    r = rehearsal
    r.s1()
    r.s2()
    r.s3()
    records = tmp_path / "records"
    run = subprocess.run([sys.executable, str(REPO / "tools" / "world_history.py"), "records", "--manifest",
                          str(MANIFEST), "--out", str(records)], capture_output=True, text=True, timeout=300)
    assert run.returncode == 0, run.stderr
    accounts = build_account_service(URL)
    reads = build_commercial_reads(URL)
    try:
        tid = accounts.tenant_by_slug(SLUG)
        svc = CommercialRecords(reads.store, clock=lambda: datetime.now(timezone.utc))
        result = svc.ingest(tid, (records / f"{SLUG}.expense_ledger.json").read_bytes(),
                            entered_by=f"person:{r.admitted_by}")
        assert result.state == "STORED" and result.outcomes, result  # records written, no upload
    finally:
        accounts._store.dispose()
        reads.dispose()
    for step in STEPS[4:]:
        getattr(r, step.lower())()
    c = r.check()
    assert c.first == "G3" and c.failed["G3"][0] == "READER_MISSING", c.failed


def test_4b_a_snapshot_built_by_a_service_fails_g6(rehearsal) -> None:  # plant P12
    c = rehearsal.run(S6={"by": "service:shortcut"})
    assert c.first == "G6" and c.failed["G6"][0] == "AFTER_NEXT_STATEMENT", c.failed


# --- test 5: no code for the new layout -------------------------------------------------------------------------------

ALLOWED = {"backend/assetops_backend/rehearsal_check.py", "backend/assetops_backend/structure_snapshot/store.py",
           "backend/assetops_backend/structure_snapshot/adapters/postgres_structure_snapshot_store.py"}


def test_5_no_code_for_the_new_layout() -> None:
    run = subprocess.run(["git", "-C", str(REPO), "diff", "--name-only", "main...HEAD"], capture_output=True,
                         text=True, timeout=60)
    assert run.returncode == 0, run.stderr
    changed = set(run.stdout.split())
    code = {p for p in changed if p.startswith(("backend/assetops_backend/", "contracts/"))}
    assert code <= ALLOWED, sorted(code - ALLOWED)
    assert "backend/assetops_backend/rehearsal_check.py" in code
    assert "backend/tests/fixtures/ddr/ddr-board-budget.profile.json" in changed


# --- test 6 (Postgres half): `portfolio_history` -----------------------------------------------------------------------

def test_6_portfolio_history_is_every_portfolio_row_by_as_of_postgres(rehearsal) -> None:  # plant P8
    from assetops_backend.structure_snapshot.composition import build_structure_snapshot

    r = rehearsal
    r.s1()
    r.s2()
    r._build("S6")
    r._build("S9")
    assert r.exits.get("S6") == 0 and r.exits.get("S9") == 0, r.errors
    service = build_structure_snapshot(URL)
    try:
        tid, _ = service.store.tenant_sites(SLUG)
        rows = service.store.portfolio_history(tid, "2026-10")
        latest = service.store.latest_portfolio(tid, "2026-10")
        assert service.store.portfolio_history(tid, "2026-09") == ()
    finally:
        service.dispose()
    assert len(rows) == 2 and rows[0].as_of < rows[1].as_of and rows[1] == latest
    assert all(row.site_id is None for row in rows)
