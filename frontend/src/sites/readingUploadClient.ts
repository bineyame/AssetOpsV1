/**
 * UP-1 (rev 7 §7.5, D-17N.5, D-UP.1-11): Kobo's reading upload, `/api/sites/{site}/reading-uploads`.
 *
 * - `entry`: `GET .../reading-uploads` is 200 only when `ASSETOPS_READING_UPLOAD_SITES` names the Site (off by
 *   default); any refusal means "not here", so the Health panel and the page stay hidden or say so.
 * - `check` / `save`: `POST ...?dry_run=true|false&file_name=` with the file as the raw `text/csv` body
 *   (D-UP.5, SPEC DEVIATION transport: not multipart). A dry run writes nothing.
 * - `status`: `GET .../reading-uploads/{id}`; the state is derived on the server from the ledger at each read.
 *
 * Every sentence shown is the server's (`text`, `message`, `*_text`); the browser never names an actor.
 */
import { isObject } from "./evidenceRead";
import { SITES_API_PATH } from "./siteDirectoryClient";

export type UploadState = "CHECKED" | "SENT" | "ACCEPTED" | "PROCESSING" | "ANALYSED" | "NOT_ANALYSED" | "REFUSED";

export interface UploadColumn {
  column: string | null;
  unit: string;
  profile_unit?: string;
  unit_matches?: boolean;
  readings: number;
  blanks: number;
  blank_times?: string[];
  meter_text?: string;
  role_name_text?: string;
}

export interface UploadPreview {
  period_start: string;
  period_end: string;
  rows: number;
  cells: number;
  readings: number;
  blanks: number;
  columns: UploadColumn[];
}

export interface UploadChecked {
  state: "CHECKED";
  preview: UploadPreview;
  latest_saved: string | null;
  text: string;
}

export interface UploadStatus {
  upload_id: string;
  file_name: string;
  state: Exclude<UploadState, "CHECKED">;
  held: boolean;
  counts: { rows: number; readings: number; blanks: number; admitted: number; held: number; accepted: number; accepted_of: number };
  period_start: string | null;
  period_end: string | null;
  uploaded_by_text: string;
  entered_at: string | null;
  text: string;
  board_day?: string;
  held_by_column?: Record<string, number>;
  refusal?: { code: string; where: string | null };
}

export interface UploadRefusal {
  code: string | null;
  message: string | null;
  /** The place in plain words ("row 7 · timestamp_utc", "column 3", "Solar power"); the server never sends a path. */
  where: string | null;
  /** A confirmed (not dry-run) refusal is recorded; its reference. */
  upload_id: string | null;
}

export type UploadResult<T> =
  | { status: "ok"; value: T }
  /** The whole file was refused (4xx); nothing was admitted. */
  | { status: "refused"; refusal: UploadRefusal }
  /** 5xx: the gateway or store could not take it now; nothing was saved. */
  | { status: "unavailable"; message: string | null }
  /** No response: a save may or may not have landed. */
  | { status: "lost" };

export type UploadEntry = { status: "on"; templateNote: string; healthText: string; templateStep: string } | { status: "off" };

export interface ReadingUploadClient {
  entry(siteId: string): Promise<UploadEntry>;
  check(siteId: string, file: File): Promise<UploadResult<UploadChecked>>;
  save(siteId: string, file: File): Promise<UploadResult<UploadStatus>>;
  status(siteId: string, uploadId: string): Promise<UploadResult<UploadStatus>>;
}

export function readingUploadsPath(siteId: string, basePath: string = SITES_API_PATH): string {
  return `${basePath}/${encodeURIComponent(siteId)}/reading-uploads`;
}

export function readingTemplateHref(siteId: string, basePath: string = SITES_API_PATH): string {
  return `${readingUploadsPath(siteId, basePath)}/template`;
}

function isChecked(value: unknown): value is UploadChecked {
  return isObject(value) && value.state === "CHECKED" && isObject(value.preview) && Array.isArray(value.preview.columns);
}

function isStatus(value: unknown): value is UploadStatus {
  return isObject(value) && typeof value.upload_id === "string" && typeof value.state === "string" &&
    isObject(value.counts) && typeof value.text === "string";
}

function refusalOf(body: unknown): UploadRefusal {
  if (!isObject(body)) return { code: null, message: null, where: null, upload_id: null };
  const refusal = isObject(body.refusal) ? body.refusal : null;
  return {
    code: typeof body.code === "string" ? body.code : null,
    message: typeof body.message === "string" ? body.message : typeof body.text === "string" ? body.text : null,
    where: refusal !== null && typeof refusal.where === "string" && refusal.where ? refusal.where : null,
    upload_id: typeof body.upload_id === "string" ? body.upload_id : null,
  };
}

export function createReadingUploadClient(basePath: string = SITES_API_PATH): ReadingUploadClient {
  async function call<T>(url: string, init: RequestInit | undefined, ok: (v: unknown) => v is T): Promise<UploadResult<T>> {
    let response: Response;
    try {
      response = await fetch(url, init);
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
    if (response.status >= 500) return { status: "unavailable", message: refusalOf(body).message };
    if (response.ok) return { status: "lost" };
    return { status: "refused", refusal: refusalOf(body) };
  }

  function post<T>(siteId: string, file: File, dryRun: boolean, ok: (v: unknown) => v is T) {
    const query = new URLSearchParams({ dry_run: dryRun ? "true" : "false", file_name: file.name });
    return call(`${readingUploadsPath(siteId, basePath)}?${query.toString()}`,
      { method: "POST", body: file, headers: { "Content-Type": "text/csv" } }, ok);
  }

  return {
    async entry(siteId) {
      try {
        const response = await fetch(readingUploadsPath(siteId, basePath));
        if (!response.ok) return { status: "off" };
        const body: unknown = await response.json();
        if (isObject(body) && body.enabled === true) {
          const word = (v: unknown) => (typeof v === "string" ? v : "");
          return { status: "on", templateNote: word(body.template_note), healthText: word(body.health_text), templateStep: word(body.template_step) };
        }
      } catch {
        /* no answer: the entry stays hidden */
      }
      return { status: "off" };
    },
    check: (siteId, file) => post(siteId, file, true, isChecked),
    save: (siteId, file) => post(siteId, file, false, isStatus),
    status: (siteId, uploadId) =>
      call(`${readingUploadsPath(siteId, basePath)}/${encodeURIComponent(uploadId)}`, undefined, isStatus),
  };
}
