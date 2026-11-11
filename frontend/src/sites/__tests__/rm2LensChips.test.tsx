import { cleanup, render } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, describe, expect, it } from "vitest";

import { LensChips } from "../SiteFindingIndex";

afterEach(cleanup);

/*
 * RM-2 (owner-approved): the Site Findings lens chips are hidden where no lens is supported. The per-Site-type
 * screens (cold, EV, mini-grid) are asserted in coldFindingIndex, evFindingIndex, w301EstateShellRoutes and
 * s404SiteFindingIndex; this is the component rule itself, including that a supplied lens brings the row back.
 */
describe("RM-2 LensChips", () => {
  it("draws nothing when no lens has a destination", () => {
    const { container } = render(<MemoryRouter><LensChips /></MemoryRouter>);
    expect(container.innerHTML).toBe("");
  });

  it("draws the row (All plus a live lens, the rest still unbuilt) when a Site supports one", () => {
    const { container } = render(<MemoryRouter><LensChips hrefs={{ Cost: "/x" }} /></MemoryRouter>);
    expect(container.querySelector("[data-site-findings-lenses]")).not.toBeNull();
    expect(container.querySelector("[data-lens='cost'] a")?.getAttribute("href")).toBe("/x");
    expect(container.querySelectorAll("[data-chip-unavailable]")).toHaveLength(2);
  });
});
