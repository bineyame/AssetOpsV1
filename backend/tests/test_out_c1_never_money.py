"""OUT-C U1: no early warning ever carries money (build sheet OUT-C §0, §2 U1). `money_hits` is reused by the
Postgres board tests."""
from __future__ import annotations

import json
import re
from datetime import date, datetime, timedelta, timezone
from typing import Any

from assetops_backend.outcomes.catalogue import COLD, EV, MINI
from assetops_backend.outcomes.outcome_map import outcome_roles
from assetops_backend.outcomes.warnings import KINDS, PRICE_NEEDS, PlanCue, Visit, WarningFacts, evaluate

MONEY_KEYS = {"amount", "amount_low", "amount_high", "currency", "value", "price", "rate"}
MONEY_TEXT = re.compile(r"[$€£]|\b(USD|EUR|GBP|KES|ETB)\b|\d+(\.\d+)?\s*(per litre|/kWh|per kWh)")


def money_hits(body: Any) -> list[str]:
    """Every money key (nested, any depth) and every money-looking text in a JSON-able body."""
    hits: list[str] = []

    def walk(x: Any) -> None:
        if isinstance(x, dict):
            for k, v in x.items():
                if k in MONEY_KEYS:
                    hits.append("key:" + k)
                walk(v)
        elif isinstance(x, list):
            for v in x:
                walk(v)
    walk(body)
    text = json.dumps(body, ensure_ascii=False)
    hits += ["text:" + m.group(0) for m in MONEY_TEXT.finditer(text)]
    return hits


TO = datetime(2026, 10, 29, tzinfo=timezone.utc)


def every_rule() -> list[Any]:
    base = dict(site_code="S1", to=TO, visits_from=TO - timedelta(days=60), soon_until=TO + timedelta(days=14),
                window_days=(date(2026, 10, 28), date(2026, 10, 28)))
    keys = outcome_roles("FINDING:COLD_START_FAILURE", COLD)
    visits = tuple(Visit(f"c{i}", f"WR-{i}", "a1", "generator-1", "COMPLETED", TO - timedelta(days=i + 1),
                         (TO - timedelta(days=i + 1)).date(), ("f1",), f"/work/c{i}") for i in range(2))
    plans = (PlanCue("p1", "PM-1", "Coil cleaning", TO - timedelta(days=2), date(2026, 10, 27), "c1"),
             PlanCue("p2", "PM-2", "Coil cleaning", TO + timedelta(days=2), date(2026, 10, 31), "a1"))
    out = list(evaluate(WarningFacts(COLD, visits=visits, plans=plans,
                                     open_findings={"f1": (keys[0] + keys[1], "/f/f1")},
                                     fault_names={"f1": "automatic start failure"}, **base)))
    out += evaluate(WarningFacts(MINI, reserve=(2, 3), **base))
    out += evaluate(WarningFacts(EV, plans=plans, faults=(("c1", "1"),), connectors_out=(("c1", "1", "2 h", "1 min"),),
                                 peak=(76.0, 80.0, "76", "80"), **base))
    return out


def test_every_rule_fires_without_money() -> None:
    ws = every_rule()
    assert "fault_name" not in MONEY_KEYS
    assert [w.wire("X", "Y")["fault_name"] for w in ws if w.kind == "REPEATED_MAINTENANCE_NO_RESULT"] == [
        "automatic start failure"]  # the key walk covers the populated value
    assert {w.kind for w in ws} == set(KINDS)  # every rule's positive output is covered
    for w in ws:
        body = w.wire("X", "Y")
        assert money_hits(body) == [], (w.kind, money_hits(body))
        assert w.price_needs in PRICE_NEEDS.values()


def test_money_check_is_not_vacuous() -> None:
    body = every_rule()[0].wire("X", "Y")
    injected = dict(body, evidence_refs=[dict(body["evidence_refs"][0], amount=1)])
    assert money_hits(injected) == ["key:amount"]
    assert money_hits(dict(body, seen="Seen at $5")) == ["text:$"]
    assert money_hits(dict(body, seen="2.5 per kWh")) == ["text:2.5 per kWh"]
