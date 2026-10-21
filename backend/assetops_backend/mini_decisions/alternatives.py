"""W4-03 unit 3: authored Alternatives on one exact W1 mini-grid dispatch Finding revision.

`.agent/W4-03-build-spec.md`: original "Alternative" domain paragraph and Alternatives panel ledger; "API, exact wire,
ordering and errors"; closure 1 Q1-Q3 (actor, attestation, literal command/response, canonical hash, retry) and
Q12-Q16 (one REPEATABLE READ snapshot, head per `(finding_id, alternative_key)` at cutoff, closed key set with fixed
ranks, carry-forward, RULED_OUT interval, list envelope, selection token, cursor); closure 4 B1, S17 (revision
query), S20 (provenance basis), N1 (mini dispatch Findings only), N2 (strict half-open overlap, point evidence).

Writes: scope, write grant and the server principal precede the body (router and `admit`); then the closed shape
(422), a USER actor (403), the attestation (422), the Finding root lock and lookup (404), the idempotency lookup
(exact retry 200 / changed body 409), and only then the Finding scope/kind, selected-revision, predecessor, citation
and counterevidence checks. A refused command writes nothing. The W1 Finding, its revisions, `claim` and money are
only read. All SQL lives in `store.py`.
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timedelta
from typing import Any, Callable, Mapping, Sequence
from uuid import UUID, uuid4

from assetops_backend.mini_decisions.model import DecisionPrincipal, DecisionRefused, invalid
from assetops_backend.mini_decisions.scenarios import (
    SELECTION_VERSION,
    _instant,
    _shape,
    admit,
    authorize,
    encode_cursor,
)
from assetops_backend.mini_decisions.store import (
    MiniDecisionStoreUnavailable,
    MiniDecisionWriteRefused,
    PostgresMiniDecisionStore,
)
from assetops_backend.mini_depth.read import MiniDepthRead, MiniReadRefused, MiniReadUnavailable, iso
from assetops_backend.work import model as work

SCHEMA_COMMAND = "mini-alternative-command-1"
SCHEMA_WRITE = "mini-alternative-write-1"
SCHEMA_LIST = "mini-alternatives-1"
ROUTE = "findings/alternatives"
#: Closure 1 Q12-Q16: the closed key set and its fixed ranks (the client never submits a rank).
RANKS = {"POLICY": 1, "UNCERTAINTY": 2, "CAPABILITY": 3}
DISPOSITIONS = ("PLAUSIBLE", "CANNOT_EXCLUDE", "INDETERMINATE", "RULED_OUT")
#: N1: the canonical Alternatives route serves W1 mini-grid dispatch Findings only.
FINDING_DOMAIN, FINDING_ANALYTIC = "mini_grid", "dispatch"
CURRENT, NEEDS_REVIEW, HISTORICAL = "CURRENT", "NEEDS_REVIEW", "HISTORICAL"


def parse_command(body: Any) -> dict[str, Any]:
    """The closed `mini-alternative-command-1` shape, canonical (sorted deduplicated citations, trimmed text)."""
    b = _shape(work.closed, body, ("schema_version", "idempotency_key", "actor", "finding_revision_id",
                                   "alternative_key", "supersedes_revision_id", "explanation", "evidence_summary",
                                   "cited_accepted_evidence_ids", "missing_evidence_reason", "disposition", "reason"))
    if b["schema_version"] != SCHEMA_COMMAND or b["alternative_key"] not in RANKS or b["disposition"] not in DISPOSITIONS:
        raise invalid()
    actor = _shape(work.actor_shape, b["actor"])
    cited = b["cited_accepted_evidence_ids"]
    if not isinstance(cited, list):
        raise invalid()
    missing = b["missing_evidence_reason"]
    canon: dict[str, Any] = {
        "schema_version": SCHEMA_COMMAND, "idempotency_key": _shape(work.idempotency_key, b["idempotency_key"]),
        "actor": {"kind": actor["kind"], "id": actor["id"], "attestation": actor["attestation"]},
        "finding_revision_id": _shape(work.uuid_text, b["finding_revision_id"]).lower(),
        "alternative_key": b["alternative_key"],
        "supersedes_revision_id": None if b["supersedes_revision_id"] is None
        else _shape(work.uuid_text, b["supersedes_revision_id"]).lower(),
        "explanation": _shape(work.text_value, b["explanation"], 1, 2000),
        "evidence_summary": _shape(work.text_value, b["evidence_summary"], 1, 2000),
        "cited_accepted_evidence_ids": sorted({_shape(work.uuid_text, i).lower() for i in cited}),
        "missing_evidence_reason": None if missing is None else _shape(work.text_value, missing, 1, 500),
        "disposition": b["disposition"], "reason": _shape(work.text_value, b["reason"], 1, 2000)}
    # The original domain paragraph: an alternative cites accepted IDs or states an explicit missing-evidence reason.
    if not canon["cited_accepted_evidence_ids"] and canon["missing_evidence_reason"] is None:
        raise invalid()
    return canon


def rules_out(intervals: Sequence[tuple[datetime, datetime]], episode_start: datetime, episode_end: datetime) -> bool:
    """N2: an empty episode never qualifies; otherwise at least one accepted interval (point evidence already
    normalized to `[source_time, source_time + 1us)`) strictly overlaps the half-open episode."""
    if episode_start >= episode_end:
        return False
    return any(lo < episode_end and hi > episode_start for lo, hi in intervals)


def _chain_order(row: Mapping[str, Any]) -> tuple[Any, int, str]:
    return row["created_at"], row["version_no"], str(row["id"])


class AlternativeService:
    """Alternative create/carry-forward (201/200/refusal) and the `mini-alternatives-1` table read."""

    def __init__(self, store: PostgresMiniDecisionStore, reader: MiniDepthRead, *,
                 test_db_clock_override: Callable[[], datetime] | None = None,
                 test_read_clock_override: Callable[[], datetime] | None = None) -> None:
        """Both overrides are constructor-only and test-only (as W4-01's `test_db_clock_override`): production
        always takes `clock_timestamp()` as the command instant and the read time."""
        self._store = store
        self._reader = reader
        self.test_db_clock_override = test_db_clock_override
        self.test_read_clock_override = test_read_clock_override

    # --- command ------------------------------------------------------------------------------------------------

    def create(self, tenant_id: UUID, site_id: UUID, principal: DecisionPrincipal | None, finding_id: str,
               body: Any) -> tuple[int, dict[str, Any]]:
        principal = admit(principal, tenant_id, site_id)
        try:
            root = str(UUID(finding_id)).lower()
        except ValueError:
            raise DecisionRefused("DECISION_NOT_FOUND") from None
        cmd = parse_command(body)
        actor = authorize(cmd["actor"], principal)
        sha = work.command_sha256({"site_id": str(site_id), "route": ROUTE, "root_id": root}, cmd)

        def write(c: Any) -> tuple[int, dict[str, Any]]:
            finding = self._store.finding_root(c, tenant_id, site_id, root, lock=True)
            if finding is None:
                raise DecisionRefused("DECISION_NOT_FOUND")
            # Final review L2: the command instant is read after the Finding lock, so two interleaved same-Finding
            # commands cannot invert `created_at` order.
            now = (self.test_db_clock_override() if self.test_db_clock_override is not None
                   else self._store.db_now(c))
            history = self._store.alternative_revisions(c, tenant_id, site_id, root)
            prior = next((r for r in history if r["idempotency_key"] == cmd["idempotency_key"]), None)
            if prior is not None:
                if prior["payload_sha256"] != sha:
                    raise DecisionRefused("DECISION_DUPLICATE_KEY")
                return 200, self._write_body(root, prior)
            revisions = self._store.finding_revisions(c, tenant_id, site_id, root)
            target = next((r for r in revisions if str(r["id"]).lower() == cmd["finding_revision_id"]), None)
            if target is None or finding["domain"] != FINDING_DOMAIN or target["analytic_id"] != FINDING_ANALYTIC:
                raise DecisionRefused("DECISION_LINK_SCOPE_INVALID")
            visible = [r for r in revisions if r["created_at"] <= now]
            if not visible or visible[-1]["id"] != target["id"]:
                raise DecisionRefused("DECISION_BASIS_CHANGED")  # not the selected Finding revision at command time
            chain = [r for r in history if r["alternative_key"] == cmd["alternative_key"]]
            previous = cmd["supersedes_revision_id"]
            if previous is None:
                if chain:
                    raise DecisionRefused("DECISION_CORRECTION_CONFLICT")
                version_no = 1
            else:
                predecessor = next((r for r in chain if str(r["id"]).lower() == previous), None)
                if predecessor is None:
                    raise DecisionRefused("DECISION_LINK_SCOPE_INVALID")
                if predecessor["id"] != chain[-1]["id"]:
                    raise DecisionRefused("DECISION_CORRECTION_CONFLICT")
                version_no = predecessor["version_no"] + 1
            cited = cmd["cited_accepted_evidence_ids"]
            intervals = self._store.accepted_intervals(c, tenant_id, site_id, cited, now)
            if set(intervals) != set(cited):
                raise DecisionRefused("DECISION_LINK_SCOPE_INVALID")
            if cmd["disposition"] == "RULED_OUT" and not rules_out(
                    list(intervals.values()), target["episode_start"], target["episode_end"]):
                raise DecisionRefused("DECISION_COUNTEREVIDENCE_INVALID")
            revision_id = uuid4()
            self._store.insert_alternative_revision(c, {
                "id": revision_id, "tenant_id": tenant_id, "site_id": site_id, "finding_id": finding["id"],
                "finding_revision_id": target["id"], "alternative_key": cmd["alternative_key"],
                "version_no": version_no, "supersedes_revision_id": previous, "rank": RANKS[cmd["alternative_key"]],
                "explanation": cmd["explanation"], "evidence_summary": cmd["evidence_summary"],
                "missing_evidence_reason": cmd["missing_evidence_reason"], "disposition": cmd["disposition"],
                "reason": cmd["reason"], **actor, "idempotency_key": cmd["idempotency_key"], "payload_sha256": sha,
                "created_at": now})
            for evidence_id in cited:
                self._store.insert_alternative_evidence(c, {
                    "tenant_id": tenant_id, "site_id": site_id, "alternative_revision_id": revision_id,
                    "evidence_id": evidence_id})
            stored = next(r for r in self._store.alternative_revisions(c, tenant_id, site_id, root)
                          if r["id"] == revision_id)
            return 201, self._write_body(root, stored)

        try:
            return self._write(write)
        except MiniDecisionWriteRefused:
            return self._write(write, final=True)  # a concurrent same-key or same-version write committed first: re-decide

    def _write(self, work_: Callable[[Any], tuple[int, dict[str, Any]]],
               final: bool = False) -> tuple[int, dict[str, Any]]:
        """One write transaction. `final` (the single retry, or a write with none): a further race or store
        refusal is 503 `DECISION_STORE_UNAVAILABLE`, never an uncaught 500 (final review L3, uF 5)."""
        try:
            with self._store.transaction() as c:
                return work_(c)
        except MiniDecisionWriteRefused as error:
            if final:
                raise DecisionRefused("DECISION_STORE_UNAVAILABLE") from error
            raise
        except (MiniDecisionStoreUnavailable, MiniReadUnavailable) as error:
            raise DecisionRefused("DECISION_STORE_UNAVAILABLE") from error

    @staticmethod
    def _write_body(finding_id: str, revision: Mapping[str, Any]) -> dict[str, Any]:
        previous = revision["supersedes_revision_id"]
        return {"schema_version": SCHEMA_WRITE, "id": str(revision["id"]), "finding_id": finding_id,
                "finding_revision_id": str(revision["finding_revision_id"]),
                "alternative_key": revision["alternative_key"], "version_no": revision["version_no"],
                "supersedes_revision_id": None if previous is None else str(previous),
                "recorded_at": iso(revision["created_at"])}

    # --- table read ---------------------------------------------------------------------------------------------

    def list(self, tenant_id: UUID, site_id: UUID, finding_id: str, revision_id: str | None,
             request: Mapping[str, Any], access_basis: str) -> dict[str, Any]:
        try:
            root = str(UUID(finding_id)).lower()
        except ValueError:
            raise DecisionRefused("DECISION_NOT_FOUND") from None
        if revision_id is not None:
            try:
                revision_id = str(UUID(revision_id)).lower()
            except ValueError:
                raise invalid() from None
        try:
            with self._store.snapshot() as c:
                read_time = self._store.db_now(c)
                if self.test_read_clock_override is not None:
                    read_time = self.test_read_clock_override()
                return self._list(c, tenant_id, site_id, root, revision_id, request, access_basis, read_time)
        except (MiniDecisionStoreUnavailable, MiniReadUnavailable, MiniReadRefused) as error:
            raise DecisionRefused("DECISION_STORE_UNAVAILABLE") from error

    def _list(self, c: Any, t: UUID, s: UUID, root: str, revision_id: str | None, request: Mapping[str, Any],
              access_basis: str, read_time: datetime) -> dict[str, Any]:
        explicit = request["known_at"]
        if explicit is not None and explicit > read_time:
            raise DecisionRefused("INVALID_KNOWN_AT")
        cursor = request["cursor"]
        if cursor is not None:
            if ((cursor["tenant_id"], cursor["site_id"], cursor["route"]) != (str(t), str(s), ROUTE)
                    or cursor["from"] is not None or cursor["to"] is not None):
                raise DecisionRefused("INVALID_CURSOR")
            if explicit is not None and iso(explicit) != cursor["known_at"]:
                raise DecisionRefused("DECISION_BASIS_CHANGED")
            known = _instant(cursor["known_at"], "INVALID_CURSOR")
            if known > read_time:
                raise DecisionRefused("DECISION_BASIS_CHANGED")
        else:
            known = read_time if explicit is None else explicit
        historical = explicit is not None and known < read_time

        finding = self._store.finding_root(c, t, s, root)
        revisions = [r for r in self._store.finding_revisions(c, t, s, root) if r["created_at"] <= known]
        if finding is None or finding["created_at"] > known or not revisions:
            raise DecisionRefused("DECISION_NOT_FOUND")
        latest = revisions[-1]
        selected = latest if revision_id is None else next(
            (r for r in revisions if str(r["id"]).lower() == revision_id), None)
        if selected is None or finding["domain"] != FINDING_DOMAIN or selected["analytic_id"] != FINDING_ANALYTIC:
            raise DecisionRefused("DECISION_NOT_FOUND")
        number = {str(r["id"]).lower(): r["revision_no"] for r in revisions}
        history = [r for r in self._store.alternative_revisions(c, t, s, root) if r["created_at"] <= known]

        rows: list[tuple[Mapping[str, Any], str, str]] = []
        for key in RANKS:  # rank order; at most one row per key
            chain = [r for r in history if r["alternative_key"] == key]
            own = [r for r in chain if r["finding_revision_id"] == selected["id"]]
            if own:
                head, state = max(own, key=_chain_order), CURRENT if selected["id"] == latest["id"] else HISTORICAL
            else:
                # S17: an earlier Finding revision's head for this key is shown only as NEEDS_REVIEW history.
                prior = [r for r in chain
                         if number.get(str(r["finding_revision_id"]).lower(), 0) < selected["revision_no"]]
                if not prior:
                    continue
                head, state = max(prior, key=_chain_order), NEEDS_REVIEW
            root_id = str(min(chain, key=lambda r: r["version_no"])["id"])
            rows.append((head, state, root_id))

        current = [h for h, state, _ in rows if state != NEEDS_REVIEW]
        blocks = self._reader.provenance_blocks(
            c, tenant_id=t, site_id=s, selected_revision_ids=[selected["id"], *(h["id"] for h in current)],
            selected_evidence_ids=[i for h in current for i in h["cited"]], pending_evidence_ids=None)
        token = "sha256:" + hashlib.sha256(work.canonical_json({
            "version": SELECTION_VERSION, "tenant_id": str(t), "site_id": str(s), "route": ROUTE, "from": None,
            "to": None, "known_at": iso(known), "access_basis": access_basis, "finding_id": root,
            "finding_revision_id": str(selected["id"]),
            "rows": [{"root_id": root_id, "selected_revision_id": str(h["id"]), "selected_selection_seq": None,
                      "linked_ids": list(h["cited"])} for h, _, root_id in rows],
            "pending_job_ids": []}).encode("utf-8")).hexdigest()
        if cursor is not None and cursor["selection_token"] != token:
            raise DecisionRefused("DECISION_BASIS_CHANGED")

        ordered = rows
        if cursor is not None:
            at = next((i for i, (h, _, _) in enumerate(rows) if str(h["id"]) == cursor["after"][1]), None)
            if at is None:
                raise DecisionRefused("DECISION_BASIS_CHANGED")
            ordered = rows[at + 1:]
        page = ordered[:request["limit"]]
        next_cursor = None
        if len(ordered) > len(page):
            last = page[-1][0]
            next_cursor = encode_cursor({"v": 1, "tenant_id": str(t), "site_id": str(s), "route": ROUTE, "from": None,
                                         "to": None, "known_at": iso(known), "selection_token": token,
                                         "after": [iso(last["created_at"]), str(last["id"])]})
        state = HISTORICAL if historical or selected["id"] != latest["id"] else CURRENT
        return {"schema_version": SCHEMA_LIST, "window": {"from": None, "to": None, "known_at": iso(known)},
                "status": "UNKNOWN", "currentness": {"state": state, "job_state": "NONE"}, **blocks,
                "total_count": len(rows), "rows": [self._row(h, review, root_id) for h, review, root_id in page],
                "next_cursor": next_cursor, "selection_token": token}

    @staticmethod
    def _row(head: Mapping[str, Any], review_state: str, root_id: str) -> dict[str, Any]:
        return {"id": root_id, "revision_id": str(head["id"]), "finding_revision_id": str(head["finding_revision_id"]),
                "explanation": head["explanation"], "evidence_summary": head["evidence_summary"],
                "cited_accepted_evidence_ids": list(head["cited"]),
                "missing_evidence_reason": head["missing_evidence_reason"], "disposition": head["disposition"],
                "reason": head["reason"], "review_state": review_state}


__all__ = ["AlternativeService", "RANKS", "ROUTE", "SCHEMA_LIST", "SCHEMA_WRITE", "parse_command", "rules_out"]
