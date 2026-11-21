"""SC-1a (spec section 6): the statement composer. Backend-suite tests that need no database.

Every expected string is a hand literal from spec sections 5 and 6 (W2); none is produced by calling `render` or a
format. Plants (spec section 6, P1 to P41) each fail with their named code; the guard plants (P12 to P14, P17,
P42 to P50) live in `tools/checks/test_statement_catalogue.py`.
"""
from __future__ import annotations

import copy
import datetime
import json
from decimal import Decimal as D

import pytest

from assetops_backend.i18n import (Absent, Count, Day, Evidence, Flag, Instant, Items, KOfN, Money, Month, Name,
                                   Percent, Price, Quantity, State, StatementError, WireError, Word, from_wire,
                                   message, render, served, to_wire)
from assetops_backend.i18n import catalogue, conditions, formats, schema
from assetops_backend.i18n.catalogue import CatalogueError
from assetops_backend.i18n.statements.en.vocabulary import VOCABULARY
from statement_cases import common as common_cases
from statement_cases import worked

FIN, EMU = worked.FIN, worked.EMU
DECLARED = Evidence("DECLARED", FIN)


def build(*modules, vocab=None):
    return catalogue._build({"en": list(modules)}, {"en": vocab or VOCABULARY})


def load_code(*modules, vocab=None) -> str:
    with pytest.raises(CatalogueError) as e:
        build(*modules, vocab=vocab)
    return e.value.code


def statement(text: str, slots: dict | None = None, **fields) -> dict:
    return {"test.thing": {"slots": slots or {}, "variants": [{"id": "only", "text": text}], **fields}}


def mutated(change, base=None) -> dict:
    stmts = copy.deepcopy(base or worked.WORKED)
    change(stmts)
    return stmts


def vocab_with(change) -> dict:
    v = copy.deepcopy(VOCABULARY)
    change(v)
    return v


# --- T1 facts ------------------------------------------------------------------------------------------------------


def test_t1_facts_are_immutable_value_objects_and_not_encodable():
    m = Money(D("1"), "USD", DECLARED)
    assert m == Money(D("1"), "USD", Evidence("DECLARED", FIN)) and hash(m) == hash(Money(D("1"), "USD", DECLARED))
    assert m != Money(D("1"), "KES", DECLARED)
    with pytest.raises(AttributeError):
        m.value = D("2")
    with pytest.raises(AttributeError):
        del m.currency
    assert repr(m).startswith("Money(Decimal('1'), 'USD', Evidence(")
    with pytest.raises(TypeError):
        json.dumps(m)  # P40: no generic encoder walks a fact
    from fastapi.encoders import jsonable_encoder
    with pytest.raises(Exception):
        jsonable_encoder(m)


@pytest.mark.parametrize("build_fact, error", [
    pytest.param(lambda: Money(D("5"), "USD"), TypeError, id="P15-money-without-evidence"),
    (lambda: Money(D("5"), "USD", None), TypeError),
    (lambda: Money(5.0, "USD", DECLARED), TypeError),
    (lambda: Money(None, "USD", DECLARED), TypeError),
    (lambda: Money(D("NaN"), "USD", DECLARED), ValueError),
    (lambda: Money(D("Infinity"), "USD", DECLARED), ValueError),
    (lambda: Money(D("1"), "usd", DECLARED), ValueError),
    (lambda: Money(D("1"), "US", DECLARED), ValueError),
    pytest.param(lambda: Evidence("NOT_AVAILABLE"), ValueError, id="P37-evidence-not-available"),
    pytest.param(lambda: Evidence("NEUTRAL"), ValueError, id="P37-evidence-neutral"),
    (lambda: Evidence("RECORDED", "observed"), ValueError),
    (lambda: Evidence("RECORDED", FIN, "yes"), TypeError),
    pytest.param(lambda: Items(()), ValueError, id="P37-items-empty"),
    pytest.param(lambda: Items((Name("A", "site.name"), Name("A", "site.name"))), ValueError, id="P37-items-repeat"),
    pytest.param(lambda: Items((Absent("NONE"),)), TypeError, id="P37-items-absent"),
    (lambda: Items((Name("A", "site.name"), Word("record", "BILLING"))), TypeError),
    (lambda: Items([Name("A", "site.name")]), TypeError),
    pytest.param(lambda: Name("", "site.code"), ValueError, id="P37-name-empty"),
    (lambda: Name("A", ""), ValueError),
    (lambda: Name("A\nB", "site.code"), ValueError),
    pytest.param(lambda: Day(datetime.datetime(2026, 12, 15)), TypeError, id="P37-day-datetime"),
    pytest.param(lambda: Quantity(D("1"), "L", Evidence("MEASURED", FIN, True)), ValueError,
                 id="P37-quantity-reconciled"),
    (lambda: Percent(D("0.1"), Evidence("DERIVED", FIN, False)), ValueError),
    (lambda: Price(D("1"), "USD", "L", Evidence("DERIVED", FIN, True)), ValueError),
    pytest.param(lambda: State("matched"), ValueError, id="P37-state-lower"),
    pytest.param(lambda: Absent("x"), ValueError, id="P37-absent-lower"),
    (lambda: Absent(""), ValueError),
    pytest.param(lambda: Month(2026, 13), ValueError, id="P37-month-13"),
    (lambda: Month(2026, 0), ValueError),
    pytest.param(lambda: Count(True, "site"), TypeError, id="P37-count-bool"),
    (lambda: Count(-1, "site"), ValueError),
    (lambda: KOfN(3, 2, "site"), ValueError),
    (lambda: KOfN(0, 0, "site"), ValueError),
    (lambda: Instant(datetime.datetime(2026, 11, 20, 8)), ValueError),
    (lambda: Flag(1), TypeError),
    (lambda: Word("", "x"), ValueError),
])
def test_t1_constructors_refuse_impossible_facts(build_fact, error):
    with pytest.raises(error):
        build_fact()


# --- T2 formats (hand literals, through the one renderer) ------------------------------------------------------------


def show(spec: dict, fact, **extra) -> str:
    """`fact` rendered alone in a one-slot statement (served for a figure, so no evidence word is appended)."""
    is_served = spec["type"] in ("money", "price", "quantity", "percent") and "evidence" not in spec
    st = statement("{x}", {"x": spec, **extra}, **({"evidence": "served"} if is_served else {}))
    with catalogue._use(build(st)):
        msg = message("test.thing", x=fact)
        return served(msg)["text"] if is_served else render(msg)


def usd(value, currency="USD"):
    return Money(D(value), currency, DECLARED)


