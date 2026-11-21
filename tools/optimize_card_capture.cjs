// 1a (spec specs/1a-optimize-card-scope/spec.md §3.6): captures of the Portfolio's Optimize card with its day and
// scope line, from the built frontend served by `vite preview`, every /api/ request answered from
// frontend/e2e-fixtures/1a/<case>/<path with / as _>.json (an unlisted API path answers 404 and is printed).
//
//   source /opt/assetecon/tools/pw/env.sh; export LD_LIBRARY_PATH=$AUDIT_LD_LIBRARY_PATH
//   tools/heavy-slot.sh -- node tools/optimize_card_capture.cjs <out-dir> [--no-build]
//
// Evidence only (never committed): PNGs plus summary.json in <out-dir>. Refuses outside a heavy slot (exit 69).
"use strict";
const { spawn, spawnSync } = require("node:child_process");
const fs = require("node:fs");
const path = require("node:path");

if (!process.env.ASSETOPS_HEAVY_SLOT) {
  console.error("optimize_card_capture: refused: run through tools/heavy-slot.sh -- node tools/optimize_card_capture.cjs");
  process.exit(69);
}
const { chromium } = require(process.env.PW);
const ROOT = path.resolve(__dirname, "..");
const FRONTEND = path.join(ROOT, "frontend");
const FIXTURES = path.join(FRONTEND, "e2e-fixtures", "1a");
const PORT = 5496;
const BASE = `http://127.0.0.1:${PORT}`;
const ROUTE = "/portfolio?from=2026-10-01T00%3A00%3A00Z&to=2026-10-31T00%3A00%3A00Z";
const CASES = ["one", "two"];
const VIEWPORTS = [[390, 844], [1280, 900], [1440, 900]];
const THEMES = ["light", "dark"];

async function waitUp(url, ms) {
  const end = Date.now() + ms;
  while (Date.now() < end) {
    try {
      if ((await fetch(url)).ok) return;
    } catch {
      /* not up yet */
    }
    await new Promise((r) => setTimeout(r, 300));
  }
  throw new Error(`no server at ${url}`);
}

(async () => {
  const out = path.resolve(process.argv[2] || "");
  if (!process.argv[2]) throw new Error("usage: optimize_card_capture.cjs <out-dir> [--no-build]");
  fs.mkdirSync(out, { recursive: true });
  if (!process.argv.includes("--no-build")) {
    const b = spawnSync("npm", ["run", "build"], { cwd: FRONTEND, stdio: "inherit" });
    if (b.status !== 0) throw new Error(`npm run build exited ${b.status}`);
  }
  // `vite preview --strictPort --port 5496 --host 127.0.0.1`, run by node directly so the one PID stopped is the server.
  const server = spawn(process.execPath, [path.join(FRONTEND, "node_modules", "vite", "bin", "vite.js"), "preview",
                                          "--strictPort", "--port", String(PORT), "--host", "127.0.0.1"],
    { cwd: FRONTEND, stdio: ["ignore", "ignore", "inherit"] });
  const summary = [];
  let browser;
  try {
    await waitUp(BASE + "/", 30000);
    browser = await chromium.launch({ executablePath: process.env.CHROME });
    for (const name of CASES) {
      for (const [width, height] of VIEWPORTS) {
        for (const theme of THEMES) {
          const page = await browser.newPage({ viewport: { width, height }, colorScheme: theme });
          const errors = [];
          const unlisted = [];
          page.on("console", (m) => m.type() === "error" && errors.push(m.text()));
          page.on("pageerror", (e) => errors.push(e.message));
          await page.route((u) => new URL(u).pathname.startsWith("/api/"), async (route) => {
            const p = new URL(route.request().url()).pathname;
            const file = path.join(FIXTURES, name, p.slice(1).replace(/\//g, "_") + ".json");
            if (fs.existsSync(file)) {
              await route.fulfill({ status: 200, contentType: "application/json", body: fs.readFileSync(file, "utf8") });
            } else {
              unlisted.push(p);
              await route.fulfill({ status: 404, contentType: "application/json", body: "{}" });
            }
          });
          await page.goto(BASE + ROUTE);
          await page.waitForSelector("[data-portfolio-card='OPTIMIZE_COST'] [data-portfolio-card-value]", { timeout: 15000 });
          await page.waitForTimeout(500);
          const card = page.locator("[data-portfolio-card='OPTIMIZE_COST']");
          const scope = await card.locator("[data-portfolio-card-scope]").allTextContents();
          const box = await card.boundingBox();
          const overflow = await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth);
          const base = `${name}-${width}-${theme}`;
          await card.screenshot({ path: path.join(out, `${base}-card.png`) });
          await page.screenshot({ path: path.join(out, `${base}-page.png`), fullPage: false });
          const row = { case: name, width, height, theme, scope, card_box: box, horizontal_overflow: overflow,
                        console_errors: errors.length, errors, unlisted_api: [...new Set(unlisted)] };
          summary.push(row);
          console.log(`${base}: scope=${JSON.stringify(scope)} errors=${errors.length} overflow=${overflow} ` +
                      `unlisted=${JSON.stringify(row.unlisted_api)}`);
          await page.close();
        }
      }
    }
  } finally {
    if (browser) await browser.close();
    server.kill("SIGTERM");
  }
  fs.writeFileSync(path.join(out, "summary.json"), JSON.stringify(summary, null, 1) + "\n");
})().catch((e) => {
  console.error(e);
  process.exit(1);
});
