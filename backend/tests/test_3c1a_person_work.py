"""3C1a (`specs/3C1-person-on-commands/spec.md` §2-§4; rulings R1, R4-R6, R8-R11, P4-P7, D-3C1.6, .8, .10, .12): the
signed-in person on the 10 work and domain commands, with no database.

The routers are built directly (P7) over in-memory fakes of the work and domain transactions and 3C0a's in-memory
`AccountService` (`test_3c0a_accounts_service.MemoryStore`). The fakes record every INSERTed row, so the stored actor
columns are read back exactly as the adapters would write them. `create_app` wiring is proved in
`test_3c1a_person_work_postgres.py`.

The expected role table, attestation and basis forms and the hashed actor are written here from the spec, not
imported from the code under test (W2).
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta, timezone
from itertools import count
from typing import Any, Callable
from uuid import UUID, uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from assetops_backend.accounts.composition import require_person
from assetops_backend.accounts.model import COOKIE
from assetops_backend.accounts.permissions import COMMAND_ROLES, roles_of
from assetops_backend.accounts.service import AccountService
from assetops_backend.config import ConfigurationError
from assetops_backend.domain_work_api import build_domain_work_router
from assetops_backend.work import domain_action as d
from assetops_backend.work.domain_intent import DomainIntentService
from assetops_backend.work.service import WorkService
from assetops_backend.work_api import WorkGate, build_work_router
from test_3c0a_accounts_service import PW, Clock, MemoryStore

NOW = datetime(2026, 11, 20, 12, 0, tzinfo=timezone.utc)
PRINCIPAL = "service:w401-fixture"
SERVICE_ACTOR = {"kind": "SERVICE", "id": PRINCIPAL, "attestation": "service=w401-fixture;job=seed;rule=w401/1"}
SM, FT, FIN = "SITE_MANAGER", "FIELD_TECHNICIAN", "FINANCE_AND_COMMERCIAL_LEAD"
KOBO, KISIWA = "KOBO-001", "KISIWA-001"

#: Spec §3 as amended (D-3C1.10, R5c/d), written out independently of `COMMAND_ROLES`.
SPEC_ROLES = {
    "work.case_create": (SM, FT), "work.case_event.COMPLETE": (SM, FT), "work.case_event.COMMENT": (SM, FT),
    "work.case_event.ASSIGN": (SM,), "work.case_event.CLOSE": (SM,), "work.case_event.REOPEN": (SM,),
    "work.case_event.CANCEL": (SM,), "work.case_revision": (SM,), "work.maintenance_record": (FT, SM),
    "work.maintenance_plan": (SM,), "work.operational_record": (FT, SM), "work.operational_entry": (FT, SM),
    "domain.create": (SM, FIN), "domain.intent": (SM, FIN), "domain.case_link": (SM,),
    "commercial.upload": ("ANALYST", FIN), "commercial.upload_decision": (FIN, "OPERATOR_EXECUTIVE"),
    "commercial.upload_read": ("ANALYST", FIN, "OPERATOR_EXECUTIVE", SM),
    "commercial.profile_admit": ("ANALYST", FIN),
    "action.agree": ("OPERATOR_EXECUTIVE",),  # 3C2 (spec §2.2; D-3C2.2): a command, not a work route
    "commercial.accounts_statement": (FIN,),
    # 3B4 (spec §5.3): the tolerance command's two keys (a command line, no route).
    "structure.tolerance.money": (FIN,), "structure.tolerance.operational": (SM,),
    "decision.prepare": ("ANALYST",), "decision.one_off": (SM, FIN), "decision.choose": ("OPERATOR_EXECUTIVE",),  # 6a
    "decision.evaluate": ("ANALYST",),  # 6c
    # 3C1b (spec §3): the trial actions.
    "action.accept": (SM,), "action.apply": (SM,), "action.observe": (SM, FT),
}


def iso(value: datetime) -> str:
    return value.strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def sha(path: dict, body: dict) -> str:
    """B6 independently: SHA-256 of sorted-key compact UTF-8 JSON of `{path, body}`."""
    text = json.dumps({"path": path, "body": body}, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


# ---- people (3C0a's in-memory account service) -----------------------------------------------------------------

class People:
    """Acme (Kobo, Kisiwa) and Beta. Peter: SM at Kobo (two sessions). Sam: SM at Kobo. Tess: FT and SM at Kobo.
    Fatma: FT. Fiona: finance lead. Ana: analyst only. Kim: SM at Kisiwa. Hugo: Beta, SM at Beta and FT."""

    def __init__(self) -> None:
        self.store, self.clock = MemoryStore(), Clock(NOW - timedelta(hours=1))
        self.svc = AccountService(self.store, clock=self.clock)
        self.acme = self.store.add_tenant("acme", "Acme Power")
        self.beta = self.store.add_tenant("beta", "Beta Cold")
        self.kobo = self.store.add_site(self.acme, KOBO)
        self.kisiwa = self.store.add_site(self.acme, KISIWA)
        self.store.add_site(self.beta, "BETA-001")
        self.ids: dict[str, UUID] = {}
        self.tokens: dict[str, str] = {}
        self.sessions: dict[str, UUID] = {}
        boss = {"acme": self._make("amina", "acme", executive=True), "beta": self._make("hugo", "beta", executive=True)}
        grants = {"peter": [(SM, KOBO)], "sam": [(SM, KOBO)], "tess": [(FT, None), (SM, KOBO)], "fatma": [(FT, None)],
                  "fiona": [(FIN, None)], "ana": [("ANALYST", None)], "kim": [(SM, KISIWA)]}
        for name, held in grants.items():
            pid = self._make(name, "acme")
            for role, site in held:
                self.svc.grant(boss["acme"], pid, role, site)
        for role, site in ((SM, "BETA-001"), (FT, None)):
            self.svc.grant(boss["beta"], self.ids["hugo"], role, site)
        for name in (*grants, "hugo"):
            self.sign(name)
        self.sign("peter", "peter2")

    def _make(self, name: str, tenant: str, executive: bool = False):
        pid = self.svc.onboard_create(tenant, f"{name}@{tenant}.example", name.title(), PW, executive=executive)
        self.ids[name] = pid
        if executive:
            signed = self.svc.sign_in(f"{name}@{tenant}.example", PW)
            return signed.principal
        return pid

    def sign(self, name: str, as_name: str | None = None) -> None:
        tenant = "beta" if name == "hugo" else "acme"
        signed = self.svc.sign_in(f"{name}@{tenant}.example", PW)
        self.tokens[as_name or name] = signed.token
        self.sessions[as_name or name] = signed.principal.session_id
        self.ids.setdefault(as_name or name, self.ids[name])

    def cookie(self, who: str | None) -> dict[str, str]:
        return {} if who is None else {"cookie": f"{COOKIE}={self.tokens[who]}"}


@pytest.fixture(scope="module")
def people() -> People:
    return People()


# ---- fakes of the two transaction ports ------------------------------------------------------------------------

class FakeWorkTx:
    def __init__(self, store: "FakeWork") -> None:
        self.w = store

    def _stamp(self, table: str, row: dict) -> dict:
        self.w.tick += 1
        stored = {**row, "recorded_at": NOW + timedelta(microseconds=self.w.tick)}
        self.w.rows.setdefault(table, []).append(stored)
        return stored

    def db_now(self) -> datetime:
        return NOW

    def next_public_no(self) -> int:
        self.w.tick += 1
        return self.w.tick

    def case_by_create_key(self, key: str):
        return next((c for c in self.w.rows.get("work_case", []) if c["create_key"] == key), None)

    def insert_case(self, row: dict) -> None:
        self._stamp("work_case", row)

    def insert_incident(self, case_id: str, key: str) -> None: ...

    def insert_request(self, case_id: str, key: str, incident_id: str | None) -> None: ...

    def insert_revision(self, row: dict) -> None:
        self._stamp("work_case_revision", row)

    def insert_event(self, row: dict) -> None:
        self._stamp("work_event", row)

    def insert_record(self, row: dict) -> None:
        self._stamp("maintenance_record", row)

    def insert_plan(self, row: dict) -> None:
        self._stamp("maintenance_plan", row)

    def insert_operational_record(self, row: dict) -> None:
        self._stamp("operational_record", row)

    def case(self, case_id: str):
        return next((c for c in self.w.rows.get("work_case", []) if str(c["id"]) == str(case_id)), None)

    lock_case = case

    def revisions(self, case_id: str) -> list[dict]:
        return [r for r in self.w.rows.get("work_case_revision", []) if r["case_id"] == case_id]

    def events(self, case_id: str) -> list[dict]:
        return [e for e in self.w.rows.get("work_event", []) if e["case_id"] == case_id]

    def revision_links(self, revision_id: str) -> dict:
        return {"finding_links": [], "action_links": [], "evidence_ids": []}

    def record_by_key(self, case_id: str, key: str):
        return next((r for r in self.w.rows.get("maintenance_record", [])
                     if r["case_id"] == case_id and r["idempotency_key"] == key), None)

    def record_in_case(self, case_id: str, record_id: str) -> bool:
        return any(r["case_id"] == case_id and r["id"] == record_id for r in self.w.rows.get("maintenance_record", []))

    def lineage_by_key(self, table: str, key: str):
        return next((r for r in self.w.rows.get(table, []) if r["idempotency_key"] == key), None)

    def lineage_row(self, table: str, row_id: str):
        return next(r for r in self.w.rows.get(table, []) if r["id"] == row_id)


class FakeWork:
    def __init__(self) -> None:
        self.rows: dict[str, list[dict]] = {}
        self.tick = 0

    def transaction(self, tenant_id: UUID, site_id: UUID, work: Callable[[Any], Any]) -> Any:
        return work(FakeWorkTx(self))


class FakeWorkService(WorkService):
    """Q11 provenance needs the evidence ledger; it is out of this unit, so the fake answers it empty."""

    def provenance(self, *args: Any, **kwargs: Any) -> dict:
        return {}


class FakeDomainTx:
    def __init__(self, store: "FakeDomain") -> None:
        self.w = store

    def _insert(self, table: str, row: dict) -> None:
        self.w.rows.setdefault(table, []).append({**row, "recorded_at": NOW})

    def db_now(self) -> datetime:
        return NOW

    def lock(self, command: str, key: str) -> None: ...

    def site_type(self) -> str:
        return "COLDCHAIN"

    def finding_revision(self, finding_id: str, revision_id: str):
        if (finding_id, revision_id) != (self.w.finding, self.w.revision):
            return None
        return {"finding_id": finding_id, "id": revision_id, "domain": d.FINDING_DOMAIN}

    def selected_pin(self, revision: dict) -> dict:
        return {"pin": revision["id"]}

    def cited_evidence(self, revision_id: str) -> set[str]:
        return {self.w.evidence}

    def next_action_no(self) -> int:
        self.w.number += 1
        return self.w.number

    def action_by_key(self, key: str):
        return next((a for a in self.w.rows.get("domain_action", []) if a["idempotency_key"] == key), None)

    def insert_action(self, row: dict) -> None:
        self._insert("domain_action", row)

    def action(self, action_id: str):
        return next((a for a in self.w.rows.get("domain_action", []) if a["id"] == action_id), None)

    def intent_by_key(self, action_id: str, key: str):
        return next((i for i in self.w.rows.get("domain_action_intent", [])
                     if i["action_id"] == action_id and i["idempotency_key"] == key), None)

    def intent_ids(self, action_id: str):
        rows = [i for i in self.w.rows.get("domain_action_intent", []) if i["action_id"] == action_id]
        return [i["id"] for i in rows], {i["supersedes_id"] for i in rows if i["supersedes_id"]}

    def insert_intent(self, row: dict) -> None:
        self._insert("domain_action_intent", row)

    def case_link_by_key(self, action_id: str, key: str):
        return next((x for x in self.w.rows.get("domain_action_case_link", [])
                     if x["action_id"] == action_id and x["idempotency_key"] == key), None)

    def case(self, case_id: str):
        return {"id": case_id, "kind": "INCIDENT"} if case_id == self.w.case else None

    def case_heads(self, case_id: str):
        return [self.w.case_revision], [self.w.case_event], self.w.case_revision, self.w.case_event

    def case_link_exists(self, action_id: str, case_id: str, revision_id: str, event_id: str) -> bool:
        return False

    def insert_case_link(self, row: dict) -> None:
        self._insert("domain_action_case_link", row)


class FakeDomain:
    def __init__(self) -> None:
        self.rows: dict[str, list[dict]] = {}
        self.number = 0
        self.finding, self.revision, self.evidence = str(uuid4()), str(uuid4()), str(uuid4())
        self.case, self.case_revision, self.case_event = str(uuid4()), str(uuid4()), str(uuid4())

    def transaction(self, tenant_id: UUID, site_id: UUID, site_code: str, work: Callable[[Any], Any]) -> Any:
        return work(FakeDomainTx(self))


# ---- the two routers, built directly (P7) ----------------------------------------------------------------------

def ids():
    n = count(1)
    return lambda: UUID(f"30000000-0000-4000-8000-{next(n):012x}")


class Api:
    """One app with the work and domain routers over fresh fakes. `principal`/`entry` False: no feature principal."""

    def __init__(self, people: People, *, principal: bool = True, entry: bool = True, require: bool = False,
                 accounts: Any = True, unavailable: tuple[type, ...] = (), scope: dict | None = None) -> None:
        self.p = people
        self.work, self.domain = FakeWork(), FakeDomain()
        self.svc = FakeWorkService(self.work, new_id=ids())
        self.dsvc = DomainIntentService(self.domain, new_id=ids())
        scopes = scope if scope is not None else {KOBO: (KOBO, people.acme, people.kobo),
                                                  KISIWA: (KISIWA, people.acme, people.kisiwa)}
        who = (lambda r, c: PRINCIPAL) if principal else (lambda r, c: None)
        accounts_svc = people.svc if accounts is True else (None if accounts is False else accounts)
        person = {"accounts": accounts_svc, "require_person": require, "accounts_unavailable": unavailable}
        app = FastAPI()
        app.include_router(build_work_router(
            self.svc, scopes.get, principal=who, entry_principal=(lambda r, c: "service:operator-entry") if entry
            else (lambda r, c: None), site_context=lambda t, s: ("UTC", None), **person))
        app.include_router(build_domain_work_router(self.dsvc, WorkGate(scopes.get, principal=who, **person)))
        self.client = TestClient(app)

    def post(self, path: str, body: Any, who: str | None = None, site: str = KOBO):
        return self.client.post(f"/api/sites/{site}/{path}", json=body, headers=self.p.cookie(who))

    # seeding through today's SERVICE path
    def seed_case(self, kind: str = "INCIDENT", key: str | None = None) -> dict:
        status, body = self.svc.create_case(self.p.acme, self.p.kobo, {**case_body(kind, key or f"seed-{uuid4()}"),
                                                                        "actor": SERVICE_ACTOR}, PRINCIPAL)
        assert status == 201, body
        return body

    def seed_event(self, case_id: str, kind: str, payload: dict) -> None:
        status, body = self.svc.post_event(self.p.acme, self.p.kobo, case_id, {**event_body(kind, payload, f"seed-{uuid4()}"),
                                                                               "actor": SERVICE_ACTOR}, PRINCIPAL)
        assert status == 201, body

    def seed_record(self, case_id: str) -> str:
        status, body = self.svc.post_record(self.p.acme, self.p.kobo, case_id,
                                            {**record_body(f"seed-{uuid4()}"), "actor": SERVICE_ACTOR}, PRINCIPAL)
        assert status == 201, body
        return body["id"]

    def seed_action(self) -> str:
        status, body = self.dsvc.create_action(self.p.acme, self.p.kobo, KOBO,
                                               {**action_body(self.domain, f"seed-{uuid4()}"), "actor": SERVICE_ACTOR},
                                               PRINCIPAL)
        assert status == 201, body
        return body["id"]

    def written(self, table: str) -> list[dict]:
        store = self.domain if table.startswith("domain") else self.work
        return store.rows.get(table, [])


# ---- bodies (the person path's shapes: no `actor`) -------------------------------------------------------------

def case_body(kind: str = "INCIDENT", key: str = "p3c1a-case-0001") -> dict:
    return {"kind": kind, "occurred_at": iso(NOW - timedelta(hours=1)), "asset_id": None, "finding_links": [],
            "action_links": [], "title": "Starter fault", "narrative": "Seen at the morning round.",
            "cited_accepted_evidence_ids": [], "idempotency_key": key}


def event_body(kind: str, payload: dict, key: str) -> dict:
    return {"kind": kind, "occurred_at": iso(NOW - timedelta(minutes=30)), "payload": payload, "idempotency_key": key}


def record_body(key: str = "p3c1a-record-0001") -> dict:
    return {"activity": "Starter inspected", "outcome_note": None, "occurred_at": iso(NOW - timedelta(minutes=20)),
            "idempotency_key": key}


def plan_body(key: str = "p3c1a-plan-0001") -> dict:
    return {"asset_id": None, "title": "Monthly start test", "trigger_kind": "CALENDAR", "next_due_at": None,
            "next_due_hours": None, "occurred_at": iso(NOW - timedelta(minutes=10)), "idempotency_key": key}


def oprec_body(key: str = "p3c1a-oprec-0001") -> dict:
    return {"kind": "OPERATOR_LOG", "body": "Generator started by hand", "occurred_at": iso(NOW - timedelta(minutes=5)),
            "period_end": None, "unit": None, "quantity": None, "source_document_sha256": None, "case_id": None,
            "idempotency_key": key}


def entry_body(key: str = "oprec-entry-" + "3c1a" * 8) -> dict:
    return {"entry": "METER_READING", "value": "1520", "taken_at_local": "2026-11-20T06:00", "ticket_reference": None,
            "idempotency_key": key}


def action_body(domain: FakeDomain, key: str = "p3c1a-action-0001") -> dict:
    return {"domain": "COLDCHAIN", "origin_finding_id": domain.finding, "origin_finding_revision_id": domain.revision,
            "title": "Witness the automatic start", "owner_label": None, "due_at": None,
            "raised_at": iso(NOW - timedelta(minutes=10)), "idempotency_key": key}


def intent_body(domain: FakeDomain, key: str = "p3c1a-intent-0001") -> dict:
    return {"supersedes_id": None, "declared_at": iso(NOW - timedelta(minutes=1)),
            "criteria": [{"key": k, "label": label, "required_evidence": r} for k, label, r in d.CRITERIA],
            "basis": {"finding_revision_id": domain.revision, "work_case_id": None, "work_record_id": None,
                      "accepted_evidence_ids": [domain.evidence]}, "idempotency_key": key}


def link_body(domain: FakeDomain, key: str = "p3c1a-link-0001") -> dict:
    return {"case_id": domain.case, "case_revision_id": domain.case_revision, "case_event_id": domain.case_event,
            "idempotency_key": key}


# ---- the 10 commands, every case_event kind as its own row ------------------------------------------------------

#: command key -> (prepare(api) -> (route path, person body), table written, the route's shape code, duplicate code)
def _event(kind: str, payload: Callable[[Api, str], dict], seed: Callable[[Api], str]):
    def prepare(api: Api) -> tuple[str, dict]:
        cid = seed(api)
        return f"work/cases/{cid}/events", event_body(kind, payload(api, cid), f"p3c1a-{kind.lower()}-0001")
    return prepare


def _incident(api: Api) -> str:
    return api.seed_case()["id"]


def _closed_incident(api: Api) -> str:
    cid = _incident(api)
    api.seed_event(cid, "CLOSE", {"reason": "Resolved"})
    return cid


def _request(api: Api) -> str:
    return api.seed_case("MAINTENANCE_REQUEST")["id"]


def _working_request(api: Api) -> str:
    cid = _request(api)
    api.seed_event(cid, "ASSIGN", {"assignee": "crew"})
    api._record = api.seed_record(cid)
    return cid


def _revision(api: Api) -> tuple[str, dict]:
    created = api.seed_case()
    return f"work/cases/{created['id']}/revisions", {
        "supersedes_revision_id": created["revision"]["id"], "title": "Starter fault (corrected)",
        "narrative": "Seen at the morning round.", "reason": "Title", "occurred_at": iso(NOW - timedelta(minutes=5)),
        "idempotency_key": "p3c1a-revision-0001"}


def _record(api: Api) -> tuple[str, dict]:
    return f"work/cases/{_request(api)}/records", record_body()


W = ("WORK_INPUT_INVALID", "WORK_EVENT_DUPLICATE_KEY")
COMMANDS: dict[str, tuple[Callable[[Api], tuple[str, dict]], str, tuple[str, str]]] = {
    "work.case_create": (lambda api: ("work/cases", case_body()), "work_case", W),
    "work.case_event.ASSIGN": (_event("ASSIGN", lambda a, c: {"assignee": "crew"}, _incident), "work_event", W),
    "work.case_event.COMMENT": (_event("COMMENT", lambda a, c: {"text": "Checked"}, _incident), "work_event", W),
    "work.case_event.CLOSE": (_event("CLOSE", lambda a, c: {"reason": "Fixed"}, _incident), "work_event", W),
    "work.case_event.REOPEN": (_event("REOPEN", lambda a, c: {"reason": "Again"}, _closed_incident), "work_event", W),
    "work.case_event.CANCEL": (_event("CANCEL", lambda a, c: {"reason": "Moot"}, _request), "work_event", W),
    "work.case_event.COMPLETE": (_event("COMPLETE", lambda a, c: {"maintenance_record_id": a._record},
                                        _working_request), "work_event", W),
    "work.case_revision": (_revision, "work_case_revision", W),
    "work.maintenance_record": (_record, "maintenance_record", W),
    "work.maintenance_plan": (lambda api: ("work/plans", plan_body()), "maintenance_plan", W),
    "work.operational_record": (lambda api: ("work/operational-records", oprec_body()), "operational_record", W),
    "work.operational_entry": (lambda api: ("work/operational-entries", entry_body()), "operational_record",
                               ("OPREC_ENTRY_INVALID", "WORK_EVENT_DUPLICATE_KEY")),
    "domain.create": (lambda api: ("domain-work/actions", action_body(api.domain)), "domain_action",
                      ("DOMAIN_INTENT_INVALID", "DOMAIN_INTENT_CONFLICT")),
    "domain.intent": (lambda api: (f"domain-work/actions/{api.seed_action()}/intents", intent_body(api.domain)),
                      "domain_action_intent", ("DOMAIN_INTENT_INVALID", "DOMAIN_INTENT_CONFLICT")),
    "domain.case_link": (lambda api: (f"domain-work/actions/{api.seed_action()}/case-links", link_body(api.domain)),
                         "domain_action_case_link", ("DOMAIN_INTENT_INVALID", "DOMAIN_INTENT_BASIS_CHANGED")),
}
ALL = sorted(COMMANDS)
#: A person per role, at Kobo: a Site manager, a field technician and a finance lead.
HOLDER = {SM: "peter", FT: "fatma", FIN: "fiona"}


def person_rows(api: Api, table: str) -> list[dict]:
    return [r for r in api.written(table) if r["actor_kind"] == "USER"]


def detail(response) -> dict:
    return response.json()["detail"]


# ---- the role table --------------------------------------------------------------------------------------------

def test_command_roles_is_the_spec_table() -> None:
    assert COMMAND_ROLES == SPEC_ROLES
    assert set(COMMANDS) == {k for k in SPEC_ROLES if not k.startswith(("commercial.", "action.", "structure.", "decision."))}
    for other in ("work.case_event.VERIFIED", "work.case_event.CREATED", "work.case_event.?"):
        assert roles_of(other) == (SM,)


# ---- role, Site binding and the stored actor -------------------------------------------------------------------

@pytest.mark.parametrize("command", ALL)
def test_each_listed_role_is_admitted_and_recorded_under_the_person(people, command) -> None:
    prepare, table, _ = COMMANDS[command]
    for role in SPEC_ROLES[command]:
        api = Api(people)
        path, body = prepare(api)
        who = HOLDER[role]
        r = api.post(path, body, who)
        assert r.status_code == 201, (role, r.text)
        rows = person_rows(api, table)
        if command == "work.case_create":  # P4: all three of a create's rows carry the person
            rows += person_rows(api, "work_case_revision") + person_rows(api, "work_event")
            assert len(rows) == 3
        else:
            assert len(rows) == 1
        pid, sid = people.ids[who], people.sessions[who]
        for row in rows:
            assert row["actor_id"] == f"person:{pid}" and row["person_id"] == str(pid)
            assert row["attestation"] == f"person={pid};session={sid};role={role}"
            if table.startswith("domain"):
                assert "authorization_basis" not in row  # R4: the domain tables have none; the role is attested
            else:
                assert row["authorization_basis"] == f"PERSON_ROLE:{role}"


@pytest.mark.parametrize("command", [c for c in ALL if set(SPEC_ROLES[c]) == {SM, FT}])
def test_the_admitting_role_is_the_first_match_in_table_order(people, command) -> None:
    prepare, table, _ = COMMANDS[command]
    api = Api(people)
    path, body = prepare(api)
    assert api.post(path, body, "tess").status_code == 201
    row = person_rows(api, table)[0]
    assert row["attestation"].endswith(f";role={SPEC_ROLES[command][0]}")


@pytest.mark.parametrize("command", ALL)
def test_a_person_without_a_listed_role_or_at_another_site_is_403(people, command) -> None:
    prepare, table, _ = COMMANDS[command]
    refused_by = ["ana", "kim"]  # analyst only; a Site manager of Kisiwa posting to Kobo
    refused_by += [HOLDER[r] for r in (SM, FT, FIN) if r not in SPEC_ROLES[command] and r != SM]
    for who in refused_by:
        api = Api(people)
        path, body = prepare(api)
        before = {t: len(rows) for t, rows in {**api.work.rows, **api.domain.rows}.items()}
        r = api.post(path, body, who)
        assert r.status_code == 403, (who, r.text)
        assert detail(r) == {"code": "PERSON_ROLE_REQUIRED", "message": "Your role cannot do this here.",
                             "params": {"roles": list(SPEC_ROLES[command])}}, who
        assert {t: len(rows) for t, rows in {**api.work.rows, **api.domain.rows}.items()} == before


@pytest.mark.parametrize("command", ALL)
def test_a_person_of_another_tenant_gets_the_unknown_site_404_byte_for_byte(people, command) -> None:
    prepare, table, _ = COMMANDS[command]
    api = Api(people)
    path, body = prepare(api)
    r = api.post(path, body, "hugo")  # Beta's Site manager and field technician
    unknown = Api(people, scope={}).post(path, body, "hugo")  # the same request where Kobo is not a known Site
    assert r.status_code == unknown.status_code == 404
    assert r.content == unknown.content and dict(r.headers) == dict(unknown.headers)
    assert detail(r) == {"code": "SITE_NOT_FOUND", "message": f"No imported Site '{KOBO}' in this tenant."}
    assert person_rows(api, table) == []


@pytest.mark.parametrize("command", ALL)
def test_a_body_carrying_an_actor_gets_the_routes_shape_code(people, command) -> None:
    prepare, table, (shape, _) = COMMANDS[command]
    api = Api(people)
    path, body = prepare(api)
    for extra in ({"actor": SERVICE_ACTOR}, {"actor": {"kind": "USER", "id": "person:x", "attestation": "x"}},
                  {"authorization_basis": "SITE_WORK_WRITE:x"}):
        r = api.post(path, {**body, **extra}, "peter")
        assert r.status_code == 422 and detail(r)["code"] == shape and set(detail(r)) == {"code", "message"}, r.text
    assert person_rows(api, table) == []


# ---- hash identity (R1, D-3C1.8) -------------------------------------------------------------------------------

@pytest.mark.parametrize("command", ALL)
def test_the_same_person_replays_after_signing_in_again_another_person_is_409(people, command) -> None:
    prepare, table, (_, duplicate) = COMMANDS[command]
    first, second = ("peter", "sam") if SM in SPEC_ROLES[command] else ("fatma", "tess")
    api = Api(people)
    path, body = prepare(api)
    made = api.post(path, body, first)
    assert made.status_code == 201, made.text
    again = api.post(path, body, "peter2" if first == "peter" else first)
    assert again.status_code == 200 and again.json() == made.json(), again.text
    other = api.post(path, body, second)
    assert other.status_code == 409 and detail(other)["code"] == duplicate, other.text
    assert len(person_rows(api, table)) == 1  # neither the replay nor the refusal wrote a row


def test_the_hashed_actor_is_the_kind_and_the_person_only(people) -> None:
    api = Api(people)
    assert api.post("work/plans", plan_body(), "peter").status_code == 201
    pid = people.ids["peter"]
    canon = {**plan_body(), "next_due_at": None, "next_due_hours": None,
             "actor": {"kind": "USER", "id": f"person:{pid}"}}
    assert api.written("maintenance_plan")[0]["payload_sha256"] == sha({"site_id": str(people.kobo)}, canon)


def test_service_hashes_are_byte_identical_to_todays_form(people) -> None:
    """Today's path: the hashed actor stays `{kind,id,attestation}` (B6), recomputed here independently."""
    api = Api(people)
    for path, body, table in (("work/plans", plan_body("svc-plan-0001"), "maintenance_plan"),
                              ("work/operational-records", oprec_body("svc-oprec-0001"), "operational_record")):
        assert api.post(path, {**body, "actor": SERVICE_ACTOR}).status_code == 201
        row = api.written(table)[-1]
        assert row["actor_kind"] == "SERVICE" and row["person_id"] is None
        assert row["authorization_basis"] == f"SITE_WORK_WRITE:{PRINCIPAL}"
        canon = {**body, "actor": SERVICE_ACTOR}
        if table == "maintenance_plan":
            canon.update(next_due_at=None, next_due_hours=None)
        assert row["payload_sha256"] == sha({"site_id": str(people.kobo)}, canon)
    created = api.post("work/cases", {**case_body(key="svc-case-0001"), "actor": SERVICE_ACTOR})
    assert created.status_code == 201
    assert api.written("work_case")[-1]["create_payload_sha256"] == sha(
        {"site_id": str(people.kobo)}, {**case_body(key="svc-case-0001"), "actor": SERVICE_ACTOR})
    assert api.post("domain-work/actions", {**action_body(api.domain, "svc-action-0001"),
                                            "actor": SERVICE_ACTOR}).status_code == 201
    row = api.written("domain_action")[-1]
    path = {"tenant_id": str(people.acme), "site_id": str(people.kobo), "action_id": None, "command": d.CMD_ACTION}
    expected = {k: v for k, v in action_body(api.domain, "svc-action-0001").items()}
    assert row["person_id"] is None and row["payload_sha256"] == sha(path, {**expected, "actor": SERVICE_ACTOR})