@pytest.mark.parametrize("value, options, english", [
    ("-1234.50", {}, "−$1,234.50"),
    ("0", {}, "$0.00"),
    ("-0.001", {"abs": True}, "less than $0.01"),
    ("-0.001", {}, "more than −$0.01"),
    ("5", {"signed": True}, "+$5.00"),
    ("5.015", {"round": "down"}, "$5.01"),
    ("5.015", {"round": "up"}, "$5.02"),
    ("0.004", {}, "less than $0.01"),
    ("-0.00", {"signed": True}, "$0.00"),
])
def test_t2_money(value, options, english):
    assert show({"type": "money", **options}, usd(value)) == english


def test_t2_money_currency_prefix():
    assert show({"type": "money"}, usd("1200", "KES")) == "KES 1,200.00"
    assert show({"type": "money"}, usd("-1200", "KES")) == "−KES 1,200.00"


@pytest.mark.parametrize("value, currency, unit, english", [
    ("1.25", "USD", "L", "$1.25 per L"),  # F1
    ("0.4321", "USD", "kWh", "$0.4321 per kWh"),  # F2
    ("1.2", "USD", "L", "$1.20 per L"),  # F3
    ("12.34567", "KES", "L", "KES 12.3457 per L"),  # F4
    ("0.00004", "USD", "kWh", "less than $0.0001 per kWh"),  # F5
])
def test_t2_price(value, currency, unit, english):
    assert show({"type": "price"}, Price(D(value), currency, unit, Evidence("DECLARED", FIN))) == english


@pytest.mark.parametrize("value, options, english", [
    ("1200.500", {}, "1,200.5 L"),
    ("1E+2", {}, "100 L"),
    ("1.2E+3", {}, "1,200 L"),
    ("0.04", {"places": 1}, "less than 0.1 L"),
    ("1234.56", {"places": 1}, "1,234.6 L"),
    ("5", {"signed": True}, "+5 L"),
])
def test_t2_quantity(value, options, english):
    assert show({"type": "quantity", **options}, Quantity(D(value), "L", Evidence("MEASURED", FIN))) == english


@pytest.mark.parametrize("value, places, english", [
    ("0.0101", 0, "1%"), ("0.0101", 1, "1.0%"), ("0.0101", 2, "1.01%"), ("0.0101", "normal", "1.01%"),
    ("0.005", "normal", "0.5%"), ("1", 0, "100%"), ("1", "normal", "100%"), ("0.004", 0, "less than 1%"),
])
def test_t2_percent(value, places, english):
    assert show({"type": "percent", "places": places}, Percent(D(value), Evidence("DERIVED", FIN))) == english


def test_t2_counts_dates_words_items():
    assert show({"type": "count"}, Count(1, "site")) == "1 Site"
    assert show({"type": "count"}, Count(2, "site")) == "2 Sites"
    assert show({"type": "count"}, Count(1200, "reading")) == "1,200 readings"
    assert show({"type": "count", "bare": True}, Count(2, "site")) == "2"
    assert show({"type": "k_of_n"}, KOfN(1, 1, "site")) == "1 of 1 Site"
    assert show({"type": "k_of_n"}, KOfN(2, 3, "site")) == "2 of 3 Sites"
    assert show({"type": "month"}, Month(2026, 10)) == "October 2026"
    assert show({"type": "month", "form": "month"}, Month(2026, 10)) == "October"
    assert show({"type": "day"}, Day(datetime.date(2026, 12, 15))) == "15 December 2026"
    eat = datetime.timezone(datetime.timedelta(hours=3))
    assert show({"type": "instant"}, Instant(datetime.datetime(2026, 11, 20, 11, 0, tzinfo=eat))) == \
        "20 November 2026, 08:00 UTC"
    assert show({"type": "word", "vocabulary": "factor", "form": "in_sentence", "article": True},
                Word("factor", "om")) == "an O&M"
    assert show({"type": "word", "vocabulary": "factor"}, Word("factor", "fuel_cost")) == "Fuel cost"
    of_names = {"type": "items", "of": {"type": "name"}}
    assert show(of_names, Items((Name("Kisiwa", "site.name"),))) == "Kisiwa"
    assert show(of_names, Items((Name("Kisiwa", "site.name"), Name("Mto", "site.name")))) == "Kisiwa and Mto"
    assert show(of_names, Items(tuple(Name(n, "site.name") for n in ("Kobo", "Kisiwa", "Mto")))) == \
        "Kobo, Kisiwa and Mto"
    by_vocabulary = {"type": "items", "order": "vocabulary",
                     "of": {"type": "word", "vocabulary": "factor", "form": "in_sentence"}}
    assert show(by_vocabulary, Items((Word("factor", "staff"), Word("factor", "om"), Word("factor", "tariff")))) == \
        "tariff, O&M and staff"


#: Spec section 3.5's three steps applied by hand: (evidence) -> words for the origins
#: observed-financial, field-integrated, bench-tested, source-emulated, demo-simulated, unknown, None.
EVIDENCE_WORDS = {
    "RECORDED": ("Recorded", "Recorded", "Recorded", "Emulated", "Simulated", "Estimated", "Estimated"),
    "MEASURED": ("Measured", "Measured", "Measured", "Emulated", "Simulated", "Estimated", "Estimated"),
    "DECLARED": ("Declared",) * 7,  # D-SC1F.1: a setting reads "Declared" for every origin
    "DERIVED": ("Calculated", "Calculated", "Calculated", "Emulated", "Simulated", "Estimated", "Estimated"),
    "ESTIMATED": ("Estimated",) * 7,
    "MODELLED": ("Modelled",) * 7,
}
ORIGIN_COLUMNS = ("observed-financial", "field-integrated", "bench-tested", "source-emulated", "demo-simulated",
                  "unknown", None)


@pytest.mark.parametrize("evidence, column", [(e, i) for e in EVIDENCE_WORDS for i in range(7)])
def test_t2_evidence_word_all_42_pairs(evidence, column):
    fact = Money(D("1"), "USD", Evidence(evidence, ORIGIN_COLUMNS[column]))
    assert show({"type": "money", "evidence": "inline"}, fact) == f"$1.00 ({EVIDENCE_WORDS[evidence][column]})"


def test_v1_declared_reads_declared_for_every_origin():
    """SC-1f V1 (D-SC1F.1): `DECLARED` is step 1 of the three, so no origin, `None` included, changes its word."""
    assert set(ORIGIN_COLUMNS) == {*schema.ORIGINS, None}
    for origin in ORIGIN_COLUMNS:
        assert formats.evidence_word(Evidence("DECLARED", origin), VOCABULARY) == "Declared"


