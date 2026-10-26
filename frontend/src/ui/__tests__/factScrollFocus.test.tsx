import { cleanup, render } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import { Fact, FactList } from "../DataTable";

const NODE_FS = (await import(/* @vite-ignore */ `node:${"fs"}`)) as { readFileSync: (p: string, e: string) => string };
const CWD = (globalThis as unknown as { process: { cwd: () => string } }).process.cwd();
const LONG = "SES-EV-9ADA0E5946202A82E53C-CONNECTOR-0001-ABORT";

/** jsdom has no layout: give the value box a scroll width and, as a page rule would, its own scroll region. */
function scroller(dd: HTMLElement, scroll: number, client: number, overflowX: string) {
  dd.style.overflowX = overflowX;
  Object.defineProperty(dd, "scrollWidth", { configurable: true, value: scroll });
  Object.defineProperty(dd, "clientWidth", { configurable: true, value: client });
}

const view = () => (
  <FactList>
    <Fact term="Session">
      <code>{LONG}</code>
    </Fact>
  </FactList>
);

afterEach(cleanup);

describe("recapture fix F4 (B13-18): a scrolling fact value is keyboard reachable", () => {
  it("is a focusable group named by its full value once it scrolls, and is released when it fits", () => {
    const r = render(view());
    const dd = r.container.querySelector("dd") as HTMLElement;
    scroller(dd, 400, 120, "auto");
    r.rerender(view());
    expect(dd.getAttribute("tabindex")).toBe("0");
    expect(dd.getAttribute("role")).toBe("group");
    expect(dd.getAttribute("aria-label")).toBe(`Full value: ${LONG}`);
    scroller(dd, 100, 120, "auto");
    r.rerender(view());
    expect(dd.hasAttribute("tabindex")).toBe(false);
    expect(dd.hasAttribute("aria-label")).toBe(false);
  });

  it("stays out of the tab order when it does not scroll (no scroll region, or it fits)", () => {
    const r = render(view());
    const dd = r.container.querySelector("dd") as HTMLElement;
    scroller(dd, 400, 120, "visible");
    r.rerender(view());
    expect(dd.hasAttribute("tabindex")).toBe(false);
    const fits = render(
      <FactList>
        <Fact term="Session">KOBO-001</Fact>
      </FactList>,
    );
    expect(fits.container.querySelector("dd")?.hasAttribute("tabindex")).toBe(false);
  });

  it("declares a visible focus ring for the scrolling value", () => {
    const css = NODE_FS.readFileSync(`${CWD}/src/ui/primitives.css`, "utf8");
    expect(css).toMatch(/\.fact-list__value\[data-scroll-focus\]:focus-visible \{[^}]*outline: 2px solid/s);
  });
});
