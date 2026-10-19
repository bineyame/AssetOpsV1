# W4-01 build spec — work-case core and thin Site lists (2026-10-20)

Authority: `tasks/W4-01-work-case-core.md`, `D-2026-10-20-post-w2-sequence`, v6.9 `sitework-incidents` and `sitework-maintenance`. This is the Architect's build contract, not a claim that the mock's INC-203/WR-019 exist. **Start only after independently reviewed W2-07 and `0026_w2_ev_money` are on main, the W4 owner wave-start scope/core-panel gate is recorded, and this spec receives independent review.** On the inspected branch main still ends at `0025_w2_ev_session`; the parent below is an explicit merge precondition. W4-01 is Lane A and the sole owner of migration/router/shell/registry/guard changes. W3-01 has no W4 dependency.

## Commit sequence and exact seam ledger

One builder run and handoff per commit; phases are commits 1–3 (store/API) and 4–5 (Site reads/UI). No builder chooses an omitted contract rule.

1. **`0027_w4_work_cases`**: the literal schema below and upgrade/downgrade/trigger/scoped-FK tests. Start from merged `0026`, assert one Alembic head. Rule-8 writer registration lands with the actual writer in commit 2. No backfill from mock or Lab.
2. **Domain and writer**: `backend/assetops_backend/work/{model,service,adapters/postgres_work_store}.py`. Service owns validation, authorization, state reduction and exact-link checks. Adapter alone imports SQL driver. It writes one serializable transaction per command, using DB time; accepted-evidence links are checked in scope, never copied from private world. Add `work/composition.py`.
3. **Case API**: `backend/assetops_backend/work_api.py`, Lane A mount in `main.py`; scoped create, transition, correction, plan, record and detail routes below. Use the existing `finding_api.py:Access,Scope,development_access`, `finding_api.py:ACCESS_BASIS` until a general auth port replaces them. The W1 Action/ActionEvent in `actions/service.py`, `actions/lifecycle.py` stay untouched and separate. Review this phase before UI.
4. **Selected projections**: `work/site_index.py` and `work/adapters/postgres_work_read.py`; `analytics/finding_index.py:FindingIndexService` and `actions/site_index.py:ActionIndexService` are link/currentness examples, not data sources for case existence. Implement one read-only REPEATABLE READ snapshot with a writer fence, full count before page, UTC cutoff and cursor. Mount Site list route in Lane A `main.py`.
5. **Two Site views**: `frontend/src/sites/{SiteWorkIncidents,SiteWorkMaintenance,workClient}.tsx/ts` plus `shell/operatorSiteRoutes.ts`, `shell/SiteAnalyticsFrames.tsx` Work subrow, navigation guard and reviewed registry panel paths. Use existing `SiteWorkActions` date-form pattern and shared `Disclosure`/`ProductStatus`; do not create a global Incidents/Maintenance root. Capture stocked and empty/unknown at 1440 and 390, then one same-revision full backend suite and independent slice review.

Registry paths to close with the implementation: `A-work-cases`, `A-incident-index`, `A-maintenance-index`, `I-work-store`, `I-incident-read/ui`, `I-maintenance-read/ui`, `D-work-records`; add each owned panel as a reviewed path, run the registry checker. No node is marked resolved merely by this spec.

## Identity, time and frozen domain rules

All IDs are lowercase UUIDs; visible codes are tenant-unique `INC-000001`, `WR-000001`, `PM-000001`, `REC-000001` generated from a DB sequence in the same transaction, never an input. `incident` and `maintenance_work_request` are disjoint typed identities over one `work_case` event/revision grammar; their child rows are mandatory and inserted atomically with the base row. `MaintenancePlan`, `MaintenanceRecord`, `WorkEvent`, `OperationalRecord` have independent UUID identities. A plan can spawn a request only by an explicit authored command. An Incident is not inferred from a Finding, gap, alarm or Action. One primary optional Asset belongs to the same tenant/Site; a case may pin **many** `(finding_id,finding_revision_id)` and `(action_id,selected_event_id)` links through immutable junctions. A case can have zero links. A cited accepted evidence ID must be in the same tenant/Site and accepted before the command's DB time. No source run mode is an attestation.

Every mutation has `actor_kind=USER|SERVICE`, nonblank `actor_id`, `authorization_basis`, `attestation` (human declaration or named service rule), `idempotency_key` (8–128 printable chars), `occurred_at` UTC supplied by the actor, and DB `recorded_at`; service commands must name service, job and rule version in attestation. A backdated `occurred_at` is permitted within 30 days and displayed as such; future >5 minutes is refused. State and history order is **`(recorded_at,id)`**, never occurrence time. A correction appends a new revision with `supersedes_revision_id`; it cannot edit old text, evidence, links, actor or event. This revision chain is linear under row lock. Lists show the latest revision known at cutoff and the state reduced from events recorded by cutoff. At the same timestamp UUID ascending breaks ties. `known_at` cannot be after the request's DB snapshot time. The selected window is half-open UTC `[from,to)` of at most 31 days, membership by incident `occurred_at` or request/plan `recorded_at`; later state changes remain visible at selected `known_at`. Local EAT formatting is presentation only.

Plan and OperationalRecord corrections append a new row with `supersedes_*_id`, a new version UUID/internal public number, and the **same canonical root ID** in `canonical_plan_id`/`canonical_record_id`. The root's visible public code remains the user-facing code; the new version code is audit metadata. Read the latest successor by `(recorded_at,id)` at cutoff, never update the root. Correction requires a nonempty reason and exact current predecessor; concurrent successors refuse 409. OperationalRecord `MANUAL_READING` requires quantity and unit, other kinds may omit them; `period_end` is optional but cannot precede occurrence. `source_document_sha256` is optional because a witnessed statement need not have a file; absence displays `No document attached`. An authored record never becomes `accepted_evidence` merely through its `ACCEPTED` state (which is unreached in W4).

| Kind | State | Allowed command → state | Unreached/terminal rule |
| --- | --- | --- | --- |
| Incident | OPEN | ASSIGN → IN_PROGRESS; CLOSE → CLOSED | CREATED event yields OPEN; no automatic case creation. |
| Incident | IN_PROGRESS | CLOSE → CLOSED; REOPEN → OPEN | REOPEN from active state is 409. |
| Incident | CLOSED | REOPEN → OPEN | CLOSED does not mean cause proved or outcome verified. |
| MaintenanceWorkRequest | OPEN | ASSIGN → IN_PROGRESS; CANCEL → CANCELLED | An Action remains a separate object. |
| MaintenanceWorkRequest | IN_PROGRESS | COMPLETE → COMPLETED; CANCEL → CANCELLED | COMPLETE requires a MaintenanceRecord ID; no verification assertion. |
| MaintenanceWorkRequest | COMPLETED | REOPEN → IN_PROGRESS; OPEN_VERIFICATION reserved | `VERIFICATION_WINDOW`, `VERIFIED`, `INEFFECTIVE`, `INCONCLUSIVE` require a frozen outcome plan and later accepted evidence. W4-01 has no evaluator or plan writer: transitions to these states are **unreached and 409**. |
| MaintenanceWorkRequest | VERIFICATION_WINDOW | REOPEN → IN_PROGRESS | Unreached in W4; later evaluator owns this state. |
| MaintenanceWorkRequest | CANCELLED | none | Terminal; correction still allowed, transition refused. |
| MaintenancePlan | DRAFT | ACTIVATE → ACTIVE; CANCEL → CANCELLED are reserved | W4 creates an immutable DRAFT only; those commands return 409 `WORK_TRANSITION_INVALID` until a later reviewed plan-event contract. Due is authored, not derived. |
| MaintenancePlan | ACTIVE/PAUSED/CANCELLED | PAUSE/ACTIVATE/CANCEL are reserved | Unreached in W4. No auto-created request or performed assertion. |
| OperationalRecord | SUBMITTED | ACCEPT → ACCEPTED; REJECT → REJECTED are reserved | W4 creates an immutable SUBMITTED record only; commands return 409 until a later reviewed review-event contract. Authored record is not telemetry. |
| OperationalRecord | ACCEPTED/REJECTED | none | Unreached in W4. A correction appends a lineage successor, retaining the old record. |

An Incident and WorkRequest can cite each other only through their exact stored IDs. `MaintenanceRecord` records activity, not success. `WorkEvent` describes transition/assignment/comment with actor and time; no implicit `VERIFIED`. An OperationalRecord is an authored statement with its own acceptance, never an `accepted_evidence` row unless a separately authorized publication mechanism exists. Source provenance of a case is the **union of exact accepted IDs it explicitly cites** plus any pinned Finding/Action version cited sets; classify via the shared DTO rule in `D-2026-10-20-shared-provenance-dto`. Empty set is UNKNOWN; never borrow the Site's source badge.

`CREATED` occurs once at create and cannot be posted later. `COMMENT` is allowed from OPEN/IN_PROGRESS/CLOSED for Incidents and OPEN/IN_PROGRESS/COMPLETED/VERIFICATION_WINDOW for requests, with no state change; `ASSIGN` on an already active case records a new assignee but remains IN_PROGRESS. `CLOSE`, `REOPEN`, `CANCEL`, `COMPLETE` and `OPEN_VERIFICATION` outside the table's named source state refuse 409. A terminal CANCELLED request accepts a correction to its text but no event. The `WorkEvent` row keeps the exact transition command; the reducer is pure over `(recorded_at,id)` and never reads the mutable plan/status column of another object.

## Literal migration `0027_w4_work_cases`

The following is the complete migration body. SQL identifiers and constraints are binding. `op.execute(SCHEMA)` is one Alembic transaction; `down_revision` must match the installed W2-07 revision exactly. Tables are append-only; the identity table is immutable too. Writers use `INSERT` only. `work_case_revision` and `work_event` are serialized on `work_case` row lock so number and state are unique at command time.

