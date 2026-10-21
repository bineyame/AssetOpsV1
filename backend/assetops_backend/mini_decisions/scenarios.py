"""W4-03 unit 2b: the authored mini-grid scenario commands and list read.

`.agent/W4-03-build-spec.md`: "API, exact wire, ordering and errors"; closure 1 Q1-Q3 (actor, attestation, literal
request/response shapes, canonical hash, retry), Q12-Q16 (one REPEATABLE READ snapshot, head at cutoff, list
envelope, selection token, cursor); closure 2 Q1 (injected server principal); closure 4 S5, S9 (the W4-02 basis is
read only through `MiniDepthRead.read_selected_renewable_basis`), S15 (optional creation-time bounds), S20
(provenance), N6 (W4-01 validators imported, not copied); u2 (`narrative`) and u2b readings.

Writes: scope, write grant and the server principal are checked by the router and `admit` before any body is
parsed; then the closed shape (422), a USER actor (403), the attestation (422), the canonical hash and idempotency
lookup (exact retry 200 / changed body 409), and only then the predecessor and pin checks against the selected
W4-02 heads at command DB time. A refused command writes nothing. All SQL lives in `store.py`.
"""

from __future__ import annotations

import base64
import binascii
import hashlib
import json
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, Callable, Mapping, Sequence
from uuid import UUID, uuid4

from assetops_backend.mini_decisions import scenario_rules as rules
from assetops_backend.mini_decisions.model import GRANT_PREFIX, DecisionPrincipal, DecisionRefused, invalid
from assetops_backend.mini_decisions.store import (
    MiniDecisionStoreUnavailable,
    MiniDecisionWriteRefused,
    PostgresMiniDecisionStore,
)
from assetops_backend.mini_depth.read import (
    MiniDepthRead,
    MiniReadRefused,
    MiniReadUnavailable,
    iso,
    renewable_revisions,
)
from assetops_backend.work import model as work
from assetops_backend.work.model import WorkRefused

SCHEMA_COMMAND = "mini-scenario-command-1"
SCHEMA_WRITE = "mini-scenario-write-1"
SCHEMA_LIST = "mini-scenarios-1"
SELECTION_VERSION = "mini-decisions-selection/1"
ROUTE = "financials/scenarios"
EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)
PAGE_DEFAULT, PAGE_MAX, MAX_PINS = 50, 100, 5
COMPUTED = (rules.ENERGY_ONLY, rules.GROSS_SCENARIO)
#: u2c PR-4.3: the read-gate codes of a pin whose selected head matches (W4-02 states reused).
GATE_CODES = {"PENDING_RECOMPUTE": "RECOMPUTE_PENDING", "STALE_SOURCE": "SOURCE_STALE"}


def _shape(fn: Callable[..., Any], *args: Any) -> Any:
    """A W4-01 validator (N6: imported, not copied) with its refusal mapped to `DECISION_INPUT_INVALID`."""
    try:
        return fn(*args)
    except WorkRefused:
        raise invalid() from None


def scenario_code(public_no: int) -> str:
    """`SCN-` + at least six digits; never truncated above 999999 (closure 1 Q17-Q30)."""
    return f"SCN-{int(public_no):06d}"


def admit(principal: DecisionPrincipal | None, tenant_id: UUID, site_id: UUID) -> DecisionPrincipal:
    """Closure 2 Q1 / closure 4 B2: the server principal must exist, be SERVICE, name this exact tenant/Site and carry
    its own `SITE_DECISION_WRITE:<id>` grant; otherwise 403 before any body is read."""
    if (principal is None or principal.kind != "SERVICE" or (principal.tenant_id, principal.site_id) != (tenant_id, site_id)
            or principal.grant != GRANT_PREFIX + principal.id):
        raise DecisionRefused("DECISION_WRITE_FORBIDDEN")
    return principal


def authorize(actor: Mapping[str, Any], principal: DecisionPrincipal) -> dict[str, str]:
    """Closure 1 Q1-Q3: a USER actor is 403 in development; a SERVICE attestation must name the authenticated
    service (W4-01's `ATTESTATION` pattern). The stored basis is the server grant, never a client field."""
    if actor["kind"] == "USER":
        raise DecisionRefused("DECISION_USER_AUTH_REQUIRED")
    match = work.ATTESTATION.match(actor["attestation"])
    if (match is None or any(g != g.strip() or not g.strip() for g in match.groups())
            or actor["id"] != principal.id or "service:" + match.group(1) != actor["id"]):
        raise DecisionRefused("DECISION_ATTESTATION_INVALID")
    return {"actor_kind": "SERVICE", "actor_id": actor["id"], "attestation": actor["attestation"],
            "authorization_basis": principal.grant}


