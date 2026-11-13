import { describe, expect, it } from "vitest";

/*
 * UQ-FI-1 (D-UQFI.2): the type tokens sit on the v7.2 scale with a 12px floor, and Inter
 * (ui/fonts.css) loads before the tokens. Source assertions; jsdom has no layout.
 */
const NODE_FS = (await import(/* @vite-ignore */ `node:${"fs"}`)) as { readFileSync: (p: string, e: string) => string };
const CWD = (globalThis as unknown as { process: { cwd: () => string } }).process.cwd();
const TOKENS = NODE_FS.readFileSync(`${CWD}/src/ui/tokens.css`, "utf8");
const FONTS = NODE_FS.readFileSync(`${CWD}/src/ui/fonts.css`, "utf8");
const MAIN = NODE_FS.readFileSync(`${CWD}/src/main.tsx`, "utf8");

const defs = new Map<string, string[]>();
for (const m of TOKENS.matchAll(/(--[\w-]+)\s*:\s*([^;]+);/g)) defs.set(m[1], [...(defs.get(m[1]) ?? []), m[2].trim()]);

/** Every rem value a token can resolve to (media overrides included). */
function resolveRem(name: string, seen = new Set<string>()): number[] {
  if (seen.has(name)) return [];
  return (defs.get(name) ?? []).flatMap((v) => {
    const ref = /^var\((--[\w-]+)\)$/.exec(v);
    if (ref) return resolveRem(ref[1], new Set([...seen, name]));
    const rem = /^([\d.]+)rem$/.exec(v);
    if (rem) return [Number(rem[1])];
    throw new Error(`${name}: ${v} is not a rem or a var()`);
  });
}

const SIZE_TOKENS = [...defs.keys()].filter(
  (k) => /^--font-size-\d+$/.test(k) || /^--text-(xs|sm|base|lg|xl|2xl|page-title|panel-title|subsection-title|panel-note|table|table-head|cell-secondary|tab|subtab|rail|rail-eyebrow)$/.test(k),
);

describe("UQ-FI type tokens", () => {
  it("defines the eight-step scale exactly", () => {
    expect(SIZE_TOKENS.filter((k) => k.startsWith("--font-size-")).map((k) => [k, defs.get(k)![0]])).toEqual([
      ["--font-size-100", "0.75rem"], ["--font-size-200", "0.8125rem"], ["--font-size-300", "0.875rem"], ["--font-size-400", "1rem"],
      ["--font-size-500", "1.125rem"], ["--font-size-600", "1.25rem"], ["--font-size-700", "1.5rem"], ["--font-size-800", "1.875rem"],
    ]);
  });

  it("every --text-* and --font-size-* size token resolves to 0.75rem (12px) or more", () => {
    expect(SIZE_TOKENS.length).toBe(25);
    for (const name of SIZE_TOKENS) {
      const values = resolveRem(name);
      expect(values.length, name).toBeGreaterThan(0);
      for (const v of values) expect(v, name).toBeGreaterThanOrEqual(0.75);
    }
  });

  it("re-points the role tokens onto the scale (page title 24px, table 13px, table head 12px)", () => {
    expect(defs.get("--text-page-title")![0]).toBe("var(--font-size-700)");
    expect(defs.get("--text-table")).toEqual(["var(--font-size-200)"]);
    expect(defs.get("--text-table-head")).toEqual(["var(--font-size-100)"]);
    expect(defs.get("--font-sans")![0]).toMatch(/^"Inter", system-ui/);
  });

  it("main.tsx imports fonts.css before tokens.css, and Inter is self-hosted", () => {
    const fonts = MAIN.indexOf('import "./ui/fonts.css"');
    expect(fonts).toBeGreaterThanOrEqual(0);
    expect(fonts).toBeLessThan(MAIN.indexOf('import "./ui/tokens.css"'));
    expect(FONTS).toContain('url("/fonts/InterVariable.woff2") format("woff2-variations")');
    expect(FONTS).not.toMatch(/https?:/);
  });
});