```python
"""W4-01: immutable authored work identities and history."""
from alembic import op
from sqlalchemy import text

revision = "0027_w4_work_cases"
down_revision = "0026_w2_ev_money"
branch_labels = None
depends_on = None

SCHEMA = r"""
CREATE SEQUENCE work_public_no_seq AS bigint START 1 NO CYCLE;
CREATE TABLE work_case (
 id uuid PRIMARY KEY, tenant_id uuid NOT NULL, site_id uuid NOT NULL,
 kind text NOT NULL CHECK (kind IN ('INCIDENT','MAINTENANCE_REQUEST')),
 public_no bigint NOT NULL UNIQUE CHECK (public_no>0),
 public_code text NOT NULL CHECK ((kind='INCIDENT' AND public_code ~ '^INC-[0-9]{6,}$') OR
                                  (kind='MAINTENANCE_REQUEST' AND public_code ~ '^WR-[0-9]{6,}$')),
 asset_id uuid NULL,
 occurred_at timestamptz NOT NULL, created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 actor_kind text NOT NULL CHECK (actor_kind IN ('USER','SERVICE')),
 actor_id text NOT NULL CHECK (length(btrim(actor_id)) BETWEEN 1 AND 128),
 authorization_basis text NOT NULL CHECK (length(btrim(authorization_basis)) BETWEEN 1 AND 500),
 attestation text NOT NULL CHECK (length(btrim(attestation)) BETWEEN 1 AND 1000),
 create_key text NOT NULL CHECK (length(create_key) BETWEEN 8 AND 128),
 create_payload_sha256 text NOT NULL CHECK(create_payload_sha256 ~ '^[0-9a-f]{64}$'),
 CONSTRAINT work_case_site_fk FOREIGN KEY(tenant_id,site_id) REFERENCES site(tenant_id,id),
 CONSTRAINT work_case_asset_fk FOREIGN KEY(tenant_id,site_id,asset_id) REFERENCES asset(tenant_id,site_id,id),
 CONSTRAINT work_case_scope UNIQUE(tenant_id,site_id,id),
 CONSTRAINT work_case_kind_scope UNIQUE(tenant_id,site_id,id,kind),
 CONSTRAINT work_case_code UNIQUE(tenant_id,public_code),
 CONSTRAINT work_case_create_once UNIQUE(tenant_id,site_id,create_key)
);
CREATE INDEX work_case_site_window ON work_case(tenant_id,site_id,occurred_at DESC,id);
CREATE INDEX work_case_site_kind ON work_case(tenant_id,site_id,kind,created_at DESC,id);
CREATE TABLE incident (
 tenant_id uuid NOT NULL, site_id uuid NOT NULL, id uuid NOT NULL,
 kind text NOT NULL DEFAULT 'INCIDENT' CHECK(kind='INCIDENT'),
 incident_key text NOT NULL CHECK(length(btrim(incident_key)) BETWEEN 8 AND 128),
 PRIMARY KEY(tenant_id,site_id,id),
 CONSTRAINT incident_case_fk FOREIGN KEY(tenant_id,site_id,id,kind) REFERENCES work_case(tenant_id,site_id,id,kind),
 CONSTRAINT incident_key_once UNIQUE(tenant_id,site_id,incident_key)
);
CREATE TABLE maintenance_work_request (
 tenant_id uuid NOT NULL, site_id uuid NOT NULL, id uuid NOT NULL,
 kind text NOT NULL DEFAULT 'MAINTENANCE_REQUEST' CHECK(kind='MAINTENANCE_REQUEST'),
 request_key text NOT NULL CHECK(length(btrim(request_key)) BETWEEN 8 AND 128),
 incident_id uuid NULL,
 PRIMARY KEY(tenant_id,site_id,id),
 CONSTRAINT maintenance_request_case_fk FOREIGN KEY(tenant_id,site_id,id,kind) REFERENCES work_case(tenant_id,site_id,id,kind),
 CONSTRAINT maintenance_request_incident_fk FOREIGN KEY(tenant_id,site_id,incident_id) REFERENCES incident(tenant_id,site_id,id),
 CONSTRAINT maintenance_request_key_once UNIQUE(tenant_id,site_id,request_key)
);
CREATE TABLE work_case_revision (
 id uuid PRIMARY KEY, tenant_id uuid NOT NULL, site_id uuid NOT NULL, case_id uuid NOT NULL,
 revision_no integer NOT NULL CHECK(revision_no>0), supersedes_revision_id uuid NULL,
 title text NOT NULL CHECK(length(btrim(title)) BETWEEN 1 AND 200),
 narrative text NOT NULL CHECK(length(btrim(narrative)) BETWEEN 1 AND 4000),
 actor_kind text NOT NULL CHECK(actor_kind IN ('USER','SERVICE')),
 actor_id text NOT NULL CHECK(length(btrim(actor_id)) BETWEEN 1 AND 128),
 attestation text NOT NULL CHECK(length(btrim(attestation)) BETWEEN 1 AND 1000),
 authorization_basis text NOT NULL CHECK(length(btrim(authorization_basis)) BETWEEN 1 AND 500),
 occurred_at timestamptz NOT NULL,
 idempotency_key text NOT NULL CHECK(length(idempotency_key) BETWEEN 8 AND 128),
 payload_sha256 text NOT NULL CHECK(payload_sha256 ~ '^[0-9a-f]{64}$'),
 reason text NULL CHECK(reason IS NULL OR length(btrim(reason)) BETWEEN 1 AND 500),
 recorded_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 CONSTRAINT work_revision_case_fk FOREIGN KEY(tenant_id,site_id,case_id) REFERENCES work_case(tenant_id,site_id,id),
 CONSTRAINT work_revision_prev_fk FOREIGN KEY(case_id,supersedes_revision_id) REFERENCES work_case_revision(case_id,id),
 CONSTRAINT work_revision_number UNIQUE(case_id,revision_no),
 CONSTRAINT work_revision_once UNIQUE(case_id,idempotency_key),
 CONSTRAINT work_revision_one_successor UNIQUE(supersedes_revision_id),
 CONSTRAINT work_revision_case_id UNIQUE(case_id,id),
 CONSTRAINT work_revision_scope UNIQUE(tenant_id,site_id,id)
);
CREATE INDEX work_revision_head ON work_case_revision(case_id,revision_no DESC);
CREATE TABLE work_case_finding_link (
 tenant_id uuid NOT NULL, site_id uuid NOT NULL, case_revision_id uuid NOT NULL,
 finding_id uuid NOT NULL, finding_revision_id uuid NOT NULL,
 PRIMARY KEY(case_revision_id,finding_id,finding_revision_id),
 CONSTRAINT work_finding_case_fk FOREIGN KEY(tenant_id,site_id,case_revision_id) REFERENCES work_case_revision(tenant_id,site_id,id),
 CONSTRAINT work_finding_revision_fk FOREIGN KEY(tenant_id,site_id,finding_id,finding_revision_id) REFERENCES finding_revision(tenant_id,site_id,finding_id,id)
);
CREATE TABLE work_case_action_link (
 tenant_id uuid NOT NULL, site_id uuid NOT NULL, case_revision_id uuid NOT NULL,
 action_id uuid NOT NULL, action_event_id uuid NOT NULL,
 PRIMARY KEY(case_revision_id,action_id,action_event_id),
 CONSTRAINT work_action_case_fk FOREIGN KEY(tenant_id,site_id,case_revision_id) REFERENCES work_case_revision(tenant_id,site_id,id),
 CONSTRAINT work_action_fk FOREIGN KEY(tenant_id,site_id,action_id) REFERENCES action(tenant_id,site_id,id),
 CONSTRAINT work_action_event_fk FOREIGN KEY(tenant_id,site_id,action_event_id) REFERENCES action_event(tenant_id,site_id,id)
);
CREATE TABLE work_case_evidence (
 tenant_id uuid NOT NULL, site_id uuid NOT NULL, case_revision_id uuid NOT NULL,
 evidence_id uuid NOT NULL,
 PRIMARY KEY(case_revision_id,evidence_id),
 CONSTRAINT work_case_evidence_revision_fk FOREIGN KEY(tenant_id,site_id,case_revision_id)
   REFERENCES work_case_revision(tenant_id,site_id,id),
 CONSTRAINT work_case_evidence_accepted_fk FOREIGN KEY(tenant_id,site_id,evidence_id)
   REFERENCES accepted_evidence(tenant_id,site_id,id)
);
CREATE TABLE work_event (
 id uuid PRIMARY KEY, tenant_id uuid NOT NULL, site_id uuid NOT NULL, case_id uuid NOT NULL,
 kind text NOT NULL CHECK(kind IN ('CREATED','ASSIGN','CLOSE','REOPEN','CANCEL','COMPLETE','OPEN_VERIFICATION','COMMENT')),
 payload jsonb NOT NULL DEFAULT '{}'::jsonb,
 occurred_at timestamptz NOT NULL, recorded_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 actor_kind text NOT NULL CHECK(actor_kind IN ('USER','SERVICE')),
 actor_id text NOT NULL CHECK(length(btrim(actor_id)) BETWEEN 1 AND 128),
 authorization_basis text NOT NULL CHECK(length(btrim(authorization_basis)) BETWEEN 1 AND 500),
 attestation text NOT NULL CHECK(length(btrim(attestation)) BETWEEN 1 AND 1000),
 idempotency_key text NOT NULL CHECK(length(idempotency_key) BETWEEN 8 AND 128),
 payload_sha256 text NOT NULL CHECK(payload_sha256 ~ '^[0-9a-f]{64}$'),
 CONSTRAINT work_event_case_fk FOREIGN KEY(tenant_id,site_id,case_id) REFERENCES work_case(tenant_id,site_id,id),
 CONSTRAINT work_event_once UNIQUE(case_id,idempotency_key),
 CONSTRAINT work_event_scope UNIQUE(tenant_id,site_id,id)
);
CREATE INDEX work_event_order ON work_event(case_id,recorded_at,id);
CREATE TABLE maintenance_plan (
 id uuid PRIMARY KEY, tenant_id uuid NOT NULL, site_id uuid NOT NULL, asset_id uuid NULL,
 public_no bigint NOT NULL UNIQUE CHECK(public_no>0),
 public_code text NOT NULL CHECK(public_code ~ '^PM-[0-9]{6,}$'),
 canonical_plan_id uuid NOT NULL,
 title text NOT NULL CHECK(length(btrim(title)) BETWEEN 1 AND 200),
 trigger_kind text NOT NULL CHECK(trigger_kind IN ('CALENDAR','RUN_HOURS')),
 next_due_at timestamptz NULL, next_due_hours numeric NULL,
 state text NOT NULL CHECK(state IN ('DRAFT','ACTIVE','PAUSED','CANCELLED')),
 supersedes_plan_id uuid NULL, actor_id text NOT NULL CHECK(length(btrim(actor_id)) BETWEEN 1 AND 128),
 actor_kind text NOT NULL CHECK(actor_kind IN ('USER','SERVICE')),
 authorization_basis text NOT NULL CHECK(length(btrim(authorization_basis)) BETWEEN 1 AND 500),
 occurred_at timestamptz NOT NULL, correction_reason text NULL CHECK(correction_reason IS NULL OR length(btrim(correction_reason)) BETWEEN 1 AND 500),
 attestation text NOT NULL CHECK(length(btrim(attestation)) BETWEEN 1 AND 1000),
 idempotency_key text NOT NULL CHECK(length(idempotency_key) BETWEEN 8 AND 128),
 payload_sha256 text NOT NULL CHECK(payload_sha256 ~ '^[0-9a-f]{64}$'),
 recorded_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 CONSTRAINT maintenance_plan_site_fk FOREIGN KEY(tenant_id,site_id) REFERENCES site(tenant_id,id),
 CONSTRAINT maintenance_plan_asset_fk FOREIGN KEY(tenant_id,site_id,asset_id) REFERENCES asset(tenant_id,site_id,id),
 CONSTRAINT maintenance_plan_prev_fk FOREIGN KEY(tenant_id,site_id,supersedes_plan_id) REFERENCES maintenance_plan(tenant_id,site_id,id),
 CONSTRAINT maintenance_plan_canonical_fk FOREIGN KEY(tenant_id,site_id,canonical_plan_id) REFERENCES maintenance_plan(tenant_id,site_id,id),
 CONSTRAINT maintenance_plan_root CHECK((supersedes_plan_id IS NULL AND canonical_plan_id=id) OR supersedes_plan_id IS NOT NULL),
 CONSTRAINT maintenance_plan_due CHECK ((trigger_kind='CALENDAR' AND next_due_hours IS NULL) OR (trigger_kind='RUN_HOURS' AND next_due_at IS NULL AND (next_due_hours IS NULL OR next_due_hours>=0))),
 CONSTRAINT maintenance_plan_scope UNIQUE(tenant_id,site_id,id),
 CONSTRAINT maintenance_plan_code UNIQUE(tenant_id,public_code),
 CONSTRAINT maintenance_plan_once UNIQUE(tenant_id,site_id,idempotency_key),
 CONSTRAINT maintenance_plan_one_successor UNIQUE(supersedes_plan_id)
);
CREATE INDEX maintenance_plan_site ON maintenance_plan(tenant_id,site_id,recorded_at DESC,id);
CREATE TABLE maintenance_record (
 id uuid PRIMARY KEY, tenant_id uuid NOT NULL, site_id uuid NOT NULL, case_id uuid NOT NULL,
 supersedes_record_id uuid NULL, activity text NOT NULL CHECK(length(btrim(activity)) BETWEEN 1 AND 4000),
 outcome_note text NULL CHECK(outcome_note IS NULL OR length(btrim(outcome_note)) BETWEEN 1 AND 2000),
 occurred_at timestamptz NOT NULL, recorded_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 actor_id text NOT NULL CHECK(length(btrim(actor_id)) BETWEEN 1 AND 128),
 actor_kind text NOT NULL CHECK(actor_kind IN ('USER','SERVICE')),
 authorization_basis text NOT NULL CHECK(length(btrim(authorization_basis)) BETWEEN 1 AND 500),
 attestation text NOT NULL CHECK(length(btrim(attestation)) BETWEEN 1 AND 1000),
 idempotency_key text NOT NULL CHECK(length(idempotency_key) BETWEEN 8 AND 128),
 payload_sha256 text NOT NULL CHECK(payload_sha256 ~ '^[0-9a-f]{64}$'),
 CONSTRAINT maintenance_record_case_fk FOREIGN KEY(tenant_id,site_id,case_id) REFERENCES work_case(tenant_id,site_id,id),
 CONSTRAINT maintenance_record_prev_fk FOREIGN KEY(tenant_id,site_id,supersedes_record_id) REFERENCES maintenance_record(tenant_id,site_id,id),
 CONSTRAINT maintenance_record_scope UNIQUE(tenant_id,site_id,id),
 CONSTRAINT maintenance_record_once UNIQUE(case_id,idempotency_key),
 CONSTRAINT maintenance_record_one_successor UNIQUE(supersedes_record_id)
);
CREATE INDEX maintenance_record_case ON maintenance_record(case_id,recorded_at DESC,id);
CREATE TABLE operational_record (
 id uuid PRIMARY KEY, tenant_id uuid NOT NULL, site_id uuid NOT NULL,
 public_no bigint NOT NULL UNIQUE CHECK(public_no>0),
 public_code text NOT NULL CHECK(public_code ~ '^REC-[0-9]{6,}$'),
 canonical_record_id uuid NOT NULL,
 kind text NOT NULL CHECK(kind IN ('OPERATOR_LOG','MANUAL_READING','SHIFT_NOTE','SITE_VISIT')),
 body text NOT NULL CHECK(length(btrim(body)) BETWEEN 1 AND 4000),
 period_end timestamptz NULL, unit text NULL CHECK(unit IS NULL OR length(btrim(unit)) BETWEEN 1 AND 32),
 quantity numeric NULL CHECK(quantity IS NULL OR (quantity >= 0 AND quantity < 'Infinity'::numeric)),
 source_document_sha256 text NULL CHECK(source_document_sha256 IS NULL OR source_document_sha256 ~ '^[0-9a-f]{64}$'),
 correction_reason text NULL CHECK(correction_reason IS NULL OR length(btrim(correction_reason)) BETWEEN 1 AND 500),
 state text NOT NULL CHECK(state IN ('SUBMITTED','ACCEPTED','REJECTED')),
 supersedes_record_id uuid NULL, case_id uuid NULL,
 occurred_at timestamptz NOT NULL, recorded_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 actor_id text NOT NULL CHECK(length(btrim(actor_id)) BETWEEN 1 AND 128),
 actor_kind text NOT NULL CHECK(actor_kind IN ('USER','SERVICE')),
 authorization_basis text NOT NULL CHECK(length(btrim(authorization_basis)) BETWEEN 1 AND 500),
 attestation text NOT NULL CHECK(length(btrim(attestation)) BETWEEN 1 AND 1000),
 idempotency_key text NOT NULL CHECK(length(idempotency_key) BETWEEN 8 AND 128),
 payload_sha256 text NOT NULL CHECK(payload_sha256 ~ '^[0-9a-f]{64}$'),
 CONSTRAINT operational_record_site_fk FOREIGN KEY(tenant_id,site_id) REFERENCES site(tenant_id,id),
 CONSTRAINT operational_record_case_fk FOREIGN KEY(tenant_id,site_id,case_id) REFERENCES work_case(tenant_id,site_id,id),
 CONSTRAINT operational_record_prev_fk FOREIGN KEY(tenant_id,site_id,supersedes_record_id) REFERENCES operational_record(tenant_id,site_id,id),
 CONSTRAINT operational_record_canonical_fk FOREIGN KEY(tenant_id,site_id,canonical_record_id) REFERENCES operational_record(tenant_id,site_id,id),
 CONSTRAINT operational_record_root CHECK((supersedes_record_id IS NULL AND canonical_record_id=id) OR supersedes_record_id IS NOT NULL),
 CONSTRAINT operational_record_period CHECK(period_end IS NULL OR period_end >= occurred_at),
 CONSTRAINT operational_record_quantity CHECK((quantity IS NULL)=(unit IS NULL)),
 CONSTRAINT operational_record_scope UNIQUE(tenant_id,site_id,id),
 CONSTRAINT operational_record_code UNIQUE(tenant_id,public_code),
 CONSTRAINT operational_record_once UNIQUE(tenant_id,site_id,idempotency_key),
 CONSTRAINT operational_record_one_successor UNIQUE(supersedes_record_id)
);
CREATE INDEX operational_record_site ON operational_record(tenant_id,site_id,occurred_at DESC,id);
CREATE FUNCTION w4_append_only() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN RAISE EXCEPTION 'W4 work history is append only' USING ERRCODE='23514'; END $$;
CREATE TRIGGER work_case_immutable BEFORE UPDATE OR DELETE ON work_case FOR EACH ROW EXECUTE FUNCTION w4_append_only();
CREATE TRIGGER incident_immutable BEFORE UPDATE OR DELETE ON incident FOR EACH ROW EXECUTE FUNCTION w4_append_only();
CREATE TRIGGER maintenance_work_request_immutable BEFORE UPDATE OR DELETE ON maintenance_work_request FOR EACH ROW EXECUTE FUNCTION w4_append_only();
CREATE TRIGGER work_case_finding_link_immutable BEFORE UPDATE OR DELETE ON work_case_finding_link FOR EACH ROW EXECUTE FUNCTION w4_append_only();
CREATE TRIGGER work_case_action_link_immutable BEFORE UPDATE OR DELETE ON work_case_action_link FOR EACH ROW EXECUTE FUNCTION w4_append_only();
CREATE TRIGGER work_revision_immutable BEFORE UPDATE OR DELETE ON work_case_revision FOR EACH ROW EXECUTE FUNCTION w4_append_only();
CREATE TRIGGER work_case_evidence_immutable BEFORE UPDATE OR DELETE ON work_case_evidence FOR EACH ROW EXECUTE FUNCTION w4_append_only();
CREATE TRIGGER work_event_immutable BEFORE UPDATE OR DELETE ON work_event FOR EACH ROW EXECUTE FUNCTION w4_append_only();
CREATE TRIGGER maintenance_plan_immutable BEFORE UPDATE OR DELETE ON maintenance_plan FOR EACH ROW EXECUTE FUNCTION w4_append_only();
CREATE TRIGGER maintenance_record_immutable BEFORE UPDATE OR DELETE ON maintenance_record FOR EACH ROW EXECUTE FUNCTION w4_append_only();
CREATE TRIGGER operational_record_immutable BEFORE UPDATE OR DELETE ON operational_record FOR EACH ROW EXECUTE FUNCTION w4_append_only();
"""

def upgrade():
    op.execute(SCHEMA)

def downgrade():
    bind = op.get_bind()
    for table in ("operational_record", "maintenance_record", "maintenance_plan", "work_event", "work_case_evidence", "work_case_action_link", "work_case_finding_link", "work_case_revision", "maintenance_work_request", "incident", "work_case"):
        if bind.execute(text(f"SELECT 1 FROM {table} LIMIT 1")).first():
            raise RuntimeError("0027 downgrade requires empty W4 work tables")
    for table in ("operational_record", "maintenance_record", "maintenance_plan", "work_event", "work_case_evidence", "work_case_action_link", "work_case_finding_link", "work_case_revision", "maintenance_work_request", "incident", "work_case"):
        op.execute(f"DROP TABLE {table}")
    op.execute("DROP FUNCTION w4_append_only()")
    op.execute("DROP SEQUENCE work_public_no_seq")
```

