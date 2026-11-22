"""6a (`specs/6a-decision-records/spec.md` §4, §6 test 8; handshake I8): the three commands on the memory store.

Each success line's exact keys and values (F-P1, F-O1, F-C1), every refusal's stderr line and exit, no `@` on either
stream, the catalogue key of `decision.refused`, and one case per malformed flag.
"""
from __future__ import annotations

import copy
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from itertools import count
from uuid import UUID, uuid4

import pytest

from assetops_backend import choose_option, prepare_decision, state_one_off
from assetops_backend.i18n import catalogue as i18n_catalogue
from assetops_backend.i18n.catalogue import CatalogueError
from assetops_backend.decisions import records
from assetops_backend.decisions.records import (REFUSAL_EXIT, DecisionService, EvaluationRow, MemoryDecisionStore,
                                                RunRow, refusal_sentence)
from lakeside_people import SLUG, LakesidePeople, email

CLOCK = datetime(2026, 11, 24, 9, 0, tzinfo=timezone.utc)
R1 = UUID("00000000-0000-0000-0000-0000000000a1")
OPTION_70 = "stop-70-reserve-30"
BASIS = "Technician sets the controller on a routine visit"


@dataclass
class Composed:
    service: DecisionService


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
        numbers = count(1)
        self.services = Composed(DecisionService(self.store, self.p.accounts, clock=lambda: CLOCK,
                                                 new_id=lambda: UUID(int=next(numbers))))
        self.store.add_agreed_action(self.p.tenant, R1, self.p.sites["KOBO-001"])

    def go(self, module, argv: list[str], capsys) -> tuple[int, str, str]:
        code = module.main(argv, services=self.services)
        out, err = capsys.readouterr()
        return code, out, err

    def prepare(self, capsys, *more: str, who="wanjiru", site="KOBO-001") -> tuple[int, str, str]:
        argv = ["--tenant", SLUG, "--as", email(who), "--site", site, "--lever", "generator_stop_reserve",
                "--period", "2026-10", "--current", "stop_soc_pct=90,reserve_soc_pct=30", *more]
        return self.go(prepare_decision, argv, capsys)

    def one_off(self, capsys, decision: str, *more: str, who="peter", option=OPTION_70):
        argv = ["--tenant", SLUG, "--as", email(who), "--decision", decision, "--option", option, "--amount", "90.00",
                "--currency", "USD", "--crew-visits", "0", "--basis", BASIS, *more]
        return self.go(state_one_off, argv, capsys)

    def choose(self, capsys, decision: str, *more: str, who="amina"):
        return self.go(choose_option, ["--tenant", SLUG, "--as", email(who), "--decision", decision, *more], capsys)

    def run_stored(self, decision: UUID) -> RunRow:
        _, options = self.store.decision(self.p.tenant, decision)
        dispositions = {"no-action": "COMPARISON", "stop-60-reserve-25": "REJECTED"}
        evaluations = tuple(EvaluationRow(uuid4(), o.id, dispositions.get(o.option_key, "ACCEPTABLE"), None, None,
                                          None, None, None, None, None, "SIMULATED", "MODELLED", (), (), None, None,
                                          ()) for o in options)
        return self.store.add_run(RunRow(uuid4(), self.p.tenant, decision, "option-evaluator-1",
                                         "RANKING_INCOMPLETE", None, None, CLOCK, self.p.people["Wanjiru"],
                                         "ANALYST", True, CLOCK, evaluations))


@pytest.fixture()
def w() -> World:
    return World()


D1 = str(UUID(int=1))
KEYS = ["no-action", "stop-90-reserve-25", "stop-85-reserve-30", "stop-85-reserve-25", "stop-80-reserve-30",
        "stop-80-reserve-25", "stop-75-reserve-30", "stop-75-reserve-25", "stop-70-reserve-30", "stop-70-reserve-25",
        "stop-65-reserve-30", "stop-65-reserve-25", "stop-60-reserve-30", "stop-60-reserve-25"]


def _prepared(w, capsys) -> dict:
    code, out, err = w.prepare(capsys)
    assert (code, err) == (0, "")
    return json.loads(out)


