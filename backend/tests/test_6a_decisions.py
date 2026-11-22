"""6a (`specs/6a-decision-records/spec.md` §5 fixtures, §6 tests 1 to 5 and 9; D-P6.1 to D-P6.29): levers, the
start-up lever check, and the decision records module on the memory store. The fixtures are hand-written literals."""
from __future__ import annotations

import ast
import dataclasses
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from fractions import Fraction
from itertools import count
from pathlib import Path
from types import MappingProxyType
from uuid import UUID, uuid4

import pytest

from assetops_backend.accounts.permissions import roles_of
from assetops_backend.decisions import records
from assetops_backend.decisions.records import (
    ChoiceRow, DecisionRefused, DecisionService, EvaluationRow, MemoryDecisionStore, OptionRow, RunRow,
    StoreUnavailable, refusal_sentence)
from assetops_backend.structure import levers as levers_module
from assetops_backend.structure import pins as pins_module
from assetops_backend.structure.check import StructureError, check_all, check_levers
from assetops_backend.structure.levers import LEVERS, Lever, SettingAxis, grid, option_key
from assetops_backend.structure.registry import REGISTRIES, Home
from lakeside_people import ANALYST, EXEC, FIN, SLUG, SM, LakesidePeople, email

PKG = Path(__file__).resolve().parents[1] / "assetops_backend"
CLOCK = datetime(2026, 11, 24, 9, 0, tzinfo=timezone.utc)
D = Decimal
CURRENT = {"stop_soc_pct": D(90), "reserve_soc_pct": D(30)}
F_P1_KEYS = ["no-action", "stop-90-reserve-25", "stop-85-reserve-30", "stop-85-reserve-25", "stop-80-reserve-30",
             "stop-80-reserve-25", "stop-75-reserve-30", "stop-75-reserve-25", "stop-70-reserve-30",
             "stop-70-reserve-25", "stop-65-reserve-30", "stop-65-reserve-25", "stop-60-reserve-30",
             "stop-60-reserve-25"]
LEVER = "generator_stop_reserve"


# --- test 1: levers -----------------------------------------------------------------------------------------------

def test_1_grid_and_keys_are_the_thirteen_literals_in_order() -> None:
    lever = LEVERS[LEVER]
    points = grid(lever)
    assert len(points) == 14
    assert [option_key(lever, p) for p in points if p != {"stop_soc_pct": D(90), "reserve_soc_pct": D(30)}] \
        == F_P1_KEYS[1:2] + F_P1_KEYS[2:]  # the 13 keys; (90, 30) is the no-action point, not an option
    assert [option_key(lever, p) for p in points][0] == "stop-90-reserve-30"
    assert points[1] == {"stop_soc_pct": D(90), "reserve_soc_pct": D(25)}


def test_1_the_grid_equals_kobo_grid() -> None:
    from assetops_backend.runs.replay_study import KOBO_GRID
    mine = [(Fraction(p["stop_soc_pct"]), Fraction(p["reserve_soc_pct"])) for p in grid(LEVERS[LEVER])]
    assert mine == [(s.stop_soc_pct, s.reserve_soc_pct) for s in KOBO_GRID]


def test_1_the_registry_row_lists_the_lever_and_no_other_does() -> None:
    listing = {(k, r.factor_id): r.levers for k, reg in REGISTRIES.items() for r in reg.rows if r.levers}
    assert listing == {("MINI_GRID", "candidate_l"): (LEVER,)}
    assert REGISTRIES["MINI_GRID"].version == 4


# --- test 2: check_levers -----------------------------------------------------------------------------------------

def _with_row(registries, key: str, factor_id: str, **change):
    reg = registries[key]
    rows = tuple(dataclasses.replace(r, **change) if r.factor_id == factor_id else r for r in reg.rows)
    return MappingProxyType({**registries, key: dataclasses.replace(reg, rows=rows)})


def _lever(**change) -> Lever:
    return dataclasses.replace(LEVERS[LEVER], **change)


def _axis(**change) -> SettingAxis:
    return dataclasses.replace(LEVERS[LEVER].axes[0], **change)


