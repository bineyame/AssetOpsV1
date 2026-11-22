"""6h4 (`specs/6h-named-option-levers/spec.md` §6, §10.2 test 4): option records on the memory store. Each step R1 to R9
refuses with its code; the newest record per option and factor is the one read; the role and the person are recorded;
the CLI prints one JSON line."""
from __future__ import annotations

import json
from datetime import timedelta
from decimal import Decimal as D
from uuid import UUID

import pytest

from assetops_backend import state_option_record
from assetops_backend.decisions.records import COMMANDS, REFUSAL_EXIT, DecisionRefused, refusal_sentence
from lakeside_people import SLUG, email
from test_6a_commands import Composed
from test_6a_decisions import CLOCK, World, _cheap_hash  # noqa: F401 - the autouse password stand-in

DOC, BASIS = "Signed storage contract", "Clause 4 of the contract"


def _decision(lever="storage_contract", site="FRIDGE-001"):
    w = World()
    return w, w.prepare(site=site, lever_id=lever, current={})


def _state(w, prepared, **change):
    args = dict(tenant_slug=SLUG, as_email=email("joseph"), decision_id=prepared.decision.id,
                option_key="storage-contract", factor_id="contract_crate_days", value=D(4500), unit="DAY",
                currency=None, document=DOC, basis=BASIS, emulated=False)
    args.update(change)
    return w.service.state_option_record(**args)


def test_the_permission_and_command():
    assert COMMANDS["option_record"] == "decision.option_record"
    from assetops_backend.accounts.permissions import roles_of
    assert roles_of("decision.option_record") == roles_of("decision.one_off")


def test_a_record_is_written_with_its_role_and_person():
    w, p = _decision()
    row = _state(w, p)
    assert (row.value, row.unit, row.currency, row.origin, row.declared_role, row.declared_by_script) == (
        D(4500), "DAY", None, "observed-financial", "FINANCE_AND_COMMERCIAL_LEAD", True)
    assert row.declared_by_person_id == w.p.people["Joseph"] and row.declared_at == CLOCK
    assert _state(w, p, emulated=True).origin == "source-emulated"


def test_the_newest_record_per_option_and_factor_is_read():
    w, p = _decision()
    _state(w, p, value=D(4400))
    w.clock[0] = CLOCK + timedelta(minutes=1)
    _state(w, p, value=D(4500))
    _state(w, p, factor_id="contract_rate", value=D("0.18"), unit="MONEY/DAY", currency="USD")
    latest = w.store.latest_option_records(w.p.tenant, p.decision.id)
    option = next(o for o in p.options if o.option_key == "storage-contract")
    assert latest[(option.id, "contract_crate_days")].value == D(4500)
    assert len(latest) == 2 and len(w.store.option_records) == 3


@pytest.mark.parametrize("name, change, code", [
    ("r1-decision", {"decision_id": UUID(int=999)}, "DECISION_NOT_FOUND"),
    ("r1b-analyst-holds-no-role", {"as_email": email("wanjiru")}, "PERSON_ROLE_REQUIRED"),
    ("r1b-site-manager-of-another-site", {"as_email": email("peter")}, "PERSON_ROLE_REQUIRED"),
    ("r2-option", {"option_key": "nope"}, "OPTION_NOT_FOUND"),
    ("r3-no-action", {"option_key": "no-action"}, "NO_ACTION_RECORD"),
    ("r4-factor-unknown", {"factor_id": "crate_days"}, "RECORD_NOT_ON_OPTION"),
    ("r5-unit", {"unit": "KWH"}, "BAD_RECORD_UNIT"),
    ("r6-not-finite", {"value": D("NaN")}, "BAD_VALUE"),
    ("r6-seven-places", {"value": D("0.1234567")}, "BAD_VALUE"),
    ("r6-fifteen-digits", {"value": D(10) ** 14}, "BAD_VALUE"),
    ("r7-money-without-currency", {"factor_id": "contract_rate", "unit": "MONEY/DAY", "currency": None}, "BAD_CURRENCY"),
    ("r7-money-malformed-currency", {"factor_id": "contract_rate", "unit": "MONEY/DAY", "currency": "usd"}, "BAD_CURRENCY"),
    ("r7-currency-on-a-count", {"currency": "USD"}, "BAD_CURRENCY"),
    ("r8-document", {"document": "  "}, "BAD_DOCUMENT"),
    ("r8-document-long", {"document": "x" * 201}, "BAD_DOCUMENT"),
    ("r8-basis", {"basis": ""}, "BAD_BASIS"),
])
def test_each_step_refuses_with_its_code(name, change, code):
    w, p = _decision()
    with pytest.raises(DecisionRefused) as caught:
        _state(w, p, **change)
    assert caught.value.code == code and w.store.option_records == []


