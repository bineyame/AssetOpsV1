"""W5-03b E5: authored EV scenario commands and the `ev-scenarios-1` list (`.agent/W5-03-build-spec.md` E5 card,
"E5 exact persisted schema and wire contract" and "E5 consolidated correction" P-E5-2..8).

Writes, after the router's gate: the server principal (`mini_decisions.scenarios.admit`), the actor policy
(`authorize`), the closed body, then one REPEATABLE READ store transaction that answers an exact-key replay from the
stored hash and the prior resolved cutoff *before* resolving a basis, and otherwise resolves the selected basis with
`EvReadService.scenario_basis_on` and `EvSiteReads.scenario_money_on` on that same connection and appends. Only a
`CURRENT` selection with a selected assessment, at least one complete metered session revision, its accepted meter
evidence and a selected Foundation can be authored (P-E5-5). A refused command writes nothing. A unique or
serialization race retries once by rereading the key; a further race or store failure is 503
`DECISION_STORE_UNAVAILABLE`. The list reads one REPEATABLE READ READ ONLY snapshot whose `clock_timestamp()` is the
default `scenario_at`; the evidence `known_at` stays the selected EV cutoff. No SQL here.
"""

from __future__ import annotations

import hashlib
from datetime import datetime
from typing import Any, Callable, Mapping
from uuid import UUID, uuid4