# ---- the switch, no person, no accounts, store errors (R10, R11) -----------------------------------------------

def _service_body(api: Api, command: str) -> tuple[str, Any]:
    path, body = COMMANDS[command][0](api)
    return path, (body if command == "work.operational_entry" else {**body, "actor": SERVICE_ACTOR})


@pytest.mark.parametrize("command", ALL)
def test_switch_on_without_a_person_is_401_and_off_is_todays_path(people, command) -> None:
    api = Api(people, require=True)
    path, body = _service_body(api, command)
    r = api.post(path, body)
    assert r.status_code == 401 and r.headers["www-authenticate"] == "Bearer", r.text
    assert detail(r) == {"code": "PERSON_REQUIRED", "message": "Sign in to continue."}
    api = Api(people)
    path, body = _service_body(api, command)
    r = api.post(path, body)
    assert r.status_code == 201, r.text
    table = COMMANDS[command][1]
    assert person_rows(api, table) == [] and api.written(table)[-1]["person_id"] is None


def test_an_expired_or_revoked_cookie_is_no_person(people) -> None:
    signed = people.svc.sign_in("sam@acme.example", PW)
    people.svc.sign_out(signed.token)
    api = Api(people, require=True)
    r = api.client.post(f"/api/sites/{KOBO}/work/plans", json=plan_body(),
                        headers={"cookie": f"{COOKIE}={signed.token}"})
    assert r.status_code == 401 and detail(r)["code"] == "PERSON_REQUIRED"


