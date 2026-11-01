/**
 * POLISH §3 record codes: the display form of a stored public record code, the frontend twin of
 * `backend/assetops_backend/outcomes/display_code.py`. Storage and every API `code`/`action_code` field keep the
 * zero-padded `PREFIX-NNNNNN` form; only the rendered text shows the prefix plus the number padded to at least 3
 * digits (`ACT-000001` -> `ACT-001`, `WR-000006` -> `WR-006`, `ACT-001234` -> `ACT-1234`), as the mock's `ACT-048`.
 * Any other text is returned unchanged, so a title or an absent code passes through.
 */
const RECORD_CODE = /^([A-Z][A-Z0-9]*)-([0-9]+)$/;

export function displayCode(code: string): string;
export function displayCode(code: string | null | undefined): string | null | undefined;
export function displayCode(code: string | null | undefined): string | null | undefined {
  if (code === null || code === undefined) return code;
  const m = RECORD_CODE.exec(code);
  if (m === null) return code;
  return `${m[1]}-${String(Number.parseInt(m[2], 10)).padStart(3, "0")}`;
}