The service additionally checks mandatory child identity, same-case `COMPLETE` record, exact ActionEvent ownership, case kind and transitions; SQL scoped FKs are a second boundary. A sequence gap on rollback is allowed. `work_case_evidence` stores the complete exact cited set for each case revision, including the initial revision; correction replaces the set rather than applying a delta. Link arrays contain `{"id":"<finding UUID>","revision_id":"<exact revision UUID>"}` and `{"id":"<action UUID>","event_id":"<exact event UUID>"}`, sorted by ID with no duplicate pair; service verifies each event belongs to the named Action. The migration test proves downgrade refuses nonempty data and a clean downgrade leaves 0026 intact; no CASCADE. At installation, check actual 0026 revision spelling. If it differs, amend this spec before building; do not invent a second head.

## API wire and refusals

Routes use bearer principal and existing tenant Site scope; unknown/foreign IDs are 404 without disclosing existence. Body IDs below are test constants, not product seed. `GET /api/sites/{site_code}/work/{kind}?from=...&to=...&known_at=...&limit=50&cursor=...` accepts `kind=incidents|maintenance`; `POST /api/sites/{site_code}/work/cases`; `POST /api/sites/{site_code}/work/cases/{id}/events`; `POST /api/sites/{site_code}/work/cases/{id}/revisions`; `POST /api/sites/{site_code}/work/cases/{id}/records`; `POST /api/sites/{site_code}/work/plans`; `POST /api/sites/{site_code}/work/operational-records`; `GET /api/sites/{site_code}/work/cases/{id}?known_at=...`. `POST` returns 201 with exact object ID, code and revision/event ID; exact idempotent retry returns 200 with the same IDs. A reused key with different canonical JSON SHA-256 is 409.

