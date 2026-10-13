import { render } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { isKnownGapPlacement, MissingClaim, UI_GAP_CATALOGUE } from "..";

describe("MissingClaim", () => {
  it("renders the honest copy with the gap ID and placement as metadata only", () => {
    const { container } = render(
      <MissingClaim as="p" gapId="G-readiness-gateway-firmware" placement="readiness.gateway.firmware">
        Firmware not available yet.
      </MissingClaim>,
    );
    const el = container.querySelector("p") as HTMLElement;
    expect(el.textContent).toBe("Firmware not available yet.");
    expect(el.getAttribute("data-gap-id")).toBe("G-readiness-gateway-firmware");
    expect(el.getAttribute("data-gap-placement")).toBe("readiness.gateway.firmware");
    expect(el.getAttribute("data-gap-status")).toBe("open");
  });

  it("rejects an unknown gap ID or placement at compile time and throws at runtime", () => {
    const quiet = vi.spyOn(console, "error").mockImplementation(() => undefined);
    expect(() =>
      // @ts-expect-error an uncatalogued gap ID is a type error
      render(<MissingClaim gapId="G-readiness-gateway-uptime" placement="readiness.gateway.firmware">x</MissingClaim>),
    ).toThrow(/not a catalogued gap placement/);
    expect(() =>
      // @ts-expect-error a placement not registered for this gap is a type error
      render(<MissingClaim gapId="G-readiness-gateway-firmware" placement="readiness.gateway.signal">x</MissingClaim>),
    ).toThrow(/not a catalogued gap placement/);
    quiet.mockRestore();
  });

  it("knows only catalogued gap placements, including inherited object keys", () => {
    expect(isKnownGapPlacement("G-readiness-gateway-firmware", "readiness.gateway.firmware")).toBe(true);
    expect(isKnownGapPlacement("toString", "readiness.gateway.firmware")).toBe(false);
    for (const entry of Object.values(UI_GAP_CATALOGUE)) expect(["open", "resolved_transition"]).toContain(entry.status);
  });
});
