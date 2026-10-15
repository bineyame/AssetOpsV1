"""The ninth PostgreSQL writer: append-only Action, event and Action-owned rows (S6-01a).

`D-2026-10-15-s601-action-store-and-ui` M1: this module is the sole runtime SQL writer of `action`,
`action_basis_assessment`, `action_basis_evidence`, `action_event`, `action_policy_change` and
`action_policy_change_binding`, and it only INSERTs (rule 8 of `tools/checks/configuration-persistence.ps1`).
Acceptance writes the Action, its pinned basis children and ACCEPTED without any Foundation publish. Apply (phase 2)
locks the Action row, then runs the S1 publish passed in from composition on this adapter's connection (it
takes the Site lock), then inserts the change artifact and APPLIED before this adapter's sole commit.

Reads here gather the persisted `reserve-trial-1` inputs: the FindingRevision, its cited INTERVAL assessments'
Candidate segments, the battery-SOC accepted evidence those segments cite, the cited FoundationRevisions and the
Site's current covering FoundationRevision.
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Callable
from uuid import UUID, uuid4

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import DBAPIError, IntegrityError, OperationalError, ProgrammingError

from assetops_backend.actions.lifecycle import ACCEPTED, APPLIED, FAILED, OBSERVED, OBSERVATION_CODE, SYSTEM_DEMO
from assetops_backend.actions.ports import ActionStoreUnavailable, ApplyFailed
from assetops_backend.actions.reserve_trial import (
    CANDIDATE,
    FIELD,
    SOC_ROLE,
    UNIT,
    FoundationBasis,
    ReserveEntry,
    RuleInputs,
    Segment,
    SocReading,
    sha,
)

RESERVE_TYPE = "BATTERY"

ACTION_COLUMNS = ("id, tenant_id, site_id, action_no, action_code, recommendation_key, acceptance_key, "
                  "acceptance_payload_sha256, origin_finding_id, origin_finding_revision_id, "
                  "primary_assessment_revision_id, foundation_revision_id, asset_id, rule_id, rule_version, field, "
                  "unit, old_value, proposed_value, limitation_code, limitation_text, input_sha256, snapshot, "
                  "snapshot_sha256, created_at")
EVENT_COLUMNS = ("id, tenant_id, site_id, action_id, kind, occurred_at, recorded_at, actor_kind, actor_id, "
                 "source_channel, authorization_basis, triggering_service, triggering_job, triggering_command, "
                 "triggering_fixture, idempotency_key, payload, payload_sha256, failure_code, observation_code, "
                 "expected_foundation_revision_id, current_foundation_revision_id")
CHANGE_COLUMNS = ("id, tenant_id, site_id, action_id, applied_event_id, command_idempotency_key, asset_id, field, unit, "
                  "old_value, new_value, expected_foundation_revision_id, superseded_foundation_revision_id, "
                  "new_foundation_revision_id, split_foundation_revision_id, effective_from, recorded_at, validity")


class PostgresActionStore:
    def __init__(self, database_url: str | None, *, statement_timeout_ms: int = 30_000,
                 lock_timeout_ms: int = 5_000) -> None:
        self._database_url = database_url
        self._options = f"-c statement_timeout={int(statement_timeout_ms)} -c lock_timeout={int(lock_timeout_ms)}"
        self._engine: Engine | None = None

    def _connect(self) -> Engine:
        if not self._database_url:
            raise ActionStoreUnavailable("DATABASE_URL is not set, so the Action store cannot be reached.")
        if self._engine is None:
            self._engine = create_engine(self._database_url, pool_pre_ping=True,
                                         connect_args={"options": self._options})
        return self._engine

    def dispose(self) -> None:
        if self._engine is not None:
            self._engine.dispose()
            self._engine = None

    def _run(self, work):
        try:
            with self._connect().begin() as c:
                return work(c)
        except (OperationalError, ProgrammingError) as error:
            raise ActionStoreUnavailable(f"The Action store failed: {error.orig}") from error
        except DBAPIError as error:
            if error.connection_invalidated:
                raise ActionStoreUnavailable(str(error.orig)) from error
            raise

    def _read(self, work):
        def snapshot(c):
            c.execute(text("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY"))
            return work(c)
        return self._run(snapshot)

    @staticmethod
    def _rows(result) -> list[dict[str, Any]]:
        return [dict(r._mapping) for r in result]

    # ---- recommendation inputs -----------------------------------------------------------------------------

    def latest_revision(self, tenant_id: UUID, site_id: UUID, finding_id: UUID) -> dict[str, Any] | None:
        def work(c):
            row = c.execute(text(
                "SELECT id, revision_no, lifecycle, transition, created_at FROM finding_revision "
                "WHERE tenant_id = :t AND site_id = :s AND finding_id = :f ORDER BY revision_no DESC LIMIT 1"),
                {"t": tenant_id, "s": site_id, "f": finding_id}).first()
            return None if row is None else dict(row._mapping)
        return self._read(work)

    def rule_inputs(self, tenant_id: UUID, site_id: UUID, finding_id: UUID, finding_revision_id: UUID,
                    *, is_latest: bool, claim_is_current: bool, at: datetime) -> RuleInputs | None:
        def work(c):
            scope = {"t": tenant_id, "s": site_id}
            rev = c.execute(text(
                "SELECT fr.id, fr.finding_id, fr.lifecycle, fr.mechanism, fr.assessment_revision_id "
                "FROM finding_revision fr JOIN finding f ON f.tenant_id = fr.tenant_id AND f.site_id = fr.site_id "
                "AND f.id = fr.finding_id WHERE fr.tenant_id = :t AND fr.site_id = :s AND fr.id = :r "
                "AND fr.finding_id = :f"), {**scope, "r": finding_revision_id, "f": finding_id}).first()
            if rev is None:
                return None
            assets = {r.asset_code: r.id for r in c.execute(text(
                "SELECT id, asset_code FROM asset WHERE tenant_id = :t AND site_id = :s"), scope)}
            intervals = self._rows(c.execute(text(
                "SELECT ar.id, ar.result FROM finding_revision_assessment fra JOIN assessment_revision ar "
                "ON ar.tenant_id = fra.tenant_id AND ar.site_id = fra.site_id AND ar.id = fra.assessment_revision_id "
                "WHERE fra.tenant_id = :t AND fra.site_id = :s AND fra.finding_revision_id = :r "
                "AND fra.scope = 'INTERVAL' ORDER BY ar.window_start, ar.id"), {**scope, "r": finding_revision_id}))
            foundation_ids = sorted({str(x) for i in intervals for x in (i["result"] or {}).get(
                "foundation_revision_ids") or ()})
            foundations = {str(r["id"]): r for r in self._rows(c.execute(text(
                "SELECT id, valid_from, valid_to, content FROM foundation_revision "
                "WHERE tenant_id = :t AND site_id = :s AND id = ANY(CAST(:ids AS uuid[]))"),
                {**scope, "ids": foundation_ids}))}
            segments = []
            for interval in intervals:
                result = interval["result"] or {}
                cited = [foundations[str(x)] for x in result.get("foundation_revision_ids") or ()
                         if str(x) in foundations]
                for seg in result.get("segments") or ():
                    if seg.get("classification") != CANDIDATE:
                        continue
                    start, end = datetime.fromisoformat(seg["start"]), datetime.fromisoformat(seg["end"])
                    soc = c.execute(text(
                        "SELECT id, asset_id, normalized_value_text, normalized_unit, quality, "
                        "COALESCE(interval_end, source_time) AS at, envelope_sha256 FROM accepted_evidence "
                        "WHERE tenant_id = :t AND site_id = :s AND role = :role "
                        "AND id = ANY(CAST(:ids AS uuid[])) ORDER BY at, id"),
                        {**scope, "role": SOC_ROLE, "ids": [str(x) for x in seg.get("evidence_ids") or ()]})
                    covering = tuple(_basis(f, assets) for f in cited
                                     if f["valid_from"] <= start and (f["valid_to"] is None or start < f["valid_to"]))
                    segments.append(Segment(
                        assessment_revision_id=interval["id"], start=start, end=end, foundations=covering,
                        soc=tuple(SocReading(r.id, r.asset_id, r.normalized_value_text, r.normalized_unit,
                                             r.quality, r.at, r.envelope_sha256) for r in soc)))
            current = self._rows(c.execute(text(
                "SELECT id, content FROM foundation_revision WHERE tenant_id = :t AND site_id = :s "
                "AND valid_from <= :at AND (valid_to IS NULL OR valid_to > :at) "
                "AND recorded_at <= :at AND (superseded_at IS NULL OR superseded_at > :at)"), {**scope, "at": at}))
            return RuleInputs(
                tenant_id=tenant_id, site_id=site_id, finding_id=rev.finding_id, finding_revision_id=rev.id,
                mechanism=rev.mechanism, lifecycle=rev.lifecycle, is_latest=is_latest,
                claim_is_current=claim_is_current, primary_assessment_revision_id=rev.assessment_revision_id,
                segments=tuple(segments),
                current_foundation=_basis(current[0], assets) if len(current) == 1 else None)
        return self._read(work)

    # ---- writes (INSERT only) ------------------------------------------------------------------------------

    def action_for_recommendation(self, tenant_id: UUID, site_id: UUID,
                                  recommendation_key: str) -> dict[str, Any] | None:
        def work(c):
            row = c.execute(text(f"SELECT {ACTION_COLUMNS} FROM action WHERE tenant_id = :t AND site_id = :s "
                                 "AND recommendation_key = :k"),
                            {"t": tenant_id, "s": site_id, "k": recommendation_key}).first()
            return None if row is None else dict(row._mapping)
        return self._read(work)

    def actions_for_revision(self, tenant_id: UUID, site_id: UUID,
                             finding_revision_id: UUID) -> list[dict[str, Any]]:
        return self._read(lambda c: self._rows(c.execute(text(
            f"SELECT {ACTION_COLUMNS} FROM action WHERE tenant_id = :t AND site_id = :s "
            "AND origin_finding_revision_id = :r ORDER BY created_at, action_no"),
            {"t": tenant_id, "s": site_id, "r": finding_revision_id})))

    def accept(self, tenant_id: UUID, site_id: UUID, proposal: dict[str, Any], *, payload_sha256: str,
               payload: dict[str, Any], idempotency_key: str, fixture_id: str,
               recorded_at: datetime) -> tuple[dict[str, Any], dict[str, Any], bool]:
        """Insert the Action, its pinned basis and ACCEPTED, or return the existing Action for this
        recommendation key (`replayed=True`); the caller compares the stored payload digest."""
        def work(c):
            scope = {"t": tenant_id, "s": site_id}
            c.execute(text("SELECT pg_advisory_xact_lock(hashtext('action-accept:' || :s || ':' || :k))"),
                      {"s": str(site_id), "k": proposal["recommendation_key"]})
            existing = c.execute(text(f"SELECT {ACTION_COLUMNS} FROM action WHERE tenant_id = :t AND site_id = :s "
                                      "AND recommendation_key = :k"),
                                 {**scope, "k": proposal["recommendation_key"]}).first()
            if existing is not None:
                event = c.execute(text(f"SELECT {EVENT_COLUMNS} FROM action_event WHERE action_id = :a "
                                       "AND kind = 'ACCEPTED'"), {"a": existing.id}).first()
                return dict(existing._mapping), dict(event._mapping), True
            number = c.execute(text("SELECT nextval('action_code_seq')")).scalar_one()
            action_id, event_id = uuid4(), uuid4()
            snapshot = {k: v for k, v in proposal.items() if k != "current_foundation_revision_id"}
            snapshot["current_foundation_revision_id_at_acceptance"] = proposal["current_foundation_revision_id"]
            c.execute(text(
                "INSERT INTO action (id, tenant_id, site_id, action_no, action_code, recommendation_key, "
                "acceptance_key, acceptance_payload_sha256, origin_finding_id, origin_finding_revision_id, "
                "primary_assessment_revision_id, foundation_revision_id, asset_id, rule_id, rule_version, field, "
                "unit, old_value, proposed_value, limitation_code, limitation_text, input_sha256, snapshot, "
                "snapshot_sha256, created_at) VALUES (:id, :t, :s, :no, :code, :rk, :ak, :ps, :f, :fr, :ar, :fo, "
                ":asset, :rule, :rv, :field, :unit, CAST(:old AS numeric), CAST(:new AS numeric), :lc, :lt, :ins, "
                "CAST(:snap AS jsonb), :ss, :at)"),
                {**scope, "id": action_id, "no": number, "code": f"ACT-{number:06d}",
                 "rk": proposal["recommendation_key"], "ak": proposal["acceptance_key"], "ps": payload_sha256,
                 "f": proposal["finding_id"], "fr": proposal["finding_revision_id"],
                 "ar": proposal["primary_assessment_revision_id"], "fo": proposal["foundation_revision_id"],
                 "asset": proposal["asset_id"], "rule": proposal["rule"]["id"], "rv": proposal["rule"]["version"],
                 "field": FIELD, "unit": UNIT, "old": proposal["old_value"], "new": proposal["proposed_value"],
                 "lc": proposal["limitation"]["code"], "lt": proposal["limitation"]["text"],
                 "ins": proposal["input_sha256"], "snap": json.dumps(snapshot, sort_keys=True),
                 "ss": sha(snapshot), "at": recorded_at})
            for seg in proposal["inputs"]["segments"]:
                c.execute(text(
                    "INSERT INTO action_basis_assessment (action_id, tenant_id, site_id, assessment_revision_id, "
                    "segment_start, segment_end) VALUES (:a, :t, :s, :ar, :start, :end)"),
                    {**scope, "a": action_id, "ar": seg["assessment_revision_id"], "start": seg["start"],
                     "end": seg["end"]})
                for reading in seg["soc_evidence"]:
                    c.execute(text(
                        "INSERT INTO action_basis_evidence (action_id, tenant_id, site_id, evidence_id, "
                        "assessment_revision_id, segment_start, role, value_text) VALUES (:a, :t, :s, :e, :ar, "
                        ":start, :role, :v)"),
                        {**scope, "a": action_id, "e": reading["evidence_id"], "ar": seg["assessment_revision_id"],
                         "start": seg["start"], "role": SOC_ROLE, "v": reading["value"]})
            self._insert_event(c, tenant_id, site_id, action_id, event_id, ACCEPTED, "ACCEPT", recorded_at,
                               recorded_at, idempotency_key, payload, payload_sha256, fixture_id)
            action = c.execute(text(f"SELECT {ACTION_COLUMNS} FROM action WHERE id = :a"), {"a": action_id}).one()
            event = c.execute(text(f"SELECT {EVENT_COLUMNS} FROM action_event WHERE id = :e"), {"e": event_id}).one()
            return dict(action._mapping), dict(event._mapping), False
        return self._run(work)

    def observe(self, tenant_id: UUID, site_id: UUID, action_id: UUID, *, occurred_at: datetime,
                idempotency_key: str, payload: dict[str, Any], payload_sha256: str, fixture_id: str,
                recorded_at: datetime) -> tuple[dict[str, Any], bool]:
        def work(c):
            c.execute(text("SELECT id FROM action WHERE tenant_id = :t AND site_id = :s AND id = :a FOR UPDATE"),
                      {"t": tenant_id, "s": site_id, "a": action_id}).one()
            existing = c.execute(text(f"SELECT {EVENT_COLUMNS} FROM action_event WHERE action_id = :a "
                                      "AND idempotency_key = :k"), {"a": action_id, "k": idempotency_key}).first()
            if existing is not None:
                return dict(existing._mapping), True
            event_id = uuid4()
            self._insert_event(c, tenant_id, site_id, action_id, event_id, OBSERVED, "OBSERVE", occurred_at,
                               recorded_at, idempotency_key, payload, payload_sha256, fixture_id)
            row = c.execute(text(f"SELECT {EVENT_COLUMNS} FROM action_event WHERE id = :e"), {"e": event_id}).one()
            return dict(row._mapping), False
        return self._run(work)

    # ---- apply: Action lock, then the caller-owned S1 publish (Site lock), then artifact + APPLIED ----------

    def apply(self, tenant_id: UUID, site_id: UUID, action_id: UUID, *, idempotency_key: str,
              payload: dict[str, Any], payload_sha256: str, fixture_id: str, recorded_at: datetime,
              expected_foundation_revision_id: UUID,
              attempt: Callable[[Any, dict[str, Any], list[dict[str, Any]], Callable[[dict[str, Any]], None]], None],
              ) -> dict[str, Any]:
        """One application attempt. Returns `{"outcome": ..., "event": ..., "change": ...}`.

        In ONE transaction: lock the same-Site Action row `FOR UPDATE` (before anything else, so before the
        S1 Site lock); return the event already stored under this idempotency key (`REPLAY`, compared by the
        caller) or `ALREADY_APPLIED`; check the expected Foundation revision is this Site's (`FOUNDATION_UNKNOWN`
        otherwise); then `attempt(connection, action, events, then)` validates and runs the S1 publish on this
        connection, and `then(written_ids)` inserts the change artifact, its binding rows and APPLIED here.
        The single commit is this method's. An `ApplyFailed` from `attempt` rolls everything back, and FAILED is
        then appended in a separate transaction (`outcome == "FAILED"`); any other exception propagates after
        the rollback with nothing written.
        """
        scope = {"t": tenant_id, "s": site_id, "a": action_id}
        written: dict[str, Any] = {}

        def work(c):
            locked = c.execute(text(f"SELECT {ACTION_COLUMNS} FROM action WHERE tenant_id = :t AND site_id = :s "
                                    "AND id = :a FOR UPDATE"), scope).first()
            if locked is None:
                return {"outcome": "NOT_FOUND"}
            action = dict(locked._mapping)
            events = self._rows(c.execute(text(f"SELECT {EVENT_COLUMNS} FROM action_event WHERE action_id = :a "
                                               "ORDER BY recorded_at, id"), scope))
            prior = next((e for e in events if e["idempotency_key"] == idempotency_key), None)
            if prior is not None:
                return {"outcome": "REPLAY", "event": prior, "change": self._change_where(c, "applied_event_id",
                                                                                         prior["id"])}
            applied = next((e for e in events if e["kind"] == APPLIED), None)
            if applied is not None:
                return {"outcome": "ALREADY_APPLIED", "event": applied}
            known = c.execute(text("SELECT 1 FROM foundation_revision WHERE tenant_id = :t AND site_id = :s "
                                   "AND id = :f"), {**scope, "f": expected_foundation_revision_id}).first()
            if known is None:
                return {"outcome": "FOUNDATION_UNKNOWN"}

            def then(ids: dict[str, Any]) -> None:
                written.update(self._insert_applied(c, tenant_id, site_id, action, ids, idempotency_key=idempotency_key,
                                                    payload=payload, payload_sha256=payload_sha256,
                                                    fixture_id=fixture_id, recorded_at=recorded_at,
                                                    expected=expected_foundation_revision_id))

            attempt(c, action, events, then)
            if "event" not in written:
                raise RuntimeError("The publish returned without recording the change artifact; rolled back.")
            return {"outcome": "APPLIED", **written}

        try:
            return self._run(work)
        except ApplyFailed as failed:
            event = self._append_failed(tenant_id, site_id, action_id, failed, idempotency_key=idempotency_key,
                                        payload=payload, payload_sha256=payload_sha256, fixture_id=fixture_id,
                                        recorded_at=recorded_at, expected=expected_foundation_revision_id)
            return {"outcome": "FAILED", "event": event, "failure": failed}

    def _insert_applied(self, c, tenant_id, site_id, action, ids, *, idempotency_key, payload, payload_sha256,
                        fixture_id, recorded_at, expected) -> dict[str, Any]:
        publish, split = ids["publish_foundation_revision_ids"], ids["split_foundation_revision_ids"]
        superseded = ids["superseded_foundation_revision_ids"]
        if len(publish) != 1 or len(superseded) != 1 or len(split) > 1:
            raise RuntimeError(f"Unexpected publish shape {ids!r}; rolled back.")
        event_id, change_id = uuid4(), uuid4()
        self._insert_event(c, tenant_id, site_id, action["id"], event_id, APPLIED, "APPLY", recorded_at,
                           recorded_at, idempotency_key, payload, payload_sha256, fixture_id,
                           expected=expected, current=publish[0])
        effective = c.execute(text("SELECT valid_from FROM foundation_revision WHERE tenant_id = :t "
                                   "AND site_id = :s AND id = :f"),
                              {"t": tenant_id, "s": site_id, "f": publish[0]}).scalar_one()
        c.execute(text(
            "INSERT INTO action_policy_change (id, tenant_id, site_id, action_id, applied_event_id, "
            "command_idempotency_key, asset_id, field, unit, old_value, new_value, expected_foundation_revision_id, "
            "superseded_foundation_revision_id, new_foundation_revision_id, split_foundation_revision_id, "
            "effective_from, recorded_at, validity) VALUES (:id, :t, :s, :a, :e, :key, :asset, :field, :unit, "
            ":old, :new, :exp, :sup, :pub, :split, :eff, :rec, 'EFFECTIVE_FROM_OPEN_ENDED')"),
            {"id": change_id, "t": tenant_id, "s": site_id, "a": action["id"], "e": event_id, "key": idempotency_key,
             "asset": action["asset_id"], "field": action["field"], "unit": action["unit"],
             "old": action["old_value"], "new": action["proposed_value"], "exp": expected, "sup": superseded[0],
             "pub": publish[0], "split": split[0] if split else None, "eff": effective, "rec": recorded_at})
        for relation, key in (("SUPERSEDED", "superseded_binding_set_revision_ids"),
                              ("INSERTED", "inserted_binding_set_revision_ids")):
            for binding_set_revision_id in ids[key]:
                c.execute(text(
                    "INSERT INTO action_policy_change_binding (change_id, tenant_id, site_id, "
                    "binding_set_revision_id, relation) VALUES (:c, :t, :s, :b, :r)"),
                    {"c": change_id, "t": tenant_id, "s": site_id, "b": binding_set_revision_id, "r": relation})
        event = c.execute(text(f"SELECT {EVENT_COLUMNS} FROM action_event WHERE id = :e"), {"e": event_id}).one()
        return {"event": dict(event._mapping), "change": self._change_where(c, "id", change_id)}

    def _append_failed(self, tenant_id, site_id, action_id, failed: "ApplyFailed", *, idempotency_key, payload,
                       payload_sha256, fixture_id, recorded_at, expected) -> dict[str, Any]:
        """FAILED in its own transaction, after the attempt's rollback. A concurrent identical retry may already
        hold this key: then the stored event is returned (unique `(action_id, idempotency_key)`), never a second
        row, and nothing here can revert an APPLIED event."""
        def work(c):
            c.execute(text("SELECT id FROM action WHERE tenant_id = :t AND site_id = :s AND id = :a FOR UPDATE"),
                      {"t": tenant_id, "s": site_id, "a": action_id}).one()
            existing = c.execute(text(f"SELECT {EVENT_COLUMNS} FROM action_event WHERE action_id = :a "
                                      "AND idempotency_key = :k"), {"a": action_id, "k": idempotency_key}).first()
            if existing is not None:
                return dict(existing._mapping)
            event_id = uuid4()
            self._insert_event(c, tenant_id, site_id, action_id, event_id, FAILED, "APPLY", recorded_at,
                               recorded_at, idempotency_key, payload, payload_sha256, fixture_id,
                               failure_code=failed.code, expected=expected, current=failed.current_foundation_revision_id)
            return dict(c.execute(text(f"SELECT {EVENT_COLUMNS} FROM action_event WHERE id = :e"),
                                  {"e": event_id}).one()._mapping)
        try:
            return self._run(work)
        except IntegrityError as error:
            if "action_event_idempotency_unique" not in str(error.orig):
                raise
            return self._read(lambda c: dict(c.execute(text(
                f"SELECT {EVENT_COLUMNS} FROM action_event WHERE action_id = :a AND idempotency_key = :k"),
                {"a": action_id, "k": idempotency_key}).one()._mapping))

    @staticmethod
    def _insert_event(c, tenant_id, site_id, action_id, event_id, kind, command, occurred_at, recorded_at,
                      idempotency_key, payload, payload_sha256, fixture_id, *, failure_code=None, expected=None,
                      current=None) -> None:
        c.execute(text(
            "INSERT INTO action_event (id, tenant_id, site_id, action_id, kind, occurred_at, recorded_at, "
            "actor_kind, actor_id, source_channel, authorization_basis, triggering_service, triggering_job, "
            "triggering_command, triggering_fixture, idempotency_key, payload, payload_sha256, failure_code, "
            "observation_code, expected_foundation_revision_id, current_foundation_revision_id) VALUES (:id, :t, "
            ":s, :a, :kind, :occ, :rec, :ak, :aid, :ch, :basis, :svc, NULL, :cmd, :fx, :key, "
            "CAST(:payload AS jsonb), :ps, :fail, :obs, :exp, :cur)"),
            {"id": event_id, "t": tenant_id, "s": site_id, "a": action_id, "kind": kind, "occ": occurred_at,
             "rec": recorded_at, "ak": SYSTEM_DEMO.actor_kind, "aid": SYSTEM_DEMO.actor_id,
             "ch": SYSTEM_DEMO.source_channel, "basis": SYSTEM_DEMO.basis(fixture_id, command),
             "svc": SYSTEM_DEMO.triggering_service, "cmd": command, "fx": fixture_id, "key": idempotency_key,
             "payload": json.dumps(payload, sort_keys=True), "ps": payload_sha256, "fail": failure_code,
             "obs": OBSERVATION_CODE if kind == OBSERVED else None, "exp": expected, "cur": current})

    # ---- change artifact reads -----------------------------------------------------------------------------

    def _change_where(self, c, column: str, value: Any) -> dict[str, Any] | None:
        row = c.execute(text(f"SELECT {CHANGE_COLUMNS} FROM action_policy_change WHERE {column} = :v"),
                        {"v": value}).first()
        if row is None:
            return None
        out = dict(row._mapping)
        out["bindings"] = self._rows(c.execute(text(
            "SELECT binding_set_revision_id, relation FROM action_policy_change_binding WHERE change_id = :c "
            "ORDER BY relation, binding_set_revision_id"), {"c": out["id"]}))
        return out

    def change(self, tenant_id: UUID, site_id: UUID, change_id: UUID) -> dict[str, Any] | None:
        def work(c):
            found = c.execute(text("SELECT id FROM action_policy_change WHERE tenant_id = :t AND site_id = :s "
                                   "AND id = :c"), {"t": tenant_id, "s": site_id, "c": change_id}).first()
            return None if found is None else self._change_where(c, "id", change_id)
        return self._read(work)

    def change_for_action(self, tenant_id: UUID, site_id: UUID, action_id: UUID) -> dict[str, Any] | None:
        def work(c):
            found = c.execute(text("SELECT id FROM action_policy_change WHERE tenant_id = :t AND site_id = :s "
                                   "AND action_id = :a"), {"t": tenant_id, "s": site_id, "a": action_id}).first()
            return None if found is None else self._change_where(c, "id", found.id)
        return self._read(work)

    def foundation_revisions(self, tenant_id: UUID, site_id: UUID, ids: list[UUID]) -> list[dict[str, Any]]:
        return self._read(lambda c: self._rows(c.execute(text(
            "SELECT id, version, origin, valid_from, valid_to, recorded_at, superseded_at, derived_from_revision_id "
            "FROM foundation_revision WHERE tenant_id = :t AND site_id = :s AND id = ANY(CAST(:ids AS uuid[])) "
            "ORDER BY version"), {"t": tenant_id, "s": site_id, "ids": [str(i) for i in ids]})))

    def current_foundation(self, tenant_id: UUID, site_id: UUID, at: datetime) -> dict[str, Any] | None:
        """The Site's single covering FoundationRevision at `at` (recorded and not superseded by then)."""
        def work(c):
            assets = {r.asset_code: r.id for r in c.execute(text(
                "SELECT id, asset_code FROM asset WHERE tenant_id = :t AND site_id = :s"), {"t": tenant_id,
                                                                                          "s": site_id})}
            rows = self._rows(c.execute(text(
                "SELECT id, version, content FROM foundation_revision WHERE tenant_id = :t AND site_id = :s "
                "AND valid_from <= :at AND (valid_to IS NULL OR valid_to > :at) "
                "AND recorded_at <= :at AND (superseded_at IS NULL OR superseded_at > :at)"),
                {"t": tenant_id, "s": site_id, "at": at}))
            if len(rows) != 1:
                return None
            basis = _basis(rows[0], assets)
            return {"id": rows[0]["id"], "version": rows[0]["version"],
                    "reserves": [{"asset_code": e.asset_code, "asset_id": e.asset_id, "value": e.value,
                                  "unit": e.unit} for e in basis.reserves]}
        return self._read(work)

    # ---- exact reads ---------------------------------------------------------------------------------------

    def action(self, tenant_id: UUID, site_id: UUID, action_id: UUID) -> dict[str, Any] | None:
        def work(c):
            row = c.execute(text(f"SELECT {ACTION_COLUMNS} FROM action WHERE tenant_id = :t AND site_id = :s "
                                 "AND id = :a"), {"t": tenant_id, "s": site_id, "a": action_id}).first()
            if row is None:
                return None
            out = dict(row._mapping)
            episode = c.execute(text("SELECT episode_start, episode_end FROM finding_revision WHERE tenant_id = :t "
                                     "AND site_id = :s AND id = :r"),
                                {"t": tenant_id, "s": site_id, "r": out["origin_finding_revision_id"]}).one()
            out["origin_episode"] = {"start": episode.episode_start, "end": episode.episode_end}
            out["basis_assessments"] = self._rows(c.execute(text(
                "SELECT assessment_revision_id, segment_start, segment_end FROM action_basis_assessment "
                "WHERE action_id = :a ORDER BY segment_start, assessment_revision_id"), {"a": action_id}))
            out["basis_evidence"] = self._rows(c.execute(text(
                "SELECT evidence_id, assessment_revision_id, segment_start, role, value_text "
                "FROM action_basis_evidence WHERE action_id = :a ORDER BY segment_start, evidence_id"),
                {"a": action_id}))
            return out
        return self._read(work)

    def events(self, tenant_id: UUID, site_id: UUID, action_id: UUID) -> list[dict[str, Any]]:
        return self._read(lambda c: self._rows(c.execute(text(
            f"SELECT {EVENT_COLUMNS} FROM action_event WHERE tenant_id = :t AND site_id = :s AND action_id = :a "
            "ORDER BY recorded_at, id"), {"t": tenant_id, "s": site_id, "a": action_id})))


def _basis(row: dict[str, Any], assets: dict[str, UUID]) -> FoundationBasis:
    entries = []
    for component in (row["content"] or {}).get("components") or ():
        if component.get("component_type") != RESERVE_TYPE:
            continue
        for item in component.get("properties") or ():
            if item.get("property_key") == FIELD:
                code = str(component.get("component_id"))
                entries.append(ReserveEntry(code, assets.get(code), item.get("value"), item.get("unit")))
    return FoundationBasis(row["id"], tuple(entries))
