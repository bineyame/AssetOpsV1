/**
 * Read-only client for a Site's central gateway contact
 * (`GET /api/sites/{id}/gateway-health`, S2-02 AC6).
 *
 * The status is `CURRENT|STALE|UNKNOWN` from the server's own receive time
 * against the registered declared cadence. A gateway report is an operational
 * record about the gateway itself: never accepted evidence, never equipment
 * health and never proof that a device was physically contacted.
 */

import { SITES_API_PATH } from "./siteDirectoryClient";
import { arrayOf, hasKeys, isObject, read, type EvidenceRead } from "./evidenceRead";

export type GatewayContactStatus = "CURRENT" | "STALE" | "UNKNOWN";

export interface GatewaySourceContact {
  source_id: string;
  source_external_id: string;
  registration: "ENABLED" | "DISABLED" | string;
  last_contact: string | null;
  contact_provenance: string;
}

export interface GatewayHealthEntry {
  gateway_id: string;
  gateway_external_id: string;
  mode: string;
  registration: "ENABLED" | "DISABLED" | string;
  declared_cadence_seconds: number | null;
  status: GatewayContactStatus | string;
  status_basis: string;
  last_server_contact: string | null;
  diagnostic_id: string | null;
  gateway_observed_at: string | null;
  observed_at_clock: string;
  queue_count: number | null;
  oldest_queue_age_seconds: number | null;
  disk_pressure: string | null;
  disk_pressure_provenance: string | null;
  clock_offset_ms: number | null;
  mapping_error_count: number | null;
  source_contacts: GatewaySourceContact[];
}

export interface GatewayHealth {
  site_id: string;
  read_at: string;
  read_at_clock: string;
  claim_scope: string;
  gateways: GatewayHealthEntry[];
}

export interface GatewayHealthClient {
  getGatewayHealth(siteId: string): Promise<EvidenceRead<GatewayHealth>>;
}

function isGatewayHealth(value: unknown): value is GatewayHealth {
  return (
    isObject(value) &&
    hasKeys(value, ["site_id", "read_at", "gateways"]) &&
    arrayOf(value.gateways, ["gateway_id", "status", "last_server_contact", "declared_cadence_seconds", "source_contacts"])
  );
}

export function createGatewayHealthClient(basePath: string = SITES_API_PATH): GatewayHealthClient {
  return {
    getGatewayHealth(siteId) {
      return read(`${basePath}/${encodeURIComponent(siteId)}/gateway-health`, isGatewayHealth);
    },
  };
}
