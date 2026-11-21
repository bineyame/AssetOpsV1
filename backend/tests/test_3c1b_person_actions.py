"""3C1b (`specs/3C1-person-on-commands/spec.md` §2, §3, §5; R2, R3, R6, R7, R9-R11; D-3C1.6, .8, .10-.12): the
signed-in person on the three trial-action commands (accept, apply, observe), with no database.

The action router is built directly (P7) over the real `ActionService` and a fake `ActionStore` that records every
event it is asked to write, with the actor the service hands it (P3). People come from 3C0a's in-memory
`AccountService`, through `test_3c1a_person_work.People`. `create_app` wiring and the stored rows are proved in
`test_3c1b_person_actions_postgres.py`.

The role table, channel, basis forms and digest payloads are written here from the spec, not imported from the code
under test (W2). Under D-SC1.28 (SC-1a not merged) no wording is asserted for the USER label: it is `None` until the
SC-1 text commit (Q-3C1b-1).
"""
from __future__ import annotations

from dataclasses import replace
from datetime import timedelta
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from assetops_backend.accounts.permissions import COMMAND_ROLES
from assetops_backend.action_api import build_action_router
from assetops_backend.actions import reserve_trial as rt
from assetops_backend.actions.capability import from_grants
from assetops_backend.actions.lifecycle import ACCEPTED, APPLIED, FAILED, OBSERVED, SYSTEM_DEMO
from assetops_backend.actions.ports import ApplyFailed
from assetops_backend.actions.service import ActionService
from test_3c1a_person_work import FT, KISIWA, KOBO, NOW, SM, People
from test_s6_action_rule import inputs, reading, segment

FIXTURE = "D-action-records-v1"
#: Spec §3, 3C1b rows (D-3C1.10: the site manager may also observe), written out independently.
SPEC_ROLES = {"action.accept": (SM,), "action.apply": (SM,), "action.observe": (SM, FT)}
UNSIGNED_LABEL = "SYSTEM demonstration"
OBSERVE_STATEMENT = ("A state-neutral SYSTEM demonstration note; it changes no application or verification state "
                     "and claims no effect.")


@pytest.fixture(scope="module")
def people() -> People:
    return People()


class Down(Exception):
    """The account store's unavailable type, as composition passes it."""


class BrokenAccounts:
    def resolve(self, token):
        raise Down("account store down")


