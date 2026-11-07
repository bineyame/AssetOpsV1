/**
 * CH-9b3 (CH9b3-R Q5/Q6): the typed client for the mill verdict of a MINI domain Action, read once from
 * `GET /api/sites/{site}/domain-work/actions/{id}/verification` (`action_api.py`, read-only; no recording route).
 *
 * The body is the backend's `verification_families.summary_wire`: the stored outcome read back (never recomputed),
 * or the not-judged state with its text. Every refusal is a named state, never a thrown error.
 */
import { SITES_API_PATH } from "./siteDirectoryClient";
import { isObject } from "./evidenceRead";

export const MILL_STATES = ["VERIFIED", "INEFFECTIVE", "INCONCLUSIVE", "NOT_JUDGED", "NO_PLAN"] as const;
export type MillState = (typeof MILL_STATES)[number];

export interface MillMetricRow {
  metric_key: string;
  label: string;
  unit: string;
  before: string | null;
  after: string | null;
  threshold: string | null;
  days_before: number;
  days_after: number;
  state: string;
}

/** MV-1 (FUEL-1 §2.3): the estimated-sales line of a VERIFIED outcome; both strings are the server's. */
export interface MillValue {
  state: "PRICED" | "UNPRICED";
  reason: string | null;
  basis: string;
  per_day: string | null;
  before_per_day: string | null;
  after_per_day: string | null;
  currency: string | null;
  price: { revision_id: string; value: string; currency: string } | null;
  text: string;
  cost_text: string;
}

export interface MillVerification {
  action_id: string;
  action_code: string | null;
  title: string | null;
  state: MillState;
  reasons: string[];
  sentence: string | null;
  line: string | null;
  not_judged_text: string | null;
  outcome: { outcome_id: string; outcome: string; recorded_at: string } | null;
  plan: { effective_day: string; baseline_days: string[]; later_days: string[] } | null;
  metrics: MillMetricRow[];
  value: MillValue | null;
}

export type MillVerificationResult =
  | { status: "loaded"; body: MillVerification }
  | { status: "not_found" }
  | { status: "error"; message: string };

export interface MillVerificationClient {
  read(siteCode: string, actionId: string): Promise<MillVerificationResult>;
}

export const MILL_UNREACHABLE = "The verification read could not be reached.";
export const MILL_UNEXPECTED = "The verification read answered in an unexpected shape.";
export const MILL_REFUSED = "The verification read was refused.";

export function millVerificationPath(basePath: string, siteCode: string, actionId: string): string {
  return `${basePath}/${encodeURIComponent(siteCode)}/domain-work/actions/${encodeURIComponent(actionId)}/verification`;
}

const text = (v: unknown): v is string | null => v === null || typeof v === "string";

function metricRow(v: unknown): v is MillMetricRow {
  return (
    isObject(v) &&
    typeof v.metric_key === "string" &&
    typeof v.label === "string" &&
    typeof v.unit === "string" &&
    text(v.before) &&
    text(v.after) &&
    text(v.threshold) &&
    typeof v.days_before === "number" &&
    typeof v.days_after === "number" &&
    typeof v.state === "string"
  );
}

/** The 200 body, or null when it is not the mill verdict shape. */
export function parseMillVerification(v: unknown): MillVerification | null {
  if (!isObject(v) || typeof v.action_id !== "string" || !(MILL_STATES as readonly unknown[]).includes(v.state)) return null;
  if (!text(v.sentence) || !text(v.line) || !text(v.not_judged_text) || !text(v.title ?? null)) return null;
  if (!Array.isArray(v.reasons) || !v.reasons.every((r) => typeof r === "string")) return null;
  if (!Array.isArray(v.metrics) || !v.metrics.every(metricRow)) return null;
  const value = v.value ?? null;
  if (value !== null && !millValue(value)) return null;
  return { ...v, value } as unknown as MillVerification;
}

/** MV-1: absent or null reads as null; an object needs string `text` and `cost_text`. */
function millValue(v: unknown): v is MillValue {
  return isObject(v) && (v.state === "PRICED" || v.state === "UNPRICED") && typeof v.text === "string" && typeof v.cost_text === "string";
}

export function createMillVerificationClient(basePath: string = SITES_API_PATH): MillVerificationClient {
  return {
    async read(siteCode, actionId) {
      let response: Response;
      try {
        response = await fetch(millVerificationPath(basePath, siteCode, actionId));
      } catch {
        return { status: "error", message: MILL_UNREACHABLE };
      }
      if (response.status === 404) return { status: "not_found" };
      if (!response.ok) return { status: "error", message: MILL_REFUSED };
      let body: unknown;
      try {
        body = await response.json();
      } catch {
        return { status: "error", message: MILL_UNEXPECTED };
      }
      const parsed = parseMillVerification(body);
      return parsed === null ? { status: "error", message: MILL_UNEXPECTED } : { status: "loaded", body: parsed };
    },
  };
}
