import { cleanup, render } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, describe, expect, it } from "vitest";

import { LensChips } from "../SiteFindingIndex";

afterEach(cleanup);

/*
 * RM-2 (owner-approved): the Site Findings lens chips stay only where the Site declares lens support
 * (`findings_lenses_supported`, from its configuration, never from Finding rows). Per-Site-type screens: Kobo-type keeps
 * and Kisiwa-type loses them (s404SiteFindingIndex), Cold (coldFindingIndex) and EV (evFindingIndex) never show them.
 */
describe("RM-2 lens chips", () => {
  it("the chip row itself is unchanged when drawn", () => {
    const { container } = render(<MemoryRouter><LensChips /></MemoryRouter>);
    expect(container.querySelectorAll("[data-chip-unavailable]")).toHaveLength(3);
  });
});