class FakeActionStore:
    """The `ActionStore` port in memory. Each written event takes its actor columns from the `actor` the service
    passes (SYSTEM_DEMO when none), exactly as `PostgresActionStore._insert_event` does."""

    def __init__(self, tenant: UUID, site: UUID, granted: UUID, outside: UUID, rule_inputs: Any) -> None:
        self.scope, self.findings = (tenant, site), {granted, outside}
        self.inputs = rule_inputs
        self.actions: dict[UUID, dict[str, Any]] = {}
        self.written: list[dict[str, Any]] = []
        self.calls: list[dict[str, Any]] = []
        self.person: dict[UUID, UUID | None] = {}

    def _event(self, action_id, kind, command, occurred, recorded, key, payload, digest, fixture, actor, **extra):
        self.calls.append({"command": command, "actor_passed": actor is not SYSTEM_DEMO})
        event = {"id": uuid4(), "tenant_id": self.scope[0], "site_id": self.scope[1], "action_id": action_id,
                 "kind": kind, "occurred_at": occurred, "recorded_at": recorded, "actor_kind": actor.actor_kind,
                 "actor_id": actor.actor_id, "source_channel": actor.source_channel,
                 "authorization_basis": actor.basis(fixture, command), "triggering_service": actor.triggering_service,
                 "triggering_job": None, "triggering_command": command, "triggering_fixture": fixture,
                 "idempotency_key": key, "payload": payload, "payload_sha256": digest,
                 "failure_code": extra.get("failure_code"),
                 "observation_code": "DEMO_REVIEW_NOTE" if kind == OBSERVED else None,
                 "expected_foundation_revision_id": extra.get("expected"),
                 "current_foundation_revision_id": None, "verification_plan_id": None,
                 "verification_outcome_id": None}
        self.written.append(event)  # `person_id` is written but not read back (not in EVENT_COLUMNS)
        self.person[event["id"]] = getattr(actor, "person_id", None)
        return event

    def latest_revision(self, tenant_id, site_id, finding_id):
        return {"id": self.inputs.finding_revision_id} if finding_id in self.findings else None

    def rule_inputs(self, *args, **kwargs):
        return self.inputs

    def action_for_recommendation(self, tenant_id, site_id, key):
        return next((a for a in self.actions.values() if a["recommendation_key"] == key), None)

    def trial_actions(self, tenant_id, site_id, asset_id, rule_id):
        return []

    def accept(self, tenant_id, site_id, proposal, *, payload_sha256, payload, idempotency_key, fixture_id,
               recorded_at, guard, actor=SYSTEM_DEMO):
        guard([])
        action_id = uuid4()
        action = {"id": action_id, "tenant_id": tenant_id, "site_id": site_id, "action_code": "ACT-000001",
                  "recommendation_key": proposal["recommendation_key"], "acceptance_payload_sha256": payload_sha256,
                  "origin_finding_id": UUID(proposal["finding_id"]),
                  "origin_finding_revision_id": UUID(proposal["finding_revision_id"]), "created_at": recorded_at,
                  "snapshot": {"asset_code": "battery"}, "snapshot_sha256": "0" * 64,
                  "proposed_value": Decimal(proposal["proposed_value"]), "old_value": Decimal(proposal["old_value"]),
                  "unit": proposal["unit"]}
        self.actions[action_id] = action
        event = self._event(action_id, ACCEPTED, "ACCEPT", recorded_at, recorded_at, idempotency_key, payload,
                            payload_sha256, fixture_id, actor)
        return action, event, False

    def action(self, tenant_id, site_id, action_id):
        return self.actions.get(action_id)

    def events(self, tenant_id, site_id, action_id):
        return [e for e in self.written if e["action_id"] == action_id]

    def observe(self, tenant_id, site_id, action_id, *, occurred_at, idempotency_key, payload, payload_sha256,
                fixture_id, recorded_at, actor=SYSTEM_DEMO):
        prior = next((e for e in self.events(tenant_id, site_id, action_id) if e["idempotency_key"] == idempotency_key),
                     None)
        if prior is not None:
            return prior, True
        return self._event(action_id, OBSERVED, "OBSERVE", occurred_at, recorded_at, idempotency_key, payload,
                           payload_sha256, fixture_id, actor), False

    def apply(self, tenant_id, site_id, action_id, *, idempotency_key, payload, payload_sha256, fixture_id,
              recorded_at, expected_foundation_revision_id, attempt, actor=SYSTEM_DEMO):
        events = self.events(tenant_id, site_id, action_id)
        prior = next((e for e in events if e["idempotency_key"] == idempotency_key), None)
        if prior is not None:
            return {"outcome": "REPLAY", "event": prior, "change": None}
        written: dict[str, Any] = {}

        def then(ids):
            written["event"] = self._event(action_id, APPLIED, "APPLY", recorded_at, recorded_at, idempotency_key,
                                           payload, payload_sha256, fixture_id, actor,
                                           expected=expected_foundation_revision_id)
        try:
            attempt(None, self.actions[action_id], events, then)
        except ApplyFailed as failed:
            event = self._event(action_id, FAILED, "APPLY", recorded_at, recorded_at, idempotency_key, payload,
                                payload_sha256, fixture_id, actor, failure_code=failed.code,
                                expected=expected_foundation_revision_id)
            return {"outcome": "FAILED", "event": event, "failure": failed}
        return {"outcome": "APPLIED", "event": written["event"], "change": None}


def _publish(site_code, connection, then, **kwargs) -> None:
    then({})


