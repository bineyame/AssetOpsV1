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
  received_at: string;
  content_digest: string | null;
}

export interface EvidenceRejections {
  site_id: string;
  total: number;
  rejections: EvidenceRejection[];
}

export type EvidenceRead<T> =
  | { status: "loaded"; value: T }
  | { status: "not_found" }
  | { status: "unavailable"; message: string | null };

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
  getEvidence(
    siteId: string,
    window: EvidenceWindowQuery,
  ): Promise<EvidenceRead<EvidenceOverview>>;
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
}

function isObject(value: unknown): value is Record<string, unknown> {
  return value !== null && typeof value === "object" && !Array.isArray(value);
}

function hasKeys(value: unknown, keys: readonly string[]): boolean {
  return isObject(value) && keys.every((key) => key in value);
}

function arrayOf(value: unknown, keys: readonly string[]): boolean {
  return Array.isArray(value) && value.every((item) => hasKeys(item, keys));
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

async function read<T>(
  path: string,
  valid: (value: unknown) => value is T,
): Promise<EvidenceRead<T>> {
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
  if (response.status === 404) {
    return { status: "not_found" };
  }
  if (response.ok && valid(body)) {
    return { status: "loaded", value: body };
  }
  const detail = isObject(body) ? body.detail : null;
  return {
    status: "unavailable",
    message:
      isObject(detail) && typeof detail.message === "string"
        ? detail.message
        : null,
  };
}

function query(params: Record<string, string | number | null | undefined>): string {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== null && value !== undefined && value !== "") {
      search.set(key, String(value));
    }
  }
  const text = search.toString();
  return text === "" ? "" : `?${text}`;
}

export function createSiteEvidenceClient(
  basePath: string = SITES_API_PATH,
): SiteEvidenceClient {
  const evidencePath = (siteId: string) =>
    `${basePath}/${encodeURIComponent(siteId)}/evidence`;
  return {
    getEvidence(siteId, window) {
      return read(
        `${evidencePath(siteId)}${query({ from: window.from, to: window.to })}`,
        isOverview,
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
