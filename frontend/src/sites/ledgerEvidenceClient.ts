/**
 * Read-only client for an imported Site's central evidence ledger (S2-02
 * phase 3b). The backend answers the same four Site Evidence routes from the
 * central ledger once that Site's legacy comparison permits it, and marks each
 * payload `store: "POSTGRES"` (`evidence/ledger_reads.py` module docstring).
 * Until then it keeps answering 409 `AWAITING_EVIDENCE_MIGRATION`, which the
 * shared `read` helper names.
 *
 * Clocks. `source_time` and `published_at` on a simulated report are
 * run-virtual instants; `received_at` is the server's real first receipt of
 * the batch. Nothing here subtracts one clock from the other.
 *
 * A response that does not match its shape is `unavailable`, never a partial
 * page.
 */

import { SITES_API_PATH } from "./siteDirectoryClient";
import {
  arrayOf,
  hasKeys,
  isObject,
  query,
  read,
  type EvidenceRead,
} from "./evidenceRead";
import type { EvidenceWindowQuery } from "./siteEvidenceClient";

export type ClockLabel = "RUN_VIRTUAL" | "SOURCE_REPORTED" | "SERVER_RECEIVED_AT" | string;

export interface LedgerClocks {
  source_time: ClockLabel;
  published_at: ClockLabel;
  received_at: ClockLabel;
}

export interface LedgerWindow {
  start: string | null;
  end: string | null;
  half_open: boolean;
  clock: string;
  basis: "ALL" | "REQUESTED";
}

export type LedgerState =
  | "NO_DATA"
  | "REJECTED_ONLY"
  | "ACCEPTED"
  | "PARTIAL_BATCH"
  | "CONFLICTING"
  | "STALE_PROJECTION"
  | "OUTDATED_CONFIGURATION";

export interface LedgerSource {
  source_id: string;
  external_id: string;
  gateway_id: string;
  gateway_external_id: string;
  source_mode: string;
  clocks: LedgerClocks;
  accepted_in_window: number;
  duplicates_in_window: number;
  conflicts_in_window: number;
  rejected_in_window: number;
  last_source_time: string | null;
  last_published_at: string | null;
  last_received_at: string | null;
}

export interface LedgerBatch {
  batch_id: string;
  batch_uuid: string;
  source_id: string;
  status: string;
  partial: boolean;
  payload_sha256: string;
  counts: {
    total: number;
    processed: number;
    accepted: number;
    duplicate: number;
    rejected: number;
    conflict: number;
  };
  accepted_in_window: number;
  received_at: string | null;
  completed_at: string | null;
}

export interface LedgerCoverage {
  device_id: string;
  signal_id: string;
  role: string | null;
  unit: string | null;
  records: number;
  good: number;
  configuration_outdated: number | boolean;
  first_source_time: string | null;
  last_source_time: string | null;
}

export interface LedgerMigration {
  report_id: string | null;
  outcome: string | null;
  empty_set: boolean | null;
  statement: string | null;
  compared_at: string | null;
}

export interface LedgerEvidence {
  store: "POSTGRES";
  site_id: string;
  site_uuid: string;
  tenant_id: string;
  window: LedgerWindow;
  extent: {
    first_source_time: string | null;
    last_source_time: string | null;
    last_received_at: string | null;
    accepted_total: number;
  };
  state: "NO_DATA" | "REJECTED_ONLY" | "ACCEPTED";
  states: LedgerState[];
  clock_statement: string;
  sources: LedgerSource[];
  batches: LedgerBatch[];
  coverage: LedgerCoverage[];
  counts: {
    accepted: number;
    duplicates: number;
    rejected: number;
    conflicts: number;
    rejected_without_source_time: number;
  };
  projection: {
    status: "STALE" | "NO_PENDING_DISPATCH" | string;
    pending_jobs: number;
    leased_jobs: number;
    failed_jobs: number;
    oldest_job_created_at: string | null;
    statement: string;
  };
  migration: LedgerMigration | null;
  limits: string[];
}

export interface LedgerRecordItem {
  evidence_id: string;
  message_id: string;
  source: { source_id: string; external_id: string };
  gateway: { gateway_id: string; external_id: string };
  device_id: string;
  signal_id: string;
  role: string | null;
  family: string | null;
  measurement: string | null;
  quality: string;
  unavailable_reason: string | null;
  original: { value: string | null; unit: string | null };
  normalized: { value: string | null; unit: string | null };
  source_time: string;
  published_at: string | null;
  received_at: string | null;
  interval: { start: string; end: string } | null;
  configuration_outdated: boolean;
  source_mode: string;
  clocks: LedgerClocks;
  receipt: { batch_id: string; ordinal: number };
}

export interface LedgerRecordPage {
  store: "POSTGRES";
  site_id: string;
  window: LedgerWindow;
  total: number;
  limit: number;
  next_cursor: string | null;
  records: LedgerRecordItem[];
}

export interface LedgerRecordDetail extends Omit<LedgerRecordItem, "receipt"> {
  store: "POSTGRES";
  site_id: string;
  sequence: { epoch: string | number | null; sequence: number | null };
  envelope: { sha256: string; text: string };
  accepted_as: {
    foundation_revision_id: string;
    binding_set_revision_id: string;
    binding_revision_id: string;
    asset_id: string | null;
    conversion_kind: string | null;
    configuration_outdated: boolean;
  };
  receipt: {
    batch_id: string;
    batch_uuid: string;
    ordinal: number;
    decision: string;
    payload_sha256: string;
    batch_status: string;
    processed: number;
    total: number;
    received_at: string | null;
    decided_at: string | null;
    completed_at: string | null;
  };
  duplicates: {
    batch_id: string;
    ordinal: number;
    received_at: string | null;
    decided_at: string | null;
  }[];
  conflicts: {
    rejection_id: string;
    batch_id: string;
    ordinal: number;
    kind: string;
    detail: string;
    envelope_sha256: string | null;
    envelope_text: string | null;
    received_at: string | null;
    decided_at: string | null;
  }[];
}

