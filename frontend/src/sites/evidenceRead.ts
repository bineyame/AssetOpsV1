/**
 * The shared read helper for the Site Evidence clients (legacy and central
 * ledger): a failure is a named state, never a thrown error, and a 409
 * `AWAITING_EVIDENCE_MIGRATION` is named as such.
 */

export type EvidenceRead<T> =
  | { status: "loaded"; value: T }
  | { status: "not_found" }
  | {
      status: "unavailable";
      message: string | null;
      /** S1-01: set when the Site's evidence is awaiting migration. */
      transition?: "AWAITING_EVIDENCE_MIGRATION";
    };

/** True when a read was refused because the Site awaits evidence migration. */
export function awaitingMigration(result: EvidenceRead<unknown> | null): boolean {
  return result !== null && result.status === "unavailable" && result.transition === "AWAITING_EVIDENCE_MIGRATION";
}

export function isObject(value: unknown): value is Record<string, unknown> {
  return value !== null && typeof value === "object" && !Array.isArray(value);
}

export function hasKeys(value: unknown, keys: readonly string[]): boolean {
  return isObject(value) && keys.every((key) => key in value);
}

export function arrayOf(value: unknown, keys: readonly string[]): boolean {
  return Array.isArray(value) && value.every((item) => hasKeys(item, keys));
}

export async function read<T>(
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
  if (response.status === 409 && isObject(detail) && detail.code === "AWAITING_EVIDENCE_MIGRATION") {
    return {
      status: "unavailable",
      message: typeof detail.message === "string" ? detail.message : null,
      transition: "AWAITING_EVIDENCE_MIGRATION",
    };
  }
  return {
    status: "unavailable",
    message:
      isObject(detail) && typeof detail.message === "string"
        ? detail.message
        : null,
  };
}

export function query(params: Record<string, string | number | null | undefined>): string {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== null && value !== undefined && value !== "") {
      search.set(key, String(value));
    }
  }
  const text = search.toString();
  return text === "" ? "" : `?${text}`;
}