```json
{"kind":"INCIDENT","occurred_at":"2026-10-06T16:11:00Z","asset_id":null,"finding_links":[],"action_links":[],"title":"Witnessed start request failed","narrative":"Operator observed a failed start request; cause not established.","cited_accepted_evidence_ids":[],"actor":{"kind":"SERVICE","id":"w401-fixture","attestation":"service=w401-fixture;job=positive-case;rule=w401/1"},"idempotency_key":"w401-incident-001"}
```

```json
{"schema_version":"work-case-1","id":"10000000-0000-4000-8000-000000000101","code":"INC-000001","kind":"INCIDENT","site_id":"10000000-0000-4000-8000-000000000001","revision":{"id":"10000000-0000-4000-8000-000000000102","number":1},"event":{"id":"10000000-0000-4000-8000-000000000103","kind":"CREATED","recorded_at":"2026-10-06T16:12:00Z"},"state":"OPEN","source_provenance":{"classification":"UNKNOWN","source_ids":[],"evidence_ids":[],"basis_sha256":"sha256:<computed-64-hex>","reasons":[{"code":"EMPTY_CITATION_SET","accepted_evidence_ids":[]}],"state":"UNKNOWN"}}
```

```json
{"kind":"ASSIGN","occurred_at":"2026-10-06T16:20:00Z","payload":{"assignee":"maintenance-lead"},"actor":{"kind":"SERVICE","id":"w401-fixture","attestation":"service=w401-fixture;job=positive-case;rule=w401/1"},"idempotency_key":"w401-assign-001"}
```

The same create route accepts a maintenance request with `{"kind":"MAINTENANCE_REQUEST","occurred_at":"2026-10-06T18:40:00Z","asset_id":"10000000-0000-4000-8000-000000000401","incident_id":"10000000-0000-4000-8000-000000000101","finding_links":[],"action_links":[],"title":"Inspect starter circuit","narrative":"Witnessed failure requires inspection.","cited_accepted_evidence_ids":[],"actor":{"kind":"USER","id":"operator-1","authorization_basis":"SITE_WORK_WRITE","attestation":"I requested inspection."},"idempotency_key":"w401-request-001"}`. It returns `{"schema_version":"work-case-1","id":"10000000-0000-4000-8000-000000000501","code":"WR-000002","kind":"MAINTENANCE_REQUEST","revision":{"id":"10000000-0000-4000-8000-000000000502","number":1},"event":{"id":"10000000-0000-4000-8000-000000000503","kind":"CREATED","recorded_at":"2026-10-06T18:41:00Z"},"state":"OPEN"}` plus the same site/source fields as the Incident response. `incident_id` is legal only for a request and must be same Site. `POST .../records` takes `{"activity":"Starter connection inspected","outcome_note":null,"occurred_at":"2026-10-06T19:00:00Z","actor":{"kind":"USER","id":"tech-1","authorization_basis":"SITE_WORK_WRITE","attestation":"I performed this inspection."},"idempotency_key":"w401-record-001"}` and returns `{"id":"10000000-0000-4000-8000-000000000504","case_id":"10000000-0000-4000-8000-000000000501","recorded_at":"2026-10-06T19:30:00Z","outcome":"UNVERIFIED"}`. `COMPLETE` then names that record ID in event payload; an absent/foreign ID is 422 `WORK_LINK_SCOPE_INVALID`.

`POST .../revisions` takes `{"supersedes_revision_id":"10000000-0000-4000-8000-000000000102","title":"Witnessed start request failed","narrative":"Corrected occurrence note; cause remains unknown.","cited_accepted_evidence_ids":[],"reason":"Corrected operator time note","actor":{"kind":"USER","id":"operator-1","authorization_basis":"SITE_WORK_WRITE","attestation":"I corrected my account."},"idempotency_key":"w401-correct-001"}` and returns `{"case_id":"10000000-0000-4000-8000-000000000101","revision_id":"10000000-0000-4000-8000-000000000104","revision_no":2,"supersedes_revision_id":"10000000-0000-4000-8000-000000000102"}`. The link arrays are copied from the predecessor unless explicitly supplied; an explicit empty array removes current links in the new revision only, never history. `POST .../plans` takes `{"asset_id":null,"title":"Witnessed start test","trigger_kind":"CALENDAR","next_due_at":null,"next_due_hours":null,"actor":{"kind":"USER","id":"manager-1","authorization_basis":"SITE_WORK_WRITE","attestation":"Draft plan for review."},"idempotency_key":"w401-plan-001"}` and returns `{"canonical_plan_id":"10000000-0000-4000-8000-000000000601","public_code":"PM-000003","state":"DRAFT"}`. `POST .../operational-records` takes `{"kind":"OPERATOR_LOG","body":"Generator started by hand","occurred_at":"2026-10-06T16:14:00Z","period_end":null,"unit":null,"quantity":null,"source_document_sha256":null,"case_id":"10000000-0000-4000-8000-000000000101","actor":{"kind":"USER","id":"operator-1","authorization_basis":"SITE_WORK_WRITE","attestation":"I made this log entry."},"idempotency_key":"w401-oprec-001"}` and returns `{"canonical_record_id":"10000000-0000-4000-8000-000000000701","public_code":"REC-000004","state":"SUBMITTED"}`. Values and IDs in this paragraph are test-wire examples only.