_SECOND = LEVERS[LEVER].axes[1]
_PROTECT = Home("PROTECT_ASSET", "P1")
CASES = {
    "1-row-names-no-lever": dict(registries=_with_row(REGISTRIES, "MINI_GRID", "unexplained_l", levers=("nope",))),
    "2-structure-key": dict(lever=_lever(structure_key="NOPE")),
    "3-purpose-factor": dict(lever=_lever(purpose_factor="nope")),
    "4-row-does-not-list": dict(registries=_with_row(REGISTRIES, "MINI_GRID", "candidate_l", levers=())),
    "5-changes-not-a-leaf": dict(lever=_lever(changes=("candidate_l", "diesel_l"))),
    "6-axis-name": dict(lever=_lever(axes=(_axis(name="Stop"), _SECOND))),
    "7-empty-values": dict(lever=_lever(axes=(_axis(values=()), _SECOND))),
    "8-repeated-value": dict(lever=_lever(axes=(_axis(values=(D(90), D(90))), _SECOND))),
    "9-units-differ": dict(lever=_lever(axes=(LEVERS[LEVER].axes[0], dataclasses.replace(_SECOND, unit="pct")))),
    "10-template-names": dict(lever=_lever(key_template="stop-{stop_soc_pct}")),
    "11-non-whole": dict(lever=_lever(axes=(_axis(values=(D("90.5"), D(85))), _SECOND))),
    "12-same-key": dict(lever=_lever(axes=(SettingAxis("a", (D(1), D(11)), "%"), SettingAxis("b", (D(1), D(11)), "%")),
                                     key_template="{a}{b}")),
    "13-key-form": dict(lever=_lever(key_template="STOP-{stop_soc_pct}-reserve-{reserve_soc_pct}")),
    "14-category": dict(registries=_with_row(REGISTRIES, "MINI_GRID", "unexplained_l", levers=(LEVER,),
                                             home=_PROTECT),
                        pins=MappingProxyType({"UNEXPLAINED_FUEL": pins_module.PINS["UNEXPLAINED_FUEL"]})),
}


def _planted(case: dict):
    lever = case.get("lever", LEVERS[LEVER])
    return dict(levers=MappingProxyType({lever.lever_id: lever}), registries=case.get("registries", REGISTRIES),
                pins=case.get("pins", pins_module.PINS))


def test_2_the_real_data_passes_and_check_all_runs_it(monkeypatch) -> None:
    check_levers()
    calls: list[str] = []
    import assetops_backend.structure.check as check_module
    monkeypatch.setattr(check_module, "check_levers", lambda: calls.append("levers"))
    check_all()
    assert calls == ["levers"]


@pytest.mark.parametrize("name", sorted(CASES))
def test_2_each_branch_refuses(name: str) -> None:
    with pytest.raises(StructureError) as caught:
        check_levers(**_planted(CASES[name]))
    assert caught.value.code == "STRUCTURE_LEVER"


def test_2_the_text_names_the_structure_and_the_lever() -> None:
    with pytest.raises(StructureError, match=r"^STRUCTURE_LEVER MINI_GRID/generator_stop_reserve$"):
        check_levers(**_planted(CASES["3-purpose-factor"]))
    with pytest.raises(StructureError, match=r"^STRUCTURE_LEVER MINI_GRID/nope$"):
        check_levers(**_planted(CASES["1-row-names-no-lever"]))


def test_2_the_cases_cover_fourteen_branches() -> None:
    assert sorted(int(n.split("-")[0]) for n in CASES) == list(range(1, 15))


def _two_pin(category: str):
    """A second pinned factor that lists the lever: `unexplained_l` (a pin of `UNEXPLAINED_FUEL`)."""
    registries = _with_row(REGISTRIES, "MINI_GRID", "unexplained_l", levers=(LEVER,),
                           home=Home(category, "O1"))
    return dict(levers=LEVERS, registries=registries, pins=pins_module.PINS)


def test_2_any_pin_rule_two_pins_one_agreeing_one_not() -> None:
    check_levers(**_two_pin("OPTIMIZE_COST"))  # both agree: passes
    with pytest.raises(StructureError, match="STRUCTURE_LEVER"):
        check_levers(**_two_pin("PROTECT_ASSET"))  # candidate_l agrees, unexplained_l does not: refuses


# --- the people and the service -----------------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _cheap_hash(monkeypatch):
    from assetops_backend.accounts import passwords
    from test_3c0a_accounts_service import PW
    stored = passwords.hash_password(PW)
    monkeypatch.setattr(passwords, "hash_password", lambda _pw: stored)


