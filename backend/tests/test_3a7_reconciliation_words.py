"""3A7 commit 2 (spec §2.7 and §6 under the rulings' "Amendment (SC-1)"; D-SC1.28): every sentence the service serves,
through the SC-1 composer. No database.

Each expected sentence is a hand literal (W2): spec §6's sentence, changed only by SC-1's rules (money reads `$505.00`,
D-SC1.10; a figure carries its evidence word, D-SC1.18: the heading's `(Recorded, Emulated and Declared)` because the
accounts are `RECORDED`, the fixture's records `source-emulated` and the tolerance `DECLARED`, D-SC1F.1 and .2; the
tolerance's `(Declared)`; number words reworded, D-SC1.21). The packet lists each changed string. Plants at the end
prove the statements, not the service, carry the rounding and the share rule.
"""
from __future__ import annotations

import copy
from decimal import Decimal as D

import pytest

from assetops_backend.i18n import Evidence, Money, render
from assetops_backend.i18n import catalogue
from assetops_backend.i18n.statements.en import reconciliation as module
from assetops_backend.i18n.statements.en.vocabulary import VOCABULARY
from assetops_backend.structure.reconciliation import (ReconRefused, _compare, heading_words, money_word,
                                                        refusal_words)
from statement_cases import reconciliation as cases
from statement_cases import worked
from test_3a7_reconciliation import (ANA, READ_AT, S1_AT, S2_AT, S3_AT, S4_AT, T3_SET_AT, OWNER_REF, _services,
                                     ReconMemoryStore, kobo_steps, ingest, kobo_world, load, only, owner_file, record,
                                     standing, t2_world, two_sites_world)

FIN, EMU = "observed-financial", "source-emulated"
OCT_K_REV = ("Revenue (Recorded, Emulated and Declared): the accounts say $500.00 and the records say $505.50, $5.50 "
             "more (1.10%), beyond the $5.00 allowed (1%).")
OCT_K_FUEL = ("Fuel bought (invoices) (Recorded, Emulated and Declared): the accounts say $780.00 and the records say $762.50, "
              "$17.50 less (2.25%), beyond the $7.80 allowed (1%).")
T2_FUEL = ("Fuel bought (invoices) (Recorded, Emulated and Declared): the accounts say $505.00 and the records say $512.50, $7.50 "
           "more (1.49%), beyond the $5.05 allowed (1%).")
T6_FUEL = "Fuel bought (invoices) (Recorded): the accounts say $40.00, but no fuel invoices are recorded for October 2026."


def texts(check) -> dict[str, str]:
    return {h.heading: h.text for h in check.headings}


# ---------------------------------------------------------------- every case of the new statements renders exactly


@pytest.mark.parametrize("case", cases.CASES, ids=lambda c: f"{c.key}-{c.variant}")
def test_every_case_renders_exactly(case) -> None:
    from assetops_backend.i18n import message

    assert render(message(case.key, **case.facts)) == case.english


def test_the_shipped_heading_gap_share_and_scope_are_sc1s_worked_shapes() -> None:
    """SC-1 §5.1 and §5.4 exactly (the rulings' amendment): `worked.py`'s copies and the shipped module agree."""
    for key in ("reconciliation.heading", "reconciliation.gap", "reconciliation.share", "reconciliation.scope"):
        assert module.STATEMENTS[key] == worked.WORKED[key], key


# ---------------------------------------------------------------- R1: §6.1, 3A4's Kobo month


def test_r1_words_before_and_after_the_corrections() -> None:
    w = kobo_world()
    for s in kobo_steps()[:4]:
        ingest(w, s["at"], s["batch"])
    k = record(w, S1_AT, site="KOBO-001", revenue="500.00", fuel="780.00")
    assert texts(k) == {"revenue": OCT_K_REV, "fuel_bought": OCT_K_FUEL}
    assert k.text == "October 2026 (KOBO-001) does not match the management accounts within 1% (Declared)."
    for s in kobo_steps()[4:6]:
        ingest(w, s["at"], s["batch"])
    after = only(w)
    assert texts(after) == {
        "revenue": "Revenue (Recorded, Emulated and Declared): the accounts say $500.00 and the records say $495.50, "
                   "$4.50 less, within the $5.00 allowed (1%).",
        "fuel_bought": "Fuel bought (invoices) (Recorded, Emulated and Declared): the accounts say $780.00 and the records say "
                     "$775.00, $5.00 less, within the $7.80 allowed (1%)."}
    assert after.text == "Revenue and fuel bought for October 2026 (KOBO-001) match the management accounts within 1% (Declared)."