def test_t2_money_suffix():
    st = statement("{x} ({basis})", {"x": {"type": "money", "evidence": {"with": "basis"}},
                                    "basis": {"type": "evidence", "of": ["x"], "money": True}})
    with catalogue._use(build(st)):
        def words(reconciled):
            return render(message("test.thing", x=Money(D("2"), "USD", Evidence("RECORDED", FIN, reconciled))))
        assert words(False) == "$2.00 (Recorded, not yet reconciled)"
        assert words(True) == "$2.00 (Recorded)"
        assert words(None) == "$2.00 (Recorded)"


def test_sc1f_a_with_basis_counts_only_the_figures_its_variant_states():
    """D-SC1F.7: a variant printing no `of` figure and declaring no `requires: present` has no basis word."""
    slots = {"x": {"type": "money", "evidence": {"with": "basis"}},
             "basis": {"type": "evidence", "of": ["x"], "money": True}}
    fact = Money(D("2"), "USD", Evidence("RECORDED", FIN, True))
    with catalogue._use(build(statement("{basis}", slots))):
        with pytest.raises(StatementError) as e:
            render(message("test.thing", x=fact))
        assert e.value.code == "ABSENT_PRINTED"
    declared = statement("{basis}", slots)
    declared["test.thing"]["variants"][0]["requires"] = {"present": "x"}
    with catalogue._use(build(declared)):
        assert render(message("test.thing", x=fact)) == "Recorded"


# --- T3 conditions -------------------------------------------------------------------------------------------------

FACTS = {"gap": usd("-562"), "big": usd("-412"), "zero": usd("0"), "kes": usd("1", "KES"),
         "sites": KOfN(2, 3, "site"), "total": Count(2, "site"), "names": Items((Name("A", "site.name"),)),
         "state": State("MATCHED"), "pending": Flag(True), "share": Absent("ACCOUNTS_ZERO"),
         "missing": Absent("OMITTED")}


@pytest.mark.parametrize("cond, expected", [
    ({"present": "gap"}, True), ({"present": "share"}, False),
    ({"absent": "share"}, True), ({"absent": "gap"}, False),
    ({"reason": ["share", "ACCOUNTS_ZERO"]}, True), ({"reason": ["share", "OTHER"]}, False),
    ({"reason": ["gap", "ACCOUNTS_ZERO"]}, False), ({"reason": ["missing", "OMITTED"]}, True),
    ({"is": ["state", "MATCHED"]}, True), ({"is": ["state", "NOT_MATCHED"]}, False),
    ({"is": ["pending", True]}, True), ({"is": ["pending", False]}, False),
    ({"sign": ["gap", "negative"]}, True), ({"sign": ["gap", "positive"]}, False), ({"sign": ["zero", "zero"]}, True),
    ({"sign": ["share", "zero"]}, False),
    ({"cmp": [{"abs": "big"}, ">", {"abs": "gap"}]}, False), ({"cmp": [{"abs": "gap"}, ">", {"abs": "big"}]}, True),
    ({"cmp": ["gap", "<", "big"]}, True), ({"cmp": ["gap", "==", {"const": "-562.00"}]}, True),
    ({"cmp": ["sites.k", "<", "sites.n"]}, True), ({"cmp": ["sites.k", "==", "total"]}, True),
    ({"cmp": ["names.count", "==", {"const": 1}]}, True), ({"cmp": ["total", ">=", {"const": 3}]}, False),
    ({"cmp": ["share", "<", {"const": 1}]}, False), ({"cmp": ["share", ">=", {"const": 1}]}, False),
    ({"all": [{"present": "gap"}, {"present": "big"}]}, True), ({"all": [{"present": "gap"}, {"present": "share"}]},
                                                                False),
    ({"any": [{"present": "share"}, {"present": "big"}]}, True), ({"any": [{"present": "share"}]}, False),
    ({"not": {"present": "share"}}, True), ({"not": {"present": "gap"}}, False),
])
def test_t3_each_operator(cond, expected):
    assert conditions.holds(cond, FACTS) is expected


def test_t3_money_in_two_currencies_does_not_compare():
    with pytest.raises(conditions.ConditionTypeError):
        conditions.holds({"cmp": ["gap", "<", "kes"]}, FACTS)
    with pytest.raises(conditions.ConditionTypeError):
        conditions.holds({"cmp": ["gap", "<", "total"]}, FACTS)


# --- T7 legacy unchanged -------------------------------------------------------------------------------------------


@pytest.mark.parametrize("key, params, english", [
    ("analytics.site_not_found", {"site_id": "KOBO-001"}, "No Site KOBO-001 is configured."),
    ("reading_upload.checked", {"readings": 1440},
     "Checked the whole file: 1440 readings. Nothing is saved until you confirm."),
    ("reading_upload.state.accepted", {"accepted": 10, "total": 12}, "Accepted 10 of 12 readings."),
    ("reading_upload.state.processing_with_held", {"accepted": 9, "total": 12, "held": 3},
     "9 of 12 sent readings accepted; 3 held because their unit is not the unit this meter reports. AssetOps is "
     "working out what the accepted readings mean."),
    ("reading_upload.bad_request", {"detail": "no file"}, "The upload request is not valid: no file."),
])
def test_t7_legacy_renders_as_before(key, params, english):
    assert render(message(key, **params)) == english


def test_t7_legacy_falls_back_to_english_per_key():
    assert render(message("reading_upload.checked", readings=5), "fr") == \
        "Checked the whole file: 5 readings. Nothing is saved until you confirm."
    with pytest.raises(KeyError):
        render(message("no_such.key"))


def test_t7_legacy_refuses_facts_and_structured_refuses_text():
    with pytest.raises(StatementError) as e:
        render(message("analytics.site_not_found", site_id=Name("KOBO-001", "site.code")))
    assert e.value.code == "FACT_TYPE"
    with pytest.raises(StatementError) as e:
        render(message("common.not_available", pending="false"))
    assert e.value.code == "FACT_TYPE"


# --- T8 load -------------------------------------------------------------------------------------------------------


def test_t8_shipped_catalogue_loads():
    cat = catalogue._load()
    # Adopters add their area's statements and vocabularies (3A7: `reconciliation.*`, D-SC1.28; 3C2: `agreed_action.*`,
    # `action_state`, D-3C2.14).
    assert set(cat.statements["en"]) == {"common.not_available", "common.budget_lines",
                                         "reconciliation.heading", "reconciliation.gap", "reconciliation.share",
                                         "reconciliation.scope", "reconciliation.statement", "reconciliation.standing",
                                         "reconciliation.money_word", "reconciliation.refused",
                                         "agreed_action.state", "agreed_action.refused",
                                         # 3C1b (D-SC1.28): the trial action's actor words.
                                         "action.actor_label", "action.observe_note", "action.change_statement",
                                         "action.publish_note", "action.client_authority_forbidden",
                                         "action.unknown_site"}
    assert set(cat.vocabulary["en"]) == {"factor", "heading", "headline_subject", "record", "record_noun",
                                         "evidence", "unit", "noun", "month", "format", "action_state"}


