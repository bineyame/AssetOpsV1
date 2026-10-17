/**
 * S6-02b: the Action verification reads (S6-02a, `backend/assetops_backend/action_api.py`;
 * wire contract `backend/tests/fixtures/s6_verification_api_contract.json`).
 *
 * - `GET .../actions/{action}/verification/plan[?plan_id= | ?recorded_at=]`
 * - `GET .../actions/{action}/verification/evidence[?plan_id= | ?recorded_at=]`
 * - `GET .../actions/{action}/verification/outcome[?outcome_id= | ?recorded_at=]`
 * - `GET .../actions/{action}/verification/history`
 *
 * Both selectors together are the server's typed `VERIFICATION_SELECTOR_CONFLICT`
 * (422). The current read state is `current_state` / `verification_state` (F5),
 * never the Action's `state.outcome`.
 */
import { SITES_API_PATH } from "./siteDirectoryClient";
import { hasKeys } from "./evidenceRead";
import { read, type ActionReadResult } from "./actionClient";

/** PENDING, REASSESSMENT_PENDING and NO_PLAN are read states; only the other three are outcomes. */
export type VerificationReadState =
  | "NO_PLAN"
  | "PENDING"
  | "REASSESSMENT_PENDING"
  | "VERIFIED"
  | "INEFFECTIVE"
  | "INCONCLUSIVE"
  | string;

export interface VerificationState {
  state: VerificationReadState;
  reasons: string[];
  plan_id: string | null;
  outcome_id: string | null;
  last_outcome?: string | null;
  statement: string;
  historical?: boolean;
}

export interface VerificationSummary extends VerificationState {
  label?: string;
  links?: Record<string, string>;
}

export interface Bands {
  feeder_demand_energy_relative: string;
  pv_available_energy_relative: string;
  initial_soc_points: string;
  inclusive: boolean;
  slot_seconds: number;
  slots_per_window: number;
  plan_version: string;
  guardrail_basis: string;
  power_semantics: string;
  zero_baseline_rule: string;
  target_ratio: { baseline: number; later: number; rule: string };
}

export interface DaySelection {
  day: string;
  run_id: string;
  model_version: string;
  cohort_status: string;
  cohort_sha256: string;
  configuration_sha256: string;
  input_sha256: string;
  interval_revision_ids: string[];
  window_revision_ids: string[];
  selection_seq: number;
}

export interface TargetSide {
  assessment_revision_ids: string[];
  candidate_seconds: number | null;
  reasons: string[];
  state: string;
  window_start: string;
  window_end: string;
}

export interface WindowSelection {
  currentness: { day: string; s3_status: string }[];
  days: DaySelection[];
  target: TargetSide;
}

export interface SelectionBinding {
  id: string;
  plan_id: string;
  recorded_at: string;
  window_name: string;
  idempotency_key: string;
  selection: WindowSelection;
  selection_sha256: string;
  actor_id: string;
  actor_kind: string;
}

export interface Bindings {
  binding_set_revision_ids: string[];
  load_asset_ids: string[];
  role_assets: Record<string, string[]>;
  critical_load_asset_ids: Record<string, string[]>;
  roles: string[];
  role_sets: string[];
}

export interface VerificationPlan {
  plan_id: string;
  plan_version: string;
  plan_sha256: string;
  action_id: string;
  change_id: string;
  applied_event_id: string;
  rule_id: string;
  field: string;
  battery_asset_id: string;
  effective_from: string;
  recorded_at: string;
  supersedes_plan_id: string | null;
  old_foundation_revision_id: string;
  new_foundation_revision_id: string;
  origin_finding_revision_id: string;
  baseline_start: string;
  baseline_end: string;
  later_start: string;
  later_end: string;
  baseline_candidate_seconds: number | null;
  baseline_evidence_ids: string[];
  baseline_selection: WindowSelection;
  later_selection_rule: { required_days: string[]; rule: string };
  bands: Bands;
  target: { classification: string; metric: string; ratio: [number, number]; rule: string; inconclusive_when: string[] };
  guardrails: Record<string, { rule: string; unit: string; label?: string; basis?: string; from?: string; after?: string }>;
  coverage: {
    missing: string;
    point_roles: string[];
    power_roles: string[];
    power_rule: string;
    reserve_rule: string;
    soc_rule: string;
    slot_minutes: number;
    slots_per_window: number;
  };
  basis: {
    baseline_bindings: Bindings;
    later_bindings_at_freeze: Bindings;
    load_asset_ids: string[];
    critical_load_asset_id: string | null;
    clock_basis: string;
    cohort_rule: string;
    model_version: string;
    analytic_id: string;
    source_rule?: string;
    later_cutoff?: string;
    baseline_cohort: { day: string; sha256: string; status: string }[];
  };
  idempotency_key: string;
  actor: { id: string; kind: string; label: string };
}

