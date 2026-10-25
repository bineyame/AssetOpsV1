/**
 * S6-01b phase 1: the Site-scoped Action and Recommendation reads and the
 * SYSTEM demonstration commands (`backend/assetops_backend/action_api.py`,
 * S6-01a; wire contract `backend/tests/fixtures/s6_action_api_contract.json`).
 *
 * Reads:
 * - `GET /api/sites/{site}/findings/{finding}/recommendation[?revision_id=]`
 * - `GET /api/sites/{site}/actions/{action}[?event_id= | ?recorded_at=]`
 * - `GET /api/sites/{site}/actions/{action}/events[?event_id= | ?recorded_at=]`
 *
 * Commands (each needs the server's scoped `system_demo_capability`; the
 * client never claims an actor or authority, and nothing here enables one):
 * - `POST .../recommendation/accept`
 * - `POST /api/sites/{site}/actions/{action}/apply`
 *
 * Every refusal is a typed result carrying the HTTP status and the server's
 * `detail.code`, never a thrown error and never an empty result.
 */
import type { SourceProvenance } from "./sourceProvenance";
import { SITES_API_PATH } from "./siteDirectoryClient";
import { hasKeys, isObject } from "./evidenceRead";
import type { VerificationSummary } from "./verificationClient";

export interface Refusal {
  status: "refused";
  /** HTTP status, or null when the server could not be reached. */
  http: number | null;
  code: string | null;
  message: string | null;
  detail: Record<string, unknown> | null;
}

export type ActionReadResult<T> = { status: "loaded"; value: T } | Refusal;

export interface SystemDemoCapability {
  actor_id: string;
  actor_kind: string;
  allowed: boolean;
  command: string;
  fixture_id: string | null;
  label: string;
  manifest_id: string | null;
  scope: string;
  unavailable_reason: string | null;
}

export interface Limitation {
  code: string;
  text: string;
}

export interface TypedReason {
  code: string;
  message: string;
}

export interface SocReading {
  at: string;
  evidence_id: string;
  envelope_sha256: string;
  unit?: string;
  value: string;
}

export interface ProposalSegment {
  assessment_revision_id: string;
  start: string;
  end: string;
  reserve: string;
  soc_threshold: string;
  selected_soc: SocReading | null;
  eligible?: boolean;
  reason?: string | null;
}

export interface Proposal {
  acceptance_key: string;
  asset_code: string;
  asset_id: string;
  current_foundation_revision_id: string;
  field: string;
  finding_id: string;
  finding_revision_id: string;
  foundation_revision_id: string;
  input_sha256: string;
  inputs: { primary_assessment_revision_id: string; segments: ProposalSegment[] };
  limitation: Limitation;
  old_value: string;
  primary_assessment_revision_id: string;
  proposed_value: string;
  recommendation_key: string;
  rule: { id: string; version: number };
  unit: string;
}

export interface AcceptedSnapshot extends Omit<Proposal, "current_foundation_revision_id"> {
  current_foundation_revision_id_at_acceptance: string;
}

export interface AcceptedRecommendation {
  accepted_at: string;
  action_code: string;
  action_id: string;
  links: { action: string; api_action: string };
  snapshot: AcceptedSnapshot;
  snapshot_sha256: string;
}

export interface LiveStatus {
  already_accepted: boolean;
  label: string;
  proposal: Proposal | null;
  state: "AVAILABLE" | "UNAVAILABLE";
  unavailable: TypedReason | null;
}

/**
 * An Action on the same canonical Finding, from any revision
 * (`D-2026-10-15-s601-reopen`). It keeps its own origin revision; it is never
 * relabelled as the selected revision's.
 */
export interface PriorAction {
  accepted_at: string;
  action_code: string;
  action_id: string;
  application: {
    application_attempts: number;
    failed_attempts: number;
    last_failure: { event_id: string; failure_code: string; recorded_at: string } | null;
    state: string;
  };
  links: { action: string; api_action: string };
  origin: { finding_id: string; finding_revision_id: string; is_selected_revision: boolean; revision_no: number };
  outcome: { state: string; statement: string };
  rule_id: string;
  unresolved: boolean;
  /** S6-02a: the latest resolution event (RESOLVED or RESOLUTION_WITHDRAWN), when one exists. */
  resolution?: {
    event_id: string;
    guardrail_failed: boolean;
    outcome: string | null;
    outcome_id: string | null;
    plan_id: string | null;
    reasons: string[];
    recorded_at: string;
    state: string;
  } | null;
  /** S6-02a: a guardrail-failed closure blocks the battery trial scope. */
  trial_block?: string | null;
}

