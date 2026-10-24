import { describe, expect, it } from "vitest";

import { measuredTime, selectedLocalDay, usableZone, zoneAbbreviation } from "../LedgerSiteEvidence";

/* post-W6 shell R170 (Q18): the evidence-analysis measured time on the Site's clock, UTC when unknown. */
describe("evidence measured time", () => {
  it("names East Africa Time for Addis Ababa and UTC for UTC", () => {
    expect(zoneAbbreviation("Africa/Addis_Ababa")).toBe("EAT");
    expect(zoneAbbreviation("UTC")).toBe("UTC");
  });

  it("falls back to UTC when the timezone is missing or unknown", () => {
    for (const zone of [null, undefined, "", "Not/AZone"]) {
      expect(usableZone(zone)).toBeNull();
      expect(zoneAbbreviation(zone)).toBe("UTC");
    }
    expect(measuredTime("2026-10-13T11:20:00Z", null, "2026-10-13")).toBe("11:20:00");
  });

  it("shows the local HH:MM:SS on the selected day and adds the local date only when it differs", () => {
    const day = selectedLocalDay("2026-10-12T21:00:00Z", "Africa/Addis_Ababa");
    expect(day).toBe("2026-10-13");
    expect(measuredTime("2026-10-13T11:20:05Z", "Africa/Addis_Ababa", day)).toBe("14:20:05");
    // 22:30Z on 13 Oct is 01:30 on 14 Oct in Addis: a different local day, so the date is shown.
    expect(measuredTime("2026-10-13T22:30:00Z", "Africa/Addis_Ababa", day)).toBe("14 Oct · 01:30:00");
    // The same instant in UTC stays on 13 Oct.
    expect(measuredTime("2026-10-13T22:30:00Z", "UTC", selectedLocalDay("2026-10-13T00:00:00Z", "UTC"))).toBe("22:30:00");
  });

  it("says none for a missing instant and keeps an unreadable one verbatim", () => {
    expect(measuredTime(null, "Africa/Addis_Ababa", null)).toBe("none");
    expect(measuredTime("not-a-time", "Africa/Addis_Ababa", null)).toBe("not-a-time");
  });
});
