/// <reference types="vite/client" />
/**
 * IA-P P0 (spec-period.md P.9, D-IAP.24): a static scan of `frontend/src` (tests excluded). Every read of the range
 * goes through `sharedRange.ts` (`readWindow`, `windowBound`), so a raw `get("from")` or `get("to")` anywhere else
 * fails: it would send the whole range to a read capped at 31 days.
 */
import { describe, expect, it } from "vitest";

const SOURCES = import.meta.glob(["../../**/*.ts", "../../**/*.tsx"], { query: "?raw", import: "default", eager: true }) as Record<
  string,
  string
>;

const RAW = /\bget(?:All)?\(\s*(["'])(from|to)\1\s*\)/;

describe("no raw range reads (P.9)", () => {
  it("scans a non-empty source tree", () => {
    expect(Object.keys(SOURCES).length).toBeGreaterThan(300);
  });

  it("reads from/to only in sharedRange.ts", () => {
    const hits: string[] = [];
    for (const [file, text] of Object.entries(SOURCES)) {
      if (/__tests__\/|\.test\.tsx?$|\/test\/|\/sharedRange\.ts$/.test(file)) continue;
      text.split("\n").forEach((line, i) => {
        if (RAW.test(line)) hits.push(`${file}:${i + 1}: ${line.trim()}`);
      });
    }
    expect(hits).toEqual([]);
  });
});