class World:
    def __init__(self) -> None:
        self.store = MemoryDecisionStore()
        self.p = LakesidePeople(self.store.add_site, self.store.add_person)
        self.clock = [CLOCK]
        numbers = count(1)
        self.service = DecisionService(self.store, self.p.accounts, clock=lambda: self.clock[0],
                                       new_id=lambda: UUID(int=next(numbers)))

    def prepare(self, who="wanjiru", site="KOBO-001", **change):
        args = dict(tenant_slug=SLUG, as_email=email(who), site_code=site, lever_id=LEVER, period="2026-10",
                    current=CURRENT, finding_id=None)
        args.update(change)
        return self.service.prepare(**args)

    def one_off(self, decision_id, key, who="peter", **change):
        args = dict(tenant_slug=SLUG, as_email=email(who), decision_id=decision_id, option_key=key,
                    amount=D("90.00"), currency="USD", crew_visits=0, basis="Technician sets the controller on a "
                    "routine visit")
        args.update(change)
        return self.service.state_one_off(**args)

    def choose(self, decision_id, key, who="amina", action=None):
        return self.service.choose(tenant_slug=SLUG, as_email=email(who), decision_id=decision_id, option_key=key,
                                   agreed_action_id=action)

    def run(self, prepared, dispositions: dict[str, str] | None = None, outcome="RANKING_INCOMPLETE",
            at: datetime = CLOCK) -> RunRow:
        """A stored run: every option `ACCEPTABLE` but the given ones (F-C1: no-action COMPARISON, `stop-60-reserve-25`
        REJECTED)."""
        dispositions = {"no-action": "COMPARISON", "stop-60-reserve-25": "REJECTED", **(dispositions or {})}
        evaluations = tuple(EvaluationRow(
            uuid4(), o.id, dispositions.get(o.option_key, "ACCEPTABLE"), None, None, None, None, None, None, None,
            "SIMULATED", "MODELLED", (), (), None, None, ()) for o in prepared.options)
        return self.store.add_run(RunRow(uuid4(), prepared.decision.tenant_id, prepared.decision.id,
                                         "option-evaluator-1", outcome, None, None, at, self.p.people["Wanjiru"],
                                         "ANALYST", True, at, evaluations))


@pytest.fixture()
def w() -> World:
    return World()


def refused(code: str):
    return pytest.raises(DecisionRefused, match=f"^{code}$")


# --- test 3: prepare (F-P1 to F-P6, P1 to P5) ---------------------------------------------------------------------

def test_3_f_p1_fourteen_options_no_action_first_then_the_grid_minus_today(w) -> None:
    got = w.prepare()
    assert got.already_prepared is False
    assert [o.option_key for o in got.options] == F_P1_KEYS
    assert [o.position for o in got.options] == list(range(14))
    assert [o.generator for o in got.options] == ["NO_ACTION"] + ["SETTING_GRID"] * 13
    assert got.options[0].settings == CURRENT and got.options[1].settings == {"stop_soc_pct": D(90),
                                                                              "reserve_soc_pct": D(25)}
    d = got.decision
    assert (d.id, d.site_id, d.structure_key, d.lever_id, d.purpose_factor_id, d.finding_id, d.period,
            d.horizon_months, d.rule_version) == (UUID(int=1), w.p.sites["KOBO-001"], "MINI_GRID", LEVER,
                                                  "candidate_l", None, "2026-10", 12, "decision-prepare-1")
    assert (d.prepared_by_person_id, d.prepared_role, d.prepared_by_script, d.prepared_at) == (
        w.p.people["Wanjiru"], ANALYST, True, CLOCK)
    assert [o.id for o in got.options] == [UUID(int=n) for n in range(2, 16)]


def test_3_f_p1_a_re_run_is_the_same_decision_and_writes_nothing(w) -> None:
    first = w.prepare()
    again = w.prepare()
    assert again.already_prepared is True and again.decision.id == first.decision.id
    assert (len(w.store.decisions), len(w.store.options)) == (1, 14)
    assert w.prepare(current={"stop_soc_pct": D("90.0"), "reserve_soc_pct": D("30.0")}).already_prepared is True


def test_3_f_p2_a_current_off_the_grid_gives_every_grid_point(w) -> None:
    got = w.prepare(current={"stop_soc_pct": D(72), "reserve_soc_pct": D(30)})
    assert len(got.options) == 15
    assert got.options[0].option_key == "no-action" and got.options[0].settings["stop_soc_pct"] == D(72)
    assert got.options[1].option_key == "stop-90-reserve-30"


def test_3_f_p3_a_finding_on_the_lever_makes_a_second_decision_with_its_pinned_category(w) -> None:
    fid = uuid4()
    w.store.add_finding(w.p.tenant, w.p.sites["KOBO-001"], fid, "GENERATOR_SUPPORT_CANDIDATE")
    first = w.prepare()
    second = w.prepare(finding_id=fid)
    assert second.decision.id != first.decision.id and second.decision.finding_id == fid
    views = {v.decision_id: v for v in w.service.for_tenant(w.p.tenant)}
    assert views[str(second.decision.id)].home_category == "OPTIMIZE_COST"
    assert views[str(first.decision.id)].home_category == "OPTIMIZE_COST"


def test_3_the_heading_follows_the_pinned_factor_when_a_finding_is_set(w, monkeypatch) -> None:
    """Plant: a Protect pin on the lever. The finding's decision reads Protect; the finding-less one, the lever's."""
    fid = uuid4()
    w.store.add_finding(w.p.tenant, w.p.sites["KOBO-001"], fid, "GENERATOR_SUPPORT_CANDIDATE")
    planted = _with_row(REGISTRIES, "MINI_GRID", "candidate_l", home=_PROTECT)
    monkeypatch.setattr(records, "REGISTRIES", planted)
    pin = pins_module.Pin("GENERATOR_SUPPORT_CANDIDATE", "MINI_GRID", "unexplained_l")
    monkeypatch.setattr(pins_module, "PINS", MappingProxyType({**pins_module.PINS, pin.mechanism: pin}))
    other = _with_row(planted, "MINI_GRID", "unexplained_l", home=Home("GROW_REVENUE", "G1"), levers=(LEVER,))
    monkeypatch.setattr(records, "REGISTRIES", other)
    prepared = w.prepare(finding_id=fid)
    plain = w.prepare()
    views = {v.decision_id: v.home_category for v in w.service.for_tenant(w.p.tenant)}
    assert views == {str(prepared.decision.id): "GROW_REVENUE", str(plain.decision.id): "PROTECT_ASSET"}


