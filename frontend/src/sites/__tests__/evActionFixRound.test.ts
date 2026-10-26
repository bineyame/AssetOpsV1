import { describe, expect, it } from "vitest";
import { coldActionRefusal } from "../coldWorkPresentation";
import { evActionRefusal } from "../evWorkPresentation";
import { coldTabSearch } from "../../shell/coldSiteRoutes";
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

describe("post-W6 final-fix L5: coldTabSearch applies the valid-window gate", () => {
  const cold = { site_type: "COLDCHAIN" };
  const FROM = "2026-10-06T00:00:00Z";
  const TO = "2026-10-07T00:00:00Z";
  const K = "2026-10-06T09:00:00Z";
  const q = (o: Record<string, string>) => new URLSearchParams(o);
  it("passes a complete, ordered window of at most 31 days with a valid cutoff", () => {
    expect(coldTabSearch(cold, q({ from: FROM, to: TO, known_at: K }))).toBe(`?from=${encodeURIComponent(FROM)}&to=${encodeURIComponent(TO)}&known_at=${encodeURIComponent(K)}`);
  });
  it.each([
    ["one-sided", q({ from: FROM, known_at: K })],
    ["reversed", q({ from: TO, to: FROM, known_at: K })],
    ["over 31 days", q({ from: "2026-09-01T00:00:00Z", to: "2026-10-03T00:00:00Z", known_at: K })],
  ])("drops a %s window but keeps the valid cutoff", (_n, params) => {
    expect(coldTabSearch(cold, params)).toBe(`?known_at=${encodeURIComponent(K)}`);
  });
  it("drops an invalid cutoff and a non-cold Site gets undefined", () => {
    expect(coldTabSearch(cold, q({ known_at: "yesterday" }))).toBe("");
    expect(coldTabSearch({ site_type: "MINIGRID" }, q({ from: FROM, to: TO }))).toBeUndefined();
  });
  it("M2 cold refusal map mirrors EV", () => {
    expect(coldActionRefusal({ http: 409, code: "DOMAIN_INTENT_BASIS_CHANGED", message: "x" })).toEqual({ message: "The Action changed while it was being read.", retry: true });
    expect(coldActionRefusal({ http: 403, code: "SITE_SCOPE_FORBIDDEN", message: "x" })).toEqual({ message: "You do not have access to this site.", retry: false });
    expect(coldActionRefusal({ http: null, code: null, message: "x" }).retry).toBe(true);
    expect(coldActionRefusal({ http: 500, code: "X", message: "x" })).toEqual({ message: "The Action could not be read.", retry: false });
  });
});
