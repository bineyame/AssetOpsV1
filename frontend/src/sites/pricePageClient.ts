/**
 * PR-2a (BL-68): the read-only Site price page read, `GET /api/sites/{site}/prices?need=&known_at=`.
 *
 * Every word on the page is the server's (`financials/price_page.py`): row labels, "Not set", the future-key
 * sentence, basis, History headlines and "Set by". The page renders them and never classifies a key. Status mapping
 * is the price read's: 401, 403, 404 as not found, 422 as invalid, 503 or a network failure as unavailable.
 */
import { arrayOf, hasKeys, isObject } from "./evidenceRead";
import type { FindingReadResult } from "./findingClient";
import { SITES_API_PATH } from "./siteDirectoryClient";

export interface PriceHistoryEntry {
  revision_id: string;
  revision_no: number;
  change_kind: "INITIAL" | "SUCCESSION" | "CORRECTION";
  headline: string;
  until_text: string | null;
  value_text: string;
  basis_text: string;
  source_reference: string | null;
  reason: string | null;
  set_by_label: string;
  recorded_text: string;
  replaced: boolean;
  replaced_text: string | null;
}

export interface CurrentPrice {
  revision_id: string;
  value: string;
  currency: string;
  unit: string;
  value_text: string;
  amount_text: string;
  per_text: string;
  basis_text: string;
  source_reference: string | null;
  applies_from_text: string;
  applies_until_text: string | null;
  set_by_label: string;
  recorded_text: string;
}

export interface PriceRowBody {
  key: string;
  noun: string;
  label: string;
  detail: string;
  /** A key the store can hold today (PR-3 adds the form to these rows only). */
  stored: boolean;
  state: "SET" | "NOT_SET";
  current: CurrentPrice | null;
  not_set_text: string | null;
  /** The future-key sentence ("Saving this price comes once a figure uses it."), or null. */
  note: string | null;
  used_by: { text: string; detail: string };
  history: PriceHistoryEntry[];
  history_title: string | null;
  /** One line when the server read stopped at its cap and older versions are not shown, else null/absent. */
  history_capped_text?: string | null;
}

export interface NeedBlock {
  need_key: string;
  title: string;
  text: string;
  meanwhile: string;
  link_label: string;
}

export interface PricePage {
  site_code: string;
  site_name: string;
  title: string;
  intro: string;
  sign_in_text: string;
  table_title: string;
  table_note: string;
  count_text: string;
  cutoff: { known_at: string | null; text: string | null };
  prices: PriceRowBody[];
  need: NeedBlock | null;
  /** PR-3: which rows take the inline price form. Absent from an older server: no form. */
  entry?: PriceEntryBlock;
}

/** PR-3 (rev 5 §5.3): `enabled` only with the entry service on and no `known_at`; `keys` are stored keys only. */
export interface PriceEntryBlock {
  enabled: boolean;
  keys: string[];
  /** The Site-local date "Applies from" defaults to. */
  today: string | null;
  /** Unit words per key for the Amount suffix ("per litre"). */
  unit_text: Record<string, string>;
  /** Currency codes for a key with no price yet. */
  currencies: string[];
  /** Under `known_at` with entry on: the honest-state words and the live-view link label. */
  live_view: { text: string; link_label: string } | null;
}

/** A 422 (a `known_at` without an offset) is its own refusal: it is not a missing Site (PR-2a review L1). */
export type PricePageResult = FindingReadResult<PricePage> | { status: "invalid"; message: string | null };

export interface PricePageClient {
  getPrices(siteId: string, query: { need?: string | null; knownAt?: string | null }): Promise<PricePageResult>;
}

const ROW_KEYS = ["key", "label", "detail", "stored", "state", "current", "note", "used_by", "history"] as const;

export function isPricePage(value: unknown): value is PricePage {
  return (
    hasKeys(value, ["site_code", "title", "sign_in_text", "table_title", "count_text", "cutoff", "prices", "need"]) &&
    arrayOf((value as { prices: unknown }).prices, ROW_KEYS)
  );
}

function message(body: unknown): string | null {
  const detail = isObject(body) ? body.detail : null;
  if (typeof detail === "string") return detail;
  return isObject(detail) && typeof detail.message === "string" ? detail.message : null;
}

export function createPricePageClient(basePath: string = SITES_API_PATH): PricePageClient {
  return {
    async getPrices(siteId, query) {
      const params = new URLSearchParams();
      if (query.need) params.set("need", query.need);
      if (query.knownAt) params.set("known_at", query.knownAt);
      const text = params.toString();
      let response: Response;
      try {
        response = await fetch(`${basePath}/${encodeURIComponent(siteId)}/prices${text ? `?${text}` : ""}`);
      } catch {
        return { status: "unavailable", message: null };
      }
      let body: unknown = null;
      try {
        body = await response.json();
      } catch {
        body = null;
      }
      if (response.ok && isPricePage(body)) return { status: "loaded", value: body };
      const said = message(body);
      switch (response.status) {
        case 401:
          return { status: "unauthenticated", message: said };
        case 403:
          return { status: "forbidden", message: said };
        case 404:
          return { status: "not_found", message: said };
        case 422:
          return { status: "invalid", message: said };
        default:
          return { status: "unavailable", message: said };
      }
    },
  };
}
