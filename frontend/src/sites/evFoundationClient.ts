import { SITES_API_PATH } from "./siteDirectoryClient";
import { isObject } from "./evidenceRead";
import type { ColdTopologyEdge, ColdTopologyNode } from "./coldFoundationClient";

/*
 * W2-05a: the selected EV Foundation read, `GET /api/sites/{site_code}/ev/foundation?at=<UTC>`
 * (`.agent/W2-05a-build-spec.md` "Role set, binding and selected read" and QH-QL). Decimal quantities are
 * strings; unknowns are null, never zero. Configuration only: a schedule is not observed availability and
 * gateway contact is not charger health.
 */

export interface EvWeeklyInterval {
  weekday: string;
  local_start: string;
  local_end: string;
  utc_offset_minutes: number;
}

export interface EvConnector {
  asset_id: string | null;
  max_kw: string | null;
  enabled_schedule: { enabled: boolean; time_zone: string | null; weekly: EvWeeklyInterval[] };
  meter_resolution_kwh: string | null;
  meter_error_bound_kwh: string | null;
  clock_error_bound_seconds: string | null;
}

export interface EvCharger {
  asset_id: string | null;
  max_kw: string | null;
  connectors: EvConnector[];
}

export interface EvBinding {
  role: string;
  asset_id: string | null;
  source_id: string;
  device_id: string;
  signal_id: string;
  unit: string;
  cadence_seconds: number | string | null;
  effective_from: string | null;
  effective_to: string | null;
}

export interface EvReadinessMessage {
  code: string;
  role: string | null;
  component_id: string | null;
  asset_id: string | null;
  message: string;
  blocking: boolean;
}

export interface EvContact {
  state: "RECENT" | "STALE" | "NEVER" | string;
  as_of: string | null;
  checked_at: string | null;
  gateway_id: string | null;
  reason: string | null;
}

export interface EvFoundationReadModel {
  site_id: string;
  site_code: string;
  site_type: string;
  selected_at: string | null;
  foundation_revision_id: string;
  binding_revision_id: string | null;
  feed: { asset_id: string | null; limit_kw: string | null; meter_asset_id: string | null };
  chargers: EvCharger[];
  topology: { nodes: ColdTopologyNode[]; edges: ColdTopologyEdge[] } | null;
  bindings: EvBinding[];
  readiness: { state: "READY_TO_REPORT" | "CONFIGURATION_INCOMPLETE" | string; messages: EvReadinessMessage[] };
  contact: EvContact;
  commissioning: { state: string; evidence_ids: string[] };
}

export type EvFoundationRead =
  | { status: "loaded"; value: EvFoundationReadModel }
  /** The server answered with a refusal envelope (403, 404, 422, 503, ...). */
  | { status: "refused"; httpStatus: number; code: string; message: string | null }
  /** No answer, or an answer that is not the documented shape. */
  | { status: "unavailable"; message: string | null };

export interface EvFoundationClient {
  getEvFoundation(siteId: string, at: string | null): Promise<EvFoundationRead>;
}

function isEvFoundation(value: unknown): value is EvFoundationReadModel {
  return (
    isObject(value) &&
    typeof value.foundation_revision_id === "string" &&
    isObject(value.feed) &&
    Array.isArray(value.chargers) &&
    Array.isArray(value.bindings) &&
    isObject(value.readiness) &&
    Array.isArray(value.readiness.messages) &&
    isObject(value.commissioning) &&
    isObject(value.contact) &&
    (value.topology === null || (isObject(value.topology) && Array.isArray(value.topology.nodes) && Array.isArray(value.topology.edges)))
  );
}

export function createEvFoundationClient(basePath: string = SITES_API_PATH): EvFoundationClient {
  return {
    async getEvFoundation(siteId, at) {
      const search = at === null ? "" : `?at=${encodeURIComponent(at)}`;
      let response: Response;
      try {
        response = await fetch(`${basePath}/${encodeURIComponent(siteId)}/ev/foundation${search}`);
      } catch {
        return { status: "unavailable", message: null };
      }
      let body: unknown = null;
      try {
        body = await response.json();
      } catch {
        body = null;
      }
      if (response.ok) {
        return isEvFoundation(body)
          ? { status: "loaded", value: body }
          : { status: "unavailable", message: "The EV configuration read answered in an unexpected shape." };
      }
      const error = isObject(body) && isObject(body.error) ? body.error : null;
      if (error !== null && typeof error.code === "string") {
        return {
          status: "refused",
          httpStatus: response.status,
          code: error.code,
          message: typeof error.message === "string" ? error.message : null,
        };
      }
      return { status: "unavailable", message: null };
    },
  };
}