export interface LedgerRejection {
  rejection_id: string;
  batch_id: string;
  ordinal: number | null;
  message_id: string | null;
  decision: string;
  kind: string;
  field: string | null;
  detail: string;
  source_time: string | null;
  received_at: string | null;
  decided_at: string | null;
  envelope_sha256: string | null;
  envelope_text: string | null;
  conflicts_with_evidence_id: string | null;
  /** Q19: the original accepted reading's source time (lineage only); the
   * rejection's own `source_time` places it. */
  conflicts_with_source_time?: string | null;
}

export interface LedgerRejections {
  store: "POSTGRES";
  site_id: string;
  total: number;
  rejected_without_source_time?: number;
  rejections: LedgerRejection[];
  conflicts: LedgerRejection[];
  duplicates: {
    batch_id: string;
    ordinal: number;
    message_id: string;
    first_accepted_evidence_id: string;
    received_at: string | null;
    decided_at: string | null;
  }[];
}

export interface LedgerRecordQuery extends EvidenceWindowQuery {
  device?: string | null;
  signal?: string | null;
  source?: string | null;
  cursor?: string | null;
  limit?: number;
}

/** The central-ledger reads beside the legacy ones; an evidence id opens a record. */
export interface LedgerEvidenceClient {
  listRecords(siteId: string, request: LedgerRecordQuery): Promise<EvidenceRead<LedgerRecordPage>>;
  getRecord(siteId: string, evidenceId: string): Promise<EvidenceRead<LedgerRecordDetail>>;
  listRejections(siteId: string, batch?: string | null): Promise<EvidenceRead<LedgerRejections>>;
}

const POSTGRES = "POSTGRES";

/** True for the central-ledger Site Evidence payload, the only one marked `store`. */
export function isLedgerEvidence(value: unknown): value is LedgerEvidence {
  return (
    isObject(value) &&
    value.store === POSTGRES &&
    hasKeys(value, ["site_id", "window", "extent", "state", "states", "counts", "projection", "clock_statement"]) &&
    hasKeys(value.window, ["start", "end", "basis"]) &&
    Array.isArray(value.states) &&
    arrayOf(value.sources, ["source_id", "external_id", "source_mode", "clocks", "accepted_in_window"]) &&
    arrayOf(value.batches, ["batch_id", "status", "partial", "counts"]) &&
    arrayOf(value.coverage, ["device_id", "signal_id", "records"]) &&
    hasKeys(value.counts, ["accepted", "duplicates", "rejected", "conflicts"]) &&
    hasKeys(value.projection, ["status", "statement"])
  );
}

function isRecordItem(value: unknown): boolean {
  return (
    hasKeys(value, [
      "evidence_id",
      "message_id",
      "source",
      "device_id",
      "signal_id",
      "original",
      "normalized",
      "source_time",
      "published_at",
      "received_at",
      "clocks",
      "receipt",
    ])
  );
}

function isRecordPage(value: unknown): value is LedgerRecordPage {
  return (
    isObject(value) &&
    value.store === POSTGRES &&
    typeof value.total === "number" &&
    "next_cursor" in value &&
    Array.isArray(value.records) &&
    value.records.every(isRecordItem)
  );
}

function isRecordDetail(value: unknown): value is LedgerRecordDetail {
  return (
    isObject(value) &&
    value.store === POSTGRES &&
    isRecordItem(value) &&
    hasKeys(value.envelope, ["sha256", "text"]) &&
    hasKeys(value.accepted_as, ["foundation_revision_id", "binding_set_revision_id", "binding_revision_id"]) &&
    hasKeys(value.receipt, ["batch_id", "ordinal", "decision", "received_at", "decided_at"]) &&
    Array.isArray(value.duplicates) &&
    Array.isArray(value.conflicts)
  );
}

function isRejections(value: unknown): value is LedgerRejections {
  return (
    isObject(value) &&
    value.store === POSTGRES &&
    typeof value.total === "number" &&
    arrayOf(value.rejections, ["batch_id", "kind", "detail", "decision"]) &&
    Array.isArray(value.conflicts) &&
    Array.isArray(value.duplicates)
  );
}

export function createLedgerEvidenceClient(basePath: string = SITES_API_PATH): LedgerEvidenceClient {
  const evidencePath = (siteId: string) => `${basePath}/${encodeURIComponent(siteId)}/evidence`;
  return {
    listRecords(siteId, request) {
      return read(
        `${evidencePath(siteId)}/records${query({
          device: request.device,
          signal: request.signal,
          source: request.source,
          from: request.from,
          to: request.to,
          cursor: request.cursor,
          limit: request.limit,
        })}`,
        isRecordPage,
      );
    },
    getRecord(siteId, evidenceId) {
      return read(`${evidencePath(siteId)}/records/${encodeURIComponent(evidenceId)}`, isRecordDetail);
    },
    listRejections(siteId, batch) {
      return read(`${evidencePath(siteId)}/rejections${query({ batch })}`, isRejections);
    },
  };
}