For a plan correction, the same `POST .../plans` includes `supersedes_plan_id`, `canonical_plan_id` and `correction_reason`; for an OperationalRecord correction the same `POST .../operational-records` includes `supersedes_record_id`, `canonical_record_id` and `correction_reason`. Omission of those three fields means create. A correction repeats the exact root code in the response while returning its new version UUID. Both routes refuse a non-head predecessor and a mismatched canonical root with 409 `WORK_BASIS_CHANGED`. Store the canonical JSON SHA-256 beside each idempotency key in service transaction logic; the SQL uniques prevent double submission and the service compares payload before returning the prior result. These are the only plan/OperationalRecord mutation shapes in W4; ACTIVATE/ACCEPT are reserved.

```json
{"schema_version":"site-work-index-1","site_code":"KOBO-001","site_name":"Kobo Mini-grid","window":{"from":"2026-10-06T00:00:00Z","to":"2026-10-07T00:00:00Z","bounds":"[from, to)"},"known_at":"2026-10-07T00:00:00Z","status":"CURRENT","coverage":{"state":"COMPLETE","reason":null},"source_provenance":{"classification":"UNKNOWN","state":"UNKNOWN","source_ids":[],"evidence_ids":[],"basis_sha256":"sha256:<computed-64-hex>","reasons":[{"code":"EMPTY_CITATION_SET","accepted_evidence_ids":[]}]},"total_count":1,"rows":[{"case_id":"10000000-0000-4000-8000-000000000101","revision_id":"10000000-0000-4000-8000-000000000102","code":"INC-000001","title":"Witnessed start request failed","narrative":"Operator observed a failed start request; cause not established.","occurred_at":"2026-10-06T16:11:00Z","recorded_at":"2026-10-06T16:12:00Z","state":"OPEN","asset_id":null,"asset_label":null,"finding_links":[],"action_links":[],"url":null}],"next_cursor":null,"selection_token":"sha256:<computed-64-hex>"}
```

`url:null` is deliberate until W6-01 detail route review; the API detail above is an exact scoped API route, not a product page. A nonempty row does not create a clickable dead end. The read's `status` is `CURRENT` for a consistent authored store snapshot, `HISTORICAL` for a prior explicit cutoff, `PENDING_RECOMPUTE` if a pinned analytic link has overlapping PENDING/LEASED/FAILED work, `STALE_SOURCE` for a cited selected source reported stale, `UNKNOWN` if a linked selection is absent. Authored case count remains a count of persisted cases even when linked analytic status is unknown; do not call the case itself current evidence. `coverage` is COMPLETE/PARTIAL/UNKNOWN per linked selected reads, separate from case-store availability.

| HTTP | Code | Exact response message / UI copy |
| --- | --- | --- |
| 401 | `UNAUTHENTICATED` | `Sign in to read work.` / `Sign in to see work at this site.` |
| 403 | `SITE_SCOPE_FORBIDDEN` | `No access to Site '{code}'.` / `You do not have access to this site's work.` |
| 403 | `WORK_WRITE_FORBIDDEN` | `This actor cannot change work at this site.` / `You cannot change this work record.` |
| 404 | `SITE_NOT_FOUND` | `No imported Site '{code}' in this tenant.` / `This site was not found.` |
| 404 | `WORK_CASE_NOT_FOUND` | `No work case with this ID at this site.` / `This work case was not found at this site.` |
| 409 | `WORK_EVENT_DUPLICATE_KEY` | `This key was used for different work content.` / `This work change conflicts with an earlier submission.` |
| 409 | `WORK_TRANSITION_INVALID` | `This transition is not allowed from the selected state.` / `This change is not available from the current state.` |
| 409 | `WORK_BASIS_CHANGED` | `The work list changed; request page one without a cursor.` / `The list changed. Reload the first page.` |
| 409 | `WORK_OUTCOME_NOT_SUPPORTED` | `No frozen outcome plan and accepted later evidence support this outcome.` / `Outcome unverified; a witnessed result is still needed.` |
| 422 | `WORK_INPUT_INVALID` | `A required work field or UTC time is invalid.` / `Check the work details and try again.` |
| 422 | `WORK_LINK_SCOPE_INVALID` | `A linked record is not in this Site and tenant.` / `One linked record does not belong to this site.` |
| 422 | `INVALID_CURSOR` | `The cursor is not a work-list cursor.` / `Reload the work list.` |
| 503 | `WORK_STORE_UNAVAILABLE` | `Work records could not be read or saved.` / `Work records are unavailable right now. Try again.` |

JSON refusals are `{"detail":{"code":"...","message":"...","rows":null,"total_count":null}}` for list requests; mutations omit `rows/total_count`. Do not return 200 empty on 503/403. Validate scope before query shape; then UTC/window/limit/cursor; then snapshot. Limit default 50, max 100. Cursor is URL-safe base64 canonical sorted-key JSON `{v:1,tenant_id,site_id,kind,from,to,known_at,selection_token,after:[occurred_at,id]}`; for maintenance use `created_at` as after time. Bind to full snapshot fence and auth Site set. Malformed is 422, changed basis/scope 409. Sort time descending, UUID ascending. No offset pagination; total and source classification use the **full** selected set.

## Fixture and exact test contract

Create `backend/tests/fixtures/w4/w401-work.json` with sorted keys, UTF-8 final LF, schema `w401-work/1`. Resolve actual `KOBO-001`, `COLD-LAB-001` and `EV-LAB-001` Site/Foundation IDs by public Site reads after W2 merge. Positive W4 Site UI branch is KOBO-001: create a SERVICE-attested Incident, request, activity record and draft plan through W4 API; cite only exact accepted IDs from ordinary public W1 reads, and pin any Finding revision IDs actually returned. The cold and EV Sites are cross-scope negatives/read-only provenance controls; W5-02 owns their Work tabs. `outcome` remains `UNVERIFIED`. Negative branches: empty mini-grid, foreign Asset/Finding/Action/event, absent accepted ID, duplicate key with different body, backdated event and correction, stale linked selection, and unavailable store. Test generator captures server UUIDs into the fixture output in its own DB; static source fixture contains deterministic input keys and expected semantic assertions, not invented resolved IDs. Do not seed INC-203/WR-019 or INSERT private Lab state.

Named proof: `backend/tests/test_w401_migration_postgres.py::{test_0027_parent_scoped_fks_append_only_and_clean_downgrade,test_0027_nonempty_downgrade_refuses}`; `backend/tests/test_w401_work_service_postgres.py::{test_incident_attestation_reload_and_exact_links,test_request_complete_stays_unverified,test_transitions_and_correction_total_order,test_foreign_asset_and_evidence_refuse,test_idempotency_payload_conflict,test_plan_draft_version_and_due,test_operational_record_attested_correction}`; `backend/tests/test_w401_site_indexes_postgres.py::{test_site_window_cutoff_and_empty_count,test_pending_link_and_missing_source_keep_gap,test_cursor_fence_and_full_count}`; `frontend/src/sites/__tests__/siteWorkCases.test.tsx::{incident_stocked_empty_and_refused,maintenance_activity_without_outcome,narrow_mock_panels_and_unavailable_links}`. Preserve W1 Action lifecycle tests and W2 cold/EV exact-ID tests. Update any literal Alembic HEAD in `backend/tests/test_w205a_ev_migration.py`, `test_w204_cold_migration.py`, `test_w203_cold_migration_postgres.py`, and W2-07 migration test from `0026` to `0027` **only where asserting upgraded head**; direct-target 0024/0025/0026 assertions stay exact. Count expectation: +11 tables, +11 append-only triggers, +7 explicit indexes, +1 sequence, +1 function; re-count catalog index totals with implicit PK/UNIQUE indexes instead of weakening to `>=`. Focused test count adds exactly 2+7+3 backend nodes and 3 frontend nodes; collection/JUnit must confirm, not guess suite total.

## Per-panel copy and layout dry-read

`frontend/mockups/v69/browser-review.json` measures both target pages at 1440 width and **1101 px page height** (the 1100 viewport floor). A direct Chrome DOM-rectangle measurement of the named screens at 1440/390 gives the table below; heights are pixels, cap is `floor(1.30 × mock)`. These are the panel budgets, and the 1440 whole-page cap is **1431 px**. Re-measure mock and app in the commit-5 capture; a viewport-floor page height is not a panel height. At 390 no page-level horizontal scroll; table alone may scroll with a visible affordance and retained first column. Status and notice wrap to at most two lines each at 1440; no clipped chip.

| Route / piece | 1440 mock → cap | 390 mock → cap |
| --- | ---: | ---: |
| Incidents status | 37 → 48 | 91 → 118 |
| Incidents panel | 316 → 410 | 354 → 460 |
| Incidents notice | 42 → 54 | 78 → 101 |
| Maintenance status | 37 → 48 | 91 → 118 |
| Maintenance panel | 296 → 384 | 316 → 410 |
| Maintenance notice | 42 → 54 | 78 → 101 |

The mock's 390 whole page is 1215 px for each route (cap 1579 px). App content may be taller only inside these piece caps; the initial state must keep every slot. The stocked replay has more than the mock's zero rows, so show at most the first 5 in the panel with in-panel paging and keep count from the full query.