@pytest.mark.parametrize("command", ALL)
def test_with_no_account_service_nobody_is_signed_in(people, command) -> None:
    api = Api(people, accounts=False)
    path, body = _service_body(api, command)
    assert api.post(path, body, "peter").status_code == 201  # Peter's cookie is ignored: today's path
    assert person_rows(api, COMMANDS[command][1]) == []
    r = Api(people, accounts=False, require=True).post(path, body, "peter")
    assert r.status_code == 401 and detail(r)["code"] == "PERSON_REQUIRED"


class AccountsDown(Exception):
    pass


class BrokenAccounts:
    def resolve(self, token):
        raise AccountsDown("store down")


@pytest.mark.parametrize("command", ALL)
def test_an_account_store_error_is_503_even_with_the_switch_off(people, command) -> None:
    api = Api(people, accounts=BrokenAccounts(), unavailable=(AccountsDown,))
    path, body = _service_body(api, command)
    r = api.post(path, body, "peter")
    assert r.status_code == 503 and detail(r) == {"code": "WORK_STORE_UNAVAILABLE",
                                                   "message": "Work records could not be read or saved."}


# ---- the feature switches still apply to people (R6, D-3C1.12) -------------------------------------------------

@pytest.mark.parametrize("command", ALL)
def test_with_no_principal_composed_a_person_is_refused_as_today(people, command) -> None:
    feature = {"entry": False} if command == "work.operational_entry" else {"principal": False}
    api = Api(people, **feature)
    path, body = COMMANDS[command][0](api)
    unsigned = api.post(path, body if command == "work.operational_entry" else {**body, "actor": SERVICE_ACTOR})
    r = api.post(path, body, HOLDER[SPEC_ROLES[command][0]])
    for answer in (unsigned, r):
        assert answer.status_code == 403 and detail(answer) == {
            "code": "WORK_WRITE_FORBIDDEN", "message": "This actor cannot change work at this site."}, answer.text
    assert person_rows(api, COMMANDS[command][1]) == []


def test_a_client_user_actor_stays_refused_on_todays_path(people) -> None:
    api = Api(people)
    r = api.post("work/plans", {**plan_body(), "actor": {"kind": "USER", "id": "operator-1", "attestation": "x"}})
    assert r.status_code == 403 and detail(r)["code"] == "WORK_USER_AUTH_REQUIRED"


# ---- the switch's configuration (R10) --------------------------------------------------------------------------

def test_require_person_is_off_by_default_and_strict(monkeypatch) -> None:
    monkeypatch.delenv("ASSETOPS_REQUIRE_PERSON", raising=False)
    assert require_person() is False
    for value, expected in (("off", False), ("on", True)):
        monkeypatch.setenv("ASSETOPS_REQUIRE_PERSON", value)
        assert require_person() is expected
    for value in ("ON", "true", "1", ""):
        monkeypatch.setenv("ASSETOPS_REQUIRE_PERSON", value)
        with pytest.raises(ConfigurationError):
            require_person()
