import { cleanup, render } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import { KeyValues } from "../V69Layout";

const NODE_FS = (await import(/* @vite-ignore */ `node:${"fs"}`)) as { readFileSync: (p: string, e: string) => string };
const CWD = (globalThis as unknown as { process: { cwd: () => string } }).process.cwd();

/** jsdom has no layout; report a code box as wider than its visible width. */
function overflow(code: HTMLElement, scroll: number, client: number) {
  Object.defineProperty(code, "scrollWidth", { configurable: true, value: scroll });
  Object.defineProperty(code, "clientWidth", { configurable: true, value: client });
}

afterEach(cleanup);

describe("post-W6 final-fix L11: an overflowing key-value code is keyboard reachable", () => {
  const LONG = "KOBO-001-GENERATOR-SUPPORT-FINDING-REVISION-0007";

  it("is focusable, named by its full value, once it overflows", async () => {
    const view = render(<KeyValues label="Facts" rows={[["Code", <code key="c">{LONG}</code>, "code"]]} />);
    const code = view.container.querySelector("code") as HTMLElement;
    overflow(code, 400, 120);
    // A re-render re-measures (the same pass a resize observer triggers).
    view.rerender(<KeyValues label="Facts" rows={[["Code", <code key="c">{LONG}</code>, "code"]]} />);
    expect(code.getAttribute("tabindex")).toBe("0");
    expect(code.getAttribute("role")).toBe("group");
    expect(code.getAttribute("aria-label")).toBe(`Full value: ${LONG}`);
    expect(code.textContent).toBe(LONG);
  });

  it("stays out of the tab order when it fits", () => {
    const view = render(<KeyValues label="Facts" rows={[["Code", <code key="c">KOBO-001</code>, "code"]]} />);
    const code = view.container.querySelector("code") as HTMLElement;
    expect(code.hasAttribute("tabindex")).toBe(false);
    expect(code.hasAttribute("aria-label")).toBe(false);
  });

  it("declares a visible focus indicator for the scrolling code", () => {
    const css = NODE_FS.readFileSync(`${CWD}/src/ui/primitives.css`, "utf8");
    expect(css).toMatch(/\.v69-key-values dd code:focus-visible \{[^}]*outline: 2px solid/s);
  });
});

describe("final-fix L11: author-supplied code attributes are preserved", () => {
  it("keeps an author aria-label on a code that fits and on one that overflows", () => {
    const row = () => <KeyValues label="Facts" rows={[["Session", <code key="c" aria-label="Session 7">SES-7</code>, "s"]]} />;
    const view = render(row());
    const code = view.container.querySelector("code") as HTMLElement;
    expect(code.getAttribute("aria-label")).toBe("Session 7");
    overflow(code, 400, 120);
    view.rerender(row());
    view.rerender(row());
    expect(code.getAttribute("aria-label")).toBe("Session 7");
    expect(code.getAttribute("tabindex")).toBe("0");
    expect(code.hasAttribute("role")).toBe(false);
    overflow(code, 100, 120);
    view.rerender(row());
    expect(code.getAttribute("aria-label")).toBe("Session 7");
    expect(code.hasAttribute("tabindex")).toBe(false);
  });
});
