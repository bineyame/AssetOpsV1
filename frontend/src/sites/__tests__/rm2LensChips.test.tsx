import { cleanup, render } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, describe, expect, it } from "vitest";

import { LensChips, siteSupportsLenses } from "../SiteFindingIndex";

afterEach(cleanup);

/*
 * RM-2 (owner-approved): the Site Findings lens chips stay only where the Site's own Findings read classifies a
 * Finding under a lens. Per-Site-type screens: Kobo-type keeps and Kisiwa-type loses them (s404SiteFindingIndex),
 * Cold (coldFindingIndex) and EV (evFindingIndex) never show them.
 */
describe("RM-2 lens support is derived from the Findings read", () => {
  it("is true only when some row carries a lens flag", () => {
    expect(siteSupportsLenses([])).toBe(false);
    expect(siteSupportsLenses([{}, { lens_flags: [] }])).toBe(false);
    expect(siteSupportsLenses([{ lens_flags: [] }, { lens_flags: ["COST"] }])).toBe(true);
  });
  it("the chip row itself is unchanged when drawn", () => {
    const { container } = render(<MemoryRouter><LensChips /></MemoryRouter>);
    expect(container.querySelectorAll("[data-chip-unavailable]")).toHaveLength(3);
  });
});
