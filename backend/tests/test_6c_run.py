"""6c (`specs/6c-option-evaluator/spec.md` §4, §6 tests 5 and 7; D-P6.20 to D-P6.31): the evaluation service on the
memory store (F1's lever injected, D-P6.21) and the command. Every expected figure is a literal of §5."""
from __future__ import annotations

import dataclasses
import json
from datetime import datetime, timezone
from decimal import Decimal
from itertools import count
from types import SimpleNamespace
from uuid import UUID

import pytest

from assetops_backend import evaluate_options as command
from assetops_backend.decisions.adapters.study_file import read_study_bytes
from assetops_backend.decisions.models import SETTING_GRID_CHANGES
from assetops_backend.decisions.records import (DecisionRefused, DecisionService, MemoryDecisionStore, StoreUnavailable,
                                                refusal_sentence)
from assetops_backend.decisions.run import EvaluationService
from assetops_backend.structure.check import StructureError
from lakeside_people import SLUG, LakesidePeople, email
from option_fixtures import (CURRENT, FIXTURES, TEST_GRID, TEST_LEVER, case_doc, f1_base, study_doc, write_study)
from test_6c_evaluate import run_f1

D = Decimal
CLOCK = datetime(2026, 11, 24, 9, 0, tzinfo=timezone.utc)
LEVERS = {"test_stop_reserve": TEST_LEVER}
F1 = FIXTURES / "study-f1.json"
SENTENCES = {
    "STUDY_REQUIRED": "Give the simulation for this kind of change (--study).",
    "STUDY_UNREADABLE": "The simulation file cannot be read.",
    "STUDY_NOT_CALIBRATED": "The simulation did not match the Site's own run, so it cannot value anything.",
    "STUDY_LABELS_INVALID": "The simulation is not labelled as a model on simulated, emulated or recorded readings.",
    "STUDY_BASELINE_MISMATCH": "The simulation starts from other settings than this decision's.",
    "STUDY_GRID_MISMATCH": "The simulation does not hold exactly this decision's settings.",
    "STUDY_ADMISSION_MISMATCH": "The simulation's service checks do not match the rule.",
    "STUDY_FRAME_MISMATCH": "The simulation is of another Site's record.",
    "STUDY_MONTH_NOT_COVERED": "The simulation does not cover the whole of this decision's month.",
    "STRUCTURE_UNAVAILABLE": "The month's figures cannot be read right now.",
}


@pytest.fixture(autouse=True)
def _cheap_hash(monkeypatch):
    from assetops_backend.accounts import passwords
    from test_3c0a_accounts_service import PW
    stored = passwords.hash_password(PW)
    monkeypatch.setattr(passwords, "hash_password", lambda _pw: stored)


class FakeRead:
    """The structure read's `site_inputs`, counting its calls; `fail` makes it raise."""

    def __init__(self, leaves) -> None:
        self.leaves = leaves
        self.calls: list[tuple] = []
        self.fail: Exception | None = None

    def site_inputs(self, site, month, known_at=None):
        self.calls.append((site.site_code, month, known_at))
        if self.fail is not None:
            raise self.fail
        return SimpleNamespace(leaves=self.leaves, stated={})


class World:
    def __init__(self, leaves=None) -> None:
        self.store = MemoryDecisionStore()
        self.p = LakesidePeople(self.store.add_site, self.store.add_person)
        numbers = count(1)
        new_id = lambda: UUID(int=next(numbers))  # noqa: E731
        decisions = DecisionService(self.store, self.p.accounts, clock=lambda: CLOCK, new_id=new_id, levers=LEVERS)
        self.prepared = decisions.prepare(tenant_slug=SLUG, as_email=email("wanjiru"), site_code="KOBO-001",
                                          lever_id="test_stop_reserve", period="2026-10", current=CURRENT,
                                          finding_id=None)
        self.decision_id = self.prepared.decision.id
        for option in self.prepared.options[1:]:
            decisions.state_one_off(tenant_slug=SLUG, as_email=email("peter"), decision_id=self.decision_id,
                                    option_key=option.option_key, amount=D("90.00"), currency="USD", crew_visits=0,
                                    basis="Technician sets the controller on a routine visit")
        self.read = FakeRead(f1_base() if leaves is None else leaves)
        self.service = EvaluationService(self.store, self.p.accounts, self.read, clock=lambda: CLOCK, new_id=new_id,
                                         levers=LEVERS, grid_changes=TEST_GRID, read_bytes=read_study_bytes)

    def evaluate(self, study=F1, who="wanjiru"):
        return self.service.evaluate(tenant_slug=SLUG, as_email=email(who), decision_id=self.decision_id,
                                     study_path=study)