| Slot | Source field / exact visible copy | Width and behavior |
| --- | --- | --- |
| Shared Work subrow | `Actions` (existing route), `Incidents`, `Maintenance`; active route | One row at 1440; 390 horizontally scrollable subrow, no text clipping. Only these two occurrences become interactive. |
| Status strip | `site.name`, `total_count`, `status`, `coverage`: `Scoped to {site short name} · {n} incidents/maintenance` only when count known; else `Count unknown · work source unavailable`. Detail `Same records and states as the global ... list` becomes `These are work records at this site`; global Manage link is static `Manage in Incidents/Maintenance · Not available yet`. | 100% panel width; status 60%, explanatory 40%; at 390 stack. |
| Incident panel heading/header | `Incidents at this site`; `Case`=`code · title`, `Window`=`occurred_at` in EAT with UTC in disclosure, `What happened`=`narrative`, `Linked findings`=pinned exact Finding links or `No linked finding`, `State`=reduced event state. | Columns 22/16/29/19/14%; 2-line title/narrative clamp then disclosure, IDs never truncated in disclosure; 390 table min-width 720 px. |
| Incident empty | `No incidents at this site`; `No operational case was opened in the selected period. A case comes from a linked chain of events, not from a single data gap.` from `total_count=0` and COMPLETE store read. | Keep mock empty block, no fake row. |
| Maintenance panel heading/header | `Maintenance at this site`; `Work request`=`code · title`; `Asset`=same-site asset code/name or `No asset linked`; `Activity`=latest `maintenance_record.activity` or `No activity recorded`; `Outcome`=`Unverified` unless later outcome evaluator exists; `Next evidence`=authored plan criterion or `No next evidence recorded`. | Columns 22/18/23/15/22%; 2-line cells with detail disclosure; 390 min-width 760 px. |
| Maintenance empty | `No maintenance work at this site`; `No inspection or repair has been raised here in the selected period.` from full count zero. | Keep mock empty block. |
| Panel subcopy | Incident: `A case links chronology, findings and work without copying them`; maintenance: `Completed work is activity; the outcome is verified separately`. These describe model, no source field. | Under heading, one/two wrapped lines. |
| Context notice | `Opening a record moves you to its own area; the breadcrumb keeps this site. New work starts from the global create flow with this site filled in.` becomes `Case history is stored with this site. A global work page and create flow are not available yet.` until W6. | Blue/neutral information, no link. |
| Missing/pending/refused | `No selected source for linked evidence`; `Linked evidence is being reassessed`; 403/404/503 copy from refusal table. Distinguish count zero from unavailable; use source notice from shared DTO. | Amber for pending, red for refusal, neutral for unknown; source class is never an equipment-health chip. |

Chip tones: OPEN/IN_PROGRESS amber, CLOSED/COMPLETED blue, CANCELLED neutral, VERIFICATION_WINDOW blue, UNVERIFIED amber, missing/UNKNOWN neutral, genuine refused red. `Prepared example data` and `Generated test data` use `sourceProvenance.tsx:SOURCE_WORDS` and neutral disclosure, never a green equipment condition. `url:null` and absent Asset/Finding links render text, no href/handler/tab stop. `Work` Site tab remains existing; no new root item.

The closed unavailable multiset before W4 is `Recommendation×2, Alternatives×1, Scenarios×1, Incidents×1, Maintenance×1, Cooling×1, Availability×1, Energy / site power×1`; chips `Cost×1, Risks×1, Opportunities×1`. **After W4 only** remove `Incidents×1` and `Maintenance×1`: tabs are `Recommendation×2, Alternatives×1, Scenarios×1, Cooling×1, Availability×1, Energy / site power×1`; chips unchanged. Update `tools/checks/navigation-truthfulness.ps1` and positive/negative fixtures atomically; retain unavailable **rail** Incidents/Maintenance because W6 owns global routes. W3 retains the three Site Finding chips, so no W3 chip removal is expected.

## Frozen surface and closeout

At independent ACCEPT and merge, freeze: the six identities and Action separation; states/transition table including unreached outcomes; actor/attestation and DB event order; append-only correction chains; tenant/Site/Asset/exact Finding/Action/evidence links; API paths, JSON keys, codes, cursor and cutoff behavior; provenance rule and selected Site read shapes. W3/W5/W6 consume this version. An amendment names the exact clause, migration/compatibility effect and all lane consumers, then receives an Architect decision and compatibility test before implementation.

Run focused tests at each commit, architecture/workflow/rule-8/navigation/registry checks, frontend typecheck/build, and one same-revision real-Postgres full backend suite with JUnit zero failed/skipped. Private DB name ends `_test`; one full suite at a time. Review packet records revision, migration SHA, fixture exact IDs, both route captures at 1440/390, rectangle measurements, currentness/empty/refusal replay and test-count deltas. Owner W4 result review follows independent review.

## Review closure (2026-10-20)

This section supersedes conflicting earlier examples. The schema columns added above are binding. The placeholder `sha256:<computed-64-hex>` is documentation notation; an API response returns the computed value. W4's two Site UI tabs are **KOBO-001 only**. COLD-LAB-001 and EV-LAB-001 are fixture scope/provenance controls, with their Work tabs left for W5-02.

### Wire, mutation and storage (B1–B8, B11; S12–S18, S30; N34–N36)

* **B1/B2:** Both list rows carry `case_id,revision_id,code,title,narrative,occurred_at,recorded_at,state,asset_id,asset_label,finding_links,action_links,url,source_provenance`. Each Finding link is `{finding_id,finding_revision_id,label,href}` with label `Finding {first 8 UUID chars}` and `siteFindingHref(site_id,finding_id,revision_id)`; Action link has `{action_id,action_event_id,label,href}`. Asset label is `asset.code · asset.name` from the scoped Asset read or null. Maintenance rows additionally carry `activity` (latest same-case record text or null), `outcome_note` (string/null), `outcome_state:"UNVERIFIED"`, `next_evidence:null`, `next_evidence_copy:"No next evidence recorded"`, `request_state` equal to reduced case state, `record_id` (UUID/null), and `incident_id` (UUID/null). Plans are separate draft resources and **not** list rows. No `maintenance_plan` criterion or request–plan link is invented; the mock's Next evidence column shows the explicit missing copy until a later reviewed verification contract supplies it.

  Literal maintenance list row (fixed UUIDs here are injected test IDs):

  ```json
  {"case_id":"10000000-0000-4000-8000-000000000501","revision_id":"10000000-0000-4000-8000-000000000502","code":"WR-000002","title":"Inspect starter circuit","narrative":"Witnessed failure requires inspection.","occurred_at":"2026-10-06T18:40:00Z","recorded_at":"2026-10-06T18:41:00Z","state":"COMPLETED","request_state":"COMPLETED","asset_id":null,"asset_label":null,"incident_id":"10000000-0000-4000-8000-000000000101","finding_links":[],"action_links":[],"record_id":"10000000-0000-4000-8000-000000000504","activity":"Starter connection inspected","outcome_note":null,"outcome_state":"UNVERIFIED","next_evidence":null,"next_evidence_copy":"No next evidence recorded","url":null,"source_provenance":{"classification":"UNKNOWN","state":"UNKNOWN","source_ids":[],"evidence_ids":[],"basis_sha256":"sha256:<computed-64-hex>","reasons":[{"code":"EMPTY_CITATION_SET","accepted_evidence_ids":[]}]}}
  ```
* **B3:** `GET /api/sites/{site_code}/work/cases/{id}?known_at=` returns exactly `{schema_version:"work-case-detail-1",site_code,case:{id,code,kind,asset_id,occurred_at,created_at,state,incident_id},selected_revision:{id,revision_no,supersedes_revision_id,title,narrative,reason,recorded_at,actor_kind,actor_id,occurred_at},finding_links:[...],action_links:[...],cited_accepted_evidence_ids:[...],events:[{id,kind,payload,occurred_at,recorded_at,actor_kind,actor_id}],records:[{id,activity,outcome_note,occurred_at,recorded_at,supersedes_record_id}],source_provenance:{...},coverage:{state,reason}}`; arrays sort `(recorded_at,id)` except links/IDs lexical UUID. 404 for absent/foreign case. POST event returns `{schema_version:"work-event-1",case_id,event:{id,kind,payload,occurred_at,recorded_at},state,revision_id}`; exact retry returns identical body with 200. POST create keeps its documented `work-case-1` body with computed provenance basis. Plan/record/operational POST response adds `id,recorded_at` and the documented canonical ID/code/state.

  Literal minimal detail body (injected IDs; computed digest substituted by the test harness):

  ```json
  {"schema_version":"work-case-detail-1","site_code":"KOBO-001","case":{"id":"10000000-0000-4000-8000-000000000101","code":"INC-000001","kind":"INCIDENT","asset_id":null,"occurred_at":"2026-10-06T16:11:00Z","created_at":"2026-10-06T16:12:00Z","state":"OPEN","incident_id":null},"selected_revision":{"id":"10000000-0000-4000-8000-000000000102","revision_no":1,"supersedes_revision_id":null,"title":"Witnessed start request failed","narrative":"Operator observed a failed start request; cause not established.","reason":null,"recorded_at":"2026-10-06T16:12:00Z","actor_kind":"SERVICE","actor_id":"w401-fixture","occurred_at":"2026-10-06T16:11:00Z"},"finding_links":[],"action_links":[],"cited_accepted_evidence_ids":[],"events":[{"id":"10000000-0000-4000-8000-000000000103","kind":"CREATED","payload":{},"occurred_at":"2026-10-06T16:11:00Z","recorded_at":"2026-10-06T16:12:00Z","actor_kind":"SERVICE","actor_id":"w401-fixture"}],"records":[],"source_provenance":{"classification":"UNKNOWN","state":"UNKNOWN","source_ids":[],"evidence_ids":[],"basis_sha256":"sha256:<computed-64-hex>","reasons":[{"code":"EMPTY_CITATION_SET","accepted_evidence_ids":[]}]},"coverage":{"state":"COMPLETE","reason":null}}
  ```
