import { describe, expect, it } from "vitest";

const NODE_FS = (await import(/* @vite-ignore */ `node:${"fs"}`)) as { readFileSync: (p: string, e: string) => string };
const CWD = (globalThis as unknown as { process: { cwd: () => string } }).process.cwd();

describe("recapture fix F1: the EV session id wraps inside the key-value code scroller", () => {
  it("out-specifies `.v69-key-values dd code` (nowrap, overflow-x:auto) for `.ev-id`", () => {
    const css = NODE_FS.readFileSync(`${CWD}/src/sites/w2-ev-assessment.css`, "utf8");
    const rule = css.match(/\.v69-key-values dd code\.ev-id\s*\{[^}]*\}/s);
    expect(rule).not.toBeNull();
    expect(rule?.[0]).toMatch(/white-space:\s*normal/);
    expect(rule?.[0]).toMatch(/overflow-x:\s*visible/);
    expect(rule?.[0]).toMatch(/word-break:\s*break-all/);
    const base = NODE_FS.readFileSync(`${CWD}/src/ui/primitives.css`, "utf8").match(/\.v69-key-values dd code\s*\{[^}]*\}/s)?.[0] ?? "";
    expect(base).toMatch(/white-space:\s*nowrap/);
  });
});