@pytest.fixture()
def w() -> World:
    return World()


def refused(code: str):
    return pytest.raises(DecisionRefused, match=f"^{code}$")


def _fields(row):
    return dataclasses.replace(row, id=None, option_id=None, one_off_id=None)


# --- test 5: the service --------------------------------------------------------------------------------------------

def test_5_f1b_end_to_end_equals_test_4(w) -> None:
    run = w.evaluate()
    assert w.store.runs == [run] and run.outcome == "RECOMMENDED"
    outcome, rows, _, _ = run_f1()
    assert outcome == run.outcome
    keys = {o.id: o.option_key for o in w.prepared.options}
    assert [keys[e.option_id] for e in run.evaluations] == list(rows)
    for e in run.evaluations:
        assert _fields(e) == _fields(rows[keys[e.option_id]]), keys[e.option_id]
    one_offs = w.store.latest_one_offs(run.tenant_id, w.decision_id)
    assert [e.one_off_id for e in run.evaluations] == [None] + [one_offs[o.id].id for o in w.prepared.options[1:]]
    assert len({e.id for e in run.evaluations}) == 8
    assert (run.evaluator_version, run.known_at, run.run_at, run.run_role, run.run_by_script) \
        == ("option-evaluator-1", CLOCK, CLOCK, "ANALYST", True)
    assert run.run_by_person_id == w.p.people["Wanjiru"]
    assert run.study_sha256 == "5aa40e709c759e8e860d346efb2b747aaed46964d3a0725affd8734e42912153"
    assert dict(run.study_identity) == {
        "input_class": "SIMULATED", "evidence_class": "MODELLED", "commit": "f1" * 20, "model": "mini-grid/8",
        "season": "v2", "season_inputs_digest": "a" * 64, "trajectory_digests": {"site": "b" * 64},
        "assumptions": ["fixture"], "admission_rule": ["fixture"], "status": "CALIBRATED",
        "window_start": "2026-09-30T21:00:00Z", "days": 31,
        "frame": {"kind": "SITE_RECORD", "tenant": "lakeside-power", "site_code": "KOBO-001"},
        "ignored_cases": [], "months_averaged": ["2026-10"]}
    assert w.read.calls == [("KOBO-001", "2026-10", CLOCK)]


def test_5_every_call_writes_a_new_run(w) -> None:
    first, second = w.evaluate(), w.evaluate()
    assert first.id != second.id and len(w.store.runs) == 2


def test_5_an_extra_case_at_todays_settings_is_ignored_and_listed(w, tmp_path) -> None:
    doc = study_doc()
    doc["cases"].append(dict(case_doc(doc, "stop-90-reserve-25"), case_id="stop-90-reserve-30",
                             reserve_soc_pct={"exact": "30/1"}))
    run = w.evaluate(write_study(tmp_path, doc))
    assert run.study_identity["ignored_cases"] == ["stop-90-reserve-30"] and run.outcome == "RECOMMENDED"


def _plant(tmp_path, fn, name="study.json"):
    doc = study_doc()
    fn(doc)
    return write_study(tmp_path, doc, name)


def _month_30(doc):
    for case in [doc["baseline"], *doc["cases"]]:
        for field in ("avoided_l_by_month", "added_throughput_kwh_by_month"):
            case[field][0]["days"] = 30