* **B4:** Event `payload` is a closed JSON object. `CREATED` is server-only `{}`; `ASSIGN` takes `{assignee:string}` (trimmed 1–128 characters); `COMPLETE` takes `{maintenance_record_id:uuid}`; `COMMENT` takes `{text:string}` (trimmed 1–2000); `CLOSE`, `REOPEN`, `CANCEL` take `{reason:string}` (trimmed 1–500); `OPEN_VERIFICATION` is reserved and not writable. Extra/missing keys, wrong types and blank text give 422 `WORK_INPUT_INVALID`. `COMPLETE` missing key is `WORK_INPUT_INVALID`; foreign/wrong-case record is `WORK_LINK_SCOPE_INVALID`. A record may be posted only to a `MAINTENANCE_REQUEST` case; an Incident receives `WORK_INPUT_INVALID`. No maintenance-record correction route exists in W4, so its `supersedes_record_id` remains null. Later corrections require same `case_id` root.
* **B5:** `work_case_revision` now stores `authorization_basis,occurred_at`; `maintenance_plan` stores `actor_kind,authorization_basis,occurred_at,correction_reason`; `maintenance_record` and `operational_record` store `actor_kind,authorization_basis`. In every table `recorded_at` is DB time; no caller controls it. The plan `correction_reason` is mandatory on a successor by service validation. The root case's asset and `occurred_at` are immutable; a revision corrects title, narrative, cited set or pinned links, with its own actor-supplied `occurred_at` as correction occurrence, not a rewrite of root time.
* **B6, N35:** One create `idempotency_key` populates `work_case.create_key`, typed child `incident_key|request_key`, revision-1 `idempotency_key`, and CREATED event `idempotency_key`. Their hash is the same SHA-256 of canonical request JSON, computed before server IDs, DB times and generated code. Canonical form is UTF-8 JSON with sorted object keys, compact separators `,`/`:`, arrays in submitted order after UUID dedupe/sort for link/citation sets, UTC times normalized to six fractional digits and `Z`, decimals normalized to plain base-10 without trailing zeros, actor **included**, and no `authorization_basis` accepted from the client. For later commands hash the validated full command body including actor, excluding DB/server fields. Reused key with identical hash returns the stored exact result (200); different hash is `WORK_EVENT_DUPLICATE_KEY` for all create/correction/event routes, despite the legacy code name. Test the retry across all root types.
* **B7/B11, S18:** Fixture input is `{schema:"w401-work/1",site_codes:["KOBO-001","COLD-LAB-001","EV-LAB-001"],positive_site:"KOBO-001",case_create_key:"w401-incident-001",request_create_key:"w401-request-001",record_create_key:"w401-record-001",plan_create_key:"w401-plan-001",accepted_evidence_ids:[],finding_links:[]}`. The test harness fills exact accepted/pinned IDs only from public reads in its private DB and records output UUIDs in generated test evidence. UUID generation is injectable for response snapshots; use `10000000-...` only under that injected test factory. No static fixture claims W2 cold accepted start/result IDs, which the merged replay does not promise. `accepted_evidence.received_at <= command DB time` is the acceptance cutoff; `published_at` describes source publication, not ledger acceptance.
* **B8:** `selection_token=sha256:` plus SHA-256 of canonical JSON `{version:"work-selection/1",tenant_id,site_id,kind,from,to,known_at,access_basis,rows:[{case_id,revision_id,selected_event_ids,selected_record_id,finding_revision_ids,action_event_ids,cited_accepted_evidence_ids}],linked_selection_fences:[...]}`. Sort row/UUID arrays lexical; timestamps six-digit UTC; include *all* eligible cases before paging, not page rows. Fence includes case/revision/event/record writers plus linked Finding/Action selection tokens. On page two any auth, selected row, linked status or window change gives 409 `WORK_BASIS_CHANGED`; malformed cursor is 422. `known_at` defaults to snapshot DB time; explicit future cutoff is `INVALID_KNOWN_AT`.
* **S12/S13:** `OPEN_VERIFICATION` refuses 409 `WORK_TRANSITION_INVALID` because no W4 transition target is reachable; a requested VERIFIED/INEFFECTIVE/INCONCLUSIVE outcome is 409 `WORK_OUTCOME_NOT_SUPPORTED`. No plan or OperationalRecord transition endpoint exists in W4, so ACTIVATE/PAUSE/CANCEL and ACCEPT/REJECT are unreachable through its API; tests assert an unregistered route is 404/405, not a fabricated 409. The state-table reserved clauses describe future commands only.
* **S14/S15/S17:** Non-head plan/op-record predecessor returns `WORK_CORRECTION_CONFLICT`, message `This record has a newer correction; reload its latest version.`, UI `A newer correction exists. Reload this record.` Case revision non-head uses the same code; `WORK_BASIS_CHANGED` is cursor-only. `occurred_at` more than five minutes after DB time → `WORK_OCCURRED_AT_FUTURE`; over 30 days before DB time → `WORK_OCCURRED_AT_TOO_OLD`; both 422. A backdated accepted command displays `Recorded later than the event · occurred {local date/time}` beside DB recorded time. Missing/invalid/from≥to/>31-day window → `INVALID_WINDOW` 422; limit outside 1..100 → `INVALID_LIMIT` 422; invalid/future `known_at` → `INVALID_KNOWN_AT` 422. Omitted correction `cited_accepted_evidence_ids` copies predecessor's full set; explicit `[]` clears it, as for links. A correction's new `occurred_at` is separately bounded and visibly backdated if applicable.
* **N34/N36:** `work_case_site_window` filters Site+occurrence with residual `kind='INCIDENT'`; `work_case_site_kind` filters Site+kind+creation for maintenance. No extra index is required. `docker-compose.yml:14` pins PostgreSQL `16.4-alpine`, so the migration's `'Infinity'::numeric` finite-quantity check is supported; retain it and test rejection of Infinity/NaN.

### Read status, UI and proof (B9–B10; S19–S29, S31; N32–N33, N37)

* **B9:** List status precedence is `UNKNOWN` (broken/missing selected link) > `PENDING_RECOMPUTE` (selected `recompute_job`, `financial_consequence_work` or `cold_consequence_work` in PENDING/LEASED/FAILED, as applicable to pinned domain) > `STALE_SOURCE` (selected source read `source_freshness=STALE`) > `HISTORICAL` (explicit earlier cutoff) > `CURRENT`. These are link/claim qualifications, never evidence that an authored case occurred. `coverage.state=UNKNOWN` for broken selection; `PARTIAL` when any eligible linked selection is pending/stale; `COMPLETE` otherwise. `coverage.reason` is one of `LINK_SELECTION_MISSING|LINK_WORK_PENDING|LINK_SOURCE_STALE` or null, with that precedence. Case count remains exact even when coverage is partial.
* **B10/S19/S22/S23:** Lane A changes the actual subrow in `shell/SiteAnalyticsFrames.tsx:1013-1014` and adds `/sites/:siteId/work/incidents` and `/sites/:siteId/work/maintenance` in `operatorSiteRoutes.ts`. Query keys are `from,to,known_at,cursor`; reuse `SiteWorkActions.tsx:113-160` whole-UTC-day date form pattern. First load is last seven complete UTC days ending today 00:00 UTC; client asks `limit=5`, shows `Previous`/`Next` buttons and `Showing {first}–{last} of {total_count}` inside panel, using cached prior cursors and server `next_cursor`. New window resets cursor. List `site_name` comes from scoped `site.name` in the same read, and mock's short name is the first whitespace-delimited word only for status copy. Maintenance membership is request `work_case.created_at` in `[from,to)` with `created_at<=known_at`; incident membership is root `occurred_at` in window and `created_at<=known_at`. `total_count` is number of matching authored cases before page; plans are excluded. Show `Window` as `6 Oct · from 19:11` in EAT from root occurrence.
* **S20/S21/S24/S29:** Maintenance Activity cell shows `request_state` badge plus `activity` (`No activity recorded` when null) and `Unverified` badge; Outcome uses `outcome_note` or `No outcome recorded`. Incident OPEN chip is red as v69 `screens.js:189-191`, not amber; IN_PROGRESS blue, CLOSED neutral, CANCELLED neutral, COMPLETED blue. Display labels are `Open`, `In progress`, `Closed`, `Cancelled`, `Completed`. Finding links are real scoped links labelled `Finding {first 8 UUID chars}`, with pinned `revision_id`; no invented F-code. The global v69 Incident/Preventive/OperationalRecord controls show severity, owner, type, criterion, interval and review stages (`screens.js:514-517` and preventive/OPREC screens), but those belong to W6 and later reviewed contracts. W4 freezes only Site work core; do not present those unsupported mock controls as live.
* **S25/S26/S27:** Update every literal `0025_w2_ev_session` head assertion in `test_s1_bindings_postgres.py`, `test_s2_evidence_ledger_postgres.py`, `test_s405_publication_postgres.py`, `test_s4_consequence_store_postgres.py`, `test_s4_evidence_consequence_work_postgres.py`, `test_w200_source_events_postgres.py`, `test_w201_cold_foundation_postgres.py`, `test_w206_ev_migration_postgres.py`, and all head tests already listed above, after 0026/0027 land. UI tests to update: `operatorSiteTabs.test.tsx`, `operatorRouteFrames.test.tsx`, `w1f4ChangesWorkStructure.test.tsx`, `siteWorkActions.test.tsx`; also `tools/checks/navigation-rail-fixtures.ps1`. Add `test_w401_work_api.py::{test_scope_before_shape_401_403_404,test_mutation_409_422_and_store_503,test_idempotent_200_same_body,test_list_refusal_has_null_rows_and_total}`. Rule-8 `tools/checks/configuration-persistence.ps1` registration lands in commit 2 with `$workWriter = 'backend/assetops_backend/work/adapters/postgres_work_store.py'` and tables `work_case,incident,maintenance_work_request,work_case_revision,work_case_finding_link,work_case_action_link,work_case_evidence,work_event,maintenance_plan,maintenance_record,operational_record`; per-table anti-vacuity counts must run only then.
* **S28:** `work_api` uses the existing `action_api.py:65` `command_access` pattern for writes. Development access has no human principal, so client-asserted `actor.kind=USER` is **rejected** 403 until a server-authenticated user identity exists. Positive fixture uses authenticated SERVICE actor `{kind:"SERVICE",id:"w401-fixture",attestation:"service=w401-fixture;job=positive-case;rule=w401/1"}`; server derives/overwrites `authorization_basis` from command access, never trusts request text. This corrects the earlier human-attested example, which is illustrative only and not an executable development fixture. Read access remains `finding_api.Access` per Site.
* **S31/N32/N33/N37:** Static `Manage in ... · Not available yet` is plain text/`Notice`, never `UnavailableEntry` outside its guarded multiset. Use existing `ProductStatus` and `Disclosure`; PascalCase page files. The 460px 1440 Incident panel cap is a measured **stocked** five-row cap; if content exceeds it, table scrolls within the panel with first column sticky, no clipped rows or page-level horizontal overflow. Verify with `test_w401_stocked_five_rows_1440_and_390`.

