import { render } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { TechnicalDetails, WorkedOut } from "../TechnicalDetails";

const UUID = "2f50c4e6-4c4c-45be-a23b-c41ff8164bdf";

describe("POLISH §3 ids: Technical details regions", () => {
  it("is a closed disclosure named Technical details that carries data-technical-details", () => {
    const { container } = render(
      <TechnicalDetails name="t">
        <code>{UUID}</code>
      </TechnicalDetails>,
    );
    const region = container.querySelector("details[data-technical-details]");
    expect(region).not.toBeNull();
    expect(region).not.toHaveAttribute("open");
    expect(region?.querySelector("summary")?.textContent).toBe("Technical details");
    expect(region?.textContent).toContain(UUID);
  });

  it("keeps the plain lines of How this was worked out outside the region and every value inside it", () => {
    const { container } = render(
      <WorkedOut name="w" lines={<p>The reading source is active.</p>} references={[{ label: "Day assessment", value: UUID }]} />,
    );
    const outer = container.querySelector("details[data-exact-references]");
    expect(outer?.querySelector(":scope > summary")?.textContent).toBe("How this was worked out");
    expect(outer).not.toHaveAttribute("data-technical-details");
    const region = outer?.querySelector("[data-technical-details]");
    expect(region?.textContent).toContain(UUID);
    // Every id is inside the region: with it removed, no UUID is left.
    const copy = outer!.cloneNode(true) as Element;
    copy.querySelectorAll("[data-technical-details]").forEach((el) => el.remove());
    expect(copy.textContent).toContain("The reading source is active.");
    expect(copy.textContent).not.toMatch(/[0-9a-f]{8}-[0-9a-f]{4}-/);
  });

  it("PB-2 review M1: with no plain lines it is one Technical details fold, never an empty middle level", () => {
    const { container } = render(<WorkedOut name="n" variant="tech" references={[{ label: "Day assessment", value: UUID }]} />);
    const all = container.querySelectorAll("details");
    expect(all).toHaveLength(1);
    const only = all[0];
    expect(only).toHaveAttribute("data-technical-details");
    expect(only).toHaveAttribute("data-exact-references");
    expect(only).toHaveAttribute("data-disclosure", "n");
    expect(only.querySelector("summary")?.textContent).toBe("Technical details");
    expect(container.textContent).not.toContain("How this was worked out");
    expect(only.textContent).toContain(UUID);
  });

  it("renders nothing when there is nothing to show", () => {
    const { container } = render(<WorkedOut name="e" references={[]} />);
    expect(container.innerHTML).toBe("");
  });
});
