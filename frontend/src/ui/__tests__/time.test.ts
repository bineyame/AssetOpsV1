import { describe, expect, it } from "vitest";

import { windowText } from "../../sites/coldFormat";
import { formatDay, formatDayRange, formatDayTime, formatRange, formatTime, TIME_NOT_AVAILABLE } from "../time";

describe("time.ts (POLISH §3 Times, R650)", () => {
  it("formats a day, a day and time, and a time in UTC with no suffix", () => {
    expect(formatDay("2026-10-29T16:00:00Z")).toBe("29 Oct 2026");
    expect(formatDayTime("2026-10-29T16:00:00Z")).toBe("29 Oct 2026, 16:00");
    expect(formatTime("2026-10-29T16:00:00Z")).toBe("16:00");
    expect(formatDayTime("2026-10-29T16:00:00Z")).not.toMatch(/UTC|T16|Z$/);
  });

  it("formats a same-day range with one date and a cross-day range with both ends in full", () => {
    expect(formatRange("2026-10-29T16:00:00Z", "2026-10-29T17:05:00Z")).toBe("29 Oct 2026, 16:00–17:05");
    expect(formatRange("2026-10-29T23:00:00Z", "2026-10-30T01:00:00Z")).toBe("29 Oct 2026, 23:00 – 30 Oct 2026, 01:00");
  });

  it("formats midnight as 00:00 of its own day", () => {
    expect(formatDayTime("2026-10-30T00:00:00Z")).toBe("30 Oct 2026, 00:00");
    expect(formatRange("2026-10-29T00:00:00Z", "2026-10-30T00:00:00Z")).toBe("29 Oct 2026, 00:00 – 30 Oct 2026, 00:00");
  });

  it("gives 'Time not available yet' for invalid input and never echoes it", () => {
    for (const bad of ["not a time", "", "2026-13-45T99:00:00Z"]) {
      expect(formatDay(bad)).toBe(TIME_NOT_AVAILABLE);
      expect(formatDayTime(bad)).toBe(TIME_NOT_AVAILABLE);
      expect(formatTime(bad)).toBe(TIME_NOT_AVAILABLE);
      expect(formatRange(bad, "2026-10-29T17:05:00Z")).toBe(TIME_NOT_AVAILABLE);
    }
    expect(formatDayTime(null)).toBe("Time not available yet");
  });

  it("shows seconds and drops the year only when asked", () => {
    expect(formatDayTime("2026-11-01T02:09:11Z", { seconds: true })).toBe("1 Nov 2026, 02:09:11");
    expect(formatDayTime("2026-11-01T02:09:11Z")).toBe("1 Nov 2026, 02:09");
    expect(formatDayTime("2026-10-27T09:00:00Z", { year: false })).toBe("27 Oct, 09:00");
    expect(formatTime("2026-10-27T09:00:05Z", { seconds: true })).toBe("09:00:05");
  });

  it("truncates microsecond fractions instead of failing", () => {
    expect(formatDayTime("2026-10-29T16:00:00.123456Z")).toBe("29 Oct 2026, 16:00");
  });

  it("formats a due date in a declared Site zone and falls back to UTC otherwise (Addendum 6 Q7)", () => {
    expect(formatDay("2026-10-29T22:30:00Z", { timeZone: "Africa/Addis_Ababa" })).toBe("30 Oct 2026");
    expect(formatDay("2026-10-29T22:30:00Z", { timeZone: null })).toBe("29 Oct 2026");
    expect(formatDay("2026-10-29T22:30:00Z", { timeZone: "Not/AZone" })).toBe("29 Oct 2026");
  });

  it("formats whole-day windows by their included days (Addendum 7 Q5)", () => {
    expect(formatDayRange("2026-10-23T00:00:00Z", "2026-10-30T00:00:00Z")).toBe("23–29 Oct 2026");
    expect(formatDayRange("2026-09-28T00:00:00Z", "2026-10-05T00:00:00Z")).toBe("28 Sep – 4 Oct 2026");
    expect(formatDayRange("2026-12-28T00:00:00Z", "2027-01-04T00:00:00Z")).toBe("28 Dec 2026 – 3 Jan 2027");
    expect(formatDayRange("2026-10-29T00:00:00Z", "2026-10-30T00:00:00Z")).toBe("29 Oct 2026");
    expect(formatDayRange("2026-10-30T00:00:00Z", "2026-10-23T00:00:00Z")).toBe(TIME_NOT_AVAILABLE);
  });
});

describe("cold windowText keeps seconds like hm (review L2, Addendum 7 Q2)", () => {
  it("shows seconds only when a bound has them", () => {
    expect(windowText("2026-10-29T16:00:00Z", "2026-10-29T17:05:00Z")).toBe("29 Oct 2026, 16:00–17:05");
    expect(windowText("2026-10-29T16:00:05Z", "2026-10-29T17:05:00Z")).toBe("29 Oct 2026, 16:00:05–17:05:00");
  });
});