export interface PlanBody {
  label: string;
  action_id: string;
  selector: { plan_id: string | null; recorded_at: string | null };
  verification_state: VerificationState;
  history: { plan_id: string; recorded_at: string; supersedes_plan_id: string | null; superseded_by_plan_id: string | null }[];
  plan: VerificationPlan | null;
  is_current_plan?: boolean;
  superseded_by_plan_id?: string | null;
  selection_bindings: SelectionBinding[];
}

export interface Problem {
  code?: string;
  detail?: string;
  role?: string;
  asset_id?: string;
  [key: string]: unknown;
}

export interface PowerCell {
  state: string;
  kwh: string | null;
  evidence_ids: string[];
  problems: (Problem | string)[];
  slot_start: string;
  slot_end: string;
}

export interface PointCell {
  state: string;
  value: string | null;
  at: string;
  evidence_ids: string[];
  problems: (Problem | string)[];
}

export interface Slot {
  slot_start: string;
  slot_end: string;
  complete: boolean;
  below_reserve_seconds: number | null;
  feeder_demand: Record<string, PowerCell>;
  feeder_demand_kwh: string | null;
  unserved_critical_kwh: string | null;
  generator_power?: PowerCell;
  pcs_discharge_capability?: PowerCell;
  pv_available_power?: PowerCell;
  critical_load_requested_power?: PowerCell;
  critical_load_delivered_power?: PowerCell;
  generator_state?: PointCell;
  soc_start?: PointCell;
  reserve?: { state: string; value: string | null; foundation_revision_id: string | null; problems: (Problem | string)[] };
}

export interface EvidenceWindow {
  window_start: string;
  window_end: string;
  complete: boolean;
  slots: Slot[];
  evidence_ids: string[];
  problems: (Problem | string)[];
  feeder_demand_kwh: string | null;
  pv_available_kwh: string | null;
  unserved_critical_kwh: string | null;
  initial_soc: string | null;
  terminal_soc: string | null;
  terminal_soc_sample: PointCell | null;
  below_reserve_seconds: number | null;
  load_asset_ids: string[];
  critical_load_asset_id: string | null;
  guardrail_basis: string;
  guardrail_label: string;
  plan_version: string;
  power_semantics: string;
  slot_seconds: number;
}

export interface SourceSide {
  state: string;
  /**
   * The source resolution's reasons. The backend sends each as an object `{ code, accepted_evidence_ids, ... }`
   * (`source_provenance.py` `_reason`); a plain code string is still accepted.
   */
  reasons: (string | { code: string; accepted_evidence_ids?: string[] })[];
  publication_ids: string[];
  source_classes: string[];
  fixtures: { fixture_id: string; fixture_version: number }[];
  runs: Record<string, unknown>[];
  problematic_accepted_evidence_ids: string[] | null;
}

export interface ComparabilityCheck {
  metric: string;
  baseline: string | null;
  later: string | null;
  difference: string | null;
  threshold: string | null;
  unit: string;
  state: string;
  reason: string;
  relative_band?: string;
  inclusive: boolean;
}

export interface EvidenceBody {
  label: string;
  action_id: string;
  plan_id: string;
  plan_version: string;
  knowledge_cutoff: string;
  bands: Bands;
  coverage: VerificationPlan["coverage"];
  comparability: { state: string; checks: ComparabilityCheck[] };
  source_resolution: { baseline: SourceSide; later: SourceSide; pair: { state: string; source_class: string | null; problems: string[]; statement: string }; rule: string };
  target: { baseline: TargetSide; later: TargetSide | { state: string; statement: string }; later_selection_binding_id: string | null; met: boolean | null; rule: string };
  verification_state: VerificationState;
  windows: { baseline: EvidenceWindow; later: EvidenceWindow };
}

export interface Metric {
  metric_key: string;
  window_name: "BASELINE" | "LATER" | "COMPARISON" | string;
  state: "PASS" | "FAIL" | "UNKNOWN" | string;
  value_text: string | null;
  threshold_text: string | null;
  unit: string | null;
  reason: string | null;
  evidence_ids: string[];
}

