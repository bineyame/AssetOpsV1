# P0 tests written before the source (IA-P1 handoff)

Copy each block to `frontend/src/ui/__tests__/` under the named file; they fail until the P0 source lands.

## readWindow.test.ts

```ts
/**
 * IA-P P0 (spec-period.md P.9, D-IAP.24): the read window. It keeps `to` and `known_at` and sets `from` to
 * max(from, to - 30 days), so a capped read sees at most the last 31 days of the range. Expected days are literals.
 */
import { describe, expect, it } from "vitest";

import { RANGE_MAX_DAYS, readSharedRange, readWindow, windowBound } from "../sharedRange";

const q = (s: string) => new URLSearchParams(s);
const NOW = Date.parse("2026-11-22T00:00:00Z");

describe("readWindow (P.9)", () => {
  it("equals the range at 7 and 31 days", () => {
    expect(readWindow(q("from=2026-10-01&to=2026-10-07"), NOW)).toEqual({ from: "2026-10-01", to: "2026-10-07", known_at: null });
    expect(readWindow(q("from=2026-10-01&to=2026-10-31"), NOW)).toEqual({ from: "2026-10-01", to: "2026-10-31", known_at: null });
  });

  it("is the last 31 days at 32 and 731 days", () => {
    expect(readWindow(q("from=2026-09-30&to=2026-10-31"), NOW)).toEqual({ from: "2026-10-01", to: "2026-10-31", known_at: null });
    expect(readWindow(q("from=2024-11-01&to=2026-10-31"), NOW)).toEqual({ from: "2026-10-01", to: "2026-10-31", known_at: null });
  });

  it("reads the instant form and keeps known_at", () => {
    const known = "2026-11-01T00:00:00Z";
    expect(
      readWindow(q(`from=2026-09-01T00:00:00Z&to=2026-11-01T00:00:00Z&known_at=${encodeURIComponent(known)}`), NOW),
    ).toEqual({ from: "2026-10-01", to: "2026-10-31", known_at: known });
  });

  it("731 days is the cap: 732 days is invalid", () => {
    expect(RANGE_MAX_DAYS).toBe(731);
    expect(readSharedRange(q("from=2024-11-01&to=2026-10-31"), NOW).status).toBe("set");
    expect(readSharedRange(q("from=2024-10-31&to=2026-10-31"), NOW).status).toBe("invalid");
    expect(readWindow(q("from=2024-10-31&to=2026-10-31"), NOW)).toBeNull();
  });

  it("windowBound keeps the address form, and the raw value within 31 days", () => {
    expect(windowBound(q("from=2026-09-01&to=2026-10-31"), "from")).toBe("2026-10-01");
    expect(windowBound(q("from=2026-09-01&to=2026-10-31"), "to")).toBe("2026-10-31");
    expect(windowBound(q("from=2026-09-01T00:00:00Z&to=2026-11-01T00:00:00Z"), "from")).toBe("2026-10-01T00:00:00Z");
    expect(windowBound(q("from=2026-10-25T00:00:00Z&to=2026-11-01T00:00:00Z"), "from")).toBe("2026-10-25T00:00:00Z");
    expect(windowBound(q("from=garbage&to=2026-11-01"), "from")).toBe("garbage");
    expect(windowBound(q(""), "from")).toBeNull();
  });
});
```

## noRawRangeReads.test.ts

```ts
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

const RAW = /\bget\(\s*(["'])(from|to)\1\s*\)/;

describe("no raw range reads (P.9)", () => {
  it("scans a non-empty source tree", () => {
    expect(Object.keys(SOURCES).length).toBeGreaterThan(300);
  });

  it("reads from/to only in sharedRange.ts", () => {
    const hits: string[] = [];
    for (const [file, text] of Object.entries(SOURCES)) {
      if (/__tests__\/|\.test\.tsx?$|\/test\/|ui\/sharedRange\.ts$/.test(file)) continue;
      text.split("\n").forEach((line, i) => {
        if (RAW.test(line)) hits.push(`${file}:${i + 1}: ${line.trim()}`);
      });
    }
    expect(hits).toEqual([]);
  });
});
```
