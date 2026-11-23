/**
 * Test-only: rail links on a range page. `/sites` fills its range on entry (IA-P P4b, spec §6 "Range pages"), and the
 * rail keeps the address range on every link (SR-1), so a rail test mounted at `/sites` reads each link's path and
 * checks that every link carries the one address range.
 */
import { expect } from "vitest";

export const hrefPath = (href: string | null): string => (href ?? "").split("?")[0];

/** Every href carries the same non-empty `from`/`to` query; returns the paths in order. */
export function pathsWithOneRange(hrefs: readonly (string | null)[]): string[] {
  const queries = new Set(hrefs.map((h) => (h ?? "").split("?")[1] ?? ""));
  expect(queries.size).toBe(1);
  expect([...queries][0]).toMatch(/^from=[^&]+&to=[^&]+$/);
  return hrefs.map(hrefPath);
}
