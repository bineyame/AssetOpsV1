/** SR-4b (D-SR.4, D-SR.5; architect rev 8 §8.3): the page day and the Service/Renewable windows under a shared range. */
import { describe, expect, it } from "vitest";

import { renewableWindowFromParams, serviceWindowFromParams } from "../../sites/miniDepthClient";
import { pageDay } from "../sharedRange";
import contract from "../../sites/__tests__/fixtures/mini-windows-contract.json";

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

  it("a story one-hour window is unchanged; a one-day window gives that day's 12:00 local hour (D-SR.59)", () => {
    const hour = "from=2026-10-31T09:00:00Z&to=2026-10-31T10:00:00Z";
    expect(serviceWindowFromParams(new URLSearchParams(hour), TZ, new Date(NOW))).toEqual({
      from: "2026-10-31T09:00:00Z",
      to: "2026-10-31T10:00:00Z",
      known_at: null,
    });
    const day = "from=2026-10-31T00:00:00Z&to=2026-11-01T00:00:00Z";
    expect(serviceWindowFromParams(new URLSearchParams(day), TZ, new Date(NOW))).toEqual({
      from: "2026-10-31T09:00:00.000Z",
      to: "2026-10-31T10:00:00.000Z",
      known_at: null,
    });
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

  it("a 3-day range gives the Site-local days of the same dates, known_at carried (D-SR.59)", () => {
    const three = "from=2026-11-06T00:00:00Z&to=2026-11-09T00:00:00Z";
    expect(renewableWindowFromParams(new URLSearchParams(`${three}&known_at=2026-11-10T00:00:00Z`), TZ, new Date(NOW))).toEqual({
      from: "2026-11-05T21:00:00.000Z",
      to: "2026-11-08T21:00:00.000Z",
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

/**
 * D-SR.59 H-1: the checked-in contract. The client must give exactly these windows; the no-DB backend test
 * `backend/tests/test_sr4_mini_windows_contract.py` feeds the same windows to `hour_windows` and asserts none is
 * refused. A client or server change that breaks the pair fails one side. This test writes nothing.
 */
describe("D-SR.59 mini window contract (+3 and -5 zones)", () => {
  const now = new Date(contract.now);
  it("covers every bar preset, 2- and 5-day ranges, a story hour and a day-form address in both zones", () => {
    for (const zone of ["Africa/Addis_Ababa", "America/Bogota"]) {
      const labels = contract.cases.filter((c) => c.zone === zone).map((c) => c.label);
      expect(labels).toEqual(expect.arrayContaining(["preset yesterday", "preset 7d", "preset 30d", "custom 2 days", "custom 5 days", "story hour", "day form"]));
    }
  });
  for (const c of contract.cases) {
    it(`${c.zone} ${c.label}`, () => {
      const params = new URLSearchParams(c.address);
      expect(renewableWindowFromParams(params, c.zone, now)).toEqual({ ...c.renewable, known_at: null });
      expect(serviceWindowFromParams(params, c.zone, now)).toEqual({ ...c.service, known_at: null });
      const withCutoff = new URLSearchParams(`${c.address}&known_at=2026-11-12T00:00:00Z`);
      expect(renewableWindowFromParams(withCutoff, c.zone, now).known_at).toBe("2026-11-12T00:00:00Z");
      expect(serviceWindowFromParams(withCutoff, c.zone, now).known_at).toBe("2026-11-12T00:00:00Z");
    });
  }
  it("the renewable window is exact local midnights; the service window is one local clock hour", () => {
    for (const c of contract.cases) {
      const span = Date.parse(c.service.to) - Date.parse(c.service.from);
      expect(span).toBe(3_600_000);
      const days = (Date.parse(c.renewable.to) - Date.parse(c.renewable.from)) / 86_400_000;
      expect(Number.isInteger(days) && days >= 1 && days <= 5).toBe(true);
    }
  });
});