class Api:
    """One action router over a fresh fake store: Kobo holds a granted Finding and one outside the grant file."""

    def __init__(self, people: People, *, accounts: Any = "people", require_person: bool = False,
                 scope: dict | None = None, unavailable: tuple = ()) -> None:
        self.people = people
        self.granted, self.outside = uuid4(), uuid4()
        revision = uuid4()
        made = replace(inputs(segment(reading("80"))), tenant_id=people.acme, site_id=people.kobo,
                       finding_id=self.granted, finding_revision_id=revision)
        self.proposal = rt.evaluate(made).proposal
        self.store = FakeActionStore(people.acme, people.kobo, self.granted, self.outside, made)
        grants = {"schema": "assetops.action-demo-grants", "version": 2, "fixture_id": FIXTURE,
                  "grants": [{"tenant_id": str(people.acme), "site_id": str(people.kobo), "site_code": KOBO,
                              "commands": ["ACCEPT", "APPLY", "OBSERVE"],
                              "records": [{"manifest_id": "rec-1", "finding_id": str(self.granted)}]}]}

        def currentness(tenant_id, site_id, finding_id, revision_id, source_open):
            if finding_id not in (self.granted, self.outside):
                return None
            return {"revision_id": revision, "latest_revision_id": revision, "is_latest": True,
                    "claim_is_current": True}

        self.service = ActionService(self.store, currentness, from_grants(grants), lambda: NOW, publish=_publish)
        scopes = scope if scope is not None else {KOBO: (KOBO, people.acme, people.kobo),
                                                  KISIWA: (KISIWA, people.acme, people.kisiwa)}
        app = FastAPI()
        app.include_router(build_action_router(
            self.service, scopes.get, gate=lambda c, t, s: (True, "test gate"),
            **({} if accounts is None else {"accounts": people.svc if accounts == "people" else accounts,
                                            "require_person": require_person,
                                            "accounts_unavailable": unavailable})))
        self.client = TestClient(app)

    def accept_body(self, key: str = "accept-0001", **over) -> dict:
        p = self.proposal
        return {"revision_id": p["finding_revision_id"], "recommendation_key": p["recommendation_key"],
                "foundation_revision_id": p["foundation_revision_id"], "proposed_value": p["proposed_value"],
                "idempotency_key": key, **over}

    def accept(self, who: str | None, finding: UUID | None = None, site: str = KOBO, **body):
        return self.client.post(f"/api/sites/{site}/findings/{finding or self.granted}/recommendation/accept",
                                json=self.accept_body(**body), headers=self.people.cookie(who))

    def accepted(self) -> str:
        made = self.accept(None)
        assert made.status_code == 201, made.text
        return made.json()["action"]["action_id"]

    def apply(self, who: str | None, action_id: str, key: str = "apply-0001", site: str = KOBO, **over):
        body = {"expected_foundation_revision_id": self.proposal["foundation_revision_id"], "value": "15",
                "effective_from": (NOW + timedelta(days=1)).isoformat(), "idempotency_key": key, **over}
        return self.client.post(f"/api/sites/{site}/actions/{action_id}/apply", json=body,
                                headers=self.people.cookie(who))

    def observe(self, who: str | None, action_id: str, key: str = "observe-0001", site: str = KOBO, **over):
        body = {"observation_code": "DEMO_REVIEW_NOTE", "occurred_at": NOW.isoformat(), "idempotency_key": key,
                **over}
        return self.client.post(f"/api/sites/{site}/actions/{action_id}/observations", json=body,
                                headers=self.people.cookie(who))

    def send(self, command: str, who: str | None, site: str = KOBO, **over):
        """One of the three commands; apply and observe run on an Action accepted unsigned beforehand."""
        if command == "action.accept":
            return self.accept(who, site=site, **over)
        action_id = self.accepted()
        return (self.apply if command == "action.apply" else self.observe)(who, action_id, site=site, **over)


COMMANDS = tuple(SPEC_ROLES)


def _detail(response) -> dict:
    return response.json()["detail"]


# ---- the role table ---------------------------------------------------------------------------------------------

def test_command_roles_hold_the_three_action_rows_in_spec_order() -> None:
    assert {k: COMMAND_ROLES[k] for k in SPEC_ROLES} == SPEC_ROLES


# ---- admitted: the actor, channel and basis are the server's ----------------------------------------------------

@pytest.mark.parametrize("command,who,role", [
    ("action.accept", "peter", SM), ("action.apply", "peter", SM), ("action.observe", "peter", SM),
    ("action.observe", "fatma", FT),
    ("action.observe", "tess", SM),  # FT and SM at Kobo: the first match in §3's order (SM, FT) admits
])
def test_a_person_with_a_listed_role_is_recorded_under_that_person(people, command, who, role) -> None:
    api = Api(people)
    made = api.send(command, who)
    assert made.status_code == 201, made.text
    event = made.json()["event"]
    stored = api.store.written[-1]
    assert (stored["actor_kind"], stored["actor_id"], api.store.person[stored["id"]]) == (
        "USER", f"person:{people.ids[who]}", people.ids[who])
    assert stored["source_channel"] == "PERSON_API"
    assert stored["authorization_basis"] == f"PERSON_ROLE:{role}"
    assert stored["triggering_fixture"] == FIXTURE  # R3: still the grant file's fixture
    assert event["actor"]["kind"] == "USER" and event["actor"]["id"] == f"person:{people.ids[who]}"
    assert event["actor"]["authorization_basis"] == f"PERSON_ROLE:{role}"
    assert event["actor"]["label"] is None  # Q-3C1b-1: the wording waits for SC-1a (D-SC1.28)
    assert stored["payload"]["actor_id"] == f"person:{people.ids[who]}"  # R2: the person is in the digest