/** The typed hold on a new acceptance while an earlier trial is unresolved. */
export interface PriorActionBlock {
  blocking_action_code: string;
  blocking_action_id: string;
  blocking_actions: PriorAction[];
  code: "PRIOR_ACTION_UNRESOLVED" | string;
  links: { action: string; api_action: string };
  message: string;
  origin_finding_revision_id: string;
  origin_revision_no: number;
  /** S6-02a: the guardrail-failed outcome behind `PRIOR_TRIAL_GUARDRAIL_FAILED`. */
  blocking_outcome_id?: string | null;
  /** S6-02a: closure/late-reading overlaps behind `PRIOR_TRIAL_REASSESSMENT_OVERLAP`. */
  overlaps?: Record<string, unknown>[] | null;
}

export interface RecommendationBody {
  accepted: AcceptedRecommendation[];
  /** Every Action on this canonical Finding, any revision (absent on older servers). */
  prior_actions?: { items: PriorAction[]; label: string } | null;
  /** Set when `state` is `PRIOR_ACTION_UNRESOLVED`. */
  prior_action_block?: PriorActionBlock | null;
  basis: "SERVED_FROM_PERSISTED_INPUTS" | "ACCEPTED_SNAPSHOT" | string;
  finding_id: string;
  is_latest: boolean;
  latest_revision_id: string;
  links: { finding: string; recommendation: string; api_recommendation: string };
  live_status: LiveStatus | null;
  /** S4-05b phase 2: the selected FindingRevision's stored source (absent on older servers: Source unverified). */
  source_provenance?: SourceProvenance | null;
  money_consequence: {
    basis: { finding_id: string; finding_revision_id: string };
    label: string;
    links: { api_consequences: string };
    statement: string;
  } | null;
  proposal: Proposal | null;
  revision_id: string;
  rule: { id: string; version: number; limitation: Limitation };
  site_code: string;
  source_open: boolean;
  state: "AVAILABLE" | "UNAVAILABLE" | "ACCEPTED" | "PRIOR_ACTION_UNRESOLVED" | string;
  /** Absent or not `allowed`: the view is read-only (Architect Q4). */
  system_demo_capability?: SystemDemoCapability | null;
  unavailable: TypedReason | null;
  /** The stored input windows the rule read when it proposes nothing (absent otherwise). */
  segments?: ProposalSegment[] | null;
  /** S6-02a: each accepted Action's current verification read state, by Action ID. */
  verification?: Record<string, VerificationSummary> | null;
}

export interface EventActor {
  id: string;
  kind: string;
  label: string;
  source_channel: string;
  authorization_basis: string;
  triggering: { command: string; fixture: string | null; job: string | null; service: string | null };
}

/** post-W6 W1-b Q29 / R218: the evaluator also records RESOLVED and RESOLUTION_WITHDRAWN on the Action. */
export type ActionEventKind = "ACCEPTED" | "APPLIED" | "FAILED" | "OBSERVED" | "RESOLVED" | "RESOLUTION_WITHDRAWN";

export interface ActionEvent {
  action_id: string;
  actor: EventActor;
  actor_id: string;
  actor_kind: string;
  current_foundation_revision_id: string | null;
  expected_foundation_revision_id: string | null;
  failure_code: string | null;
  id: string;
  idempotency_key: string;
  kind: ActionEventKind | string;
  observation_code: string | null;
  occurred_at: string;
  occurred_before_recorded: boolean;
  recorded_at: string;
  source_channel: string;
  triggering_command: string;
  triggering_fixture: string | null;
  triggering_job: string | null;
  triggering_service: string | null;
}

export interface Outcome {
  state: string;
  statement: string;
}

export interface ActionState {
  accepted_at: string;
  application: "PENDING" | "APPLIED" | string;
  application_attempts: number;
  applied_at: string | null;
  failed_attempts: number;
  last_failure: { event_id: string; failure_code: string; recorded_at: string } | null;
  outcome: Outcome;
}

export interface Selection {
  basis: string;
  cutoff_event_id: string | null;
  cutoff_recorded_at: string | null;
  event_count: number;
  event_id: string | null;
  kind: "LATEST" | "EVENT_ID" | "RECORDED_AT" | string;
  order: string;
  recorded_at: string | null;
  total_event_count: number;
}

export interface FoundationRevisionRef {
  derived_from_revision_id: string | null;
  id: string;
  origin: string;
  recorded_at: string;
  superseded_at: string | null;
  valid_from: string;
  valid_to: string | null;
  version: number;
}

