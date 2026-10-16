// W1-UX-06: the shared width check and as-of pattern (tools/evidence-checks.mjs), and the inventory rule:
// every browser evidence script in tools/ applies the ONE shared width check after each resize and navigation.
// Run: node --test tools/checks/test_evidence_checks.mjs (tools/check-all.ps1 runs it).
import assert from "node:assert/strict";
import { readdirSync, readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { test } from "node:test";
import { fileURLToPath } from "node:url";
import { AS_OF_PATTERN, WIDTH_SLACK, widthGuard, widthVerdict } from "../evidence-checks.mjs";

const TOOLS = join(dirname(fileURLToPath(import.meta.url)), "..");
const REPO = join(TOOLS, "..");

/** A fake CDP page whose layout reports `widths()` and records every call. */
function fakePage(widths, { fixOnWindow = null } = {}) {
  const calls = [];
  let current = widths;
  const send = async (method, params) => {
    calls.push(method);
    if (method === "Runtime.evaluate") return { result: { value: { ...current, innerHeight: 900 } } };
    if (method === "Browser.getWindowForTarget") return { windowId: 1 };
    if (method === "Browser.setWindowBounds" && fixOnWindow !== null && params.bounds.width !== undefined) current = fixOnWindow;
    return {};
  };
  return { send, calls };
}
const claims = () => {
  const list = [];
  return { list, claim: (name, ok, detail) => list.push({ name, ok, detail }) };
};
const fast = { waitMs: 30, sleep: async () => {} };

test("the verdict holds only when innerWidth is the requested width and clientWidth is within the slack", () => {
  assert.equal(WIDTH_SLACK, 20);
  assert.equal(widthVerdict(390, 390, 390).ok, true);
  assert.equal(widthVerdict(390, 390, 370).ok, true);
  assert.equal(widthVerdict(1440, 1440, 1425).ok, true);
  assert.equal(widthVerdict(390, 390, 369).ok, false);
  assert.equal(widthVerdict(390, 1440, 1425).ok, false, "the UX-05 L1 case: a nominal 390 laid out at desktop width");
  assert.equal(widthVerdict(390, 980, 980).ok, false, "a mobile page widened by its content");
  assert.equal(widthVerdict(390, 390, 391).ok, false);
  assert.equal(widthVerdict(390, undefined, undefined).ok, false);
});

test("a page at the requested width passes and the claim records both widths", async () => {
  const { send } = fakePage({ innerWidth: 390, clientWidth: 390 });
  const c = claims();
  const v = await widthGuard({ send, claim: c.claim, ...fast })(390, 900, "case");
  assert.equal(v.ok, true);
  assert.equal(c.list.length, 1);
  assert.equal(c.list[0].ok, true);
  assert.match(c.list[0].name, /innerWidth 390, clientWidth 390/);
});

test("a deliberately wrong width fails, throws, and records the failure even when not recording passes", async () => {
  const { send, calls } = fakePage({ innerWidth: 1440, clientWidth: 1425 });
  const c = claims();
  await assert.rejects(widthGuard({ send, claim: c.claim, ...fast })(390, 900, "wrong", { record: false }), /width check failed at wrong: requested 390, innerWidth 1440, clientWidth 1425/);
  assert.equal(c.list.length, 1);
  assert.equal(c.list[0].ok, false);
  assert.ok(calls.includes("Browser.setWindowBounds"), "the width-specific window fallback was tried before failing");
});

test("a page wider than requested fails", async () => {
  const { send } = fakePage({ innerWidth: 390, clientWidth: 1400 });
  await assert.rejects(widthGuard({ send, ...fast })(390, 900, "wide"), /width check failed/);
});

test("the window fallback is accepted only when the recheck then holds", async () => {
  const { send } = fakePage({ innerWidth: 1440, clientWidth: 1425 }, { fixOnWindow: { innerWidth: 390, clientWidth: 390 } });
  const c = claims();
  const v = await widthGuard({ send, claim: c.claim, ...fast })(390, 900, "fallback");
  assert.equal(v.ok, true);
  assert.equal(v.windowFallback, true);
  assert.deepEqual(v.firstAttempt, { innerWidth: 1440, clientWidth: 1425 });
});

test("the evidence as-of pattern is the frontend's shared acceptance pattern, byte for byte", () => {
  const ts = readFileSync(join(REPO, "frontend", "src", "test", "productPresentation.ts"), "utf8");
  const m = ts.match(/export const AS_OF_PATTERN = (\/.+\/);/);
  assert.ok(m, "frontend AS_OF_PATTERN found");
  assert.equal(m[1], String(AS_OF_PATTERN));
  assert.ok(AS_OF_PATTERN.test("As of 16 Oct 2026, 10:05 UTC"));
  assert.ok(AS_OF_PATTERN.test("As of: time not recorded"));
  for (const wrong of ["As of now", "As of ", "As of : time not recorded", "As of 16 Oct 2026"]) assert.ok(!AS_OF_PATTERN.test(wrong), wrong);
});

// --- Inventory rule ----------------------------------------------------------------------------------------

/** Scripts that set a viewport but make no width-dependent claim. Anything else unguarded fails this test. */
const EXEMPT = {
  "run-store-browser-evidence.mjs": "timing only, at one fixed 1280 px viewport; it makes no layout, overflow or narrow-width claim",
};
/** Scripts whose single guarded measure step sits far from the navigation (checked by presence, not proximity). */
const GUARDED_AT_MEASURE = {
  "layout-evidence.mjs": "visit() navigates, waits and acts, then checks the width immediately before MEASURE",
};
const GUARD_CALL = /\b(requireWidth|widthHolds)\(|widthGuard\(\{[^}]*\}\)\(/;
const TRIGGER = /Emulation\.setDeviceMetricsOverride|"Page\.navigate"|"Page\.reload"|history\.(back|forward)\(/;

const browserScripts = () =>
  readdirSync(TOOLS)
    .filter((f) => f.endsWith(".mjs") && f !== "evidence-checks.mjs")
    .filter((f) => /Emulation\.setDeviceMetricsOverride/.test(readFileSync(join(TOOLS, f), "utf8")));

/** Every trigger line must be followed by a guard call within `window` lines, before any other trigger. */
export function unguardedTriggers(source, window = 6) {
  const lines = source.split("\n");
  const misses = [];
  lines.forEach((line, i) => {
    if (!TRIGGER.test(line) || line.trim().startsWith("//") || line.trim().startsWith("*")) return;
    for (let k = i + 1; k <= Math.min(i + window, lines.length - 1); k += 1) {
      if (GUARD_CALL.test(lines[k])) return;
      if (TRIGGER.test(lines[k]) && !/Emulation\.setDeviceMetricsOverride/.test(line)) break;
    }
    misses.push(`${i + 1}: ${line.trim().slice(0, 100)}`);
  });
  return misses;
}

test("the inventory is non-empty and names the walkthrough's scripts", () => {
  const found = browserScripts();
  for (const name of ["w1-ux-01-evidence.mjs", "w1-ux-03-evidence.mjs", "w1-ux-05-evidence.mjs", "v01a-foundation-evidence.mjs", "s408-assumption-history-evidence.mjs", "s502-overview-finding-list-evidence.mjs", "s602b-verification-evidence.mjs", "s603-site-work-evidence.mjs", "s601b-action-evidence.mjs", "s3-dispatch-evidence.mjs", "s302-claim-limit-evidence.mjs", "s404-finding-index-evidence.mjs", "s701-health-evidence.mjs"]) {
    assert.ok(found.includes(name), `${name} is in the inventory`);
  }
  assert.ok(found.length >= 20, `found ${found.length}`);
});

test("every browser evidence script imports the shared width check and calls it after each resize and navigation", () => {
  const problems = [];
  for (const file of browserScripts()) {
    if (EXEMPT[file]) continue;
    const src = readFileSync(join(TOOLS, file), "utf8");
    if (!/from "\.\/evidence-checks\.mjs"/.test(src) || !/widthGuard\(/.test(src)) {
      problems.push(`${file}: does not use the shared width check (tools/evidence-checks.mjs)`);
      continue;
    }
    if (GUARDED_AT_MEASURE[file]) continue;
    for (const miss of unguardedTriggers(src)) problems.push(`${file}:${miss}`);
  }
  assert.deepEqual(problems, []);
});

test("the proximity rule fails on an unguarded navigation (non-vacuous)", () => {
  const guarded = 'await send("Page.navigate", { url });\nawait waitFor(x);\nawait requireWidth(390, 900, "w");';
  const bare = 'await send("Page.navigate", { url });\nawait waitFor(x);\nconst m = await js(MEASURE);';
  const resize = 'await send("Emulation.setDeviceMetricsOverride", { width });\nawait send("Page.navigate", { url });\nawait requireWidth(390, 900, "w");';
  assert.deepEqual(unguardedTriggers(guarded), []);
  assert.equal(unguardedTriggers(bare).length, 1);
  assert.deepEqual(unguardedTriggers(resize), []);
});
