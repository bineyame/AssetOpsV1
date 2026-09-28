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
  // The unsupported optional inputs, on the same terms as the disclosure.
  //
  // T020B lowers two forcing states to OPTIONAL so the shipped scenario can
  // reach READY, and the decision that permits it requires them to stay
  // VISIBLE. A READY run that recorded them and drew nothing would satisfy
  // "recorded" and defeat the point, because the whole argument for lowering
  // is that the run still says what the profile does not model. So the item
  // count is measured rather than the panel's existence.
  const optionalHeading = document.getElementById("run-optional-heading");
  const optionalPanel = optionalHeading
    ? optionalHeading.closest("section") || optionalHeading.parentElement
    : null;
  const optionalBox = optionalPanel
    ? optionalPanel.getBoundingClientRect()
    : null;
  const unsupportedOptional =
    optionalPanel === null
      ? null
      : {
          itemCount: optionalPanel.querySelectorAll("li").length,
          length: (optionalPanel.textContent || "").trim().length,
          visible: optionalBox.width > 0 && optionalBox.height > 0,
        };
  // T022: the execution panels. Read as ROWS with their own cells rather than
  // as page text, because the whole difficulty of this screen is that private
  // truth, a reported value and a retained reading sit inches apart. A
  // measurement over text would hold on a screen that merged the three columns.
  const executionStatusNode = document.querySelector("[data-execution-status]");
  const executionStatus = executionStatusNode
    ? executionStatusNode.getAttribute("data-execution-status")
    : null;
  const attributeOf = (row, attribute) => {
    const cell = row.querySelector("[" + attribute + "]");
    return cell ? cell.getAttribute(attribute) : null;
  };
  const cellText = (row, attribute) => {
    const cell = row.querySelector("[" + attribute + "]");
    return cell ? (cell.textContent || "").trim() : null;
  };
  const observationRows = Array.from(
    document.querySelectorAll("[data-observation]"),
  ).map((row) => ({
    signal: row.getAttribute("data-observation"),
    trueValue: cellText(row, "data-observation-true"),
    reported: cellText(row, "data-observation-reported"),
    sourceTime: cellText(row, "data-observation-source-time"),
    quality: attributeOf(row, "data-observation-quality"),
    outcome: attributeOf(row, "data-observation-outcome"),
  }));
  const privateStateRows = Array.from(
    document.querySelectorAll("[data-private-state]"),
  ).map((row) => ({
    address: row.getAttribute("data-private-state"),
    text: (row.textContent || "").trim(),
  }));
  const reportingGapRows = document.querySelectorAll("[data-reporting-gap]").length;
  const signalRows = document.querySelectorAll("[data-signal]").length;
  const sampleAttemptRows = document.querySelectorAll("[data-sample-attempt]").length;
  // The two digests, read off the fact list they are rendered in. Sixty-four
  // hexadecimal characters is what one looks like; a placeholder is not.
  const digestLeaves = Array.from(document.querySelectorAll("main dd"))
    .map((node) => (node.textContent || "").trim())
    .filter((value) => /^[0-9a-f]{64}$/.test(value));
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
    executionStatus,
    observationRows,
    privateStateRows,
    reportingGapRows,
    signalRows,
    sampleAttemptRows,
    digestLeaves,
    disclosure,
    unsupportedOptional,
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
    //
    // Three answers, not two, and the third is a wait rather than a failure.
    // `not-ready` means the form is there and its submit is still disabled,
    // which is what the run setup page does until the configured site has
    // been read. Clicking a disabled button silently does nothing, so the
    // old two-answer version posted nothing and then reported that the
    // summary never appeared - a race that reads exactly like a defect.
    let acted = "not-ready";
    for (let attempt = 0; attempt < 40 && acted === "not-ready"; attempt += 1) {
      if (attempt > 0) await sleep(250);
      const answer = await cdp.send("Runtime.evaluate", {
        expression: act.script,
        returnByValue: true,
      });
      acted = answer.result.value;
    }
    if (acted === "not-ready") {
      throw new Error(
        `The page action for ${path} found its submit still disabled after ` +
          "ten seconds, so nothing was submitted. The page never became " +
          "ready; it is not that the form is wrong.",
      );
    }
    if (acted !== true) {
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
  // A disabled submit is NOT-READY, not missing. The form disables it until
  // the configured site has been read, and clicking it then does nothing at
  // all: the run is never posted and the summary never renders, which
  // surfaced here as the summary "never appearing" and looked like a
  // rendering defect. Reporting it separately lets the caller wait for the
  // page rather than mistake a race for a broken screen.
  if (!filled || !submit) return "controls-missing";
  if (submit.disabled) return "not-ready";
  submit.click();
  return true;
})()`;

/**
 * Click one named control on the Draft screen, the way a person would.
 *
 * The three execution controls are found by their exact labels rather than by
 * position, so a renamed control fails loudly instead of driving whichever
 * button happened to be third.
 */
const clickControl = (label) =>
  `(() => {
  const control = Array.from(document.querySelectorAll('main button')).find(
    (button) => (button.textContent || '').trim() === ${JSON.stringify(label)},
  );
  if (!control) return 'controls-missing';
  if (control.disabled) return 'not-ready';
  control.click();
  return true;
})()`;

/**
 * Set the step size and step, which is how the owner crosses the fuel event.
 *
 * 104 boundaries at a fifteen-minute timestep lands the run at offset 1545:
 * inside the shipped reporting gap [1490, 1580) and past the removal
 * [1500, 1545). That is the instant the whole slice exists to make inspectable,
 * so it is the instant a browser is asked to draw.
 */
const STEP_ACROSS_THE_FUEL_EVENT = `(() => {
  const setNative = (prototype, element, value) => {
    const setter = Object.getOwnPropertyDescriptor(prototype, 'value').set;
    setter.call(element, value);
    element.dispatchEvent(new Event('input', { bubbles: true }));
  };
  const size = document.getElementById('run-step-boundaries');
  const step = Array.from(document.querySelectorAll('main button')).find(
    (button) => (button.textContent || '').trim() === 'Step',
  );
  if (!size || !step) return 'controls-missing';
  setNative(window.HTMLInputElement.prototype, size, '104');
  if (step.disabled) return 'not-ready';
  step.click();
  return true;
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
        // A lower bound on the table's shape, named as one.
        //
        // It said "names every reason the draft carries" while asserting a
        // floor, which an independent review called what it is: with five
        // reasons rendered the table could lose two and still pass. Renaming
        // it to mention the three unmodelled states was still a half-measure,
        // because this script never checks WHICH rows are there - the second
        // pass asked for the plain thing, so the claim now says row count and
        // column count and nothing about identity.
        //
        // Comparing identities would need the response this script does not
        // fetch. Until something does, the identities are covered by
        // `test_runs_api.py`, which asserts the exact reason set on the same
        // shipped scenario.
        //
        // The count itself is a joint fact about the shipped document, the
        // selected profile and the target Site's foundation, and all three
        // are allowed to move: T020A added two unresolved foundation values
        // to this Draft, because MG-001 was created before typed properties
        // existed and a template does not migrate a Site.
        //
        // T020B moved it the other way, from three to two, and this floor is
        // the thing that noticed. The three unmodelled-state reasons are gone:
        // two of those states are now declared OPTIONAL and are recorded
        // rather than blocking, and the third is the publication profile's to
        // answer and it answers. What is left is the two values MG-001's
        // Foundation does not declare, so two is the true count and not a
        // weakened floor. `test_runs_api.py` asserts that exact pair; the
        // measured number is printed below, so a later drift is visible in the
        // output rather than absorbed by the inequality.
        "the blocked table is at least two rows in three columns",
        blocked !== undefined &&
          blocked.columnCount === 3 &&
          blocked.rowCount >= 2,
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
// --- A Draft this build can execute ---------------------------------------
//
// The shipped Fuel Loss Event targets MG-001, and the MG-001 in this checkout
// was created from a template that predates the two Foundation properties the
// model profile binds to - so every Draft of it comes back BLOCKED, truthfully.
// That was fine while nothing executed: the READY measurements below ran against
// a READY Draft somebody had left in the store.
//
// T022 executes, and an execution needs a Draft frozen under THIS build's
// contract and publication profile. A Draft left behind by an earlier build is
// refused, correctly, so relying on one would measure the refusal rather than the
// slice. This creates one through the product path, from the user's own MG-006
// scenario - MG-006 declares both properties, so its Draft reaches READY - and
// the inventory below then finds it as the newest READY row.
const readySetup = await visit(
  cdp,
  "/simulator-lab/scenarios/fuel-loss-event-mg006/run-setup",
  1280,
  800,
  "form",
  // `.fact-list` is already on the page BEFORE the form is submitted, so
  // waiting for it returns instantly and the create lands seconds later - which
  // is exactly what happened the first time this ran, and the inventory below
  // then found a Draft from an earlier build instead of this one. The summary
  // table only exists after a Draft was created, so that is what is waited for.
  { script: SUBMIT_RUN_SETUP, waitFor: ".data-table__scroll" },
);
console.log(
  `\n=== Created a Draft for the execution measurements ===\n  ` +
    `run setup summary drawn with ${readySetup.scrollers.length} table(s)`,
);

let readyHref = null;
let blockedHref = null;

for (const [label, width, height] of [
  ["1280x800, the committed minimum", 1280, 800],
  ["1000x700, below the commitment", 1000, 700],
  ["640x700, narrow enough that the inventory cannot fit", 640, 700],
]) {
  const runs = await visit(cdp, "/simulator-lab/runs", width, height, "table");
  const inventory = runs.scrollers.find((s) => s.name === "runs-table-heading");

  // The NEWEST of each, re-read at every visit rather than latched at the
  // first. The inventory is newest first, so this is the Draft this run of the
  // script created - which is the only one frozen under this build's contract
  // and publication profile, and so the only one an execution measurement can
  // be made against.
  readyHref =
    runs.runRows.find((row) => row.status === "READY")?.href ?? readyHref;
  blockedHref =
    runs.runRows.find((row) => row.status === "BLOCKED")?.href ?? blockedHref;

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
              // T022 replaced the one disabled "Run this draft" control with
              // three real ones. The claim moves with it: a closed set by NAME,
              // and at least one of them enabled - because a ready draft whose
              // controls were all disabled would satisfy a count and assert
              // nothing about a Lab that can execute.
              "a ready draft offers exactly the three execution controls, at least one enabled",
              run.buttons.length === 3 &&
                run.buttons.map((b) => b.label).join("|") ===
                  "Start this run|Step|Run to the end" &&
                run.buttons.some((b) => !b.disabled),
              run.buttons
                .map((b) => `${b.label}:${b.disabled ? "disabled" : "ENABLED"}`)
                .join(", ") || "no button rendered",
            ],
        ...(expectBlockedTable
          ? []
          : [
              [
                // The floor is two because the shipped Fuel Loss Event
                // declares exactly two states this profile does not model, and
                // a READY run of it has to keep saying so. A panel drawn with
                // no items would pass "the panel exists" and assert nothing.
                "a ready draft still lists what the profile does not model",
                run.unsupportedOptional !== null &&
                  run.unsupportedOptional.visible &&
                  run.unsupportedOptional.itemCount >= 2,
                run.unsupportedOptional === null
                  ? "no optional-inputs panel"
                  : `${run.unsupportedOptional.itemCount} items, ` +
                    `${run.unsupportedOptional.length} characters, visible ` +
                    `${run.unsupportedOptional.visible}`,
              ],
            ]),
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

// --- The executed run, which is what T022 is for -------------------------
//
// jsdom has no layout, so no suite in this repository can see any of this. It is
// also the only place the slice's own demonstration is driven end to end through
// real input events: start a Draft, step it across the fuel event, and run it to
// the end, measuring what a browser actually drew at each stop.
//
// Every claim below is pinned to a CELL of a named row rather than to page text.
// Private truth, the reported value and a retained reading sit inches apart on
// this screen by construction, and a text assertion would hold on a screen that
// merged them - which is the defect this milestone has paid for five times.

const started = await visit(
  cdp,
  readyHref,
  1280,
  800,
  "[data-execution-status]",
  {
    script: clickControl("Start this run"),
    waitFor: "[data-execution-status='RUNNING']",
  },
);
allPass =
  report("Draft run started at 1280x800", started, [
    [
      "starting a draft leaves it RUNNING at its first boundary",
      started.executionStatus === "RUNNING",
      `status ${started.executionStatus}`,
    ],
    [
      // Starting is not stepping. No boundary has been run, so there is no
      // world at any instant and no sample has been taken - and the screen
      // draws neither rather than a zeroed clock and an empty reading, which
      // is the shape a shell that reads as a stopped runtime would have.
      "a started run has no world and no reading yet",
      started.privateStateRows.length === 0 &&
        started.observationRows.length === 0,
      `${started.privateStateRows.length} state rows, ` +
        `${started.observationRows.length} observation rows`,
    ],
    [
      // What IS drawn: what the profile declares and the document forces. Those
      // are facts about what WOULD be reported and do not wait on a boundary.
      "both configured reporting paths are drawn",
      started.signalRows === 2,
      `${started.signalRows} configured signal rows`,
    ],
    [
      "the declared reporting gap is drawn",
      started.reportingGapRows === 1,
      `${started.reportingGapRows} gap rows`,
    ],
    [
      "the page does not scroll horizontally",
      !started.pageScrollsHorizontally,
      `scrollWidth ${started.pageScrollWidth} vs clientWidth ${started.pageClientWidth}`,
    ],
  ]) && allPass;

for (const [label, width, height] of [
  ["1280x800, the committed minimum", 1280, 800],
  ["640x700, narrow enough that the observation table cannot fit", 640, 700],
]) {
  // The step is driven ONCE, at the first width. The run's position lives on
  // the server, so the second width re-measures the same instant rather than
  // stepping again - which advanced 208 boundaries of 165, finished the run,
  // and left the next block's control correctly disabled.
  const stepped = await visit(
    cdp,
    readyHref,
    width,
    height,
    "[data-observation]",
    width === 1280
      ? {
          script: STEP_ACROSS_THE_FUEL_EVENT,
          waitFor: "[data-observation-quality='STALE']",
        }
      : undefined,
  );
  const fuel = stepped.observationRows.find(
    (row) => row.signal === "fuel-level-sensor:fuel-level",
  );
  const tank = stepped.privateStateRows.find(
    (row) => row.address === "fuel-tank-volume@fuel-tank",
  );

  allPass =
    report(`Draft run stepped into the reporting gap at ${label}`, stepped, [
      [
        "the fuel sensor row is drawn at all",
        fuel !== undefined,
        stepped.observationRows.map((r) => r.signal).join(", ") || "no rows",
      ],
      [
        "the true value and the reported value are two different cells",
        fuel !== undefined &&
          fuel.trueValue !== null &&
          fuel.reported !== null &&
          fuel.trueValue !== fuel.reported,
        fuel === undefined
          ? "no fuel row"
          : `true ${fuel.trueValue} vs reported ${fuel.reported}`,
      ],
      [
        "the world holds 254.02 L after the removal",
        tank !== undefined && tank.text.includes("254.02"),
        tank === undefined ? "no tank row" : tank.text,
      ],
      [
        "the reading is the one taken before the gap opened, marked stale",
        fuel !== undefined &&
          fuel.quality === "STALE" &&
          fuel.outcome === "SUPPRESSED_BY_GAP" &&
          fuel.reported.startsWith("373.52"),
        fuel === undefined
          ? "no fuel row"
          : `${fuel.quality}/${fuel.outcome}, reported ${fuel.reported}`,
      ],
      [
        "the retained reading carries its own source time, not this instant",
        fuel !== undefined &&
          fuel.sourceTime !== null &&
          fuel.sourceTime.startsWith("2026-09-22T00:45"),
        fuel === undefined ? "no fuel row" : `source ${fuel.sourceTime}`,
      ],
      [
        "the newest sample attempts are drawn",
        stepped.sampleAttemptRows > 0,
        `${stepped.sampleAttemptRows} attempts`,
      ],
      [
        "the page does not scroll horizontally",
        !stepped.pageScrollsHorizontally,
        `scrollWidth ${stepped.pageScrollWidth} vs clientWidth ${stepped.pageClientWidth}`,
      ],
      [
        "every table that overflows scrolls inside its own region",
        stepped.scrollers
          .filter((s) => s.overflows)
          .every((s) => s.scrolledBy > 0),
        stepped.scrollers
          .map(
            (s) =>
              `${s.name}: ${s.overflows ? `overflows, scrolled ${s.scrolledBy}px` : "fits"}`,
          )
          .join("; "),
      ],
      ...(width <= 640
        ? [
            [
              "at least one table overflows here, so the claim above is not vacuous",
              stepped.scrollers.some((s) => s.overflows),
              `${stepped.scrollers.filter((s) => s.overflows).length} of ${stepped.scrollers.length} overflow`,
            ],
          ]
        : []),
    ]) && allPass;
}

const finished = await visit(
  cdp,
  readyHref,
  1280,
  800,
  "[data-execution-status]",
  {
    script: clickControl("Run to the end"),
    waitFor: "[data-execution-status='COMPLETED']",
  },
);
allPass =
  report("Draft run run to the end at 1280x800", finished, [
    [
      "the run reached a terminal outcome",
      finished.executionStatus === "COMPLETED",
      `status ${finished.executionStatus}`,
    ],
    [
      "both digests are drawn as real sixty-four character values",
      finished.digestLeaves.length >= 3,
      `${finished.digestLeaves.length} digest-shaped values`,
    ],
    [
      "the tank is at its capacity after the bounded delivery",
      finished.privateStateRows.some(
        (row) =>
          row.address === "fuel-tank-volume@fuel-tank" &&
          row.text.includes("500"),
      ),
      finished.privateStateRows.map((r) => r.text).join(" | ") || "no rows",
    ],
    [
      "a terminal run offers no enabled control",
      finished.buttons.length > 0 && finished.buttons.every((b) => b.disabled),
      finished.buttons
        .map((b) => `${b.label}:${b.disabled ? "disabled" : "ENABLED"}`)
        .join(", ") || "no button rendered",
    ],
    [
      "the page does not scroll horizontally",
      !finished.pageScrollsHorizontally,
      `scrollWidth ${finished.pageScrollWidth} vs clientWidth ${finished.pageClientWidth}`,
    ],
  ]) && allPass;

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