export interface PolicyChange {
  action_id: string;
  applied_event_id: string;
  asset_id: string;
  binding_set_revisions: { inserted: string[]; superseded: string[] };
  change_id: string;
  command_idempotency_key?: string;
  effective_from: string;
  expected_foundation_revision_id: string;
  field: string;
  foundation_revisions: FoundationRevisionRef[];
  label: string;
  new_foundation_revision_id: string;
  new_value: string;
  old_value: string;
  outcome: Outcome;
  recorded_at: string;
  split_foundation_revision_id: string | null;
  statement: string;
  superseded_foundation_revision_id: string | null;
  unit: string;
  validity: string;
}

export interface PolicyChangeBody {
  access_basis?: string;
  change: PolicyChange;
  site_code: string;
  /** S6-02a: the Action's current verification read state (absent on older servers). */
  verification?: VerificationSummary | null;
}

export interface ActionBody {
  /** S4-05b phase 2: the pinned origin FindingRevision's stored source (absent on older servers: Source unverified). */
  source_provenance?: SourceProvenance | null;
  accepted_recommendation: {
    field: string;
    limitation: Limitation;
    old_value: string;
    proposed_value: string;
    rule_id: string;
    rule_version: number;
    snapshot: AcceptedSnapshot;
    snapshot_sha256: string;
    unit: string;
  };
  action: {
    acceptance_key: string;
    action_code: string;
    created_at: string;
    id: string;
    label: string;
    recommendation_key: string;
  };
  application_basis: {
    covers_instant: string;
    current_foundation_revision_id: string | null;
    current_reserve: { unit: string; value: number } | null;
    label: string;
    matches_accepted_basis: boolean;
    read_at: string;
  } | null;
  basis: {
    assessments: { assessment_revision_id: string; segment_start: string; segment_end: string }[];
    asset_id: string;
    evidence: { assessment_revision_id: string; evidence_id: string; role: string; segment_start: string; value_text: string }[];
    foundation_revision_id: string;
    input_sha256: string;
  };
  change: PolicyChange | null;
  last_event: ActionEvent | null;
  latest_finding_revision: {
    id: string;
    is_origin: boolean;
    lifecycle: string;
    revision_no: number;
    transition: string;
  } | null;
  links: Record<string, string>;
  newer_revision_notice: {
    latest_revision_id: string;
    lifecycle: string;
    revision_no: number;
    statement: string;
    transition: string;
  } | null;
  origin: { finding_id: string; finding_revision_id: string; primary_assessment_revision_id: string };
  selection: Selection;
  site_code: string;
  state: ActionState;
  /** Absent or not `allowed`: the view is read-only (Architect Q4). */
  system_demo_capability?: { apply?: SystemDemoCapability | null; observe?: SystemDemoCapability | null } | null;
  /** S6-02a: the current verification read state, beside (never instead of) `state.outcome` (F5). */
  verification?: VerificationSummary | null;
}

export interface ActionEventsBody {
  action_code: string;
  action_id: string;
  events: ActionEvent[];
  links: Record<string, string>;
  selection: Selection;
  site_code: string;
  state: ActionState;
}

/** An exact event or a server `recorded_at` cutoff; both together is the server's typed 422. */
export interface EventSelector {
  eventId: string | null;
  recordedAt: string | null;
}

export interface AcceptCommand {
  revision_id: string;
  foundation_revision_id: string;
  recommendation_key: string;
  proposed_value: string;
  idempotency_key: string;
}

export interface ApplyCommand {
  value: string;
  expected_foundation_revision_id: string;
  effective_from: string;
  idempotency_key: string;
}

export type CommandResult =
  | {
      status: "done";
      http: number;
      replayed: boolean;
      event: ActionEvent | null;
      action: AcceptedRecommendation | null;
      change: PolicyChange | null;
    }
  | Refusal;

export interface ActionClient {
  getRecommendation(siteId: string, findingId: string, revisionId: string | null): Promise<ActionReadResult<RecommendationBody>>;
  getAction(siteId: string, actionId: string, selector: EventSelector): Promise<ActionReadResult<ActionBody>>;
  getActionEvents(siteId: string, actionId: string, selector: EventSelector): Promise<ActionReadResult<ActionEventsBody>>;
  accept(siteId: string, findingId: string, command: AcceptCommand): Promise<CommandResult>;
  apply(siteId: string, actionId: string, command: ApplyCommand): Promise<CommandResult>;
  getChange(siteId: string, changeId: string): Promise<ActionReadResult<PolicyChangeBody>>;
}

