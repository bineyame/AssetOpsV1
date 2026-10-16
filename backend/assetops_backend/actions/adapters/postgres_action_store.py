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
from datetime import datetime, timedelta
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
                 "expected_foundation_revision_id, current_foundation_revision_id, verification_plan_id, "
                 "verification_outcome_id")
PLAN_COLUMNS = ("id, tenant_id, site_id, action_id, plan_version, supersedes_plan_id, origin_finding_revision_id, "
                "applied_event_id, change_id, old_foundation_revision_id, new_foundation_revision_id, battery_asset_id, "
                "field, rule_id, effective_from, baseline_start, baseline_end, later_start, later_end, "
                "baseline_candidate_seconds, baseline_selection, baseline_evidence_ids, basis, target, guardrails, bands, "
                "coverage, later_selection_rule, plan_sha256, actor_kind, actor_id, source_channel, "
                "authorization_basis, triggering_service, triggering_fixture, idempotency_key, payload, payload_sha256, "
                "recorded_at")
PLAN_JSON = frozenset({"baseline_selection", "baseline_evidence_ids", "basis", "target", "guardrails", "bands",
                       "coverage", "later_selection_rule", "payload"})
BINDING_COLUMNS = ("id, tenant_id, site_id, plan_id, window_name, selection, selection_sha256, actor_kind, actor_id, "
                   "triggering_service, triggering_job, triggering_fixture, idempotency_key, payload_sha256, recorded_at")
OUTCOME_COLUMNS = ("id, tenant_id, site_id, action_id, plan_id, selection_binding_id, evaluation_request_id, "
                   "supersedes_outcome_id, outcome, reasons, basis, basis_sha256, details, actor_kind, actor_id, "
                   "triggering_job, idempotency_key, recorded_at")
METRIC_COLUMNS = ("outcome_id, tenant_id, site_id, metric_key, window_name, state, value_text, threshold_text, unit, "
                  "reason, evidence_ids")