#: E3's order: each plant fails at its step and no earlier.
E3 = [
    ("STUDY_UNREADABLE", lambda d: d.pop("commit")),
    ("STUDY_NOT_CALIBRATED", lambda d: d.update(status="NOT_CALIBRATED", frame={"kind": "SITE_RECORD",
                                                                                "tenant": "x", "site_code": "y"})),
    ("STUDY_LABELS_INVALID", lambda d: d.update(input_class="OBSERVED", frame={"kind": "SITE_RECORD",
                                                                               "tenant": "x", "site_code": "y"})),
    ("STUDY_FRAME_MISMATCH", lambda d: (d["frame"].update(site_code="MTO-001"), _month_30(d))),
    ("STUDY_MONTH_NOT_COVERED", lambda d: (_month_30(d), d["baseline"].update(stop_soc_pct={"exact": "85/1"}))),
    ("STUDY_BASELINE_MISMATCH", lambda d: (d["baseline"].update(stop_soc_pct={"exact": "85/1"}),
                                           d["cases"].remove(case_doc(d, "stop-70-reserve-30")))),
    ("STUDY_GRID_MISMATCH", lambda d: (d["cases"].remove(case_doc(d, "stop-70-reserve-30")),
                                       case_doc(d, "stop-80-reserve-30")["admission"].update(admitted=False))),
    ("STUDY_GRID_MISMATCH", lambda d: d["cases"].append(dict(case_doc(d, "stop-70-reserve-30"),
                                                             case_id="stop-75-reserve-30",
                                                             stop_soc_pct={"exact": "75/1"}))),
    ("STUDY_ADMISSION_MISMATCH", lambda d: case_doc(d, "stop-70-reserve-30")["admission"].update(admitted=False)),
]


@pytest.mark.parametrize("code,plant", E3, ids=[f"{i}-{c}" for i, (c, _) in enumerate(E3)])
def test_5_each_e3_refusal_in_order_never_reads_the_structure(w, tmp_path, code, plant) -> None:
    with refused(code):
        w.evaluate(_plant(tmp_path, plant))
    assert w.read.calls == [] and w.store.runs == []


def test_5_e0_to_e2_refusals(w) -> None:
    with refused("PERSON_ROLE_REQUIRED"):
        w.evaluate(who="joseph")
    with refused("DECISION_NOT_FOUND"):
        w.service.evaluate(tenant_slug=SLUG, as_email=email("wanjiru"), decision_id=UUID(int=999), study_path=F1)
    with refused("STUDY_REQUIRED"):
        w.evaluate(study=None)
    assert w.read.calls == [] and w.store.runs == []


def test_5_the_structure_cannot_be_read_or_raises(w) -> None:
    w.read.fail = StoreUnavailable("down")
    with refused("STRUCTURE_UNAVAILABLE"):
        w.evaluate()
    w.read.fail = None
    w.read.leaves = {k: v for k, v in f1_base().items() if k != "wear_rate"}  # E6: a leaf missing is a StructureError
    with pytest.raises(StructureError):
        from assetops_backend.structure.evaluate import evaluate
        from option_fixtures import MG
        evaluate(MG, w.read.leaves)
    with refused("STRUCTURE_UNAVAILABLE"):
        w.evaluate()
    assert w.store.runs == []


def test_5_a_declared_failure_of_the_structure_read_exits_3_and_writes_nothing(w) -> None:
    for error in (StoreUnavailable("down"), StructureError("STRUCTURE_LEAF_INPUT", "MINI_GRID", "x")):
        w.read.fail = error
        with pytest.raises(DecisionRefused) as caught:
            w.evaluate()
        assert (caught.value.code, caught.value.exit) == ("STRUCTURE_UNAVAILABLE", 3)
        assert w.store.runs == []


def test_5_any_other_failure_of_the_structure_read_propagates(w) -> None:
    """D-P6.41: a wiring fault is a traceback, never "the month's figures cannot be read right now"."""
    for error in (TypeError("a wiring fault"), RuntimeError("a defect"), KeyError("leaf")):
        w.read.fail = error
        with pytest.raises(type(error)):
            w.evaluate()
        assert w.store.runs == []