def test_r1_words_in_eur() -> None:
    w = kobo_world()
    for s in kobo_steps():
        ingest(w, s["at"], s["batch"])
    k = record(w, S1_AT, site="KOBO-001", revenue="500.00", fuel="780.00", currency="EUR")
    assert texts(k) == {"revenue": "Revenue: the accounts are in EUR, but the records are in USD.",
                        "fuel_bought": "Fuel bought (invoices): the accounts are in EUR, but the records are in USD."}
    assert k.text == "October 2026 (KOBO-001) cannot be compared with the management accounts yet."


# ---------------------------------------------------------------- R2: §6.2's cases


def test_r2_words_t1_t2_t4_t5_t6() -> None:
    w = two_sites_world()
    load(w, "A", "B")
    record(w, S1_AT, site=None, revenue="755.00", fuel="505.00")
    t1 = only(w)
    assert texts(t1) == {
        "revenue": "Revenue (Recorded, Emulated and Declared): the accounts say $755.00 and the records say $750.00, "
                   "$5.00 less, within the $7.55 allowed (1%).",
        "fuel_bought": "Fuel bought (invoices) (Recorded, Emulated and Declared): the accounts say $505.00 and the records say "
                     "$500.00, $5.00 less, within the $5.05 allowed (1%)."}
    for code in ("KOBO-001", "MTO-001"):
        st = standing(w, code)
        assert st.text == ("Reconciled: revenue and fuel bought for October 2026 (the organisation) match the management accounts within 1% "
                           "(Declared).")
        assert st.details == ()
    load(w, "C")  # T2
    assert texts(only(w))["fuel_bought"] == T2_FUEL
    for code in ("KOBO-001", "MTO-001"):
        st = standing(w, code)
        assert st.text == ("Not yet reconciled: October 2026 (the organisation) does not match the management "
                           "accounts within 1% (Declared).")
        assert st.details == (T2_FUEL,)  # D-3A7.13's failing headings, one sentence each (packet D1)
    record(w, S2_AT, site=None, revenue="755.00", fuel="510.00")  # T4
    assert texts(only(w))["fuel_bought"] == ("Fuel bought (invoices) (Recorded, Emulated and Declared): the accounts say $510.00 and "
                                           "the records say $512.50, $2.50 more, within the $5.10 allowed (1%).")
    assert standing(w, "KOBO-001").text == ("Reconciled: revenue and fuel bought for October 2026 (the organisation) match the management "
                                            "accounts within 1% (Declared).")
    s3 = record(w, S3_AT, site="MTO-001", revenue="250.00", fuel="0.00")  # T5
    assert texts(s3) == {
        "revenue": "Revenue (Recorded, Emulated and Declared): the accounts say $250.00 and the records say $250.00, "
                   "the same, within the $2.50 allowed (1%).",
        "fuel_bought": "Fuel bought (invoices) (Recorded): the accounts say $0.00 and no fuel invoices are recorded."}
    assert s3.text == "Revenue and fuel bought for October 2026 (MTO-001) match the management accounts within 1% (Declared)."
    s4 = record(w, S4_AT, site="MTO-001", revenue="250.00", fuel="40.00")  # T6
    assert texts(s4)["fuel_bought"] == T6_FUEL
    assert s4.text == "October 2026 (MTO-001) cannot be compared with the management accounts yet."
    st = standing(w, "MTO-001")
    assert st.text == "Not yet reconciled: October 2026 (MTO-001) cannot be compared with the management accounts yet."
    assert st.details == (T6_FUEL,)



def test_r2_words_t3(tmp_path) -> None:
    w = t2_world(tmp_path)
    owner_file(tmp_path, "Tolerance for lakeside-power: 2% of revenue and of fuel cost.\n")
    w["clock"].now = T3_SET_AT
    w["recon"].set_tolerance(w["tid"], "0.02", OWNER_REF)
    w["clock"].now = READ_AT
    assert texts(only(w))["fuel_bought"] == ("Fuel bought (invoices) (Recorded, Emulated and Declared): the accounts say $505.00 and "
                                           "the records say $512.50, $7.50 more, within the $10.10 allowed (2%).")
    assert standing(w, "KOBO-001").text == ("Reconciled: revenue and fuel bought for October 2026 (the organisation) match the management "
                                            "accounts within 2% (Declared).")


