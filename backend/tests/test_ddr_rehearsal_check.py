"""DDR (spec §4, test 6's memory half, tests 7 and 8; no database). Test 8 runs `rehearsal_check.main` over injected
reads built from the expectation file (hand-written, spec §3.4) and asserts codes and facts only (D-DDR.11)."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

from assetops_backend.structure_snapshot.store import MemoryStructureSnapshotStore

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "ddr"


def _generator():
    spec = importlib.util.spec_from_file_location("make_board_budget_ddr", FIXTURES / "make_board_budget.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_7_the_generator_writes_the_committed_bytes(tmp_path, capsys) -> None:
    written = _generator().main(tmp_path)
    capsys.readouterr()
    committed = (FIXTURES / "ddr-board-budget.xlsx").read_bytes()
    assert written.read_bytes() == committed
    expect = json.loads((FIXTURES / "lakeside-2026-10.expect.json").read_text(encoding="utf-8"))
    assert hashlib.sha256(committed).hexdigest() == expect["profile"]["sample_sha256"] == \
        "2f629a1fc77a087932dbf565969b67ddd290395dcfb010a214782dd62576ad75"


def test_6_portfolio_history_is_every_portfolio_row_by_as_of_memory() -> None:

    store = MemoryStructureSnapshotStore()
    tenant = uuid4()
    at = datetime(2026, 11, 20, 8, 0, tzinfo=timezone.utc)
    base = _row_like(store, tenant, at)
    later = replace(base, id=uuid4(), as_of=at + timedelta(hours=1))
    site_row = replace(base, id=uuid4(), site_id=uuid4())
    store.rows.extend([later, site_row, base])
    assert [r.as_of for r in store.portfolio_history(tenant, "2026-10")] == [at, at + timedelta(hours=1)]
    assert store.portfolio_history(tenant, "2026-09") == ()


def _row_like(store, tenant, at):
    from assetops_backend.structure_snapshot.model import SnapshotRow
    fields = {name: None for name in SnapshotRow.__dataclass_fields__}
    fields.update(id=uuid4(), tenant_id=tenant, site_id=None, period="2026-10", as_of=at)
    return SnapshotRow(**fields)


# --- test 8: the gates over injected reads (spec §4 test 8; plants P9-P13, P15, P17) -----------------------------

import copy  # noqa: E402
import re  # noqa: E402
import sys  # noqa: E402
from datetime import date  # noqa: E402
from decimal import Decimal as D  # noqa: E402
from types import SimpleNamespace as NS  # noqa: E402

import pytest  # noqa: E402

from assetops_backend import rehearsal_check as check  # noqa: E402
from assetops_backend.commercial.pseudonym import PseudonymKeyErased  # noqa: E402
from assetops_backend.i18n.schema import UNSERVED  # noqa: E402
from assetops_backend.structure.targets.read import TargetCheck  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
EXPECT = json.loads((FIXTURES / "lakeside-2026-10.expect.json").read_text(encoding="utf-8"))
TENANT = uuid4()
IDS = {e: uuid4() for e in ("amina@lakeside-power.example", "joseph@lakeside-power.example",
                            "wanjiru@lakeside-power.example", "peter@lakeside-power.example")}
WANJIRU, JOSEPH = IDS["wanjiru@lakeside-power.example"], IDS["joseph@lakeside-power.example"]
ROLES = {"amina@lakeside-power.example": "OPERATOR_EXECUTIVE", "joseph@lakeside-power.example":
         "FINANCE_AND_COMMERCIAL_LEAD", "wanjiru@lakeside-power.example": "ANALYST",
         "peter@lakeside-power.example": "SITE_MANAGER"}
T0 = datetime(2026, 11, 21, 8, 0, tzinfo=timezone.utc)
LINE = re.compile(r"^DDR_GATE_FAILED G(10|[1-9]) [A-Z_]+$")


def at(hours: int) -> datetime:
    return T0 + timedelta(hours=hours)


class Reads:
    """Every read `rehearsal_check` makes, answering what a whole rehearsal leaves (accepted at 08:00, statement 1 at
    09:00, snapshot A at 10:00, statement 2 at 11:00, snapshot B at 12:00); a test changes one thing."""

    def __init__(self) -> None:
        self.x = copy.deepcopy(EXPECT)
        self.admitted_by = WANJIRU
        self.built_by = [f"person:{WANJIRU}", f"person:{WANJIRU}"]
        self.key_error: Exception | None = None
        self.collected = {}
        self.owners = ["Peter"]
        self.body = self._body()

    def _body(self) -> dict:
        b = copy.deepcopy(self.x["screen"])
        b["status_line"] = "Figures as of 21 November 2026, 12:00 UTC. " + b["status_line"]
        b.update(as_of="2026-11-21T12:00:00Z", as_of_text="Figures as of 21 November 2026, 12:00 UTC.",
                 nav={"previous": "2026-09", "next": None}, state_text=None,
                 actions={"connected": True, "rows": [{"title": self.x["action"]["title"]}], "more": 0})
        return b

    def tenant_id(self, slug):
        return TENANT if slug == "lakeside-power" else None

    def people(self, tid):
        return tuple(NS(email=e, person_id=i, grants=(NS(role=ROLES[e], by_service="service:onboarding"),))
                     for e, i in IDS.items())

    def sites(self, tid):
        return tuple(NS(site_code=c.split(":")[0], site_type=c.split(":")[1]) for c in self.x["sites"])

    def key(self, tid):
        if self.key_error is not None:
            raise self.key_error
        return b"k" * 32

    def profile(self, tid, profile_id):
        p = self.x["profile"]
        return NS(status="ADMITTED", version=1, admitted_by=self.admitted_by, profile_sha256=p["profile_sha256"],
                  sample_sha256=p["sample_sha256"])

    def held_uploads(self, tid):
        return tuple(NS(upload_id=r, reader=r, waiting=False, submitted_by=WANJIRU)
                     for r in self.x["readers"]["accepted"])

    def upload(self, tid, upload_id):
        return NS(decision=NS(decided_by=JOSEPH, decided_at=at(0)))

    def statements(self, tid):
        s1, s2 = self.x["statements"]
        return (NS(site_id=None, period="2026-10", revenue=s1["revenue"], fuel_cost=s1["fuel_cost"],
                   recorded_by_script=True, recorded_by=JOSEPH, result_at_record="NOT_MATCHED", recorded_at=at(1)),
                NS(site_id=None, period="2026-10", revenue=s2["revenue"], fuel_cost=s2["fuel_cost"],
                   recorded_by_script=True, recorded_by=JOSEPH, result_at_record="MATCHED", recorded_at=at(3)))

    def site_refs(self, slug):
        return tuple(NS(site_code=c) for c in self.x["stated"])

    def _value(self, code, factor):
        v = self.collected.get(code) if factor == "collected" else None
        v = v or self.x["stated"][code][factor]
        missing = NS(cause=self.x["absent_causes"].get(code, {}).get(factor))
        return NS(value=None if v is None else D(v), missing=missing if v is None else None, sources=())

    def site_inputs(self, site, month):
        c = site.site_code
        price = NS(value=D("1.50"), missing=None, sources=("commercial:expense",))
        return NS(stated={f: self._value(c, f) for f in ("revenue", "fuel_cost")},
                  leaves={**{f: self._value(c, f) for f in ("om", "staff", "in_transit")}, "diesel_price": price})

    def site_actual(self, site, month):
        return NS(values={"collected": self._value(site.site_code, "collected")})

    def site_targets(self, site, month):
        c = site.site_code
        want = self.x["target_checks"].get(c)
        checks = () if want is None else (TargetCheck(want["factor_id"], D(want["stated"]), D(want["computed"]),
                                                      want["currency"], want["agrees"]),)
        return NS(structure=NS(values={"contribution": NS(value=D(self.x["target_contribution"][c]))}),
                  checks=checks)

    def portfolio_history(self, tid, month):
        return (NS(as_of=at(2), built_by=self.built_by[0], asked=self.x["asked"]),
                NS(as_of=at(4), built_by=self.built_by[1], asked=self.x["asked"]))

    def asked(self, row):
        return tuple(row.asked)

    def served(self, tid, month):
        return NS(state="SERVED", freshness=NS(current=True, reasons=()))

    def opens(self, tid, statement):
        return True, "MATCHED"

    def screen(self, slug, month):
        return copy.deepcopy(self.body)

    def actions(self, tid):
        a = self.x["action"]
        return tuple(NS(title=a["title"], created_by_name="Amina", owner_name=o, due_on=date(2026, 12, 15),
                        site_code="KOBO-001", factor_id="candidate_l") for o in self.owners)


@pytest.fixture()
def env(monkeypatch, tmp_path):
    monkeypatch.setenv("DATABASE_URL", "postgresql://unused/injected_test")
    monkeypatch.setenv("ASSETOPS_PSEUDONYM_KEY_DIR", str(tmp_path))


def run(reads, capsys, *argv) -> tuple[int, dict, list[str]]:
    code = check.main(["--tenant", "lakeside-power", "--month", "2026-10", *argv], services=reads)
    out, err = capsys.readouterr()
    lines = [json.loads(line) for line in out.splitlines()]
    assert [l["gate"] for l in lines] in ([], list(check.GATES))  # R7: ten lines, or none on a refusal
    for line in lines:
        assert set(line) == {"gate", "step", "state", "code", "facts"}
        assert (line["state"], line["code"], line["facts"]) == ("PASS", None, {}) or line["state"] == "FAIL"
    assert all(LINE.match(e) or re.fullmatch(r"[A-Z_]+", e) for e in err.splitlines())  # 8(g): codes only
    return code, {l["gate"]: l for l in lines}, err.splitlines()


def failed(lines: dict) -> dict:
    return {g: (l["code"], l["facts"]) for g, l in lines.items() if l["state"] == "FAIL"}


def test_8_the_whole_rehearsal_passes(env, capsys) -> None:
    code, lines, err = run(Reads(), capsys)
    assert (code, failed(lines), err) == (0, {}, [])


def test_8a_g2_fails_when_joseph_admitted_the_profile(env, capsys) -> None:  # plant P11
    reads = Reads()
    reads.admitted_by = JOSEPH
    code, lines, err = run(reads, capsys)
    assert failed(lines) == {"G2": ("ADMITTER", {"expected": str(WANJIRU), "found": str(JOSEPH)})}
    assert (code, err) == (4, ["DDR_GATE_FAILED G2 ADMITTER"])


def test_8b_g6_and_g8_fail_when_a_service_built_the_snapshots(env, capsys) -> None:  # plant P12
    reads = Reads()
    reads.built_by = ["service:x", "service:x"]
    _, lines, err = run(reads, capsys)
    assert failed(lines) == {"G6": ("SNAPSHOT_MISSING", {"period": "2026-10", "built_by": f"person:{WANJIRU}"}),
                             "G8": ("BUILDER", {"expected": f"person:{WANJIRU}", "found": "service:x"})}
    assert err == ["DDR_GATE_FAILED G6 SNAPSHOT_MISSING"]


def test_8c_g9_ignores_the_clock_and_fails_on_a_figure(env, capsys) -> None:  # plant P10
    reads = Reads()
    reads.body.update(as_of="2030-01-02T03:04:05Z", as_of_text="Figures as of 2 January 2030, 03:04 UTC.",
                      nav={"previous": "2026-09", "next": "2026-11"},
                      status_line="Figures as of 2 January 2030, 03:04 UTC. " + EXPECT["screen"]["status_line"])
    code, lines, _ = run(reads, capsys)
    assert (code, failed(lines)) == (0, {})
    reads.body["bridge"]["by_site"]["rows"][1][3] = "−$563.00"
    code, lines, _ = run(reads, capsys)
    assert failed(lines) == {"G9": ("SCREEN", {"path": "$.bridge.by_site.rows[1][3]"})}
    assert EXPECT["screen"]["bridge"]["by_site"]["rows"][1][:4] == ["Kobo mini-grid", "$883.00", "$1,445.00",
                                                                     "−$562.00"]


def test_8d_g4_fails_on_kobo_collected(env, capsys) -> None:  # plant P13
    reads = Reads()
    reads.collected["KOBO-001"] = "3000.00"
    _, lines, err = run(reads, capsys)
    assert failed(lines) == {"G4": ("FIGURE", {"site": "KOBO-001", "factor": "collected", "expected": "3180.00",
                                               "found": "3000.00"})}
    assert err == ["DDR_GATE_FAILED G4 FIGURE"]


def test_8e_g10_reads_the_newest_action(env, capsys) -> None:  # plant P9
    reads = Reads()
    reads.owners = ["Halima", "Peter"]  # the newest first (`for_tenant`); an older one would pass
    _, lines, _ = run(reads, capsys)
    assert failed(lines) == {"G10": ("ACTION_FIELD", {"field": "owner_name", "expected": "Peter",
                                                      "found": "Halima"})}
    reads.owners = []
    _, lines, _ = run(reads, capsys)
    assert failed(lines) == {"G10": ("ACTION_MISSING", {})}
    reads.owners = ["Peter"]
    reads.body["actions"] = {"connected": False, "rows": [], "more": 0}
    _, lines, _ = run(reads, capsys)
    assert failed(lines) == {"G10": ("SCREEN_NOT_CONNECTED", {})}


def test_8f_the_key(env, capsys, monkeypatch) -> None:  # plant P17
    reads = Reads()
    reads.key_error = PseudonymKeyErased()
    _, lines, err = run(reads, capsys)
    assert failed(lines) == {"G1": ("KEY_STATE", {"state": "ERASED"})}
    assert err == ["DDR_GATE_FAILED G1 KEY_STATE"]
    monkeypatch.delenv("ASSETOPS_PSEUDONYM_KEY_DIR")
    code, lines, err = run(Reads(), capsys)
    assert (code, lines, err) == (2, {}, ["NO_KEY_DIR"])


def test_8_refusals_before_any_read(env, capsys, monkeypatch, tmp_path) -> None:
    assert run(Reads(), capsys, "--tenant", "nobody")[::2] == (2, ["UNKNOWN_TENANT"])
    assert run(Reads(), capsys, "--month", "2026-13")[::2] == (2, ["BAD_MONTH"])
    assert run(Reads(), capsys, "--expect", str(tmp_path / "absent.json"))[::2] == (2, ["EXPECT_UNREADABLE"])
    monkeypatch.delenv("DATABASE_URL")
    assert run(Reads(), capsys)[::2] == (2, ["NO_DATABASE"])


def test_8_a_read_that_raises_fails_only_its_gate(env, capsys) -> None:
    reads = Reads()

    def broken(*_):
        raise RuntimeError("down")
    reads.statements = broken
    _, lines, _ = run(reads, capsys)
    assert failed(lines)["G5"] == ("READ_FAILED", {"store": "build_commercial_reads"})
    assert lines["G10"]["state"] == "PASS"  # the later gates still run


def _guard():
    spec = importlib.util.spec_from_file_location("statement_catalogue_ddr", REPO / "tools/checks/statement_catalogue.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules.setdefault(spec.name, module)
    spec.loader.exec_module(module)
    return module


def test_8g_the_checker_holds_no_prose(env) -> None:  # plant P15
    rel = "backend/assetops_backend/rehearsal_check.py"
    guard = _guard()
    assert rel not in guard.ADOPTED
    assert guard.ratchet_hits(rel, (REPO / rel).read_text(encoding="utf-8"), UNSERVED) == []
    baseline = json.loads((REPO / guard.HANDBUILT_BASELINE).read_text(encoding="utf-8"))
    allow = json.loads((REPO / guard.ALLOW).read_text(encoding="utf-8"))
    assert rel not in baseline and rel not in allow