def test_8_prepare_line_has_exactly_its_keys_and_values(w, capsys) -> None:
    code, out, err = w.prepare(capsys)
    line = json.loads(out)
    assert (code, err) == (0, "") and out.endswith("\n") and out.count("\n") == 1 and "@" not in out
    assert list(line) == ["decision_id", "site_code", "lever_id", "period", "horizon_months", "home_category",
                          "options", "prepared_by", "already_prepared"]
    assert (line["decision_id"], line["site_code"], line["lever_id"], line["period"], line["horizon_months"],
            line["home_category"], line["prepared_by"], line["already_prepared"]) == (
        D1, "KOBO-001", "generator_stop_reserve", "2026-10", 12, "OPTIMIZE_COST", "Wanjiru", False)
    assert [o["option_key"] for o in line["options"]] == KEYS
    assert line["options"][0] == {"option_key": "no-action", "settings": {"stop_soc_pct": "90", "reserve_soc_pct": "30"}}
    assert line["options"][8]["settings"] == {"stop_soc_pct": "70", "reserve_soc_pct": "30"}
    again = json.loads(w.prepare(capsys)[1])
    assert again["already_prepared"] is True and again["decision_id"] == D1


def test_8_one_off_line_has_exactly_its_keys_and_values(w, capsys) -> None:
    _prepared(w, capsys)
    code, out, err = w.one_off(capsys, D1)
    line = json.loads(out)
    assert (code, err) == (0, "") and "@" not in out
    assert line == {"decision_id": D1, "option_key": OPTION_70, "amount": "90.00", "currency": "USD",
                    "crew_visits": 0, "basis": BASIS, "declared_by": "Peter", "declared_at": "2026-11-24T09:00:00Z"}
    assert list(line) == ["decision_id", "option_key", "amount", "currency", "crew_visits", "basis", "declared_by",
                          "declared_at"]


def test_8_choose_line_has_exactly_its_keys_and_values(w, capsys) -> None:
    _prepared(w, capsys)
    run = w.run_stored(UUID(int=1))
    code, out, err = w.choose(capsys, D1, "--option", OPTION_70, "--action", str(R1))
    line = json.loads(out)
    assert (code, err) == (0, "") and "@" not in out
    assert list(line) == ["decision_id", "option_key", "run_id", "agreed_action_id", "chosen_by", "chosen_at",
                          "already_chosen"]
    assert line == {"decision_id": D1, "option_key": OPTION_70, "run_id": str(run.id), "agreed_action_id": str(R1),
                    "chosen_by": "Amina", "chosen_at": "2026-11-24T09:00:00Z", "already_chosen": False}
    again = json.loads(w.choose(capsys, D1, "--option", OPTION_70, "--action", str(R1))[1])
    assert again["already_chosen"] is True
    code, _, err = w.choose(capsys, D1, "--option", "stop-80-reserve-30", "--action", str(R1))
    assert (code, err) == (2, f"ALREADY_CHOSEN {refusal_sentence('ALREADY_CHOSEN')}\n")


def test_8_none_is_a_null_option_and_allows_an_action(w, capsys) -> None:
    _prepared(w, capsys)
    w.run_stored(UUID(int=1))
    code, out, _ = w.choose(capsys, D1, "--none", "--action", str(R1))
    line = json.loads(out)
    assert code == 0 and line["option_key"] is None and line["agreed_action_id"] == str(R1)
    assert w.services.service.for_tenant(w.p.tenant)[0].state == "KEPT_AS_IS"


def test_8_option_and_none_together_or_neither_is_argparses_error(w, capsys) -> None:
    for more in (["--option", OPTION_70, "--none"], []):
        with pytest.raises(SystemExit) as stop:
            w.choose(capsys, D1, *more)
        assert stop.value.code == 2
        assert capsys.readouterr().out == ""


