/**
 * The persisted Foundation read and its one S1 write (S1-01).
 *
 * `GET /api/sites/{id}/foundation?at=` reads the revision effective at a
 * chosen instant (the server resolves and returns the instant), `GET
 * .../foundation/versions` lists persisted periods for selection, and `POST
 * .../foundation/revisions` publishes a battery reserve change and nothing
 * else. `knowledge_at` is an API-only audit parameter in S1 and is not sent
 * from the screen. A Site still read from its legacy document answers
 * `migration_required`, never a fabricated version.
 */

import { SITES_API_PATH } from "./siteDirectoryClient";
import type { SiteDetailReadModel } from "./siteReadModel";
import { isObject } from "./siteEvidenceClient";

export interface FoundationRevisionSummary {
  revision_id: string;
  version: number;
  valid_from: string;
  valid_to: string | null;
  recorded_at: string;
  superseded_at: string | null;
  recorded_state: "CURRENT" | "SUPERSEDED";
  period_state: "PAST" | "CURRENT" | "FUTURE";
  origin: "IMPORT" | "PUBLISH" | "SPLIT";
  derived_from_revision_id: string | null;
  content_sha256: string;
  change_note: string | null;
  battery_reserve: { value: number; unit: string } | null;
}

export interface FoundationControl {
  state: "CONFIGURED" | "DECLARED" | "NOT_CONFIGURED";
  editable: boolean;
  asset_code?: string;
  asset_id?: string | null;
  value?: number;
  unit?: string;
  members?: string[];
  authority?: string;
  message?: string;
}

export interface FoundationGap {
  code: string;
  subject: string;
  message: string;
}

export interface FoundationReadModel {
  resolved: { at: string; knowledge_at: string; server_now: string };
  site: {
    site_uuid: string;
    site_code: string;
    tenant: string;
    display_name: string;
    site_type: string;
    timezone: string;
    lifecycle_status: string;
  };
  revision: FoundationRevisionSummary & {
    is_current: boolean;
    current_revision_id: string | null;
  };
  provenance: {
    import_id: string | null;
    source_path: string | null;
    source_sha256: string | null;
    imported_at: string | null;
    imported_revision_id: string | null;
    imported_version: number | null;
  };
  detail: SiteDetailReadModel;
  assets: { asset_id: string; asset_code: string; asset_type: string; display_name: string | null }[];
  gateways: {
    gateway_id: string;
    gateway_external_id: string;
    mode: string;
    status: string;
    credential: string;
  }[];
  sources: {
    source_id: string;
    source_external_id: string;
    device_kind: string;
    display_name: string | null;
    asset_code: string | null;
    status: string;
  }[];
  controls: {
    battery_reserve: FoundationControl;
    generator_minimum_runtime: FoundationControl;
    generator_start_stop: FoundationControl;
    source_priority: FoundationControl;
    critical_load_priority: FoundationControl;
  };
  bindings: { state: string; legacy_signal_mapping_count: number; statement: string };
  acquisition_snapshot: { available: boolean; reason: string };
  evidence: { state: string; statement: string };
  configuration_gaps: FoundationGap[];
}

export interface FoundationVersionsReadModel {
  server_now: string;
  current_revision_id: string | null;
  revisions: FoundationRevisionSummary[];
}

export type FoundationRead<T> =
  | { status: "loaded"; value: T }
  | { status: "migration_required"; message: string }
  | { status: "not_found"; message: string }
  | { status: "invalid"; message: string }
  | { status: "unavailable"; message: string | null };

export interface ReservePublication {
  asset_code: string;
  value: number;
  valid_from: string;
}

export type PublishOutcome =
  | { status: "published"; revision: FoundationRevisionSummary }
  | { status: "refused"; code: string; message: string };

export interface SiteFoundationClient {
  getFoundation(siteId: string, at: string | null): Promise<FoundationRead<FoundationReadModel>>;
  listVersions(siteId: string): Promise<FoundationRead<FoundationVersionsReadModel>>;
  publishReserve(siteId: string, change: ReservePublication): Promise<PublishOutcome>;
}

function isFoundation(value: unknown): value is FoundationReadModel {
  return (
    isObject(value) &&
    isObject(value.revision) &&
    isObject(value.site) &&
    isObject(value.detail) &&
    isObject(value.controls) &&
    Array.isArray(value.configuration_gaps) &&
    Array.isArray(value.sources)
  );
}

function isVersions(value: unknown): value is FoundationVersionsReadModel {
  return isObject(value) && Array.isArray(value.revisions);
}

function refusal(body: unknown): { code: string; message: string } {
  const detail = isObject(body) ? body.detail : null;
  if (isObject(detail) && typeof detail.code === "string" && typeof detail.message === "string") {
    return { code: detail.code, message: detail.message };
  }
  return { code: "UNKNOWN", message: "The request was refused." };
}

async function readFoundation<T>(
  path: string,
  valid: (value: unknown) => value is T,
): Promise<FoundationRead<T>> {
  let response: Response;
  try {
    response = await fetch(path);
  } catch {
    return { status: "unavailable", message: null };
  }
  let body: unknown = null;
  try {
    body = await response.json();
  } catch {
    body = null;
  }
  if (response.ok && valid(body)) {
    return { status: "loaded", value: body };
  }
  const { code, message } = refusal(body);
  if (code === "FOUNDATION_MIGRATION_REQUIRED") return { status: "migration_required", message };
  if (response.status === 404) return { status: "not_found", message };
  if (response.status === 422) return { status: "invalid", message };
  return { status: "unavailable", message };
}

export function createSiteFoundationClient(basePath: string = SITES_API_PATH): SiteFoundationClient {
  const site = (siteId: string) => `${basePath}/${encodeURIComponent(siteId)}/foundation`;
  return {
    getFoundation(siteId, at) {
      const query = at === null ? "" : `?at=${encodeURIComponent(at)}`;
      return readFoundation(`${site(siteId)}${query}`, isFoundation);
    },
    listVersions(siteId) {
      return readFoundation(`${site(siteId)}/versions`, isVersions);
    },
    async publishReserve(siteId, change) {
      let response: Response;
      try {
        response = await fetch(`${site(siteId)}/revisions`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            asset_code: change.asset_code,
            property_key: "reserve-state-of-charge",
            value: change.value,
            unit: "%",
            valid_from: change.valid_from,
          }),
        });
      } catch {
        return { status: "refused", code: "UNAVAILABLE", message: "The change could not be sent." };
      }
      let body: unknown = null;
      try {
        body = await response.json();
      } catch {
        body = null;
      }
      if (response.status === 201 && isObject(body) && isObject(body.revision)) {
        return { status: "published", revision: body.revision as unknown as FoundationRevisionSummary };
      }
      return { status: "refused", ...refusal(body) };
    },
  };
}
