import { describe, expect, it } from "vitest";

/*
 * post-W6 shell-typography-copy: source assertions for the shared CSS contracts. jsdom has no layout, so these
 * prove the rule is declared; the 390/1440 recapture proves the geometry (rulings Q5, Q8, Q10, Q13, Q22).
 */
const NODE_FS = (await import(/* @vite-ignore */ `node:${"fs"}`)) as { readFileSync: (p: string, e: string) => string };
const CWD = (globalThis as unknown as { process: { cwd: () => string } }).process.cwd();
const CSS = NODE_FS.readFileSync(`${CWD}/src/ui/primitives.css`, "utf8").replace(/\r\n/g, "\n");
const TOKENS = NODE_FS.readFileSync(`${CWD}/src/ui/tokens.css`, "utf8");
const SLD = NODE_FS.readFileSync(`${CWD}/src/sites/SiteSingleLineDiagram.tsx`, "utf8");

/** The body of the first `selector { ... }` block found after `from`. */
function block(source: string, selector: string, from = 0): string {
  const start = source.indexOf(`${selector} {`, from);
  expect(start, `${selector} block`).toBeGreaterThanOrEqual(0);
  return source.slice(start, source.indexOf("}", start));
}

describe("post-W6 shell CSS contracts", () => {
  it("R115: the phone-width operator frame names both grid rows so a short page cannot stretch the brand band", () => {
    const media = CSS.indexOf("@media (max-width: 640px) {\n  .app-frame--operator,");
    expect(media).toBeGreaterThanOrEqual(0);
    const rule = block(CSS, "  .app-frame--lab", media);
    expect(rule).toContain("grid-template-rows: auto minmax(0, 1fr);");
  });

  it("R125: the provenance badge uses the mock purple, distinct from the configuration-origin violet", () => {
    expect(TOKENS).toContain("--badge-provenance-bg: #f0eafa;");
    expect(TOKENS).toContain("--badge-provenance-text: #725094;");
    expect(TOKENS).not.toContain("--badge-provenance-text: #15803d;");
    expect(TOKENS).toContain("--badge-origin-text: #5b34b8;");
  });

  it("R129: the topology bus uses the mock teal token and the icon row is centred", () => {
    expect(TOKENS).toContain("--plant-bus: #6ca99a;");
    expect(block(CSS, ".plant-bus")).toContain("border-top: 3px solid var(--plant-bus);");
    expect(block(CSS, ".plant-card__icons")).toContain("margin: 0 auto;");
  });

  it("R130: code values in key-values never break mid-token", () => {
    expect(block(CSS, ".v69-key-values dd code")).toContain("white-space: nowrap;");
    expect(block(CSS, ".panel-pair--top")).toContain("align-items: start;");
  });

  it("R140: the single line diagram scales through its viewBox and keeps its scroll region", () => {
    const sld = block(CSS, ".sld");
    expect(sld).toContain("width: 100%;");
    expect(sld).toContain("height: auto;");
    expect(block(CSS, ".sld__scroll")).toContain("overflow-x: auto;");
    expect(SLD).toContain("viewBox={`0 0 ${lattice.width} ${lattice.height}`}");
    expect(SLD).toContain("style={{ maxWidth: lattice.width }}");
    expect(SLD).not.toMatch(/\n\s+width=\{lattice\.width\}/);
  });

  it("Q13: the readable SLD key is hidden at desktop and shown at phone width", () => {
    expect(block(CSS, ".sld-key")).toContain("display: none;");
    const media = CSS.indexOf("@media (max-width: 640px) {\n  .sld-key {");
    expect(media).toBeGreaterThanOrEqual(0);
    const rule = block(CSS, "  .sld-key", media);
    expect(rule).toContain("display: flex;");
    expect(rule).toContain("font-size: 12px;");
  });

  it("Q23: long Identity values stack full width; the opened reading scrolls inside itself; phone rows wrap wider", () => {
    expect(block(CSS, ".v69-key-values > div[data-key-value-wide] > dd")).toContain("grid-column: 1 / -1;");
    expect(block(CSS, ".v69-key-values > div[data-key-value-wide] > dt")).toContain("grid-column: 1 / -1;");
    const body = block(CSS, ".evidence-record-view__body");
    expect(body).toContain("max-height: 26rem;");
    expect(body).toContain("overflow-y: auto;");
    expect(block(CSS, '  [data-evidence-inspector] tbody th[scope="row"]')).toContain("min-width: 15rem;");
  });
});
