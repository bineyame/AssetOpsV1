/** SR-4b (D-SR.4, D-SR.5; architect rev 8 §8.3): the page day and the Service/Renewable windows under a shared range. */
import { describe, expect, it } from "vitest";

import { renewableWindowFromParams, serviceWindowFromParams } from "../../sites/miniDepthClient";
import { pageDay } from "../sharedRange";

const NOW = Date.parse("2026-11-12T10:00:00Z");
const WEEK = "from=2026-11-02T00:00:00Z&to=2026-11-09T00:00:00Z"; // 2-8 Nov
const TZ = "Africa/Nairobi"; // UTC+3, the Kisiwa fixture zone

describe("SR-4b pageDay", () => {
  it("day wins, else the range's last day, else today only with no range", () => {
    expect(pageDay(new URLSearchParams(`${WEEK}&day=2026-11-04`), NOW)).toBe("2026-11-04");
    expect(pageDay(new URLSearchParams(`${WEEK}&date=2026-11-05`), NOW)).toBe("2026-11-05");
    expect(pageDay(new URLSearchParams(WEEK), NOW)).toBe("2026-11-08");
    expect(pageDay(new URLSearchParams(""), NOW)).toBe("2026-11-12");
    // An invalid range is no range: today.
    expect(pageDay(new URLSearchParams("from=2026-11-09T00:00:00Z&to=2026-11-02T00:00:00Z"), NOW)).toBe("2026-11-12");
  });
});

describe("SR-4b Service under a long range", () => {
  it("a 7-day range gives the 12:00 local hour of the range's last day", () => {
    expect(serviceWindowFromParams(new URLSearchParams(WEEK), TZ, new Date(NOW))).toEqual({
      from: "2026-11-08T09:00:00.000Z",
      to: "2026-11-08T10:00:00.000Z",
      known_at: null,
    });
  });

  it("a story one-hour window and a one-day window are unchanged", () => {
    const hour = "from=2026-10-31T09:00:00Z&to=2026-10-31T10:00:00Z";
    expect(serviceWindowFromParams(new URLSearchParams(hour), TZ, new Date(NOW))).toEqual({
      from: "2026-10-31T09:00:00Z",
      to: "2026-10-31T10:00:00Z",
      known_at: null,
    });
    const day = "from=2026-10-31T00:00:00Z&to=2026-11-01T00:00:00Z";
    expect(serviceWindowFromParams(new URLSearchParams(day), TZ, new Date(NOW)).from).toBe("2026-10-31T00:00:00Z");
  });

  it("a named day inside a long range gives that day's 12:00 local hour", () => {
    expect(serviceWindowFromParams(new URLSearchParams(`${WEEK}&day=2026-11-04`), TZ, new Date(NOW)).from).toBe("2026-11-04T09:00:00.000Z");
  });
});

describe("SR-4b Renewable under a long range", () => {
  it("a 7-day range gives its last 5 Site-local days", () => {
    expect(renewableWindowFromParams(new URLSearchParams(WEEK), TZ, new Date(NOW))).toEqual({
      from: "2026-11-03T21:00:00.000Z",
      to: "2026-11-08T21:00:00.000Z",
      known_at: null,
    });
  });

  it("a 3-day range is unchanged", () => {
    const three = "from=2026-11-06T00:00:00Z&to=2026-11-09T00:00:00Z";
    expect(renewableWindowFromParams(new URLSearchParams(`${three}&known_at=2026-11-10T00:00:00Z`), TZ, new Date(NOW))).toEqual({
      from: "2026-11-06T00:00:00Z",
      to: "2026-11-09T00:00:00Z",
      known_at: "2026-11-10T00:00:00Z",
    });
  });

  it("a named day (a story link the shell gave 7 days) reads that one Site-local day", () => {
    expect(renewableWindowFromParams(new URLSearchParams(`from=2026-10-25T00:00:00Z&to=2026-11-01T00:00:00Z&day=2026-10-31`), TZ, new Date(NOW))).toEqual({
      from: "2026-10-30T21:00:00.000Z",
      to: "2026-10-31T21:00:00.000Z",
      known_at: null,
    });
  });
});