def parse_pins(value: Any) -> list[dict[str, Any]]:
    """u2b reading 1: 0-5 exact `(local_day, selection_seq, mini_revision_id)` tuples on distinct consecutive
    Site-local days, sorted by day; a duplicate day or revision, a gap, or a sixth tuple is 422."""
    if not isinstance(value, list) or len(value) > MAX_PINS:
        raise invalid()
    pins = []
    for item in value:
        pin = _shape(work.closed, item, ("local_day", "selection_seq", "mini_revision_id"))
        day, seq = pin["local_day"], pin["selection_seq"]
        if not isinstance(day, str) or isinstance(seq, bool) or not isinstance(seq, int) or seq <= 0:
            raise invalid()
        try:
            parsed = date.fromisoformat(day)
        except ValueError:
            raise invalid() from None
        if parsed.isoformat() != day:
            raise invalid()
        pins.append({"local_day": day, "selection_seq": seq,
                     "mini_revision_id": _shape(work.uuid_text, pin["mini_revision_id"]).lower()})
    pins.sort(key=lambda p: p["local_day"])
    days = [date.fromisoformat(p["local_day"]) for p in pins]
    if (len({p["mini_revision_id"] for p in pins}) != len(pins)
            or any(b - a != timedelta(days=1) for a, b in zip(days, days[1:]))):
        raise invalid()
    return pins


def parse_command(body: Any, *, correction: bool) -> dict[str, Any]:
    """The closed `mini-scenario-command-1` shape, canonical (sorted assumptions and pins, trimmed text)."""
    required = ["schema_version", "idempotency_key", "actor", "name", "kind", "assumptions", "pinned_selection",
                "narrative"]
    if correction:
        required += ["supersedes_revision_id", "correction_reason"]
    b = _shape(work.closed, body, required)
    if b["schema_version"] != SCHEMA_COMMAND:
        raise invalid()
    actor = _shape(work.actor_shape, b["actor"])
    canon: dict[str, Any] = {
        "schema_version": SCHEMA_COMMAND, "idempotency_key": _shape(work.idempotency_key, b["idempotency_key"]),
        "actor": {"kind": actor["kind"], "id": actor["id"], "attestation": actor["attestation"]},
        "name": _shape(work.text_value, b["name"], 1, 160), "kind": b["kind"],
        "assumptions": rules.assumptions(b["kind"], b["assumptions"]),
        "pinned_selection": parse_pins(b["pinned_selection"]),
        "narrative": _shape(work.text_value, b["narrative"], 1, 2000)}
    if correction:
        canon["supersedes_revision_id"] = _shape(work.uuid_text, b["supersedes_revision_id"]).lower()
        canon["correction_reason"] = _shape(work.text_value, b["correction_reason"], 1, 500)
    return canon


def _decimal(text: str | None) -> str | None:
    """u2c PR-4.4: the stored exact decimal as a normalized plain base-10 JSON string; null stays null."""
    return None if text is None else rules.decimal_text(Decimal(text))


def _instant(value: str, code: str) -> datetime:
    try:
        at = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        raise DecisionRefused(code) from None
    if at.tzinfo is None:
        raise DecisionRefused(code)
    return at.astimezone(timezone.utc)


def encode_cursor(payload: Mapping[str, Any]) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def decode_cursor(value: str) -> dict[str, Any]:
    try:
        payload = json.loads(base64.urlsafe_b64decode(value + "=" * (-len(value) % 4)).decode("utf-8"))
        ok = (isinstance(payload, dict) and payload.get("v") == 1
              and all(isinstance(payload.get(k), str)
                      for k in ("tenant_id", "site_id", "route", "from", "to", "known_at", "selection_token"))
              and isinstance(payload.get("after"), list) and len(payload["after"]) == 2
              and all(isinstance(x, str) for x in payload["after"]))
        if ok:
            for key in ("from", "to", "known_at"):
                _instant(payload[key], "INVALID_CURSOR")
            _instant(payload["after"][0], "INVALID_CURSOR")
            UUID(payload["after"][1])
    except (binascii.Error, ValueError, UnicodeDecodeError, TypeError, DecisionRefused):
        ok = False
    if not ok:
        raise DecisionRefused("INVALID_CURSOR")
    return payload


