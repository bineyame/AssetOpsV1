"""OUT-D U3 (pure): declaration validation, payload digest, the demo file and the CLI over a fake store."""
from __future__ import annotations

import json
from dataclasses import replace
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

import pytest

from assetops_backend import declare_objective
from assetops_backend.objectives.model import (
    SYSTEM_DECLARER, Declaration, ObjectiveRefused, payload_sha256, target_string, validate)
from assetops_backend.outcomes.objectives import MEASURES

DEMO = Path(__file__).resolve().parents[1] / "conversions" / "demo-objectives.json"


def decl(**over) -> Declaration:
    base = Declaration("KOBO-001", "MG-2", "avoidable_generator_minutes", Decimal("0"), None, "DECLARED",
                       "Declared for the demonstration; not a customer target", None, "out-d-kobo-001-mg-2-v1")
    return replace(base, **over)


def refused(d: Declaration) -> ObjectiveRefused:
    with pytest.raises(ObjectiveRefused) as caught:
        validate(d)
    assert caught.value.status == 422 and caught.value.code == "OBJECTIVE_INVALID"
    return caught.value


@pytest.mark.parametrize("over", [
    {"measure_key": "supply_cost_per_kwh"},
    {"measure_key": "productive_use_kwh"},                     # measure of MG-1, not MG-2
    {"target": Decimal("-1")},
    {"target": Decimal("NaN")},
    {"currency": "USD"},                                       # a leading measure carries no money
    {"outcome_key": "EV-2", "measure_key": "energy_cost_per_km", "currency": None},
    {"outcome_key": "EV-2", "measure_key": "energy_cost_per_km", "currency": "usd"},
    {"source": "GUESSED"},
    {"source_note": ""},
    {"idempotency_key": "short"},
])
def test_validate_refuses(over) -> None:
    refused(decl(**over))


def test_backup_start_failures_admits_only_zero() -> None:
    cc6 = decl(outcome_key="CC-6", measure_key="backup_start_failures")
    validate(cc6)
    assert "only a zero target" in refused(replace(cc6, target=Decimal("1"))).message


def test_every_other_measure_accepts_a_non_zero_target() -> None:
    others = [m for m in MEASURES.values() if not m.zero_only]
    assert len(others) == 5
    for m in others:
        validate(decl(outcome_key=m.outcome, measure_key=m.key, target=Decimal("5"),
                      currency="USD" if m.unit == "currency/km" else None))


def test_payload_digest_is_canonical_and_excludes_the_key() -> None:
    a = decl(outcome_key="EV-2", measure_key="energy_cost_per_km", target=Decimal("0.20"), currency="USD")
    assert payload_sha256(a) == payload_sha256(replace(a, target=Decimal("0.2"), idempotency_key="another-key"))
    assert payload_sha256(a) != payload_sha256(replace(a, target=Decimal("0.3")))
    assert payload_sha256(a) != payload_sha256(replace(a, expected_prior=uuid4()))
    assert [target_string(Decimal(x)) for x in ("300", "0.20", "0", "0.000")] == ["300", "0.2", "0", "0"]