def test_t8_a_module_with_a_docstring_loads_by_its_assignment_value():
    source = '"""Doc."""\nSTATEMENTS = {"test.thing": {"variants": [{"id": "only", "text": "Hello."}]}}\n'
    assert catalogue.read_module(source, "STATEMENTS") == {
        "test.thing": {"variants": [{"id": "only", "text": "Hello."}]}}
    with catalogue._use(build(source)):
        assert render(message("test.thing")) == "Hello."


def test_t8_unit_symbol_may_hold_a_superscript():
    v = vocab_with(lambda v: v["unit"]["entries"].update({"m3": {"symbol": "m³"}}) or v["unit"]["order"].append(
        "m3"))
    build(vocab=v)


# --- T10 wire ------------------------------------------------------------------------------------------------------

EVERY_FACT = {
    "money": Money(D("1.2E+3"), "USD", Evidence("RECORDED", FIN, False)),
    "price": Price(D("0.4321"), "KES", "kWh", Evidence("DECLARED", None)),
    "quantity": Quantity(D("1200.500"), "L", Evidence("MEASURED", "bench-tested")),
    "percent": Percent(D("-0.0100"), Evidence("DERIVED", EMU)),
    "count": Count(4, "site"), "k_of_n": KOfN(2, 3, "site"), "month": Month(2026, 10),
    "day": Day(datetime.date(2026, 12, 15)),
    "instant": Instant(datetime.datetime(2026, 11, 20, 11, tzinfo=datetime.timezone(datetime.timedelta(hours=3)))),
    "word": Word("factor", "om"), "name": Name("KOBO-001", "site.code"), "state": State("MATCHED"),
    "flag": Flag(False), "items": Items((Name("A", "site.name"), Name("B", "site.name"))),
    "absent": Absent("ACCOUNTS_ZERO"), "legacy": "text", "number": 3, "real": 1.5,
}


def round_trip(msg):
    return from_wire(json.loads(json.dumps(to_wire(msg))))


def test_t10_every_fact_class_round_trips_exactly():
    msg = message("any.key", **EVERY_FACT)
    back = round_trip(msg)
    assert back == msg
    assert str(back["params"]["money"].value) == "1.2E+3" and str(back["params"]["quantity"].value) == "1200.500"
    assert back["params"]["instant"].at.utcoffset() == datetime.timedelta(hours=3)


def test_t10_common_cases_render_the_same_after_the_wire():
    for case in common_cases.CASES:
        msg = message(case.key, **case.facts)
        assert render(round_trip(msg)) == render(msg) == case.english


@pytest.mark.parametrize("obj", [
    pytest.param({"key": "k", "params": {"x": {"fact": "money_amount", "value": "1"}}}, id="P40-unknown-fact"),
    pytest.param({"key": "k", "params": {"x": {"fact": "state", "value": "A", "extra": 1}}}, id="P40-extra-field"),
    pytest.param({"key": "k", "params": {"x": {"fact": "percent", "value": 0.1, "evidence": {
        "evidence": "DERIVED", "origin": None, "reconciled": None}}}}, id="P40-float-value"),
    {"key": "k", "params": {"x": {"fact": "count", "n": True, "noun": "site"}}},
    {"key": "k", "params": {"x": {"fact": "count", "noun": "site"}}},
    {"key": "k", "params": {"x": {"fact": "percent", "value": "abc", "evidence": {
        "evidence": "DERIVED", "origin": None, "reconciled": None}}}},
    {"key": "k", "params": {"x": {"fact": "percent", "value": "1", "evidence": {"evidence": "DERIVED"}}}},
    {"key": "k", "params": {"x": None}},
    {"key": "k"},
    pytest.param({"key": "k", "params": {"m": {"fact": ["money"]}}}, id="P40b-unhashable-fact-name"),
])
def test_t10_from_wire_is_strict(obj):
    with pytest.raises(WireError) as e:
        from_wire(obj)
    assert e.value.code == "WIRE_FORM"


def test_t10_from_wire_runs_the_constructor():
    with pytest.raises(ValueError):
        from_wire({"key": "k", "params": {"x": {"fact": "state", "value": "lower"}}})


# --- T11 reach -----------------------------------------------------------------------------------------------------


def test_t11_reach_passes_on_the_worked_statements():
    build(worked.WORKED)


def test_t11_p35_headline_without_on_target_reaches_zero():
    stmts = mutated(lambda s: s["deep_dive.headline"]["variants"].pop(1))
    with pytest.raises(CatalogueError) as e:
        build(stmts)
    assert e.value.code == "PICK_REACH" and e.value.detail[2:] == ("direction", "zero")


def picked(with_guard: bool) -> dict:
    variants = [{"id": "other", "when": {"is": ["level", "OTHER"]}, "text": "Unknown level."}] * with_guard
    return {"test.level": {
        "slots": {"level": {"type": "state", "values": ["LOW", "HIGH", "OTHER"]},
                  "word": {"type": "pick", "on": "level", "domain": ["LOW", "HIGH"],
                           "words": {"LOW": "low", "HIGH": "high"}}},
        "variants": [*variants, {"id": "level", "text": "The level is {word}."}]}}


def test_t11_state_pick_reach():
    build(picked(True))
    assert load_code(picked(False)) == "PICK_REACH"


# --- T12 schema ----------------------------------------------------------------------------------------------------


def test_t12_schema_parity_with_structure_evaluate():
    from assetops_backend.structure import evaluate
    assert schema.EVIDENCE_ORDER == evaluate.EVIDENCE_ORDER
    assert schema.ORIGINS == schema.ORIGIN_ORDER == evaluate.ORIGIN_ORDER


def test_t12_names_read_as_identifiers():
    """Spec section 3.12, "Names read as identifiers" (D-SC1.30): read from code, never in `TOKENS`."""
    from assetops_backend.i18n import facts, messages, wire
    assert tuple(conditions._Operand.__annotations__) == ("abs", "const")
    assert tuple(messages.Message.__annotations__) == ("key", "params")
    assert tuple(wire._Envelope.__annotations__) == ("fact",)
    assert {cls.__name__: cls.__slots__ for cls in (
        facts.Evidence, facts.Money, facts.Price, facts.Quantity, facts.Percent, facts.Count, facts.KOfN, facts.Month,
        facts.Day, facts.Instant, facts.Word, facts.Name, facts.State, facts.Flag, facts.Absent, facts.Items)} == {
        "Evidence": ("evidence", "origin", "reconciled"), "Money": ("value", "currency", "evidence"),
        "Price": ("value", "currency", "unit", "evidence"), "Quantity": ("value", "unit", "evidence"),
        "Percent": ("value", "evidence"), "Count": ("n", "noun"), "KOfN": ("k", "n", "noun"),
        "Month": ("year", "month"), "Day": ("day",), "Instant": ("at",), "Word": ("vocabulary", "key"),
        "Name": ("text", "source"), "State": ("value",), "Flag": ("value",), "Absent": ("reason",),
        "Items": ("items",)}
    # `abs` and `key` are also option names (money `abs`, part `key`), so they sit in TOKENS by that route.
    assert not {"const", "params", "fact"} & schema.TOKENS