export interface OutcomeRecord {
  outcome_id: string;
  outcome: "VERIFIED" | "INEFFECTIVE" | "INCONCLUSIVE" | string;
  reasons: string[];
  plan_id: string;
  action_id: string;
  recorded_at: string;
  supersedes_outcome_id: string | null;
  selection_binding_id: string;
  evaluation_request_id: string;
  idempotency_key: string;
  basis_sha256: string;
  actor_id: string;
  actor_kind: string;
  triggering_job: string | null;
  basis?: { evidence_ids?: { baseline?: string[]; later?: string[] }; [key: string]: unknown };
  details?: {
    blockers?: string[];
    target?: { baseline_seconds: number | null; later: TargetSide; met: boolean | null; rule: string };
    windows?: Record<string, Record<string, unknown>>;
    source?: { state: string; source_class: string | null; problems: string[]; statement: string };
    [key: string]: unknown;
  };
}

export interface OutcomeBody {
  label: string;
  action_id: string;
  selector: { outcome_id: string | null; recorded_at: string | null };
  current_state: VerificationState;
  outcome: OutcomeRecord | null;
  metrics: Metric[];
  is_latest_outcome: boolean | null;
  superseded_by_outcome_id?: string | null;
  historical_label?: string;
}

export interface ResolutionEvent {
  id: string;
  kind: "RESOLVED" | "RESOLUTION_WITHDRAWN" | string;
  recorded_at: string;
  verification_plan_id: string | null;
  verification_outcome_id: string | null;
  triggering_job: string | null;
  payload: { outcome?: string | null; reasons?: string[]; attribution?: string; statement?: string; [key: string]: unknown };
}

export interface HistoryBody {
  label: string;
  action_id: string;
  current_state: VerificationState;
  plans: { plan_id: string; supersedes_plan_id: string | null; recorded_at: string }[];
  outcomes: OutcomeRecord[];
  evaluation_requests: { id: string; plan_id: string; idempotency_key: string; recorded_at: string }[];
  resolution_events: ResolutionEvent[];
  statement: string;
}

/** One selected plan (`plan_id`) or outcome (`outcome_id`) or a server `recorded_at` cutoff. */
export interface VerificationSelector {
  id: string | null;
  recordedAt: string | null;
}

export interface VerificationClient {
  getPlan(siteId: string, actionId: string, selector: VerificationSelector): Promise<ActionReadResult<PlanBody>>;
  getEvidence(siteId: string, actionId: string, selector: VerificationSelector): Promise<ActionReadResult<EvidenceBody>>;
  getOutcome(siteId: string, actionId: string, selector: VerificationSelector): Promise<ActionReadResult<OutcomeBody>>;
  getHistory(siteId: string, actionId: string): Promise<ActionReadResult<HistoryBody>>;
}

const isPlan = (v: unknown): v is PlanBody => hasKeys(v, ["verification_state", "history", "plan", "selector"]);
const isEvidence = (v: unknown): v is EvidenceBody => hasKeys(v, ["windows", "plan_id", "target", "verification_state"]);
const isOutcome = (v: unknown): v is OutcomeBody => hasKeys(v, ["current_state", "outcome", "metrics", "selector"]);
const isHistory = (v: unknown): v is HistoryBody => hasKeys(v, ["current_state", "plans", "outcomes", "resolution_events"]);

function query(name: string, selector: VerificationSelector): string {
  const q = new URLSearchParams();
  if (selector.id !== null) q.set(name, selector.id);
  if (selector.recordedAt !== null) q.set("recorded_at", selector.recordedAt);
  const text = q.toString();
  return text ? `?${text}` : "";
}

export function createVerificationClient(basePath: string = SITES_API_PATH): VerificationClient {
  const base = (siteId: string, actionId: string) =>
    `${basePath}/${encodeURIComponent(siteId)}/actions/${encodeURIComponent(actionId)}/verification`;
  return {
    getPlan: (siteId, actionId, selector) => read(`${base(siteId, actionId)}/plan${query("plan_id", selector)}`, isPlan),
    getEvidence: (siteId, actionId, selector) =>
      read(`${base(siteId, actionId)}/evidence${query("plan_id", selector)}`, isEvidence),
    getOutcome: (siteId, actionId, selector) =>
      read(`${base(siteId, actionId)}/outcome${query("outcome_id", selector)}`, isOutcome),
    getHistory: (siteId, actionId) => read(`${base(siteId, actionId)}/history`, isHistory),
  };
}