def test_3_f_p4_p5_findings_refused(w) -> None:
    other = uuid4()
    w.store.add_finding(w.p.tenant, w.p.sites["KOBO-001"], other, "UNEXPLAINED_FUEL")
    with refused("FINDING_NOT_ON_LEVER"):
        w.prepare(finding_id=other)
    with refused("FINDING_NOT_FOUND"):
        w.prepare(finding_id=uuid4())


@pytest.mark.parametrize("change", [
    {"current": {"stop_soc_pct": D(90), "reserve_soc_pct": D(25)}},
    {"horizon_months": 6},
], ids=["other-reserve", "other-horizon"])
def test_3_f_p6_a_re_run_with_other_settings_is_refused(w, change) -> None:
    w.prepare()
    with refused("ALREADY_PREPARED_OTHER"):
        w.prepare(**change)
    assert len(w.store.decisions) == 1


@pytest.mark.parametrize("change, code", [
    ({"period": "2026-13"}, "BAD_PERIOD"), ({"period": "2026-1"}, "BAD_PERIOD"), ({"period": "2026-10-01"}, "BAD_PERIOD"),
    ({"horizon_months": 0}, "BAD_HORIZON"), ({"horizon_months": 61}, "BAD_HORIZON"),
    ({"site": "NOPE-1"}, "SITE_NOT_FOUND"), ({"lever_id": "nope"}, "LEVER_UNKNOWN"),
    ({"site": "FRIDGE-001"}, "LEVER_SITE_TYPE"),
    ({"current": {"stop_soc_pct": D(90)}}, "BAD_CURRENT"),
    ({"current": {**CURRENT, "extra": D(1)}}, "BAD_CURRENT"),
    ({"who": "peter"}, "PERSON_ROLE_REQUIRED"), ({"who": "amina"}, "PERSON_ROLE_REQUIRED"),
    ({"who": "zara"}, "PERSON_NOT_FOUND"), ({"tenant_slug": "nobody"}, "UNKNOWN_TENANT"),
], ids=lambda v: str(v)[:30])
def test_3_each_refusal(w, change, code) -> None:
    if change.get("who") == "zara":
        change = {"as_email": "zara@other-op.example"}
    with refused(code):
        w.prepare(**change)
    assert not w.store.decisions


def test_3_a_store_error_is_decisions_unavailable_exit_3(w, monkeypatch) -> None:
    def boom(*a):
        raise StoreUnavailable()
    monkeypatch.setattr(w.store, "site", boom)
    with pytest.raises(DecisionRefused) as caught:
        w.prepare()
    assert (caught.value.code, caught.value.exit) == ("DECISIONS_UNAVAILABLE", 3)


def test_3_one_clock_read_per_method_and_a_naive_clock_is_refused(w) -> None:
    reads: list[int] = []
    service = DecisionService(w.store, w.p.accounts, clock=lambda: reads.append(1) or CLOCK.replace(microsecond=7))
    service.prepare(tenant_slug=SLUG, as_email=email("wanjiru"), site_code="KOBO-001", lever_id=LEVER, period="2026-10",
                    current=CURRENT, finding_id=None)
    assert len(reads) == 1 and w.store.decisions[0].prepared_at == CLOCK
    naive = DecisionService(w.store, w.p.accounts, clock=lambda: datetime(2026, 11, 24, 9, 0))
    with pytest.raises(ValueError):
        naive.prepare(tenant_slug=SLUG, as_email=email("wanjiru"), site_code="KOBO-001", lever_id=LEVER,
                      period="2026-11", current=CURRENT, finding_id=None)


def test_3_the_memory_store_refuses_a_decision_without_a_no_action_option(w) -> None:
    got = w.prepare()
    bad = dataclasses.replace(got.decision, id=uuid4(), period="2026-09")
    only_grid = tuple(dataclasses.replace(o, id=uuid4(), decision_id=bad.id) for o in got.options[1:])
    with refused("RECORD_INVALID"):
        w.store.add_decision(bad, only_grid)
    twice = (got.options[0], dataclasses.replace(got.options[0], id=uuid4(), position=0)) + got.options[1:]
    with refused("RECORD_INVALID"):
        w.store.add_decision(bad, tuple(dataclasses.replace(o, decision_id=bad.id) for o in twice))