def test_t12_schema_sets_equal_the_spec():
    assert schema.TYPES == ("money", "price", "quantity", "percent", "count", "k_of_n", "month", "day", "instant",
                            "word", "name", "items", "evidence", "pick", "part", "example", "state", "flag")
    forms = ("inline", "with", "derived_from")
    assert schema.OPTIONS == {
        "money": {"round": ("half_even", "down", "up"), "abs": (False, True), "signed": (False, True),
                  "evidence": forms},
        "price": {"abs": (False, True), "evidence": forms},
        "quantity": {"places": ("normal", int), "abs": (False, True), "signed": (False, True), "evidence": forms},
        "percent": {"places": (0, 1, 2, "normal"), "round": ("half_even", "down", "up"), "evidence": forms},
        "count": {"bare": (False, True)}, "k_of_n": {}, "month": {"form": ("month_year", "month")}, "day": {},
        "instant": {}, "word": {"vocabulary": (), "form": ("label", "in_sentence"), "article": (False, True)},
        "name": {}, "items": {"of": (), "order": ("given", "vocabulary")}, "evidence": {"of": (), "money": (False, True)},
        "pick": {"on": (), "words": (), "domain": ()}, "part": {"key": ()}, "example": {"text": ()},
        "state": {"values": ()}, "flag": {}}
    assert schema.FIELDS == ("slots", "variants", "exhaustive", "evidence", "rephrase", "part_only", "id", "when",
                             "requires", "options", "text", "type", "absent", "optional", "forms", "order", "entries",
                             "label", "in_sentence", "article", "one", "other", "symbol", "by_evidence_first",
                             "by_origin", "no_origin", "observed_by_evidence", "money_suffix")
    assert schema.OPERATORS == ("present", "absent", "reason", "is", "sign", "cmp", "all", "any", "not")
    assert schema.COMPARATORS == ("<", "<=", "==", ">=", ">")
    assert schema.SIGNS == ("negative", "zero", "positive")
    assert schema.MODES == ("inline", "served") and schema.REPHRASE == ("never", "allowed")
    assert schema.EVIDENCES == ("RECORDED", "MEASURED", "DECLARED", "DERIVED", "ESTIMATED", "MODELLED")
    assert schema.FORMAT_VOCABULARIES == ("format", "unit", "noun", "month", "evidence")
    assert schema.FORMAT_WORDS == ("less_than", "more_than", "and", "of", "per", "utc")
    assert schema.NUMBER_WORDS == {"en": (
        (("zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten", "eleven", "twelve",
          "hundred", "thousand", "million", "billion", "trillion"), ("", "s", "th", "ths", "fold")),
        (("thir", "four", "fif", "six", "seven", "eigh", "nine"), ("teen", "teens", "teenth", "teenths")),
        (("twen", "thir", "for", "fif", "six", "seven", "eigh", "nine"), ("ty", "ties", "tieth", "tieths", "tyfold")),
        (("first", "second", "third", "fifth", "eighth", "ninth", "twelfth"), ("", "s")),
        (("once", "twice", "thrice", "single", "both", "pair", "couple", "dozen", "half", "quarter", "percent",
          "cent"), ("", "s")),
        (("doubl", "tripl", "quadrupl", "halv"), ("e", "es", "ed", "ing")),
        (("zero", "nought"), ("", "s", "es")))}
    assert schema.UNSERVED == ("ValueError", "TypeError", "KeyError", "LookupError", "RuntimeError", "AssertionError",
                               "SeriesRefused", "NotImplementedError", "StatementError", "CatalogueError", "WireError")
    assert schema.SYMBOLS == ("", " ", ", ", "$", "−", "+", "%", ",", ".", "(", ")", " (", "{", "}", ":", "-",
                              "T")
    assert schema.SYSTEM == ("STATEMENTS", "VOCABULARY", "statements", "vocabulary", "utf-8", "en", "USD", "OMITTED",
                             "ABSENT")
    assert "money" in schema.TOKENS and "less_than" in schema.TOKENS and "$" not in schema.TOKENS
    # D-SC1.32: `TOKENS` no longer holds `NUMBER_WORDS`; no root or suffix is in it unless another set holds it.
    others = set()
    for group in (schema.TYPES, schema.FIELDS, schema.OPERATORS, schema.COMPARATORS, schema.SIGNS, schema.MODES,
                  schema.REPHRASE, schema.EVIDENCES, schema.EVIDENCE_ORDER, schema.ORIGINS,
                  schema.FORMAT_VOCABULARIES, schema.FORMAT_WORDS, schema.UNSERVED, schema.SYSTEM):
        others.update(group)
    for kind, opts in schema.OPTIONS.items():
        others.add(kind)
        for name, allowed in opts.items():
            others.add(name)
            others.update(v for v in allowed if isinstance(v, str))
    parts = {x for roots, suffixes in schema.NUMBER_WORDS["en"] for x in (*roots, *suffixes)}
    assert schema.TOKENS == frozenset(others)
    assert not (parts & schema.TOKENS) - others and "s" not in schema.TOKENS and "teen" not in schema.TOKENS
    words = schema.number_words("en")
    assert {"sixty", "thirteen", "tenth", "hundreds", "dozens", "doubled", "twelfth", "trillionths"} <= words
    assert {"fourth", "ones", "seconds"} <= words and not {"tend", "often", "s", "teen", "ty"} & words


# --- T12b number words (D-SC1.32) ------------------------------------------------------------------------------------

T12B_REFUSED = ("sixty days", "Ninety", "thirteen sites", "the tenth site", "hundreds of sites", "dozens",
                "a couple of sites", "twenty-five", "two-thirds", "tenfold", "doubled", "halved", "Seventieth",
                "millionths", "fourteenth", "eleventh",
                # review round 2, L6: the -ing forms, the spaced percent, and the other zero forms (D-SC1.32's class)
                "doubling", "tripling", "quadrupling", "halving", "per cent", "ten per cent", "zeroes", "nought",
                "noughts", "doubles", "halves")
T12B_LOADS = ("tend", "often", "attend", "tone", "someone", "everyone", "forth", "content", "tenant", "coupled",
              "secondary", "quarterly", "several", "doubt",
              "percentage", "centre", "recent", "century", "doubtful")