def test_5_the_adapter_maps_a_database_error_and_nothing_else(w) -> None:
    from sqlalchemy.exc import OperationalError

    from assetops_backend.decisions.adapters.structure_read import GuardedStructureRead
    guarded = GuardedStructureRead(w.read)
    assert guarded.site_inputs(SimpleNamespace(site_code="KOBO-001"), "2026-10").leaves is w.read.leaves
    w.read.fail = OperationalError("select 1", {}, Exception("connection refused"))
    with pytest.raises(StoreUnavailable):
        guarded.site_inputs(SimpleNamespace(site_code="KOBO-001"), "2026-10")
    w.read.fail = TypeError("a wiring fault")
    with pytest.raises(TypeError):
        guarded.site_inputs(SimpleNamespace(site_code="KOBO-001"), "2026-10")


def test_5_an_option_of_an_unmodelled_generator_refuses_before_the_study_and_the_read(w, monkeypatch) -> None:
    """D-P6.38: no model for this generator, so no figure: LEVER_UNKNOWN at E3, the study unread, nothing read."""
    real = w.store.decision

    def planted(tenant_id, decision_id):
        decision, options = real(tenant_id, decision_id)
        return decision, tuple(dataclasses.replace(o, generator="PLANT_GENERATOR") if o.position == 3 else o
                               for o in options)
    monkeypatch.setattr(w.store, "decision", planted)
    for study in (F1, "no-such-study.json"):  # a missing file would be STUDY_UNREADABLE if it were read
        with refused("LEVER_UNKNOWN"):
            w.evaluate(study)
        assert w.read.calls == [] and w.store.runs == []


def test_5_e2_reads_the_levers_generator(w) -> None:
    """STUDY_REQUIRED is for a SETTING_GRID lever; a lever of another generator has no model: LEVER_UNKNOWN."""
    other = dataclasses.replace(TEST_LEVER, generator="PLANT_GENERATOR")
    service = EvaluationService(w.store, w.p.accounts, w.read, clock=lambda: CLOCK, levers={"test_stop_reserve": other},
                                grid_changes={}, read_bytes=read_study_bytes)
    with refused("LEVER_UNKNOWN"):
        service.evaluate(tenant_slug=SLUG, as_email=email("wanjiru"), decision_id=w.decision_id, study_path=None)
    with refused("STUDY_REQUIRED"):
        w.evaluate(study=None)
    assert w.read.calls == [] and w.store.runs == []


def test_5_a_refused_record_is_record_invalid(w, monkeypatch) -> None:
    def refuse(run):
        raise DecisionRefused("RECORD_INVALID")
    monkeypatch.setattr(w.store, "add_run", refuse)
    with refused("RECORD_INVALID"):
        w.evaluate()


def test_5_the_start_up_assertion_runs_over_every_entry(w) -> None:
    with pytest.raises(ValueError):
        EvaluationService(w.store, w.p.accounts, w.read, clock=lambda: CLOCK, levers=LEVERS,
                          grid_changes={"test_stop_reserve": SETTING_GRID_CHANGES["generator_stop_reserve"][:1]},
                          read_bytes=read_study_bytes)
    EvaluationService(w.store, w.p.accounts, w.read, clock=lambda: CLOCK, read_bytes=read_study_bytes)  # default map


# --- test 7: the command --------------------------------------------------------------------------------------------

def _main(w, argv, capsys):
    code = command.main(["--tenant", SLUG, "--decision", str(w.decision_id), *argv],
                        services=SimpleNamespace(service=w.service, dispose=lambda: None))
    out, err = capsys.readouterr()
    return code, out, err


