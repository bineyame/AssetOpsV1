/**
 * Read-only client for a Site's accepted evidence (T027, Site > Evidence).
 *
 * An operator capability, never gated: accepted evidence is served with the
 * Simulator Lab gate closed, so this client spells only operator paths under
 * `/api/sites` and is built with no reference to the feature flag. It reads.
 * There is no ingest, edit or delete method here; evidence is written only by
 * ingestion.
 *
 * Every shape below is the backend's (`evidence_api.py` module docstring).
 * Instants are `YYYY-MM-DDTHH:MM:SSZ` text and values are exact decimal text or
 * a discrete member, never floats, so nothing here parses a number it would
 * then display rounded.
 *
 * Failures are named states rather than thrown. A response that does not match
 * the expected shape is `unavailable`, not a partial page: a screen must not
 * show half the coverage and let a reader believe the rest was not reported.
 */

import { SITES_API_PATH } from "./siteDirectoryClient";
import { arrayOf, hasKeys, isObject, query, read, type EvidenceRead } from "./evidenceRead";
import { createClaimLimitClient, type ClaimLimitClient } from "./claimLimitClient";
import { createGatewayHealthClient, type GatewayHealthClient } from "./gatewayHealthClient";
import { createLedgerEvidenceClient, isLedgerEvidence, type LedgerEvidence, type LedgerEvidenceClient } from "./ledgerEvidenceClient";

export { arrayOf, awaitingMigration, hasKeys, isObject, query, read, type EvidenceRead } from "./evidenceRead";

export interface EvidenceBatchProgress {
  batch_id: string;
  status: string;
  processed: number;
  total: number;
}

export interface EvidenceSourceHealth {
  source_id: string;
  gateway_id: string;
  source_mode: string;
  accepted_total: number;
  accepted_in_window: number;
  duplicates: number;
  rejected: number;
  conflicts: number;
  last_source_time: string | null;
  last_published_at: string | null;
  last_received_at: string | null;
  batches: EvidenceBatchProgress[];
}

export interface EvidenceCoverage {
  device_id: string;
  signal_id: string;
  family: string | null;
  status: "REPORTED" | "NOT_REPORTED";
  unit: string | null;
  records: number;
  good: number;
  unavailable: number;
  overlapping: number;
  first_source_time: string | null;
  last_source_time: string | null;
  longest_silence_seconds: number | null;
  needed_by: string[];
}

export interface EvidenceBasis {
  mappings: { mapping_set_id: string; mapping_version: number }[];
  configurations: {
    foundation_version: number;
    foundation_valid_from: string;
    registered_at: string;
    signal_count: number;
  }[];
  current_foundation: {
    foundation_version: number;
    foundation_valid_from: string;
  } | null;
}

export interface EvidenceOverview {
  site_id: string;
  window: {
    start: string | null;
    end: string | null;
    basis: "LATEST_RELEASE" | "REQUESTED";
  };
  sources: EvidenceSourceHealth[];
  source_health_statement: string;
  coverage: EvidenceCoverage[];
  coverage_statement: string;
  overlap_statement: string;
  basis: EvidenceBasis;
  rejection_count: number;
  conflict_count: number;
}

export interface EvidenceRecordItem {
  message_id: string;
  source_id: string;
  gateway_id: string;
  device_id: string;
  signal_id: string;
  family: string | null;
  value: string | null;
  unit: string | null;
  quality: string;
  source_time: string;
  published_at: string;
  received_at: string;
  overlapping: boolean;
}

export interface EvidenceRecordList {
  site_id: string;
  total: number;
  limit: number;
  records: EvidenceRecordItem[];
}

export interface EvidenceRecordDetail {
  message_id: string;
  site_id: string;
  source_id: string;
  gateway_id: string;
  source_mode: string;
  device_id: string;
  signal_id: string;
  family: string | null;
  measurement: string | null;
  mapping: { mapping_set_id: string; mapping_version: number };
  configuration: {
    foundation_version: number;
    foundation_valid_from: string;
    registered_at: string;
  };
  quality: string;
  unavailable_reason: string | null;
  original: { value: string | null; unit: string | null };
  normalized: { value: string | null; unit: string | null };
  normalization: string;
  normalization_statement: string;
  interval: { start: string; end: string } | null;
  record_detail: Record<string, string> | null;
  source_time: string;
  published_at: string;
  received_at: string;
  batch_id: string;
  content_digest: string;
  /** The canonical envelope exactly as accepted. */
  envelope_text: string;
  overlapping_with: string[];
  conflicts: {
    batch_id: string;
    original_digest: string;
    conflicting_digest: string;
    received_at: string;
  }[];
}