# --- test 4: one-offs ---------------------------------------------------------------------------------------------

def test_4_f_o1_the_latest_statement_is_current(w) -> None:
    d = w.prepare().decision
    first = w.one_off(d.id, "stop-70-reserve-30")
    assert (first.amount, first.currency, first.crew_visits, first.declared_role, first.declared_by_script) == (
        D("90.00"), "USD", 0, SM, True)
    assert first.declared_by_person_id == w.p.people["Peter"] and first.declared_at == CLOCK
    w.clock[0] = CLOCK + timedelta(minutes=5)
    second = w.one_off(d.id, "stop-70-reserve-30", amount=D("120.00"))
    latest = w.store.latest_one_offs(w.p.tenant, d.id)
    assert list(latest.values()) == [second] and len(w.store.one_offs) == 2


@pytest.mark.parametrize("change, code", [
    ({"who": "musa"}, "PERSON_ROLE_REQUIRED"), ({"who": "david"}, "PERSON_ROLE_REQUIRED"),
    ({"who": "wanjiru"}, "PERSON_ROLE_REQUIRED"), ({"key": "no-action"}, "NO_ACTION_ONE_OFF"),
    ({"key": "stop-1-reserve-1"}, "OPTION_NOT_FOUND"),
    ({"amount": D("-1")}, "BAD_AMOUNT"), ({"amount": D("1.001")}, "BAD_AMOUNT"),
    ({"amount": D("1" + "0" * 12)}, "BAD_AMOUNT"), ({"amount": D("NaN")}, "BAD_AMOUNT"),
    ({"currency": "usd"}, "BAD_CURRENCY"), ({"currency": "US"}, "BAD_CURRENCY"),
    ({"crew_visits": -1}, "BAD_CREW_VISITS"),
    ({"basis": "   "}, "BAD_BASIS"), ({"basis": "x" * 201}, "BAD_BASIS"), ({"basis": "a\nb"}, "BAD_BASIS"),
], ids=lambda v: str(v)[:30])
def test_4_each_refusal(w, change, code) -> None:
    d = w.prepare().decision
    key = change.pop("key", "stop-70-reserve-30")
    with refused(code):
        w.one_off(d.id, key, **change)
    assert not w.store.one_offs


def test_4_zero_amount_and_whole_digits_are_allowed(w) -> None:
    d = w.prepare().decision
    assert w.one_off(d.id, "stop-70-reserve-30", amount=D("0")).amount == D("0.00")
    assert w.one_off(d.id, "stop-70-reserve-30", amount=D("999999999999.99")).amount == D("999999999999.99")


def test_4_david_on_a_missing_decision_is_decision_not_found(w) -> None:
    with refused("DECISION_NOT_FOUND"):
        w.one_off(uuid4(), "stop-70-reserve-30", who="david")


def test_4_joseph_covers_every_site_and_hassan_is_recorded_as_finance(w) -> None:
    d = w.prepare().decision
    assert w.one_off(d.id, "stop-70-reserve-30", who="joseph").declared_role == FIN
    hassan = w.one_off(d.id, "stop-70-reserve-25", who="hassan")  # SITE_MANAGER at MTO-001 only, and finance lead
    assert hassan.declared_role == FIN
    # Peter on KOBO-001 is a site manager of it.
    assert w.one_off(d.id, "stop-70-reserve-30", who="peter").declared_role == SM


def test_4_zara_cannot_state_one_off_on_lakesides_decision(w) -> None:
    d = w.prepare().decision
    with refused("PERSON_NOT_FOUND"):
        w.one_off(d.id, "stop-70-reserve-30", as_email="zara@other-op.example")


# --- test 5: choose and the read ----------------------------------------------------------------------------------

R1 = UUID(int=900)


def _with_action(w, site="KOBO-001"):
    w.store.add_agreed_action(w.p.tenant, R1, w.p.sites[site])


def test_5_f_c1_chosen_once_under_the_agreed_action(w) -> None:
    _with_action(w)
    prepared = w.prepare()
    run = w.run(prepared)
    got = w.choose(prepared.decision.id, "stop-70-reserve-30", action=R1)
    option = next(o for o in prepared.options if o.option_key == "stop-70-reserve-30")
    c = got.choice
    assert got.already_chosen is False
    assert (c.option_id, c.run_id, c.agreed_action_id, c.chosen_by_person_id, c.chosen_role, c.chosen_by_script,
            c.chosen_at) == (option.id, run.id, R1, w.p.people["Amina"], EXEC, True, CLOCK)
    assert w.choose(prepared.decision.id, "stop-70-reserve-30", action=R1).already_chosen is True
    with refused("ALREADY_CHOSEN"):
        w.choose(prepared.decision.id, "stop-80-reserve-30", action=R1)
    with refused("ALREADY_CHOSEN"):
        w.choose(prepared.decision.id, "stop-70-reserve-30")  # same option, no Action: a different choice
    assert len(w.store.choices) == 1
    assert w.service.for_tenant(w.p.tenant)[0].state == "UNDER_WAY"


