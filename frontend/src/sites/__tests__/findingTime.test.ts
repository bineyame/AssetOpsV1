import { describe, expect, it } from "vitest";

import { findingLocalPeriod, findingLocalTime } from "../findingTime";

describe("post-W6 W1-a: Finding local time over the canonical siteTime formatter", () => {
  it("formats Addis Ababa local time as EAT with the exact UTC instant", () => {
    expect(findingLocalTime("2026-10-15T12:00:00Z", "Africa/Addis_Ababa")).toEqual({
      day: "2026-10-15",
      dayMonth: "15 Oct",
      clock: "15:00",
      utc: "2026-10-15T12:00:00.000Z",
      zone: "EAT",
      siteZone: true,
    });
  });

  it("formats a UTC Site in UTC", () => {
    expect(findingLocalTime("2026-10-15T12:00:00Z", "Etc/UTC")).toMatchObject({ day: "2026-10-15", clock: "12:00", zone: "UTC", siteZone: true });
  });

  it("moves the local day across midnight and across a New Year boundary", () => {
    expect(findingLocalTime("2026-10-15T22:30:00Z", "Africa/Addis_Ababa")).toMatchObject({ day: "2026-10-16", dayMonth: "16 Oct", clock: "01:30" });
    expect(findingLocalTime("2026-12-31T22:30:00Z", "Africa/Addis_Ababa")).toMatchObject({ day: "2027-01-01", clock: "01:30" });
  });

  it("falls back to UTC and says so for a missing or invalid zone", () => {
    expect(findingLocalTime("2026-10-15T12:00:00Z", null)).toMatchObject({ clock: "12:00", zone: "UTC", siteZone: false });
    expect(findingLocalTime("2026-10-15T12:00:00Z", "Not/AZone")).toMatchObject({ zone: "UTC", siteZone: false });
    expect(findingLocalTime("nope", "Etc/UTC")).toBeNull();
  });

  it("writes a same-day period once and a midnight-crossing period with both days", () => {
    expect(findingLocalPeriod("2026-10-15T12:00:00Z", "2026-10-15T13:30:00Z", "Africa/Addis_Ababa")?.text).toBe("2026-10-15 15:00–16:30 EAT");
    expect(findingLocalPeriod("2026-10-15T20:00:00Z", "2026-10-15T22:30:00Z", "Africa/Addis_Ababa")?.text).toBe(
      "2026-10-15 23:00 – 2026-10-16 01:30 EAT",
    );
    expect(findingLocalPeriod("2026-10-15T20:00:00Z", "2026-10-15T22:30:00Z", "Etc/UTC")?.text).toBe("2026-10-15 20:00–22:30 UTC");
  });
});