# Every refusal: (name, setup, call, code); one fixture each (spec §5).
def _refusals():
    return [
        ("peter-prepares", lambda w, c: w.prepare(c, who="peter"), "PERSON_ROLE_REQUIRED"),
        ("fridge-lever", lambda w, c: w.prepare(c, site="FRIDGE-001"), "LEVER_SITE_TYPE"),
        ("unknown-site", lambda w, c: w.prepare(c, site="NOPE-001"), "SITE_NOT_FOUND"),
        ("finding-missing", lambda w, c: w.prepare(c, "--finding", str(uuid4())), "FINDING_NOT_FOUND"),
        ("horizon-too-big", lambda w, c: w.prepare(c, "--horizon", "61"), "BAD_HORIZON"),
        ("other-horizon", lambda w, c: (w.prepare(c), w.prepare(c, "--horizon", "6"))[1], "ALREADY_PREPARED_OTHER"),
        ("musa-one-off", lambda w, c: (w.prepare(c), w.one_off(c, D1, who="musa"))[1], "PERSON_ROLE_REQUIRED"),
        ("david-one-off-on-kobo", lambda w, c: (w.prepare(c), w.one_off(c, D1, who="david"))[1],
         "PERSON_ROLE_REQUIRED"),
        ("one-off-no-action", lambda w, c: (w.prepare(c), w.one_off(c, D1, option="no-action"))[1],
         "NO_ACTION_ONE_OFF"),
        ("david-missing-decision", lambda w, c: w.one_off(c, D1, who="david"), "DECISION_NOT_FOUND"),
        ("zara-one-off", lambda w, c: (w.prepare(c), w.one_off(c, D1, who="zara"))[1], "PERSON_NOT_FOUND"),
        ("zara-chooses", lambda w, c: (w.prepare(c), w.choose(c, D1, "--none", who="zara"))[1], "PERSON_NOT_FOUND"),
        ("choose-before-run", lambda w, c: (w.prepare(c), w.choose(c, D1, "--option", OPTION_70))[1], "NOT_EVALUATED"),
        ("choose-rejected", lambda w, c: (w.prepare(c), w.run_stored(UUID(int=1)),
                                          w.choose(c, D1, "--option", "stop-60-reserve-25"))[2], "OPTION_REJECTED"),
        ("peter-chooses", lambda w, c: (w.prepare(c), w.run_stored(UUID(int=1)),
                                        w.choose(c, D1, "--none", who="peter"))[2], "PERSON_ROLE_REQUIRED"),
        ("action-elsewhere", lambda w, c: (w.prepare(c), w.run_stored(UUID(int=1)),
                                           w.store.add_agreed_action(w.p.tenant, UUID(int=0xb2), w.p.sites["MTO-001"]),
                                           w.choose(c, D1, "--none", "--action", str(UUID(int=0xb2))))[3],
         "ACTION_SITE_MISMATCH"),
        ("action-without-site", lambda w, c: (w.prepare(c), w.run_stored(UUID(int=1)),
                                              w.store.add_agreed_action(w.p.tenant, UUID(int=0xb3), None),
                                              w.choose(c, D1, "--none", "--action", str(UUID(int=0xb3))))[3],
         "ACTION_SITE_MISMATCH"),
        ("action-missing", lambda w, c: (w.prepare(c), w.run_stored(UUID(int=1)),
                                         w.choose(c, D1, "--none", "--action", str(uuid4())))[2], "ACTION_NOT_FOUND"),
    ]


@pytest.mark.parametrize("name, act, code", _refusals(), ids=[r[0] for r in _refusals()])
def test_8_every_refusal_is_one_stderr_line_and_exit_two(w, capsys, name, act, code) -> None:
    exit_code, stdout, stderr = act(w, capsys)
    assert stderr == f"{code} {refusal_sentence(code)}\n" and exit_code == REFUSAL_EXIT[code] == 2
    assert stdout == "" and "@" not in stderr


# One case per malformed flag (handshake I8): the code, before any store call.
MALFORMED = [
    ("current-no-equals", "BAD_CURRENT", "--current", "stop_soc_pct"),
    ("current-not-decimal", "BAD_CURRENT", "--current", "stop_soc_pct=abc,reserve_soc_pct=30"),
    ("current-empty", "BAD_CURRENT", "--current", ""),
    ("horizon-text", "BAD_HORIZON", "--horizon", "x"),
    ("period-slash", "BAD_PERIOD", "--period", "2026/10"),
    ("period-month-13", "BAD_PERIOD", "--period", "2026-13"),
    ("finding-not-uuid", "BAD_UUID", "--finding", "nope"),
]


@pytest.mark.parametrize("name, code, flag, value", MALFORMED, ids=[m[0] for m in MALFORMED])
def test_8_a_malformed_prepare_flag_maps_to_its_code(w, capsys, name, code, flag, value) -> None:
    flags = {"--tenant": SLUG, "--as": email("wanjiru"), "--site": "KOBO-001", "--lever": "generator_stop_reserve",
             "--period": "2026-10", "--current": "stop_soc_pct=90,reserve_soc_pct=30"}
    flags[flag] = value
    argv = [x for pair in flags.items() for x in pair]
    exit_code, out, err = w.go(prepare_decision, argv, capsys)
    assert (exit_code, out, err) == (2, "", f"{code} {refusal_sentence(code)}\n")
    assert w.store.decisions == []


