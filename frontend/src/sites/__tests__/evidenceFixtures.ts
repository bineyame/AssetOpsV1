import type {
  EvidenceOverview,
  EvidenceRead,
  EvidenceRecordDetail,
  EvidenceRecordList,
  EvidenceRejections,
  EvidenceRecordQuery,
  SiteEvidenceClient,
} from "../siteEvidenceClient";

/**
 * Site > Evidence fixtures in the backend's shapes (`evidence_api.py`).
 * Spelled once so the screen tests and the tab-row test agree on what an
 * empty and a populated evidence read look like.
 */

export const EVIDENCE_SITE_ID = "KLG-014";

export const POPULATED_EVIDENCE: EvidenceOverview = {
  site_id: EVIDENCE_SITE_ID,
  window: {
    start: "2026-07-01T00:00:00Z",
    end: "2026-07-01T06:00:00Z",
    basis: "LATEST_RELEASE",
  },
  sources: [
    {
      source_id: "kobo-gw-1",
      gateway_id: "gw-1",
      source_mode: "SIMULATED",
      accepted_total: 120,
      accepted_in_window: 118,
      duplicates: 3,
      rejected: 2,
      conflicts: 1,
      last_source_time: "2026-07-01T05:55:00Z",
      last_published_at: "2026-07-01T05:56:00Z",
      last_received_at: "2026-07-02T09:00:12Z",
      batches: [
        { batch_id: "artifact-1", status: "COMPLETED", processed: 125, total: 125 },
        { batch_id: "artifact-0", status: "IN_PROGRESS", processed: 4, total: 10 },
      ],
    },
  ],
  source_health_statement:
    "Source and connector health describe data delivery and quality, never asset health.",
  coverage: [
    {
      device_id: "GEN-1",
      signal_id: "active_power",
      family: "MEASUREMENT",
      status: "REPORTED",
      unit: "kW",
      records: 72,
      good: 70,
      unavailable: 2,
      overlapping: 1,
      first_source_time: "2026-07-01T00:00:00Z",
      last_source_time: "2026-07-01T05:55:00Z",
      longest_silence_seconds: 900,
      needed_by: ["Dispatch"],
    },
    {
      device_id: "BAT-1",
      signal_id: "soc",
      family: "MEASUREMENT",
      status: "NOT_REPORTED",
      unit: "%",
      records: 0,
      good: 0,
      unavailable: 0,
      overlapping: 0,
      first_source_time: null,
      last_source_time: null,
      longest_silence_seconds: null,
      needed_by: ["Battery"],
    },
  ],
  coverage_statement:
    "Coverage counts accepted records in the window only. A gap is not filled, unavailable records are counted rather than given a value, and no sample is carried forward.",
  overlap_statement:
    "Distinct records at the same device, signal and source time are all kept and shown; none is summed with, or replaces, another.",
  basis: {
    mappings: [{ mapping_set_id: "kobo-v3", mapping_version: 3 }],
    configurations: [
      {
        foundation_version: 2,
        foundation_valid_from: "2026-06-01T00:00:00Z",
        registered_at: "2026-07-02T09:00:00Z",
        signal_count: 14,
      },
    ],
    current_foundation: {
      foundation_version: 3,
      foundation_valid_from: "2026-08-01T00:00:00Z",
    },
  },
  rejection_count: 2,
  conflict_count: 1,
};

export const EMPTY_EVIDENCE: EvidenceOverview = {
  ...POPULATED_EVIDENCE,
  window: { start: null, end: null, basis: "LATEST_RELEASE" },
  sources: [],
  coverage: [],
  basis: {
    mappings: [],
    configurations: [],
    current_foundation: POPULATED_EVIDENCE.basis.current_foundation,
  },
  rejection_count: 0,
  conflict_count: 0,
};

