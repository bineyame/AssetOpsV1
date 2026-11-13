import { cleanup, render } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { StatusPill, statusLook } from "../StatusPill";

afterEach(cleanup);

const NODE_FS = (await import(/* @vite-ignore */ `node:${"fs"}`)) as { readFileSync: (p: string, e: string) => string };
const CWD = (globalThis as unknown as { process: { cwd: () => string } }).process.cwd();
const readSrc = (rel: string) => NODE_FS.readFileSync(`${CWD}/src/${rel}`, "utf8");

function pill(state: string, label: string): HTMLElement {
  const { container } = render(<StatusPill state={state} label={label} />);
  return container.querySelector("[data-status-pill]") as HTMLElement;
}

// UQ-FI-3: the six outcome states of the Portfolio key, plus the two the server also sends. Look and symbol per
// state; the word is always the caller's (the server's `state_label`).
const CASES: readonly [state: string, label: string, look: string, glyph: string | null][] = [
  ["NEEDS_ATTENTION", "Needs attention", "partial", "alert"],
  ["WATCH", "Watch", "neutral", null],
  ["OPPORTUNITY", "Opportunity", "accent", "trend"],
  ["ON_TRACK", "On track", "complete", "check"],
  ["UNKNOWN", "Unknown", "noreadings", "ring"],
  ["NOT_MEASURED", "Not measured yet", "notanalysed", null],
  ["NO_OBJECTIVE", "No target for this outcome", "neutral", null],
  ["NOT_APPLICABLE", "N/A", "notanalysed", null],
];

describe("UQ-FI-3 StatusPill", () => {
  for (const [state, label, look, glyph] of CASES) {
    it(`renders ${state} with the ${look} look and the caller's word`, () => {
      const el = pill(state, label);
      expect(el.getAttribute("data-status-pill")).toBe(state);
      expect(el.className).toBe(`status-pill s-${look}`);
      expect(el.textContent).toBe(label);
      const svg = el.querySelector("svg");
      if (glyph === null) expect(svg).toBeNull();
      else {
        expect(svg?.getAttribute("data-status-glyph")).toBe(glyph);
        expect(svg?.getAttribute("aria-hidden")).toBe("true");
      }
      expect(statusLook(state).look).toBe(look);
    });
  }

  it("readsAnUnrecognisedCodeAsNeutralAndNeverShowsTheCode", () => {
    const el = pill("SOMETHING_NEW", "Server word");
    expect(el.className).toBe("status-pill s-neutral");
    expect(el.textContent).toBe("Server word");
    expect(el.textContent).not.toContain("SOMETHING_NEW");
  });

  it("everyLookHasItsTokensAndTheStylesUseTokensOnly", () => {
    const css = readSrc("ui/status-pill.css");
    const tokens = readSrc("ui/tokens.css");
    expect(css).not.toMatch(/#[0-9a-fA-F]{3,8}\b/);
    for (const look of new Set(CASES.map((c) => c[2]))) {
      expect(css).toContain(`.status-pill.s-${look} {`);
      for (const part of ["bg", "text", "border"]) expect(tokens).toContain(`--color-status-${look}-${part}:`);
    }
    // The sheet's "not analysed" chip is dashed: colour is never the only signal.
    expect(css).toMatch(/\.s-notanalysed \{[^}]*border-style: dashed/);
  });
});