@pytest.mark.parametrize("text", T12B_REFUSED)
def test_t12b_p28b_number_words_are_refused(text):
    assert load_code(statement(text)) == "LITERAL_NUMBER_WORD"


@pytest.mark.parametrize("text", T12B_LOADS)
def test_t12b_n_t12_words_that_hold_a_number_root_load(text):
    build(statement(text))


# --- load plants ---------------------------------------------------------------------------------------------------

HEADING = "reconciliation.heading"


def set_text(key, index, text):
    def change(s):
        s[key]["variants"][index]["text"] = text
    return change


def share_as_money(s):
    """P19: the parent declares `share` as the part's percent; the part declares it as money."""
    s[HEADING]["slots"]["share"] = copy.deepcopy(s["reconciliation.share"]["slots"]["share"])
    s["reconciliation.share"]["slots"]["share"] = {"type": "money", "optional": True,
                                                   "evidence": {"derived_from": ["difference", "accounts"]}}


MONEY_SLOT = {"x": {"type": "money", "evidence": "inline"}}

LOAD_PLANTS = [
    pytest.param(lambda: statement("within 1%"), None, "LITERAL_DIGIT", id="P1"),
    pytest.param(lambda: statement("within %"), None, "LITERAL_SYMBOL", id="P1-symbol"),
    pytest.param(lambda: {}, lambda v: v["record"]["entries"]["BILLING"].update(in_sentence="35% at 5 am"),
                 "LITERAL_DIGIT", id="P2"),
    pytest.param(lambda: mutated(set_text(HEADING, 0, "{heading} ({basis}): {accounts} {recorded}, {gap_words}, "
                                          "{allowd} ({tolerance}).")), None, "FIELD_UNDECLARED", id="P3"),
    pytest.param(lambda: mutated(set_text(HEADING, 5, "{heading}: {month} {accounts:,.2f}.")), None, "FIELD_FORM",
                 id="P4"),
    pytest.param(lambda: statement("{x!r}", MONEY_SLOT), None, "FIELD_FORM", id="P4-conversion"),
    pytest.param(lambda: statement("{x[0]}", MONEY_SLOT), None, "FIELD_FORM", id="P4-index"),
    pytest.param(lambda: statement("a {{brace}}"), None, "FIELD_FORM", id="P4-literal-brace"),
    pytest.param(lambda: statement("a } stray"), None, "FIELD_FORM", id="P4-stray-brace"),
    pytest.param(lambda: mutated(set_text(HEADING, 5, "{heading}: {month} is {state}.")), None, "STATE_PRINTED",
                 id="P5"),
    pytest.param(lambda: mutated(lambda s: s[HEADING]["variants"][0].update(when={"gt": ["state", "MATCHED"]})), None,
                 "CONDITION_OPERATOR", id="P6-operator"),
    pytest.param(lambda: mutated(lambda s: s["reconciliation.gap"]["variants"][0].update(
        when={"sign": ["differenc", "zero"]})), None, "CONDITION_SLOT", id="P6-slot"),
    pytest.param(lambda: mutated(lambda s: s["deep_dive.headline"]["variants"][2].update(when={"absent": "gapp"})),
                 None, "CONDITION_SLOT", id="P6-path-gapp"),
    pytest.param(lambda: mutated(lambda s: s[HEADING]["variants"][0].update(when={"is": ["state", "MATCH"]})), None,
                 "CONDITION_VALUE", id="P6-value"),
    pytest.param(lambda: mutated(lambda s: s[HEADING]["variants"].pop(5)), None, "NOT_EXHAUSTIVE", id="P7"),
    pytest.param(lambda: mutated(lambda s: s[HEADING]["variants"][5].update(
        when={"all": [{"is": ["state", "MONTH_OPEN"]}, {"present": "month"}]})), None, "NOT_EXHAUSTIVE", id="P7b"),
    pytest.param(lambda: mutated(lambda s: s["deep_dive.headline"]["variants"][4].update(
        when={"present": "big"})), None, "NO_FALLBACK", id="P8"),
    pytest.param(lambda: mutated(lambda s: s["reconciliation.gap"]["slots"]["direction"]["words"].pop("positive")),
                 None, "PICK_INCOMPLETE", id="P9"),
    pytest.param(lambda: mutated(lambda s: s["reconciliation.gap"]["slots"].update(
        again={"type": "part", "key": "reconciliation.gap"})), None, "PART_CYCLE", id="P10"),
    pytest.param(lambda: "STATEMENTS = dict(a=1)\n", None, "NOT_DATA", id="P11-dict-call"),
    pytest.param(lambda: 'STATEMENTS = {"test.thing": lambda: 1}\n', None, "NOT_DATA", id="P11-lambda"),
    pytest.param(lambda: 'STATEMENTS = {}\nSTATEMENTS = {}\n', None, "NOT_DATA", id="P11-second-assignment"),
    pytest.param(lambda: {}, lambda v: v["evidence"]["observed_by_evidence"].update(MEASURED="Verified"),
                 "VOCABULARY_SCHEMA", id="P18"),
    pytest.param(lambda: mutated(share_as_money), None, "SLOT_CONFLICT", id="P19"),
    pytest.param(lambda: mutated(lambda s: s["reconciliation.gap"]["variants"][1].update(id="same")), None,
                 "VARIANT_ID", id="P20"),
    pytest.param(lambda: mutated(lambda s: s[HEADING]["slots"]["gap_words"].update(key="reconciliation.gapp")), None,
                 "PART_UNKNOWN", id="P21"),
    pytest.param(lambda: {}, lambda v: v["factor"]["entries"]["om"].pop("article"), "VOCABULARY_FORM", id="P22"),
    pytest.param(lambda: mutated(lambda s: s[HEADING].update(rephrase="sometimes")), None, "REPHRASE", id="P23"),
    pytest.param(lambda: 'STATEMENTS = {"test.thing": {"variants": []}, "test.thing": {"variants": []}}\n', None,
                 "KEY_DUPLICATE", id="P25-statement-key"),
    pytest.param(lambda: {}, 'VOCABULARY = {"unit": {"forms": ["symbol"], "order": ["L"], "entries": {'
                             '"L": {"symbol": "L"}, "L": {"symbol": "L"}}}}\n', "KEY_DUPLICATE",
                 id="P25-vocabulary-entry"),
    pytest.param(lambda: statement("within ٣ days"), None, "LITERAL_DIGIT", id="P26-arabic-indic-digit"),
    pytest.param(lambda: {}, lambda v: v["noun"]["entries"]["reading"].update(one="m³"), "LITERAL_DIGIT",
                 id="P26-superscript-outside-unit"),
    pytest.param(lambda: statement("costs ¥"), None, "LITERAL_SYMBOL", id="P27-yen"),
    pytest.param(lambda: {}, lambda v: v["format"]["entries"]["per"].update(in_sentence="per ‰"),
                 "LITERAL_SYMBOL", id="P27-per-mille"),
    pytest.param(lambda: statement("twice the gap"), None, "LITERAL_NUMBER_WORD", id="P28-twice"),
    pytest.param(lambda: statement("Both match"), None, "LITERAL_NUMBER_WORD", id="P28-both"),
    pytest.param(lambda: statement("less", {"p": {"type": "pick", "on": {"sign": "x"}, "words": {
        "negative": "one", "zero": "none", "positive": "more"}}, "x": {"type": "money", "evidence": "inline"}}), None,
        "LITERAL_NUMBER_WORD", id="P28-pick-word"),
    pytest.param(lambda: mutated(lambda s: s["common.not_available"]["variants"][0].update(
        when={"is": ["pending", "true"]}), base=common_statements()), None, "CONDITION_VALUE", id="P29"),
    pytest.param(lambda: mutated(set_text(HEADING, 0, "{heading}: the accounts say {accounts} and the records say "
                                          "{recorded}, {gap_words}, within the {allowed} allowed ({tolerance}).")),
                 None, "EVIDENCE_UNSHOWN", id="P30"),
    pytest.param(lambda: statement("{x}", {"x": {"type": "money"}}), None, "EVIDENCE_UNSHOWN", id="P31"),
    pytest.param(lambda: statement("{x}", {"x": {"type": "money", "evidence": "inline", "tiny": True}}), None,
                 "SLOT_OPTION", id="P31b"),
    pytest.param(lambda: mutated(lambda s: s["deep_dive.headline"]["slots"]["gap"].update(evidence="inline")), None,
                 "SLOT_OPTION", id="P31c"),
    pytest.param(lambda: {**worked.DEEP_DIVE, **statement("{c}", {"c": {"type": "part", "key": "deep_dive.compared"}})},
                 None, "EVIDENCE_MODE", id="P34"),
    pytest.param(lambda: mutated(lambda s: s["reconciliation.share"]["variants"][0].update(
        when={"reason": ["share", "ACCOUNT_ZERO"]})), None, "CONDITION_VALUE", id="P38a"),
    pytest.param(lambda: statement("x", evidence="both_ways"), None, "EVIDENCE_MODE", id="evidence-mode-value"),
    pytest.param(lambda: {"test.thing1": {"variants": [{"id": "only", "text": "x"}]}}, None, "KEY_FORM",
                 id="key-form-digit"),
    pytest.param(lambda: {"test.thing.more": {"variants": [{"id": "only", "text": "x"}]}}, None, "KEY_FORM",
                 id="key-form-segments"),
    pytest.param(lambda: statement("{x}", {"x": {"type": "amount"}}), None, "SLOT_TYPE", id="slot-type"),
    pytest.param(lambda: statement("x", part_only="yes"), None, "REPHRASE", id="part-only-not-bool"),
    pytest.param(lambda: {"test.thing": {"variants": [{"id": "a", "text": "x"}, {"id": "b", "text": "y"}]}}, None,
                 "VARIANT_ID", id="variant-without-when-not-last"),
    pytest.param(lambda: {}, lambda v: v["month"]["order"].reverse() or v["month"]["order"].pop(),
                 "VOCABULARY_SCHEMA", id="vocabulary-order"),
    pytest.param(lambda: mutated(lambda s: s[HEADING]["variants"][0]["options"].update(nothing={"round": "up"})),
                 None, "SLOT_OPTION", id="variant-option-undeclared-slot"),
    pytest.param(lambda: mutated(lambda s: s["reconciliation.share"]["slots"]["share"].update(absent=["lower"])),
                 None, "SLOT_OPTION", id="bad-absent-list"),
    pytest.param(lambda: mutated(lambda s: s[HEADING]["slots"]["state"].update(values=["A", "A"])), None,
                 "SLOT_OPTION", id="repeated-state-value"),
]


