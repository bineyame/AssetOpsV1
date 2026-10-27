import { render } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { ClaimLabel } from "../ClaimLabel";
import { BENEFICIARY_WORDS, CLAIM_LABEL } from "../actionPresentation";

describe("CC-R1 ClaimLabel", () => {
  it("states the claim level and who benefits, with data attributes", () => {
    const { container } = render(<ClaimLabel level="MODELLED_OPPORTUNITY" beneficiary="MINI_OPERATOR" />);
    const p = container.querySelector("p.claim-label");
    expect(p).toHaveAttribute("data-claim-level", "MODELLED_OPPORTUNITY");
    expect(p).toHaveAttribute("data-beneficiary", "MINI_OPERATOR");
    expect(p?.textContent).toBe("Modelled opportunity · declared assumptions · benefits: mini-grid operator");
  });

  it.each([
    ["NOT_A_LEVEL", "MINI_OPERATOR"],
    ["MODELLED_OPPORTUNITY", "NOBODY"],
    ["toString", "MINI_OPERATOR"],
    ["", ""],
  ])("says the claim is not stated for %s / %s and never throws", (level, beneficiary) => {
    const { container } = render(<ClaimLabel level={level} beneficiary={beneficiary} />);
    expect(container.querySelector(".claim-label")?.textContent).toBe("Claim not stated");
  });

  it("has all five levels and five beneficiaries", () => {
    expect(Object.keys(CLAIM_LABEL)).toHaveLength(5);
    expect(Object.keys(BENEFICIARY_WORDS)).toEqual([
      "MINI_OPERATOR",
      "GOODS_OWNER",
      "FLEET_OPERATOR",
      "CHARGING_SERVICE",
      "COOLING_PROVIDER",
    ]);
  });

  it("the labels rendered this sprint never say saving or saved", () => {
    for (const level of ["MODELLED_OPPORTUNITY", "VERIFIED_SIMULATED_TECHNICAL"]) {
      for (const beneficiary of Object.keys(BENEFICIARY_WORDS)) {
        const { container, unmount } = render(<ClaimLabel level={level} beneficiary={beneficiary} />);
        expect(container.textContent).not.toMatch(/saving|saved/i);
        unmount();
      }
    }
  });
});