ONE_OFF_MALFORMED = [
    ("amount-text", "BAD_AMOUNT", "--amount", "abc"), ("amount-nan", "BAD_AMOUNT", "--amount", "NaN"),
    ("crew-text", "BAD_CREW_VISITS", "--crew-visits", "x"), ("decision-uuid", "BAD_UUID", "--decision", "nope"),
]


@pytest.mark.parametrize("name, code, flag, value", ONE_OFF_MALFORMED, ids=[m[0] for m in ONE_OFF_MALFORMED])
def test_8_a_malformed_one_off_flag_maps_to_its_code(w, capsys, name, code, flag, value) -> None:
    _prepared(w, capsys)
    argv = ["--tenant", SLUG, "--as", email("peter"), "--decision", D1, "--option", OPTION_70, "--amount", "90.00",
            "--currency", "USD", "--crew-visits", "0", "--basis", BASIS]
    argv[argv.index(flag) + 1] = value
    exit_code, out, err = w.go(state_one_off, argv, capsys)
    assert (exit_code, out, err) == (2, "", f"{code} {refusal_sentence(code)}\n")
    assert w.store.one_offs == []


def test_8_a_malformed_choose_flag_is_bad_uuid(w, capsys) -> None:
    for more in (["--decision", "nope", "--none"], ["--none", "--action", "nope"]):
        argv = ["--tenant", SLUG, "--as", email("amina"), "--decision", D1, "--none"]
        if more[0] == "--decision":
            argv[argv.index("--decision") + 1] = "nope"
        else:
            argv += ["--action", "nope"]
        exit_code, out, err = w.go(choose_option, argv, capsys)
        assert (exit_code, out, err) == (2, "", f"BAD_UUID {refusal_sentence('BAD_UUID')}\n")


@pytest.mark.parametrize("module, argv", [
    (prepare_decision, ["--tenant", SLUG, "--as", email("wanjiru"), "--site", "KOBO-001", "--lever", "l", "--period",
                        "2026-10", "--current", "a=1"]),
    (state_one_off, ["--tenant", SLUG, "--as", email("peter"), "--decision", D1, "--option", "k", "--amount", "1",
                     "--currency", "USD", "--crew-visits", "0", "--basis", "b"]),
    (choose_option, ["--tenant", SLUG, "--as", email("amina"), "--decision", D1, "--none"]),
])
def test_8_no_database_url_is_no_database_exit_two(module, argv, capsys, monkeypatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    assert module.main(argv) == 2
    out, err = capsys.readouterr()
    assert (out, err) == ("", f"NO_DATABASE {refusal_sentence('NO_DATABASE')}\n")


def test_8_an_unreachable_store_is_exit_three(w, capsys, monkeypatch) -> None:
    def boom(*_a):
        raise records.StoreUnavailable()

    monkeypatch.setattr(w.store, "site", boom)
    code, out, err = w.prepare(capsys)
    assert (code, out, err) == (3, "", f"DECISIONS_UNAVAILABLE {refusal_sentence('DECISIONS_UNAVAILABLE')}\n")


def _shipped() -> tuple[dict, dict]:
    cat = i18n_catalogue.current()
    return copy.deepcopy(cat.statements["en"]), copy.deepcopy(cat.vocabulary["en"])


def _load_code(statements: dict, vocabulary: dict) -> str:
    with pytest.raises(CatalogueError) as e:
        i18n_catalogue._build({"en": [statements]}, {"en": vocabulary})
    return e.value.code


def test_8_the_catalogue_validator_passes_decision_refused_with_one_key_and_a_variant_per_code() -> None:
    statements, vocabulary = _shipped()
    assert sorted(k for k in statements if k.startswith("decision.")) == ["decision.refused"]
    i18n_catalogue._build({"en": [statements]}, {"en": vocabulary})  # loads: exhaustive over the code slot
    for code in REFUSAL_EXIT:
        assert refusal_sentence(code).strip() and "@" not in refusal_sentence(code)


def test_8_plant_a_dropped_variant_fails_the_load() -> None:
    statements, vocabulary = _shipped()
    statements["decision.refused"]["variants"].pop()
    assert _load_code(statements, vocabulary) == "NOT_EXHAUSTIVE"


def test_8_plant_a_key_per_code_fails_the_load() -> None:
    statements, vocabulary = _shipped()
    other = next(k for k in statements if not k.startswith("decision."))
    statements["decision.refused.bad_period"] = statements.pop(other)
    assert _load_code(statements, vocabulary) == "KEY_FORM"
