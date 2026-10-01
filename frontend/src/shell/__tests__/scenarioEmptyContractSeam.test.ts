import { describe, expect, it } from "vitest";

import fixture from "../../../../contract-fixtures/scenario-empty-site-contract.json";
import { isScenarioSummary } from "../scenarioCatalogClient";

// The fixture is the backend's own summary for a document carrying
// `site_contract: {}`, written by test_run_binds_scenario_to_site.py. One such
// row must not make the whole catalog unreadable.
describe("an empty site_contract block, as the backend serialises it", () => {
  it("is a valid scenario summary", () => {
    expect(isScenarioSummary(fixture)).toBe(true);
  });

  it("is not a vacuous check: a null description is still refused", () => {
    expect(
      isScenarioSummary({ ...fixture, site_contract: { description: null } }),
    ).toBe(false);
  });
});
