/**
 * Layout evidence from a real browser, with no new dependency.
 *
 * jsdom has no layout, so nothing in the suite can see a scrollbar. This
 * drives the Chrome already installed on this machine over the DevTools
 * Protocol, using Node's built-in fetch and WebSocket, and reports measured
 * numbers rather than opinions.
 *
 * It asserts nothing about pixels being pretty. It measures the claims T011B
 * makes and the ones T012 adds, each of which is a fact a browser can answer
 * yes or no to: does the document scroll sideways, does the rail move when the
 * table is scrolled, is the frame as tall as the viewport, is every action
 * disabled.
 *
 * Deliberately not wired into `tools/check-architecture.ps1`. That runner is
 * for seams that must hold on every change, it must run anywhere, and this
 * needs a browser and two servers. Whether layout evidence should become a
 * standing check is an Architect decision about what review means here, not
 * something an implementer should settle by adding a module.
 *
 * Run it with both servers up:
 *
 *   .venv/Scripts/python.exe -m uvicorn assetops_backend.main:app --port 8000
 *   npm run dev            # from frontend/
 *   node tools/layout-evidence.mjs [baseUrl]
 *
 * It exits non-zero if any claim fails, so it can be read by a person or by a
 * script. It drives the Chrome already installed on this machine over the
 * DevTools Protocol using Node's built-in fetch and WebSocket, so it adds no
 * dependency to the project and nothing to install.
 */

