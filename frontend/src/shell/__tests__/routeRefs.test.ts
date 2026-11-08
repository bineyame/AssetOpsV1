import { describe, expect, it } from "vitest";
import rows from "../__fixtures__/route-refs.json";
import { REF_ESTATE_VIEWS, REF_SITE_VIEWS, linkFor, routeFor, type Ref } from "../operatorSiteRoutes";

type Row = { name: string; ref: Ref; path: string | null };
const fixture = rows as unknown as Row[];

describe("routeFor (CH-5a2a B1)", () => {
  it.each(fixture.map((row) => [row.name, row] as const))("%s matches the shared fixture", (_name, row) => {
    expect(routeFor(row.ref)).toBe(row.path);
  });

  it("has a fixture row for every kind and enumerated view", () => {
    const kinds = new Set(fixture.map((row) => row.ref.kind));
    expect([...kinds].sort()).toEqual(["ACTION", "CASE", "DOMAIN_VERDICT", "ESTATE", "EVIDENCE", "FINDING", "FUEL_FINDING", "OPPORTUNITY", "SITE", "THREAD"]);
    const siteViews = new Set(fixture.flatMap((row) => (row.ref.kind === "SITE" ? [row.ref.view ?? "home"] : [])));
    expect([...siteViews].sort()).toEqual([...REF_SITE_VIEWS].sort());
    const estateViews = new Set(fixture.flatMap((row) => (row.ref.kind === "ESTATE" ? [row.ref.view] : [])));
    expect([...estateViews].sort()).toEqual([...REF_ESTATE_VIEWS].sort());
  });

  it("never produces an /api path", () => {
    for (const row of fixture) expect(routeFor(row.ref) ?? "").not.toMatch(/^\/api/);
  });

  it("renders no link without a ref", () => {
    expect(linkFor(undefined)).toBeNull();
    expect(linkFor(null)).toBeNull();
  });

  it("routes a FUEL_FINDING ref to the fuel Finding page (DIESEL-K5 F7)", () => {
    expect(routeFor({ kind: "FUEL_FINDING", site: "KISIWA-001", id: "f-1" })).toBe("/sites/KISIWA-001/fuel-findings/f-1");
    expect(routeFor({ kind: "FUEL_FINDING", site: "KISIWA 1", id: "f/1", revision: "r 2" })).toBe(
      "/sites/KISIWA%201/fuel-findings/f%2F1?revision_id=r%202",
    );
  });
});