F1B_LINE = [  # option_key, disposition, reason_code, rank, monthly, 12 months, value, admitted
    ("no-action", "COMPARISON", None, None, "0.00", "0.00", "0.00", None, None),
    ("stop-90-reserve-25", "DEFERRED", "NOT_WORTH_MORE_THAN_NO_ACTION", None, "6.25", "75.00", "-15.00", "USD", True),
    ("stop-80-reserve-30", "ACCEPTABLE", None, 3, "224.50", "2694.00", "2604.00", "USD", True),
    ("stop-80-reserve-25", "REJECTED", "NOT_ADMITTED_STARTS", None, "236.50", "2838.00", "2748.00", "USD", False),
    ("stop-70-reserve-30", "RECOMMENDED", None, 1, "247.50", "2970.00", "2880.00", "USD", True),
    ("stop-70-reserve-25", "ACCEPTABLE", None, 2, "258.50", "3102.00", "3012.00", "USD", True),
    ("stop-60-reserve-30", "ACCEPTABLE", None, 4, "182.50", "2190.00", "2100.00", "USD", True),
    ("stop-60-reserve-25", "REJECTED", "NOT_ADMITTED_FULL_CHARGE", None, "305.00", "3660.00", "3570.00", "USD", False),
]


def test_7_the_f1b_line_exactly(w, capsys) -> None:
    code, out, err = _main(w, ["--as", email("wanjiru"), "--study", str(F1)], capsys)
    assert (code, err) == (0, "")
    run = w.store.runs[-1]
    expected = {"run_id": str(run.id), "decision_id": str(w.decision_id), "outcome": "RECOMMENDED",
                "source_class": "SIMULATED",
                "frame": {"kind": "SITE_RECORD", "tenant": "lakeside-power", "site_code": "KOBO-001"},
                "months_averaged": ["2026-10"],
                "options": [{"option_key": k, "disposition": d, "reason_code": r, "rank": n, "monthly_change": m,
                             "horizon_change": h, "value": v, "currency": c, "missing": [], "admitted": a}
                            for k, d, r, n, m, h, v, c, a in F1B_LINE]}
    assert out == json.dumps(expected) + "\n"
    assert "@" not in out


def test_7_a_declared_season_line(w, capsys) -> None:
    code, out, _ = _main(w, ["--as", email("wanjiru"), "--study", str(FIXTURES / "study-f1h.json")], capsys)
    got = json.loads(out)
    assert code == 0 and got["outcome"] == "RANKING_INCOMPLETE" and got["months_averaged"] == []
    assert got["frame"] == {"kind": "DECLARED_SEASON", "tenant": None, "site_code": None}
    assert got["options"][4]["missing"] == [["SITE_MONTH_SIMULATION", "SIMULATION", "candidate_l"],
                                            ["SITE_MONTH_SIMULATION", "SIMULATION", "battery_throughput_kwh"]]
    assert got["options"][4]["value"] is None and got["options"][4]["monthly_change"] is None


def test_7_refusals_stderr_and_exit(w, capsys, tmp_path) -> None:
    cases = [(["--as", email("wanjiru")], "STUDY_REQUIRED", 2),
             (["--as", email("wanjiru"), "--study", str(tmp_path / "absent.json")], "STUDY_UNREADABLE", 2),
             (["--as", email("joseph"), "--study", str(F1)], "PERSON_ROLE_REQUIRED", 2)]
    for i, (code_name, plant) in enumerate(E3[1:]):
        cases.append((["--as", email("wanjiru"), "--study", str(_plant(tmp_path, plant, f"s{i}.json"))], code_name, 2))
    for argv, code_name, status in cases:
        code, out, err = _main(w, argv, capsys)
        assert (code, out, err) == (status, "", f"{code_name} {refusal_sentence(code_name)}\n"), code_name
    w.read.fail = StoreUnavailable("down")
    code, out, err = _main(w, ["--as", email("wanjiru"), "--study", str(F1)], capsys)
    assert (code, out, err) == (3, "", "STRUCTURE_UNAVAILABLE The month's figures cannot be read right now.\n")
    code = command.main(["--tenant", SLUG, "--as", email("wanjiru"), "--decision", "nope"])
    assert (code, capsys.readouterr().err) == (2, "BAD_UUID Write the reference as it was printed.\n")


def test_7_the_sentences(w) -> None:
    for code, sentence in SENTENCES.items():
        assert refusal_sentence(code) == sentence
    from assetops_backend.decisions.records import REFUSAL_EXIT
    assert {c: REFUSAL_EXIT[c] for c in SENTENCES} == {**{c: 2 for c in SENTENCES}, "STRUCTURE_UNAVAILABLE": 3}
