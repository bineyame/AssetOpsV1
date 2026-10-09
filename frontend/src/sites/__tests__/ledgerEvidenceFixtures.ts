/**
 * S2-02 phase 3b fixtures: central-ledger Site Evidence payloads in the shapes
 * `backend/assetops_backend/evidence/ledger_reads.py` builds, and a fake
 * client that records what the screen asked for.
 */

import type { EvidenceRead } from "../evidenceRead";
import type { GatewayHealth, GatewayHealthClient } from "../gatewayHealthClient";
import type {
  LedgerEvidence,
  LedgerEvidenceClient,
  LedgerRecordDetail,
  LedgerRecordPage,
  LedgerRecordQuery,
  LedgerRejections,
} from "../ledgerEvidenceClient";
import type { SiteEvidenceClient } from "../siteEvidenceClient";

const CLOCKS = { source_time: "RUN_VIRTUAL", published_at: "RUN_VIRTUAL", received_at: "SERVER_RECEIVED_AT" };
export const EVIDENCE_UUID = "3f6b2a10-0000-4000-8000-000000000001";
export const SECOND_UUID = "3f6b2a10-0000-4000-8000-000000000002";

export const LEDGER_EVIDENCE: LedgerEvidence = {
  store: "POSTGRES",
  site_id: "KOBO-001",
  site_uuid: "11111111-0000-4000-8000-000000000000",
  tenant_id: "22222222-0000-4000-8000-000000000000",
  window: { start: "2026-09-22T06:00:00Z", end: "2026-09-22T18:00:00Z", half_open: true, clock: "SOURCE_TIME", basis: "REQUESTED" },
  extent: {
    first_source_time: "2026-09-22T06:00:00Z",
    last_source_time: "2026-09-22T17:55:00Z",
    last_received_at: "2026-10-09T09:14:03.123456Z",
    accepted_total: 290,
  },
  state: "ACCEPTED",
  states: ["ACCEPTED"],
  clock_statement: "Source and publication times on simulated reports are run-virtual instants.",
  sources: [
    {
      source_id: "aaaa0000-0000-4000-8000-000000000001",
      external_id: "kobo-inverter-1",
      gateway_id: "bbbb0000-0000-4000-8000-000000000001",
      gateway_external_id: "kobo-gw-1",
      source_mode: "SIMULATED",
      clocks: CLOCKS,
      accepted_in_window: 288,
      duplicates_in_window: 3,
      conflicts_in_window: 1,
      rejected_in_window: 2,
      last_source_time: "2026-09-22T17:55:00Z",
      last_published_at: "2026-09-22T17:55:00Z",
      last_received_at: "2026-10-09T09:14:03.123456Z",
    },
  ],
  batches: [
    {
      batch_id: "batch-0001",
      batch_uuid: "cccc0000-0000-4000-8000-000000000001",
      source_id: "aaaa0000-0000-4000-8000-000000000001",
      status: "COMPLETED",
      partial: false,
      payload_sha256: "a".repeat(64),
      counts: { total: 3, processed: 3, accepted: 2, duplicate: 0, rejected: 1, conflict: 0 },
      accepted_in_window: 2,
      received_at: "2026-10-09T09:00:00.000001Z",
      completed_at: "2026-10-09T09:00:01.000001Z",
    },
  ],
  coverage: [
    {
      device_id: "inv-1",
      signal_id: "ac_power",
      role: "AC_POWER",
      unit: "kW",
      records: 288,
      good: 287,
      configuration_outdated: 0,
      first_source_time: "2026-09-22T06:00:00Z",
      last_source_time: "2026-09-22T17:55:00Z",
    },
  ],
  counts: { accepted: 288, duplicates: 3, rejected: 2, conflicts: 1, rejected_without_source_time: 1 },
  projection: {
    status: "NO_PENDING_DISPATCH",
    pending_jobs: 0,
    leased_jobs: 0,
    failed_jobs: 0,
    oldest_job_created_at: null,
    statement: "Accepted evidence queues dispatch recompute jobs.",
  },
  migration: {
    report_id: "20261009T080000Z-abc",
    outcome: "PASSED",
    empty_set: true,
    statement: "No file-backed evidence existed.",
    compared_at: "2026-10-09T08:00:00Z",
  },
  limits: [],
};

