/**
 * S4-03 fix round (Q2, review carry L3): the frontend's plain link words and
 * the backend's `finding_read.BROKEN_WORDS` are held equal, key for key and
 * word for word, so a new backend code cannot reach the screen unreviewed.
 */
import { describe, expect, it } from "vitest";

import { LINK_WORDS } from "../SiteFindingEvidence";
// The backend source, read as text by the bundler (Vite `?raw`), so both sides are compared from their own files.
import findingReadSource from "../../../../backend/assetops_backend/analytics/finding_read.py?raw";

function backendWords(): Record<string, string> {
  const source: string = findingReadSource;
  const start = source.indexOf("BROKEN_WORDS = {");
  const end = source.indexOf("\n}\n", start);
  expect(start).toBeGreaterThan(-1);
  const out: Record<string, string> = {};
  for (const m of source.slice(start, end).matchAll(/^\s+"([A-Z_]+)":\s*"([^"]*)",?\s*$/gm)) {
    out[m[1]] = m[2];
  }
  return out;
}

describe("lineage link words parity (backend BROKEN_WORDS and frontend LINK_WORDS)", () => {
  it("has the same codes and the same wording", () => {
    const backend = backendWords();
    expect(Object.keys(backend).length).toBeGreaterThan(0);
    expect(backend).toEqual(LINK_WORDS);
  });

  it("uses no engineering vocabulary in either map", () => {
    for (const text of [...Object.values(backendWords()), ...Object.values(LINK_WORDS)]) {
      expect(text).not.toMatch(/envelope|binding|mapping|cited_evidence|sha256|digest|_/i);
    }
  });
});
