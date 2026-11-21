// WK smoke S3 (specs/WK-walkthrough-database/spec.md §3.6): open each served page, record the /api/ answers.
//
//   node tools/walk_world_smoke.cjs --base http://127.0.0.1:<web_port> --pages '<JSON list>' --out <dir>/
//
// Run only by `tools/walk_world.py smoke`, which is itself run inside the heavy-tool slot (spec §5 step 8) and gives
// this script exactly PATH, HOME, PW, CHROME, FONTCONFIG_FILE and LD_LIBRARY_PATH (I3). A page FAILs on a status of
// 500 or more, a failed request, a page error, or the 30 s cap. One full-page PNG per page and report.json
// ([{"page", "api", "fail": [{"url", "status"}], "errors"}]). Exit 0 when every page passes, else 1; 2 on bad usage.
"use strict";

const fs = require("node:fs");
const path = require("node:path");

const USAGE = "usage: node tools/walk_world_smoke.cjs --base URL --pages JSON --out DIR";
const CAP_MS = 30000;

function parse(argv) {
  const out = {};
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === "--help" || a === "-h") out.help = true;
    else if (a === "--base" || a === "--pages" || a === "--out") out[a.slice(2)] = argv[++i];
    else throw new Error(`unknown argument ${a}`);
  }
  return out;
}

function fileFor(page, i) {
  return `${String(i + 1).padStart(2, "0")}-${page.replace(/^\//, "").replace(/[^A-Za-z0-9-]+/g, "_") || "root"}.png`;
}

async function walk(base, pages, out) {
  const engine = require(process.env.PW);
  const browser = await engine.chromium.launch({ executablePath: process.env.CHROME });
  const report = [];
  try {
    for (const [i, page] of pages.entries()) {
      const tab = await browser.newPage({ viewport: { width: 1440, height: 900 } });
      const row = { page, api: [], fail: [], errors: [] };
      tab.on("response", (r) => {
        const u = new URL(r.url());
        if (!u.pathname.startsWith("/api/")) return;
        row.api.push({ url: u.pathname + u.search, status: r.status() });
        if (r.status() >= 500) row.fail.push({ url: u.pathname + u.search, status: r.status() });
      });
      tab.on("requestfailed", (r) => {
        const u = new URL(r.url());
        row.fail.push({ url: u.pathname + u.search, status: null });
      });
      tab.on("pageerror", (e) => row.errors.push(String(e && e.message ? e.message : e)));
      try {
        await tab.goto(base + page, { waitUntil: "networkidle", timeout: CAP_MS });
      } catch (e) {
        row.errors.push(`cap ${CAP_MS} ms`);
      }
      try {
        await tab.screenshot({ path: path.join(out, fileFor(page, i)), fullPage: true });
      } catch (e) {
        row.errors.push("screenshot");
      }
      await tab.close();
      report.push(row);
    }
  } finally {
    await browser.close();
  }
  return report;
}

async function main() {
  let args;
  try {
    args = parse(process.argv.slice(2));
  } catch (e) {
    console.error(USAGE);
    return 2;
  }
  if (args.help) {
    console.log(USAGE);
    return 0;
  }
  let pages;
  try {
    pages = JSON.parse(args.pages || "");
  } catch (e) {
    pages = null;
  }
  if (!args.base || !args.out || !Array.isArray(pages) || !pages.every((p) => typeof p === "string" && p.startsWith("/"))) {
    console.error(USAGE);
    return 2;
  }
  fs.mkdirSync(args.out, { recursive: true });
  const report = await walk(args.base.replace(/\/$/, ""), pages, args.out);
  fs.writeFileSync(path.join(args.out, "report.json"), JSON.stringify(report, null, 1) + "\n");
  const failed = report.filter((r) => r.fail.length || r.errors.length);
  console.log(JSON.stringify({ pages: report.length, failed: failed.map((r) => r.page) }));
  return failed.length ? 1 : 0;
}

main().then((code) => process.exit(code), (e) => {
  console.error(`SMOKE_FAILED ${e && e.name ? e.name : "error"}`);
  process.exit(1);
});
