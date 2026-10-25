/* Copied from frontend/src/shell/__tests__/siteFoundationRevision.test.tsx (revision, UNKNOWN_READINESS, foundation, PAST, FUTURE, VERSIONS);
   the only change: the site code and detail DTO are parameters, so the harness can lengthen selected fields. */
import type { ConfigurationReadiness, FoundationReadModel, FoundationRevisionSummary, FoundationVersionsReadModel } from "../../../frontend/src/sites/siteFoundationClient";
import type { SiteDetailReadModel } from "../../../frontend/src/sites/siteReadModel";
function revision(over: Partial<FoundationRevisionSummary>): FoundationRevisionSummary {
  return {
    revision_id: "rev-1",
    version: 1,
    valid_from: "2026-09-29T11:57:49Z",
    valid_to: null,
    recorded_at: "2026-10-07T11:00:00Z",
    superseded_at: null,
    recorded_state: "CURRENT",
    period_state: "CURRENT",
    origin: "IMPORT",
    derived_from_revision_id: null,
    content_sha256: "a".repeat(64),
    change_note: null,
    battery_reserve: { value: 30, unit: "%" },
    ...over,
  };
}

const UNKNOWN_READINESS: ConfigurationReadiness = {
  role_set: "minigrid-roles-1",
  state: "UNKNOWN",
  binding_set_revision_id: null,
  foundation_revision_id: "rev-2",
  roles: [
    { role: "generator_power", label: "Generator power", required: true, canonical_unit: "kW", covered_by: "CHANNEL", status: "UNBOUND", subjects: [] },
  ],
  missing_roles: ["Generator power"],
  foundation_gaps: [],
  channels: [],
  statement: "No channel-link set is in effect for the period shown, so every role is unbound and readiness is Unknown. Operational status is not assessed here.",
};

export function foundation(rev: FoundationRevisionSummary, ID: string, SITE: SiteDetailReadModel, over: Partial<FoundationReadModel> = {}): FoundationReadModel {
  return {
    resolved: { at: rev.valid_from, knowledge_at: "2026-10-07T12:00:00Z", server_now: "2026-10-07T12:00:00Z" },
    site: {
      site_uuid: "site-uuid-1",
      site_code: ID,
      tenant: "demo",
      display_name: SITE.display_name,
      site_type: "MINIGRID",
      timezone: SITE.timezone,
      lifecycle_status: "PLANNED",
    },
    revision: { ...rev, is_current: rev.period_state === "CURRENT", current_revision_id: "rev-2" },
    provenance: {
      import_id: "imp-1",
      source_path: "var/sites/kobo-001.yaml",
      source_sha256: "b".repeat(64),
      imported_at: "2026-10-07T11:00:00Z",
      imported_revision_id: "rev-1",
      imported_version: 1,
    },
    detail: SITE,
    assets: [],
    gateways: [
      { gateway_id: "g1", gateway_external_id: "edge-kobo-001", mode: "SIMULATED", status: "PENDING", credential: "NOT_PROVISIONED" },
    ],
    sources: [
      { source_id: "s1", source_external_id: "generator-controller", device_kind: "CONTROLLER", display_name: "Generator controller", asset_code: "generator", status: "PENDING" },
    ],
    controls: {
      battery_reserve: { state: "CONFIGURED", editable: true, asset_code: "battery", value: rev.battery_reserve?.value ?? 30, unit: "%", authority: `Foundation v${rev.version}` },
      generator_minimum_runtime: { state: "DECLARED", editable: false, value: 30, unit: "min", authority: `Foundation v${rev.version}` },
      generator_start_stop: { state: "NOT_CONFIGURED", editable: false, message: "This Foundation declares no generator start or stop threshold." },
      source_priority: { state: "CONFIGURED", editable: false, members: ["pv-array", "battery", "generator"], authority: `Foundation v${rev.version}` },
      critical_load_priority: { state: "CONFIGURED", editable: false, members: ["load-clinic", "load-res", "load-mill"], authority: `Foundation v${rev.version}` },
    },
    bindings: {
      state: "NONE",
      binding_set: null,
      mappings: [],
      legacy_signal_mapping_count: 9,
      statement: "No channel-link set is in effect for the period shown. Every channel is unbound; the imported signal links are kept for comparison only.",
    },
    readiness: UNKNOWN_READINESS,
    acquisition_snapshot: {
      available: false,
      code: "ACQUISITION_SNAPSHOT_UNAVAILABLE",
      reason: "No channel-link set is in effect for the period shown, so no gateway snapshot exists.",
    },
    evidence: { statement: "Operational status (contact, credentials, data received, accepted evidence) is not assessed here." },
    configuration_gaps: [],
    ...over,
  };
}
export const PAST = revision({ revision_id: "rev-2", version: 2, origin: "SPLIT", valid_to: "2026-10-10T00:00:00Z", period_state: "CURRENT" });
export const FUTURE = revision({ revision_id: "rev-3", version: 3, origin: "PUBLISH", valid_from: "2026-10-10T00:00:00Z", period_state: "FUTURE", battery_reserve: { value: 25, unit: "%" } });
export const VERSIONS: FoundationVersionsReadModel = {
  server_now: "2026-10-07T12:00:00Z",
  current_revision_id: "rev-2",
  revisions: [revision({ recorded_state: "SUPERSEDED", superseded_at: "2026-10-07T12:00:00Z" }), PAST, FUTURE],
  binding_sets: [],
};
