"""W5-02a K1a: the pure domain Action model - closed bodies, fixed criteria, bounds, canonical digests, messages.

`.agent/W5-02-build-spec.md` "Command/read wire", "Backend wire, validation and lineage (K1a-K1c)" and the
Architect pre-flight ruling A2. No database.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

import pytest

from assetops_backend.work import domain_action as d
from assetops_backend.work import model as m

T, S = UUID(int=1), UUID(int=2)
ACTOR = {"kind": "SERVICE", "id": "service:w401-fixture", "attestation": "service=w401-fixture;job=j;rule=r/1"}
F, R, E1, E2 = (str(uuid4()) for _ in range(4))


def action(**over) -> dict:
    return {"domain": "COLDCHAIN", "origin_finding_id": F, "origin_finding_revision_id": R,
            "title": "Witness automatic-start test", "owner_label": "Maintenance lead", "due_at": None,
            "raised_at": "2026-10-20T10:00:00Z", "actor": dict(ACTOR), "idempotency_key": "w502-model-01", **over}


def crit() -> list[dict]:
    return [{"key": k, "label": label, "required_evidence": req} for k, label, req in d.CRITERIA]


def intent(**over) -> dict:
    return {"supersedes_id": None, "declared_at": "2026-10-20T11:00:00Z", "criteria": crit(),
            "basis": {"finding_revision_id": R, "work_case_id": None, "work_record_id": None,
                      "accepted_evidence_ids": [E2, E1]},
            "actor": dict(ACTOR), "idempotency_key": "w502-model-02", **over}


def invalid(call, *args) -> None:
    with pytest.raises(d.DomainIntentRefused) as caught:
        call(*args)
    assert (caught.value.status, caught.value.code, caught.value.message) == (
        422, "DOMAIN_INTENT_INVALID", "The cold Action declaration is incomplete or invalid.")


def test_four_exact_messages_and_statuses() -> None:
    assert d.MESSAGES == {
        "DOMAIN_INTENT_INVALID": "The cold Action declaration is incomplete or invalid.",
        "DOMAIN_INTENT_LINK_INVALID": "The declared Finding or work record is not selected at this site and cutoff.",
        "DOMAIN_INTENT_CONFLICT": "This Action declaration has a newer version; reload it.",
        "DOMAIN_INTENT_BASIS_CHANGED": "The selected cold work basis changed; reload the Action.",
        "ACTION_NOT_FOUND": "Action was not found at this site."}
    assert d.STATUS == {"DOMAIN_INTENT_INVALID": 422, "DOMAIN_INTENT_LINK_INVALID": 422,
                        "DOMAIN_INTENT_CONFLICT": 409, "DOMAIN_INTENT_BASIS_CHANGED": 409, "ACTION_NOT_FOUND": 404}
    assert d.refuse("ACTION_NOT_FOUND").detail() == {"code": "ACTION_NOT_FOUND",
                                                    "message": "Action was not found at this site."}
    # No new code is added to W4's WorkRefused table (ruling A2).
    assert not set(d.MESSAGES) & set(m.MESSAGES)


def test_action_body_closed_trimmed_and_bounded() -> None:
    body = d.action_body(action(title="  Witness automatic-start test ", owner_label=" Lead "))
    assert body["title"] == "Witness automatic-start test" and body["owner_label"] == "Lead"
    assert body["raised_at"] == datetime(2026, 10, 20, 10, tzinfo=timezone.utc) and body["due_at"] is None
    assert d.action_body(action(owner_label=None))["owner_label"] is None
    assert len(d.action_body(action(title="é" * 160))["title"]) == 160  # code points, not bytes
    for over in ({"domain": "MINIGRID"}, {"title": "   "}, {"title": "x" * 161}, {"owner_label": ""},
                 {"owner_label": "y" * 161}, {"raised_at": "2026-10-20T10:00:00"},
                 {"raised_at": "2026-10-20T13:00:00+03:00"}, {"due_at": "2026-10-20T09:59:59Z"},
                 {"due_at": "2027-10-21T10:00:00Z"}, {"origin_finding_id": "x"}, {"idempotency_key": "short"},
                 {"extra": 1}):
        invalid(d.action_body, action(**over))
    invalid(d.action_body, {k: v for k, v in action().items() if k != "owner_label"})
    invalid(d.action_body, "not an object")
    assert d.action_body(action(due_at="2027-10-20T10:00:00Z"))["due_at"] is not None  # exactly 365 days


def test_intent_criteria_and_basis() -> None:
    body = d.intent_body(intent())
    assert [c["key"] for c in body["criteria"]] == ["AUTOMATIC_START", "POWER_DELIVERY", "COOLING_RECOVERY",
                                                     "RECURRENCE"]
    assert body["basis"]["accepted_evidence_ids"] == sorted([E1, E2])
    swapped = crit()
    swapped[0], swapped[1] = swapped[1], swapped[0]
    relabel = crit()
    relabel[2] = {**relabel[2], "label": "Cooling"}
    extra = crit()
    extra[3] = {**extra[3], "note": "x"}
    for criteria in (crit()[:3], swapped, relabel, extra, crit() + crit()[:1], {}):
        invalid(d.intent_body, intent(criteria=criteria))
    for basis in ({"finding_revision_id": R, "work_case_id": None, "work_record_id": str(uuid4()),
                   "accepted_evidence_ids": []},
                  {"finding_revision_id": R, "work_case_id": None, "work_record_id": None,
                   "accepted_evidence_ids": [E1, E1]},
                  {"finding_revision_id": R, "work_case_id": None, "accepted_evidence_ids": []}):
        invalid(d.intent_body, intent(basis=basis))
    invalid(d.intent_body, intent(declared_at="yesterday"))
    invalid(d.intent_body, intent(supersedes_id="x"))


def test_case_link_body_and_path_id() -> None:
    ids = [str(uuid4()) for _ in range(3)]
    body = {"case_id": ids[0], "case_revision_id": ids[1], "case_event_id": ids[2], "actor": dict(ACTOR),
            "idempotency_key": "w502-model-03"}
    assert d.case_link_body(body)["case_event_id"] == ids[2]
    invalid(d.case_link_body, {**body, "case_event_id": None})
    invalid(d.case_link_body, {k: v for k, v in body.items() if k != "case_revision_id"})
    assert d.path_action_id("nope") is None and d.path_action_id(ids[0].upper()) == ids[0]


def test_command_window() -> None:
    now = datetime(2026, 10, 22, tzinfo=timezone.utc)
    assert d.within_command_window(now + timedelta(minutes=5), now)
    assert not d.within_command_window(now + timedelta(minutes=5, microseconds=1), now)
    assert d.within_command_window(now - timedelta(days=30), now)
    assert not d.within_command_window(now - timedelta(days=30, microseconds=1), now)


def test_canonical_command_hash() -> None:
    actor = m.authorize(m.actor_shape(ACTOR), ACTOR["id"])
    a = d.command_sha256(T, S, None, d.CMD_ACTION, d.action_body(action(title=" Witness automatic-start test")), actor)
    b = d.command_sha256(T, S, None, d.CMD_ACTION,
                         d.action_body(action(raised_at="2026-10-20T10:00:00.000000+00:00")), actor)
    assert a == b and len(a) == 64  # trimmed text and UTC `Z` normalization hash identically
    assert a != d.command_sha256(T, S, None, d.CMD_INTENT, d.action_body(action()), actor)
    assert a != d.command_sha256(T, UUID(int=3), None, d.CMD_ACTION, d.action_body(action()), actor)
    i1 = d.command_sha256(T, S, F, d.CMD_INTENT, d.intent_body(intent()), actor)
    i2 = d.command_sha256(T, S, F, d.CMD_INTENT, d.intent_body(intent(basis={**intent()["basis"],
                                                                              "accepted_evidence_ids": [E1, E2]})),
                          actor)
    assert i1 == i2  # sorted evidence IDs
    assert i1 != d.command_sha256(T, S, R, d.CMD_INTENT, d.intent_body(intent()), actor)  # route Action identity


def test_selection_token_shape_and_inputs() -> None:
    root = {"id": F, "raised_at": datetime(2026, 10, 20, 10, tzinfo=timezone.utc)}
    case = {"case_id": E1, "case_revision_id": E2, "case_event_id": R}
    token = d.selection_token(T, S, root, R, "i-1", case, None, [E2, E1])
    assert token.startswith("sha256:") and len(token) == 71 and token[7:] == token[7:].lower()
    assert token == d.selection_token(str(T), str(S), root, R, "i-1", case, None, [E1, E2])
    for changed in (d.selection_token(T, S, root, R, "i-2", case, None, [E1, E2]),
                    d.selection_token(T, S, root, R, "i-1", None, None, [E1, E2]),
                    d.selection_token(T, S, root, R, "i-1", case, F, [E1, E2]),
                    d.selection_token(T, S, root, R, "i-1", case, None, [E1]),
                    d.selection_token(T, S, {**root, "raised_at": datetime(2026, 10, 20, 11, tzinfo=timezone.utc)},
                                      R, "i-1", case, None, [E1, E2])):
        assert changed != token