REQUEST_COLUMNS = ("id, tenant_id, site_id, action_id, plan_id, actor_kind, actor_id, source_channel, "
                   "authorization_basis, triggering_service, triggering_fixture, idempotency_key, payload, "
                   "payload_sha256, recorded_at")
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

    def _finding_actions(self, c, tenant_id: UUID, site_id: UUID, finding_id: UUID, *,
                         where: str = "", **params: Any) -> list[dict[str, Any]]:
        """The canonical Finding's Actions (any origin revision) in acceptance order, each with its origin
        revision number and its `(recorded_at, id)`-ordered events."""
        return self._actions_where(c, tenant_id, site_id, f"AND a.origin_finding_id = :f {where}",
                                   f=finding_id, **params)

    def _trial_actions(self, c, tenant_id: UUID, site_id: UUID, asset_id: Any, rule_id: str, *,
                       where: str = "", **params: Any) -> list[dict[str, Any]]:
        """S6-02a: every Action of this battery trial scope (Site, battery asset, reserve field, rule), whatever
        its Finding, in acceptance order with events. `asset_id=None` reads every battery of the Site."""
        asset = "" if asset_id is None else "AND a.asset_id = CAST(:asset AS uuid) "
        return self._actions_where(c, tenant_id, site_id, f"{asset}AND a.field = :field AND a.rule_id = :rule {where}",
                                   **({} if asset_id is None else {"asset": str(asset_id)}), field=FIELD,
                                   rule=rule_id, **params)

    def trial_actions(self, tenant_id: UUID, site_id: UUID, asset_id: Any, rule_id: str) -> list[dict[str, Any]]:
        return self._read(lambda c: self._trial_actions(c, tenant_id, site_id, asset_id, rule_id))

    @staticmethod
    def trial_lock(c, tenant_id: UUID, site_id: UUID, asset_id: Any, rule_id: str) -> None:
        """The one `(tenant, Site, battery asset, reserve field, rule)` trial lock shared by accept, plan freeze and
        the verification evaluator (`D-2026-10-16-s6-verification`)."""
        c.execute(text("SELECT pg_advisory_xact_lock(hashtext('action-trial:' || :t || ':' || :s || ':' || :asset "
                       "|| ':' || :field || ':' || :rule))"),
                  {"t": str(tenant_id), "s": str(site_id), "asset": str(asset_id), "field": FIELD, "rule": rule_id})

    def _actions_where(self, c, tenant_id: UUID, site_id: UUID, where: str, **params: Any) -> list[dict[str, Any]]:
        rows = self._rows(c.execute(text(
            f"SELECT {', '.join('a.' + col.strip() for col in ACTION_COLUMNS.split(','))}, "
            "fr.revision_no AS origin_revision_no FROM action a JOIN finding_revision fr ON fr.tenant_id = a.tenant_id "
            "AND fr.site_id = a.site_id AND fr.id = a.origin_finding_revision_id WHERE a.tenant_id = :t "
            f"AND a.site_id = :s {where} ORDER BY a.created_at, a.action_no"),
            {"t": tenant_id, "s": site_id, **params}))
        for row in rows:
            row["events"] = self._rows(c.execute(text(
                f"SELECT {EVENT_COLUMNS} FROM action_event WHERE action_id = :a ORDER BY recorded_at, id"),
                {"a": row["id"]}))
        return rows

    def actions_for_finding(self, tenant_id: UUID, site_id: UUID, finding_id: UUID) -> list[dict[str, Any]]:
        return self._read(lambda c: self._finding_actions(c, tenant_id, site_id, finding_id))

    def accept(self, tenant_id: UUID, site_id: UUID, proposal: dict[str, Any], *, payload_sha256: str,
               payload: dict[str, Any], idempotency_key: str, fixture_id: str, recorded_at: datetime,
               guard: Callable[[list[dict[str, Any]]], None]) -> tuple[dict[str, Any], dict[str, Any], bool]:
        """Insert the Action, its pinned basis and ACCEPTED, or return the existing Action for this
        recommendation key (`replayed=True`); the caller compares the stored payload digest.

        S6-02a (`D-2026-10-16-s6-verification`) widens `D-2026-10-15-s601-reopen`'s Finding-scoped lock to one
        advisory lock per (tenant, Site, battery asset, reserve field, rule), shared with plan freeze and the
        evaluator; under it `guard` sees every other Action of that battery trial scope, on any Finding (with
        events), and raises to refuse, so two accepts on the same battery cannot both pass the prior-Action check."""
        def work(c):
            scope = {"t": tenant_id, "s": site_id}
            self.trial_lock(c, tenant_id, site_id, proposal["asset_id"], proposal["rule"]["id"])
            c.execute(text("SELECT pg_advisory_xact_lock(hashtext('action-accept:' || :s || ':' || :k))"),
                      {"s": str(site_id), "k": proposal["recommendation_key"]})
            existing = c.execute(text(f"SELECT {ACTION_COLUMNS} FROM action WHERE tenant_id = :t AND site_id = :s "
                                      "AND recommendation_key = :k"),
                                 {**scope, "k": proposal["recommendation_key"]}).first()
            if existing is not None:
                event = c.execute(text(f"SELECT {EVENT_COLUMNS} FROM action_event WHERE action_id = :a "
                                       "AND kind = 'ACCEPTED'"), {"a": existing.id}).first()
                return dict(existing._mapping), dict(event._mapping), True
            guard(self._trial_actions(c, tenant_id, site_id, proposal["asset_id"], proposal["rule"]["id"],
                                      where="AND a.recommendation_key <> :k", k=proposal["recommendation_key"]))
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

    # ---- S6-02a verification plan and selection (D-2026-10-16-s6-verification) --------------------------------

    @staticmethod
    def _covering(c, tenant_id: UUID, site_id: UUID, valid_at: datetime, known_at: datetime) -> list[dict[str, Any]]:
        """FoundationRevisions valid at `valid_at` under what was recorded by `known_at` (bitemporal)."""
        return [dict(r._mapping) for r in c.execute(text(
            "SELECT id, version, valid_from, valid_to FROM foundation_revision WHERE tenant_id = :t "
            "AND site_id = :s AND valid_from <= :v AND (valid_to IS NULL OR valid_to > :v) AND recorded_at <= :k "
            "AND (superseded_at IS NULL OR superseded_at > :k)"), {"t": tenant_id, "s": site_id, "v": valid_at,
                                                                   "k": known_at})]

    def verification_context(self, tenant_id: UUID, site_id: UUID, action_id: UUID, *,
                             probes: list[datetime], windows: dict[str, tuple[datetime, datetime]],
                             days: list[datetime], known_at: datetime) -> dict[str, Any] | None:
        """Everything a plan freeze reads, in one snapshot: the Action and its events, its change artifact, the
        covering FoundationRevision at each probe instant, bindings covering each whole window, the latest DEFAULT
        dispatch selection of each UTC day (with its INTERVAL revisions), the Action's plans, and how much accepted
        evidence already overlaps each window."""
        def work(c):
            row = c.execute(text(f"SELECT {ACTION_COLUMNS} FROM action WHERE tenant_id = :t AND site_id = :s "
                                 "AND id = :a"), {"t": tenant_id, "s": site_id, "a": action_id}).first()
            if row is None:
                return None
            out: dict[str, Any] = {"action": dict(row._mapping)}
            out["events"] = self._rows(c.execute(text(
                f"SELECT {EVENT_COLUMNS} FROM action_event WHERE action_id = :a ORDER BY recorded_at, id"),
                {"a": action_id}))
            change = c.execute(text(f"SELECT {CHANGE_COLUMNS} FROM action_policy_change WHERE action_id = :a"),
                               {"a": action_id}).first()
            out["change"] = None if change is None else dict(change._mapping)
            out["covering"] = {p: [r["id"] for r in self._covering(c, tenant_id, site_id, p, known_at)]
                               for p in probes}
            out["bindings"] = {name: self._rows(c.execute(text(
                "SELECT b.role, b.asset_id, b.binding_set_revision_id, bs.role_set FROM signal_binding_revision b "
                "JOIN signal_binding_set_revision bs ON bs.id = b.binding_set_revision_id WHERE b.tenant_id = :t "
                "AND b.site_id = :s AND b.valid_from <= :lo AND (b.valid_to IS NULL OR b.valid_to >= :hi) "
                "AND b.recorded_at <= :k AND (b.superseded_at IS NULL OR b.superseded_at > :k) "
                "ORDER BY b.role, b.asset_id"), {"t": tenant_id, "s": site_id, "lo": lo, "hi": hi, "k": known_at}))
                for name, (lo, hi) in windows.items()}
            out["days"] = [self._day_selection(c, tenant_id, site_id, day, known_at) for day in days]
            out["plans"] = self._rows(c.execute(text(
                f"SELECT {PLAN_COLUMNS} FROM verification_plan WHERE action_id = :a ORDER BY recorded_at, id"),
                {"a": action_id}))
            out["outcome_plan_ids"] = {r.plan_id for r in c.execute(text(
                "SELECT DISTINCT plan_id FROM verification_outcome WHERE action_id = :a"), {"a": action_id})}
            out["accepted_in_window"] = {name: self._accepted_count(c, tenant_id, site_id, lo, hi, known_at)
                                         for name, (lo, hi) in windows.items()}
            return out
        return self._read(work)

    @staticmethod
    def _accepted_count(c, tenant_id: UUID, site_id: UUID, lo: datetime, hi: datetime, known_at: datetime) -> int:
        """Accepted evidence (any role) of this Site whose time overlaps `[lo, hi)`, accepted by `known_at`."""
        return int(c.execute(text(
            "SELECT count(*) FROM accepted_evidence e JOIN ingestion_disposition d ON d.batch_id = e.batch_id "
            "AND d.ordinal = e.ordinal WHERE e.tenant_id = :t AND e.site_id = :s AND d.decision = 'ACCEPTED' "
            "AND d.accepted_evidence_id = e.id AND d.decided_at <= :k AND e.source_time >= :lo "
            "AND COALESCE(e.interval_start, e.source_time) < :hi"),
            {"t": tenant_id, "s": site_id, "k": known_at, "lo": lo, "hi": hi}).scalar_one())

    def _day_selection(self, c, tenant_id: UUID, site_id: UUID, day: datetime, known_at: datetime) -> dict[str, Any]:
        """The latest DEFAULT `dispatch` selection of one UTC day recorded by `known_at` (S3's head rule:
        newest selection seq, never newest completion), with its WINDOW and INTERVAL revisions."""
        head = c.execute(text(
            "SELECT sel.seq, sel.selected_at, sel.run_id, r.model_version, r.cohort_status, r.cohort_sha256, "
            "r.input_sha256, r.configuration_sha256 FROM analytic_run_selection sel JOIN analytic_run r "
            "ON r.id = sel.run_id WHERE sel.tenant_id = :t AND sel.site_id = :s AND sel.analytic_id = 'dispatch' "
            "AND sel.window_start = :ws AND sel.window_end = :we AND sel.selected_at <= :k "
            "ORDER BY sel.seq DESC LIMIT 1"),
            {"t": tenant_id, "s": site_id, "ws": day, "we": day + timedelta(days=1), "k": known_at}).first()
        if head is None:
            return {"day": day.date().isoformat(), "selected": False}
        revisions = self._rows(c.execute(text(
            "SELECT a.scope, r.id, r.assessment_key, r.result FROM analytic_run_assessment a "
            "JOIN assessment_revision r ON r.id = a.assessment_revision_id WHERE a.run_id = :run "
            "ORDER BY a.scope, r.assessment_key"), {"run": head.run_id}))
        return {"day": day.date().isoformat(), "selected": True, "selection_seq": head.seq,
                "selected_at": head.selected_at, "run_id": head.run_id, "model_version": head.model_version,
                "cohort_status": head.cohort_status, "cohort_sha256": head.cohort_sha256,
                "input_sha256": head.input_sha256, "configuration_sha256": head.configuration_sha256,
                "window_revision_ids": [r["id"] for r in revisions if r["scope"] == "WINDOW"],
                "intervals": [{"assessment_revision_id": r["id"], "assessment_key": r["assessment_key"],
                               "result": r["result"]} for r in revisions if r["scope"] == "INTERVAL"]}

    def day_selections(self, tenant_id: UUID, site_id: UUID, days: list[datetime],
                       known_at: datetime) -> list[dict[str, Any]]:
        return self._read(lambda c: [self._day_selection(c, tenant_id, site_id, d, known_at) for d in days])

    def window_readings(self, tenant_id: UUID, site_id: UUID, start: datetime, end: datetime, roles: list[str],
                        known_at: datetime) -> list[dict[str, Any]]:
        """Accepted evidence of these roles touching `[start, end]` (the closed end keeps the terminal SOC sample),
        as accepted by `known_at`."""
        return self._read(lambda c: self._rows(c.execute(text(
            "SELECT e.id, e.role, e.asset_id, e.measurement, e.source_time, e.interval_start, e.interval_end, "
            "e.normalized_value_text, e.normalized_unit, e.quality, e.envelope_sha256, e.batch_id, d.decided_at "
            "FROM accepted_evidence e JOIN ingestion_disposition d ON d.batch_id = e.batch_id "
            "AND d.ordinal = e.ordinal WHERE e.tenant_id = :t AND e.site_id = :s AND d.decision = 'ACCEPTED' "
            "AND d.accepted_evidence_id = e.id AND d.decided_at <= :k AND e.source_time >= :lo "
            "AND COALESCE(e.interval_start, e.source_time) <= :hi AND e.role = ANY(:roles) "
            "ORDER BY e.source_time, e.id"),
            {"t": tenant_id, "s": site_id, "k": known_at, "lo": start, "hi": end, "roles": list(roles)})))

    def reserve_history(self, tenant_id: UUID, site_id: UUID, battery_asset_id: Any, start: datetime,
                        end: datetime, known_at: datetime) -> list[dict[str, Any]]:
        """The battery's configured reserve on each FoundationRevision overlapping `[start, end)` as known at
        `known_at`, with that revision's validity."""
        def work(c):
            assets = {r.asset_code: r.id for r in c.execute(text(
                "SELECT id, asset_code FROM asset WHERE tenant_id = :t AND site_id = :s"),
                {"t": tenant_id, "s": site_id})}
            rows = self._rows(c.execute(text(
                "SELECT id, version, valid_from, valid_to, content FROM foundation_revision WHERE tenant_id = :t "
                "AND site_id = :s AND valid_from < :hi AND (valid_to IS NULL OR valid_to > :lo) "
                "AND recorded_at <= :k AND (superseded_at IS NULL OR superseded_at > :k) ORDER BY valid_from"),
                {"t": tenant_id, "s": site_id, "lo": start, "hi": end, "k": known_at}))
            out = []
            for row in rows:
                for entry in _basis(row, assets).reserves:
                    if str(entry.asset_id) == str(battery_asset_id):
                        out.append({"foundation_revision_id": row["id"], "value": entry.value,
                                    "valid_from": row["valid_from"], "valid_to": row["valid_to"]})
            return out
        return self._read(work)

    def freeze_plan(self, tenant_id: UUID, site_id: UUID, plan: dict[str, Any], *,
                    check: Callable[[Any, list[dict[str, Any]]], None]) -> tuple[dict[str, Any], bool]:
        """Insert one immutable plan revision under the battery trial lock, or return the plan already frozen
        with this idempotency key (`replayed=True`; the caller compares the payload digest). `check(c, plans)`
        re-validates the Action's plan chain and the later-window cutoff under the lock and raises to refuse."""
        def work(c):
            self.trial_lock(c, tenant_id, site_id, plan["battery_asset_id"], plan["rule_id"])
            existing = c.execute(text(f"SELECT {PLAN_COLUMNS} FROM verification_plan WHERE action_id = :a "
                                      "AND idempotency_key = :k"),
                                 {"a": plan["action_id"], "k": plan["idempotency_key"]}).first()
            if existing is not None:
                return dict(existing._mapping), True
            self.acceptance_fence(c, site_id)  # F3: the cutoff check and insert serialize with S2 acceptance
            plans = self._rows(c.execute(text(
                f"SELECT {PLAN_COLUMNS} FROM verification_plan WHERE action_id = :a ORDER BY recorded_at, id"),
                {"a": plan["action_id"]}))
            check(c, plans)
            values = {**plan, "tenant_id": tenant_id, "site_id": site_id}
            columns = [col.strip() for col in PLAN_COLUMNS.split(",")]
            params = ", ".join(f"CAST(:{col} AS jsonb)" if col in PLAN_JSON else f":{col}" for col in columns)
            c.execute(text(f"INSERT INTO verification_plan ({PLAN_COLUMNS}) VALUES ({params})"),
                      {col: json.dumps(values[col], sort_keys=True, default=str) if col in PLAN_JSON else values[col]
                       for col in columns})
            return dict(c.execute(text(f"SELECT {PLAN_COLUMNS} FROM verification_plan WHERE id = :i"),
                                  {"i": plan["id"]}).one()._mapping), False
        return self._run(work)

    def accepted_count(self, c, tenant_id: UUID, site_id: UUID, lo: datetime, hi: datetime,
                       known_at: datetime) -> int:
        return self._accepted_count(c, tenant_id, site_id, lo, hi, known_at)

    def append_selection_binding(self, tenant_id: UUID, site_id: UUID, plan: dict[str, Any],
                                 binding: dict[str, Any], *,
                                 check: Callable[[Any], None] | None = None) -> tuple[dict[str, Any], bool]:
        """Append the later window's selection binding, or return the binding already made with this idempotency
        key, or the plan's latest binding when it already pins the same selection digest (`replayed=True`; the
        caller compares the payload digest). `check(c)` re-validates the plan head under the lock and raises."""
        def work(c):
            self.trial_lock(c, tenant_id, site_id, plan["battery_asset_id"], plan["rule_id"])
            keyed = c.execute(text(f"SELECT {BINDING_COLUMNS} FROM verification_selection_binding WHERE plan_id = :p "
                                   "AND idempotency_key = :k"),
                              {"p": plan["id"], "k": binding["idempotency_key"]}).first()
            if keyed is not None:
                return dict(keyed._mapping), True
            if check is not None:
                check(c)
            latest = c.execute(text(
                f"SELECT {BINDING_COLUMNS} FROM verification_selection_binding WHERE plan_id = :p "
                "ORDER BY recorded_at DESC, id DESC LIMIT 1"), {"p": plan["id"]}).first()
            if latest is not None and latest.selection_sha256 == binding["selection_sha256"]:
                return dict(latest._mapping), True
            values = {**binding, "tenant_id": tenant_id, "site_id": site_id, "plan_id": plan["id"]}
            columns = [col.strip() for col in BINDING_COLUMNS.split(",")]
            params = ", ".join("CAST(:selection AS jsonb)" if col == "selection" else f":{col}" for col in columns)
            c.execute(text(f"INSERT INTO verification_selection_binding ({BINDING_COLUMNS}) VALUES ({params})"),
                      {col: json.dumps(values[col], sort_keys=True, default=str) if col == "selection"
                       else values[col] for col in columns})
            return dict(c.execute(text(f"SELECT {BINDING_COLUMNS} FROM verification_selection_binding "
                                       "WHERE id = :i"), {"i": binding["id"]}).one()._mapping), False
        return self._run(work)

    def plans(self, tenant_id: UUID, site_id: UUID, action_id: UUID) -> list[dict[str, Any]]:
        return self._read(lambda c: self._rows(c.execute(text(
            f"SELECT {PLAN_COLUMNS} FROM verification_plan WHERE tenant_id = :t AND site_id = :s AND action_id = :a "
            "ORDER BY recorded_at, id"), {"t": tenant_id, "s": site_id, "a": action_id})))

    def selection_bindings(self, tenant_id: UUID, site_id: UUID, plan_id: UUID) -> list[dict[str, Any]]:
        return self._read(lambda c: self._rows(c.execute(text(
            f"SELECT {BINDING_COLUMNS} FROM verification_selection_binding WHERE tenant_id = :t AND site_id = :s "
            "AND plan_id = :p ORDER BY recorded_at, id"), {"t": tenant_id, "s": site_id, "p": plan_id})))

    # ---- S6-02a phase 2: evaluation request, outcome, metrics and evaluator events --------------------------

    @staticmethod
    def is_superseded(c, plan_id: UUID) -> bool:
        return c.execute(text("SELECT 1 FROM verification_plan WHERE supersedes_plan_id = :p"),
                         {"p": plan_id}).first() is not None

    def covering_ids(self, tenant_id: UUID, site_id: UUID, instants: list[datetime],
                     known_at: datetime) -> list[list[str]]:
        """The covering FoundationRevision IDs at each instant, as recorded by `known_at`."""
        return self._read(lambda c: [sorted(str(r["id"]) for r in self._covering(c, tenant_id, site_id, i, known_at))
                                     for i in instants])

    def window_bindings(self, tenant_id: UUID, site_id: UUID, lo: datetime, hi: datetime,
                        known_at: datetime) -> list[dict[str, Any]]:
        """Signal bindings covering the whole window `[lo, hi]`, as recorded by `known_at`."""
        return self._read(lambda c: self._rows(c.execute(text(
            "SELECT b.role, b.asset_id, b.binding_set_revision_id, bs.role_set FROM signal_binding_revision b "
            "JOIN signal_binding_set_revision bs ON bs.id = b.binding_set_revision_id WHERE b.tenant_id = :t "
            "AND b.site_id = :s AND b.valid_from <= :lo AND (b.valid_to IS NULL OR b.valid_to >= :hi) "
            "AND b.recorded_at <= :k AND (b.superseded_at IS NULL OR b.superseded_at > :k) "
            "ORDER BY b.role, b.asset_id"), {"t": tenant_id, "s": site_id, "lo": lo, "hi": hi, "k": known_at})))

    @staticmethod
    def acceptance_fence(c, site_id: UUID) -> None:
        """The advisory lock every S2 accepting transaction takes before it commits (the evidence ledger's
        `_coalesce_job`, key `hashtextextended(site || ':dispatch', 0)`). Taking it here serializes a plan freeze's
        later-window cutoff check and insert against acceptance (`D-2026-10-16-s602a-cutoff`): an acceptance that
        holds it commits first and is seen by the check; one that arrives later waits for the freeze to commit."""
        c.execute(text("SELECT pg_advisory_xact_lock(hashtextextended(CAST(:site AS text) || ':' || :d, 0))"),
                  {"site": site_id, "d": "dispatch"})

    def late_evidence(self, tenant_id: UUID, site_id: UUID, windows: list[tuple[datetime, datetime]],
                      roles: list[str], after: datetime) -> list[dict[str, Any]]:
        """Accepted evidence of these roles touching any window (closed end), decided after `after`."""
        def work(c):
            out: dict[Any, dict[str, Any]] = {}
            for lo, hi in windows:
                for r in c.execute(text(
                        "SELECT e.id, e.role, e.source_time, d.decided_at FROM accepted_evidence e "
                        "JOIN ingestion_disposition d ON d.batch_id = e.batch_id AND d.ordinal = e.ordinal "
                        "WHERE e.tenant_id = :t AND e.site_id = :s AND d.decision = 'ACCEPTED' "
                        "AND d.accepted_evidence_id = e.id AND d.decided_at > :after AND e.source_time >= :lo "
                        "AND COALESCE(e.interval_start, e.source_time) <= :hi AND e.role = ANY(:roles)"),
                        {"t": tenant_id, "s": site_id, "after": after, "lo": lo, "hi": hi, "roles": list(roles)}):
                    out[r.id] = dict(r._mapping)
            return sorted(out.values(), key=lambda r: (r["decided_at"], str(r["id"])))
        return self._read(work)

    def outcomes(self, tenant_id: UUID, site_id: UUID, action_id: UUID) -> list[dict[str, Any]]:
        def work(c):
            rows = self._rows(c.execute(text(
                f"SELECT {OUTCOME_COLUMNS} FROM verification_outcome WHERE tenant_id = :t AND site_id = :s "
                "AND action_id = :a ORDER BY recorded_at, id"), {"t": tenant_id, "s": site_id, "a": action_id}))
            for row in rows:
                row["metrics"] = self._rows(c.execute(text(
                    f"SELECT {METRIC_COLUMNS} FROM verification_metric WHERE outcome_id = :o "
                    "ORDER BY metric_key, window_name"), {"o": row["id"]}))
            return rows
        return self._read(work)

    def evaluation_requests(self, tenant_id: UUID, site_id: UUID, action_id: UUID) -> list[dict[str, Any]]:
        return self._read(lambda c: self._rows(c.execute(text(
            f"SELECT {REQUEST_COLUMNS} FROM verification_evaluation_request WHERE tenant_id = :t AND site_id = :s "
            "AND action_id = :a ORDER BY recorded_at, id"), {"t": tenant_id, "s": site_id, "a": action_id})))

    @staticmethod
    def _insert(c, table: str, columns: str, values: dict[str, Any], json_cols: frozenset[str]) -> None:
        cols = [col.strip() for col in columns.split(",")]
        params = ", ".join(f"CAST(:{col} AS jsonb)" if col in json_cols else f":{col}" for col in cols)
        c.execute(text(f"INSERT INTO {table} ({columns}) VALUES ({params})"),
                  {col: json.dumps(values[col], sort_keys=True, default=str) if col in json_cols else values[col]
                   for col in cols})

    def record_evaluation(self, tenant_id: UUID, site_id: UUID, plan: dict[str, Any], request: dict[str, Any],
                          compose: Callable[[Any, dict[str, Any], dict[str, Any] | None, list[dict[str, Any]]],
                                            dict[str, Any]]) -> dict[str, Any]:
        """The evaluator job's one serialized transaction under the battery trial lock.

        Returns the earlier request's outcome when this idempotency key already produced one (`replayed=True`;
        the caller compares the payload digest). Otherwise inserts the request (once per key), re-reads the
        Action's latest outcome and events under the lock and lets `compose(c, request, latest, events)` decide
        the writes: `{"outcome": row | None, "metrics": [...], "events": [...], "result": {...}}`. Outcome,
        metrics and RESOLVED / RESOLUTION_WITHDRAWN events commit together or not at all."""
        def work(c):
            self.trial_lock(c, tenant_id, site_id, plan["battery_asset_id"], plan["rule_id"])
            scope = {"t": tenant_id, "s": site_id}
            existing = c.execute(text(f"SELECT {REQUEST_COLUMNS} FROM verification_evaluation_request "
                                      "WHERE plan_id = :p AND idempotency_key = :k"),
                                 {"p": plan["id"], "k": request["idempotency_key"]}).first()
            if existing is not None:
                stored = dict(existing._mapping)
                made = c.execute(text(f"SELECT {OUTCOME_COLUMNS} FROM verification_outcome "
                                      "WHERE evaluation_request_id = :r"), {"r": stored["id"]}).first()
                if made is not None or stored["payload_sha256"] != request["payload_sha256"]:
                    return {"replayed": True, "request": stored,
                            "outcome": None if made is None else dict(made._mapping)}
                request = stored
            else:
                self._insert(c, "verification_evaluation_request", REQUEST_COLUMNS,
                             {**request, "tenant_id": tenant_id, "site_id": site_id}, frozenset({"payload"}))
            latest = c.execute(text(f"SELECT {OUTCOME_COLUMNS} FROM verification_outcome WHERE action_id = :a "
                                    "ORDER BY recorded_at DESC, id DESC LIMIT 1"), {"a": plan["action_id"]}).first()
            events = self._rows(c.execute(text(
                f"SELECT {EVENT_COLUMNS} FROM action_event WHERE action_id = :a ORDER BY recorded_at, id"),
                {"a": plan["action_id"], **scope}))
            writes = compose(c, request, None if latest is None else dict(latest._mapping), events)
            outcome = writes.get("outcome")
            if outcome is not None and writes.get("insert_outcome"):
                self._insert(c, "verification_outcome", OUTCOME_COLUMNS,
                             {**outcome, "tenant_id": tenant_id, "site_id": site_id}, frozenset({"basis", "details"}))
                for metric in writes.get("metrics", []):
                    self._insert(c, "verification_metric", METRIC_COLUMNS,
                                 {**metric, "outcome_id": outcome["id"], "tenant_id": tenant_id, "site_id": site_id},
                                 frozenset({"evidence_ids"}))
            for event in writes.get("events", []):
                self._insert_evaluator_event(c, tenant_id, site_id, plan["action_id"], event)
            return {"replayed": False, "request": request, "outcome": outcome, **writes.get("result", {})}
        return self._run(work)

    @staticmethod
    def _insert_evaluator_event(c, tenant_id: UUID, site_id: UUID, action_id: UUID, event: dict[str, Any]) -> None:
        """RESOLVED / RESOLUTION_WITHDRAWN, written only by the evaluator job (SYSTEM_JOB channel, migration 0019
        `action_event_evaluator_job`)."""
        c.execute(text(
            "INSERT INTO action_event (id, tenant_id, site_id, action_id, kind, occurred_at, recorded_at, "
            "actor_kind, actor_id, source_channel, authorization_basis, triggering_service, triggering_job, "
            "triggering_command, triggering_fixture, idempotency_key, payload, payload_sha256, "
            "verification_plan_id, verification_outcome_id) VALUES (:id, :t, :s, :a, :kind, :rec, :rec, 'SYSTEM', "
            "'service:verification-evaluator', 'SYSTEM_JOB', 'SYSTEM_VERIFICATION_EVALUATOR', :svc, :job, "
            "'EVALUATE', :fx, :key, CAST(:payload AS jsonb), :ps, :plan, :outcome)"),
            {"id": event["id"], "t": tenant_id, "s": site_id, "a": action_id, "kind": event["kind"],
             "rec": event["recorded_at"], "svc": event["triggering_service"], "job": event["triggering_job"],
             "fx": event["triggering_fixture"], "key": event["idempotency_key"],
             "payload": json.dumps(event["payload"], sort_keys=True, default=str), "ps": sha(event["payload"]),
             "plan": event["verification_plan_id"], "outcome": event["verification_outcome_id"]})

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
