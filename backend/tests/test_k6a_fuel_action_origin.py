"""DIESEL-K6a L0 (build sheet DIESEL-1 §9m.3, ruling DIESEL-1-R3m): the fuel Finding as a domain-Action origin.

No database: the closed creation body, the closed domain tables, `create_action`'s fuel branch against a fake
transaction (the fuel path never reaches `selected_pin`), the refused intent, and the client literals against
guard V and the H4 words. Each test names the mutation that must make it fail.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from uuid import UUID, uuid4

import pytest

from assetops_backend.work import domain_action as d
from assetops_backend.work.domain_intent import DomainIntentService

UTC = timezone.utc
T, S = uuid4(), uuid4()
NOW = datetime(2026, 11, 8, 9, tzinfo=UTC)
PRINCIPAL = "service:story"
ACTOR = {"kind": "SERVICE", "id": PRINCIPAL, "attestation": "service=story;job=k6a;rule=fuel-seal-dip-sensor-power@1"}
FID, RID = str(uuid4()), str(uuid4())


def _body(**over) -> dict:
    base = {"domain": "FUEL_BALANCE", "origin_finding_id": FID, "origin_finding_revision_id": RID,
            "title": "Seal the tank cap and sign the dip log", "owner_label": None, "due_at": None,
            "raised_at": "2026-11-08T08:00:00Z", "actor": ACTOR, "idempotency_key": "kisiwa-fuel-action-0001"}
    return {**base, **over}


# --- 1. the closed creation body ----------------------------------------------------------------------------------

def test_fuel_body_takes_the_finding_pair_only():
    """Must fail if `FUEL_SPEC.origin` is `ORIGIN_OPPORTUNITY`."""
    got = d.action_body(_body())
    assert got["domain"] == "FUEL_BALANCE" and got["origin_finding_id"] == FID
    assert got["origin_finding_revision_id"] == RID and "origin_opportunity_id" not in got
    opp = {"origin_opportunity_id": str(uuid4()), "origin_opportunity_revision_id": str(uuid4())}
    only_opp = {k: v for k, v in _body(**opp).items() if not k.startswith("origin_finding")}
    for bad in (only_opp, _body(**opp)):
        with pytest.raises(d.DomainIntentRefused) as e:
            d.action_body(bad)
        assert (e.value.status, e.value.code) == (422, "DOMAIN_INTENT_INVALID")
        assert e.value.message == d.FUEL_MESSAGES["DOMAIN_INTENT_INVALID"]


# --- 2. the closed domain tables ----------------------------------------------------------------------------------

def test_fuel_is_an_action_domain_but_never_intent_capable():
    """Must fail if `FUEL_SPEC` is added to `DOMAINS` (that would make an intent possible)."""
    assert set(d.ACTION_DOMAINS) == {"COLDCHAIN", "EV_CHARGING", "MINI", "FUEL_BALANCE"}
    assert d.spec_of("FUEL_BALANCE") is d.FUEL_SPEC
    assert {k: v.finding_domain for k, v in d.DOMAINS.items()} == {"COLDCHAIN": "cold_chain",
                                                                   "EV_CHARGING": "ev_charging"}
    assert dict(d.BY_FINDING_DOMAIN) == {"cold_chain": "COLDCHAIN", "ev_charging": "EV_CHARGING"}
    assert d.FUEL_SPEC.origin == d.ORIGIN_FINDING and d.FUEL_SPEC.site_type == "MINIGRID"
    assert d.FUEL_SPEC.criteria == () and d.FUEL_SPEC.basis_keys == () and d.FUEL_SPEC.finding_domain == "fuel_balance"


# --- 3. create_action's fuel branch -------------------------------------------------------------------------------

class _Tx:
    def __init__(self, *, domain: str = "fuel_balance", selected: bool = True, site_type: str = "MINIGRID") -> None:
        self.domain, self.selected, self.type = domain, selected, site_type
        self.inserted: list[dict] = []
        self.selected_calls: list[tuple[str, str]] = []

    def lock(self, command: str, key: str) -> None:
        pass

    def action_by_key(self, key: str):
        return None

    def db_now(self) -> datetime:
        return NOW

    def site_type(self) -> str:
        return self.type

    def finding_revision(self, finding_id: str, revision_id: str):
        return {"id": revision_id, "finding_id": finding_id, "domain": self.domain, "analytic_id": "fuel-balance-1"}

    def fuel_finding_selected(self, finding_id: str, revision_id: str) -> bool:
        self.selected_calls.append((finding_id, revision_id))
        return self.selected

    def selected_pin(self, revision):
        raise AssertionError("the fuel path must never reach selected_pin")

    def next_action_no(self) -> int:
        return 42

    def insert_action(self, row: dict) -> None:
        self.inserted.append(row)


class _Store:
    def __init__(self, tx: _Tx) -> None:
        self.tx = tx

    def transaction(self, tenant_id: UUID, site_id: UUID, site_code: str, work):
        return work(self.tx)


def _create(tx: _Tx):
    return DomainIntentService(_Store(tx)).create_action(T, S, "KISIWA-001", _body(), PRINCIPAL)


@pytest.mark.parametrize("tx", [_Tx(domain="mini_grid"), _Tx(selected=False), _Tx(site_type="COLDCHAIN")],
                         ids=["mini_grid_revision", "not_selected", "coldchain_site"])
def test_create_refuses_a_link_that_is_not_the_selected_fuel_finding(tx: _Tx):
    with pytest.raises(d.DomainIntentRefused) as e:
        _create(tx)
    assert (e.value.status, e.value.code) == (422, "DOMAIN_INTENT_LINK_INVALID")
    assert e.value.message == d.FUEL_MESSAGES["DOMAIN_INTENT_LINK_INVALID"]
    assert tx.inserted == []


def test_create_writes_a_fuel_action_with_the_finding_pair_without_a_pin():
    """Must fail if the fuel branch falls through to `selected_pin` (the fake raises)."""
    tx = _Tx()
    status, body = _create(tx)
    assert status == 201 and body["action_code"] == "ACT-000042" and body["schema_version"] == d.SCHEMA_ACTION
    (row,) = tx.inserted
    assert row["domain"] == "FUEL_BALANCE"
    assert (row["origin_finding_id"], row["origin_finding_revision_id"]) == (FID, RID)
    assert "origin_opportunity_id" not in row
    assert tx.selected_calls == [(FID, RID)]


# --- 4. a fuel Action declares no intent --------------------------------------------------------------------------

class _IntentTx(_Tx):
    def action(self, action_id: str):
        return {"id": action_id, "domain": "FUEL_BALANCE", "origin_finding_id": FID,
                "origin_finding_revision_id": RID, "raised_at": NOW}


def test_post_intent_on_a_fuel_action_is_refused_with_the_fuel_literal():
    body = {"supersedes_id": None, "declared_at": "2026-11-08T08:30:00Z", "criteria": [],
            "basis": {"finding_revision_id": RID, "work_case_id": None, "work_record_id": None,
                      "accepted_evidence_ids": []},
            "actor": ACTOR, "idempotency_key": "kisiwa-fuel-intent-0001"}
    with pytest.raises(d.DomainIntentRefused) as e:
        DomainIntentService(_Store(_IntentTx())).post_intent(T, S, "KISIWA-001", str(uuid4()), body, PRINCIPAL)
    assert (e.value.status, e.value.code) == (422, "DOMAIN_INTENT_INVALID")
    assert e.value.message == d.FUEL_MESSAGES["DOMAIN_INTENT_INVALID"]


# --- 5. client literals: guard V and H4 ---------------------------------------------------------------------------

H4 = re.compile(r"\b(theft|stolen|stole|siphon\w*|pilfer\w*)\b", re.IGNORECASE)


def test_fuel_literals_pass_guard_v_and_h4():
    import test_out_b2_vocabulary as v  # guard V's own pattern loader (frontend productVocabulary.json)

    patterns = v._patterns()
    copy = [*d.FUEL_MESSAGES.values(), d.FUEL_SPEC.summary]
    assert len(copy) == 6 and set(d.FUEL_MESSAGES) == set(d.STATUS)
    assert [(text, name) for text in copy for name, p in patterns if p.search(text)] == []
    assert [text for text in copy if H4.search(text)] == []
    # not vacuous: both scans catch a planted word
    assert any(p.search("The fuel draft is loaded") for _, p in patterns)
    assert H4.search("Fuel was siphoned")