def test_the_observe_statement_is_none_for_a_person_and_unchanged_unsigned(people) -> None:
    api = Api(people)
    action_id = api.accepted()
    signed = api.observe("peter", action_id, key="observe-person")
    assert signed.status_code == 201 and signed.json()["statement"] is None
    unsigned = api.observe(None, action_id, key="observe-system")
    assert unsigned.status_code == 201 and unsigned.json()["statement"] == OBSERVE_STATEMENT
    assert unsigned.json()["event"]["actor"]["label"] == UNSIGNED_LABEL


def test_a_failed_apply_is_the_persons_act(people) -> None:
    api = Api(people)
    action_id = api.accepted()
    failed = api.apply("peter", action_id, value="12")
    assert failed.status_code == 422 and _detail(failed)["code"] == "ACTION_VALUE_INVALID"
    stored = api.store.written[-1]
    assert stored["kind"] == FAILED
    assert (stored["actor_kind"], stored["source_channel"], stored["authorization_basis"]) == (
        "USER", "PERSON_API", "PERSON_ROLE:SITE_MANAGER")
    assert _detail(failed)["event"]["actor"]["label"] is None


# ---- refused: role, Site, tenant, client actor, grant scope -----------------------------------------------------

@pytest.mark.parametrize("command,who", [
    ("action.accept", "fatma"), ("action.apply", "fatma"), ("action.accept", "fiona"), ("action.apply", "fiona"),
    ("action.observe", "fiona"), ("action.observe", "ana"),
])
def test_a_person_without_a_listed_role_gets_403(people, command, who) -> None:
    api = Api(people)
    before = len(api.store.written) + (0 if command == "action.accept" else 1)
    refused = api.send(command, who)
    assert refused.status_code == 403
    assert _detail(refused)["code"] == "PERSON_ROLE_REQUIRED"
    assert _detail(refused)["params"] == {"roles": list(SPEC_ROLES[command])}
    assert len(api.store.written) == before


@pytest.mark.parametrize("command", COMMANDS)
def test_a_site_manager_of_another_site_gets_403(people, command) -> None:
    api = Api(people)
    refused = api.send(command, "kim")
    assert refused.status_code == 403 and _detail(refused)["code"] == "PERSON_ROLE_REQUIRED"


@pytest.mark.parametrize("command", COMMANDS)
def test_another_tenant_gets_the_routes_unknown_site_404_byte_for_byte(people, command) -> None:
    api = Api(people)
    before = len(api.store.written) + (0 if command == "action.accept" else 1)
    refused = api.send(command, "hugo")
    unknown = Api(people, scope={})  # the same request where Kobo is not a Site of this tenant
    path = refused.request.url.path
    expected = unknown.client.post(path, json={}, headers=people.cookie("hugo"))
    assert refused.status_code == expected.status_code == 404
    assert refused.content == expected.content
    assert len(api.store.written) == before


@pytest.mark.parametrize("command", COMMANDS)
def test_a_body_carrying_actor_gets_422(people, command) -> None:
    api = Api(people)
    refused = api.send(command, "peter", actor={"kind": "SERVICE", "id": "service:x"})
    assert refused.status_code == 422
    assert _detail(refused)["code"] == "CLIENT_AUTHORITY_FORBIDDEN" and _detail(refused)["fields"] == ["actor"]


def test_a_finding_outside_the_grant_is_refused_as_today(people) -> None:
    api = Api(people)
    signed = api.accept("peter", finding=api.outside)
    unsigned = api.accept(None, finding=api.outside)
    assert signed.status_code == unsigned.status_code == 403
    assert _detail(signed)["code"] == "SYSTEM_DEMO_CAPABILITY_DENIED"
    assert signed.content == unsigned.content
    missing = api.accept("peter", finding=uuid4())
    assert missing.status_code == 404 and _detail(missing)["code"] == "FINDING_NOT_FOUND"
    assert api.store.written == []


