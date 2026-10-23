"""W5-01b C4: authored cold scenario commands and the `cold-scenarios-1` list (`.agent/W5-01-build-spec.md` C4 card,
"C4 exact persisted schema and wire contract", "Reconciliation with C1q" and pre-flight rulings P-C4-6..23).

Writes, after the router's gate: the server principal (`mini_decisions.scenarios.admit`), the actor policy
(`authorize`), the closed body, then one REPEATABLE READ store transaction that answers an exact-key replay from the
stored hash and the prior resolved cutoff *before* resolving a basis, and otherwise resolves the selected basis with
`ColdDepthReadService.basis_on` on that same connection and appends. A refused command writes nothing. A unique or
serialization race retries once by rereading the key; a further race or store failure is 503
`DECISION_STORE_UNAVAILABLE`. The list reads one REPEATABLE READ READ ONLY snapshot whose `clock_timestamp()` is the
default `scenario_at`; the evidence `known_at` stays the selected assessment cutoff. No SQL here.
"""

from __future__ import annotations

import hashlib
from datetime import datetime
from typing import Any, Callable, Mapping
from uuid import UUID, uuid4

from assetops_backend.analytics.cold_depth import ColdDepthReadService
from assetops_backend.analytics.cold_reads import ColdCursorRefused, ColdReadUnavailable
from assetops_backend.cold_scenarios import rules
from assetops_backend.cold_scenarios.rules import refused
from assetops_backend.cold_scenarios.store import (
    ColdScenarioReadFailed,
    ColdScenarioStoreUnavailable,
    ColdScenarioWriteRefused,
    PostgresColdScenarioStore,
)
from assetops_backend.mini_decisions.model import DecisionPrincipal, DecisionRefused
from assetops_backend.mini_decisions.scenarios import admit, authorize, decode_cursor, encode_cursor
from assetops_backend.work import model as work

