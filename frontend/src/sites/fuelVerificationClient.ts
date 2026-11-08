/**
 * DIESEL-K6b (DIESEL-1-R3m): the typed client for the fuel verdict of a FUEL_BALANCE domain Action, read once from
 * `GET /api/sites/{site}/domain-work/actions/{id}/fuel-verification` (`action_api.py`, read-only).
 *
 * The body is the backend's `fuel_verification.fuel_summary_wire`: the stored outcome read back (never recomputed),
 * or the not-judged state with its text. Every string is the server's; the browser formats no number. `value` and
 * `cost_check` are always null (H2). Every refusal is a named state, never a thrown error.
 */
import type { Ref } from "./chainRef";
import { SITES_API_PATH } from "./siteDirectoryClient";
import { isObject } from "./evidenceRead";

export const FUEL_STATES = ["VERIFIED", "INEFFECTIVE", "INCONCLUSIVE", "NOT_JUDGED", "NO_PLAN"] as const;
export type FuelState = (typeof FUEL_STATES)[number];

export interface FuelCard {
  label: string;
  value: string;
  note: string;
}

export interface FuelNight {
  role: "BASELINE" | "LATER";
  label: string;
  range_text: string;
  sensor_text: string;
  result_text: string;
  passes: boolean | null;
  window_id: string;
  revision: number;
}

export interface FuelVerification {
  action_id: string;
  action_code: string | null;
  title: string | null;
  owner_label: string | null;
  rule_id: string;
  state: FuelState;
  headline: string;
  sentence: string | null;
  not_judged_text: string | null;
  fixed_line: string;
  criterion_text: string;
  rule_text: string;
  cards: FuelCard[];
  origin: { finding_id: string; revision_id: string; title: string; night_text: string | null; ref: Ref; href: string | null };
  nights: FuelNight[];
  activity: {
    case_code: string | null;
    case_ref: Ref;
    case_href: string | null;
    completed_text: string;
    site_visit_text: string | null;
    note: string;
  } | null;
  effective_from: string | null;
  plan: { plan_id: string; later_candidates: { from: string; to: string } } | null;
  outcome: { outcome_id: string; outcome: string; reasons: string[]; recorded_at: string; source_class: string | null } | null;
  value: null;
  cost_check: null;
}

export type FuelVerificationResult =
  | { status: "loaded"; body: FuelVerification }
  | { status: "not_found" }
  | { status: "error"; message: string };

export interface FuelVerificationClient {
  read(siteCode: string, actionId: string): Promise<FuelVerificationResult>;
}

export const FUEL_UNREACHABLE = "The fuel check could not be reached.";
export const FUEL_UNEXPECTED = "The fuel check answered in an unexpected shape.";
export const FUEL_REFUSED = "The fuel check was refused.";

export function fuelVerificationPath(basePath: string, siteCode: string, actionId: string): string {
  return `${basePath}/${encodeURIComponent(siteCode)}/domain-work/actions/${encodeURIComponent(actionId)}/fuel-verification`;
}

const text = (v: unknown): v is string | null => v === null || typeof v === "string";
const str = (v: unknown): v is string => typeof v === "string";

function card(v: unknown): v is FuelCard {
  return isObject(v) && str(v.label) && str(v.value) && str(v.note);
}

function night(v: unknown): v is FuelNight {
  return (
    isObject(v) &&
    (v.role === "BASELINE" || v.role === "LATER") &&
    str(v.label) &&
    str(v.range_text) &&
    str(v.sensor_text) &&
    str(v.result_text) &&
    (v.passes === null || typeof v.passes === "boolean")
  );
}

/** The 200 body, or null when it is not the fuel verdict shape (a value or cost check is never accepted: H2). */
export function parseFuelVerification(v: unknown): FuelVerification | null {
  if (!isObject(v) || !str(v.action_id) || !(FUEL_STATES as readonly unknown[]).includes(v.state)) return null;
  if (!str(v.headline) || !str(v.fixed_line) || !str(v.criterion_text) || !str(v.rule_text)) return null;
  if (!text(v.sentence) || !text(v.not_judged_text)) return null;
  if (!Array.isArray(v.cards) || v.cards.length !== 4 || !v.cards.every(card)) return null;
  if (!Array.isArray(v.nights) || !v.nights.every(night)) return null;
  if (!isObject(v.origin) || !str(v.origin.title) || !isObject(v.origin.ref)) return null;
  if ((v.value ?? null) !== null || (v.cost_check ?? null) !== null) return null;
  return { ...v, value: null, cost_check: null } as unknown as FuelVerification;
}

export function createFuelVerificationClient(basePath: string = SITES_API_PATH): FuelVerificationClient {
  return {
    async read(siteCode, actionId) {
      let response: Response;
      try {
        response = await fetch(fuelVerificationPath(basePath, siteCode, actionId));
      } catch {
        return { status: "error", message: FUEL_UNREACHABLE };
      }
      if (response.status === 404) return { status: "not_found" };
      if (!response.ok) {
        // The server's own message (a 409 for a non-fuel Action, a 503 when the fuel checks cannot be read).
        try {
          const body = (await response.json()) as unknown;
          const detail = isObject(body) && isObject(body.detail) ? body.detail : body;
          if (isObject(detail) && str(detail.message)) return { status: "error", message: detail.message };
        } catch {
          /* fall through to the fixed refusal */
        }
        return { status: "error", message: FUEL_REFUSED };
      }
      let body: unknown;
      try {
        body = await response.json();
      } catch {
        return { status: "error", message: FUEL_UNEXPECTED };
      }
      const parsed = parseFuelVerification(body);
      return parsed === null ? { status: "error", message: FUEL_UNEXPECTED } : { status: "loaded", body: parsed };
    },
  };
}