def parse_list(start: str | None, end: str | None, limit: str | None, known: Sequence[str],
               cursor: str | None) -> dict[str, Any]:
    """S15 and Q12-Q16, in order: window (both bounds or neither), limit, `known_at`, cursor."""
    if (start is None) != (end is None):
        raise DecisionRefused("INVALID_WINDOW")
    lo = hi = None
    if start is not None and end is not None:
        lo, hi = _instant(start, "INVALID_WINDOW"), _instant(end, "INVALID_WINDOW")
        if not lo < hi:
            raise DecisionRefused("INVALID_WINDOW")
    size = PAGE_DEFAULT
    if limit not in (None, ""):
        try:
            size = int(limit)  # type: ignore[arg-type]
        except ValueError:
            size = 0
        if not 1 <= size <= PAGE_MAX:
            raise DecisionRefused("INVALID_LIMIT")
    if len(known) > 1:
        raise DecisionRefused("INVALID_KNOWN_AT")
    known_at = _instant(known[0], "INVALID_KNOWN_AT") if known else None
    return {"from": lo, "to": hi, "limit": size, "known_at": known_at,
            "cursor": None if cursor in (None, "") else decode_cursor(cursor)}


class ScenarioService:
    """Scenario create/correct (201/200/refusal) and the `mini-scenarios-1` list read."""

    def __init__(self, store: PostgresMiniDecisionStore, reader: MiniDepthRead, *,
                 test_read_clock_override: Callable[[], datetime] | None = None) -> None:
        self._store = store
        self._reader = reader
        self.test_read_clock_override = test_read_clock_override

    # --- commands -----------------------------------------------------------------------------------------------

    def create(self, tenant_id: UUID, site_id: UUID, principal: DecisionPrincipal | None,
               body: Any) -> tuple[int, dict[str, Any]]:
        principal = admit(principal, tenant_id, site_id)
        cmd = parse_command(body, correction=False)
        actor = authorize(cmd["actor"], principal)
        sha = work.command_sha256({"site_id": str(site_id), "route": ROUTE}, cmd)

        def write(c: Any) -> tuple[int, dict[str, Any]]:
            prior = self._store.scenario_by_create_key(c, tenant_id, site_id, cmd["idempotency_key"])
            if prior is not None:
                if prior["create_payload_sha256"] != sha:
                    raise DecisionRefused("DECISION_DUPLICATE_KEY")
                first = self._store.scenario_revisions(c, tenant_id, site_id, prior["id"])[0]
                return 200, self._write_body(prior["id"], prior["public_no"], first)
            pins = cmd["pinned_selection"]
            calculation = self._calculation(c, tenant_id, site_id, cmd, pins)
            scenario_id, revision_id = uuid4(), uuid4()
            public_no = self._store.insert_scenario(c, {
                "id": scenario_id, "tenant_id": tenant_id, "site_id": site_id, "create_key": cmd["idempotency_key"],
                "create_payload_sha256": sha, "create_actor_id": actor["actor_id"]})
            self._insert_revision(c, tenant_id, site_id, scenario_id, revision_id, 1, None, cmd, actor, sha,
                                  calculation)
            first = self._store.scenario_revisions(c, tenant_id, site_id, scenario_id)[0]
            return 201, self._write_body(scenario_id, public_no, first)

        try:
            return self._write(write)
        except MiniDecisionWriteRefused:
            return self._write(write)  # a concurrent identical-key create committed first: the lookup answers

    def correct(self, tenant_id: UUID, site_id: UUID, principal: DecisionPrincipal | None, scenario_id: str,
                body: Any) -> tuple[int, dict[str, Any]]:
        principal = admit(principal, tenant_id, site_id)
        try:
            root_id = str(UUID(scenario_id)).lower()
        except ValueError:
            raise DecisionRefused("DECISION_NOT_FOUND") from None
        cmd = parse_command(body, correction=True)
        actor = authorize(cmd["actor"], principal)
        sha = work.command_sha256({"site_id": str(site_id), "route": ROUTE, "root_id": root_id}, cmd)

        def write(c: Any) -> tuple[int, dict[str, Any]]:
            root = self._store.lock_scenario(c, tenant_id, site_id, root_id)
            if root is None:
                raise DecisionRefused("DECISION_NOT_FOUND")
            revisions = self._store.scenario_revisions(c, tenant_id, site_id, root["id"])
            prior = next((r for r in revisions if r["idempotency_key"] == cmd["idempotency_key"]), None)
            if prior is not None:
                if prior["payload_sha256"] != sha:
                    raise DecisionRefused("DECISION_DUPLICATE_KEY")
                return 200, self._write_body(root["id"], root["public_no"], prior)
            predecessor = next((r for r in revisions if str(r["id"]).lower() == cmd["supersedes_revision_id"]), None)
            if predecessor is None:
                raise DecisionRefused("DECISION_LINK_SCOPE_INVALID")
            head = revisions[-1]
            if predecessor["id"] != head["id"]:
                raise DecisionRefused("DECISION_CORRECTION_CONFLICT")
            calculation = self._calculation(c, tenant_id, site_id, cmd, cmd["pinned_selection"])
            revision_id = uuid4()
            self._insert_revision(c, tenant_id, site_id, root["id"], revision_id, head["revision_no"] + 1,
                                  head["id"], cmd, actor, sha, calculation)
            stored = self._store.scenario_revisions(c, tenant_id, site_id, root["id"])[-1]
            return 201, self._write_body(root["id"], root["public_no"], stored)

        return self._write(write)

    def _write(self, work_: Callable[[Any], tuple[int, dict[str, Any]]]) -> tuple[int, dict[str, Any]]:
        try:
            with self._store.transaction() as c:
                return work_(c)
        except (MiniDecisionStoreUnavailable, MiniReadUnavailable) as error:
            raise DecisionRefused("DECISION_STORE_UNAVAILABLE") from error

    @staticmethod
    def _write_body(scenario_id: Any, public_no: int, revision: Mapping[str, Any]) -> dict[str, Any]:
        previous = revision["supersedes_revision_id"]
        return {"schema_version": SCHEMA_WRITE, "id": str(scenario_id), "code": scenario_code(public_no),
                "revision_id": str(revision["id"]), "revision_no": revision["revision_no"],
                "supersedes_revision_id": None if previous is None else str(previous),
                "recorded_at": iso(revision["recorded_at"])}

    def _insert_revision(self, c: Any, tenant_id: UUID, site_id: UUID, scenario_id: Any, revision_id: UUID,
                         revision_no: int, previous: Any, cmd: Mapping[str, Any], actor: Mapping[str, str], sha: str,
                         calculation: dict[str, Any]) -> None:
        pins = cmd["pinned_selection"]
        self._store.insert_scenario_revision(c, {
            "id": revision_id, "tenant_id": tenant_id, "site_id": site_id, "scenario_id": scenario_id,
            "revision_no": revision_no, "supersedes_revision_id": previous, "name": cmd["name"], "kind": cmd["kind"],
            "narrative": cmd["narrative"], "assumptions": cmd["assumptions"],
            "pinned_mini_revision_ids": sorted(p["mini_revision_id"] for p in pins),
            "pinned_selection_hours": pins, "calculation": calculation,
            "correction_reason": cmd.get("correction_reason"), **actor,
            "idempotency_key": cmd["idempotency_key"], "payload_sha256": sha})

    def _calculation(self, c: Any, tenant_id: UUID, site_id: UUID, cmd: Mapping[str, Any],
                     pins: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
        """u2b reading 1: each pin must be a renewable revision of this tenant/Site (else 422) and equal the selected
        head `(selection_seq, mini_revision_id)` of its day at command DB time (else 409); the stored calculation
        uses those exact selected day rows."""
        days: list[rules.DayRow] = []
        if pins:
            found = renewable_revisions(c, tenant_id, site_id, [p["mini_revision_id"] for p in pins])
            if any(p["mini_revision_id"] not in found for p in pins):
                raise DecisionRefused("DECISION_LINK_SCOPE_INVALID")
            try:
                basis = self._reader.read_selected_renewable_basis(
                    c, tenant_id=tenant_id, site_id=site_id, days=[date.fromisoformat(p["local_day"]) for p in pins],
                    known=self._store.db_now(c), historical=False)
            except MiniReadRefused:
                raise invalid() from None
            for pin, day in zip(pins, basis["days"]):
                if (day["selection_seq"], day["mini_revision_id"]) != (pin["selection_seq"], pin["mini_revision_id"]):
                    raise DecisionRefused("DECISION_BASIS_CHANGED")
                days.append(rules.DayRow(day["local_day"], day["decision"], day["opportunity_kwh"]))
        return rules.calculate(cmd["kind"], cmd["assumptions"], days)

    # --- list read ----------------------------------------------------------------------------------------------

    def list(self, tenant_id: UUID, site_id: UUID, request: Mapping[str, Any], access_basis: str) -> dict[str, Any]:
        try:
            with self._store.snapshot() as c:
                read_time = self._store.db_now(c)
                if self.test_read_clock_override is not None:
                    read_time = self.test_read_clock_override()
                return self._list(c, tenant_id, site_id, request, access_basis, read_time)
        except (MiniDecisionStoreUnavailable, MiniReadUnavailable, MiniReadRefused) as error:
            raise DecisionRefused("DECISION_STORE_UNAVAILABLE") from error

    def _list(self, c: Any, t: UUID, s: UUID, request: Mapping[str, Any], access_basis: str,
              read_time: datetime) -> dict[str, Any]:
        explicit = request["known_at"]
        if explicit is not None and explicit > read_time:
            raise DecisionRefused("INVALID_KNOWN_AT")
        cursor = request["cursor"]
        if cursor is not None:
            # Page two reuses page one's effective bounds and cutoff; an explicit differing value is a changed basis.
            if (cursor["tenant_id"], cursor["site_id"], cursor["route"]) != (str(t), str(s), ROUTE):
                raise DecisionRefused("INVALID_CURSOR")
            for key in ("from", "to", "known_at"):
                if request[key] is not None and iso(request[key]) != cursor[key]:
                    raise DecisionRefused("DECISION_BASIS_CHANGED")
            lo, hi, known = (_instant(cursor[k], "INVALID_CURSOR") for k in ("from", "to", "known_at"))
            if known > read_time:
                raise DecisionRefused("DECISION_BASIS_CHANGED")
        else:
            lo = request["from"] if request["from"] is not None else EPOCH
            hi = request["to"] if request["to"] is not None else read_time + timedelta(microseconds=1)
            known = read_time if explicit is None else explicit
        historical = explicit is not None and known < read_time

        heads = self._store.scenario_heads(c, t, s, lo, hi, known)
        pinned_ids = sorted({p["mini_revision_id"] for h in heads for p in h["pinned_selection_hours"]})
        days = sorted({date.fromisoformat(p["local_day"]) for h in heads for p in h["pinned_selection_hours"]})
        basis = self._reader.read_selected_renewable_basis(c, tenant_id=t, site_id=s, days=days, known=known,
                                                           historical=historical)
        by_day = {d["local_day"]: d for d in basis["days"]}
        revisions = renewable_revisions(c, t, s, pinned_ids)
        if set(revisions) != set(pinned_ids):
            raise MiniDecisionStoreUnavailable("A stored scenario pin no longer names a renewable revision.")
        blocks = self._reader.provenance_blocks(
            c, tenant_id=t, site_id=s, selected_revision_ids=pinned_ids,
            selected_evidence_ids=[i for r in pinned_ids for i in revisions[r]["evidence_ids"]],
            pending_evidence_ids=basis["pending_evidence_ids"])

        token_rows = sorted(({"root_id": str(h["id"]), "selected_revision_id": str(h["revision_id"]),
                              "selected_selection_seq": None,
                              "linked_ids": [str(i) for i in h["pinned_mini_revision_ids"]]} for h in heads),
                            key=lambda r: r["root_id"])
        token = "sha256:" + hashlib.sha256(work.canonical_json({
            "version": SELECTION_VERSION, "tenant_id": str(t), "site_id": str(s), "route": ROUTE, "from": iso(lo),
            "to": iso(hi), "known_at": iso(known), "access_basis": access_basis, "rows": token_rows,
            "pending_job_ids": basis["pending_job_ids"]}).encode("utf-8")).hexdigest()
        if cursor is not None and cursor["selection_token"] != token:
            raise DecisionRefused("DECISION_BASIS_CHANGED")

        ordered = sorted(heads, key=lambda h: str(h["id"]))  # (recorded_at DESC, id ASC) by two stable sorts
        ordered.sort(key=lambda h: h["recorded_at"], reverse=True)
        if cursor is not None:
            after_at, after_id = _instant(cursor["after"][0], "INVALID_CURSOR"), cursor["after"][1]
            ordered = [h for h in ordered
                       if h["recorded_at"] < after_at or (h["recorded_at"] == after_at and str(h["id"]) > after_id)]
        page = ordered[:request["limit"]]
        next_cursor = None
        if len(ordered) > len(page):
            last = page[-1]
            next_cursor = encode_cursor({"v": 1, "tenant_id": str(t), "site_id": str(s), "route": ROUTE,
                                         "from": iso(lo), "to": iso(hi), "known_at": iso(known),
                                         "selection_token": token,
                                         "after": [iso(last["recorded_at"]), str(last["id"])]})
        # u2c PR-4.5: the W4-02 aggregate over every eligible root's pinned days (before paging); an empty union
        # asserts no current physical basis.
        currentness = basis["currentness"] if days else {"state": "HISTORICAL" if historical else "UNKNOWN",
                                                         "job_state": "NONE"}
        return {"schema_version": SCHEMA_LIST,
                "window": {"from": iso(lo), "to": iso(hi), "known_at": iso(known)},
                "status": "UNKNOWN", "currentness": currentness, **blocks,
                "total_count": len(heads),
                "rows": [self._row(c, t, s, h, by_day, revisions, historical) for h in page],
                "next_cursor": next_cursor, "selection_token": token}

    def _row(self, c: Any, t: UUID, s: UUID, head: Mapping[str, Any], by_day: Mapping[str, Mapping[str, Any]],
             revisions: Mapping[str, Mapping[str, Any]], historical: bool) -> dict[str, Any]:
        """u2b readings 2/3: the read gate per row (its own pins' heads, currentness and provenance) may withhold a
        stored computed calculation without changing it; `scenario_state` is independent of it."""
        stored = head["calculation"]
        pins = head["pinned_selection_hours"]
        codes: list[str] = []
        if stored.get("reason"):
            codes.append(stored["reason"])
        for pin in pins:
            day = by_day[pin["local_day"]]
            if day.get("mini_revision_id") is None or day["mini_revision_id"] != pin["mini_revision_id"]:
                codes.append("SELECTION_CHANGED")  # absent or different head; same revision, new seq is harmless
            elif day["state"] in GATE_CODES:
                codes.append(GATE_CODES[day["state"]])
        if pins:
            ids = [p["mini_revision_id"] for p in pins]
            selected = self._reader.provenance_blocks(
                c, tenant_id=t, site_id=s, selected_revision_ids=ids,
                selected_evidence_ids=[i for r in ids for i in revisions[r]["evidence_ids"]],
                pending_evidence_ids=None)["selected_source_provenance"]
            if selected["classification"] in ("UNKNOWN", "MIXED"):
                codes.append(f"SOURCE_CLASS_{selected['classification']}")
        state, energy, gross = stored["state"], stored["energy_kwh"], stored["gross_sales"]
        if state in COMPUTED and any(code != stored.get("reason") for code in codes):
            state, energy, gross = rules.WITHHELD, None, None
        return {
            "id": str(head["id"]), "code": scenario_code(head["public_no"]), "revision_id": str(head["revision_id"]),
            "name": head["name"], "kind": head["kind"], "narrative": head["narrative"],
            "authored_at": iso(head["recorded_at"]), "actor_id": head["actor_id"],
            "assumptions": head["assumptions"], "pinned_mini_revision_ids": list(head["pinned_mini_revision_ids"]),
            "scenario_state": "HISTORICAL" if historical else "DEFINED", "calculation_state": state,
            "energy_kwh": _decimal(energy),
            "gross_sales": None if gross is None else {"amount": _decimal(gross["amount"]),
                                                       "currency": gross["currency"], "basis": "SCENARIO"},
            "limitations": [{"code": code, "evidence_ids": []} for code in dict.fromkeys(codes)], "url": None}


__all__ = ["ROUTE", "SCHEMA_LIST", "SCHEMA_WRITE", "ScenarioService", "admit", "authorize", "decode_cursor",
           "encode_cursor", "parse_command", "parse_list", "parse_pins", "scenario_code"]
