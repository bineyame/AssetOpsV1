"""6h (`specs/6h-named-option-levers/spec.md` §5.4, §10.2 test 7): every lever's words in `decision_lever.*`.

Every lever, option, record and study selector the catalogue names has its variant; every template passes SC-1's
`check_literal` (no digit, symbol or number word) and the banned vocabulary scan, and names no system id."""
from __future__ import annotations

import re

from assetops_backend.control_vocabulary import banned_tokens_in
from assetops_backend.i18n.catalogue import check_literal
from assetops_backend.i18n.statements.en.decision_lever import STATEMENTS
from assetops_backend.structure.levers import LEVERS, NO_ACTION_WORDS

GENERATOR_LABELS = ["NO_ACTION", "STOP", "RESERVE_DOWN", "RESERVE_UP", "STOP_RESERVE_DOWN", "STOP_RESERVE_UP"]


def _selector(name: str) -> str:
    return name.upper().replace("-", "_")


def _selected(key: str) -> list[str]:
    st = STATEMENTS[f"decision_lever.{key}"]
    return [v["when"]["is"][1] for v in st["variants"]]


def test_7_every_selector_the_catalogue_names_has_its_variant() -> None:
    levers = [_selector(lid) for lid in LEVERS]
    assert _selected("title") == levers and _selected("question") == levers
    assert _selected("no_action") == list(NO_ACTION_WORDS)
    assert {lever.no_action_words for lever in LEVERS.values()} <= set(NO_ACTION_WORDS)
    options = list(dict.fromkeys(_selector(o.key) for lever in LEVERS.values() for o in lever.options))
    assert _selected("option_label") == GENERATOR_LABELS + options
    records = [f"{_selector(lid)}__{_selector(leaf)}" for lid, lever in LEVERS.items()
               for leaf, src in sorted(lever.change_sources.items()) if src.kind == "RECORD"]
    assert sorted(_selected("record")) == sorted(records) and len(records) == 12
    studies = [_selector(lid) for lid, lever in LEVERS.items() if lever.generator == "STATED_OPTIONS"
               and any(src.kind == "STUDY" for src in lever.change_sources.values())]
    assert _selected("study") == studies == ["CHARGING_SCHEDULE"]


def test_7_each_question_is_built_from_its_title() -> None:
    titles = {v["id"]: v["text"] for v in STATEMENTS["decision_lever.title"]["variants"]}
    for v in STATEMENTS["decision_lever.question"]["variants"]:
        assert v["text"] == f"What should we do about the {titles[v['id']]}?"


def test_7_every_template_is_a_clean_literal() -> None:
    for key, st in STATEMENTS.items():
        assert key.startswith("decision_lever.") and st["exhaustive"]
        for v in st["variants"]:
            literal = re.sub(r"\{[a-z_]+\}", "", v["text"])
            check_literal(literal, "en", key, v["id"])
            assert banned_tokens_in(v["text"]) == [], (key, v["id"])
            assert not re.search(r"[A-Z]{2,}|[a-z]+_[a-z]+|%|\$", literal), (key, v["id"])