def common_statements() -> dict:
    return copy.deepcopy(catalogue._load().statements["en"])


@pytest.mark.parametrize("modules, vocab, code", LOAD_PLANTS)
def test_load_plants_fail_with_their_code(modules, vocab, code):
    v = vocab_with(vocab) if callable(vocab) else vocab
    module = modules()
    assert load_code(*([module] if module else []), vocab=v) == code


def test_p39_locale_incomplete(monkeypatch):
    partial = mutated(lambda s: s.pop("reconciliation.share"))
    with pytest.raises(CatalogueError) as e:  # no number words for `xx`
        catalogue._build({"en": [worked.WORKED], "xx": [worked.WORKED]}, {"en": VOCABULARY, "xx": VOCABULARY})
    assert e.value.code == "LOCALE_INCOMPLETE"
    monkeypatch.setitem(schema.NUMBER_WORDS, "xx", schema.NUMBER_WORDS["en"])
    catalogue._build({"en": [worked.WORKED], "xx": [worked.WORKED]}, {"en": VOCABULARY, "xx": VOCABULARY})
    with pytest.raises(CatalogueError) as e:
        catalogue._build({"en": [worked.WORKED], "xx": [partial]}, {"en": VOCABULARY, "xx": VOCABULARY})
    assert e.value.code == "LOCALE_INCOMPLETE" and e.value.key == "reconciliation.share"


def test_key_duplicate_with_a_legacy_key():
    st = {"analytics.site_not_found": {"variants": [{"id": "only", "text": "x"}]}}
    assert load_code(st) == "KEY_DUPLICATE"


# --- unit 2: the worked statements (T4, T5, T6, T9, T13 and the render plants) ---------------------------------------

WORKED_CAT = worked.catalogue()
ALL_CASES = [*common_cases.CASES, *worked.CASES]


def say(case_or_key, facts=None, serve=None):
    """Render through the test catalogue; `served` for a case with an evidence list."""
    key, facts, serve = (case_or_key.key, case_or_key.facts, case_or_key.evidence is not None) \
        if facts is None else (case_or_key, facts, serve)
    with catalogue._use(WORKED_CAT):
        msg = message(key, **facts)
        return served(msg) if serve else render(msg)


def refusal(key, facts, serve=False) -> str:
    with pytest.raises(StatementError) as e:
        say(key, facts, serve)
    return e.value.code


@pytest.mark.parametrize("case", worked.CASES, ids=lambda c: f"{c.key}-{c.variant}")
def test_t4_worked_cases_render_exactly(case):
    out = say(case)
    if case.evidence is None:
        assert out == case.english
    else:
        assert out == {"text": case.english, "evidence": case.evidence}


