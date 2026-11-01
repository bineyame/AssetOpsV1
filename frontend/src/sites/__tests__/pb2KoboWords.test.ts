import { describe, expect, it } from "vitest";

import { roleWords } from "../dispatchWords";
import { episodeRange } from "../OverviewFindingList";
import { accessWords } from "../SiteWindowOverview";
import { LIFECYCLE_WORDS } from "../findingWords";

describe("POLISH PB-2 Kobo words", () => {
  it("names the essential-service power inputs (Addendum 8 Q2) and capitalises an unmapped role", () => {
    expect(roleWords("critical_load_delivered_power")).toBe("Essential services: power supplied");
    expect(roleWords("critical_load_requested_power")).toBe("Essential services: power requested");
    expect(roleWords("some_new_role")).toBe("Some new role");
  });

  it("writes a Finding's episode as a short same-day range, and an open one without an end", () => {
    expect(episodeRange("2026-10-29T04:35:00Z", "2026-10-29T07:55:00Z")).toBe("29 Oct, 04:35–07:55");
    expect(episodeRange("2026-10-29T04:35:00Z", null)).toBe("from 29 Oct, 04:35, no end time yet");
  });

  it("states the access basis in words, never its code", () => {
    expect(accessWords("DEVELOPMENT_TENANT_OPERATOR_CONTEXT: no authenticated human principal exists yet")).toBe(
      "Access: operator account",
    );
    expect(accessWords(null)).toBe("Access: not recorded");
  });

  it("uses the Addendum 4 Finding titles, with no run/ran/running", () => {
    expect(LIFECYCLE_WORDS.SUPPORTED.title).toBe("Generator may have been on longer than needed");
    expect(LIFECYCLE_WORDS.UNCONFIRMED.title).toBe("Extra generator time not confirmed by the latest check");
    expect(LIFECYCLE_WORDS.NO_LONGER_SUPPORTED.title).toBe("Extra generator time no longer supported by the latest check");
    for (const w of Object.values(LIFECYCLE_WORDS)) expect(w.title).not.toMatch(/\b(run|ran|running)\b/i);
  });
});
