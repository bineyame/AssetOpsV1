import { describe, expect, it } from "vitest";

import { eatTime } from "../coldSiteViews";
import { siteTime, siteZoneLabel } from "../siteTime";

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