import { spawn } from "node:child_process";
import { mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

const BASE = process.argv[2] ?? "http://localhost:5173";
const PORT = 9333;
const CHROME = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";

const profile = mkdtempSync(join(tmpdir(), "assetops-cdp-"));

const chrome = spawn(
  CHROME,
  [
    "--headless=new",
    "--disable-gpu",
    "--no-first-run",
    "--no-default-browser-check",
    `--remote-debugging-port=${PORT}`,
    `--user-data-dir=${profile}`,
    "about:blank",
  ],
  { stdio: "ignore" },
);

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

async function pageSocketUrl() {
  for (let attempt = 0; attempt < 60; attempt += 1) {
    try {
      const res = await fetch(`http://127.0.0.1:${PORT}/json/list`);
      const targets = await res.json();
      const page = targets.find((t) => t.type === "page");
      if (page?.webSocketDebuggerUrl) return page.webSocketDebuggerUrl;
    } catch {
      /* not up yet */
    }
    await sleep(250);
  }
  throw new Error("Chrome did not expose a page target");
}

class Cdp {
  constructor(ws) {
    this.ws = ws;
    this.id = 0;
    this.pending = new Map();
    ws.addEventListener("message", (event) => {
      const msg = JSON.parse(event.data);
      if (msg.id && this.pending.has(msg.id)) {
        const { resolve, reject } = this.pending.get(msg.id);
        this.pending.delete(msg.id);
        msg.error ? reject(new Error(JSON.stringify(msg.error))) : resolve(msg.result);
      }
    });
  }

  send(method, params = {}) {
    this.id += 1;
    const id = this.id;
    return new Promise((resolve, reject) => {
      this.pending.set(id, { resolve, reject });
      this.ws.send(JSON.stringify({ id, method, params }));
    });
  }
}

/** Runs in the page. Returns measurements, never judgements. */
const MEASURE = `(() => {
  const doc = document.scrollingElement;
  const rail = document.querySelector(".app-frame__side");
  const scroller = document.querySelector(".data-table__scroll");
  const frame = document.querySelector(".app-frame");
  const railLeftBefore = rail ? Math.round(rail.getBoundingClientRect().left) : null;
  let scrollerOverflows = null;
  let scrolledBy = 0;
  if (scroller) {
    scrollerOverflows = scroller.scrollWidth > scroller.clientWidth;
    scroller.scrollLeft = 99999;
    scrolledBy = Math.round(scroller.scrollLeft);
  }
  const railLeftAfter = rail ? Math.round(rail.getBoundingClientRect().left) : null;
  // Every table on the page, not only the first. Before T014 a Foundation had
  // one table; it now has six, and measuring one of them would report on a
  // screen that no longer exists. Each is scrolled to its end so the rail
  // measurement below covers all of them at once.
  const scrollers = Array.from(
    document.querySelectorAll(".data-table__scroll"),
  ).map((region) => {
    const table = region.querySelector("table");
    const overflows = region.scrollWidth > region.clientWidth;
    region.scrollLeft = 99999;
    return {
      name: region.getAttribute("aria-labelledby"),
      overflows,
      scrolledBy: Math.round(region.scrollLeft),
      columnCount: table ? table.querySelectorAll("thead th").length : 0,
      rowCount: table ? table.querySelectorAll("tbody tr").length : 0,
      focusable: region.getAttribute("tabindex") === "0",
    };
  });
  // The configured diagram is the second piece of dense content with an
  // intrinsic width, and it is not a table, so the region scan above cannot
  // see it. Measured here and scrolled to its end before the rail is read
  // again, so the rail claim below covers the drawing as well as the tables.
  const diagrams = Array.from(document.querySelectorAll(".sld__scroll")).map(
    (region) => {
      const svg = region.querySelector("svg");
      const overflows = region.scrollWidth > region.clientWidth;
      region.scrollLeft = 99999;
      return {
        name: region.getAttribute("aria-labelledby"),
        overflows,
        scrolledBy: Math.round(region.scrollLeft),
        focusable: region.getAttribute("tabindex") === "0",
        nodes: svg ? svg.querySelectorAll("[data-sld-node]").length : 0,
        connections: svg ? svg.querySelectorAll("[data-sld-connection]").length : 0,
        named:
          svg !== null &&
          svg.getAttribute("role") === "img" &&
          (svg.getAttribute("aria-labelledby") || "").length > 0,
      };
    },
  );
  const diagramRefusals = document.querySelectorAll("[data-sld-unavailable]").length;
  const slots = Array.from(document.querySelectorAll(".sld-node__slot")).map((slot) =>
    (slot.textContent || "").trim(),
  );
  const railLeftAfterAll = rail ? Math.round(rail.getBoundingClientRect().left) : null;
  return {
    scrollers,
    diagrams,
    diagramRefusals,
    slots,
    railLeftAfterAll,
    pageScrollsHorizontally: doc.scrollWidth > doc.clientWidth,
    pageScrollWidth: doc.scrollWidth,
    pageClientWidth: doc.clientWidth,
    pageScrollsVertically: doc.scrollHeight > doc.clientHeight,
    pageScrollHeight: doc.scrollHeight,
    pageClientHeight: doc.clientHeight,
    railLeftBefore,
    railLeftAfter,
    scrollerOverflows,
    scrolledBy,
    frameHeight: frame ? Math.round(frame.getBoundingClientRect().height) : null,
    viewportHeight: window.innerHeight,
    headerCount: document.querySelectorAll("table thead th").length,
    buttons: Array.from(document.querySelectorAll("main button")).map((b) => ({
      label: (b.textContent || "").trim(),
      disabled: b.disabled,
    })),
    tabLabels: Array.from(document.querySelectorAll(".site-tabs__list li")).map(
      (li) => (li.textContent || "").trim(),
    ),
    // Scoped by landmark name, because a Foundation page carries two of these
    // rows - the operator Site tabs and the Foundation subtabs - and counting
    // them together would say twelve and mean nothing.
    navRows: Array.from(
      document.querySelectorAll("nav.site-tabs, nav.section-nav"),
    ).map((nav) => ({
      label: nav.getAttribute("aria-label"),
      items: Array.from(nav.querySelectorAll("li")).map((li) =>
        (li.textContent || "").trim(),
      ),
    })),
    bodyText: (document.body.textContent || "").slice(0, 0),
  };
})()`;

async function visit(cdp, path, width, height, waitFor) {
  await cdp.send("Emulation.setDeviceMetricsOverride", {
    width,
    height,
    deviceScaleFactor: 1,
    mobile: false,
  });
  await cdp.send("Page.navigate", { url: `${BASE}${path}` });

  for (let attempt = 0; attempt < 80; attempt += 1) {
    await sleep(150);
    const probe = await cdp.send("Runtime.evaluate", {
      expression: `document.querySelector(${JSON.stringify(waitFor)}) !== null`,
      returnByValue: true,
    });
    if (probe.result.value === true) break;
  }
  await sleep(250);

  const result = await cdp.send("Runtime.evaluate", {
    expression: MEASURE,
    returnByValue: true,
  });
  return result.result.value;
}

function report(title, m, checks) {
  console.log(`\n=== ${title} ===`);
  for (const [claim, pass, detail] of checks) {
    console.log(`  ${pass ? "PASS" : "FAIL"}  ${claim}${detail ? `  [${detail}]` : ""}`);
  }
  return checks.every(([, pass]) => pass);
}

const socketUrl = await pageSocketUrl();
const ws = new WebSocket(socketUrl);
await new Promise((resolve) => ws.addEventListener("open", resolve));
const cdp = new Cdp(ws);
await cdp.send("Page.enable");
await cdp.send("Runtime.enable");

let allPass = true;

for (const [label, width, height] of [
  ["1280x800, the committed minimum", 1280, 800],
  ["1000x700, below the commitment", 1000, 700],
]) {
  const sites = await visit(cdp, "/sites", width, height, "table");
  allPass =
    report(`Sites index at ${label}`, sites, [
      [
        "the page does not scroll horizontally",
        !sites.pageScrollsHorizontally,
        `scrollWidth ${sites.pageScrollWidth} vs clientWidth ${sites.pageClientWidth}`,
      ],
      [
        "the rail does not move when the table is scrolled",
        sites.railLeftBefore === sites.railLeftAfter,
        `left ${sites.railLeftBefore} -> ${sites.railLeftAfter}, table scrolled by ${sites.scrolledBy}px`,
      ],
      [
        "all nine columns are still rendered",
        sites.headerCount === 9,
        `${sites.headerCount} headers`,
      ],
    ]) && allPass;

  const site = await visit(cdp, "/sites/MG-001", width, height, ".site-tabs");
  allPass =
    report(`Site page at ${label}`, site, [
      [
        "the page does not scroll horizontally",
        !site.pageScrollsHorizontally,
        `scrollWidth ${site.pageScrollWidth} vs clientWidth ${site.pageClientWidth}`,
      ],
      [
        "all eight tabs are rendered",
        site.tabLabels.length === 8,
        site.tabLabels.join(" | "),
      ],
      [
        // Not "every action is disabled", which would require an action to
        // exist and so would fail on any tree before the Quick actions panel
        // lands. What holds across the milestone is that nothing on this
        // screen can be operated: zero actions satisfies it, and one enabled
        // action breaks it.
        "no enabled action renders",
        site.buttons.every((b) => b.disabled),
        site.buttons.length === 0
          ? "no action rendered"
          : site.buttons
              .map((b) => `${b.label}:${b.disabled ? "disabled" : "ENABLED"}`)
              .join(", "),
      ],
    ]) && allPass;
}

const short = await visit(cdp, "/", 1280, 800, ".app-frame");
allPass =
  report("Operator home at 1280x800, gate open, short page", short, [
    [
      "the page does not scroll vertically",
      !short.pageScrollsVertically,
      `scrollHeight ${short.pageScrollHeight} vs clientHeight ${short.pageClientHeight}`,
    ],
  ]) && allPass;

for (const [label, width, height] of [
  ["1280x800", 1280, 800],
  ["1000x700", 1000, 700],
  // Narrow enough that the dense relationship tables cannot fit. Without a
  // width where something actually overflows, "every table that overflows
  // scrolls inside its own region" is a claim about an empty set: it passes on
  // a page whose regions do not scroll at all, which is the defect it exists
  // to catch. The claim below asserts the set is not empty here.
  ["640x700, narrow enough that a dense table cannot fit", 640, 700],
]) {
  const foundation = await visit(
    cdp,
    "/sites/MG-001/foundation",
    width,
    height,
    ".site-tabs",
  );
  const subtabs =
    foundation.navRows.find((row) => row.label === "Foundation sections")
      ?.items ?? [];
  const siteTabs =
    foundation.navRows.find((row) => row.label === "Site sections")?.items ?? [];

  allPass =
    report(`Foundation at ${label}`, foundation, [
      [
        "the page does not scroll horizontally",
        !foundation.pageScrollsHorizontally,
        `scrollWidth ${foundation.pageScrollWidth} vs clientWidth ${foundation.pageClientWidth}`,
      ],
      [
        "the Site tab row still carries all eight",
        siteTabs.length === 8,
        siteTabs.join(" | "),
      ],
      [
        "the Foundation subtab row is the four, without Changes",
        subtabs.length === 4 && !subtabs.includes("Changes"),
        subtabs.join(" | "),
      ],
      [
        "no enabled action renders",
        foundation.buttons.every((b) => b.disabled),
        foundation.buttons.length === 0
          ? "no action rendered"
          : foundation.buttons.map((b) => b.label).join(", "),
      ],
      // T014 fills this page with relationship tables. The viewport
      // commitment is that a dense table keeps its columns and scrolls inside
      // its own region; these three claims are that commitment, measured.
      [
        "every table on the page has a named, focusable overflow region",
        foundation.scrollers.length > 0 &&
          foundation.scrollers.every((s) => s.focusable && s.name),
        foundation.scrollers.map((s) => s.name ?? "unnamed").join(", "),
      ],
      [
        "every table that overflows scrolls inside its own region",
        foundation.scrollers
          .filter((s) => s.overflows)
          .every((s) => s.scrolledBy > 0),
        foundation.scrollers
          .map(
            (s) =>
              `${s.name}: ${s.overflows ? `overflows, scrolled ${s.scrolledBy}px` : "fits"}`,
          )
          .join("; "),
      ],
      [
        "the rail does not move when every table is scrolled to its end",
        foundation.railLeftBefore === foundation.railLeftAfterAll,
        `left ${foundation.railLeftBefore} -> ${foundation.railLeftAfterAll}`,
      ],
      ...(width <= 640
        ? [
            [
              "at least one table overflows here, so the claim above is not vacuous",
              foundation.scrollers.some((s) => s.overflows),
              `${foundation.scrollers.filter((s) => s.overflows).length} of ${foundation.scrollers.length} overflow`,
            ],
            [
              "the diagram overflows here too, so its scroll claim is not vacuous",
              foundation.diagrams.some((d) => d.overflows),
              foundation.diagrams
                .map((d) => (d.overflows ? "overflows" : "fits"))
                .join("; "),
            ],
          ]
        : []),
      [
        "no table renders a header row with no rows under it",
        foundation.scrollers.every((s) => s.columnCount === 0 || s.rowCount > 0),
        foundation.scrollers
          .map((s) => `${s.name}: ${s.columnCount} cols, ${s.rowCount} rows`)
          .join("; "),
      ],
      // T016 draws the configured diagram here. It has an intrinsic width the
      // content column does not have, so it is the one piece of content on
      // this page most able to push the rail sideways - and jsdom cannot see
      // any of that.
      [
        "the configured diagram is drawn, with nodes and connections",
        foundation.diagrams.length === 1 &&
          foundation.diagrams[0].nodes > 0 &&
          foundation.diagrams[0].connections > 0,
        foundation.diagrams
          .map((d) => `${d.nodes} nodes, ${d.connections} connections`)
          .join("; ") || "no diagram region",
      ],
      [
        "the drawing sits in a named, focusable region and carries a name",
        foundation.diagrams.every((d) => d.focusable && d.name && d.named),
        foundation.diagrams
          .map(
            (d) =>
              `${d.name ?? "unnamed"}: focusable ${d.focusable}, labelled ${d.named}`,
          )
          .join("; "),
      ],
      [
        "the diagram scrolls inside its own region when it overflows",
        foundation.diagrams
          .filter((d) => d.overflows)
          .every((d) => d.scrolledBy > 0),
        foundation.diagrams
          .map((d) =>
            d.overflows ? `overflows, scrolled ${d.scrolledBy}px` : "fits",
          )
          .join("; "),
      ],
      [
        "every drawn node carries an empty slot and nothing else",
        foundation.slots.length === (foundation.diagrams[0]?.nodes ?? -1) &&
          foundation.slots.every((slot) => slot === "Awaiting runtime/evidence"),
        `${foundation.slots.length} slots: ${[...new Set(foundation.slots)].join(" | ")}`,
      ],
      [
        "a drawn diagram and a refusal are never both on the page",
        (foundation.diagrams[0]?.nodes ?? 0) > 0
          ? foundation.diagramRefusals === 0
          : foundation.diagramRefusals === 1,
        `${foundation.diagrams[0]?.nodes ?? 0} nodes, ${foundation.diagramRefusals} refusals`,
      ],
    ]) && allPass;
}

const lab = await visit(cdp, "/simulator-lab", 1280, 800, ".app-frame");
allPass =
  report("Simulator Lab at 1280x800", lab, [
    [
      "the standalone Lab frame still fills the viewport",
      lab.frameHeight !== null && lab.frameHeight >= lab.viewportHeight,
      `frame ${lab.frameHeight}px vs viewport ${lab.viewportHeight}px`,
    ],
  ]) && allPass;

console.log(`\n${allPass ? "ALL CLAIMS HOLD" : "AT LEAST ONE CLAIM FAILED"}\n`);

ws.close();
chrome.kill();
try {
  rmSync(profile, { recursive: true, force: true });
} catch {
  /* Windows sometimes holds the profile briefly */
}
process.exit(allPass ? 0 : 1);
