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
    expect(readSharedRange(q("from=2024-10-31&to=2026-10-31"), NOW).status).toBe("set");
    expect(readSharedRange(q("from=2024-10-30&to=2026-10-31"), NOW).status).toBe("invalid");
    expect(readWindow(q("from=2024-10-30&to=2026-10-31"), NOW)).toBeNull();
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
