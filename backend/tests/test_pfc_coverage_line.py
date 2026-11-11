"""PF-C / PF-W (architect proposal 2026-11-10 §4 PF-C1/PF-C2, §10; D-E5.46): the Portfolio's one coverage line, the
cards' exception-only days lines, and the readings term family that replaces "checked" for data."""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))

from assetops_backend.chain import vocabulary as v  # noqa: E402
from assetops_backend.site_outcomes.read import portfolio_cards, portfolio_coverage  # noqa: E402

FULL = {"complete": 7, "partial": 0, "low": 0, "no_data": 0, "pending": 0, "expected": 7}
PART = {"complete": 4, "partial": 1, "low": 1, "no_data": 1, "pending": 0, "expected": 7}
STUDY = {"complete": 3, "partial": 2, "low": 0, "no_data": 0, "pending": 0, "expected": 5}


class _Counted:
    def __init__(self, days: dict) -> None:
        self.days = days
        self.claims = {}

    def claims_json(self) -> dict:
        return {}


def _site(code: str, name: str, earnings=None) -> dict:
    return {"site_code": code, "site_name": name, "earnings": earnings, "rows": []}


SITES = [_site("K", "Kobo"), _site("G", "GreenHarvest")]


# ---------------------------------------------------------------- D-E5.46 term family (exact strings)

def test_gap_reason_words_are_d_e5_46_verbatim() -> None:
    assert v.GAP_REASON_WORDS == {
        "NO_READINGS": ("No readings received for this day", "no readings"),
        "READINGS_CONFLICT": ("Readings for this day conflict (duplicate or overlapping reports), so it can't be "
                              "analysed", "conflicting readings"),
        "NOT_ENOUGH_READINGS": ("Not enough readings received to analyse this day", "not enough readings"),
        "NOT_ANALYSED": ("Not analysed yet", "not analysed yet"),
    }
    assert v.STILL_PROCESSING == "Still processing"
    assert (v.incomplete_sites(1), v.incomplete_sites(3)) == ("1 site with incomplete days",
                                                              "3 sites with incomplete days")


def test_readings_terms_cover_the_family_and_never_say_checked() -> None:
    terms = [t for _, t, _ in v.READINGS_TERMS]
    assert terms == ["Complete readings", "Partial readings", "Too few readings", "No readings received",
                     "Not enough readings", "Conflicting readings", "Still processing", "Not analysed yet"]
    for _, term, definition in v.READINGS_TERMS:
        assert "check" not in (term + definition).lower(), term
    # "not analysed yet" is system work only (D-E5.46): its definition says the system will do it
    assert dict((t, d) for _, t, d in v.READINGS_TERMS)["Not analysed yet"].startswith("AssetOps has not analysed")


def test_frontend_words_carry_the_same_gap_reason_and_term_strings() -> None:
    """One shared vocabulary: the browser's words file holds the backend strings byte for byte, so GAP-REASONS only
    wires the reasons (it adds no words)."""
    root = Path(__file__).resolve().parents[2] / "frontend" / "src"
    words = (root / "estate" / "portfolioWords.ts").read_text(encoding="utf-8")
    # The gap-reason table is ONE table, `ui/productWords.ts` DAY_GAP (PB-4); portfolioWords imports it, never copies it.
    gap_table = (root / "ui" / "productWords.ts").read_text(encoding="utf-8")
    assert "dayGapWords" in words and '"no readings"' not in words
    for full, short in v.GAP_REASON_WORDS.values():
        assert f'"{full}"' in gap_table and f'"{short}"' in gap_table, (full, short)
    for _, term, definition in v.READINGS_TERMS:
        assert f'"{term}"' in words and f'"{definition}"' in words, term
    assert '"site with incomplete days"' in words and '"sites with incomplete days"' in words


_DATA_TEMPLATES = {**v.NODE_TEXT, **v.WHY_TEXT, **v.CARD_TEXT,
                   **{f"{k}.{i}": t for k, forms in v.COUNT_TEXT.items() for i, t in enumerate(forms)},
                   "MG1_SO_FAR": v.MG1_SO_FAR, "MG1_TOO_EARLY": v.MG1_TOO_EARLY, "MG1_MISSED": v.MG1_MISSED,
                   "MG1_NO_DAY": v.MG1_NO_DAY}


@pytest.mark.parametrize("key", sorted(_DATA_TEMPLATES))
def test_no_data_template_says_checked(key: str) -> None:
    """Owner item 3: "checked" never describes data (proposal §10.1 B rows of `chain/vocabulary.py`)."""
    assert not re.search(r"\b(un)?checked\b|\bchecking\b", _DATA_TEMPLATES[key], re.I), _DATA_TEMPLATES[key]


def test_days_line_reads_what_arrived() -> None:
    assert v.days_line(FULL) == "Complete readings on 7 of 7 days"
    assert v.days_line(PART) == ("Complete readings on 4 of 7 days · 1 with partial readings · "
                                 "1 with too few readings, not counted")
    one = {**FULL, "complete": 1, "expected": 1}
    assert v.days_line(one) == "Complete readings on 1 of 1 day"
    assert v.money_claim("estimated_income", {"amount": "2", "currency": "USD"}, one).text \
        == "2.00 USD over 1 of 1 day with complete readings · not billed or collected"
    zero = {"value": 0, "basis": "CHECKED_DAYS", "text": "None found on days with complete readings"}
    assert v.count_card_value(zero) == {"text": "None found", "small": "on days with complete readings"}