from assetops_backend.analytics.ev_reads import EvPinnedLineageUnavailable, EvReadRefused, EvReadUnavailable
from assetops_backend.ev_scenarios import rules
from assetops_backend.ev_scenarios.rules import refused
from assetops_backend.ev_scenarios.store import (
    EvScenarioReadFailed,
    EvScenarioStoreUnavailable,
    EvScenarioWriteRefused,
    PostgresEvScenarioStore,
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


class EvScenarioService:
    """Create/correct (201, exact replay 200, refusal) and the list read."""

    def __init__(self, store: PostgresEvScenarioStore, reads: Any, site_reads: Any) -> None:
        self._store, self._reads, self._site = store, reads, site_reads

    # --- the selected basis -----------------------------------------------------------------------------------

    def _basis(self, c: Any, t: UUID, s: UUID, code: str, lo, hi, known_at, *, money: bool) -> dict[str, Any]:
        """`scenario_basis_on` (and, for a write, `scenario_money_on`) on the store connection; a selected-read
        failure is 503 `EV_READ_UNAVAILABLE` and a future `known_at` its 422 `EV_TIME_INVALID`."""
        def read() -> dict[str, Any]:
            basis = self._reads.scenario_basis_on(c, t, s, code, lo, hi, known_at)
            if money and basis["snap"]["state"] == "CURRENT" and basis["snap"]["lo"] is not None:
                basis["money"] = self._site.scenario_money_on(c, basis["snap"])
            return basis
        try:
            return self._store.reading(read)
        except EvReadRefused as error:
            raise refused(error.code, str(error), error.status) from error
        except (EvReadUnavailable, EvPinnedLineageUnavailable, EvScenarioReadFailed) as error:
            raise refused("EV_READ_UNAVAILABLE", "EV assessments cannot be read right now.", 503) from error

    @staticmethod
    def _authorable(basis: Mapping[str, Any]) -> dict[str, Any]:
        """P-E5-5: only a CURRENT selection with a selected assessment, complete metered sessions, their accepted
        meter evidence and a selected Foundation; anything else is 422 `EV_SCENARIO_INVALID`."""
        window, selection = basis["window"], basis["selection"]
        if (selection["state"] != "CURRENT" or selection["assessment_revision_id"] is None
                or window["from"] is None or window["known_at"] is None or not basis["session_revision_ids"]
                or not basis["meter_evidence_ids"] or basis["foreign_meter_evidence"]
                or basis["foundation_revision_id"] is None):
            raise rules.invalid()
        money = basis.get("money") or {"consequence_revision_id": None, "tariff_revision_id": None}
        return {"from": window["from"], "to": window["to"], "cutoff": window["known_at"],
                "assessment_revision_id": selection["assessment_revision_id"],
                "session_revision_ids": list(basis["session_revision_ids"]),
                "accepted_evidence_ids": list(basis["meter_evidence_ids"]),
                "foundation_revision_id": basis["foundation_revision_id"],
                "consequence_revision_id": money["consequence_revision_id"],
                "tariff_revision_id": money["tariff_revision_id"],
                "source_provenance": basis["source_provenance"]}

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
                    raise refused("EV_SCENARIO_IDEMPOTENCY_CONFLICT")
                return 200, self._write_body(prior["id"], prior["public_no"], first)
            authored = self._authorable(self._basis(c, t, s, code, lo, hi, known_at, money=True))
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
                raise rules.invalid()  # a correction keeps revision 1's window exactly, refused before append
            prior = next((r for r in revisions if r["idempotency_key"] == cmd["idempotency_key"]), None)
            if prior is not None:
                cutoff = known_text if known_text is not None else self._stored(prior)["cutoff"]
                if rules.correction_sha256(cmd, root_id, lo_text, hi_text, cutoff) != prior["payload_sha256"]:
                    raise refused("EV_SCENARIO_IDEMPOTENCY_CONFLICT")
                return 200, self._write_body(root["id"], root["public_no"], prior)
            predecessor = next((r for r in revisions if str(r["id"]).lower() == cmd["supersedes_revision_id"]),
                               None)
            if predecessor is None:
                raise refused("DECISION_LINK_SCOPE_INVALID")
            head = revisions[-1]
            if predecessor["id"] != head["id"]:
                raise refused("EV_SCENARIO_REVISION_CONFLICT")
            authored = self._authorable(self._basis(c, t, s, code, lo, hi, known_at, money=True))
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
            raise EvScenarioStoreUnavailable(str(error)) from error

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
            except EvScenarioWriteRefused as error:
                if attempt == 2:
                    raise _store_unavailable() from error
            except EvScenarioStoreUnavailable as error:
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
        except EvScenarioStoreUnavailable as error:
            raise _store_unavailable() from error

    @staticmethod
    def _decode(value: str, t: UUID, s: UUID) -> dict[str, Any]:
        """The mini cursor codec with E5 code translation and the E5 bindings (`scenario_at`, `limit`, whether
        `known_at` was explicit, the committed watermark)."""
        try:
            payload = decode_cursor(value)
            _instant(payload["scenario_at"])
            ok = (payload["route"] == rules.ROUTE and isinstance(payload["known_explicit"], bool)
                  and isinstance(payload["limit"], int) and not isinstance(payload["limit"], bool)
                  and 1 <= payload["limit"] <= rules.PAGE_MAX and payload["from"] is not None
                  and (payload["watermark"] is None or isinstance(payload["watermark"], str)))
        except (DecisionRefused, KeyError, TypeError, ValueError, AttributeError):
            ok = False
        if not ok or (payload["tenant_id"], payload["site_id"]) != (str(t), str(s)):
            raise refused("EV_SCENARIO_CURSOR_INVALID")
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
                raise refused("EV_SCENARIO_CURSOR_BASIS_CHANGED")
            lo, hi = _instant(page["from"]), _instant(page["to"])
            known_explicit = page["known_explicit"]
            known_at = _instant(page["known_at"]) if known_explicit else None
            scenario_at, limit = _instant(page["scenario_at"]), page["limit"]
        if scenario_at is None:
            scenario_at = now
        elif scenario_at > now:
            raise refused("EV_TIME_INVALID", "'scenario_at' is later than the current authored time.", 422)
        size = rules.PAGE_DEFAULT if limit is None else limit

        basis = self._basis(c, t, s, code, lo, hi, known_at, money=False)
        window, selection = basis["window"], basis["selection"]
        token = "sha256:" + hashlib.sha256(work.canonical_json(
            {"window": window, "selection": selection}).encode("utf-8")).hexdigest()
        if page is not None and (page["selection_token"] != token or page["known_at"] != window["known_at"]
                                 or page["watermark"] != window["committed_watermark"]):
            raise refused("EV_SCENARIO_CURSOR_BASIS_CHANGED")

        # The C4 Q-C5c item 3 rule: a Site root whose revision 1 lacks from/to has no trustworthy window (503).
        if self._store.malformed_roots(c, t, s, scenario_at):
            raise _store_unavailable()
        rows: list[Mapping[str, Any]] = []
        if window["from"] is not None and window["known_at"] is not None:
            w_lo, w_hi, w_known = _instant(window["from"]), _instant(window["to"]), _instant(window["known_at"])
            # The C4 Q-C5b item 5 rule: a candidate whose stored basis lacks from/to/cutoff is malformed (503).
            if self._store.malformed_candidates(c, t, s, w_lo, w_hi, scenario_at):
                raise _store_unavailable()
            after = None if page is None else (_instant(page["after"][0]), page["after"][1])
            rows = self._store.heads(c, t, s, w_lo, w_hi, w_known, scenario_at, after, size + 1)
        historical_evidence = (window["committed_watermark"] is not None and window["known_at"] is not None
                               and _instant(window["known_at"]) < _instant(window["committed_watermark"]))
        items = [self._item(r, historical_evidence) for r in rows[:size]]
        next_cursor = None
        if len(rows) > size:
            last = rows[size - 1]
            next_cursor = encode_cursor({
                "v": 1, "tenant_id": str(t), "site_id": str(s), "route": rules.ROUTE, "from": window["from"],
                "to": window["to"], "known_at": window["known_at"], "known_explicit": known_explicit,
                "watermark": window["committed_watermark"], "scenario_at": work.iso(scenario_at), "limit": size,
                "selection_token": token, "after": [work.iso(last["recorded_at"]), str(last["id"]).lower()]})
        return {"schema_version": rules.SCHEMA_LIST, "site_id": str(s), "window": window,
                "scenario_at": work.iso(scenario_at), "selection": selection, "items": items,
                "next_cursor": next_cursor}

    def _item(self, row: Mapping[str, Any], historical_evidence: bool) -> dict[str, Any]:
        authored = self._stored(row)
        superseded = row["revision_no"] < row["latest_no"]
        return {"id": str(row["scenario_id"]).lower(), "code": rules.scenario_code(row["public_no"]),
                "revision_id": str(row["id"]).lower(), "revision_no": row["revision_no"], "name": row["name"],
                "kind": row["kind"], "assumptions": row["assumptions"], "authored_basis": authored,
                "recorded_at": work.iso(row["recorded_at"]),
                "scenario_state": "HISTORICAL" if superseded or historical_evidence else "DEFINED"}


__all__ = ["EvScenarioService"]
