/**
 * IA-P P1 (spec §6 P1, D-IAP.27, handshake R4 and I2): the "no screen lost" control, both ways.
 *
 * (a) Every route path `App.tsx` mounts is a live route (it matches an `IA_HOMES` family), a live alias, a Lab route or
 *     `*`. Paths are read raw from `App.tsx`; each `{IDENT}` resolves through `operatorSiteRoutes.ts`; a `path={path}`
 *     inside `[...].map` takes the array literal before the `.map`; the Lab paths come from `simulatorLabRoutes`.
 *     An unresolvable `path={…}` fails.
 * (b) Every spec §2.4 "Current address" (held here as literals) resolves to a mounted route or a live alias.
 */
import { matchPath } from "react-router-dom";
import { describe, expect, it } from "vitest";

import * as siteRoutes from "../operatorSiteRoutes";
import { simulatorLabRoutes } from "../simulatorLabRoutes";
import { IA_HOMES, liveLegacyRoutes } from "../iaRoutes";
import APP_SOURCE from "../../App.tsx?raw";

const APP: string = APP_SOURCE;
const CONSTANTS = siteRoutes as unknown as Record<string, unknown>;

/** Spec §2.4 "Current address", one concrete address per row (rev 3), plus the new tabs landed so far. */
const SECTION_2_4 = [
  "/",
  "/portfolio",
  "/portfolio/month",
  "/portfolio/act-first",
  "/portfolio/outcomes",
  "/portfolio/opportunity",
  "/portfolio/changes",
  "/portfolio/scope",
  "/portfolio/anything-else",
  "/sites",
  "/sites/KOBO-001",
  "/sites/KOBO-001/performance",
  "/sites/KOBO-001/findings",
  "/sites/KOBO-001/configuration",
  "/findings",
  "/findings/cost",
  "/findings/risks",
  "/findings/opportunities",
  "/findings/KOBO-001/ASM-1",
  "/findings/KOBO-001/ASM-1/evidence",
  "/actions",
  "/incidents",
  "/maintenance",
  "/maintenance/preventive",
  "/maintenance/requests/C-1",
  "/maintenance/requests/C-1/record",
  "/operational-records",
  "/evidence",
  "/financials",
  "/evidence/records",
];

function resolveExpr(expr: string): string[] {
  const text = expr.trim();
  const literal = /^"([^"]*)"$/.exec(text);
  if (literal) return [literal[1]];
  if (/^[A-Z][A-Z0-9_]*$/.test(text)) {
    const value = CONSTANTS[text];
    if (typeof value !== "string") throw new Error(`unresolvable route constant ${text}`);
    return [value];
  }
  const template = /^`([^`]*)`$/.exec(text);
  if (template) {
    return [
      template[1].replace(/\$\{([A-Z][A-Z0-9_]*)\}/g, (_, name: string) => {
        const value = CONSTANTS[name];
        if (typeof value !== "string") throw new Error(`unresolvable route constant ${name}`);
        return value;
      }),
    ];
  }
  throw new Error(`unresolvable path={${text}}`);
}

/** The array literal before the `.map(` that precedes `at`, as its route constants. */
function mappedPaths(at: number): string[] {
  const mapAt = APP.lastIndexOf(".map(", at);
  if (mapAt < 0) throw new Error("path={path} outside a .map");
  let depth = 0;
  let start = -1;
  for (let i = mapAt - 1; i >= 0; i -= 1) {
    const ch = APP[i];
    if (ch === "]") depth += 1;
    else if (ch === "[") {
      depth -= 1;
      if (depth === 0) {
        start = i;
        break;
      }
    }
  }
  const array = APP.slice(start, mapAt);
  const names = array.match(/\b[A-Z][A-Z0-9_]+\b/g) ?? [];
  if (names.length === 0) throw new Error("path={path} maps an array with no route constants");
  return names.map((name: string) => resolveExpr(name)[0]);
}

interface Mounted {
  path: string;
  kind: "route" | "alias" | "lab";
}

function mountedPaths(): Mounted[] {
  const out: Mounted[] = [];
  const re = /path=(\{|")/g;
  let m: RegExpExecArray | null;
  while ((m = re.exec(APP)) !== null) {
    if (m[1] === '"') {
      const end = APP.indexOf('"', m.index + 6);
      out.push({ path: APP.slice(m.index + 6, end), kind: "route" });
      continue;
    }
    let depth = 1;
    let i = m.index + 6;
    while (depth > 0 && i < APP.length) {
      if (APP[i] === "{") depth += 1;
      else if (APP[i] === "}") depth -= 1;
      i += 1;
    }
    const expr = APP.slice(m.index + 6, i - 1).trim();
    if (expr === "path") {
      for (const path of mappedPaths(m.index)) out.push({ path, kind: "route" });
    } else if (/^route\.prefix \? `\$\{route\.from\}\/\*` : route\.from$/.test(expr)) {
      for (const route of liveLegacyRoutes()) out.push({ path: route.from, kind: "alias" });
    } else if (expr === "route.path") {
      const lab = simulatorLabRoutes({ simulatorLab: { enabled: true } });
      for (const route of lab) out.push({ path: route.path, kind: "lab" });
    } else {
      for (const path of resolveExpr(expr)) out.push({ path, kind: "route" });
    }
  }
  return out;
}

/** A concrete address for a route pattern: each `:param` a sample segment, an optional segment both ways. */
function samples(pattern: string): string[] {
  const optional = pattern.match(/\/:[A-Za-z]+\?/);
  if (optional) {
    return [...samples(pattern.replace(optional[0], "")), ...samples(pattern.replace(optional[0], "/sample"))];
  }
  return [pattern.replace(/:[A-Za-z]+/g, "sample").replace(/\/\*$/, "/sample")];
}

describe("IA-P route map (spec §2.4, D-IAP.27)", () => {
  const mounted = mountedPaths();

  it("reads a non-empty route table", () => {
    expect(mounted.filter((m) => m.kind === "route").length).toBeGreaterThan(40);
    expect(mounted.some((m) => m.kind === "alias")).toBe(true);
  });

  it("(a) every mounted route is a live route, a live alias, a Lab route or *", () => {
    const aliases = new Set(liveLegacyRoutes().map((r) => r.from));
    const stray: string[] = [];
    for (const m of mounted) {
      if (m.kind === "lab" || m.path === "*") continue;
      if (m.kind === "alias" || aliases.has(m.path)) continue;
      for (const sample of samples(m.path)) {
        if (!IA_HOMES.some((home) => home.pattern.test(sample))) stray.push(`${m.path} (${sample})`);
      }
    }
    expect(stray).toEqual([]);
  });

  it("(b) every spec §2.4 address resolves to a mounted route or a live alias", () => {
    const patterns = mounted.filter((m) => m.path !== "*").map((m) => m.path);
    const lost = SECTION_2_4.filter((address) => !patterns.some((path) => matchPath({ path, end: true }, address) !== null));
    expect(lost).toEqual([]);
  });
});