def _instant(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _iso(value: datetime | None) -> str | None:
    return None if value is None else work.iso(value)


def _store_unavailable() -> DecisionRefused:
    return refused("DECISION_STORE_UNAVAILABLE")


class ColdScenarioService:
    """Create/correct (201, exact replay 200, refusal) and the list read."""

    def __init__(self, store: PostgresColdScenarioStore, reads: Any) -> None:
        self._store = store
        self._depth = ColdDepthReadService(reads)

    # --- the selected basis -----------------------------------------------------------------------------------

    def _basis(self, c: Any, t: UUID, s: UUID, code: str, lo, hi, known_at) -> dict[str, Any]:
        """`basis_on` on the store connection; a selected-read failure is 503 `COLD_READ_UNAVAILABLE` and a
        future `known_at` its 422 `COLD_TIME_INVALID`."""
        try:
            return self._store.reading(lambda: self._depth.basis_on(c, t, s, code, lo, hi, known_at))
        except ColdCursorRefused as error:
            raise refused(error.code, str(error), error.status) from error
        except (ColdReadUnavailable, ColdScenarioReadFailed) as error:
            raise refused("COLD_READ_UNAVAILABLE", str(error), 503) from error

    @staticmethod
    def _authorable(basis: Mapping[str, Any]) -> dict[str, Any]:
        authored = basis["authored_basis"]
        if not authored["assessment_revision_ids"] or authored["foundation_revision_id"] is None:
            raise rules.invalid()
        return authored

    # --- commands ---------------------------------------------------------------------------------------------

    def create(self, t: UUID, s: UUID, code: str, principal: DecisionPrincipal | None, lo: datetime, hi: datetime,
               known_at: datetime | None, body: Any) -> tuple[int, dict[str, Any]]:
        principal = admit(principal, t, s)
        actor = authorize(rules.actor_of(body), principal)
        cmd = rules.parse_command(body, correction=False)
        lo_text, hi_text, known_text = work.iso(lo), work.iso(hi), _iso(known_at)

        def write(c: Any) -> tuple[int, dict[str, Any]]:
            prior = self._store.scenario_by_create_key(c, t, s, cmd["idempotency_key"])
            if prior is not None:
                first = self._store.scenario_revisions(c, t, s, prior["id"])[0]
                cutoff = known_text if known_text is not None else self._stored(first)["cutoff"]
                if rules.create_sha256(cmd, s, lo_text, hi_text, cutoff) != prior["create_payload_sha256"]:
                    raise refused("COLD_SCENARIO_IDEMPOTENCY_CONFLICT")
                return 200, self._write_body(prior["id"], prior["public_no"], first)
            authored = self._authorable(self._basis(c, t, s, code, lo, hi, known_at))
            sha = rules.create_sha256(cmd, s, authored["from"], authored["to"], authored["cutoff"])
            scenario_id, revision_id = uuid4(), uuid4()
            public_no = self._store.insert_scenario(c, {
                "id": scenario_id, "tenant_id": t, "site_id": s, "create_key": cmd["idempotency_key"],
                "create_payload_sha256": sha, "create_actor_id": actor["actor_id"],
                "actor_kind": actor["actor_kind"], "actor_id": actor["actor_id"]})
            revision = self._append(c, t, s, scenario_id, revision_id, 1, None, cmd, actor, authored, sha)
            return 201, self._write_body(scenario_id, public_no, revision)

        return self._write(write)

    def correct(self, t: UUID, s: UUID, code: str, principal: DecisionPrincipal | None, scenario_id: str,
                lo: datetime, hi: datetime, known_at: datetime | None, body: Any) -> tuple[int, dict[str, Any]]:
        principal = admit(principal, t, s)
        try:
            root_id = str(UUID(scenario_id)).lower()
        except ValueError:
            raise refused("DECISION_NOT_FOUND") from None
        actor = authorize(rules.actor_of(body), principal)
        cmd = rules.parse_command(body, correction=True)
        lo_text, hi_text, known_text = work.iso(lo), work.iso(hi), _iso(known_at)

        def write(c: Any) -> tuple[int, dict[str, Any]]:
            root = self._store.lock_scenario(c, t, s, root_id)
            if root is None:
                raise refused("DECISION_NOT_FOUND")
            revisions = self._store.scenario_revisions(c, t, s, root["id"])
            first = self._stored(revisions[0])
            if (first["from"], first["to"]) != (lo_text, hi_text):
                raise rules.invalid()  # a correction keeps revision 1's window exactly
            prior = next((r for r in revisions if r["idempotency_key"] == cmd["idempotency_key"]), None)
            if prior is not None:
                cutoff = known_text if known_text is not None else self._stored(prior)["cutoff"]
                if rules.correction_sha256(cmd, root_id, lo_text, hi_text, cutoff) != prior["payload_sha256"]:
                    raise refused("COLD_SCENARIO_IDEMPOTENCY_CONFLICT")
                return 200, self._write_body(root["id"], root["public_no"], prior)
            predecessor = next((r for r in revisions if str(r["id"]).lower() == cmd["supersedes_revision_id"]),
                               None)
            if predecessor is None:
                raise refused("DECISION_LINK_SCOPE_INVALID")
            head = revisions[-1]
            if predecessor["id"] != head["id"]:
                raise refused("COLD_SCENARIO_REVISION_CONFLICT")
            authored = self._authorable(self._basis(c, t, s, code, lo, hi, known_at))
            sha = rules.correction_sha256(cmd, root_id, authored["from"], authored["to"], authored["cutoff"])
            revision = self._append(c, t, s, root["id"], uuid4(), head["revision_no"] + 1, head["id"], cmd, actor,
                                    authored, sha)
            return 201, self._write_body(root["id"], root["public_no"], revision)

        return self._write(write)

    @staticmethod
    def _stored(revision: Mapping[str, Any]) -> dict[str, Any]:
        try:
            return rules.check_basis(revision["authored_basis"])
        except ValueError as error:
            raise ColdScenarioStoreUnavailable(str(error)) from error

    def _append(self, c: Any, t: UUID, s: UUID, scenario_id: Any, revision_id: UUID, revision_no: int,
                previous: Any, cmd: Mapping[str, Any], actor: Mapping[str, str], authored: Mapping[str, Any],
                sha: str) -> Mapping[str, Any]:
        self._store.insert_scenario_revision(c, {
            "id": revision_id, "tenant_id": t, "site_id": s, "scenario_id": scenario_id, "revision_no": revision_no,
            "supersedes_revision_id": previous, "name": cmd["name"], "kind": cmd["kind"],
            "assumptions": cmd["assumptions"], "authored_basis": dict(authored),
            "basis_sha256": rules.basis_sha256(authored), "formula_version": rules.FORMULA_VERSION,
            "correction_reason": cmd.get("correction_reason"), **actor,
            "idempotency_key": cmd["idempotency_key"], "payload_sha256": sha})
        return {"id": revision_id, "revision_no": revision_no}

    def _write(self, work_: Callable[[Any], tuple[int, dict[str, Any]]]) -> tuple[int, dict[str, Any]]:
        """One write transaction, retried once after a unique or serialization race (the retry rereads the key);
        a further race or any store failure is 503 `DECISION_STORE_UNAVAILABLE`, never a fabricated 409."""
        for attempt in (1, 2):
            try:
                with self._store.transaction() as c:
                    return work_(c)
            except ColdScenarioWriteRefused as error:
                if attempt == 2:
                    raise _store_unavailable() from error
            except ColdScenarioStoreUnavailable as error:
                raise _store_unavailable() from error
        raise _store_unavailable()  # pragma: no cover - the loop always returns or raises

    @staticmethod
    def _write_body(scenario_id: Any, public_no: int, revision: Mapping[str, Any]) -> dict[str, Any]:
        return {"schema_version": rules.SCHEMA_WRITE, "id": str(scenario_id).lower(),
                "code": rules.scenario_code(public_no), "revision_id": str(revision["id"]).lower(),
                "revision_no": revision["revision_no"]}

    # --- list read --------------------------------------------------------------------------------------------

    def list(self, t: UUID, s: UUID, code: str, lo: datetime | None, hi: datetime | None,
             known_at: datetime | None, scenario_at: datetime | None, limit: int | None,
             cursor: str | None) -> dict[str, Any]:
        page = None if cursor in (None, "") else self._decode(cursor, t, s)
        try:
            with self._store.snapshot() as c:
                return self._list(c, t, s, code, lo, hi, known_at, scenario_at, limit, page)
        except ColdScenarioStoreUnavailable as error:
            raise _store_unavailable() from error

    @staticmethod
    def _decode(value: str, t: UUID, s: UUID) -> dict[str, Any]:
        """The mini cursor codec with C4 code translation and the C4 bindings (`scenario_at`, `limit`, whether
        `known_at` was explicit)."""
        try:
            payload = decode_cursor(value)
            _instant(payload["scenario_at"])
            ok = (payload["route"] == rules.ROUTE and isinstance(payload["known_explicit"], bool)
                  and isinstance(payload["limit"], int) and not isinstance(payload["limit"], bool)
                  and 1 <= payload["limit"] <= rules.PAGE_MAX and payload["from"] is not None)
        except (DecisionRefused, KeyError, TypeError, ValueError, AttributeError):
            ok = False
        if not ok or (payload["tenant_id"], payload["site_id"]) != (str(t), str(s)):
            raise refused("COLD_SCENARIO_CURSOR_INVALID")
        return payload

    def _list(self, c: Any, t: UUID, s: UUID, code: str, lo, hi, known_at, scenario_at, limit,
              page: dict[str, Any] | None) -> dict[str, Any]:
        now = self._store.db_now(c)
        known_explicit = known_at is not None
        if page is not None:
            # Page two inherits page one's clocks, window and limit; an explicit different value is a changed basis.
            explicit = {"from": _iso(lo), "to": _iso(hi), "known_at": _iso(known_at),
                        "scenario_at": _iso(scenario_at), "limit": limit}
            if any(v is not None and v != page[k] for k, v in explicit.items()):
                raise refused("COLD_SCENARIO_CURSOR_BASIS_CHANGED")
            lo, hi = _instant(page["from"]), _instant(page["to"])
            known_explicit = page["known_explicit"]
            known_at = _instant(page["known_at"]) if known_explicit else None
            scenario_at, limit = _instant(page["scenario_at"]), page["limit"]
        if scenario_at is None:
            scenario_at = now
        elif scenario_at > now:
            raise refused("COLD_TIME_INVALID", "'scenario_at' is later than the current authored time.", 422)
        size = rules.PAGE_DEFAULT if limit is None else limit

        basis = self._basis(c, t, s, code, lo, hi, known_at)
        window, selection = basis["window"], basis["selection"]
        token = "sha256:" + hashlib.sha256(work.canonical_json(
            {"window": window, "selection": selection}).encode("utf-8")).hexdigest()
        if page is not None and (page["selection_token"] != token or page["known_at"] != window["known_at"]):
            raise refused("COLD_SCENARIO_CURSOR_BASIS_CHANGED")

        # Q-C5c item 3: a Site root whose revision 1 lacks from/to has no trustworthy window, so it poisons every list.
        if self._store.malformed_roots(c, t, s, scenario_at):
            raise _store_unavailable()
        rows: list[Mapping[str, Any]] = []
        count = 0
        if window["from"] is not None and window["known_at"] is not None:
            w_lo, w_hi, w_known = _instant(window["from"]), _instant(window["to"]), _instant(window["known_at"])
            # Q-C5b item 5: a candidate whose stored basis lacks from/to/cutoff is malformed history (503), checked
            # before the cutoff predicate so it never silently vanishes from the list.
            if self._store.malformed_candidates(c, t, s, w_lo, w_hi, scenario_at):
                raise _store_unavailable()
            after = None if page is None else (_instant(page["after"][0]), page["after"][1])
            rows = self._store.heads(c, t, s, w_lo, w_hi, w_known, scenario_at, after, size + 1)
            # Q-C5b item 2: every selected head in this snapshot, before cursor and limit.
            count = self._store.count_heads(c, t, s, w_lo, w_hi, w_known, scenario_at)
        historical_evidence = (window["committed_watermark"] is not None and window["known_at"] is not None
                               and _instant(window["known_at"]) < _instant(window["committed_watermark"]))
        items = [self._item(r, historical_evidence) for r in rows[:size]]
        next_cursor = None
        if len(rows) > size:
            last = rows[size - 1]
            next_cursor = encode_cursor({
                "v": 1, "tenant_id": str(t), "site_id": str(s), "route": rules.ROUTE, "from": window["from"],
                "to": window["to"], "known_at": window["known_at"], "known_explicit": known_explicit,
                "scenario_at": work.iso(scenario_at), "limit": size, "selection_token": token,
                "after": [work.iso(last["recorded_at"]), str(last["id"]).lower()]})
        return {"schema_version": rules.SCHEMA_LIST, "site_id": str(s), "window": window,
                "scenario_at": work.iso(scenario_at), "selection": selection, "items": items,
                "next_cursor": next_cursor, "total_pages": -(-count // size)}

    def _item(self, row: Mapping[str, Any], historical_evidence: bool) -> dict[str, Any]:
        authored = self._stored(row)
        superseded = row["revision_no"] < row["latest_no"]
        return {"id": str(row["scenario_id"]).lower(), "code": rules.scenario_code(row["public_no"]),
                "revision_id": str(row["id"]).lower(), "revision_no": row["revision_no"], "name": row["name"],
                "kind": row["kind"], "assumptions": row["assumptions"], "authored_basis": authored,
                "recorded_at": work.iso(row["recorded_at"]),
                "scenario_state": "HISTORICAL" if superseded or historical_evidence else "DEFINED"}


__all__ = ["ColdScenarioService"]
