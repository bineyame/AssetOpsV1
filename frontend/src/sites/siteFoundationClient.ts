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
 *
 * S1-02 adds the binding set in effect, configuration-only Readiness, the
 * gateway acquisition snapshot (download by `at`) and `POST
 * .../foundation/bindings`, which publishes a complete replacement binding
 * set from an effective time. Readiness is configuration: "ready to report"
 * never means a device is reporting or healthy.
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

export interface BindingSetSummary {
  binding_set_id: string;
  binding_set_revision_id: string;
  version: number;
  role_set: string;
  valid_from: string;
  valid_to: string | null;
  recorded_at: string;
  superseded_at: string | null;
  recorded_state: "CURRENT" | "SUPERSEDED";
  period_state: "PAST" | "CURRENT" | "FUTURE";
  origin: "CONVERSION" | "PUBLISH" | "SPLIT";
  derived_from_revision_id: string | null;
  bindings_sha256: string;
  foundation_revision_id: string;
  gateway_id: string;
  snapshot_schema: string;
  snapshot_sha256: string;
  binding_count: number;
  change_note: string | null;
}

export interface SignalBindingConversion {
  /** S1 publishes IDENTITY and ENUM only (D-2026-10-08-s1-bindings-roles-and-snapshot, Q4). */
  kind: "IDENTITY" | "ENUM";
  parameters: Record<string, unknown>;
}

export interface SignalBinding {
  binding_revision_id: string;
  binding_set_revision_id: string;
  device_id: string;
  signal_id: string;
  source_id: string;
  source_external_id: string | null;
  gateway_id: string;
  gateway_external_id: string | null;
  asset_id: string | null;
  asset_code: string | null;
  role: string;
  role_label: string;
  source_unit: string;
  canonical_unit: string;
  conversion: SignalBindingConversion;
}

export interface ReadinessRole {
  role: string;
  label: string;
  required: boolean;
  canonical_unit: string;
  covered_by: "CHANNEL" | "FOUNDATION_CONTROL";
  status: "CONFIGURED" | "UNBOUND" | "NOT_CONFIGURED";
  subjects: {
    asset_id: string | null;
    asset_code: string | null;
    status: "CONFIGURED" | "UNBOUND";
    binding_revision_ids: string[];
  }[];
  detail?: string;
  foundation_revision_id?: string;
}

export interface ReadinessChannel {
  device_id: string;
  signal_id: string;
  display_name: string | null;
  unit: string;
  source_id: string | null;
  status: "BOUND" | "UNBOUND" | "UNREGISTERED";
  binding_revision_id: string | null;
  role: string | null;
}

export interface ConfigurationReadiness {
  role_set: string | null;
  state: "READY_TO_REPORT" | "INCOMPLETE" | "UNKNOWN";
  binding_set_revision_id: string | null;
  foundation_revision_id: string;
  roles: ReadinessRole[];
  missing_roles: string[];
  /**
   * Configuration gaps of the selected Foundation revision. Any gap keeps the
   * aggregate state INCOMPLETE; they are reported apart from unbound roles.
   */
  foundation_gaps: FoundationGap[];
  channels: ReadinessChannel[];
  statement: string;
}

export interface FoundationBindings {
  state: "NONE" | "PUBLISHED";
  binding_set: BindingSetSummary | null;
  mappings: SignalBinding[];
  legacy_signal_mapping_count: number;
  statement: string;
}

export type AcquisitionSnapshotSummary =
  | { available: false; code: string; reason: string }
  | {
      available: true;
      sha256: string;
      schema: string;
      access: string;
      foundation_revision_id: string;
      binding_set_revision_id: string;
      valid_from: string;
      valid_to: string | null;
      byte_length: number;
    };

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
  bindings: FoundationBindings;
  readiness: ConfigurationReadiness;
  acquisition_snapshot: AcquisitionSnapshotSummary;
  evidence: { state: string; statement: string };
  configuration_gaps: FoundationGap[];
}

export interface FoundationVersionsReadModel {
  server_now: string;
  current_revision_id: string | null;
  revisions: FoundationRevisionSummary[];
  binding_sets: BindingSetSummary[];
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

/** One binding as the publish route takes it: the full replacement set. */
export interface BindingPublicationItem {
  device_id: string;
  signal_id: string;
  asset_id: string | null;
  role: string;
  source_unit: string;
  canonical_unit: string;
  conversion: SignalBindingConversion;
}

export interface BindingPublication {
  valid_from: string;
  bindings: BindingPublicationItem[];
  note?: string;
}

export type BindingPublishOutcome =
  | {
      status: "published";
      binding_set: BindingSetSummary;
      /** Where the change stops applying; null means it is open-ended. */
      applies_until?: string | null;
      /** The later independent binding version that stopped it, if any. */
      stopped_by_binding_version?: number | null;
    }
  | { status: "refused"; code: string; message: string };

export interface SiteFoundationClient {
  getFoundation(siteId: string, at: string | null): Promise<FoundationRead<FoundationReadModel>>;
  listVersions(siteId: string): Promise<FoundationRead<FoundationVersionsReadModel>>;
  publishReserve(siteId: string, change: ReservePublication): Promise<PublishOutcome>;
  publishBindings(siteId: string, change: BindingPublication): Promise<BindingPublishOutcome>;
  /** Where the browser downloads the snapshot for the instant shown. */
  snapshotUrl(siteId: string, at: string): string;
}

/** The publish shape of a binding read from the screen. */
export function bindingPublicationItem(binding: SignalBinding): BindingPublicationItem {
  return {
    device_id: binding.device_id,
    signal_id: binding.signal_id,
    asset_id: binding.asset_id,
    role: binding.role,
    source_unit: binding.source_unit,
    canonical_unit: binding.canonical_unit,
    conversion: binding.conversion,
  };
}

function isFoundation(value: unknown): value is FoundationReadModel {
  return (
    isObject(value) &&
    isObject(value.revision) &&
    isObject(value.site) &&
    isObject(value.detail) &&
    isObject(value.controls) &&
    isObject(value.bindings) &&
    Array.isArray(value.bindings.mappings) &&
    isObject(value.readiness) &&
    Array.isArray(value.readiness.roles) &&
    Array.isArray(value.readiness.foundation_gaps) &&
    isObject(value.acquisition_snapshot) &&
    Array.isArray(value.configuration_gaps) &&
    Array.isArray(value.sources)
  );
}

function isVersions(value: unknown): value is FoundationVersionsReadModel {
  return isObject(value) && Array.isArray(value.revisions) && Array.isArray(value.binding_sets);
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
    async publishBindings(siteId, change) {
      let response: Response;
      try {
        response = await fetch(`${site(siteId)}/bindings`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(change),
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
      if (response.status === 201 && isObject(body) && isObject(body.binding_set)) {
        return {
          status: "published",
          binding_set: body.binding_set as unknown as BindingSetSummary,
          applies_until: typeof body.applies_until === "string" ? body.applies_until : null,
          stopped_by_binding_version:
            typeof body.stopped_by_binding_version === "number" ? body.stopped_by_binding_version : null,
        };
      }
      return { status: "refused", ...refusal(body) };
    },
    snapshotUrl(siteId, at) {
      return `${site(siteId)}/snapshot?at=${encodeURIComponent(at)}`;
    },
  };
}
