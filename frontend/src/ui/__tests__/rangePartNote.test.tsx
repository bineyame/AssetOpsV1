/** IA-P P0: the part note renders only when the window differs from the range, in the bar's words. */
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { RangePartNote } from "../RangePartNote";

describe("RangePartNote (P.9)", () => {
  it("says the window of a 61-day range", () => {
    render(<RangePartNote range={{ from: "2026-09-01", to: "2026-10-31" }} />);
    expect(screen.getByRole("note").textContent).toBe("Showing 1–31 Oct of the range");
  });
  it("renders nothing for 31 days or fewer, or no range", () => {
    const { container, rerender } = render(<RangePartNote range={{ from: "2026-10-01", to: "2026-10-31" }} />);
    expect(container.textContent).toBe("");
    rerender(<RangePartNote range={null} />);
    expect(container.textContent).toBe("");
  });
});