def test_r2_words_t7_t8_t10() -> None:
    w = two_sites_world()
    load(w, "A", "B")
    assert standing(w, "KOBO-001").text == ("Not yet reconciled: no closed month has been compared with the "
                                            "management accounts.")
    none_matched = ("Not yet reconciled: no month's recorded revenue and fuel bought match the management accounts "
                    "within 1% (Declared) yet.")
    assert standing(t2_world(), "KOBO-001", "2026-09").text == none_matched  # T8
    record(w, S3_AT, site="MTO-001", revenue="250.00", fuel="0.00")  # T10
    for code in ("KOBO-001", "MTO-001"):
        assert (standing(w, code).text, standing(w, code).details) == (none_matched, ())


# ---------------------------------------------------------------- R3: the boundary (pure)


def words(accounts: str, recorded: str, origins=(FIN,)) -> str:
    state = _compare(D(accounts), D(recorded), D("0.01"))
    return render(heading_words("revenue", state, None, D(accounts), D(recorded), D("0.01"), "USD", "2026-10", (),
                                origins=origins))


def test_mixed_origin_lines_read_the_weakest_origin() -> None:
    """Review L1: used lines of financial and emulated origin read "(Recorded, Emulated and Declared)" (D-4B.2: the
    weakest)."""
    assert words("500.00", "505.50", origins=(FIN, EMU)).startswith("Revenue (Recorded, Emulated and Declared):")
    assert words("500.00", "505.50", origins=(EMU, FIN)).startswith("Revenue (Recorded, Emulated and Declared):")


def test_mixed_origin_lines_read_the_weakest_origin() -> None:
    """Review L1: used lines of financial and emulated origin read "(Recorded, Emulated and Declared)" (D-4B.2: the
    weakest)."""
    assert words("500.00", "505.50", origins=(FIN, EMU)).startswith("Revenue (Recorded, Emulated and Declared):")
    assert words("500.00", "505.50", origins=(EMU, FIN)).startswith("Revenue (Recorded, Emulated and Declared):")


@pytest.mark.parametrize("accounts, recorded, english", [
    ("0.00", "3.00", "Revenue (Recorded and Declared): the accounts say $0.00 and the records say $3.00, $3.00 more, "
                     "beyond the $0.00 allowed (1%)."),  # no share for a zero figure (V12)
    ("501.50", "506.52", "Revenue (Recorded and Declared): the accounts say $501.50 and the records say $506.52, "
                         "$5.02 more (1.01%), beyond the $5.01 allowed (1%)."),  # V15: the allowed amount rounds down
    ("500.00", "500.004", "Revenue (Recorded and Declared): the accounts say $500.00 and the records say $500.00, "
                          "less than $0.01 more, within the $5.00 allowed (1%)."),
    ("505.00", "510.05", "Revenue (Recorded and Declared): the accounts say $505.00 and the records say $510.05, "
                         "$5.05 more, within the $5.05 allowed (1%)."),
    ("505.00", "499.94", "Revenue (Recorded and Declared): the accounts say $505.00 and the records say $499.94, "
                         "$5.06 less (1.01%), beyond the $5.05 allowed (1%)."),
    ("1234567.89", "1234567.89", "Revenue (Recorded and Declared): the accounts say $1,234,567.89 and the records say "
                                 "$1,234,567.89, the same, within the $12,345.68 allowed (1%)."),
])
def test_r3_boundary_words(accounts, recorded, english) -> None:
    assert words(accounts, recorded) == english


def test_r3_an_unnamed_origin_reads_estimated() -> None:
    assert words("500.00", "500.00", origins=()).startswith("Revenue (Recorded, Estimated and Declared): ")


# ---------------------------------------------------------------- R4: refusal sentences


@pytest.mark.parametrize("kw, english", [
    (dict(actor=ANA), "Only the finance lead records the management accounts."),
    (dict(period="2026-13"), "Write the month as YYYY-MM, like 2026-10."),
    (dict(site="NOPE-001"), "This Site is not this organisation's: NOPE-001."),
    (dict(currency="usd"), "Write the currency as its code in capital letters, like USD."),
    (dict(revenue="755"), "Write the revenue as digits with a decimal point and no separators, like 1200.00."),
    (dict(fuel="05.00"), "Write the fuel bought as digits with a decimal point and no separators, like 1200.00."),
    (dict(source_ref=""), "Say where the figures come from, in at most 200 characters."),
    (dict(period="2026-11"), "November 2026 is not closed yet: record a closed month."),  # T9
    (dict(site="FRZ-001"), "Only mini-grid Sites are compared with the management accounts for now: FRZ-001."),
])
def test_r4_refusal_words(kw, english) -> None:
    w = two_sites_world()
    load(w, "A", "B")
    args = dict(site=None, revenue="755.00", fuel="505.00")
    args.update(kw)
    with pytest.raises(ReconRefused) as got:
        record(w, READ_AT, **args)
    assert render(refusal_words(got.value)) == english


