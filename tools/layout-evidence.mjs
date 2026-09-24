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

/**
 * Which configured Site the site and Foundation claims are measured against.
 *
 * `MG-001` by default, which is what every earlier run used. It is an argument
 * because a claim is only about the content the page actually renders: a
 * Foundation section a site declares nothing for renders as a stated absence
 * and not as a table, so measuring table containment against that site is
 * measuring an empty set. A slice that adds a section measures it against a
 * site whose foundation declares one.
 */
const SITE = process.argv[3] ?? process.env.ASSETOPS_LAYOUT_SITE ?? "MG-001";
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
  // T017's checkpoint regions. A proposal that renders but has no box is a
  // proposal nobody can read, and "the screen carries a proposal" would then be
  // true of a page where all three were invisible.
  const proposalNodes = Array.from(
    document.querySelectorAll("[data-review-proposal]"),
  );
  const reviewProposals = proposalNodes.map((node) =>
    node.getAttribute("data-review-proposal"),
  );
  const reviewProposalsVisible = proposalNodes.filter((node) => {
    const box = node.getBoundingClientRect();
    return box.width > 0 && box.height > 0;
  }).length;
  const privateNodes = Array.from(
    document.querySelectorAll("[data-private-region]"),
  );
  const privateRegions = privateNodes.length;
  const privateRegionVisible =
    privateNodes.length > 0 &&
    privateNodes.every((node) => {
      const box = node.getBoundingClientRect();
      return box.width > 0 && box.height > 0;
    });
  const slots = Array.from(document.querySelectorAll(".sld-node__slot")).map((slot) =>
    (slot.textContent || "").trim(),
  );
  // T020's Runs inventory rows: where each row goes and what it says about
  // execution. A run identity is allocated per installation, so this script
  // cannot know one in advance; it reads the inventory and then follows the
  // rows, which is also how a person reaches a run.
  const runRows = Array.from(
    document.querySelectorAll('[aria-labelledby="runs-table-heading"] tbody tr'),
  ).map((row) => {
    const link = row.querySelector("a");
    const cells = Array.from(row.querySelectorAll("td")).map((cell) =>
      (cell.textContent || "").trim(),
    );
    return {
      href: link ? link.getAttribute("href") : null,
      // Site, Foundation, Scenario, Scenario version, Lifecycle, Execution.
      status: cells.length > 5 ? cells[5] : null,
    };
  });
  // The READY disclosure. Its presence is measured as rendered TEXT with a
  // real box rather than as a heading that exists: a panel collapsed to zero
  // height would satisfy "the screen says what READY does not assert" while
  // saying nothing at all.
  const disclosureHeading = document.getElementById("run-disclosure-heading");
  const disclosurePanel = disclosureHeading
    ? disclosureHeading.closest("section") || disclosureHeading.parentElement
    : null;
  const disclosureBox = disclosurePanel
    ? disclosurePanel.getBoundingClientRect()
    : null;
  const disclosure =
    disclosurePanel === null
      ? null
      : {
          length: (disclosurePanel.textContent || "").trim().length,
          visible: disclosureBox.width > 0 && disclosureBox.height > 0,
        };
  const railLeftAfterAll = rail ? Math.round(rail.getBoundingClientRect().left) : null;
  return {
    scrollers,
    diagrams,
    diagramRefusals,
    reviewProposals,
    reviewProposalsVisible,
    privateRegions,
    privateRegionVisible,
    slots,
    runRows,
    disclosure,
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

/**
 * Wait up to thirty seconds for a selector, not twelve.
 *
 * The run setup page is reached by submitting a form, and the create it posts
 * re-reads and re-parses every Draft in the local store twice to refuse a
 * duplicate identity. This script writes one Draft per visit and nothing
 * clears them, so on a developer machine that create is measured in seconds
 * and grows. At twelve seconds this aborted mid-run with a precondition
 * failure that looked like a defect and was a stopwatch.
 *
 * Raising a timeout weakens nothing: a page that never renders still fails,
 * and every claim below is still measured against what the browser drew.
 */
async function waitForSelector(cdp, selector) {
  for (let attempt = 0; attempt < 200; attempt += 1) {
    await sleep(150);
    const probe = await cdp.send("Runtime.evaluate", {
      expression: `document.querySelector(${JSON.stringify(selector)}) !== null`,
      returnByValue: true,
    });
    if (probe.result.value === true) return true;
  }
  return false;
}

async function visit(cdp, path, width, height, waitFor, act) {
  await cdp.send("Emulation.setDeviceMetricsOverride", {
    width,
    height,
    deviceScaleFactor: 1,
    mobile: false,
  });
  await cdp.send("Page.navigate", { url: `${BASE}${path}` });

  await waitForSelector(cdp, waitFor);
  await sleep(250);

  // Some pages only render the thing worth measuring after somebody does
  // something. `act` is that somebody: it fills a form and submits it through
  // real input events, then the page is waited on again before measuring.
  // Without it the run setup summary could not be measured at all, and "the
  // dense table scrolls inside its own region" would be a claim about a table
  // no browser had ever drawn.
  if (act) {
    // The script returns whether it found every control it meant to drive,
    // and that answer is checked rather than discarded. It was discarded in
    // the first version, so a renamed field or button would have produced a
    // page with no summary on it and the measurement below would have
    // reported an empty set of tables as a set that holds.
    const acted = await cdp.send("Runtime.evaluate", {
      expression: act.script,
      returnByValue: true,
    });
    if (acted.result.value !== true) {
      throw new Error(
        `The page action for ${path} did not find the controls it drives, ` +
          "so nothing was submitted and there is nothing to measure. The " +
          "form has changed and this script has not.",
      );
    }
    const appeared = await waitForSelector(cdp, act.waitFor);
    if (!appeared) {
      throw new Error(
        `The page action for ${path} ran and ${act.waitFor} never appeared. ` +
          "Measuring now would report on a page the action did not produce.",
      );
    }
    await sleep(250);
  }

  const result = await cdp.send("Runtime.evaluate", {
    expression: MEASURE,
    returnByValue: true,
  });
  return result.result.value;
}

/**
 * Fill the run setup form and submit it, the way a person would.
 *
 * React reads the value from its own state, so setting `element.value`
 * directly is invisible to it. The native setter plus a bubbling `input`
 * event is what a real keystroke does, and it is the only way to drive a
 * controlled input from outside React.
 *
 * The interval covers the whole shipped Fuel Loss Event - its last entry is a
 * point at two thousand four hundred minutes - and divides by the timestep,
 * so the request is structurally valid and the draft is created. It comes
 * back BLOCKED against the shipped model profile, which is the truthful
 * outcome for that scenario in this build and is exactly the state whose
 * layout needs measuring: the frozen summary AND the reasons are both on the
 * page at once.
 */
const SUBMIT_RUN_SETUP = `(() => {
  const setNative = (prototype, element, value) => {
    const setter = Object.getOwnPropertyDescriptor(prototype, "value").set;
    setter.call(element, value);
    element.dispatchEvent(new Event("input", { bubbles: true }));
    element.dispatchEvent(new Event("change", { bubbles: true }));
  };

  const setValue = (id, value) => {
    const element = document.getElementById(id);
    if (!element) return false;
    setNative(window.HTMLInputElement.prototype, element, value);
    return true;
  };

  // The two profiles are chosen here rather than assumed. Since T020 the form
  // does default them where there is exactly one option, and says in the
  // field that it did; choosing explicitly keeps this script measuring the
  // same submitted draft whether or not a second profile ever ships. The
  // first real option is taken - the leading one is the empty "choose" entry.
  const chooseFirst = (id) => {
    const element = document.getElementById(id);
    if (!element) return false;
    const option = Array.from(element.options).find((item) => item.value !== "");
    if (!option) return false;
    setNative(window.HTMLSelectElement.prototype, element, option.value);
    return true;
  };

  const filled =
    setValue("run-setup-start", "2026-09-21T00:00:00Z") &&
    setValue("run-setup-end", "2026-09-22T17:00:00Z") &&
    setValue("run-setup-timestep", "15") &&
    setValue("run-setup-seed", "20260921") &&
    chooseFirst("run-setup-model-profile") &&
    chooseFirst("run-setup-publication-profile");

  const submit = Array.from(document.querySelectorAll("main button")).find(
    (button) => (button.textContent || "").trim() === "Create draft run",
  );
  if (filled && submit) submit.click();
  return filled && Boolean(submit);
})()`;

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

  const site = await visit(cdp, `/sites/${SITE}`, width, height, ".site-tabs");
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
    `/sites/${SITE}/foundation`,
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

// The scenario detail. The event timeline is eight columns of dense content
// with an unbreakable description and a parameter list per row, so it is the
// same situation the Sites index and the Foundation relationship tables are
// in: it must keep every column and scroll inside its own region rather than
// pushing the rail sideways. jsdom cannot see any of that.
//
// 640px is measured for the reason T014 needed it: without a width where
// something actually overflows, "every table that overflows scrolls inside its
// own region" is a claim about an empty set, and it passes on a page whose
// regions do not scroll at all. The non-vacuity claim below asserts the set is
// not empty there.
for (const [label, width, height] of [
  ["1280x800, the committed minimum", 1280, 800],
  ["1000x700, below the commitment", 1000, 700],
  ["640x700, narrow enough that the timeline cannot fit", 640, 700],
]) {
  const scenario = await visit(
    cdp,
    "/simulator-lab/scenarios/fuel-loss-event",
    width,
    height,
    ".review-proposal",
  );

  allPass =
    report(`Scenario detail at ${label}`, scenario, [
      [
        "the page does not scroll horizontally",
        !scenario.pageScrollsHorizontally,
        `scrollWidth ${scenario.pageScrollWidth} vs clientWidth ${scenario.pageClientWidth}`,
      ],
      [
        "every table on the page has a named, focusable overflow region",
        scenario.scrollers.length > 0 &&
          scenario.scrollers.every((s) => s.focusable && s.name),
        scenario.scrollers.map((s) => s.name ?? "unnamed").join(", "),
      ],
      [
        "every table that overflows scrolls inside its own region",
        scenario.scrollers
          .filter((s) => s.overflows)
          .every((s) => s.scrolledBy > 0),
        scenario.scrollers
          .map(
            (s) =>
              `${s.name}: ${s.overflows ? `overflows, scrolled ${s.scrolledBy}px` : "fits"}`,
          )
          .join("; "),
      ],
      [
        "the rail does not move when every table is scrolled to its end",
        scenario.railLeftBefore === scenario.railLeftAfterAll,
        `left ${scenario.railLeftBefore} -> ${scenario.railLeftAfterAll}`,
      ],
      [
        "no table renders a header row with no rows under it",
        scenario.scrollers.every((s) => s.columnCount === 0 || s.rowCount > 0),
        scenario.scrollers
          .map((s) => `${s.name}: ${s.columnCount} cols, ${s.rowCount} rows`)
          .join("; "),
      ],
      [
        // Eight since T018: the execution role and the timing shape are
        // columns rather than prose, because a later run setup reads them as
        // fields and a reviewer has to be able to see the same thing.
        "the timeline keeps all eight of its columns",
        scenario.scrollers.some((s) => s.columnCount === 8),
        scenario.scrollers.map((s) => `${s.name}: ${s.columnCount}`).join("; "),
      ],
      [
        "all four review proposals are on the page",
        scenario.reviewProposals.length === 4,
        scenario.reviewProposals.join(" | ") || "none",
      ],
      [
        "every review proposal is visible, not collapsed or clipped away",
        scenario.reviewProposals.length > 0 &&
          scenario.reviewProposalsVisible === scenario.reviewProposals.length,
        `${scenario.reviewProposalsVisible} of ${scenario.reviewProposals.length} have a non-zero box`,
      ],
      [
        "the private expectations region is on the page and visible",
        scenario.privateRegionVisible === true,
        `${scenario.privateRegions} region(s), visible ${scenario.privateRegionVisible}`,
      ],
      [
        // Measured over buttons. The one enabled control this screen may carry
        // is the target-site LINK, which is an anchor rather than a button
        // precisely because following it is navigation, so it is deliberately
        // outside this set. Which states enable it is covered by the UI suite.
        "no enabled button renders",
        scenario.buttons.every((b) => b.disabled),
        scenario.buttons.length === 0
          ? "no button rendered"
          : scenario.buttons
              .map((b) => `${b.label}:${b.disabled ? "disabled" : "ENABLED"}`)
              .join(", "),
      ],
      ...(width <= 640
        ? [
            [
              "at least one table overflows here, so the claim above is not vacuous",
              scenario.scrollers.some((s) => s.overflows),
              `${scenario.scrollers.filter((s) => s.overflows).length} of ${scenario.scrollers.length} overflow`,
            ],
          ]
        : []),
    ]) && allPass;
}

const scenarios = await visit(
  cdp,
  "/simulator-lab/scenarios",
  1280,
  800,
  "table",
);
allPass =
  report("Scenario catalog at 1280x800", scenarios, [
    [
      "the page does not scroll horizontally",
      !scenarios.pageScrollsHorizontally,
      `scrollWidth ${scenarios.pageScrollWidth} vs clientWidth ${scenarios.pageClientWidth}`,
    ],
    [
      "the catalog renders a row from the real scenario store",
      scenarios.scrollers.some((s) => s.rowCount > 0),
      scenarios.scrollers
        .map((s) => `${s.name}: ${s.rowCount} rows`)
        .join("; ") || "no table",
    ],
    [
      "the rail does not move when the table is scrolled",
      scenarios.railLeftBefore === scenarios.railLeftAfterAll,
      `left ${scenarios.railLeftBefore} -> ${scenarios.railLeftAfterAll}`,
    ],
  ]) && allPass;

// T019's run setup summary. It is the densest table the Lab has: four
// columns, an unbreakable identity in one of them and a whole sentence in
// another, and it only exists after a form has been submitted - so it is
// reached here by filling the form rather than by navigating to it.
//
// 640px is measured for the reason every other dense table is measured there:
// without a width at which something actually overflows, "every table that
// overflows scrolls inside its own region" is a claim about an empty set.
for (const [label, width, height] of [
  ["1280x800, the committed minimum", 1280, 800],
  ["1000x700, below the commitment", 1000, 700],
  ["640x700, narrow enough that the summary cannot fit", 640, 700],
]) {
  const setup = await visit(
    cdp,
    "/simulator-lab/scenarios/fuel-loss-event/run-setup",
    width,
    height,
    "form",
    { script: SUBMIT_RUN_SETUP, waitFor: ".data-table__scroll" },
  );

  // The two tables by name. `scrollers.some(...)` would let one table's
  // shape satisfy a claim written about the other.
  const frozen = setup.scrollers.find(
    (s) => s.name === "run-setup-frozen-heading",
  );
  const blocked = setup.scrollers.find(
    (s) => s.name === "run-setup-blocked-heading",
  );

  allPass =
    report(`Run setup summary at ${label}`, setup, [
      [
        "the page does not scroll horizontally",
        !setup.pageScrollsHorizontally,
        `scrollWidth ${setup.pageScrollWidth} vs clientWidth ${setup.pageClientWidth}`,
      ],
      [
        "the frozen summary was drawn at all",
        setup.scrollers.length > 0,
        `${setup.scrollers.length} table region(s)`,
      ],
      [
        "every table on the page has a named, focusable overflow region",
        setup.scrollers.length > 0 &&
          setup.scrollers.every((s) => s.focusable && s.name),
        setup.scrollers.map((s) => s.name ?? "unnamed").join(", "),
      ],
      [
        "every table that overflows scrolls inside its own region",
        setup.scrollers.filter((s) => s.overflows).every((s) => s.scrolledBy > 0),
        setup.scrollers
          .map(
            (s) =>
              `${s.name}: ${s.overflows ? `overflows, scrolled ${s.scrolledBy}px` : "fits"}`,
          )
          .join("; "),
      ],
      [
        "the rail does not move when every table is scrolled to its end",
        setup.railLeftBefore === setup.railLeftAfterAll,
        `left ${setup.railLeftBefore} -> ${setup.railLeftAfterAll}`,
      ],
      [
        "no table renders a header row with no rows under it",
        setup.scrollers.every((s) => s.columnCount === 0 || s.rowCount > 0),
        setup.scrollers
          .map((s) => `${s.name}: ${s.columnCount} cols, ${s.rowCount} rows`)
          .join("; "),
      ],
      // Named rather than "some table has four columns", which the blocked
      // table could have satisfied by accident once it grew a column. The
      // row count is asserted for the same reason the column count is: a
      // frozen summary with a header and one row would satisfy every claim
      // above it, and it is not a frozen summary.
      [
        "the frozen input table keeps all four of its columns",
        frozen !== undefined && frozen.columnCount === 4,
        frozen === undefined
          ? "no region named run-setup-frozen-heading"
          : `${frozen.name}: ${frozen.columnCount} columns`,
      ],
      [
        "the frozen input table renders a row for every frozen value",
        frozen !== undefined && frozen.rowCount >= 20,
        frozen === undefined
          ? "no region named run-setup-frozen-heading"
          : `${frozen.name}: ${frozen.rowCount} rows`,
      ],
      [
        // Three columns and at least three rows, and the claim is named for
        // what that measures rather than for what it would be nice to know.
        //
        // It said "names every reason the draft carries" while asserting a
        // floor, which an independent review called what it is: with five
        // reasons rendered the table could lose two and still pass. This
        // script cannot see the response, so it cannot compare identities;
        // what it can say is that the table is still a table and still has
        // at least the three states the shipped profile cannot model.
        //
        // The count itself is a joint fact about the shipped document, the
        // selected profile and the target Site's foundation, and all three
        // are allowed to move: T020A added two unresolved foundation values
        // to this Draft, because MG-001 was created before typed properties
        // existed and a template does not migrate a Site.
        "the blocked table renders at least the three unmodelled-state rows",
        blocked !== undefined &&
          blocked.columnCount === 3 &&
          blocked.rowCount >= 3,
        blocked === undefined
          ? "no region named run-setup-blocked-heading"
          : `${blocked.name}: ${blocked.columnCount} columns, ${blocked.rowCount} rows`,
      ],
      ...(width <= 640
        ? [
            [
              "at least one table overflows here, so the claim above is not vacuous",
              setup.scrollers.some((s) => s.overflows),
              `${setup.scrollers.filter((s) => s.overflows).length} of ${setup.scrollers.length} overflow`,
            ],
          ]
        : []),
    ]) && allPass;
}

// T020's Runs inventory. Ten columns, two of them unbreakable identities, and
// it is the first Lab screen whose row count grows with use. Measured at the
// same three widths as every other dense table, for the same reason: without
// a width at which something overflows, "every table that overflows scrolls
// inside its own region" is a claim about an empty set.
//
// The two run detail measurements below are reached from here rather than
// from a literal address, because a run identity is allocated per
// installation and this script cannot know one in advance.
let readyHref = null;
let blockedHref = null;

for (const [label, width, height] of [
  ["1280x800, the committed minimum", 1280, 800],
  ["1000x700, below the commitment", 1000, 700],
  ["640x700, narrow enough that the inventory cannot fit", 640, 700],
]) {
  const runs = await visit(cdp, "/simulator-lab/runs", width, height, "table");
  const inventory = runs.scrollers.find((s) => s.name === "runs-table-heading");

  readyHref =
    readyHref ??
    runs.runRows.find((row) => row.status === "READY")?.href ??
    null;
  blockedHref =
    blockedHref ??
    runs.runRows.find((row) => row.status === "BLOCKED")?.href ??
    null;

  allPass =
    report(`Runs inventory at ${label}`, runs, [
      [
        "the page does not scroll horizontally",
        !runs.pageScrollsHorizontally,
        `scrollWidth ${runs.pageScrollWidth} vs clientWidth ${runs.pageClientWidth}`,
      ],
      [
        "every table on the page has a named, focusable overflow region",
        runs.scrollers.length > 0 &&
          runs.scrollers.every((s) => s.focusable && s.name),
        runs.scrollers.map((s) => s.name ?? "unnamed").join(", "),
      ],
      [
        "every table that overflows scrolls inside its own region",
        runs.scrollers.filter((s) => s.overflows).every((s) => s.scrolledBy > 0),
        runs.scrollers
          .map(
            (s) =>
              `${s.name}: ${s.overflows ? `overflows, scrolled ${s.scrolledBy}px` : "fits"}`,
          )
          .join("; "),
      ],
      [
        "the rail does not move when the inventory is scrolled to its end",
        runs.railLeftBefore === runs.railLeftAfterAll,
        `left ${runs.railLeftBefore} -> ${runs.railLeftAfterAll}`,
      ],
      [
        "the inventory keeps all ten of its columns",
        inventory !== undefined && inventory.columnCount === 10,
        inventory === undefined
          ? "no region named runs-table-heading"
          : `${inventory.columnCount} columns`,
      ],
      [
        "the inventory renders a row from the real run store",
        inventory !== undefined && inventory.rowCount > 0,
        inventory === undefined
          ? "no region named runs-table-heading"
          : `${inventory.rowCount} rows`,
      ],
      [
        "no table renders a header row with no rows under it",
        runs.scrollers.every((s) => s.columnCount === 0 || s.rowCount > 0),
        runs.scrollers
          .map((s) => `${s.name}: ${s.columnCount} cols, ${s.rowCount} rows`)
          .join("; "),
      ],
      [
        // Stronger than "no enabled button": the inventory is a list of
        // records and there is nothing on it to operate at all.
        "the inventory offers no button of any kind",
        runs.buttons.length === 0,
        runs.buttons.map((b) => b.label).join(", ") || "no button rendered",
      ],
      ...(width <= 640
        ? [
            [
              "at least one table overflows here, so the claim above is not vacuous",
              runs.scrollers.some((s) => s.overflows),
              `${runs.scrollers.filter((s) => s.overflows).length} of ${runs.scrollers.length} overflow`,
            ],
          ]
        : []),
    ]) && allPass;
}

// Both run states have to be on the page for the two measurements below to
// mean anything. A missing one is a failure rather than a skip: a skipped
// READY measurement would leave "the disclosure is visible" as a claim about
// a page no browser drew, which is the exact failure mode every non-vacuity
// claim in this file exists to prevent.
if (readyHref === null || blockedHref === null) {
  throw new Error(
    "The run store does not hold both a READY and a BLOCKED draft, so the " +
      `two run detail measurements cannot be made (READY ${readyHref}, ` +
      `BLOCKED ${blockedHref}). No READY run is reachable through the ` +
      "product path in this build; one is written through the SimulationRun " +
      "port as a fixture.",
  );
}

for (const [state, href, expectBlockedTable] of [
  ["READY", readyHref, false],
  ["BLOCKED", blockedHref, true],
]) {
  for (const [label, width, height] of [
    ["1280x800, the committed minimum", 1280, 800],
    ["1000x700, below the commitment", 1000, 700],
    ["640x700, narrow enough that the frozen table cannot fit", 640, 700],
  ]) {
    const run = await visit(cdp, href, width, height, ".fact-list");
    const frozen = run.scrollers.find((s) => s.name === "run-frozen-heading");
    const blocked = run.scrollers.find((s) => s.name === "run-blocked-heading");

    allPass =
      report(`${state} draft run at ${label}`, run, [
        [
          // The claim that catches an unbreakable run identity in the fact
          // list, which is exactly how T019 broke this page at 640px.
          "the page does not scroll horizontally",
          !run.pageScrollsHorizontally,
          `scrollWidth ${run.pageScrollWidth} vs clientWidth ${run.pageClientWidth}`,
        ],
        [
          "every table on the page has a named, focusable overflow region",
          run.scrollers.length > 0 &&
            run.scrollers.every((s) => s.focusable && s.name),
          run.scrollers.map((s) => s.name ?? "unnamed").join(", "),
        ],
        [
          "every table that overflows scrolls inside its own region",
          run.scrollers.filter((s) => s.overflows).every((s) => s.scrolledBy > 0),
          run.scrollers
            .map(
              (s) =>
                `${s.name}: ${s.overflows ? `overflows, scrolled ${s.scrolledBy}px` : "fits"}`,
            )
            .join("; "),
        ],
        [
          "the rail does not move when every table is scrolled to its end",
          run.railLeftBefore === run.railLeftAfterAll,
          `left ${run.railLeftBefore} -> ${run.railLeftAfterAll}`,
        ],
        [
          "the frozen input table keeps all four of its columns",
          frozen !== undefined && frozen.columnCount === 4,
          frozen === undefined
            ? "no region named run-frozen-heading"
            : `${frozen.columnCount} columns`,
        ],
        [
          "the frozen input table renders a row for every frozen value",
          frozen !== undefined && frozen.rowCount >= 20,
          frozen === undefined
            ? "no region named run-frozen-heading"
            : `${frozen.rowCount} rows`,
        ],
        [
          "no table renders a header row with no rows under it",
          run.scrollers.every((s) => s.columnCount === 0 || s.rowCount > 0),
          run.scrollers
            .map((s) => `${s.name}: ${s.columnCount} cols, ${s.rowCount} rows`)
            .join("; "),
        ],
        expectBlockedTable
          ? [
              "the blocked table names every reason the draft carries",
              blocked !== undefined &&
                blocked.columnCount === 3 &&
                blocked.rowCount > 0,
              blocked === undefined
                ? "no region named run-blocked-heading"
                : `${blocked.columnCount} columns, ${blocked.rowCount} rows`,
            ]
          : [
              "a ready draft carries no blocked table",
              blocked === undefined,
              blocked === undefined
                ? "absent"
                : `${blocked.rowCount} rows on a READY run`,
            ],
        expectBlockedTable
          ? [
              // The disclosure qualifies READY. On a blocked draft there is
              // no READY to qualify, and a panel about it would be a screen
              // discussing a status the record does not hold.
              "a blocked draft carries no readiness disclosure",
              run.disclosure === null,
              run.disclosure === null
                ? "absent"
                : `${run.disclosure.length} characters`,
            ]
          : [
              "the readiness disclosure is drawn, with a real box and real text",
              run.disclosure !== null &&
                run.disclosure.visible &&
                run.disclosure.length > 200,
              run.disclosure === null
                ? "no disclosure panel"
                : `${run.disclosure.length} characters, visible ${run.disclosure.visible}`,
            ],
        expectBlockedTable
          ? [
              // A blocked draft cannot be run for a second, prior reason, so
              // the same disabled button on both would say the two are the
              // same distance from working.
              "a blocked draft offers no run action at all",
              run.buttons.length === 0,
              run.buttons.map((b) => b.label).join(", ") || "no button rendered",
            ]
          : [
              "the one action on a ready draft is rendered and disabled",
              run.buttons.length === 1 && run.buttons[0].disabled,
              run.buttons
                .map((b) => `${b.label}:${b.disabled ? "disabled" : "ENABLED"}`)
                .join(", ") || "no button rendered",
            ],
        ...(width <= 640
          ? [
              [
                "at least one table overflows here, so the claim above is not vacuous",
                run.scrollers.some((s) => s.overflows),
                `${run.scrollers.filter((s) => s.overflows).length} of ${run.scrollers.length} overflow`,
              ],
            ]
          : []),
      ]) && allPass;
  }
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
