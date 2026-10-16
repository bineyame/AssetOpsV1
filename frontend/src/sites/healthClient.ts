/**
 * S7-01b: client for the two S7-01a reads the Site Health and battery screens show.
 *
 * - `GET /api/sites/{site}/source-health` (`assetops.site-source-health` v1): server-receipt gateway contact,
 *   separate from what each gateway last reported about itself (`D-2026-10-16-a-s7-health`,
 *   `D-2026-10-16-s701-clock`).
 * - `GET /api/sites/{site}/battery` and `GET /api/sites/{site}/assets/{asset}/battery`
 *   (`assetops.asset-boundary` v1): the configured battery and its Unknown condition with named missing inputs.
 *
 * Every non-200 answer is a typed refusal that keeps its HTTP status and server code, so 401/403/404/409/422/503
 * never read as an empty or healthy result.
 */
import { SITES_API_PATH } from "./siteDirectoryClient";
import { arrayOf, hasKeys, isObject } from "./evidenceRead";

export interface HealthRefusal {
  status: "refused";
  /** HTTP status, or null when the server could not be reached. */
  http: number | null;
  code: string | null;
  message: string | null;
}

export type HealthRead<T> = { status: "loaded"; value: T } | HealthRefusal;

export type ContactStatus = "CURRENT" | "STALE" | "UNKNOWN";

export interface GatewayHealthRow {
  gateway_id: string;
  gateway_external_id: string;
  mode: string;
  registration: "ENABLED" | "DISABLED";
  registered_at: string;
  declared_cadence_seconds: number;
  contact: {
    status: ContactStatus;
    basis: string;
    last_received_at: string | null;
    threshold_seconds: number;
    since_last_receipt_seconds: number | null;
    reason: string;
  };
  diagnostic: {
    diagnostic_id: string;
    sequence_epoch: string;
    diagnostic_sequence: number;
    received_at: string;
    observed_at: string;
    observed_at_clock: string;
    payload_sha256: string;
  } | null;
  reported_facts: {
    status: "CURRENT" | "OLD" | "UNKNOWN";
    reason: string;
    observed_at: string | null;
    fact_age_seconds: number | null;
    receipt_lag_seconds: number | null;
    clock: {
      offset_ms: number | null;
      trust: "WITHIN_TOLERANCE" | "UNTRUSTED" | "UNKNOWN";
      reason: string;
      tolerance_ms: number;
      observed_after_receipt_allowance_ms?: number;
    };
    queue: { count: number; oldest_age_seconds: number | null; as: string } | null;
    disk_pressure: { value: string; as: string; provenance: string } | null;
    mapping_error_count: number | null;
  };
  sources: {
    source_id: string;
    source_external_id: string;
    registration: "ENABLED" | "DISABLED";
    reported_contact: string | null;
    reported_contact_status: "REPORTED" | "REPORTED_NEVER_HEARD" | "NOT_IN_SELECTED_DIAGNOSTIC";
    reported_contact_age_seconds: number | null;
    contact_basis: string;
  }[];
  source_watermark: {
    diagnostic_id: string;
    sequence_epoch: string;
    diagnostic_sequence: number;
    received_at: string;
  } | null;
}

export interface SourceHealthDocument {
  schema: { id: string; version: number };
  rule_id: string;
  site_code: string;
  site_id: string;
  read_at: string;
  read_at_clock: string;
  claim_scope: string;
  not_claimed: string[];
  snapshot: { isolation: string; selection: string };
  stale_projection: { applicable: boolean; reason: string };
  summary: {
    status: "NO_REGISTERED_SOURCE" | "ALL_CURRENT" | "NOT_ALL_CURRENT";
    /** `D-2026-10-16-s701-clock` L3; absent on a pre-follow-up server. */
    reason?: "NO_ENABLED_GATEWAY" | "NO_REGISTERED_GATEWAY" | null;
    enabled_gateway_count: number;
    disabled_gateway_count: number;
    contact_counts: Record<ContactStatus, number>;
    source_watermark: {
      selected_diagnostic_count: number;
      latest_received_at: string | null;
      selected_diagnostic_ids_sha256: string;
    };
  };
  gateways: GatewayHealthRow[];
}

export interface AssetBasis {
  foundation_revision_id: string;
  foundation_version: number;
  binding_set_revision_id: string | null;
  binding_set_version: number | null;
  binding_set_foundation_revision_id: string | null;
  effective_at: string;
  knowledge_at: string;
}

export interface PhysicalCondition {
  status: "UNKNOWN";
  reason: string;
  missing_causal_inputs: { input: string; status: string; reason: string }[];
}