export function ledgerEvidence(patch: Partial<LedgerEvidence>): LedgerEvidence {
  return { ...LEDGER_EVIDENCE, ...patch };
}

const ITEM = {
  evidence_id: EVIDENCE_UUID,
  message_id: "msg-0001",
  source: { source_id: "aaaa0000-0000-4000-8000-000000000001", external_id: "kobo-inverter-1" },
  gateway: { gateway_id: "bbbb0000-0000-4000-8000-000000000001", external_id: "kobo-gw-1" },
  device_id: "inv-1",
  signal_id: "ac_power",
  role: "AC_POWER",
  family: "MEASUREMENT",
  measurement: "POWER",
  quality: "GOOD",
  unavailable_reason: null,
  original: { value: "12500", unit: "W" },
  normalized: { value: "12.5", unit: "kW" },
  source_time: "2026-09-22T06:00:00Z",
  published_at: "2026-09-22T06:00:00Z",
  received_at: "2026-10-09T09:00:00.000001Z",
  interval: null,
  configuration_outdated: false,
  source_mode: "SIMULATED",
  clocks: CLOCKS,
};

export const LEDGER_PAGE: LedgerRecordPage = {
  store: "POSTGRES",
  site_id: "KOBO-001",
  window: LEDGER_EVIDENCE.window,
  total: 288,
  limit: 50,
  next_cursor: "2026-09-22T06:00:00.000000Z~" + EVIDENCE_UUID,
  records: [{ ...ITEM, receipt: { batch_id: "batch-0001", ordinal: 0 } }],
};

export const LEDGER_RECORD: LedgerRecordDetail = {
  ...ITEM,
  store: "POSTGRES",
  site_id: "KOBO-001",
  sequence: { epoch: "e1", sequence: 1 },
  envelope: { sha256: "e".repeat(64), text: '{"message_id":"msg-0001","value":"12500"}' },
  accepted_as: {
    foundation_revision_id: "f0000000-0000-4000-8000-000000000001",
    binding_set_revision_id: "f0000000-0000-4000-8000-000000000002",
    binding_revision_id: "f0000000-0000-4000-8000-000000000003",
    asset_id: "f0000000-0000-4000-8000-000000000004",
    conversion_kind: "SCALE",
    configuration_outdated: false,
  },
  receipt: {
    batch_id: "batch-0001",
    batch_uuid: "cccc0000-0000-4000-8000-000000000001",
    ordinal: 0,
    decision: "ACCEPTED",
    payload_sha256: "a".repeat(64),
    batch_status: "COMPLETED",
    processed: 3,
    total: 3,
    received_at: "2026-10-09T09:00:00.000001Z",
    decided_at: "2026-10-09T09:07:00.000001Z",
    completed_at: "2026-10-09T09:07:01.000001Z",
  },
  duplicates: [{ batch_id: "batch-0002", ordinal: 4, received_at: "2026-10-09T09:10:00.000001Z", decided_at: "2026-10-09T09:10:00.000002Z" }],
  conflicts: [
    {
      rejection_id: "dddd0000-0000-4000-8000-000000000001",
      batch_id: "batch-0003",
      ordinal: 1,
      kind: "MESSAGE_CONFLICT",
      detail: "message id seen with different bytes",
      envelope_sha256: "f".repeat(64),
      envelope_text: '{"message_id":"msg-0001","value":"99999"}',
      received_at: "2026-10-09T09:11:00.000001Z",
      decided_at: "2026-10-09T09:11:00.000002Z",
    },
  ],
};

