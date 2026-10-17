/**
 * Read-only client for a cold-chain Site's selected configuration
 * (`GET /api/sites/{code}/cold/foundation?at=`, W2-01; design
 * `.agent/W2-technical-design-cold.md` section 3 D-I).
 *
 * The read describes configuration only: rooms and their policy band, the
 * configured topology, channel bindings, readiness messages, commissioning
 * (always unconfirmed until a commissioning record exists) and gateway contact.
 * It makes no temperature, equipment-health or evidence claim.
 */

import { SITES_API_PATH } from "./siteDirectoryClient";
import { isObject } from "./evidenceRead";

export interface ColdPolicy {
  low: number;
  high: number;
  unit: string;
  revision_id: string;
}

export interface ColdRoom {
  asset_id: string;
  policy: ColdPolicy | null;
  probe_ids: string[];
  compressor_ids: string[];
}

export interface ColdTopologyNode {
  node_id: string;
  component_id: string;
  asset_id: string | null;
  component_type: string;
  display_name: string | null;
  node_role: string;
}

export interface ColdTopologyEdge {
  connection_id: string;
  from_node: string;
  to_node: string;
  medium: string;
}

export interface ColdBinding {
  role: string;
  asset_id: string;
  source_id: string;
  unit: string;
  cadence_seconds: number | null;
  publication_mode: string;
}

export interface ColdReadinessMessage {
  code: string;
  role: string | null;
  component_id: string | null;
  asset_id: string | null;
  message: string;
  blocking: boolean;
}

export type ColdContactState = "RECENT" | "STALE" | "NEVER";

export interface ColdFoundationReadModel {
  foundation_revision_id: string;
  valid_from: string;
  valid_to: string | null;
  rooms: ColdRoom[];
  topology: { nodes: ColdTopologyNode[]; edges: ColdTopologyEdge[] } | null;
  bindings: ColdBinding[];
  readiness: { state: "READY_TO_REPORT" | "CONFIGURATION_INCOMPLETE" | string; messages: ColdReadinessMessage[] };
  commissioning: { state: string; evidence_ids: string[] };
  contact: { state: ColdContactState | string | null; as_of: string | null; limitations?: string[] };
}

export type ColdFoundationRead =
  | { status: "loaded"; value: ColdFoundationReadModel }
  /** The server answered with a refusal envelope (404, 422, 503, ...). */
  | { status: "refused"; httpStatus: number; code: string; message: string | null }
  /** No answer, or an answer that is not the documented shape. */
  | { status: "unavailable"; message: string | null };

export interface ColdFoundationClient {
  getColdFoundation(siteId: string, at: string | null): Promise<ColdFoundationRead>;
}

function isColdFoundation(value: unknown): value is ColdFoundationReadModel {
  return (
    isObject(value) &&
    typeof value.foundation_revision_id === "string" &&
    typeof value.valid_from === "string" &&
    Array.isArray(value.rooms) &&
    Array.isArray(value.bindings) &&
    isObject(value.readiness) &&
    Array.isArray(value.readiness.messages) &&
    isObject(value.commissioning) &&
    isObject(value.contact) &&
    (value.topology === null || (isObject(value.topology) && Array.isArray(value.topology.nodes) && Array.isArray(value.topology.edges)))
  );
}

export function createColdFoundationClient(basePath: string = SITES_API_PATH): ColdFoundationClient {
  return {
    async getColdFoundation(siteId, at) {
      const search = at === null ? "" : `?at=${encodeURIComponent(at)}`;
      let response: Response;
      try {
        response = await fetch(`${basePath}/${encodeURIComponent(siteId)}/cold/foundation${search}`);
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
        return isColdFoundation(body)
          ? { status: "loaded", value: body }
          : { status: "unavailable", message: "The configuration read answered in an unexpected shape." };
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