interface AssetEnvelope {
  schema: { id: string; version: number };
  rule_id: string;
  site_code: string;
  site_id: string;
  read_at: string;
  basis: AssetBasis;
  withheld: string[];
}

export interface BatteryEntry extends AssetEnvelope {
  configuration: "CONFIGURED" | "NOT_CONFIGURED";
  reason: string | null;
  batteries: { asset_id: string; asset_code: string; display_name: string | null; detail_path: string }[];
  physical_condition?: PhysicalCondition;
}

export interface BatteryDetail extends AssetEnvelope {
  configuration: "CONFIGURED";
  asset: { asset_id: string; asset_code: string; asset_type: string; display_name: string | null };
  binding_status: "BOUND" | "UNBOUND" | "NO_BINDING_SET";
  bound_channels: {
    binding_revision_id: string;
    role: string;
    gateway_id: string;
    source_id: string;
    device_id: string;
    signal_id: string;
    label: string;
  }[];
  declared_nameplate: {
    value: number | null;
    unit: string | null;
    label: string;
    foundation_revision_id: string;
    component_id: string;
  } | null;
  accepted_state_of_charge: { included: boolean; reason: string };
  physical_condition: PhysicalCondition;
}

export interface HealthClient {
  getSourceHealth(siteId: string): Promise<HealthRead<SourceHealthDocument>>;
  getBatteryEntry(siteId: string): Promise<HealthRead<BatteryEntry>>;
  getBatteryDetail(siteId: string, assetId: string): Promise<HealthRead<BatteryDetail>>;
}

const SCHEMA_HEALTH = "assetops.site-source-health";
const SCHEMA_ASSET = "assetops.asset-boundary";

function schemaIs(value: unknown, id: string): boolean {
  return isObject(value) && isObject(value.schema) && value.schema.id === id && value.schema.version === 1;
}

export function isSourceHealthDocument(value: unknown): value is SourceHealthDocument {
  return (
    schemaIs(value, SCHEMA_HEALTH) &&
    hasKeys(value, ["site_code", "read_at", "summary", "gateways"]) &&
    hasKeys((value as Record<string, unknown>).summary, ["status", "enabled_gateway_count", "contact_counts"]) &&
    arrayOf((value as Record<string, unknown>).gateways, [
      "gateway_id",
      "gateway_external_id",
      "registration",
      "contact",
      "reported_facts",
      "sources",
    ])
  );
}

export function isBatteryEntry(value: unknown): value is BatteryEntry {
  return (
    schemaIs(value, SCHEMA_ASSET) &&
    hasKeys(value, ["configuration", "basis", "batteries"]) &&
    arrayOf((value as Record<string, unknown>).batteries, ["asset_id", "detail_path"])
  );
}

export function isBatteryDetail(value: unknown): value is BatteryDetail {
  return (
    schemaIs(value, SCHEMA_ASSET) &&
    hasKeys(value, ["asset", "binding_status", "bound_channels", "physical_condition", "basis"]) &&
    hasKeys((value as Record<string, unknown>).physical_condition, ["status", "reason", "missing_causal_inputs"]) &&
    // S7-01b L4: only an Unknown condition is a battery detail this page can show; anything else is refused.
    ((value as Record<string, Record<string, unknown>>).physical_condition.status === "UNKNOWN")
  );
}

function refusal(http: number | null, body: unknown): HealthRefusal {
  const detail = isObject(body) ? body.detail : null;
  if (typeof detail === "string") {
    return { status: "refused", http, code: null, message: detail };
  }
  if (isObject(detail)) {
    return {
      status: "refused",
      http,
      code: typeof detail.code === "string" ? detail.code : null,
      message: typeof detail.message === "string" ? detail.message : null,
    };
  }
  return { status: "refused", http, code: null, message: null };
}

async function read<T>(path: string, valid: (value: unknown) => value is T): Promise<HealthRead<T>> {
  let response: Response;
  try {
    response = await fetch(path);
  } catch {
    return refusal(null, null);
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
  // A 200 that is not the versioned document is a refusal too (502: the answer could not be used).
  return refusal(response.ok ? 502 : response.status, body);
}

export function createHealthClient(basePath: string = SITES_API_PATH): HealthClient {
  const site = (siteId: string) => `${basePath}/${encodeURIComponent(siteId)}`;
  return {
    getSourceHealth: (siteId) => read(`${site(siteId)}/source-health`, isSourceHealthDocument),
    getBatteryEntry: (siteId) => read(`${site(siteId)}/battery`, isBatteryEntry),
    getBatteryDetail: (siteId, assetId) =>
      read(`${site(siteId)}/assets/${encodeURIComponent(assetId)}/battery`, isBatteryDetail),
  };
}