export const REJECTIONS: EvidenceRejections = {
  site_id: EVIDENCE_SITE_ID,
  total: 2,
  rejections: [
    {
      batch_id: "artifact-1",
      index: 7,
      message_id: "m-7",
      kind: "SIGNAL_NOT_IN_CONFIGURATION",
      field: "signal_id",
      detail: "The signal is not in the mapping.",
      reason: "The record's signal is not part of this site's equipment details.",
      received_at: "2026-07-02T09:00:05Z",
      content_digest: "sha256:aa",
    },
    {
      batch_id: "artifact-1",
      index: 9,
      message_id: "m-9",
      kind: "INVALID_PAYLOAD",
      field: "value",
      detail: "The value is not exact decimal text.",
      reason: "The record's value was not valid.",
      received_at: "2026-07-02T09:00:06Z",
      content_digest: "sha256:bb",
    },
  ],
};

export const RECORD_LIST: EvidenceRecordList = {
  site_id: EVIDENCE_SITE_ID,
  total: 72,
  limit: 50,
  records: [
    {
      message_id: "msg-gen-72",
      source_id: "kobo-gw-1",
      gateway_id: "gw-1",
      device_id: "GEN-1",
      signal_id: "active_power",
      family: "MEASUREMENT",
      value: "41.5",
      unit: "kW",
      quality: "GOOD",
      source_time: "2026-07-01T05:55:00Z",
      published_at: "2026-07-01T05:56:00Z",
      received_at: "2026-07-02T09:00:12Z",
      overlapping: false,
    },
  ],
};

export const RECORD_DETAIL: EvidenceRecordDetail = {
  message_id: "msg-gen-72",
  site_id: EVIDENCE_SITE_ID,
  source_id: "kobo-gw-1",
  gateway_id: "gw-1",
  source_mode: "SIMULATED",
  device_id: "GEN-1",
  signal_id: "active_power",
  family: "MEASUREMENT",
  measurement: "INSTANTANEOUS",
  mapping: { mapping_set_id: "kobo-v3", mapping_version: 3 },
  configuration: {
    foundation_version: 2,
    foundation_valid_from: "2026-06-01T00:00:00Z",
    registered_at: "2026-07-02T09:00:00Z",
  },
  quality: "GOOD",
  unavailable_reason: null,
  original: { value: "41.5", unit: "kW" },
  normalized: { value: "41.5", unit: "kW" },
  normalization: "IDENTITY",
  normalization_statement:
    "AssetOps uses this value and unit exactly as the source sent them; it does not convert units.",
  interval: null,
  record_detail: {},
  source_time: "2026-07-01T05:55:00Z",
  published_at: "2026-07-01T05:56:00Z",
  received_at: "2026-07-02T09:00:12Z",
  batch_id: "artifact-1",
  content_digest: "sha256:cc",
  envelope_text: "{}",
  overlapping_with: [],
  conflicts: [],
};

export interface FakeEvidence extends SiteEvidenceClient {
  recordQueries: EvidenceRecordQuery[];
}

export function evidenceClient(
  overview: EvidenceRead<EvidenceOverview>,
  rejections: EvidenceRead<EvidenceRejections> = {
    status: "loaded",
    value: REJECTIONS,
  },
): FakeEvidence {
  const recordQueries: EvidenceRecordQuery[] = [];
  return {
    recordQueries,
    getEvidence: () => Promise.resolve(overview),
    listRejections: () => Promise.resolve(rejections),
    listRecords: (_siteId, query) => {
      recordQueries.push(query);
      return Promise.resolve({ status: "loaded", value: RECORD_LIST });
    },
    getRecord: (_siteId, messageId) =>
      Promise.resolve(
        messageId === RECORD_DETAIL.message_id
          ? { status: "loaded", value: RECORD_DETAIL }
          : { status: "not_found" },
      ),
  };
}

export const EMPTY_EVIDENCE_CLIENT = evidenceClient(
  { status: "loaded", value: EMPTY_EVIDENCE },
  { status: "loaded", value: { site_id: EVIDENCE_SITE_ID, total: 0, rejections: [] } },
);