def test_5_a_site_manager_cannot_choose_and_only_the_executive_can(w) -> None:
    prepared = w.prepare()
    w.run(prepared)
    for who in ("peter", "joseph", "wanjiru", "musa"):
        with refused("PERSON_ROLE_REQUIRED"):
            w.choose(prepared.decision.id, "stop-70-reserve-30", who=who)
    with refused("PERSON_NOT_FOUND"):
        w.service.choose(tenant_slug=SLUG, as_email="zara@other-op.example", decision_id=prepared.decision.id,
                         option_key=None, agreed_action_id=None)
    assert not w.store.choices


def test_5_refusals_in_order(w) -> None:
    _with_action(w)
    w.store.add_agreed_action(w.p.tenant, UUID(int=901), w.p.sites["MTO-001"])
    w.store.add_agreed_action(w.p.tenant, UUID(int=902), None)
    prepared = w.prepare()
    d = prepared.decision.id
    with refused("DECISION_NOT_FOUND"):
        w.choose(uuid4(), None)
    with refused("NOT_EVALUATED"):
        w.choose(d, "stop-70-reserve-30")
    w.run(prepared)
    with refused("OPTION_NOT_FOUND"):
        w.choose(d, "nope")
    with refused("CHOOSE_NONE_INSTEAD"):
        w.choose(d, "no-action")
    with refused("OPTION_REJECTED"):
        w.choose(d, "stop-60-reserve-25")
    with refused("ACTION_NOT_FOUND"):
        w.choose(d, "stop-70-reserve-30", action=UUID(int=999))
    with refused("ACTION_SITE_MISMATCH"):
        w.choose(d, "stop-70-reserve-30", action=UUID(int=901))
    with refused("ACTION_SITE_MISMATCH"):
        w.choose(d, "stop-70-reserve-30", action=UUID(int=902))  # a Site-less Action
    assert not w.store.choices


def test_5_none_stores_a_null_option_and_none_with_an_action_reads_kept_as_is(w) -> None:
    _with_action(w)
    prepared = w.prepare()
    w.run(prepared)
    got = w.choose(prepared.decision.id, None, action=R1)
    assert got.choice.option_id is None and got.choice.agreed_action_id == R1
    assert w.choose(prepared.decision.id, None, action=R1).already_chosen is True
    assert w.service.for_tenant(w.p.tenant)[0].state == "KEPT_AS_IS"  # not UNDER_WAY: a null option reads first


def test_5_choosing_an_unvalued_or_deferred_option_is_allowed(w) -> None:
    prepared = w.prepare()
    w.run(prepared, {"stop-70-reserve-30": "DEFERRED"})
    assert w.choose(prepared.decision.id, "stop-70-reserve-30").already_chosen is False


def test_5_the_choice_is_tied_to_the_latest_run(w) -> None:
    prepared = w.prepare()
    w.run(prepared)
    later = w.run(prepared, at=CLOCK + timedelta(hours=1))
    assert w.choose(prepared.decision.id, None).choice.run_id == later.id


def test_5_site_by_id_found_and_missing(w) -> None:
    found = w.store.site_by_id(w.p.tenant, w.p.sites["KOBO-001"])
    assert (found.site_code, found.site_type) == ("KOBO-001", "MINIGRID")
    assert w.store.site_by_id(w.p.tenant, uuid4()) is None
    assert w.store.site_by_id(w.p.other, w.p.sites["KOBO-001"]) is None


def test_5_the_read_states_names_order_and_period(w) -> None:
    older = w.prepare(period="2026-10")
    w.clock[0] = CLOCK + timedelta(hours=1)
    newer = w.prepare(site="KISIWA-001", period="2026-11")
    views = w.service.for_tenant(w.p.tenant)
    assert [v.decision_id for v in views] == [str(newer.decision.id), str(older.decision.id)]
    first = views[1]
    assert (first.state, first.decides_role, first.prepared_by_name, first.site_code, first.site_name,
            first.recommended, first.run, first.choice) == (
        "NOT_VALUED", "OPERATOR_EXECUTIVE", "Wanjiru", "KOBO-001", "KOBO-001", None, None, None)
    assert [o.option_key for o in first.options] == F_P1_KEYS
    w.one_off(older.decision.id, "stop-70-reserve-30")
    w.run(older)
    first = w.service.for_tenant(w.p.tenant)[1]
    assert first.state == "WAITING" and first.recommended is None  # RANKING_INCOMPLETE
    assert first.run.run_by_name == "Wanjiru" and first.run.source_class == "SIMULATED"
    option = next(o for o in first.options if o.option_key == "stop-70-reserve-30")
    assert (option.one_off.amount, option.one_off.declared_by_name, option.evaluation.disposition) == (
        D("90.00"), "Peter", "ACCEPTABLE")
    w.choose(older.decision.id, "stop-70-reserve-30")
    chosen = w.service.for_tenant(w.p.tenant)[1]
    assert chosen.state == "CHOSEN" and (chosen.choice.option_key, chosen.choice.chosen_by_name) == (
        "stop-70-reserve-30", "Amina")
    only_oct = w.service.for_tenant(w.p.tenant, period_from="2026-10", period_to="2026-10")
    assert [v.period for v in only_oct] == ["2026-10"]
    assert w.service.for_tenant(w.p.tenant, period_from="2026-11", period_to="2026-12")[0].period == "2026-11"
    assert w.service.for_tenant(w.p.tenant, period_from="2026-12", period_to="2026-11") == ()
    with refused("BAD_PERIOD"):
        w.service.for_tenant(w.p.tenant, period_from="2026-1")
    assert w.service.for_tenant(w.p.other) == ()


