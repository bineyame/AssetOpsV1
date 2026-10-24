"""W5-04a V1: the EV domain Action contract without a database - closed dispatch, EV criteria/basis parsing, the
readiness-28 neutral literals and refusal order, and the readiness-27/30 membership rules over a fake store.

`.agent/W5-04-build-spec.md` "Frozen contract" and "V1 selection, clock and schema", readiness rulings 7, 9, 11, 12,
27, 28 and 30, pre-flight 9-18. The fake transaction records every write so each refusal proves zero writes.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

import pytest

from assetops_backend.work import domain_action as d
from assetops_backend.work import model as m
from assetops_backend.work.domain_intent import DomainIntentService

T, S = UUID(int=1), UUID(int=2)
ACTOR = {"kind": "SERVICE", "id": "service:w401-fixture", "attestation": "service=w401-fixture;job=j;rule=r/1"}
PRINCIPAL = ACTOR["id"]
NOW = datetime(2026, 10, 24, 12, tzinfo=timezone.utc)
F, R, SES, SES2, E1, E2, E3 = (str(uuid4()) for _ in range(7))
EV_INVALID = "The EV Action declaration is incomplete or invalid."
EV_LINK = "The declared Finding or session is not selected at this site and cutoff."
COLD_INVALID = "The cold Action declaration is incomplete or invalid."
COLD_LINK = "The declared Finding or work record is not selected at this site and cutoff."


def iso(value: datetime) -> str:
    return value.strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def crit(spec=d.EV_CRITERIA) -> list[dict]:
    return [{"key": k, "label": label, "required_evidence": req} for k, label, req in spec]


def ev_basis(**over) -> dict:
    return {"finding_revision_id": R, "work_case_id": None, "work_record_id": None,
            "accepted_evidence_ids": [E1], "session_ids": [SES], **over}


def ev_intent(key="w504-model-intent-01", **over) -> dict:
    return {"supersedes_id": None, "declared_at": iso(NOW - timedelta(minutes=1)), "criteria": crit(),
            "basis": ev_basis(), "actor": dict(ACTOR), "idempotency_key": key, **over}


def action_body(domain="EV_CHARGING", **over) -> dict:
    return {"domain": domain, "origin_finding_id": F, "origin_finding_revision_id": R, "title": "Replace connector",
            "owner_label": None, "due_at": None, "raised_at": iso(NOW - timedelta(minutes=10)), "actor": dict(ACTOR),
            "idempotency_key": "w504-model-action-01", **over}


def refusal(call, *args) -> tuple[int, str, str]:
    with pytest.raises(d.DomainIntentRefused) as caught:
        call(*args)
    return caught.value.status, caught.value.code, caught.value.message


def selected_basis(**over) -> dict:
    """A `composition.selected_ev_basis` result selecting R (SUPPORTED, own session SES, cites E1 and E2)."""
    return {"state": "CURRENT", "window_start": NOW, "window_end": NOW, "assessment_revision_id": str(uuid4()),
            "finding": {"finding_id": F, "revision_id": R, "session_id": SES, "lifecycle": "SUPPORTED",
                        "evidence_ids": sorted([E1, E2])},
            "sessions": {SES: str(uuid4()), SES2: str(uuid4())},
            "accepted_evidence_ids": sorted([E1, E2, E3]), "selected_evidence_ids": sorted([E1, E2, E3]), **over}


# ---- the closed contract -------------------------------------------------------------------------------------------

def test_ev_contract_literals_and_closed_dispatch() -> None:
    ev = d.spec_of("EV_CHARGING")
    assert ev is not None and ev.finding_domain == "ev_charging" and len(ev.criteria) == 3
    assert ev.messages["DOMAIN_INTENT_INVALID"] == EV_INVALID and ev.messages["DOMAIN_INTENT_LINK_INVALID"] == EV_LINK
    assert ev.messages["DOMAIN_INTENT_BASIS_CHANGED"] == "The selected EV work basis changed; reload the Action."
    assert ev.initial_results == ("PENDING", "PENDING", "PENDING")
    assert ev.summary == "A complete witnessed session and no repeat fault"
    assert ev.basis_keys == ("finding_revision_id", "work_case_id", "work_record_id", "accepted_evidence_ids",
                             "session_ids")
    for unknown in ("MINIGRID", "ev_charging", "coldchain", None, 3):
        assert d.spec_of(unknown) is None
    assert (d.NEUTRAL_DOMAIN_INVALID, d.NEUTRAL_INTENT_INVALID, d.NEUTRAL_CASE_LINK_INVALID) == (
        "The Action domain is missing or unsupported.", "The Action declaration is incomplete or invalid.",
        "The Action case link is incomplete or invalid.")
    assert not hasattr(d, "NEUTRAL_LINK_INVALID")  # readiness 28: an unresolved Action is 404


def test_ev_action_body_and_neutral_domain() -> None:
    body = d.action_body(action_body())
    assert body["domain"] == "EV_CHARGING" and body["origin_finding_revision_id"] == R
    assert refusal(d.action_body, action_body(title="")) == (422, "DOMAIN_INTENT_INVALID", EV_INVALID)
    for bad in (action_body(domain="MINIGRID"), action_body(domain="ev_charging"), action_body(domain=None),
                {k: v for k, v in action_body().items() if k != "domain"}, [1]):
        assert refusal(d.action_body, bad) == (422, "DOMAIN_INTENT_INVALID", d.NEUTRAL_DOMAIN_INVALID)


def test_ev_criteria_and_basis_after_resolution() -> None:
    ev = d.DOMAINS["EV_CHARGING"]
    shape = d.intent_shape(ev_intent(basis=ev_basis(session_ids=[SES2.upper(), SES], accepted_evidence_ids=[E2, E1])))
    body = d.intent_for(ev, shape)
    assert [c["key"] for c in body["criteria"]] == ["WITNESSED_SESSION", "NO_FAULT_RECURRENCE", "NO_SERVICE_REDUCTION"]
    assert list(body["basis"]) == list(ev.basis_keys)  # exactly the closed five keys, no pin key
    assert body["basis"]["session_ids"] == sorted([SES, SES2]) and body["basis"]["accepted_evidence_ids"] == sorted(
        [E1, E2])
    swapped = crit()
    swapped[0], swapped[1] = swapped[1], swapped[0]
    for criteria in (crit()[:2], crit() + crit()[:1], swapped, crit(d.CRITERIA), []):
        assert refusal(d.intent_for, ev, d.intent_shape(ev_intent(criteria=criteria))) == (
            422, "DOMAIN_INTENT_INVALID", EV_INVALID)
    cold_basis = {k: v for k, v in ev_basis().items() if k != "session_ids"}
    for basis in (cold_basis, ev_basis(session_ids=[]), ev_basis(session_ids=[SES, SES]),
                  ev_basis(session_ids=["ev-SES-011"]), ev_basis(session_ids=SES)):
        assert refusal(d.intent_for, ev, d.intent_shape(ev_intent(basis=basis))) == (
            422, "DOMAIN_INTENT_INVALID", EV_INVALID)
    # The cold contract refuses an EV body with the cold literal (stored domain selects the literal).
    assert refusal(d.intent_for, d.DOMAINS["COLDCHAIN"], d.intent_shape(ev_intent())) == (
        422, "DOMAIN_INTENT_INVALID", COLD_INVALID)


def test_shared_shape_is_neutral_before_resolution() -> None:
    d.intent_shape(ev_intent(criteria=crit()[:2], basis={k: v for k, v in ev_basis().items() if k != "session_ids"}))
    d.intent_shape(ev_intent(criteria=crit(d.CRITERIA)))  # a cold body passes the shared shape too
    for bad in (ev_intent(declared_at="later"), ev_intent(supersedes_id="x"), ev_intent(extra=1),
                ev_intent(criteria={}), ev_intent(criteria=[{"key": "K", "label": "L"}]),
                ev_intent(criteria=[{"key": 1, "label": "L", "required_evidence": "E"}]),
                ev_intent(basis=ev_basis(pin={"known_at": iso(NOW)})), ev_intent(basis=ev_basis(work_record_id=E3)),
                ev_intent(basis=ev_basis(accepted_evidence_ids=[E1, E1])), ev_intent(idempotency_key="x"), "nope"):
        assert refusal(d.intent_shape, bad) == (422, "DOMAIN_INTENT_INVALID", d.NEUTRAL_INTENT_INVALID)
    link = {"case_id": E1, "case_revision_id": E2, "case_event_id": "x", "actor": dict(ACTOR),
            "idempotency_key": "w504-model-link-01"}
    assert refusal(d.case_link_body, link) == (422, "DOMAIN_INTENT_INVALID", d.NEUTRAL_CASE_LINK_INVALID)


def test_ev_membership_has_no_silent_intersection() -> None:
    ev = selected_basis()
    assert d.ev_selects_finding(ev, R) and d.ev_selects_finding(ev, R.upper())
    assert not d.ev_selects_finding(ev, str(uuid4())) and not d.ev_selects_finding(None, R)
    assert not d.ev_selects_finding(selected_basis(finding={**ev["finding"], "lifecycle": "NO_LONGER_SUPPORTED"}), R)
    ok = ev_basis(session_ids=[SES, SES2], accepted_evidence_ids=[E1, E2])
    assert d.ev_members_selected(ev, ok)
    assert d.ev_members_selected(ev, ev_basis(session_ids=[SES.upper()], accepted_evidence_ids=[E1.upper()]))
    foreign = str(uuid4())
    for basis in (ev_basis(session_ids=[SES2]),                       # the Finding's own session is missing
                  ev_basis(session_ids=[SES, foreign]),               # a session outside the selection
                  ev_basis(accepted_evidence_ids=[foreign]),          # foreign evidence
                  ev_basis(accepted_evidence_ids=[E3])):              # in A and B, uncited by the exact Finding
        assert not d.ev_members_selected(ev, basis)
    # Readiness 30: accepted but not cited by the head (A only), head-cited but not accepted (B only).
    assert not d.ev_members_selected(selected_basis(selected_evidence_ids=[E2]), ev_basis(accepted_evidence_ids=[E1]))
    assert not d.ev_members_selected(selected_basis(accepted_evidence_ids=[E2]), ev_basis(accepted_evidence_ids=[E1]))
    assert not d.ev_members_selected(selected_basis(finding={**ev["finding"], "session_id": None}), ev_basis())


# ---- the service over a fake store ------------------------------------------------------------------------------------

class FakeTx:
    def __init__(self, site_type="EV_CHARGING", action_domain="EV_CHARGING", revision_domain="ev_charging",
                 ev=None, pin=True) -> None:
        self.site, self.revision_domain, self.pin, self.ev = site_type, revision_domain, pin, ev or selected_basis()
        self.writes: list[str] = []
        self.root = {"id": F, "domain": action_domain, "origin_finding_id": F, "origin_finding_revision_id": R,
                     "raised_at": NOW - timedelta(minutes=10)}

    def lock(self, *a): pass
    def action_by_key(self, key): return None
    def db_now(self): return NOW
    def site_type(self): return self.site
    def finding_revision(self, f, r): return {"id": r, "finding_id": f, "domain": self.revision_domain}
    def selected_pin(self, revision): return {"window_start": NOW} if self.pin else None
    def selected_ev_basis(self, pin, revision_id): return self.ev
    def next_action_no(self): return 7
    def insert_action(self, row): self.writes.append("action")
    def action(self, aid): return self.root if aid == F else None
    def intent_by_key(self, aid, key): return None
    def intent_ids(self, aid): return [], set()
    def insert_intent(self, row): self.writes.append("intent"); self.inserted = row
    def selected_case_link(self, *a): return None
    def cited_evidence(self, revision_id): return {E1}
    def case_link_by_key(self, *a): return None
    def case(self, case_id): return None


class FakeStore:
    def __init__(self, tx: FakeTx) -> None:
        self.tx, self.calls = tx, 0

    def transaction(self, t, s, code, work):
        self.calls += 1
        return work(self.tx)


def run(tx: FakeTx, method: str, *args):
    store = FakeStore(tx)
    svc = DomainIntentService(store, new_id=lambda: UUID(int=9))
    return store, getattr(svc, method)(T, S, "EV-1", *args, PRINCIPAL)


def refused(tx: FakeTx, method: str, *args) -> tuple[int, str, str]:
    store = FakeStore(tx)
    svc = DomainIntentService(store)
    with pytest.raises(d.DomainIntentRefused) as caught:
        getattr(svc, method)(T, S, "EV-1", *args, PRINCIPAL)
    assert tx.writes == [], "a refused command writes nothing"
    return caught.value.status, caught.value.code, caught.value.message


def test_create_dispatch_site_type_and_supported_finding() -> None:
    tx = FakeTx()
    _, (status, body) = run(tx, "create_action", action_body())
    assert status == 201 and tx.writes == ["action"] and body["action_code"] == "ACT-000007"
    # Pre-flight 11: both Site-type mismatches refuse with the declared domain's link literal, before any read.
    assert refused(FakeTx(site_type="COLDCHAIN"), "create_action", action_body()) == (
        422, "DOMAIN_INTENT_LINK_INVALID", EV_LINK)
    assert refused(FakeTx(site_type="EV_CHARGING", revision_domain="cold_chain"), "create_action",
                   action_body(domain="COLDCHAIN")) == (422, "DOMAIN_INTENT_LINK_INVALID", COLD_LINK)
    assert refused(FakeTx(revision_domain="cold_chain"), "create_action", action_body()) == (
        422, "DOMAIN_INTENT_LINK_INVALID", EV_LINK)
    assert refused(FakeTx(pin=False), "create_action", action_body()) == (422, "DOMAIN_INTENT_LINK_INVALID", EV_LINK)
    unsupported = selected_basis(finding={**selected_basis()["finding"], "lifecycle": "NO_LONGER_SUPPORTED"})
    assert refused(FakeTx(ev=unsupported), "create_action", action_body()) == (
        422, "DOMAIN_INTENT_LINK_INVALID", EV_LINK)
    assert refused(FakeTx(), "create_action", action_body(raised_at=iso(NOW + timedelta(hours=1)))) == (
        422, "DOMAIN_INTENT_INVALID", EV_INVALID)
    store = FakeStore(FakeTx())
    with pytest.raises(d.DomainIntentRefused) as caught:
        DomainIntentService(store).create_action(T, S, "EV-1", action_body(domain="MINIGRID"), PRINCIPAL)
    assert caught.value.message == d.NEUTRAL_DOMAIN_INVALID and store.calls == 0


def test_intent_refusal_order_and_ev_membership() -> None:
    unknown = str(uuid4())
    # Shared-shape failure: neutral 422 before the store is touched, even for an unknown Action.
    store = FakeStore(FakeTx())
    with pytest.raises(d.DomainIntentRefused) as caught:
        DomainIntentService(store).post_intent(T, S, "EV-1", unknown, ev_intent(declared_at="x"), PRINCIPAL)
    assert caught.value.message == d.NEUTRAL_INTENT_INVALID and store.calls == 0
    with pytest.raises(d.DomainIntentRefused) as caught:
        DomainIntentService(store).post_intent(T, S, "EV-1", unknown, {**ev_intent(), "actor": {"kind": "X"}},
                                               PRINCIPAL)
    assert caught.value.message == d.NEUTRAL_INTENT_INVALID and store.calls == 0
    # Valid shared shape with malformed EV criteria or missing session_ids: 404 on an unknown Action ...
    two = ev_intent(criteria=crit()[:2])
    no_sessions = ev_intent(basis={k: v for k, v in ev_basis().items() if k != "session_ids"})
    for body in (two, no_sessions):
        assert refused(FakeTx(), "post_intent", unknown, body) == (404, "ACTION_NOT_FOUND",
                                                                    "Action was not found at this site.")
        # ... and the EV literal against the resolved EV Action.
        assert refused(FakeTx(), "post_intent", F, body) == (422, "DOMAIN_INTENT_INVALID", EV_INVALID)
    # A cold four-criterion body against the resolved EV Action is the EV literal; a three-criterion body against a
    # resolved cold Action is the cold literal.
    cold_body = ev_intent(criteria=crit(d.CRITERIA), basis={k: v for k, v in ev_basis().items() if k != "session_ids"})
    assert refused(FakeTx(), "post_intent", F, cold_body) == (422, "DOMAIN_INTENT_INVALID", EV_INVALID)
    assert refused(FakeTx(action_domain="COLDCHAIN", revision_domain="cold_chain"), "post_intent", F,
                   ev_intent(criteria=crit(d.CRITERIA)[:3])) == (422, "DOMAIN_INTENT_INVALID", COLD_INVALID)
    # Membership after resolution: the EV link literal, zero writes, no intersection.
    foreign = str(uuid4())
    for basis in (ev_basis(finding_revision_id=foreign), ev_basis(session_ids=[SES2]),
                  ev_basis(session_ids=[SES, foreign]), ev_basis(accepted_evidence_ids=[E1, foreign]),
                  ev_basis(accepted_evidence_ids=[E3])):
        assert refused(FakeTx(), "post_intent", F, ev_intent(basis=basis)) == (
            422, "DOMAIN_INTENT_LINK_INVALID", EV_LINK)
    for ev in (None, selected_basis(finding=None), selected_basis(selected_evidence_ids=[E2]),
               selected_basis(accepted_evidence_ids=[E2])):
        tx = FakeTx(ev=ev)
        tx.ev = ev
        assert refused(tx, "post_intent", F, ev_intent()) == (422, "DOMAIN_INTENT_LINK_INVALID", EV_LINK)
    assert refused(FakeTx(pin=False), "post_intent", F, ev_intent()) == (422, "DOMAIN_INTENT_LINK_INVALID", EV_LINK)
    tx = FakeTx()
    _, (status, body) = run(tx, "post_intent", F, ev_intent(basis=ev_basis(session_ids=[SES2, SES],
                                                                           accepted_evidence_ids=[E2, E1])))
    assert status == 201 and tx.writes == ["intent"] and body["schema_version"] == "domain-action-intent-1"
    assert tx.inserted["basis"] == {"finding_revision_id": R, "work_case_id": None, "work_record_id": None,
                                    "accepted_evidence_ids": sorted([E1, E2]), "session_ids": sorted([SES, SES2])}
    assert [c["key"] for c in tx.inserted["criteria"]] == [k for k, _, _ in d.EV_CRITERIA]


def test_case_link_neutral_then_404_then_domain_literal() -> None:
    link = {"case_id": E1, "case_revision_id": E2, "case_event_id": E3, "actor": dict(ACTOR),
            "idempotency_key": "w504-model-link-02"}
    store = FakeStore(FakeTx())
    with pytest.raises(d.DomainIntentRefused) as caught:
        DomainIntentService(store).post_case_link(T, S, "EV-1", F, {**link, "case_id": None}, PRINCIPAL)
    assert caught.value.message == d.NEUTRAL_CASE_LINK_INVALID and store.calls == 0
    assert refused(FakeTx(), "post_case_link", "not-a-uuid", link)[:2] == (404, "ACTION_NOT_FOUND")
    assert refused(FakeTx(), "post_case_link", F, link) == (422, "DOMAIN_INTENT_LINK_INVALID", EV_LINK)
    assert refused(FakeTx(action_domain="COLDCHAIN"), "post_case_link", F, link) == (
        422, "DOMAIN_INTENT_LINK_INVALID", COLD_LINK)


def test_unsupported_stored_domain_is_a_store_fault() -> None:
    with pytest.raises(m.WorkStoreUnavailable):
        DomainIntentService(FakeStore(FakeTx(action_domain="MINIGRID"))).post_intent(T, S, "EV-1", F, ev_intent(),
                                                                                     PRINCIPAL)