def test_a_study_sourced_leaf_refuses_r4():
    w = World()
    w.store.add_site(w.p.tenant, "DEPOT-001", "EV_CHARGING", UUID(int=0xE1))
    p = w.prepare(site="DEPOT-001", lever_id="charging_schedule", current={})
    with pytest.raises(DecisionRefused) as caught:
        w.service.state_option_record(tenant_slug=SLUG, as_email=email("joseph"), decision_id=p.decision.id,
                                      option_key="deadline-aware", factor_id="peak_kwh", value=D(1), unit="KWH",
                                      currency=None, document=DOC, basis=BASIS, emulated=False)
    assert caught.value.code == "RECORD_NOT_ON_OPTION"


def test_a_grid_option_refuses_r4():
    w = World()
    p = w.prepare()  # a SETTING_GRID decision
    with pytest.raises(DecisionRefused) as caught:
        w.service.state_option_record(tenant_slug=SLUG, as_email=email("joseph"), decision_id=p.decision.id,
                                      option_key="stop-70-reserve-30", factor_id="candidate_l", value=D(1), unit="L",
                                      currency=None, document=DOC, basis=BASIS, emulated=False)
    assert caught.value.code == "RECORD_NOT_ON_OPTION"


def test_the_one_off_still_reads_its_own_command():
    w = World()
    p = w.prepare()
    assert w.one_off(p.decision.id, "stop-70-reserve-30").declared_role == "SITE_MANAGER"


def test_the_six_codes_have_their_sentences_and_exit_2():
    sentences = {
        "NO_ACTION_RECORD": "Doing nothing has no records to state.",
        "RECORD_NOT_ON_OPTION": "That option does not change that figure, or its change comes from a simulation.",
        "BAD_RECORD_UNIT": "The unit does not match that figure's unit.",
        "BAD_VALUE": "Give a number with at most 6 decimal places.",
        "BAD_DOCUMENT": "Name the document, in 1 to 200 characters.",
        "STUDY_NOT_FOR_LEVER": "This kind of change is not valued from a simulation file."}
    for code, text in sentences.items():
        assert REFUSAL_EXIT[code] == 2 and refusal_sentence(code) == text


def test_the_cli_prints_one_json_line(capsys):
    w, p = _decision()
    argv = ["--tenant", SLUG, "--as", email("joseph"), "--decision", str(p.decision.id), "--option", "storage-contract",
            "--factor", "contract_rate", "--value", "0.18", "--unit", "MONEY/DAY", "--currency", "USD",
            "--document", DOC, "--basis", BASIS, "--emulated"]
    code = state_option_record.main(argv, services=Composed(w.service))
    out, err = capsys.readouterr()
    line = json.loads(out)
    assert (code, err, out.count("\n")) == (0, "", 1)
    assert line == {"decision_id": str(p.decision.id), "option_key": "storage-contract", "factor_id": "contract_rate",
                    "value": "0.18", "unit": "MONEY/DAY", "currency": "USD", "origin": "source-emulated",
                    "document": DOC, "basis": BASIS, "declared_role": "FINANCE_AND_COMMERCIAL_LEAD",
                    "declared_at": line["declared_at"]}


def test_the_cli_refuses_a_bad_value_with_exit_2(capsys):
    w, p = _decision()
    argv = ["--tenant", SLUG, "--as", email("joseph"), "--decision", str(p.decision.id), "--option", "storage-contract",
            "--factor", "contract_crate_days", "--value", "many", "--unit", "DAY", "--document", DOC, "--basis", BASIS]
    code = state_option_record.main(argv, services=Composed(w.service))
    out, err = capsys.readouterr()
    assert (code, out) == (2, "") and err.startswith("BAD_VALUE ")