export const LEDGER_REJECTIONS: LedgerRejections = {
  store: "POSTGRES",
  site_id: "KOBO-001",
  total: 1,
  rejections: [
    {
      rejection_id: "dddd0000-0000-4000-8000-000000000009",
      batch_id: "batch-0001",
      ordinal: 2,
      message_id: "msg-0003",
      decision: "REJECTED",
      kind: "SOURCE_TIME_INVALID",
      field: "timing.source_time",
      detail: "source_time is not a valid instant",
      source_time: null,
      received_at: "2026-10-09T09:00:00.000001Z",
      decided_at: "2026-10-09T09:00:00.500001Z",
      envelope_sha256: "b".repeat(64),
      envelope_text: "{}",
      conflicts_with_evidence_id: null,
    },
  ],
  conflicts: [],
  duplicates: [
    {
      batch_id: "batch-0002",
      ordinal: 4,
      message_id: "msg-0001",
      first_accepted_evidence_id: EVIDENCE_UUID,
      received_at: "2026-10-09T09:10:00.000001Z",
      decided_at: "2026-10-09T09:10:00.000002Z",
    },
  ],
};

export const GATEWAY_HEALTH: GatewayHealth = {
  site_id: "11111111-0000-4000-8000-000000000000",
  read_at: "2026-10-09T09:15:00Z",
  read_at_clock: "SERVER_REAL_UTC",
  claim_scope: "GATEWAY_OPERATIONAL_REPORT",
  gateways: [
    {
      gateway_id: "bbbb0000-0000-4000-8000-000000000001",
      gateway_external_id: "kobo-gw-1",
      mode: "SIMULATED",
      registration: "ENABLED",
      declared_cadence_seconds: 60,
      status: "CURRENT",
      status_basis: "SERVER_RECEIVED_AT",
      last_server_contact: "2026-10-09T09:14:30Z",
      diagnostic_id: "99990000-0000-4000-8000-000000000001",
      gateway_observed_at: "2026-10-09T09:14:29Z",
      observed_at_clock: "GATEWAY_REAL_UTC",
      queue_count: 4,
      oldest_queue_age_seconds: 12,
      disk_pressure: "OK",
      disk_pressure_provenance: "REPORTED_SIMULATED_GATEWAY",
      clock_offset_ms: null,
      mapping_error_count: 0,
      source_contacts: [
        {
          source_id: "aaaa0000-0000-4000-8000-000000000001",
          source_external_id: "kobo-inverter-1",
          registration: "ENABLED",
          last_contact: "2026-10-09T09:14:00Z",
          contact_provenance: "OBSERVED_SIMULATED_REPORT",
        },
      ],
    },
  ],
};

export interface FakeLedger extends SiteEvidenceClient {
  recordQueries: LedgerRecordQuery[];
  recordKeys: string[];
}

export function ledgerClient(
  overview: EvidenceRead<LedgerEvidence>,
  options: { health?: EvidenceRead<GatewayHealth>; rejections?: EvidenceRead<LedgerRejections> } = {},
): FakeLedger {
  const recordQueries: LedgerRecordQuery[] = [];
  const recordKeys: string[] = [];
  const ledger: LedgerEvidenceClient = {
    listRecords: (_site, query) => {
      recordQueries.push(query);
      return Promise.resolve({ status: "loaded", value: LEDGER_PAGE });
    },
    getRecord: (_site, key) => {
      recordKeys.push(key);
      return Promise.resolve({ status: "loaded", value: LEDGER_RECORD });
    },
    listRejections: () => Promise.resolve(options.rejections ?? { status: "loaded", value: LEDGER_REJECTIONS }),
  };
  const gatewayHealth: GatewayHealthClient = {
    getGatewayHealth: () => Promise.resolve(options.health ?? { status: "loaded", value: GATEWAY_HEALTH }),
  };
  return {
    recordQueries,
    recordKeys,
    ledger,
    gatewayHealth,
    getEvidence: () => Promise.resolve(overview),
    listRecords: () => Promise.resolve({ status: "unavailable", message: null }),
    getRecord: () => Promise.resolve({ status: "unavailable", message: null }),
    listRejections: () => Promise.resolve({ status: "unavailable", message: null }),
  };
}