def test_an_action_outside_the_grant_or_unknown_is_refused_as_today(people) -> None:
    api = Api(people)
    for command in ("apply", "observe"):
        missing = getattr(api, command)("peter", str(uuid4()))
        assert missing.status_code == 404 and _detail(missing)["code"] == "ACTION_NOT_FOUND"
    assert api.store.written == []


# ---- the digest: same person replays, a second person is refused (R2, D-3C1.8) ----------------------------------

def test_a_second_persons_identical_accept_gets_409_and_the_same_persons_retry_replays(people) -> None:
    api = Api(people)
    first = api.accept("peter")
    assert first.status_code == 201, first.text
    again = api.accept("peter2")  # Peter in a second session
    assert again.status_code == 200 and again.json()["replayed"] is True
    other = api.accept("sam")
    assert other.status_code == 409 and _detail(other)["code"] == "ACTION_ACCEPTANCE_CONFLICT"
    unsigned = api.accept(None)
    assert unsigned.status_code == 409 and _detail(unsigned)["code"] == "ACTION_ACCEPTANCE_CONFLICT"
    assert len(api.store.written) == 1


@pytest.mark.parametrize("command", ("apply", "observe"))
def test_a_second_persons_reuse_of_a_key_gets_409_and_the_same_persons_retry_replays(people, command) -> None:
    api = Api(people)
    action_id = api.accepted()
    send = getattr(api, command)
    assert send("peter", action_id).status_code == 201
    again = send("peter2", action_id)
    assert again.status_code == 200 and again.json()["replayed"] is True
    other = send("sam", action_id)
    assert other.status_code == 409 and _detail(other)["code"] == "IDEMPOTENCY_KEY_CONFLICT"
    assert len(api.store.written) == 2


# ---- no person: the switch, no accounts, an account outage ------------------------------------------------------

@pytest.mark.parametrize("command", COMMANDS)
def test_with_the_switch_on_no_person_gets_401(people, command) -> None:
    api = Api(people, require_person=True)
    action_id = str(uuid4())
    if command == "action.accept":
        refused = api.accept(None)
    else:
        refused = (api.apply if command == "action.apply" else api.observe)(None, action_id)
    assert refused.status_code == 401 and _detail(refused)["code"] == "PERSON_REQUIRED"
    assert api.store.written == []


@pytest.mark.parametrize("command", COMMANDS)
def test_with_the_switch_off_no_person_is_todays_system_path(people, command) -> None:
    api = Api(people)
    made = api.send(command, None)
    assert made.status_code == 201, made.text
    for stored in api.store.written:
        assert (stored["actor_kind"], stored["actor_id"], stored["source_channel"]) == (
            "SYSTEM", "service:assetops-action-demonstration", "SYSTEM_DEMONSTRATION_API")
        assert stored["authorization_basis"].startswith("SYSTEM_DEMONSTRATION_CAPABILITY: ")
        assert api.store.person[stored["id"]] is None and "actor_id" not in stored["payload"]
        assert stored["payload_sha256"] == rt.sha(stored["payload"])
    assert made.json()["event"]["actor"]["label"] == UNSIGNED_LABEL
    assert not any(call["actor_passed"] for call in api.store.calls)  # the store is called exactly as before (P6)


def test_with_no_accounts_composed_a_cookie_is_no_person(people) -> None:
    api = Api(people, accounts=None)
    made = api.accept("peter")
    assert made.status_code == 201 and api.store.written[-1]["actor_kind"] == "SYSTEM"


def test_an_account_store_outage_is_the_routes_503_even_with_the_switch_off(people) -> None:
    api = Api(people, accounts=BrokenAccounts(), unavailable=(Down,))
    refused = api.accept("peter")
    assert refused.status_code == 503 and _detail(refused)["code"] == "ACTION_STORE_UNAVAILABLE"
    assert api.store.written == []


# ---- reads: SYSTEM labels unchanged, USER label None ------------------------------------------------------------

def test_event_reads_label_by_actor_kind(people) -> None:
    api = Api(people)
    action_id = api.accepted()
    assert api.observe("peter", action_id).status_code == 201
    events = api.client.get(f"/api/sites/{KOBO}/actions/{action_id}/events").json()["events"]
    labels = {e["actor"]["kind"]: e["actor"]["label"] for e in events}
    assert labels == {"SYSTEM": UNSIGNED_LABEL, "USER": None}
    assert all("person_id" not in e for e in events)  # not in EVENT_COLUMNS: reads stay byte-equal