def test_5_recommended_is_the_runs_recommended_row(w) -> None:
    prepared = w.prepare()
    run = w.run(prepared, outcome="RECOMMENDED")
    target = next(e for e in run.evaluations if e.option_id == prepared.options[3].id)
    w.store.runs[-1] = dataclasses.replace(run, evaluations=tuple(
        dataclasses.replace(e, disposition="RECOMMENDED", value=D("12.5"), currency="USD") if e is target else e
        for e in run.evaluations))
    view = w.service.for_tenant(w.p.tenant)[0]
    assert (view.recommended.option_key, view.recommended.value, view.recommended.currency) == (
        prepared.options[3].option_key, D("12.5"), "USD")


def test_5_no_email_in_the_read(w) -> None:
    w.prepare()
    assert "@" not in repr(w.service.for_tenant(w.p.tenant))


def test_5_the_memory_store_refuses_a_run_missing_an_option(w) -> None:
    prepared = w.prepare()
    run = w.run(prepared)
    short = dataclasses.replace(run, id=uuid4(), evaluations=run.evaluations[:-1])
    with refused("RECORD_INVALID"):
        w.store.add_run(short)


def _whole_run(w, prepared):
    """A complete run that is not stored (the world's `run` stores it)."""
    stored = w.run(prepared)
    w.store.runs.remove(stored)
    return dataclasses.replace(stored, id=uuid4())


def test_5_cross_row_an_evaluation_of_another_decisions_option_is_refused(w) -> None:  # D-P6.30
    one, two = w.prepare(), w.prepare(period="2026-09")
    run = _whole_run(w, one)
    foreign = dataclasses.replace(run.evaluations[0], option_id=two.options[0].id)  # same count, a foreign option
    with refused("RECORD_INVALID"):
        w.store.add_run(dataclasses.replace(run, evaluations=(foreign, *run.evaluations[1:])))
    assert w.store.runs == []
    w.store.add_run(run)


def test_5_cross_row_a_one_off_of_another_option_is_refused(w) -> None:  # D-P6.30
    prepared = w.prepare()
    other = w.one_off(prepared.decision.id, "stop-70-reserve-30")
    run = _whole_run(w, prepared)
    own = next(e for e in run.evaluations if e.option_id == other.option_id)
    wrong = next(e for e in run.evaluations if e.option_id != other.option_id)
    for e, ok in ((wrong, False), (own, True)):
        priced = dataclasses.replace(run, id=uuid4(), evaluations=tuple(
            dataclasses.replace(x, one_off_id=other.id) if x is e else x for x in run.evaluations))
        if ok:
            w.store.add_run(priced)
        else:
            with refused("RECORD_INVALID"):
                w.store.add_run(priced)


def test_5_cross_row_a_choice_of_another_decisions_option_or_run_is_refused(w) -> None:  # D-P6.30
    one, two = w.prepare(), w.prepare(period="2026-09")
    run_one, run_two = w.run(one), w.run(two)
    me = w.p.people["Amina"]

    def row(decision, option, run):
        return ChoiceRow(uuid4(), decision.tenant_id, decision.id, option, run.id, None, me, EXEC, True, CLOCK)

    with refused("RECORD_INVALID"):
        w.store.add_choice(row(one.decision, two.options[1].id, run_one))  # an option of another decision
    with refused("RECORD_INVALID"):
        w.store.add_choice(row(one.decision, one.options[1].id, run_two))  # a run of another decision
    assert w.store.choices == []
    w.store.add_choice(row(one.decision, one.options[1].id, run_one))


def test_5_a_choice_that_loses_a_race_is_refused_when_it_differs(w) -> None:  # F2, D-P6.33
    prepared = w.prepare()
    w.run(prepared)
    w.choose(prepared.decision.id, "stop-70-reserve-30")
    real, seen = w.store.choice, []
    w.store.choice = lambda t, d: None if not seen and not seen.append(1) else real(t, d)  # H2 sees nothing
    with refused("ALREADY_CHOSEN"):
        w.choose(prepared.decision.id, "stop-80-reserve-30")