def test_principal_and_demo_file() -> None:
    assert SYSTEM_DECLARER.actor_id == "service:assetops-objective-declarer"
    assert SYSTEM_DECLARER.actor_kind == "SYSTEM" and "not a customer target" in SYSTEM_DECLARER.authorization_basis
    doc = json.loads(DEMO.read_text(encoding="utf-8"))
    rows = doc["objectives"]
    assert [(r["site_code"], r["outcome_key"], r["measure_key"], r["target"], r["currency"]) for r in rows] == [
        ("KOBO-001", "MG-2", "avoidable_generator_minutes", "0", None),
        ("KOBO-001", "MG-1", "productive_use_kwh", "300", None),
        ("KOBO-001", "MG-5", "unserved_critical_kwh", "0", None),
        ("COLD-LAB-001", "CC-6", "backup_start_failures", "0", None),
        ("EV-LAB-001", "EV-1", "interrupted_sessions", "0", None),
        ("EV-LAB-001", "EV-2", "energy_cost_per_km", "0.20", "USD")]
    assert not any(r["outcome_key"] == "CC-1" for r in rows)  # CC-1 reads the chamber range (U4)
    for r in rows:
        assert r["source"] == "DECLARED"
        assert r["source_note"] == "Declared for the demonstration; not a customer target"
        assert r["idempotency_key"] == f"out-d-{r['site_code'].lower()}-{r['outcome_key'].lower()}-v1"
        validate(Declaration(r["site_code"], r["outcome_key"], r["measure_key"], Decimal(r["target"]), r["currency"],
                             r["source"], r["source_note"], None, r["idempotency_key"]))


class FakeStore:
    def __init__(self, sites: set[str]) -> None:
        self.sites, self.calls, self.rows = sites, [], {}

    def tenant_id(self, slug):
        return "tenant"

    def site_id(self, tenant, code):
        return f"site-{code}" if code in self.sites else None

    def revision_id(self, tenant, site, key):
        return self.rows.get(key, {}).get("id")

    def declare(self, tenant, d, principal, channel):
        self.calls.append((d, principal, channel))
        if d.idempotency_key in self.rows:
            return self.rows[d.idempotency_key], False
        row = {"id": uuid4(), "outcome_key": d.outcome_key, "revision_no": 1, "measure_key": d.measure_key,
               "target": d.target, "recorded_at": datetime(2026, 10, 30, tzinfo=timezone.utc),
               "actor_id": principal.actor_id}
        self.rows[d.idempotency_key] = row
        return row, True


def lines(capsys) -> list[dict]:
    return [json.loads(x) for x in capsys.readouterr().out.splitlines()]


def test_fixture_skips_unimported_sites_and_is_idempotent(capsys) -> None:
    store = FakeStore({"KOBO-001"})
    assert declare_objective.main(["fixture", "--file", str(DEMO)], store=store) == 0
    out = lines(capsys)
    assert [o.get("inserted") for o in out if "skipped" not in o] == [True, True, True]
    assert [o["site_code"] for o in out if o.get("skipped") == "SITE_NOT_IMPORTED"] == [
        "COLD-LAB-001", "EV-LAB-001", "EV-LAB-001"]
    assert all(c[1] is SYSTEM_DECLARER and c[2] == "SYSTEM_FIXTURE" for c in store.calls)
    assert declare_objective.main(["fixture", "--file", str(DEMO), "--site", "kobo-001"], store=store) == 0
    assert [o["inserted"] for o in lines(capsys)] == [False, False, False]


def test_declare_command_and_refusal_exit_code(capsys) -> None:
    store = FakeStore({"KOBO-001"})
    argv = ["declare", "--site", "KOBO-001", "--outcome", "MG-2", "--measure", "avoidable_generator_minutes",
            "--target", "5", "--source-note", "Declared for the demonstration; not a customer target",
            "--expected-prior", "none", "--idempotency-key", "out-d-kobo-001-mg-2-v2"]
    assert declare_objective.main(argv, store=store) == 0
    (out,) = lines(capsys)
    assert out["target"] == "5" and out["inserted"] is True and store.calls[-1][2] == "SYSTEM_CLI"

    class Refusing(FakeStore):
        def declare(self, tenant, d, principal, channel):
            raise ObjectiveRefused(409, "OBJECTIVE_PRIOR_MISMATCH", "stale")

    assert declare_objective.main(argv, store=Refusing({"KOBO-001"})) == 3
    assert json.loads(capsys.readouterr().err)["refused"] == "OBJECTIVE_PRIOR_MISMATCH"
    assert declare_objective.main([*argv[:-2], "--idempotency-key", "x", "--expected-prior", "bad"],
                                  store=store) == 3
