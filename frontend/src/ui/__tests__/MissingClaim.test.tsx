import { render } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { isKnownGapPlacement, MissingClaim, MissingClaimSvg, UI_GAP_CATALOGUE } from "..";

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

  it("MissingClaimSvg tags an SVG text or tspan, keeps its words and attributes, and rejects unknown pairs", () => {
    const { container } = render(
      <svg role="img" aria-label="drawing">
        <MissingClaimSvg gapId="G-sld-reporting-status" placement="sld.diagram.node-slot" className="slot" x={4} y={5}>
          Readings not assessed here
        </MissingClaimSvg>
        <text>
          <MissingClaimSvg as="tspan" gapId="G-sld-reporting-status" placement="sld.diagram.bus-slot">
            Readings not assessed here
          </MissingClaimSvg>
        </text>
      </svg>,
    );
    const [text, tspan] = [...container.querySelectorAll("[data-gap-id]")];
    expect(text.localName).toBe("text");
    expect(text.namespaceURI).toBe("http://www.w3.org/2000/svg");
    expect(text.getAttribute("class")).toBe("slot");
    expect(text.getAttribute("x")).toBe("4");
    expect(text.getAttribute("data-gap-placement")).toBe("sld.diagram.node-slot");
    expect(text.textContent).toBe("Readings not assessed here");
    expect(tspan.localName).toBe("tspan");
    expect(tspan.getAttribute("data-gap-status")).toBe("open");
    const quiet = vi.spyOn(console, "error").mockImplementation(() => undefined);
    expect(() =>
      // @ts-expect-error a placement not registered for this gap is a type error
      render(<svg><MissingClaimSvg gapId="G-sld-reporting-status" placement="sld.nope">x</MissingClaimSvg></svg>),
    ).toThrow(/not a catalogued gap placement/);
    quiet.mockRestore();
  });
});
