import { describe, expect, it } from "vitest";
import { evActionRefusal } from "../evWorkPresentation";
import { evWorkTabSearch } from "../../shell/evSiteRoutes";

describe("post-W6 W5-EV fix round: review Mediums", () => {
  it("INVALID_KNOWN_AT with no HTTP status (client refused pre-fetch) says choose a valid cutoff, no Reload", () => {
    expect(evActionRefusal({ http: null, code: "INVALID_KNOWN_AT", message: "x" })).toEqual({ message: "Choose a valid evidence cutoff.", retry: false });
    expect(evActionRefusal({ http: 422, code: "INVALID_KNOWN_AT", message: "x" }).retry).toBe(false);
    // A genuinely unreached read still offers Reload.
    expect(evActionRefusal({ http: null, code: null, message: "x" }).retry).toBe(true);
  });

  const ev = { site_type: "EV_CHARGING" };
  const KNOWN = "2026-10-06T09:00:00Z";
  it("a known_at-only address carries the valid UTC cutoff to the Work tabs", () => {
    expect(evWorkTabSearch(ev, new URLSearchParams({ known_at: KNOWN }))).toBe(`?known_at=${encodeURIComponent(KNOWN)}`);
  });
  it("a non-UTC known_at-only, one-sided and empty addresses carry nothing", () => {
    expect(evWorkTabSearch(ev, new URLSearchParams({ known_at: "yesterday" }))).toBe("");
    expect(evWorkTabSearch(ev, new URLSearchParams({ from: KNOWN, known_at: KNOWN }))).toBe("");
    expect(evWorkTabSearch(ev, new URLSearchParams())).toBe("");
    expect(evWorkTabSearch({ site_type: "COLDCHAIN" }, new URLSearchParams({ known_at: KNOWN }))).toBeUndefined();
  });
});
