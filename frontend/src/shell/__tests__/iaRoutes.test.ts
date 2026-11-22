/**
 * IA-P P1 (spec §5.1, §6 P1): the route registry. `railHomeOf` for one path per spec §2.4 family, the landed filter of
 * `LEGACY_ROUTES` and the search merge. Expected values are spec §2.1/§2.4 literals, not read from the module.
 */
import { describe, expect, it } from "vitest";

import { IA_LANDED, LEGACY_ROUTES, liveLegacyRoutes, mergeLegacySearch, railHomeOf } from "../iaRoutes";

describe("railHomeOf (spec §2.4)", () => {
  it.each([
    ["/portfolio", "Portfolio"],
    ["/portfolio/outcomes", "Portfolio"],
    ["/portfolio/month", "Portfolio"],
    ["/sites", "Sites"],
    ["/sites/KOBO-001", "Sites"],
    ["/sites/KOBO-001/performance/renewable", "Sites"],
    ["/sites/KOBO-001/findings", "Sites"],
    ["/sites/KOBO-001/findings/F-1", "Findings"],
    ["/sites/KOBO-001/findings/F-1/recommendation", "Findings"],
    ["/sites/KOBO-001/actions/A-1", "Actions"],
    ["/sites/KOBO-001/actions/A-1/verification", "Actions"],
    ["/findings", "Findings"],
    ["/findings/KOBO-001/ASM-1/evidence", "Findings"],
    ["/actions", "Actions"],
    ["/incidents", "Incidents"],
    ["/maintenance", "Maintenance"],
    ["/maintenance/preventive", "Maintenance"],
    ["/maintenance/requests/C-1/record", "Maintenance"],
    ["/evidence", "Evidence & records"],
    ["/evidence/records", "Evidence & records"],
    ["/financials", "Financials"],
  ])("%s lights %s", (path, home) => {
    expect(railHomeOf(path)).toBe(home);
  });

  it("an address outside every family lights nothing", () => {
    expect(railHomeOf("/nowhere")).toBeNull();
    expect(railHomeOf("/simulator-lab")).toBeNull();
  });
});

describe("LEGACY_ROUTES (spec §2.4)", () => {
  it("only landed units' aliases are live", () => {
    expect(IA_LANDED.has("IA-P1")).toBe(true);
    const none = liveLegacyRoutes(new Set());
    expect(none).toEqual([]);
    const p1 = liveLegacyRoutes(new Set(["IA-P1"])).map((r) => [r.from, r.to]);
    expect(p1).toEqual(expect.arrayContaining([["/", "/portfolio"], ["/operational-records", "/evidence/records"]]));
    for (const route of LEGACY_ROUTES.filter((r) => r.unit !== "IA-P1")) {
      expect(liveLegacyRoutes(new Set(["IA-P1"]))).not.toContain(route);
    }
  });

  it("merges the search: the target's own query first, then the original's unset parameters", () => {
    const original = new URLSearchParams("from=2026-10-01&to=2026-10-31&lens=risks&kind=OPERATOR_LOG");
    expect(mergeLegacySearch("/evidence/records", original)).toBe(
      "/evidence/records?from=2026-10-01&to=2026-10-31&lens=risks&kind=OPERATOR_LOG",
    );
    expect(mergeLegacySearch("/findings?lens=cost", original)).toBe(
      "/findings?lens=cost&from=2026-10-01&to=2026-10-31&kind=OPERATOR_LOG",
    );
    expect(mergeLegacySearch("/portfolio", new URLSearchParams())).toBe("/portfolio");
  });
});
