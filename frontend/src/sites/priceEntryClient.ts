/**
 * PR-3 (D-PRICE.1, rev 5 §5.3): the site-admin price entry, `POST /api/sites/{site}/financial-assumptions/entries`.
 *
 * The browser sends only what the person typed plus one idempotency key per opened form; it never sends a change
 * kind, an instant or an actor. Every word shown back (dry-run summary, saved summary, refusal message) is the
 * server's. A refusal is `{"detail": {"code", "message"[, "fields"]}}` and nothing was written.
 */
import { isObject } from "./evidenceRead";
import { SITES_API_PATH } from "./siteDirectoryClient";

export type PriceBasis = "AUTHORED_ESTIMATE" | "CONTRACT_RATE" | "RECORDED_PURCHASE";

export interface PriceEntryRequest {
  key: string;
  value: string;
  currency: string;
  basis: PriceBasis | null;
  source: string;
  applies_from: string;
  reason: string | null;
  dry_run: boolean;
  idempotency_key: string;
}

export interface PriceEntryDryRun {
  dry_run: true;
  change_kind: "INITIAL" | "SUCCESSION" | "CORRECTION";
  applies_from: string;
  reason_required: boolean;
  summary: string;
}

export interface PriceEntrySaved {
  revision_id: string;
  revision_no: number;
  change_kind: "INITIAL" | "SUCCESSION" | "CORRECTION";
  applies_from: string;
  recorded_at: string;
  replayed: boolean;
  set_by: string;
  summary: string;
}

export type PriceEntryResult<T> =
  | { status: "ok"; value: T }
  /** 4xx with the server's code and words; nothing was written. */
  | { status: "refused"; code: string | null; message: string | null; fields: string[] }
  /** 503 (or a 5xx): the store cannot take a price now; nothing was written. */
  | { status: "unavailable" }
  /** No response: the save may or may not have landed; retrying with the same key is safe. */
  | { status: "lost" };

export interface PriceEntryClient {
  dryRun(siteId: string, request: PriceEntryRequest): Promise<PriceEntryResult<PriceEntryDryRun>>;
  save(siteId: string, request: PriceEntryRequest): Promise<PriceEntryResult<PriceEntrySaved>>;
}

/** `price-entry-<32 lowercase hex>`, the server's idempotency key shape; one per opened form. */
export function freshPriceEntryKey(): string {
  const bytes = new Uint8Array(16);
  if (globalThis.crypto?.getRandomValues) {
    globalThis.crypto.getRandomValues(bytes);
  } else {
    for (let i = 0; i < bytes.length; i += 1) bytes[i] = Math.floor(Math.random() * 256);
  }
  return `price-entry-${Array.from(bytes, (b) => b.toString(16).padStart(2, "0")).join("")}`;
}

function isDryRun(value: unknown): value is PriceEntryDryRun {
  return isObject(value) && value.dry_run === true && typeof value.summary === "string" &&
    typeof value.reason_required === "boolean";
}

function isSaved(value: unknown): value is PriceEntrySaved {
  return isObject(value) && typeof value.revision_id === "string" && typeof value.summary === "string";
}

function refusal(body: unknown): { code: string | null; message: string | null; fields: string[] } {
  const detail = isObject(body) ? body.detail : null;
  if (typeof detail === "string") return { code: null, message: detail, fields: [] };
  if (!isObject(detail)) return { code: null, message: null, fields: [] };
  return {
    code: typeof detail.code === "string" ? detail.code : null,
    message: typeof detail.message === "string" ? detail.message : null,
    fields: Array.isArray(detail.fields) ? detail.fields.filter((f): f is string => typeof f === "string") : [],
  };
}

export function createPriceEntryClient(basePath: string = SITES_API_PATH): PriceEntryClient {
  async function post<T>(siteId: string, request: PriceEntryRequest, ok: (v: unknown) => v is T): Promise<PriceEntryResult<T>> {
    let response: Response;
    try {
      response = await fetch(`${basePath}/${encodeURIComponent(siteId)}/financial-assumptions/entries`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(request),
      });
    } catch {
      return { status: "lost" };
    }
    let body: unknown = null;
    try {
      body = await response.json();
    } catch {
      body = null;
    }
    if (response.ok && ok(body)) return { status: "ok", value: body };
    if (response.status >= 500) return { status: "unavailable" };
    if (response.ok) return { status: "lost" };
    return { status: "refused", ...refusal(body) };
  }
  return {
    dryRun: (siteId, request) => post(siteId, { ...request, dry_run: true }, isDryRun),
    save: (siteId, request) => post(siteId, { ...request, dry_run: false }, isSaved),
  };
}
