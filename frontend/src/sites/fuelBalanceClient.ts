/**
 * DIESEL-K5 (DIESEL-1-R3l): the fuel-balance night and fuel Finding reads. Every visible string in these bodies is
 * composed on the server (`backend/assetops_backend/fuel_balance/night_text.py`); the browser formats no number.
 */
import type { MiniRead, MiniSourceBlock } from "./miniDepthClient";
import { SITES_API_PATH } from "./siteDirectoryClient";

export interface FuelProvenance {
  source_provenance: MiniSourceBlock | null;
  selected_source_provenance: MiniSourceBlock | null;
  pending_source_provenance: MiniSourceBlock | null;
}

export interface FuelNightSummary {
  night_date: string;
  label: string;
  state: string;
  status: string;
  tone: string;
  revision: number;
}

export interface FuelNightsBody {
  site_code: string;
  mode: "NIGHTS" | "NONE";
  time_zone: string | null;
  known_at: string;
  nights: FuelNightSummary[];
  provenance: FuelProvenance;
}

export interface FuelNightCard {
  key: string;
  label: string;
  value: string;
  note: string | null;
  word: boolean;
}

export interface FuelNightBar {
  key: string;
  label: string;
  value_l: number | null;
  text: string;
}

export interface FuelBridgeRow {
  term: string;
  label: string;
  value: string;
  basis: string;
  treatment: string;
  evidence_count: number;
}

export interface FuelRecordRow {
  code: string;
  kind: string;
  when: string;
  volume: string;
  occurred_at: string;
}

export interface FuelNightFinding {
  finding_id: string;
  title: string;
  text: string;
  href: string;
}

export interface FuelNightBody extends FuelNightSummary {
  site_code: string;
  time_zone: string;
  known_at: string;
  window_start: string;
  window_end: string;
  cards: FuelNightCard[];
  bars: FuelNightBar[];
  bridge: FuelBridgeRow[];
  notes: string[];
  margin: string | null;
  records: FuelRecordRow[];
  records_empty: string;
  finding?: FuelNightFinding | null;
  finding_note?: string | null;
  provenance: FuelProvenance;
  links: { evidence: string | null; fuel_page: string };
}

export interface FuelFindingRow {
  finding_id: string;
  night_date: string;
  lifecycle: string;
  text: string;
  href: string;
}

export interface FuelFindingsBody {
  site_code: string;
  rows: FuelFindingRow[];
}

export interface FuelFindingLines {
  title: string;
  claim: string | null;
  gap: string | null;
  money: string | null;
  not_why: string;
  margin: string | null;
  no_longer: string | null;
}

export interface FuelFindingBody {
  site_code: string;
  finding_id: string;
  revision_id: string;
  revision_no: number;
  lifecycle: string;
  lifecycle_text: string;
  night_date: string;
  label: string;
  lines: FuelFindingLines;
  night: FuelNightBody;
  revisions: { revision_id: string; revision_no: number; text: string }[];
  provenance: FuelProvenance;
  links: { canonical: string; fuel_night: string; fuel_night_label: string };
}

export interface FuelBalanceClient {
  /** SR-10k: with `range` (the date range's UTC instants, `to` excluded) the list holds that range's nights only. */
  getNights(siteCode: string, range?: { from: string; to: string } | null): Promise<MiniRead<FuelNightsBody>>;
  getNight(siteCode: string, nightDate: string): Promise<MiniRead<FuelNightBody>>;
  getFuelFindings(siteCode: string, window: { from: string; to: string }): Promise<MiniRead<FuelFindingsBody>>;
  getFuelFinding(siteCode: string, findingId: string, revisionId?: string | null): Promise<MiniRead<FuelFindingBody>>;
}

const isObject = (value: unknown): value is Record<string, unknown> => typeof value === "object" && value !== null;

async function read<T>(url: string, shape: (value: Record<string, unknown>) => boolean): Promise<MiniRead<T>> {
  let response: Response;
  try {
    response = await fetch(url);
  } catch {
    return { status: "unavailable", message: null };
  }
  let body: unknown = null;
  try {
    body = await response.json();
  } catch {
    body = null;
  }
  if (response.ok) {
    return isObject(body) && shape(body)
      ? { status: "loaded", value: body as T }
      : { status: "unavailable", message: null };
  }
  const detail = isObject(body) && isObject(body.detail) ? body.detail : null;
  if (detail !== null && typeof detail.code === "string") {
    return { status: "refused", httpStatus: response.status, code: detail.code, message: typeof detail.message === "string" ? detail.message : null };
  }
  return { status: "unavailable", message: null };
}

export function createFuelBalanceClient(basePath: string = SITES_API_PATH): FuelBalanceClient {
  const site = (code: string) => `${basePath}/${encodeURIComponent(code)}`;
  return {
    getNights: (code, range) =>
      read(`${site(code)}/fuel-balance/nights${range ? `?${new URLSearchParams({ from: range.from, to: range.to }).toString()}` : ""}`, (b) => (b.mode === "NIGHTS" || b.mode === "NONE") && Array.isArray(b.nights)),
    getNight: (code, nightDate) =>
      read(`${site(code)}/fuel-balance/nights/${encodeURIComponent(nightDate)}`, (b) => Array.isArray(b.cards) && Array.isArray(b.bridge)),
    getFuelFindings: (code, window) =>
      read(
        `${site(code)}/fuel-findings?${new URLSearchParams({ from: window.from, to: window.to }).toString()}`,
        (b) =>
          Array.isArray(b.rows) &&
          b.rows.every((r) => isObject(r) && typeof r.finding_id === "string" && typeof r.text === "string" && typeof r.lifecycle === "string"),
      ),
    getFuelFinding: (code, findingId, revisionId) =>
      read(
        `${site(code)}/fuel-findings/${encodeURIComponent(findingId)}${revisionId ? `?revision_id=${encodeURIComponent(revisionId)}` : ""}`,
        (b) => isObject(b.lines) && isObject(b.night),
      ),
  };
}