# ---------------------------------------------------------------- PF-C1: one coverage line

def test_coverage_line_names_each_site_in_reading_words() -> None:
    line = portfolio_coverage(SITES, _Counted({"K": PART, "G": FULL}))
    assert line["state"] == "INCOMPLETE"
    assert line["lead"] == "Some days have incomplete readings"
    assert line["rule"] == "Figures on this page count days with complete readings."
    assert line["sites"] == [
        {"site_code": "K", "site_name": "Kobo", "complete": False,
         "text": "Kobo: complete readings on 4 of 7 days · 1 with partial readings · 1 with too few readings, "
                 "not counted · 1 with no readings received"},
        {"site_code": "G", "site_name": "GreenHarvest", "complete": True,
         "text": "GreenHarvest: complete readings on 7 of 7 days"}]
    # the Why? days of a card without its own line: every Site's days line, built once
    # (PF-C review Low: the same parts the line shows, including the days with no readings received)
    assert line["days_text"] == ("Kobo: Complete readings on 4 of 7 days · 1 with partial readings · 1 with too few "
                                 "readings, not counted · 1 with no readings received · "
                                 "GreenHarvest: Complete readings on 7 of 7 days")
    for row in line["sites"]:  # parity: each Site's days_text part is its coverage text, first letter capitalised
        text = row["text"]
        assert text[len(row["site_name"]) + 2:].lower() in line["days_text"].lower(), row


def test_coverage_line_collapses_when_every_day_is_complete_and_says_not_known_without_counts() -> None:
    full = portfolio_coverage(SITES, _Counted({"K": FULL, "G": FULL}))
    assert (full["state"], full["lead"]) == ("COMPLETE", "Complete readings on every day")
    unknown = portfolio_coverage(SITES, None)
    assert (unknown["state"], unknown["lead"], unknown["sites"], unknown["days_text"]) == (
        "NOT_KNOWN", "Day readings are not known yet", [], None)
    one_missing = portfolio_coverage(SITES, _Counted({"K": FULL}))
    assert one_missing["state"] == "INCOMPLETE"
    assert one_missing["sites"][1]["text"] == "GreenHarvest: readings not known yet"


# ---------------------------------------------------------------- PF-C2: exception-only card days lines

def _income(days: dict) -> dict:
    return {"key": "money.estimated_income", "value": {"amount": "7.50", "currency": "USD"}, "basis": "COMPLETE",
            "days": days, "text": "x"}


def test_protect_and_assure_drop_the_shared_days_line() -> None:
    cards = portfolio_cards(SITES, _Counted({"K": PART, "G": FULL}), v.estate_income([]), [], None, 0)
    assert cards["PROTECT_ASSET"]["days_line"] is None and cards["ASSURE_PERFORMANCE"]["days_line"] is None


def test_grow_keeps_its_days_line_only_when_its_days_differ() -> None:
    counted = _Counted({"K": FULL, "G": FULL})
    both = [_site("K", "Kobo", {"estimated_income": _income(FULL)}),
            _site("G", "GreenHarvest", {"estimated_income": _income(FULL)})]
    total = v.estate_income([("Kobo", _income(FULL)), ("GreenHarvest", _income(FULL))])
    assert portfolio_cards(both, counted, total, [], None, 0)["GROW_REVENUE"]["days_line"] is None
    # PF-C review Low: with only Kobo earning, the Why? days name Kobo alone, never a Site the figure does not use
    one = [_site("K", "Kobo", {"estimated_income": _income(FULL)}), _site("G", "GreenHarvest")]
    card = portfolio_cards(one, counted, v.estate_income([("Kobo", _income(FULL))]), [], None, 0)["GROW_REVENUE"]
    assert card["days_line"] == "Kobo: Complete readings on 7 of 7 days"
    study = [_site("K", "Kobo", {"estimated_income": _income(STUDY)}), _site("G", "GreenHarvest")]
    card = portfolio_cards(study, counted, v.estate_income([("Kobo", _income(STUDY))]), [], None, 0)["GROW_REVENUE"]
    assert card["days_line"] == "Kobo: Complete readings on 3 of 5 days · 2 with partial readings"


def test_the_summary_carries_one_coverage_line_and_why_falls_back_to_it() -> None:
    import test_ch6b_estate_chain as EC

    _, body, _, days = EC._summary(EC.ManyPort())
    line = body["coverage_line"]
    assert line["state"] == "INCOMPLETE"   # Kobo 6 of 7 (1 day without readings), cold 7 of 7, EV 1 of 1
    by = {s["site_code"]: s for s in line["sites"]}
    assert by["KOBO-001"]["complete"] is False and "1 with no readings received" in by["KOBO-001"]["text"]
    assert by["COLD-LAB-001"]["complete"] is True
    assert body["cards"]["PROTECT_ASSET"]["days_line"] is None