def test_r4_an_organisation_with_no_mini_grid_site_words() -> None:
    store = ReconMemoryStore()
    tid = store.add_tenant("harvest-cold")
    w = _services(store, {"COLD-THIKA": store.add_site(tid, "COLD-THIKA", "COLDCHAIN")}, tid, None)
    with pytest.raises(ReconRefused) as got:
        record(w, READ_AT, site=None, revenue="0.00", fuel="0.00")
    assert render(refusal_words(got.value)) == ("This organisation has no mini-grid Site to compare with the "
                                                "management accounts.")


def test_r4_tolerance_refusals_are_codes_only() -> None:
    """`set-tolerance` refusals print their code (exit 2, spec §5); they have no sentence."""
    with pytest.raises(KeyError):
        refusal_words(ReconRefused("TOLERANCE_INVALID"))


# ---------------------------------------------------------------- R6: money_word through the evidence format


def test_r6_money_word() -> None:
    w = t2_world()
    unmatched = standing(w, "KOBO-001")
    w2 = two_sites_world()
    load(w2, "A", "B")
    record(w2, S1_AT, site=None, revenue="755.00", fuel="505.00")
    matched = standing(w2, "KOBO-001")
    assert (matched.reconciled, unmatched.reconciled) == (True, False)

    def fig(origin: str) -> Money:
        return Money(D("512.50"), "USD", Evidence("RECORDED", origin))

    assert money_word(fig(FIN), matched) == "Recorded"
    assert money_word(fig(FIN), unmatched) == "Recorded, not yet reconciled"
    assert money_word(fig(EMU), matched) == "Emulated"
    assert money_word(fig(EMU), unmatched) == "Emulated, not yet reconciled"


# ---------------------------------------------------------------- plants: the statements carry the rules


def planted(change) -> object:
    stmts = copy.deepcopy(module.STATEMENTS)
    change(stmts)
    return catalogue._build({"en": [stmts]}, {"en": VOCABULARY})


def c1() -> tuple[dict, str]:
    """SC-1's C1 (501.50 against 506.52), whose allowed amount 5.015 rounds down and whose share is 1.01%."""
    (case,) = [c for c in worked.CASES if c.key == "reconciliation.heading" and "$501.50" in c.english]
    return case.facts, case.english


def test_plant_v15_allowed_half_even_in_a_not_matched_sentence_changes_the_words() -> None:
    from assetops_backend.i18n import message

    facts, english = c1()

    def v15(s):
        s["reconciliation.heading"]["variants"][1]["options"]["allowed"] = {"round": "half_even"}
    with catalogue._use(planted(v15)):
        got = render(message("reconciliation.heading", **facts))
    assert got != english and "$5.02 allowed" in got


def test_plant_v12_a_share_shown_for_a_zero_figure_cannot_render() -> None:
    """V12: the service hands an `Absent("ACCOUNTS_ZERO")` share for a zero figure; once the statement no longer
    declares that absence, the sentence cannot render (no share is ever invented)."""
    from assetops_backend.i18n import StatementError, message
    (case,) = [c for c in worked.CASES if c.key == "reconciliation.heading" and "KES 0.00 allowed" in c.english]

    def v12(s):
        s["reconciliation.share"]["slots"]["share"].pop("absent")
    with catalogue._use(planted(v12)), pytest.raises(StatementError):
        render(message("reconciliation.heading", **case.facts))


def test_plant_a_number_word_in_a_template_is_refused_at_load() -> None:
    def two(s):
        s["reconciliation.refused"]["variants"][6]["text"] = ("Write the {heading} with two decimals and no "
                                                              "separators, like {amount_example}.")
    with pytest.raises(catalogue.CatalogueError) as got:
        planted(two)
    assert got.value.code == "LITERAL_NUMBER_WORD"


def test_plant_v19_the_failing_headings_leave_the_standing() -> None:
    """V19 is a service plant (leave `details` empty); R2's `details == (T2_FUEL,)` fails on it. Shown here: the
    standing sentence alone never names the heading that did not match."""
    w = t2_world()
    st = standing(w, "KOBO-001")
    assert "Fuel bought" not in st.text and st.details and "Fuel bought" in st.details[0]
