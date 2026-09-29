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

  // Every request is bounded. A reply that never arrives - a crashed renderer,
  // a detached target, a socket that closed without an event - used to leave
  // this promise pending forever, and the run simply stopped: no output, no
  // error, no exit. A measurement harness that stalls silently is the same
  // defect as a guard that cannot fail, one layer out. It now fails loudly and
  // names the request it was waiting on.
  send(method, params = {}, timeoutMs = 60000) {
    this.id += 1;
    const id = this.id;
    return new Promise((resolve, reject) => {
      const timer = setTimeout(() => {
        this.pending.delete(id);
        reject(
          new Error(
            `CDP ${method} (#${id}) got no reply within ${timeoutMs}ms. The ` +
              "browser stopped answering - most often a renderer that ran out " +
              "of memory on a very large page. Nothing below this point was " +
              "measured.",
          ),
        );
      }, timeoutMs);
      this.pending.set(id, {
        resolve: (value) => {
          clearTimeout(timer);
          resolve(value);
        },
        reject: (error) => {
          clearTimeout(timer);
          reject(error);
        },
      });
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
  const simulationTimeNode = document.querySelector(
    "[data-execution-simulation-time]",
  );
  const simulationTime = simulationTimeNode
    ? simulationTimeNode.getAttribute("data-execution-simulation-time")
    : null;
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
  // The gap row's own cells. The declared instant and the span it resolves to
  // are separate columns, because for a POINT they differ: an entry declared at
  // offset 1490 in a fifteen-minute run silences the sample at 1485. The
  // shipped entry is a WINDOW, where the two coincide - so what a browser can
  // prove here is that the surface carries both, which is the half a jsdom
  // fixture cannot vouch for.
  const gapRow = document.querySelector("[data-reporting-gap]");
  const reportingGapCells = gapRow
    ? Array.from(gapRow.querySelectorAll("th, td")).map((cell) =>
        (cell.textContent || "").trim(),
      )
    : [];
  const reportingGapDeclaredAt = gapRow
    ? (
        gapRow.querySelector("[data-reporting-gap-declared-at]")?.textContent ||
        ""
      ).trim()
    : null;
  const signalRows = document.querySelectorAll("[data-signal]").length;
  const sampleAttemptRows = document.querySelectorAll("[data-sample-attempt]").length;
  // The two digests, read off the fact list they are rendered in. Sixty-four
  // hexadecimal characters is what one looks like; a placeholder is not.
  const digestLeaves = Array.from(document.querySelectorAll("main dd"))
    .map((node) => (node.textContent || "").trim())
    .filter((value) => /^[0-9a-f]{64}$/.test(value));
  // T023: the stage inspector. Read off its own attributes and cells, because
  // a source time and a publication time three seconds apart sit side by side
  // and a text match would hold with the two columns swapped.
  const stageNode = document.querySelector("[data-stage-statement]");
  const stageStatus = stageNode ? stageNode.getAttribute("data-stage-status") : null;
  const stageCount = stageNode
    ? Number(stageNode.getAttribute("data-stage-count"))
    : null;
  const stageReleaseNode = document.querySelector("[data-stage-release]");
  const stageRelease = stageReleaseNode
    ? stageReleaseNode.getAttribute("data-stage-release")
    : null;
  const stagedRows = Array.from(
    document.querySelectorAll("[data-staged-envelope]"),
  ).map((row) => ({
    id: row.getAttribute("data-staged-envelope"),
    sourceTime: cellText(row, "data-staged-source-time"),
    publishedAt: cellText(row, "data-staged-published-at"),
    value: cellText(row, "data-staged-value"),
  }));
  // The exact canonical text. Its box is measured, not only its presence: a
  // single line several hundred characters long with break opportunities only
  // at punctuation is exactly the content that pushes a page sideways, and a
  // pre that rendered with no box would be exact text nobody can read.
  const canonicalNode = document.querySelector("pre.canonical-text");
  let canonical = null;
  if (canonicalNode) {
    const box = canonicalNode.getBoundingClientRect();
    const text = canonicalNode.textContent || "";
    const lineHeight = parseFloat(getComputedStyle(canonicalNode).lineHeight) || 20;
    let parses = false;
    try {
      JSON.parse(text);
      parses = true;
    } catch (error) {
      parses = false;
    }
    canonical = {
      id: canonicalNode.getAttribute("data-stage-canonical"),
      text,
      length: text.length,
      width: Math.round(box.width),
      height: Math.round(box.height),
      overflows: canonicalNode.scrollWidth > canonicalNode.clientWidth,
      wraps: box.height > 2 * lineHeight,
      parses,
    };
  }
  const railLeftAfterAll = rail ? Math.round(rail.getBoundingClientRect().left) : null;
  return {
    stageStatus,
    stageCount,
    stageRelease,
    stagedRows,
    canonical,
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
    simulationTime,
    observationRows,
    privateStateRows,
    reportingGapRows,
    reportingGapCells,
    reportingGapDeclaredAt,
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
        // Three since T022, not four. The fourth was the reconciliation
        // panel's, and it went with the panel under
        // `D-2026-09-22-reconciliation-panel-retirement`: a checkpoint asking
        // what to do about a difference this build no longer computes would
        // be a question nobody can answer. Named rather than counted, so a
        // renamed or missing proposal fails on which one rather than on how
        // many.
        "the three review proposals are on the page, by name",
        scenario.reviewProposals.join("|") ===
          "scenario-execution-roles|scenario-input-ownership|scenario-timing-and-bounds",
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
    // `[data-execution-status]` rather than `.fact-list`, and the difference
    // is the same race `settledScreen` exists for in jsdom. This screen makes
    // TWO reads - the persisted Draft and its execution - and `.fact-list`
    // appears when the first lands. At 1280 and 1000 the second landed inside
    // the settle pause and at 640 it did not, so one width measured a screen
    // that had not finished loading and reported no controls. Waiting for
    // something only the second read draws is what makes all three widths
    // measure the same screen.
    const run = await visit(cdp, href, width, height, "[data-execution-status]");
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
      // Six cells, not five. The declared instant and the covered span are two
      // columns, and one column carrying the resolved start under a heading
      // promising the authored number is what this replaced.
      "the gap row carries the declared instant beside the span it covers",
      started.reportingGapCells.length === 6 &&
        started.reportingGapDeclaredAt === "1490",
      `${started.reportingGapCells.length} cells, declared at ${started.reportingGapDeclaredAt}: ${started.reportingGapCells.join(" | ")}`,
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
  // Both waits require the readings AND the stage, because the screen reads
  // them separately and the stage is re-read after the step returns. Waiting on
  // the readings alone would measure a stage inspector still showing the stage
  // from before the step.
  const stepped = await visit(
    cdp,
    readyHref,
    width,
    height,
    width === 1280
      ? "[data-observation]"
      : "main:has([data-observation]) [data-staged-envelope]",
    width === 1280
      ? {
          script: STEP_ACROSS_THE_FUEL_EVENT,
          waitFor:
            "main:has([data-observation-quality='STALE']) " +
            "[data-stage-count]:not([data-stage-count='0'])",
        }
      : undefined,
  );
  const newestStaged = stepped.stagedRows[stepped.stagedRows.length - 1];
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
        // The RELATIONSHIP, not a hard-coded timestamp. Which sample the
        // retained reading came from depends on the run's seed and on the draw
        // identity - correcting that identity moved it from 1485 to 1470 here -
        // and a claim naming one instant would be a claim about a particular
        // draw outcome rather than about the mechanism. What must hold is that
        // the reading is older than now and was taken before the gap opened.
        "the retained reading carries its own source time, earlier than this instant and before the gap",
        fuel !== undefined &&
          fuel.sourceTime !== null &&
          fuel.sourceTime !== stepped.simulationTime &&
          fuel.sourceTime < (stepped.simulationTime ?? "") &&
          fuel.sourceTime < "2026-09-22T00:50",
        fuel === undefined
          ? "no fuel row"
          : `source ${fuel.sourceTime}, now ${stepped.simulationTime}`,
      ],
      [
        "the newest sample attempts are drawn",
        stepped.sampleAttemptRows > 0,
        `${stepped.sampleAttemptRows} attempts`,
      ],
      [
        // T023. The non-empty set first, so every stage claim below is about
        // rows a browser actually drew.
        "the stage inspector draws every staged envelope, and there are some",
        stepped.stageStatus === "STAGED" &&
          stepped.stagedRows.length > 0 &&
          stepped.stagedRows.length === stepped.stageCount,
        `${stepped.stageStatus}, ${stepped.stagedRows.length} rows drawn of ${stepped.stageCount} staged`,
      ],
      [
        "the newest staged envelope is the last reading before the gap, published after its source time",
        newestStaged !== undefined &&
          newestStaged.sourceTime < "2026-09-22T00:50" &&
          newestStaged.publishedAt > newestStaged.sourceTime &&
          (newestStaged.value ?? "").startsWith("373.52"),
        newestStaged === undefined
          ? "no staged row"
          : `source ${newestStaged.sourceTime}, published ${newestStaged.publishedAt}, value ${newestStaged.value}`,
      ],
      [
        "no envelope is staged at an instant inside the reporting gap",
        stepped.stagedRows.every(
          (row) =>
            !(
              row.sourceTime >= "2026-09-22T00:50" &&
              row.sourceTime < "2026-09-22T02:20"
            ),
        ),
        `${stepped.stagedRows.filter((row) => row.sourceTime >= "2026-09-22T00:50").length} rows at or after the gap opened`,
      ],
      [
        "the exact canonical text is drawn, parses, wraps, and stays inside its box",
        stepped.canonical !== null &&
          newestStaged !== undefined &&
          stepped.canonical.id === newestStaged.id &&
          stepped.canonical.width > 0 &&
          stepped.canonical.height > 0 &&
          stepped.canonical.parses &&
          stepped.canonical.wraps &&
          !stepped.canonical.overflows,
        stepped.canonical === null
          ? "no canonical text drawn"
          : `${stepped.canonical.length} characters in ${stepped.canonical.width}x${stepped.canonical.height}px, ` +
            `${stepped.canonical.parses ? "parses" : "DOES NOT PARSE"}, ` +
            `${stepped.canonical.wraps ? "wraps" : "one line"}, ` +
            `${stepped.canonical.overflows ? "OVERFLOWS" : "contained"}`,
      ],
      [
        "a stage whose execution is still running is not eligible for release",
        stepped.stageRelease === "NOT_ELIGIBLE",
        `release ${stepped.stageRelease}`,
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
    // The stage is re-read after the control returns, so wait for the stage
    // to say its execution completed as well as the execution panel.
    waitFor:
      "main:has([data-execution-status='COMPLETED']) " +
      "[data-stage-execution='COMPLETED']",
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
      // The EXECUTION controls. Since T023 the stage inspector renders one
      // enabled button per staged envelope, and it chooses which envelope's
      // exact text to read - it changes nothing on the server. They are
      // excluded by their exact label shape, so any other enabled button still
      // fails this claim.
      "a terminal run offers no enabled execution control",
      finished.buttons.some((b) => !/^Show envelope \d+$/.test(b.label)) &&
        finished.buttons
          .filter((b) => !/^Show envelope \d+$/.test(b.label))
          .every((b) => b.disabled),
      finished.buttons
        .filter((b) => !/^Show envelope \d+$/.test(b.label))
        .map((b) => `${b.label}:${b.disabled ? "disabled" : "ENABLED"}`)
        .join(", ") || "no execution control rendered",
    ],
    [
      "a completed run's verified stage is eligible for release",
      finished.stageRelease === "ELIGIBLE" && finished.stagedRows.length > 100,
      `release ${finished.stageRelease}, ${finished.stagedRows.length} envelopes`,
    ],
    [
      "the page does not scroll horizontally",
      !finished.pageScrollsHorizontally,
      `scrollWidth ${finished.pageScrollWidth} vs clientWidth ${finished.pageClientWidth}`,
    ],
  ]) && allPass;

// A fresh page load, at the narrow width: nothing the screen held survives a
// navigation, so what it shows is what the persisted stage reads back as. The
// owner's "reload the exact payload", made by a browser.
const reloaded = await visit(
  cdp,
  readyHref,
  640,
  700,
  "main:has([data-execution-status='COMPLETED']) [data-staged-envelope]",
);
allPass =
  report("Draft run stage reloaded at 640x700", reloaded, [
    [
      "the reloaded stage holds the same envelopes",
      reloaded.stagedRows.length === finished.stagedRows.length &&
        reloaded.stagedRows.every(
          (row, index) => row.id === finished.stagedRows[index]?.id,
        ),
      `${reloaded.stagedRows.length} rows after reload vs ${finished.stagedRows.length} before`,
    ],
    [
      "the reloaded exact text is byte for byte the text shown before",
      reloaded.canonical !== null &&
        finished.canonical !== null &&
        reloaded.canonical.text === finished.canonical.text,
      reloaded.canonical === null
        ? "no canonical text drawn"
        : `${reloaded.canonical.length} characters, ` +
          `${reloaded.canonical.text === finished.canonical?.text ? "identical" : "DIFFERENT"}`,
    ],
    [
      "the long canonical text stays inside its box at 640px",
      reloaded.canonical !== null &&
        reloaded.canonical.wraps &&
        !reloaded.canonical.overflows,
      reloaded.canonical === null
        ? "no canonical text drawn"
        : `${reloaded.canonical.width}x${reloaded.canonical.height}px`,
    ],
    [
      "the page does not scroll horizontally",
      !reloaded.pageScrollsHorizontally,
      `scrollWidth ${reloaded.pageScrollWidth} vs clientWidth ${reloaded.pageClientWidth}`,
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

// --- T024: the daytime mini-grid on the Draft screen ------------------------
//
// Measured against a Kobo Draft created here through the product path, from
// the shipped `kobo-daytime-overcast` scenario, against the Site `KOBO-001`
// created from the `kobo-mini-grid-60kw` template (it must exist; this script
// creates no Site). The run is stepped to offset 600, where the evening reserve
// override is in effect and the battery is serving the evening deficit, so
// every electrical table has rows and the series table has forty-one.
const KOBO_SITE = process.env.ASSETOPS_KOBO_SITE ?? "KOBO-001";

const SUBMIT_KOBO_SETUP = `(() => {
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
  const choose = (id, fragment) => {
    const element = document.getElementById(id);
    if (!element) return false;
    const option = Array.from(element.options).find(
      (item) => item.value !== "" && item.value.includes(fragment),
    );
    if (!option) return false;
    setNative(window.HTMLSelectElement.prototype, element, option.value);
    return true;
  };
  const filled =
    setValue("run-setup-start", "2026-09-22T03:00:00Z") &&
    setValue("run-setup-end", "2026-09-22T15:00:00Z") &&
    setValue("run-setup-timestep", "15") &&
    setValue("run-setup-seed", "20260929") &&
    choose("run-setup-model-profile", "daytime-mini-grid") &&
    choose("run-setup-publication-profile", "simulator-lab-publication");
  const submit = Array.from(document.querySelectorAll("main button")).find(
    (button) => (button.textContent || "").trim() === "Create draft run",
  );
  if (!filled || !submit) return "controls-missing";
  if (submit.disabled) return "not-ready";
  submit.click();
  return true;
})()`;

const STEP_TO_THE_EVENING = `(() => {
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
  setNative(window.HTMLInputElement.prototype, size, '41');
  if (step.disabled) return 'not-ready';
  step.click();
  return true;
})()`;

const READ_ELECTRICAL = `(() => {
  const text = (element) => (element ? (element.textContent || '').trim() : null);
  const control = document.querySelector('[data-control="battery-power"]');
  return {
    steps: document.querySelectorAll('[data-electrical-step]').length,
    loads: Array.from(document.querySelectorAll('[data-load]')).map((row) => ({
      address: row.getAttribute('data-load'),
      demand: text(row.querySelector('[data-load-demand]')),
      served: text(row.querySelector('[data-load-served]')),
      unserved: text(row.querySelector('[data-load-unserved]')),
    })),
    flows: document.querySelectorAll('[data-flow]').length,
    requested: text(control && control.querySelector('[data-control-requested]')),
    accepted: text(control && control.querySelector('[data-control-accepted]')),
    reserve: text(document.querySelector('[data-electrical-reserve]')),
    reserveOrigin: (document.querySelector('[data-electrical-reserve]') || {
      getAttribute: () => null,
    }).getAttribute('data-electrical-reserve'),
    socEnd: text(document.querySelector('[data-electrical-soc-end]')),
  };
})()`;

const koboSetup = await visit(
  cdp,
  "/simulator-lab/scenarios/kobo-daytime-overcast/run-setup",
  1280,
  800,
  "form",
  { script: SUBMIT_KOBO_SETUP, waitFor: ".data-table__scroll" },
);
console.log(
  `\n=== Created a Kobo Draft against ${KOBO_SITE} ===\n  ` +
    `run setup summary drawn with ${koboSetup.scrollers.length} table(s)`,
);
const koboRuns = await visit(cdp, "/simulator-lab/runs", 1280, 800, "table");
const koboHref =
  koboRuns.runRows.find((row) => row.status === "READY")?.href ?? null;
if (koboHref === null) {
  throw new Error(
    `No READY Draft was found after setting one up against ${KOBO_SITE}, so ` +
      "the electrical measurements cannot be made. Does the Site exist, " +
      "created from the kobo-mini-grid-60kw template?",
  );
}

await visit(cdp, koboHref, 1280, 800, "[data-execution-status]", {
  script: clickControl("Start this run"),
  waitFor: "[data-execution-status='RUNNING']",
});

for (const [label, width, height] of [
  ["1280x800, the committed minimum", 1280, 800],
  ["1000x700, below the commitment", 1000, 700],
  ["640x700, narrow enough that the series table cannot fit", 640, 700],
]) {
  // Stepped once, at the first width; the other widths re-measure the same
  // instant, because the run's position lives on the server.
  const kobo = await visit(
    cdp,
    koboHref,
    width,
    height,
    width === 1280 ? "[data-execution-status]" : "[data-electrical-step]",
    width === 1280
      ? { script: STEP_TO_THE_EVENING, waitFor: "[data-electrical-step]" }
      : undefined,
  );
  const electrical = (
    await cdp.send("Runtime.evaluate", {
      expression: READ_ELECTRICAL,
      returnByValue: true,
    })
  ).result.value;
  const series = kobo.scrollers.find(
    (s) => s.name === "run-electrical-series-heading",
  );
  const loadsTable = kobo.scrollers.find((s) => s.name === "run-loads-heading");
  const controlTable = kobo.scrollers.find(
    (s) => s.name === "run-control-heading",
  );
  allPass =
    report(`Kobo daytime draft stepped to the evening at ${label}`, kobo, [
      [
        "the series against simulation time has a row per resolved step, and there are some",
        electrical.steps === 41 && series !== undefined && series.rowCount === 41,
        `${electrical.steps} step rows, series table ${series === undefined ? "absent" : `${series.rowCount} rows`}`,
      ],
      [
        "each of the three loads has its own row with demand, service and unserved load",
        electrical.loads.length === 3 &&
          electrical.loads.every(
            (row) => row.demand && row.served && row.unserved !== null,
          ) &&
          loadsTable !== undefined &&
          loadsTable.rowCount === 3,
        electrical.loads
          .map((row) => `${row.address}: ${row.demand} / ${row.served} / ${row.unserved}`)
          .join("; ") || "no load rows",
      ],
      [
        "the requested and the accepted battery power are two cells",
        electrical.requested !== null &&
          electrical.accepted !== null &&
          controlTable !== undefined &&
          controlTable.rowCount === 1,
        `requested ${electrical.requested}, accepted ${electrical.accepted}`,
      ],
      [
        "the named flows are drawn",
        electrical.flows >= 18,
        `${electrical.flows} flow rows`,
      ],
      [
        "the reserve in effect is the scenario override, named as one",
        electrical.reserveOrigin === "OVERRIDE" &&
          (electrical.reserve ?? "").startsWith("15 %"),
        `${electrical.reserve} (${electrical.reserveOrigin})`,
      ],
      [
        "the page does not scroll horizontally",
        !kobo.pageScrollsHorizontally,
        `scrollWidth ${kobo.pageScrollWidth} vs clientWidth ${kobo.pageClientWidth}`,
      ],
      [
        "every table on the page has a named, focusable overflow region",
        kobo.scrollers.length > 0 &&
          kobo.scrollers.every((s) => s.focusable && s.name),
        kobo.scrollers.map((s) => s.name ?? "unnamed").join(", "),
      ],
      [
        "every table that overflows scrolls inside its own region",
        kobo.scrollers.filter((s) => s.overflows).every((s) => s.scrolledBy > 0),
        kobo.scrollers
          .map(
            (s) =>
              `${s.name}: ${s.overflows ? `overflows, scrolled ${s.scrolledBy}px` : "fits"}`,
          )
          .join("; "),
      ],
      [
        "the rail does not move when every table is scrolled to its end",
        kobo.railLeftBefore === kobo.railLeftAfterAll,
        `left ${kobo.railLeftBefore} -> ${kobo.railLeftAfterAll}`,
      ],
      ...(width <= 640
        ? [
            [
              "at least one table overflows here, so the claim above is not vacuous",
              kobo.scrollers.some((s) => s.overflows),
              `${kobo.scrollers.filter((s) => s.overflows).length} of ${kobo.scrollers.length} overflow`,
            ],
          ]
        : []),
    ]) && allPass;
}

// The Kobo Site's Foundation: the typed Site Controls render as a table.
const koboFoundation = await visit(
  cdp,
  `/sites/${KOBO_SITE}/foundation`,
  1280,
  800,
  "table",
);
const siteControls = koboFoundation.scrollers.find(
  (s) => s.name === "foundation-site-controls-heading",
);
allPass =
  report(`Kobo Foundation at 1280x800`, koboFoundation, [
    [
      "the typed Site Controls render as a table with both controls",
      siteControls !== undefined && siteControls.rowCount === 2,
      siteControls === undefined ? "no Site Controls table" : `${siteControls.rowCount} rows`,
    ],
    [
      "the page does not scroll horizontally",
      !koboFoundation.pageScrollsHorizontally,
      `scrollWidth ${koboFoundation.pageScrollWidth} vs clientWidth ${koboFoundation.pageClientWidth}`,
    ],
  ]) && allPass;

// --- T025a: the full mini-grid and its generator on the Draft screen --------
//
// A Draft of the shipped `kobo-mini-grid-evening` scenario with the
// `mini-grid` profile at 5-minute steps, against the same Site (whose
// Foundation must carry the generator policy the T025a template adds). It is
// stepped to offset 390, where the generator has started and is RUNNING at
// its rating, so the generator series has 79 rows and the transitions table
// two. A missing generator section fails rather than passing on nothing.
const SUBMIT_MINI_GRID_SETUP = SUBMIT_KOBO_SETUP.replace(
  '"2026-09-22T03:00:00Z"',
  '"2026-09-22T09:00:00Z"',
)
  .replace('"2026-09-22T15:00:00Z"', '"2026-09-22T17:00:00Z"')
  .replace('setValue("run-setup-timestep", "15")', 'setValue("run-setup-timestep", "5")')
  // Pinned to mini-grid v1 and publication profile 3: T025b offers v2 and 4
  // beside them, and the form preselects neither.
  .replace('"daytime-mini-grid"', '"mini-grid@1"')
  .replace('"simulator-lab-publication")', '"simulator-lab-publication@3")')
  // `choose` matches by substring, and "mini-grid" is inside "daytime-mini-grid".
  .replace('item.value.includes(fragment)', 'item.value.startsWith(fragment)');

const STEP_TO_THE_RUNNING_GENERATOR = STEP_TO_THE_EVENING.replace("'41'", "'79'");

const READ_GENERATOR = `(() => {
  const text = (element) => (element ? (element.textContent || '').trim() : null);
  return {
    steps: document.querySelectorAll('[data-generator-step]').length,
    transitions: Array.from(document.querySelectorAll('[data-generator-transition]')).map(
      (row) => row.getAttribute('data-generator-transition'),
    ),
    stateForStep: text(document.querySelector('[data-generator-state-for-step]')),
    requested: text(document.querySelector('[data-generator-request]')),
    output: text(document.querySelector('[data-generator-output]')),
    reported: text(document.querySelector('[data-generator-reported-status]')),
    served: text(document.querySelector('[data-electrical-served]')),
    demand: text(document.querySelector('[data-electrical-demand]')),
  };
})()`;

await visit(
  cdp,
  "/simulator-lab/scenarios/kobo-mini-grid-evening/run-setup",
  1280,
  800,
  "form",
  { script: SUBMIT_MINI_GRID_SETUP, waitFor: ".data-table__scroll" },
);
const miniRuns = await visit(cdp, "/simulator-lab/runs", 1280, 800, "table");
// Newest first, as the Kobo daytime lookup above relies on too.
const miniHref =
  miniRuns.runRows.find((row) => row.status === "READY")?.href ?? null;
if (miniHref === null || miniHref === koboHref) {
  throw new Error(
    `No READY mini-grid Draft was found after setting one up against ${KOBO_SITE}. ` +
      "Does its Foundation carry the generator policy properties?",
  );
}
await visit(cdp, miniHref, 1280, 800, "[data-execution-status]", {
  script: clickControl("Start this run"),
  waitFor: "[data-execution-status='RUNNING']",
});
for (const [label, width, height] of [
  ["1280x800, the committed minimum", 1280, 800],
  ["1000x700, below the commitment", 1000, 700],
  ["640x700, narrow enough that the generator series cannot fit", 640, 700],
]) {
  const mini = await visit(
    cdp,
    miniHref,
    width,
    height,
    width === 1280 ? "[data-execution-status]" : "[data-generator-step]",
    width === 1280
      ? { script: STEP_TO_THE_RUNNING_GENERATOR, waitFor: "[data-generator-step]" }
      : undefined,
  );
  const generator = (
    await cdp.send("Runtime.evaluate", {
      expression: READ_GENERATOR,
      returnByValue: true,
    })
  ).result.value;
  const series = mini.scrollers.find(
    (s) => s.name === "run-generator-series-heading",
  );
  const transitions = mini.scrollers.find(
    (s) => s.name === "run-generator-transitions-heading",
  );
  allPass =
    report(`Kobo mini-grid draft stepped to a running generator at ${label}`, mini, [
      [
        "the generator series has a row per resolved step, and there are some",
        generator.steps === 79 && series !== undefined && series.rowCount === 79,
        `${generator.steps} step rows, series table ${series === undefined ? "absent" : `${series.rowCount} rows`}`,
      ],
      [
        "both lifecycle transitions are drawn, start request then running",
        transitions !== undefined &&
          transitions.rowCount === 2 &&
          generator.transitions.join(",") === "STARTING,RUNNING",
        `${generator.transitions.join(" -> ") || "none"}`,
      ],
      [
        "request, physical state and accepted output are three drawn values",
        generator.requested === "RUN" &&
          generator.stateForStep === "RUNNING" &&
          generator.output === "40 kW",
        `requested ${generator.requested}, state ${generator.stateForStep}, output ${generator.output}`,
      ],
      [
        "service counts the generator's share",
        generator.served !== null && generator.served === generator.demand,
        `served ${generator.served} of demand ${generator.demand}`,
      ],
      [
        "the reported status is stated as pending",
        (generator.reported ?? "").includes("pending T025b"),
        generator.reported ?? "absent",
      ],
      [
        "the page does not scroll horizontally",
        !mini.pageScrollsHorizontally,
        `scrollWidth ${mini.pageScrollWidth} vs clientWidth ${mini.pageClientWidth}`,
      ],
      [
        "every table that overflows scrolls inside its own region",
        mini.scrollers.filter((s) => s.overflows).every((s) => s.scrolledBy > 0),
        mini.scrollers
          .map(
            (s) =>
              `${s.name}: ${s.overflows ? `overflows, scrolled ${s.scrolledBy}px` : "fits"}`,
          )
          .join("; "),
      ],
      [
        "the rail does not move when every table is scrolled to its end",
        mini.railLeftBefore === mini.railLeftAfterAll,
        `left ${mini.railLeftBefore} -> ${mini.railLeftAfterAll}`,
      ],
      ...(width <= 640
        ? [
            [
              "the generator series overflows here, so the claim above is not vacuous",
              series !== undefined && series.overflows,
              series === undefined ? "absent" : series.overflows ? "overflows" : "fits",
            ],
          ]
        : []),
    ]) && allPass;
}

// --- T025b: healthy, prolonged and changed-policy runs, profile 4 ----------
//
// Three Drafts against the same Site, each `mini-grid` v2 under publication
// profile 4 at 5-minute steps and each run to its end: the shipped
// `kobo-mini-grid-evening` (09:00Z-17:00Z, healthy), and the shipped
// `kobo-mini-grid-prolonged` and `kobo-mini-grid-stop-60` (03:00Z-11:00Z),
// identical but for the stop-threshold override. The claims are the ones the
// owner inspects by hand: the reported status column beside the physical
// state (with GOOD and STALE both present, so it is not a column of blanks),
// both controls in effect named by address, the stop-threshold origin, the
// earlier STOPPED of the 60 % run and its larger fuel remainder, and the
// status disclosed as observed and not staged. The 640 px pass proves the
// wider generator series still scrolls inside its own region.
const submitV2Setup = (start, end) =>
  SUBMIT_KOBO_SETUP.replace('"2026-09-22T03:00:00Z"', JSON.stringify(start))
    .replace('"2026-09-22T15:00:00Z"', JSON.stringify(end))
    .replace('setValue("run-setup-timestep", "15")', 'setValue("run-setup-timestep", "5")')
    .replace('"daytime-mini-grid"', '"mini-grid@2"')
    .replace('"simulator-lab-publication")', '"simulator-lab-publication@4")')
    .replace("item.value.includes(fragment)", "item.value.startsWith(fragment)");

const READ_V2_RUN = `(() => {
  const text = (element) => (element ? (element.textContent || '').trim() : null);
  const all = (selector) => Array.from(document.querySelectorAll(selector));
  return {
    status: document.querySelector('[data-execution-status]')?.getAttribute('data-execution-status') ?? null,
    steps: all('[data-generator-step]').length,
    reportedCells: all('[data-generator-step-reported]').map((cell) =>
      cell.getAttribute('data-generator-step-reported'),
    ),
    transitions: all('[data-generator-transition]').map(
      (row) => row.getAttribute('data-generator-transition') + '@' + text(row.querySelector('th')),
    ),
    controls: all('[data-effective-control-address]').map(
      (row) => row.getAttribute('data-effective-control-address') + '=' + row.getAttribute('data-effective-control'),
    ),
    stopValue: text(document.querySelector('[data-effective-control-address^="generator-stop"] td:last-child')),
    stateAtT: text(document.querySelector('[data-generator-state-at-t]')),
    reportedState: text(document.querySelector('[data-generator-reported-state]')),
    fuelEnd: text(document.querySelector('[data-generator-fuel-end]')),
    unstaged: all('[data-stage-unstaged-signal]').map((item) => item.getAttribute('data-stage-unstaged-signal')),
    statusObserved: text(document.querySelector('[data-observation="generator-controller:status"] [data-observation-true]')),
  };
})()`;

const seenHrefs = new Set([koboHref, miniHref]);
const v2Runs = {};
for (const [name, start, end] of [
  ["kobo-mini-grid-evening", "2026-09-22T09:00:00Z", "2026-09-22T17:00:00Z"],
  ["kobo-mini-grid-prolonged", "2026-09-22T03:00:00Z", "2026-09-22T11:00:00Z"],
  ["kobo-mini-grid-stop-60", "2026-09-22T03:00:00Z", "2026-09-22T11:00:00Z"],
]) {
  await visit(cdp, `/simulator-lab/scenarios/${name}/run-setup`, 1280, 800, "form", {
    script: submitV2Setup(start, end),
    waitFor: ".data-table__scroll",
  });
  const listed = await visit(cdp, "/simulator-lab/runs", 1280, 800, "table");
  const href = listed.runRows.find((row) => row.status === "READY")?.href ?? null;
  if (href === null || seenHrefs.has(href)) {
    throw new Error(
      `No new READY mini-grid v2 Draft of ${name} was found against ${KOBO_SITE}. ` +
        "Does the Site carry the generator-controller status signal and policy properties?",
    );
  }
  seenHrefs.add(href);
  await visit(cdp, href, 1280, 800, "[data-execution-status]", {
    script: clickControl("Start this run"),
    waitFor: "[data-execution-status='RUNNING']",
  });
  await visit(cdp, href, 1280, 800, "[data-execution-status]", {
    script: clickControl("Run to the end"),
    waitFor: "[data-execution-status='COMPLETED']",
  });
  v2Runs[name] = href;
}

const v2Reads = {};
for (const [name, href] of Object.entries(v2Runs)) {
  for (const [label, width, height] of [
    ["1280x800", 1280, 800],
    ...(name === "kobo-mini-grid-stop-60" ? [["640x700", 640, 700]] : []),
  ]) {
    const page = await visit(cdp, href, width, height, "[data-generator-step]");
    const read = (
      await cdp.send("Runtime.evaluate", { expression: READ_V2_RUN, returnByValue: true })
    ).result.value;
    v2Reads[name] = read;
    const series = page.scrollers.find((s) => s.name === "run-generator-series-heading");
    const qualities = new Set(read.reportedCells);
    allPass =
      report(`T025b ${name}, mini-grid v2 / profile 4, run to its end, at ${label}`, page, [
        [
          "the run completed and the series has a row per step, and there are some",
          read.status === "COMPLETED" &&
            read.steps === 96 &&
            series !== undefined &&
            series.rowCount === 96,
          `${read.status}, ${read.steps} step rows`,
        ],
        [
          "every step row has a reported-status cell, with GOOD and STALE both present",
          read.reportedCells.length === read.steps && qualities.has("GOOD") && qualities.has("STALE"),
          `${read.reportedCells.length} cells, qualities ${[...qualities].join(",")}`,
        ],
        [
          "the reported status is drawn beside the physical state at T",
          read.stateAtT !== null && (read.reportedState ?? "").length > 0,
          `physical ${read.stateAtT}, reported ${read.reportedState}`,
        ],
        [
          "both controls in effect are named by address",
          read.controls.length === 2 &&
            read.controls[0].startsWith("battery-reserve-state-of-charge@battery=") &&
            read.controls[1].startsWith("generator-stop-soc-threshold@generator="),
          `${read.controls.join("; ")}; stop ${read.stopValue}`,
        ],
        [
          "the status is disclosed as observed and not staged, and read as a member",
          read.unstaged.join(",") === "generator-controller:status" &&
            /^[A-Z]+$/.test(read.statusObserved ?? ""),
          `unstaged ${read.unstaged.join(",") || "none"}; status true value ${read.statusObserved}`,
        ],
        [
          "the page does not scroll horizontally",
          !page.pageScrollsHorizontally,
          `scrollWidth ${page.pageScrollWidth} vs clientWidth ${page.pageClientWidth}`,
        ],
        [
          "every table that overflows scrolls inside its own region",
          page.scrollers.filter((s) => s.overflows).every((s) => s.scrolledBy > 0),
          page.scrollers
            .map((s) => `${s.name}: ${s.overflows ? `overflows, scrolled ${s.scrolledBy}px` : "fits"}`)
            .join("; "),
        ],
        ...(width <= 640
          ? [
              [
                "the generator series overflows here, so the claim above is not vacuous",
                series !== undefined && series.overflows,
                series === undefined ? "absent" : series.overflows ? "overflows" : "fits",
              ],
            ]
          : []),
      ]) && allPass;
  }
}

const prolongedRead = v2Reads["kobo-mini-grid-prolonged"];
const changedRead = v2Reads["kobo-mini-grid-stop-60"];
const stoppedAt = (read) =>
  read.transitions.find((item) => item.startsWith("STOPPED@")) ?? "none";
const policyChecks = [
  [
    "the stop threshold is the baseline in one run and the override in the other",
    Boolean(prolongedRead.controls[1]?.endsWith("=BASELINE")) &&
      Boolean(changedRead.controls[1]?.endsWith("=OVERRIDE")),
    `prolonged ${prolongedRead.controls[1]} (${prolongedRead.stopValue}); changed ${changedRead.controls[1]} (${changedRead.stopValue})`,
  ],
  [
    "the 60 % run stops earlier (07:10Z against 09:15Z)",
    stoppedAt(changedRead) === "STOPPED@2026-09-22T07:10:00Z" &&
      stoppedAt(prolongedRead) === "STOPPED@2026-09-22T09:15:00Z",
    `changed ${stoppedAt(changedRead)}; prolonged ${stoppedAt(prolongedRead)}`,
  ],
  [
    "the 60 % run ends with more fuel (272.3 L against 259.8 L)",
    changedRead.fuelEnd === "272.3 L" && prolongedRead.fuelEnd === "259.8 L",
    `changed ${changedRead.fuelEnd}; prolonged ${prolongedRead.fuelEnd}`,
  ],
];
allPass =
  report("T025b prolonged (stop 90 %) against changed policy (stop 60 %)", null, policyChecks) &&
  allPass;

console.log(`\n${allPass ? "ALL CLAIMS HOLD" : "AT LEAST ONE CLAIM FAILED"}\n`);

ws.close();
chrome.kill();
try {
  rmSync(profile, { recursive: true, force: true });
} catch {
  /* Windows sometimes holds the profile briefly */
}
process.exit(allPass ? 0 : 1);