export interface EvidenceRejection {
  batch_id: string;
  index: number | null;
  message_id: string | null;
  kind: string;
  field: string | null;
  detail: string;
  /** The plain read-time reason (T028 presentation 2b); absent from an older backend. */
  reason?: string;
  received_at: string;
  content_digest: string | null;
}

export interface EvidenceRejections {
  site_id: string;
  total: number;
  rejections: EvidenceRejection[];
}

export interface EvidenceWindowQuery {
  from?: string | null;
  to?: string | null;
}

export interface EvidenceRecordQuery extends EvidenceWindowQuery {
  device?: string | null;
  signal?: string | null;
  source?: string | null;
  limit?: number;
}

export interface SiteEvidenceClient {
  /**
   * A legacy Site answers the file-backed overview; an imported Site whose
   * comparison permits it answers the central-ledger payload (`store: "POSTGRES"`).
   */
  getEvidence(
    siteId: string,
    window: EvidenceWindowQuery,
  ): Promise<EvidenceRead<EvidenceOverview | LedgerEvidence>>;
  listRecords(
    siteId: string,
    query: EvidenceRecordQuery,
  ): Promise<EvidenceRead<EvidenceRecordList>>;
  getRecord(
    siteId: string,
    messageId: string,
  ): Promise<EvidenceRead<EvidenceRecordDetail>>;
  listRejections(
    siteId: string,
    batch?: string | null,
  ): Promise<EvidenceRead<EvidenceRejections>>;
  /** The central-ledger reads (records by cursor, record by evidence id). */
  ledger?: LedgerEvidenceClient;
  /** The Site's central gateway contact, shown beside ledger evidence. */
  gatewayHealth?: GatewayHealthClient;
  /** S3-02b: the selected assessment's claim limit on Evidence Analysis. */
  claimLimit?: ClaimLimitClient;
}

function isOverview(value: unknown): value is EvidenceOverview {
  return (
    hasKeys(value, [
      "site_id",
      "window",
      "sources",
      "coverage",
      "basis",
      "rejection_count",
    ]) &&
    isObject(value) &&
    hasKeys(value.window, ["start", "end", "basis"]) &&
    arrayOf(value.sources, ["source_id", "gateway_id", "source_mode", "batches"]) &&
    arrayOf(value.coverage, ["device_id", "signal_id", "status", "needed_by"]) &&
    hasKeys(value.basis, ["mappings", "configurations", "current_foundation"])
  );
}

function isRecordList(value: unknown): value is EvidenceRecordList {
  return (
    isObject(value) &&
    typeof value.total === "number" &&
    arrayOf(value.records, [
      "message_id",
      "device_id",
      "signal_id",
      "source_time",
      "published_at",
      "received_at",
    ])
  );
}

function isRecordDetail(value: unknown): value is EvidenceRecordDetail {
  return (
    hasKeys(value, [
      "message_id",
      "mapping",
      "configuration",
      "original",
      "normalized",
      "source_time",
      "published_at",
      "received_at",
    ]) &&
    isObject(value) &&
    Array.isArray(value.overlapping_with) &&
    Array.isArray(value.conflicts)
  );
}

function isRejections(value: unknown): value is EvidenceRejections {
  return (
    isObject(value) &&
    typeof value.total === "number" &&
    arrayOf(value.rejections, ["batch_id", "kind", "detail"])
  );
}

export function createSiteEvidenceClient(
  basePath: string = SITES_API_PATH,
): SiteEvidenceClient {
  const evidencePath = (siteId: string) =>
    `${basePath}/${encodeURIComponent(siteId)}/evidence`;
  return {
    ledger: createLedgerEvidenceClient(basePath),
    gatewayHealth: createGatewayHealthClient(basePath),
    claimLimit: createClaimLimitClient(basePath),
    getEvidence(siteId, window) {
      return read(
        `${evidencePath(siteId)}${query({ from: window.from, to: window.to })}`,
        (value: unknown): value is EvidenceOverview | LedgerEvidence =>
          isLedgerEvidence(value) || isOverview(value),
      );
    },
    listRecords(siteId, request) {
      return read(
        `${evidencePath(siteId)}/records${query({
          device: request.device,
          signal: request.signal,
          source: request.source,
          from: request.from,
          to: request.to,
          limit: request.limit,
        })}`,
        isRecordList,
      );
    },
    getRecord(siteId, messageId) {
      return read(
        `${evidencePath(siteId)}/records/${encodeURIComponent(messageId)}`,
        isRecordDetail,
      );
    },
    listRejections(siteId, batch) {
      return read(
        `${evidencePath(siteId)}/rejections${query({ batch })}`,
        isRejections,
      );
    },
  };
}