function isRecommendation(value: unknown): value is RecommendationBody {
  return (
    hasKeys(value, ["accepted", "state", "rule", "revision_id", "finding_id", "links"]) &&
    Array.isArray((value as { accepted: unknown }).accepted)
  );
}

function isAction(value: unknown): value is ActionBody {
  return hasKeys(value, ["action", "accepted_recommendation", "origin", "state", "selection", "links"]);
}

function isChange(value: unknown): value is PolicyChangeBody {
  return (
    hasKeys(value, ["change", "site_code"]) &&
    hasKeys((value as { change: unknown }).change, ["change_id", "action_id", "applied_event_id", "old_value", "new_value"])
  );
}

function isEvents(value: unknown): value is ActionEventsBody {
  return (
    hasKeys(value, ["action_id", "events", "selection", "state"]) &&
    Array.isArray((value as { events: unknown }).events)
  );
}

function refusal(http: number | null, body: unknown): Refusal {
  const detail = isObject(body) ? body.detail : null;
  if (typeof detail === "string") {
    return { status: "refused", http, code: null, message: detail, detail: null };
  }
  if (isObject(detail)) {
    return {
      status: "refused",
      http,
      code: typeof detail.code === "string" ? detail.code : null,
      message: typeof detail.message === "string" ? detail.message : null,
      detail,
    };
  }
  return { status: "refused", http, code: null, message: null, detail: null };
}

async function exchange(path: string, init?: RequestInit): Promise<{ http: number | null; ok: boolean; body: unknown }> {
  let response: Response;
  try {
    response = init === undefined ? await fetch(path) : await fetch(path, init);
  } catch {
    return { http: null, ok: false, body: null };
  }
  let body: unknown = null;
  try {
    body = await response.json();
  } catch {
    body = null;
  }
  return { http: response.status, ok: response.ok, body };
}

/** One typed read (S6-02b reuses it for the verification reads). */
export async function read<T>(path: string, valid: (value: unknown) => value is T): Promise<ActionReadResult<T>> {
  const { http, ok, body } = await exchange(path);
  if (ok && valid(body)) {
    return { status: "loaded", value: body };
  }
  return refusal(ok ? 502 : http, body);
}

async function command(path: string, payload: object): Promise<CommandResult> {
  const { http, ok, body } = await exchange(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (ok && http !== null && isObject(body)) {
    return {
      status: "done",
      http,
      replayed: body.replayed === true,
      event: isObject(body.event) ? (body.event as unknown as ActionEvent) : null,
      action: isObject(body.action) ? (body.action as unknown as AcceptedRecommendation) : null,
      change: isObject(body.change) ? (body.change as unknown as PolicyChange) : null,
    };
  }
  return refusal(http, body);
}

export function selectorQuery(selector: EventSelector): string {
  const query = new URLSearchParams();
  if (selector.eventId !== null) query.set("event_id", selector.eventId);
  if (selector.recordedAt !== null) query.set("recorded_at", selector.recordedAt);
  const text = query.toString();
  return text ? `?${text}` : "";
}

export function createActionClient(basePath: string = SITES_API_PATH): ActionClient {
  const site = (siteId: string) => `${basePath}/${encodeURIComponent(siteId)}`;
  const action = (siteId: string, actionId: string) => `${site(siteId)}/actions/${encodeURIComponent(actionId)}`;
  return {
    getRecommendation(siteId, findingId, revisionId) {
      const query = revisionId === null ? "" : `?revision_id=${encodeURIComponent(revisionId)}`;
      return read(`${site(siteId)}/findings/${encodeURIComponent(findingId)}/recommendation${query}`, isRecommendation);
    },
    getAction(siteId, actionId, selector) {
      return read(`${action(siteId, actionId)}${selectorQuery(selector)}`, isAction);
    },
    getActionEvents(siteId, actionId, selector) {
      return read(`${action(siteId, actionId)}/events${selectorQuery(selector)}`, isEvents);
    },
    accept(siteId, findingId, payload) {
      return command(`${site(siteId)}/findings/${encodeURIComponent(findingId)}/recommendation/accept`, payload);
    },
    apply(siteId, actionId, payload) {
      return command(`${action(siteId, actionId)}/apply`, payload);
    },
    getChange(siteId, changeId) {
      return read(`${site(siteId)}/foundation/changes/${encodeURIComponent(changeId)}`, isChange);
    },
  };
}

/** A fresh idempotency key for one deliberate command attempt. */
export function freshIdempotencyKey(): string {
  const random = globalThis.crypto?.randomUUID?.();
  return `ui-${random ?? `${Date.now().toString(36)}-${Math.random().toString(36).slice(2)}`}`;
}