The shared provenance decision's compatibility alias and digest rules apply to both W4 list and detail rows. Every W4-01 review question is closed; none remains open.

## Review closure 2 (2026-10-20)

This section supersedes incompatible illustrative responses and status prose above; it is a proposed W4 contract against merged main `e109f4f6`.

**Q11 — case and pinned Action provenance.** A case's `selected_revision_ids` is the sorted unique set of selected `work_case_revision.id`, all selected `work_event.id` through `known_at`, the selected latest same-case `maintenance_record.id` if present, every pinned `work_case_finding_link.finding_revision_id`, and every pinned `work_case_action_link.action_event_id`. It includes linked Finding and Action selected IDs, not merely the case revision. The cited accepted set is the union of the selected `work_case_evidence.evidence_id`, exact pinned `finding_revision_evidence.evidence_id`, and each pinned Action's `action_basis_evidence.evidence_id` plus its origin Finding revision's `finding_revision_evidence.evidence_id`, all scoped to tenant/Site and read in the same transaction. A pinned Action's event comes from `work_case_action_link.action_event_id`, then the Action basis is read with that link's `action_id`; do not use the current Action event or a plan ID. Missing/foreign pinned lineage gives UNKNOWN and `LINK_SELECTION_MISSING`, never a reduced citation set. The shared `evidence/public_provenance.py` patch belongs to **W3-01 commit 1** with Lane A compatibility integration; if W4 merges first, **W4-01 commit 2** carries that same reviewed patch and W3 consumes it. W4 commit 2 is thus the explicit W4-first owner, with no second adapter.

**Q7 — positive linked fixture.** In its private `_test` DB, run `python -m assetops_backend.sites.import_kobo --source var/sites/kobo-001.yaml` after migration (`tools/s2_demo_walkthrough.py:134-136`), then execute the KOBO-001 accepted-evidence/assessment replay used by `tools/s4_finding_walkthrough.py` and require a CURRENT public `GET /api/sites/KOBO-001/finding-index` row. Read that row's `finding_id,finding_revision_id,cited.accepted_evidence_ids` and pin exactly one link; no hard-coded UUID. If a selected Action exists, `GET /api/sites/KOBO-001/action-index` supplies `action_id,selected_event.id` for one pinned Action link; otherwise the fixture creates/accepts it by the existing Action API before W4 POST and records its returned event. `accepted_evidence_ids:[]` and `finding_links:[]` in the static fixture are unresolved inputs only, not the positive posted request. The generated fixture output records exact IDs and a positive `finding_links` array. Add `backend/tests/test_w401_work_service_postgres.py::test_incident_attestation_reload_and_exact_links` asserting pinned revision and evidence, `backend/tests/test_w401_site_indexes_postgres.py::test_pinned_link_survives_later_finding_and_action_heads`, and `frontend/src/sites/__tests__/siteWorkCases.test.tsx::finding_link_uses_pinned_revision` asserting label `Finding {first 8 UUID chars}` and `siteFindingHref(siteId,findingId,revisionId)` (`frontend/src/shell/operatorSiteRoutes.ts:162`). A missing public Finding row fails fixture setup, rather than yielding a fabricated positive case.

**Q9 — computable link coverage.** W4 commit 3 creates `backend/assetops_backend/work/link_coverage.py:linked_coverage(snapshot, tenant_id, site_id, revision_id, from_, to, known_at) -> {state,reason,links:[{kind,id,selected_id,selection_token,state}]}` in the same REPEATABLE READ list/detail transaction. Join `work_case_finding_link` by `(tenant_id,site_id,case_revision_id)` to exact `(finding_id,finding_revision_id)` and `finding_revision` by `(tenant_id,site_id,id)`; join `work_case_action_link` by the same case revision to exact `(action_id,action_event_id)` and `action_event` by `(action_id,id)`, then Action root's `origin_finding_revision_id`. Compare each pinned Finding to the exact selected read for its domain: mini-grid `analytics/finding_index.py:259-322` matcher pass (`finding_match_pass.selection_seq`) and overlapping `recompute_job.status` (`0005_evidence_ledger.py:289-306`); cold `ColdReadService` (`analytics/adapters/postgres_assessment_store.py:1549`) `currentness.state` and `cold_reads.probe_fresh(latest_probe_at,to)` with ten-minute threshold; EV `EvReadService` (same file:2075) `currentness.state`. Extract the existing Cold/Ev `_snapshot(c,...)` query and pure status rules for the caller's open connection; calling their public `_read` wrapper would start another transaction and is forbidden here. The linked read uses the case list's `[from_,to)` window; detail with no window uses the pinned Finding episode window. For a pinned Action, use its origin Finding's exact revision and selected event at cutoff; an unrecognized domain/missing exact selected revision is UNKNOWN. Map `PENDING_RECOMPUTE` from the selected read or overlapping PENDING/LEASED/FAILED job; `STALE_SOURCE` from selected cold read only; `HISTORICAL` from explicit earlier cutoff only when no higher-priority failure; otherwise CURRENT. `financial_consequence_work` and `cold_consequence_work` have no `status` column; use their attempt/selected consequence read when money coverage is relevant. This supplies the B9 precedence without guessing joins.

**Q8 — complete fence.** `selected_event_ids` in each case token row means every `work_event.id` for that case with `recorded_at<=known_at`, sorted lowercase lexical, including CREATED and later COMMENT/ASSIGN/COMPLETE/CLOSE/REOPEN/CANCEL. `linked_selection_fences` is one object per pinned link, sorted `(kind,root_id,selected_id)`: `{kind:"FINDING",root_id:finding_id,selected_id:finding_revision_id,selection_token:<exact selected Finding read token>,state:<exact read state>}` or `{kind:"ACTION",root_id:action_id,selected_id:action_event_id,selection_token:<exact Action read fence token>,state:<linked origin Finding state>}`. Read tokens from the same scoped transaction using the selected W1 Site index fence (`finding_index.py` or `actions/site_index.py`); if an exact token cannot be produced, `state=UNKNOWN`, `selection_token:null`, and coverage refuses a current claim. Recompute these objects for every page request at the same window/cutoff; any difference from cursor payload returns 409 `WORK_BASIS_CHANGED`. A later head does not silently replace a pinned revision/event.

**Q6/Q28 — canonical commands and literal refusals.** Hash the normalized request body plus the canonical path identity: create includes `{site_code}`; correction/event/record includes `{site_code,case_id}`; plan/operational includes `{site_code}` and any canonical root ID supplied for correction. Normalize site code by resolved scoped Site ID before hashing; lower-case UUIDs; path and body are both included in sorted-key compact UTF-8 JSON `{path:{...},body:{...}}`. Idempotent retry compares this hash within the same tenant/Site/route. Development `actor.kind=USER` is `403 {"detail":{"code":"WORK_USER_AUTH_REQUIRED","message":"A signed-in user identity is required for user-attested work commands."}}`. SERVICE attestation must match `^service=([^;]+);job=([^;]+);rule=([^;]+)$`, all three nonblank with no surrounding whitespace; captured service equals authenticated `actor.id` and server service principal ID, and the rule names a version. Mismatch is `422 {"detail":{"code":"WORK_ATTESTATION_INVALID","message":"Service attestation must name the authenticated service, job and rule version."}}`. `authorization_basis` is server-derived.

Literal successful POST bodies (injected test IDs and DB times, not seed data): plan create `{"schema_version":"maintenance-plan-1","id":"10000000-0000-4000-8000-000000000601","canonical_plan_id":"10000000-0000-4000-8000-000000000601","public_code":"PM-000003","state":"DRAFT","recorded_at":"2026-10-06T18:41:00Z"}`; maintenance record `{"schema_version":"maintenance-record-1","id":"10000000-0000-4000-8000-000000000504","case_id":"10000000-0000-4000-8000-000000000501","recorded_at":"2026-10-06T19:30:00Z","outcome":"UNVERIFIED"}`; OperationalRecord create `{"schema_version":"operational-record-1","id":"10000000-0000-4000-8000-000000000701","canonical_record_id":"10000000-0000-4000-8000-000000000701","public_code":"REC-000004","state":"SUBMITTED","recorded_at":"2026-10-06T16:14:00Z"}`. A plan/OperationalRecord correction returns the new `id` and `recorded_at`, original canonical ID and code, and unchanged DRAFT/SUBMITTED state. These replace the shorter examples above. Add API tests `test_user_actor_403_and_service_attestation_422`, `test_path_identity_changes_idempotency_hash`, and `test_plan_record_operational_literal_responses`.

No item in the closure check remains open.
