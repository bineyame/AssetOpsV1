import { describe, expect, it } from "vitest";

import APP from "../App.tsx?raw";
import routesFixture from "../../../tools/checks/fixtures/chain_coherence/screen_routes.json";
import { featureFlagsWith } from "../config/featureFlags";
import * as labRouteModule from "../shell/simulatorLabRoutes";
import * as siteRouteModule from "../shell/operatorSiteRoutes";

/**
 * CH-0 U2: `tools/checks/fixtures/chain_coherence/screen_routes.json` is exactly the set of path patterns App
 * registers with `<Route path=...>`, minus `"*"` and the `"/"` redirect. The chain coherence check (COH-1) matches
 * every link a body carries against that list, so a route added to App without the JSON fails here.
 *
 * App's inline route arrays are not exported, so this reads App.tsx as text (Vite `?raw`): literal `path="..."`, constant
 * `path={NAME}`, the inline `[NAME, ...].map((path)` and `[[NAME, "view"], ...]` arrays behind `path={path}`, and
 * `simulatorLabRoutes(...)` (called with the Lab enabled) behind `path={route.path}`. Every `path=` attribute in
 * App must be one of those forms, so a new form fails too.
 */

const CONSTANTS: Record<string, unknown> = { ...siteRouteModule, ...labRouteModule };

function constant(name: string): string {
  const value = CONSTANTS[name];
  if (typeof value !== "string") throw new Error(`route constant ${name} is not exported as a string`);
  return value;
}

function appRoutePatterns(): string[] {
  const found = new Set<string>();
  const attributes = [...APP.matchAll(/\bpath=(\{[^}]*\}|"[^"]*")/g)].map((m) => m[1]);
  for (const attribute of attributes) {
    const literal = /^"(.*)"$/.exec(attribute);
    const named = /^\{([A-Z][A-Z0-9_]*)\}$/.exec(attribute);
    if (literal) found.add(literal[1]);
    else if (named) found.add(constant(named[1]));
    else if (attribute !== "{path}" && attribute !== "{route.path}") {
      throw new Error(`unrecognised Route path form ${attribute}`);
    }
  }
  for (const m of APP.matchAll(/\{\s*\[([A-Z0-9_,\s]+)\]\s*\.map\(\s*\(\s*path\s*\)/g)) {
    for (const name of m[1].split(",").map((x: string) => x.trim()).filter(Boolean)) found.add(constant(name));
  }
  for (const m of APP.matchAll(/\[\s*([A-Z][A-Z0-9_]*_PATH)\s*,\s*"[a-z-]+"\s*\]/g)) found.add(constant(m[1]));
  for (const route of labRouteModule.simulatorLabRoutes(featureFlagsWith(true))) found.add(route.path);
  found.delete("*");
  found.delete("/");
  return [...found].sort();
}

describe("chain coherence screen routes", () => {
  it("lists exactly the path patterns App registers", () => {
    expect(routesFixture.schema).toBe("screen-routes/1");
    expect([...routesFixture.routes].sort()).toEqual(appRoutePatterns());
    expect(new Set(routesFixture.routes).size).toBe(routesFixture.routes.length);
  });

  it("finds the dynamic routes, so the text reading is not vacuous", () => {
    const patterns = appRoutePatterns();
    expect(patterns).toContain(siteRouteModule.SITE_EV_SCENARIOS_ROUTE_PATH); // [[NAME, "view"]] array
    expect(patterns).toContain(siteRouteModule.SITE_FINDING_VIEW_ROUTE_PATH); // [NAME, NAME].map((path)
    expect(patterns).toContain(labRouteModule.EV_RUN_SETUP_PATH); // simulatorLabRoutes
    expect(patterns).toContain("/maintenance/requests/:caseId/*"); // literal
    expect(patterns).toContain(siteRouteModule.FINDINGS_OPPORTUNITIES_PATH);
  });
});
