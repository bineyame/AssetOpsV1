import { describe, expect, it } from "vitest";

import { eatTime } from "../coldSiteViews";
import { nextIsoDate, siteLocalEndUtc, siteLocalLastDay, siteSevenDayWindow, siteTime, siteZoneDisplayLabel, siteZoneLabel } from "../siteTime";

describe("post-W6 W2-EV: shared Site-timezone formatter", () => {
  it("formats Addis Ababa local time with seconds, the EAT label and exact UTC", () => {
    expect(siteTime("2026-10-24T13:08:42Z", "Africa/Addis_Ababa")).toEqual({ text: "16:08:42", utc: "2026-10-24T13:08:42.000Z", zone: "EAT", siteZone: true });
  });

  it.each(["Africa/Asmara", "Africa/Djibouti", "Africa/Mogadishu"])("W1-a closeout ruling 5: %s is EAT in the canonical table", (zone) => {
    expect(siteTime("2026-10-24T13:08:42Z", zone)).toEqual({ text: "16:08:42", utc: "2026-10-24T13:08:42.000Z", zone: "EAT", siteZone: true });
    expect(siteZoneLabel(zone)).toBe("EAT");
  });

  it("formats a UTC Site in UTC", () => {
    expect(siteTime("2026-10-24T13:08:42Z", "Etc/UTC")?.text).toBe("13:08:42");
    expect(siteZoneLabel("Etc/UTC")).toBe("UTC");
  });

  it("prefixes the local date when the local day differs from the reference (midnight crossing)", () => {
    // 22:30Z is 01:30 the next day in Addis; the reference 20:00Z is still 24 Oct locally.
    expect(siteTime("2026-10-24T22:30:05Z", "Africa/Addis_Ababa", "2026-10-24T20:00:00Z")?.text).toBe("25 Oct 01:30:05");
    expect(siteTime("2026-10-24T22:30:05Z", "Etc/UTC", "2026-10-24T20:00:00Z")?.text).toBe("22:30:05");
  });

  it("falls back to UTC, and says so, when the timezone is missing or invalid", () => {
    expect(siteTime("2026-10-24T13:08:42Z", null)).toMatchObject({ text: "13:08:42", zone: "UTC", siteZone: false });
    expect(siteTime("2026-10-24T13:08:42Z", "Not/AZone")).toMatchObject({ text: "13:08:42", zone: "UTC", siteZone: false });
    expect(siteZoneLabel(undefined)).toBe("UTC");
  });

  it("returns null for a missing instant", () => {
    expect(siteTime(null, "Etc/UTC")).toBeNull();
    expect(siteTime("not a time", "Etc/UTC")).toBeNull();
  });

  it("keeps eatTime's earlier default and accepts a Site timezone", () => {
    expect(eatTime("2026-10-24T13:08:42Z")).toBe("16:08:42");
    expect(eatTime("2026-10-24T13:08:42Z", "Etc/UTC")).toBe("13:08:42");
    expect(eatTime(null)).toBeNull();
  });
});

describe("post-W6 W4 build ruling 7: inclusive Site-local end dates over a half-open UTC bound", () => {
  it("an included last day becomes the next Site-local midnight, across month end", () => {
    expect(siteLocalEndUtc("2026-10-31", "Africa/Addis_Ababa")).toBe("2026-10-31T21:00:00Z");
    expect(siteLocalEndUtc("2026-12-31", null)).toBe("2027-01-01T00:00:00Z");
    expect(nextIsoDate("2026-02-28")).toBe("2026-03-01");
    expect(siteLocalEndUtc("not-a-date", "Africa/Addis_Ababa")).toBe("");
  });

  it("a clock change: the next local midnight keeps the offset in force at that midnight", () => {
    // Europe/London leaves BST (UTC+1) at 01:00Z on 25 Oct 2026.
    expect(siteLocalEndUtc("2026-10-24", "Europe/London")).toBe("2026-10-24T23:00:00Z");
    expect(siteLocalEndUtc("2026-10-25", "Europe/London")).toBe("2026-10-26T00:00:00Z");
  });

  it("an exclusive bound shows its preceding Site-local date", () => {
    expect(siteLocalLastDay("2026-10-31T21:00:00Z", "Africa/Addis_Ababa")).toBe("2026-10-31");
    expect(siteLocalLastDay("2026-10-26T00:00:00Z", "Europe/London")).toBe("2026-10-25");
    expect(siteLocalLastDay("bad", null)).toBe("");
  });
});

describe("post-W6 final-fix M1: the mini Site Work seven-Site-local-day default", () => {
  it("EAT near midnight: 22:30Z on the 26th is the 27th at the Site, so the window ends 28 Oct 00:00 EAT", () => {
    expect(siteSevenDayWindow("Africa/Addis_Ababa", new Date("2026-10-26T22:30:00Z"))).toEqual({ from: "2026-10-20T21:00:00Z", to: "2026-10-27T21:00:00Z" });
  });

  it("EAT just before local midnight stays on the same Site day", () => {
    expect(siteSevenDayWindow("Africa/Addis_Ababa", new Date("2026-10-26T20:59:59Z"))).toEqual({ from: "2026-10-19T21:00:00Z", to: "2026-10-26T21:00:00Z" });
  });

  it("falls back to UTC days for a missing or invalid zone", () => {
    const utc = { from: "2026-10-20T00:00:00Z", to: "2026-10-27T00:00:00Z" };
    expect(siteSevenDayWindow(null, new Date("2026-10-26T22:30:00Z"))).toEqual(utc);
    expect(siteSevenDayWindow("Not/AZone", new Date("2026-10-26T22:30:00Z"))).toEqual(utc);
  });

  it("a clock-change zone keeps local midnights: New York leaves daylight time on 1 Nov 2026", () => {
    // 3 Nov: six days back is 28 Oct (EDT, UTC-4); tomorrow 4 Nov 00:00 is EST (UTC-5). The window is 7 local days, 169 hours.
    const w = siteSevenDayWindow("America/New_York", new Date("2026-11-03T15:00:00Z"));
    expect(w).toEqual({ from: "2026-10-28T04:00:00Z", to: "2026-11-04T05:00:00Z" });
    expect((new Date(w.to).getTime() - new Date(w.from).getTime()) / 3_600_000).toBe(169);
  });

  it("names an unavailable Site zone in full for display, and keeps the short label for valid zones", () => {
    expect(siteZoneDisplayLabel(null)).toBe("UTC (Site time zone unavailable)");
    expect(siteZoneDisplayLabel("Not/AZone")).toBe("UTC (Site time zone unavailable)");
    expect(siteZoneDisplayLabel("Etc/UTC")).toBe("UTC");
    expect(siteZoneDisplayLabel("Africa/Addis_Ababa")).toBe("EAT");
  });
});