# --- statements (D-P6.7) ------------------------------------------------------------------------------------------

SENTENCES = {
    "UNKNOWN_TENANT": "No operator has that name.",
    "PERSON_NOT_FOUND": "The person is not an active person of this operator.",
    "PERSON_ROLE_REQUIRED": "This person's role does not allow this step.",
    "BAD_PERIOD": "Write the month as YYYY-MM, like 2026-10.",
    "BAD_HORIZON": "Write the horizon as 1 to 60 months.",
    "SITE_NOT_FOUND": "This operator has no Site with that code.",
    "LEVER_UNKNOWN": "No change of that kind is known.",
    "LEVER_SITE_TYPE": "That kind of change does not apply to this Site's type.",
    "FINDING_NOT_FOUND": "This Site has no finding with that reference.",
    "FINDING_NOT_ON_LEVER": "That finding is not about what this change acts on.",
    "BAD_CURRENT": "Give today's value for each setting of this change.",
    "ALREADY_PREPARED_OTHER": "This decision was prepared with other current settings.",
    "DECISION_NOT_FOUND": "This operator has no decision with that reference.",
    "OPTION_NOT_FOUND": "This decision has no option with that name.",
    "NO_ACTION_ONE_OFF": "Doing nothing costs nothing to put in place.",
    "BAD_AMOUNT": "Write the amount as a number with at most 2 decimals, like 90.00.",
    "BAD_CURRENCY": "Write the currency as 3 capital letters, like USD.",
    "BAD_CREW_VISITS": "Write the crew visits as a whole number.",
    "BAD_BASIS": "Say in up to 200 characters what the cost is based on.",
    "ALREADY_CHOSEN": "This decision already has a recorded choice.",
    "NOT_EVALUATED": "The options have not been valued yet.",
    "CHOOSE_NONE_INSTEAD": "To keep things as they are, choose none.",
    "OPTION_REJECTED": "This option was rejected and cannot be chosen.",
    "ACTION_NOT_FOUND": "This operator has no agreed Action with that reference.",
    "ACTION_SITE_MISMATCH": "That Action is for another Site.",
    "BAD_UUID": "Write the reference as it was printed.",
    "NO_DATABASE": "Set DATABASE_URL to the operator's database.",
    "RECORD_INVALID": "This record does not fit the decision it names, so nothing was stored.",
    "DECISIONS_UNAVAILABLE": "The decisions store cannot be reached right now.",
}


def test_statements_every_code_renders_its_sentence() -> None:
    six_c = {c for c in records.REFUSAL_EXIT if c.startswith("STUDY_") or c == "STRUCTURE_UNAVAILABLE"}  # 6c's test 7
    assert set(SENTENCES) == set(records.REFUSAL_EXIT) - six_c
    for code, sentence in SENTENCES.items():
        assert refusal_sentence(code) == sentence, code
    assert records.REFUSAL_EXIT["DECISIONS_UNAVAILABLE"] == 3
    assert {c for c, e in records.REFUSAL_EXIT.items() if e == 2} - six_c == set(SENTENCES) - {"DECISIONS_UNAVAILABLE"}


def test_the_roles_are_the_spec_table() -> None:
    assert roles_of("decision.prepare") == (ANALYST,)
    assert roles_of("decision.one_off") == (SM, FIN)
    assert roles_of("decision.choose") == (EXEC,)


# --- test 9: seams ------------------------------------------------------------------------------------------------

def _imports(path: Path) -> set[str]:
    out: set[str] = set()
    for node in ast.walk(ast.parse(path.read_text())):
        if isinstance(node, ast.Import):
            out |= {a.name for a in node.names}
        elif isinstance(node, ast.ImportFrom):
            out.add(node.module or "")
            out |= {f"{node.module}.{a.name}" for a in node.names}
    return out


def test_9_records_imports_no_adapter_and_only_6cs_modules_import_runs() -> None:
    # 6c amends this test (D-P6.28): only study_input, models, evaluate and run import runs.admission and
    # runs.replay_study (6c's test 9 checks the names).
    for path in (PKG / "decisions").rglob("*.py"):
        for name in _imports(path):
            if name.startswith("assetops_backend.runs"):
                assert path.name in ("study_input.py", "models.py", "evaluate.py", "run.py"), (path, name)
    assert not [n for n in _imports(PKG / "decisions" / "records.py") if "adapters" in n or "sqlalchemy" in n
                or "psycopg" in n]


def test_9_levers_imports_only_the_pure_standard_modules() -> None:
    names = {n.split(".")[0] + ("." + n.split(".")[1] if n.startswith("collections") else "")
             for n in _imports(PKG / "structure" / "levers.py")}
    assert names <= {"__future__", "decimal", "dataclasses", "types", "collections.abc"}, names