def chosen(key, facts, serve=False) -> list:
    from assetops_backend.i18n.render import _render
    trace: list = []
    with catalogue._use(WORKED_CAT):
        _render(message(key, **facts), None, serve, trace)
    return trace


def test_t5_parent_options_reach_the_part():
    c2 = worked.CASES[1]
    assert chosen(c2.key, c2.facts) == [("reconciliation.heading", "matched"), ("reconciliation.gap", "differs")]
    assert "less than $0.01 less" in say(c2)  # `matched`'s round down and the money slot's tiny, in the part
    c1 = worked.CASES[0]
    assert "$5.02 more (1.01%)" in say(c1)  # `not_matched`'s round up on the difference and the share


def test_t5_a_part_ignores_facts_it_does_not_declare():
    facts = {"scope": State("SITE"), "site": Name("KOBO-001", "site.code")}
    assert say("reconciliation.scope", facts) == "KOBO-001"
    assert chosen("reconciliation.scope", facts) == [("reconciliation.scope", "site")]


@pytest.mark.parametrize("case", ALL_CASES, ids=lambda c: f"{c.key}-{c.variant}")
def test_t9_every_case_renders_its_english(case):
    if case.key.startswith("common."):
        assert render(message(case.key, **case.facts)) == case.english
    else:
        test_t4_worked_cases_render_exactly(case)
    trace = chosen(case.key, case.facts, case.evidence is not None) if not case.key.startswith("common.") else None
    assert trace is None or trace[0] == (case.key, case.variant)


@pytest.mark.parametrize("case", ALL_CASES, ids=lambda c: f"{c.key}-{c.variant}")
def test_t10_every_case_renders_the_same_after_the_wire(case):
    msg = message(case.key, **case.facts)
    back = round_trip(msg)
    assert back == msg
    with catalogue._use(WORKED_CAT if not case.key.startswith("common.") else catalogue.current()):
        fn = served if case.evidence is not None else render
        assert fn(back) == fn(msg)


def test_t13_evidence_on_the_page():
    h4, h5, sh4, c9 = worked.CASES[12], worked.CASES[13], worked.CASES[18], worked.CASES[8]
    assert say(h4)["evidence"] == ["Emulated"]  # the gap is stated by `on_target`'s `when`
    assert say(h5)["evidence"] == []  # the gap is absent: nothing stated
    assert say(sh4)["evidence"] == ["Emulated"]  # the share is stated by `no_effect`'s `requires`
    assert say(c9).startswith("Revenue (Recorded, Emulated and Declared): ")
    c7, c10 = worked.CASES[6], worked.CASES[-1]
    assert "tolerance" not in c7.facts and c10.facts["tolerance"].evidence.evidence == "DECLARED"
    assert say(c10) == say(c7) == "Fuel cost (Recorded): the accounts say $0.00 and no fuel invoices are recorded."


C1 = worked.CASES[0].facts
H1 = worked.CASES[9].facts


def without(facts, *names, **replace):
    return {**{k: v for k, v in facts.items() if k not in names}, **replace}


@pytest.mark.parametrize("key, facts, serve, code", [
    pytest.param(HEADING, without(C1, "accounts"), False, "ABSENT_PRINTED", id="P16"),
    pytest.param("deep_dive.headline", without(H1, big=worked.usd("-412.00", "DERIVED", EMU, "KES")), True,
                 "CONDITION_TYPE", id="P24"),
    pytest.param(HEADING, {**worked.CASES[8].facts, "difference": worked.usd("0", "DERIVED", FIN)}, False,
                 "EVIDENCE_DERIVED", id="P32"),
    pytest.param(HEADING, without(C1, allowed=worked.usd("5.015", "DECLARED")), False, "EVIDENCE_DERIVED",
                 id="P32-stronger-than-derived"),
    pytest.param("deep_dive.headline", H1, False, "EVIDENCE_UNSERVED", id="P33"),
    pytest.param(HEADING, C1, True, "EVIDENCE_MODE", id="P33b"),
    pytest.param("deep_dive.headline", without(H1, big=worked.usd("412.00", "DERIVED", EMU)), True,
                 "REQUIRES_FAILED", id="P36-H7"),
    pytest.param("deep_dive.headline", without(H1, big=worked.usd("700.00", "DERIVED", EMU)), True,
                 "REQUIRES_FAILED", id="P36-H8"),
    pytest.param("deep_dive.status_disagreement",
                 {"sites": worked.names("Kisiwa", "Mto", "Kobo", "Thika"), "total": Count(5, "site")}, False,
                 "REQUIRES_FAILED", id="P36-SD5"),
    pytest.param(HEADING, without(C1, share=Absent("OTHER")), False, "ABSENT_REASON", id="P38b"),
    pytest.param("reconciliation.gap", {"difference": C1["difference"]}, False, "PART_ONLY", id="P41"),
    pytest.param(HEADING, {**C1, "colour": State("RED")}, False, "FACT_UNKNOWN", id="fact-unknown"),
    pytest.param(HEADING, without(C1, "heading"), False, "FACT_MISSING", id="fact-missing"),
    pytest.param(HEADING, without(C1, accounts="501.50"), False, "FACT_TYPE", id="fact-type-str-for-money"),
    pytest.param(HEADING, without(C1, heading=Word("record_noun", "REVENUE")), False, "FACT_TYPE",
                 id="fact-type-word-from-wrong-vocabulary"),
    pytest.param(HEADING, without(C1, basis=Evidence("DECLARED", FIN)), False, "FACT_TYPE",
                 id="fact-type-evidence-as-param"),
    pytest.param(HEADING, without(C1, accounts=Absent("OMITTED"), heading=Absent("OMITTED")), False, "FACT_TYPE",
                 id="fact-type-absent-for-required"),
    pytest.param(HEADING, without(C1, state=State("SETTLED")), False, "FACT_TYPE", id="fact-type-state-value"),
    pytest.param(HEADING, without(C1, heading=Word("heading", "WATER")), False, "VOCABULARY_UNKNOWN",
                 id="vocabulary-unknown-key"),
    pytest.param("deep_dive.status_disagreement", {"sites": worked.names("A"), "total": Count(1, "lorry")}, False,
                 "VOCABULARY_UNKNOWN", id="vocabulary-unknown-noun"),
])
def test_render_plants_fail_with_their_code(key, facts, serve, code):
    assert refusal(key, facts, serve) == code


def test_no_fallback_text_anywhere_in_render():
    """D-SC1.11: nothing in the renderer catches an error to substitute text."""
    import ast
    import inspect
    from assetops_backend.i18n import render as render_module
    tree = ast.parse(inspect.getsource(render_module))
    handlers = [h for n in ast.walk(tree) if isinstance(n, ast.Try) for h in n.handlers]
    assert all(isinstance(h.body[-1], ast.Raise) for h in handlers)
