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
 * T025c adds a second invocation, made after the host has been restarted over
 * the same store: `node tools/layout-evidence.mjs <baseUrl> <site> --readback
 * <file>` reopens the completed run the first invocation recorded in <file>
 * (`ASSETOPS_READBACK_FILE`, default in the OS temp directory) and measures
 * that its charts and identity came back from the artifact alone. With
 * `ASSETOPS_EVIDENCE_ENV` naming the served store it hashes the run's
 * artifact before and after the reads, so "reading changes no artifact" is
 * measured rather than assumed.
 *
 * It exits non-zero if any claim fails, so it can be read by a person or by a
 * script. It drives the Chrome already installed on this machine over the
 * DevTools Protocol using Node's built-in fetch and WebSocket, so it adds no
 * dependency to the project and nothing to install.
 */

import { spawn } from "node:child_process";
import { createHash } from "node:crypto";
import { mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
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
const PUBLISH_RESERVE_LABEL = "Publish reserve change";
// S1-02: the binding-removal publish, rendered only when a binding set is in
// effect. Allowed on an imported Site beside the reserve change, and nothing else.
// This is a deliberate S1-02 allowance (Architect ruling D3,
// .agent/architect-S1-02-deviations-2026-10-08.md), not a relaxation of the
// S1-01 rule: the battery reserve stays the only editable Foundation control.
// A binding publication is a separate S1-02 action - it changes the signal
// binding set, subject to atomic validation and append-only history - and it
// may render at most once, on a stored imported Site with a binding set.
const PUBLISH_BINDING_LABEL = "Publish binding change";
const IMPORTED_SITE_ACTIONS = new Set([PUBLISH_RESERVE_LABEL, PUBLISH_BINDING_LABEL]);
// S1-01: the Site the Lab run setup binds to. Defaults to SITE; set it to an
// unimported Site when SITE is imported, because the Lab refuses an imported
// Site's Draft setup until S2.
const LAB_SITE = process.env.ASSETOPS_LAB_SITE ?? SITE;
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
  // T025e: a closed <details> measures as zero, so every disclosure is opened first.
  document.querySelectorAll('details').forEach((d) => { d.open = true; });
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
    finalPathname: window.location.pathname,
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

  // T025g: the site is chosen at run setup and the picker selects nothing on
  // its own. The measured site is picked when it is listed, else the first.
  const chooseSite = () => {
    const radios = Array.from(
      document.querySelectorAll('input[name="run-setup-site"]'),
    );
    const radio =
      radios.find((item) => item.value === ${JSON.stringify(LAB_SITE)}) ?? radios[0];
    if (!radio) return false;
    radio.click();
    return true;
  };

  // S1-01: the site picker renders only after the Sites index has been read,
  // which can land after the form itself. No radio yet is the page still
  // loading - the same NOT-READY as a disabled submit - not a missing control.
  if (document.querySelectorAll('input[name="run-setup-site"]').length === 0) {
    return "not-ready";
  }

  const filled =
    chooseSite() &&
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

// --- T025c: recorded day curves, the shared cursor and the run header -------
//
// Measured on a completed mini-grid v2 run. Everything the fingerprint holds is
// a data attribute - which series, how many recorded steps, which report at
// which source time with which exact value, which gap glyph where, which state
// run from where, and the exact-value table - so the same record drawn at two
// widths, or before and after a host restart, fingerprints the same, and a
// record that changed does not.
const READBACK_ARG = process.argv.indexOf("--readback");
const READBACK_FILE =
  READBACK_ARG > 0
    ? process.argv[READBACK_ARG + 1]
    : process.env.ASSETOPS_READBACK_FILE ?? join(tmpdir(), "assetops-t025c-readback.json");
const EVIDENCE_ENV = process.env.ASSETOPS_EVIDENCE_ENV ?? null;

const READ_CHARTS = `(() => {
  // T025e: a closed <details> measures as zero, so every disclosure is opened first.
  document.querySelectorAll('details').forEach((d) => { d.open = true; });
  const text = (element) => (element ? (element.textContent || '').trim() : null);
  const all = (selector, scope) => Array.from((scope || document).querySelectorAll(selector));
  const panels = all('[data-chart-panel]').map((figure) => {
    const region = figure.querySelector('.history-chart__scroll');
    const svg = figure.querySelector('svg');
    const box = figure.getBoundingClientRect();
    const legend = all('.history-legend li', figure).map((item) => {
      const r = item.getBoundingClientRect();
      return {
        inside: r.left >= box.left - 1 && r.right <= box.right + 1 && r.width > 0,
        fontPx: parseFloat(getComputedStyle(item).fontSize),
      };
    });
    const label = figure.querySelector('.history-chart__label');
    return {
      id: figure.getAttribute('data-chart-panel'),
      svgWidth: svg ? Math.round(svg.getBoundingClientRect().width) : 0,
      overflows: region ? region.scrollWidth > region.clientWidth : null,
      scrolledBy: region ? (region.scrollLeft = 99999, Math.round(region.scrollLeft)) : 0,
      paths: all('[data-chart-series]', figure).filter((p) => (p.getAttribute('d') || '').length > 0).length,
      stateRuns: all('[data-chart-state]', figure).length,
      reports: all('[data-chart-report]', figure).length,
      missing: all('[data-chart-missing]', figure).map((g) => (g.firstChild ? g.firstChild.textContent : '') + '@' + g.getAttribute('data-offset') + ':' + g.getAttribute('data-chart-missing')),
      titledMarks: all('[data-chart-report] > title, [data-chart-missing] > title', figure).length,
      legend,
      axisFontPx: label ? parseFloat(getComputedStyle(label).fontSize) : 0,
    };
  });
  const panelOf = (element) => element.closest('[data-chart-panel]').getAttribute('data-chart-panel');
  const fingerprint = [
    ...all('[data-chart-series]').map((p) => panelOf(p) + '/' + p.getAttribute('data-chart-series') + '#' + p.getAttribute('data-points')),
    ...all('[data-chart-report]').map((c) => panelOf(c) + '/r' + c.getAttribute('data-chart-report') + '=' + c.getAttribute('data-value')),
    ...all('[data-chart-missing]').map((g) => panelOf(g) + '/m' + g.getAttribute('data-offset') + '=' + g.getAttribute('data-chart-missing')),
    ...all('[data-chart-state]').map((g) => panelOf(g) + '/s' + g.getAttribute('data-from') + '=' + g.getAttribute('data-chart-state')),
    ...all('[data-value-row]').map((row) => row.getAttribute('data-value-row') + '=' + text(row.querySelector('td:last-child'))),
  ].join('|');
  const history = performance.getEntriesByType('resource').find((e) => e.name.includes('/execution/history'));
  return {
    panels,
    fingerprint,
    cursors: [...new Set(all('[data-chart-cursor]').map((c) => c.getAttribute('data-chart-cursor')))],
    selected: document.querySelector('[data-history-selected]')?.getAttribute('data-history-selected') ?? null,
    valueRows: all('[data-value-row]').length,
    status: document.querySelector('[data-execution-status]')?.getAttribute('data-execution-status') ?? null,
    boundaries: text(document.querySelector('[data-header-boundaries]')),
    headerExecution: document.querySelector('[data-header-execution]')?.getAttribute('data-header-execution') ?? null,
    headerHistory: document.querySelector('[data-header-history]')?.getAttribute('data-header-history') ?? null,
    headerHistoryText: text(document.querySelector('[data-header-history]')),
    headerStage: document.querySelector('[data-header-stage]')?.getAttribute('data-header-stage') ?? null,
    headerWindow: text(document.querySelector('[data-header-window]')),
    headerTimestep: document.querySelector('[data-header-timestep]')?.getAttribute('data-header-timestep') ?? null,
    historyDigest: text(document.querySelector('[data-history-digest]')),
    historySource: document.querySelector('[data-history-source]')?.getAttribute('data-history-source') ?? null,
    historyBytes: history ? history.decodedBodySize : null,
    historyResponseEnd: history ? history.responseEnd : null,
    chartsAt: window.__chartsAt ?? null,
  };
})()`;

/** Record when the first chart appears, from the very start of each page. */
const CHARTS_TIMER = `window.__chartsAt = null;
new MutationObserver((_, observer) => {
  if (document.querySelector('[data-chart-panel]')) {
    window.__chartsAt = performance.now();
    observer.disconnect();
  }
}).observe(document, { subtree: true, childList: true });`;

/** Move the shared cursor with the keyboard, as a person would. */
async function pressOnCursor(cdp, key, keyCode) {
  await cdp.send("Runtime.evaluate", {
    expression: "document.getElementById('history-cursor-range').focus()",
  });
  for (const type of ["keyDown", "keyUp"]) {
    await cdp.send("Input.dispatchKeyEvent", {
      type,
      key,
      code: key,
      windowsVirtualKeyCode: keyCode,
      nativeVirtualKeyCode: keyCode,
    });
  }
  await sleep(300);
}

async function readCharts(cdp) {
  return (await cdp.send("Runtime.evaluate", { expression: READ_CHARTS, returnByValue: true }))
    .result.value;
}

function artifactDigest(runId) {
  if (EVIDENCE_ENV === null) return null;
  try {
    return createHash("sha256")
      .update(readFileSync(join(EVIDENCE_ENV, "executions", `${runId}.yaml`)))
      .digest("hex");
  } catch {
    return "missing";
  }
}

/**
 * Wait until every read the run screen makes has settled, not only the first
 * chart. The history can arrive before the execution read, and a measurement
 * taken then sees the charts that need no electrical steps and a header that is
 * still reading - a race, not a finding. After a host restart the execution
 * read parses its artifact cold and is the slower of the two.
 */
async function settledCockpit(cdp) {
  for (const selector of ['[data-header-boundaries]', '[data-chart-panel="battery-power"]', '[data-header-stage]']) {
    if (!(await waitForSelector(cdp, selector))) {
      throw new Error(`The run screen never rendered ${selector}; nothing below was measured.`);
    }
  }
  await sleep(500);
  // Measured again now that everything has rendered: `visit` measured the page
  // at its first chart, before the slower reads had landed.
  return (await cdp.send("Runtime.evaluate", { expression: MEASURE, returnByValue: true })).result.value;
}

/**
 * The cost of re-rendering every chart and the exact-value table for one
 * selection change, the render a person pays on each keypress. Mount time is
 * reported beside it for information only: the first paint of the run screen
 * also renders the stage, the reading and the generator tables, so it measures
 * the page, not the charts.
 */
async function cursorMoveCost(cdp, index) {
  return (
    await cdp.send("Runtime.evaluate", {
      expression: `(() => {
        const range = document.getElementById('history-cursor-range');
        const setter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set;
        const t0 = performance.now();
        setter.call(range, '${index}');
        range.dispatchEvent(new Event('input', { bubbles: true }));
        return new Promise((resolve) => requestAnimationFrame(() => requestAnimationFrame(() =>
          resolve({
            ms: Math.round(performance.now() - t0),
            cursor: document.querySelector('[data-chart-cursor]')?.getAttribute('data-chart-cursor') ?? null,
          }))));
      })()`,
      awaitPromise: true,
      returnByValue: true,
    })
  ).result.value;
}

const mountNote = (reads) =>
  reads
    .map((r) => `${r.historyBytes} B history; first chart ${Math.round((r.chartsAt ?? 0) - (r.historyResponseEnd ?? 0))} ms after its response (page render, informational)`)
    .join("; ");

// --- T025d: the run-bound drawing, the interval inspection and auto-play ----
//
// Read from data attributes only. The drawing's value labels are measured
// against every node box and every other label, because label placement at a
// polyline's midpoint was the one geometry claim phase 1 left unmeasured.
const READ_INSPECTION = `(() => {
  // T025e: a closed <details> measures as zero, so every disclosure is opened first.
  document.querySelectorAll('details').forEach((d) => { d.open = true; });
  const all = (s) => Array.from(document.querySelectorAll(s));
  const rect = (el) => { const r = el.getBoundingClientRect(); return { l: r.left, t: r.top, r: r.right, b: r.bottom }; };
  const overlap = (a, b) => Math.min(a.r, b.r) - Math.max(a.l, b.l) > 0.5 && Math.min(a.b, b.b) - Math.max(a.t, b.t) > 0.5;
  const bound = document.querySelector('[data-drawing-bound]');
  const svg = bound ? bound.querySelector('svg') : null;
  const labels = svg ? Array.from(svg.querySelectorAll('[data-sld-connection-value]')) : [];
  const boxes = svg ? Array.from(svg.querySelectorAll('.sld-node__box')).map(rect) : [];
  const labelRects = labels.map(rect);
  const svgBox = svg ? svg.getBoundingClientRect() : null;
  const collisions = [];
  labelRects.forEach((l, i) => {
    boxes.forEach((b, j) => { if (overlap(l, b)) collisions.push(labels[i].getAttribute('data-sld-connection-value') + '~node' + j); });
    labelRects.forEach((m, k) => { if (k > i && overlap(l, m)) collisions.push(labels[i].getAttribute('data-sld-connection-value') + '~' + labels[k].getAttribute('data-sld-connection-value')); });
  });
  const clipped = svgBox === null ? [] : labels.filter((el) => {
    const r = el.getBoundingClientRect();
    return r.left < svgBox.left - 0.5 || r.right > svgBox.right + 0.5 || r.top < svgBox.top - 0.5 || r.bottom > svgBox.bottom + 0.5;
  }).map((el) => el.getAttribute('data-sld-connection-value'));
  const directions = {};
  labels.forEach((el) => { directions[el.getAttribute('data-sld-connection-value')] = el.getAttribute('data-sld-direction'); });
  const region = (id) => {
    const el = document.querySelector('.data-table__scroll[aria-labelledby="' + id + '"]');
    return el === null ? null : { overflows: el.scrollWidth > el.clientWidth, focusable: el.getAttribute('tabindex') === '0' };
  };
  const tableRegions = all('.data-table__scroll').map((el) => el.getAttribute('aria-labelledby') || '');
  const timelineIds = tableRegions.filter((id) => id.startsWith('run-timeline-'));
  const controls = all('[data-interval-control]').map((el) => el.getAttribute('data-interval-control') + ':' + el.getAttribute('data-accepted-differs'));
  const balances = all('[data-interval-balance]').map((el) => el.getAttribute('data-balance-holds'));
  const text = (el) => (el ? (el.textContent || '').replace(/\\s+/g, ' ').trim() : '');
  const statement = document.querySelector('[data-execution-statement]');
  const playback = document.querySelector('[data-playback-state]');
  const factValue = (term) => {
    const dt = all('dt').find((d) => text(d) === term);
    return dt && dt.nextElementSibling ? text(dt.nextElementSibling) : null;
  };
  const play = all('main button').find((b) => /^(Play|Resume)$/.test(text(b)));
  return {
    drawingBoundary: document.querySelector('[data-drawing-boundary]')?.getAttribute('data-drawing-boundary') ?? null,
    drawingBound: bound ? bound.getAttribute('data-drawing-bound') : null,
    drawingUnavailable: text(document.querySelector('[data-drawing-unavailable]')),
    labels: labels.length,
    labelTexts: labels.map((el) => text(el)),
    collisions,
    clipped,
    directions,
    controls,
    balances,
    timelineRows: all('[data-phase]').length,
    timelineIds,
    timelineRegions: timelineIds.map(region),
    balanceRegion: region('run-interval-balance-heading'),
    controlRegion: region('run-interval-control-heading'),
    pageScrolls: document.scrollingElement.scrollWidth > document.scrollingElement.clientWidth,
    selected: document.querySelector('[data-history-selected]')?.getAttribute('data-history-selected') ?? null,
    status: statement ? statement.getAttribute('data-execution-status') : null,
    playbackState: playback ? playback.getAttribute('data-playback-state') : null,
    playbackReason: playback ? playback.getAttribute('data-playback-reason') : null,
    playEnabled: play ? !play.disabled : null,
    boundaries: factValue('Boundaries covered'),
    trajectory: factValue('Trajectory digest'),
    readings: factValue('Reading series digest'),
    inputs: factValue('Frozen inputs identity'),
    steps: window.__t025dSteps ?? null,
    fingerprint: JSON.stringify([
      document.querySelector('[data-drawing-boundary]')?.getAttribute('data-drawing-boundary'),
      labels.map((el) => el.getAttribute('data-sld-connection-value') + '=' + el.getAttribute('data-sld-direction') + ':' + text(el)),
      controls,
      all('[data-interval-load]').map((el) => text(el)),
      all('[data-interval-balance]').map((el) => text(el)),
    ]),
  };
})()`;

/** Count guarded step requests, and how many were ever in flight at once. */
const STEP_COUNTER = `window.__t025dSteps = { count: 0, open: 0, maxOpen: 0, historyReads: 0 };
(() => {
  const original = window.fetch;
  window.fetch = async (...args) => {
    const url = String(args[0] && args[0].url ? args[0].url : args[0]);
    const step = url.endsWith('/execution/step');
    // A full read; a T025e delta carries '?since_boundary=' and is counted apart.
    if (url.endsWith('/execution/history')) window.__t025dSteps.historyReads += 1;
    if (url.includes('/execution/history?since_boundary=')) window.__t025dSteps.deltaReads = (window.__t025dSteps.deltaReads || 0) + 1;
    if (step) {
      window.__t025dSteps.count += 1;
      window.__t025dSteps.open += 1;
      window.__t025dSteps.maxOpen = Math.max(window.__t025dSteps.maxOpen, window.__t025dSteps.open);
    }
    try { return await original(...args); } finally { if (step) window.__t025dSteps.open -= 1; }
  };
})();`;

async function readInspection(cdp) {
  return (await cdp.send("Runtime.evaluate", { expression: READ_INSPECTION, returnByValue: true }))
    .result.value;
}

/** Move the history cursor to a boundary index and time the drawing's follow. */
async function selectBoundary(cdp, index, offset) {
  return (
    await cdp.send("Runtime.evaluate", {
      expression: `(() => {
        const range = document.getElementById('history-cursor-range');
        const setter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set;
        const t0 = performance.now();
        setter.call(range, '${index}');
        range.dispatchEvent(new Event('input', { bubbles: true }));
        return new Promise((resolve) => requestAnimationFrame(() => requestAnimationFrame(() =>
          resolve({
            ms: Math.round(performance.now() - t0),
            follows: document.querySelector('[data-drawing-boundary]')?.getAttribute('data-drawing-boundary') === '${offset}',
          }))));
      })()`,
      awaitPromise: true,
      returnByValue: true,
    })
  ).result.value;
}

const selectDelay = (value) => `(() => {
  const select = document.getElementById('run-playback-delay');
  if (!select) return 'controls-missing';
  const setter = Object.getOwnPropertyDescriptor(HTMLSelectElement.prototype, 'value').set;
  setter.call(select, '${value}');
  select.dispatchEvent(new Event('change', { bubbles: true }));
  return true;
})()`;

function inspectionClaims(read, width) {
  return [
    [
      "the drawing is bound to the frozen Site and follows the history cursor",
      read.drawingBound !== null && read.drawingBoundary !== null,
      `bound ${read.drawingBound}; boundary ${read.drawingBoundary}; ${read.drawingUnavailable}`,
    ],
    [
      "the drawing carries value labels, so the geometry claims below are not vacuous",
      read.labels >= 5,
      `${read.labels} labels`,
    ],
    [
      "no value label overlaps a component box or another label",
      read.collisions.length === 0,
      read.collisions.join(", ") || "none",
    ],
    [
      "no value label is clipped by the drawing's own bounds",
      read.clipped.length === 0,
      read.clipped.join(", ") || "none",
    ],
    [
      "every balance identity at the selected interval holds, and there are some",
      read.balances.length > 0 && read.balances.every((holds) => holds === "yes"),
      `${read.balances.length} identities: ${read.balances.join(",")}`,
    ],
    [
      "the applied timeline has rows and each lane is a focusable table region",
      read.timelineRows > 0 &&
        read.timelineRegions.length > 0 &&
        read.timelineRegions.every((r) => r !== null && r.focusable),
      `${read.timelineRows} rows in ${read.timelineIds.join(", ")}`,
    ],
    [
      "the page itself never scrolls sideways",
      !read.pageScrolls,
      `width ${width}`,
    ],
  ];
}

const EXPECTED_PANELS =
  "pv,load-load-clinic,load-load-res,load-load-mill,soc-battery,battery-power,generator-output,fuel-fuel-tank,state-generator";

const chartClaims = (read, page, width) => [
  [
    "nine populated chart panels: PV, three addressed loads, SOC, battery power, generator output, fuel, generator state",
    read.panels.map((p) => p.id).join(",") === EXPECTED_PANELS &&
      read.panels.every((p) => p.paths > 0 || p.stateRuns > 0),
    read.panels.map((p) => `${p.id}: ${p.paths} series, ${p.stateRuns} state runs, ${p.reports} reports`).join("; "),
  ],
  [
    "the report markers are the whole series, far longer than the 12-report tail",
    read.panels.reduce((sum, p) => sum + p.reports, 0) > 12,
    `${read.panels.reduce((sum, p) => sum + p.reports, 0)} report markers`,
  ],
  [
    "each due attempt without a reading is a glyph with its outcome in words, and there are some",
    read.panels.some((p) => p.missing.length > 0) &&
      read.panels.every((p) => p.missing.every((m) => /^[×□–]@\d+:[A-Z_]+$/.test(m))),
    read.panels.flatMap((p) => p.missing.map((m) => `${p.id} ${m}`)).join("; "),
  ],
  [
    "every report marker and gap glyph carries its own tooltip",
    read.panels.every((p) => p.titledMarks === p.reports + p.missing.length),
    read.panels.map((p) => `${p.id} ${p.titledMarks}/${p.reports + p.missing.length}`).join("; "),
  ],
  [
    "every legend entry sits inside its chart at 11 px or more, and so do the axis labels",
    read.panels.every(
      (p) => p.legend.length > 0 && p.legend.every((l) => l.inside && l.fontPx >= 11) && p.axisFontPx >= 11,
    ),
    read.panels.map((p) => `${p.id} ${p.legend.length} entries`).join("; "),
  ],
  [
    "no chart pushes the page sideways",
    !page.pageScrollsHorizontally,
    `page scrollWidth ${page.pageScrollWidth} vs ${page.pageClientWidth}; svg width ${[...new Set(read.panels.map((p) => p.svgWidth))].join("/")} at ${width}; ${read.panels.filter((p) => p.overflows).length} chart regions overflow`,
  ],
  [
    "every chart region that overflows scrolls inside itself",
    read.panels.filter((p) => p.overflows).every((p) => p.scrolledBy > 0),
    `${read.panels.filter((p) => p.overflows).length} of ${read.panels.length} overflow; scrolled ${read.panels.filter((p) => p.overflows).map((p) => p.scrolledBy).join("/") || "none"} px`,
  ],
  [
    "every table that overflows scrolls inside its own region",
    page.scrollers.filter((s) => s.overflows).every((s) => s.scrolledBy > 0),
    page.scrollers
      .filter((s) => (s.name ?? "").startsWith("run-history"))
      .map((s) => `${s.name}: ${s.overflows ? `overflows, scrolled ${s.scrolledBy}px` : "fits"}`)
      .join("; "),
  ],
  [
    "the header keeps execution outcome, recorded coverage and stage apart",
    read.headerExecution === "COMPLETED" &&
      read.headerHistory !== null &&
      read.headerStage !== null &&
      read.headerTimestep === "5",
    `execution ${read.headerExecution}; history ${read.headerHistoryText}; stage ${read.headerStage}; window ${read.headerWindow}; timestep ${read.headerTimestep}; ${read.boundaries}`,
  ],
];

const socketUrl = await pageSocketUrl();
const ws = new WebSocket(socketUrl);
await new Promise((resolve) => ws.addEventListener("open", resolve));
const cdp = new Cdp(ws);
await cdp.send("Page.enable");
await cdp.send("Runtime.enable");

let allPass = true;

if (process.env.ASSETOPS_LAYOUT_T028_JOURNEY_ONLY === "1") {
  // T028 presentation 2b: the product journey alone, against a Lab-off build
  // and host over an already populated store. Nothing else in this file runs.
  allPass = (await t028Journey({ labOff: true })) && allPass;
  console.log(`\n${allPass ? "ALL CLAIMS HOLD" : "AT LEAST ONE CLAIM FAILED"}\n`);
  ws.close();
  chrome.kill();
  process.exit(allPass ? 0 : 1);
}

if (process.env.ASSETOPS_LAYOUT_S2_01A_RUN) {
  // S2-01a: a run set up from a registered basis, measured alone. The run ID
  // names an already created registered Draft; nothing else in this file runs.
  const runId = process.env.ASSETOPS_LAYOUT_S2_01A_RUN;
  for (const [width, height] of [[1280, 800], [640, 700]]) {
    await visit(cdp, `/simulator-lab/runs/${runId}`, width, height, "[data-run-basis]");
    await waitForSelector(cdp, "[data-commit-state]");
    const read = await cdp.send("Runtime.evaluate", {
      expression: `(() => {
        const doc = document.scrollingElement;
        const basis = document.querySelector("[data-run-basis]");
        const sha = document.querySelector("[data-run-basis-sha256]");
        const meta = document.querySelector("[data-run-basis-site-metadata]");
        const stage = document.querySelector("[data-stage-basis]");
        const commit = [...document.querySelectorAll("button")].find((b) => b.textContent.trim() === "Commit and release");
        const shaBox = sha ? sha.getBoundingClientRect() : null;
        return {
          scrollWidth: doc.scrollWidth, clientWidth: doc.clientWidth,
          basis: basis ? basis.getAttribute("data-run-basis") : null,
          sha: sha ? sha.textContent : "",
          shaRight: shaBox ? Math.round(shaBox.right) : null,
          meta: meta ? meta.parentElement.textContent : "",
          stage: stage ? stage.getAttribute("data-stage-basis") : null,
          commitDisabled: commit ? commit.disabled : null,
          basisBlock: document.querySelector("[data-commit-basis-block]") !== null,
        };
      })()`,
      returnByValue: true,
    });
    const m = read.result.value;
    allPass = report(`S2-01a registered run ${runId} at ${width}x${height}`, m, [
      ["the page does not scroll horizontally", m.scrollWidth <= m.clientWidth, `scrollWidth ${m.scrollWidth} vs clientWidth ${m.clientWidth}`],
      ["the configuration basis is drawn as registered", m.basis === "REGISTERED", String(m.basis)],
      ["the snapshot hash is drawn in full, so the set measured is not empty", /^[0-9a-f]{64}$/.test(m.sha), m.sha],
      ["the hash ends inside the viewport", m.shaRight !== null && m.shaRight <= m.clientWidth, `right ${m.shaRight}`],
      ["Site name and time zone are labelled as setup metadata", /Not chosen by the knowledge time/.test(m.meta), m.meta.slice(0, 60)],
      ["the Stage read is labelled registered", m.stage === "REGISTERED", String(m.stage)],
      ["Commit is disabled with the basis reason", m.commitDisabled === true && m.basisBlock, `disabled ${m.commitDisabled}, basis block ${m.basisBlock}`],
    ]) && allPass;
  }
  console.log(`\n${allPass ? "ALL CLAIMS HOLD" : "AT LEAST ONE CLAIM FAILED"}\n`);
  ws.close();
  chrome.kill();
  process.exit(allPass ? 0 : 1);
}

if (process.env.ASSETOPS_LAYOUT_S2_01B_RUN) {
  // S2-01b: a registered run whose Stage is the gateway ledger, measured alone.
  // The run ID names an already executed registered Draft whose gateway is
  // running; nothing else in this file runs.
  const runId = process.env.ASSETOPS_LAYOUT_S2_01B_RUN;
  for (const [width, height] of [[1280, 800], [640, 700]]) {
    await visit(cdp, `/simulator-lab/runs/${runId}`, width, height, "[data-gateway-ledger]");
    await waitForSelector(cdp, "[data-commit-state]");
    const read = await cdp.send("Runtime.evaluate", {
      expression: `(() => {
        for (const d of document.querySelectorAll("details[data-disclosure]")) d.open = true;
        const doc = document.scrollingElement;
        const right = (el) => (el ? Math.round(el.getBoundingClientRect().right) : null);
        const ledger = document.querySelector("[data-gateway-ledger]");
        const snap = document.querySelector("[data-gateway-snapshot]");
        const pres = [...document.querySelectorAll("[data-gateway-batch-canonical], [data-gateway-envelope-canonical]")];
        const shas = [...document.querySelectorAll("[data-gateway-batch-sha256]")];
        const scrollers = shas.map((s) => s.closest(".data-table__scroll"));
        const commit = [...document.querySelectorAll("button")].find((b) => b.textContent.trim() === "Commit and release");
        return {
          scrollWidth: doc.scrollWidth, clientWidth: doc.clientWidth,
          status: ledger ? ledger.getAttribute("data-gateway-status") : null,
          snapshot: snap ? snap.textContent : "",
          snapshotRight: right(snap),
          upload: document.querySelector("[data-gateway-upload]")?.getAttribute("data-gateway-upload") ?? null,
          receipts: document.querySelector("[data-gateway-receipts]")?.textContent ?? null,
          batches: document.querySelectorAll("[data-gateway-batch]").length,
          envelopes: document.querySelectorAll("[data-gateway-envelope]").length,
          holds: document.querySelectorAll("[data-gateway-hold]").length,
          shaFull: shas.filter((s) => /^[0-9a-f]{64}$/.test(s.textContent)).length,
          scrollersRight: Math.max(0, ...scrollers.map((s) => right(s) ?? 0)),
          pres: pres.length,
          presRight: Math.max(0, ...pres.map(right)),
          presNonEmpty: pres.filter((p) => p.textContent.length > 0).length,
          resolutionCells: document.querySelectorAll("[data-signal-resolution]").length,
          resolutionNote: document.querySelector("[data-signal-resolution-note]") !== null,
          commitDisabled: commit ? commit.disabled : null,
          basisBlock: document.querySelector("[data-commit-basis-block]") !== null,
          resumeOrRetry: [...document.querySelectorAll("button")].some((b) => /Resume release|Retry release/.test(b.textContent)),
        };
      })()`,
      returnByValue: true,
    });
    const m = read.result.value;
    allPass = report(`S2-01b gateway-ledger run ${runId} at ${width}x${height}`, m, [
      ["the page does not scroll horizontally", m.scrollWidth <= m.clientWidth, `scrollWidth ${m.scrollWidth} vs clientWidth ${m.clientWidth}`],
      ["the Stage is the gateway ledger, staged", m.status === "STAGED", String(m.status)],
      ["the snapshot hash is drawn in full and ends inside the viewport", /^[0-9a-f]{64}$/.test(m.snapshot) && m.snapshotRight !== null && m.snapshotRight <= m.clientWidth, `right ${m.snapshotRight}`],
      ["upload is pending with no receipt", m.upload === "PENDING" && m.receipts === "None", `${m.upload} / ${m.receipts}`],
      ["sealed batches are drawn, each with its full SHA-256 (set not empty)", m.batches > 0 && m.shaFull === m.batches, `${m.batches} batches, ${m.shaFull} full digests`],
      ["the batch table scrolls inside its own box", m.scrollersRight <= m.clientWidth, `right ${m.scrollersRight}`],
      ["sealed envelopes are drawn (set not empty)", m.envelopes > 0, `${m.envelopes} envelopes, ${m.holds} holds`],
      ["exact batch and envelope text is shown and ends inside the viewport", m.pres === 2 && m.presNonEmpty === 2 && m.presRight <= m.clientWidth, `${m.pres} blocks, right ${m.presRight}`],
      ["each reporting path shows its resolution, with the half-step note", m.resolutionCells > 0 && m.resolutionNote, `${m.resolutionCells} cells`],
      ["Commit is disabled with the basis reason, and no release is offered", m.commitDisabled === true && m.basisBlock && !m.resumeOrRetry, `disabled ${m.commitDisabled}, basis block ${m.basisBlock}`],
    ]) && allPass;
  }
  console.log(`\n${allPass ? "ALL CLAIMS HOLD" : "AT LEAST ONE CLAIM FAILED"}\n`);
  ws.close();
  chrome.kill();
  process.exit(allPass ? 0 : 1);
}

if (READBACK_ARG > 0) {
  // T025c's second invocation, made after the host was stopped and started
  // again over the same store: no live session exists for the run any more.
  const saved = JSON.parse(readFileSync(READBACK_FILE, "utf-8"));
  await cdp.send("Page.addScriptToEvaluateOnNewDocument", { source: CHARTS_TIMER });
  const runId = saved.href.split("/").pop();
  const before = artifactDigest(runId);
  const reads = [];
  for (const [label, width, height] of [
    ["1280x800", 1280, 800],
    ["640x700", 640, 700],
  ]) {
    await visit(cdp, saved.href, width, height, "[data-chart-panel]");
    const page = await settledCockpit(cdp);
    const read = await readCharts(cdp);
    reads.push(read);
    allPass =
      report(`T025c readback after a host restart, ${saved.href}, at ${label}`, page, [
        [
          "the history is the persisted record with its digest, not a live session",
          read.historySource === "PERSISTED" &&
            read.headerHistory === "PERSISTED" &&
            /^[0-9a-f]{64}$/.test(read.historyDigest ?? ""),
          `source ${read.historySource}; digest ${read.historyDigest}`,
        ],
        [
          "the charts and exact values are the ones drawn before the restart",
          read.fingerprint.length > 0 && read.fingerprint === saved.fingerprint,
          `${read.fingerprint.length} fingerprint characters; before the restart ${saved.fingerprint.length}`,
        ],
        [
          "the port reports the same completed run at the same boundary count",
          read.status === "COMPLETED" && read.boundaries === saved.boundaries,
          `${read.status}; ${read.boundaries} (before: ${saved.boundaries})`,
        ],
        ...chartClaims(read, page, width),
      ]) && allPass;
  }
  const moved = await cursorMoveCost(cdp, 48);
  await pressOnCursor(cdp, "Home", 36);
  const home = await readCharts(cdp);
  const after = artifactDigest(runId);
  allPass =
    report("T025c browsing the reloaded run changes nothing", null, [
      [
        "the keyboard moves the reloaded cursor on every chart, and the run stays where it was",
        home.cursors.join(",") === "0" &&
          home.selected === "0" &&
          home.status === "COMPLETED" &&
          home.boundaries === saved.boundaries,
        `cursor ${home.cursors.join(",")}; ${home.status}; ${home.boundaries}`,
      ],
      [
        "the artifact's bytes are unchanged by every read (ASSETOPS_EVIDENCE_ENV names the store)",
        EVIDENCE_ENV !== null && before !== "missing" && before === after && before === saved.artifact,
        `at completion ${saved.artifact}; before the reads ${before}; after ${after}`,
      ],
      [
        "render cost: one selection change re-renders every reloaded chart within 250 ms",
        moved.ms < 250 && moved.cursor === "240",
        `cursor move to 240 in ${moved.ms} ms; ${mountNote(reads)}`,
      ],
    ]) && allPass;
  if (saved.t025d !== undefined) {
    // T025d after the restart: the same interval inspection, from the
    // persisted record, and a run that was live before is no longer playable.
    await visit(cdp, saved.href, 1280, 800, "[data-drawing-boundary]");
    await settledCockpit(cdp);
    await selectBoundary(cdp, 13, 65);
    await sleep(300);
    const again = await readInspection(cdp);
    let live = null;
    if (saved.t025d.live !== undefined) {
      await visit(cdp, saved.t025d.live, 1280, 800, "[data-execution-status]");
      await sleep(500);
      live = await readInspection(cdp);
    }
    allPass =
      report("T025d readback after a host restart", null, [
        [
          "the drawing, control panel, loads and balance at [60, 65) are the ones shown before the restart",
          again.fingerprint === saved.t025d.inspection,
          `${again.fingerprint.length} characters; before ${saved.t025d.inspection.length}`,
        ],
        [
          "a run that was RUNNING before the restart is INTERRUPTED, paused, and cannot be played",
          live !== null &&
            live.status === "INTERRUPTED" &&
            live.playbackState === "stopped" &&
            live.playEnabled === false,
          live === null ? "no live run was recorded" : `${live.status}; playback ${live.playbackState}; Play ${live.playEnabled}`,
        ],
      ]) && allPass;
  }
  console.log(`\n${allPass ? "ALL CLAIMS HOLD" : "AT LEAST ONE CLAIM FAILED"}\n`);
  ws.close();
  chrome.kill();
  process.exit(allPass ? 0 : 1);
}

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
        // D-2026-10-02-rendered-tabs-per-capability: Overview, Foundation and
        // Evidence render, and nothing else.
        "exactly five tabs are rendered: Overview, Foundation, Performance, Findings, Evidence (T028)",
        site.tabLabels.length === 5 &&
          site.tabLabels.join("|") === "Overview|Foundation|Performance|Findings|Evidence",
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
  report("Landing at / (redirects to /sites) at 1280x800, gate open, short page", short, [
    [
      "/ lands on the Sites index",
      short.finalPathname === "/sites",
      `final pathname ${short.finalPathname}`,
    ],
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
  // S1-03: the phone width the owner compares against the v6.9 mock.
  ["390x844, phone width", 390, 844],
]) {
  // S1-01 (Architect, 2026-10-08): an imported Site's Foundation carries one
  // required enabled action, "Publish reserve change", the only editable
  // Foundation control. S1-02 adds "Publish binding change" (ruling D3; see
  // PUBLISH_BINDING_LABEL), which edits bindings, not a Foundation control.
  // Both are allowed only on an imported Site; every other enabled action
  // still fails.
  const siteImported = (await configurationStore(SITE)) === "POSTGRES";
  // S1-03: an imported Site's Foundation is three views (Site model, Single
  // line diagram, Readiness); each is measured at its own address. The reserve
  // change lives on the Site model, the binding change on Readiness, the
  // diagram on the SLD view, and the densest table (the binding set) on
  // Readiness. A legacy Site keeps its one page, with every claim on it.
  const foundationViews = siteImported
    ? [
        { name: "Site model", suffix: "", diagram: false, reserve: 1, binding: 0, dense: false },
        { name: "Single line diagram", suffix: "/sld", diagram: true, reserve: 0, binding: 0, dense: false },
        { name: "Readiness", suffix: "/readiness", diagram: false, reserve: 0, binding: 1, dense: true },
      ]
    : [{ name: "page", suffix: "", diagram: true, reserve: 0, binding: 0, dense: true }];
  for (const foundationView of foundationViews) {
  const foundation = await visit(
    cdp,
    `/sites/${SITE}/foundation${foundationView.suffix}`,
    width,
    height,
    ".site-tabs",
  );
  const subtabs =
    foundation.navRows.find((row) => row.label === "Foundation views")
      ?.items ?? [];
  const contentsRow = foundation.navRows.find((row) => row.label === "Foundation sections");
  const siteTabs =
    foundation.navRows.find((row) => row.label === "Site sections")?.items ?? [];

  allPass =
    report(`Foundation ${foundationView.name} at ${label}`, foundation, [
      [
        "the page does not scroll horizontally",
        !foundation.pageScrollsHorizontally,
        `scrollWidth ${foundation.pageScrollWidth} vs clientWidth ${foundation.pageClientWidth}`,
      ],
      [
        // D-2026-10-02-rendered-tabs-per-capability (T027 AC23): only the
        // tabs whose capability exists render.
        "the Site tab row is exactly Overview, Foundation, Evidence",
        siteTabs.join("|") === "Overview|Foundation|Performance|Findings|Evidence",
        siteTabs.join(" | "),
      ],
      [
        siteImported
          ? "the Foundation view row is exactly Site model, Single line diagram, Readiness, and no contents row renders"
          : "a legacy Site renders no Foundation view row and no contents row",
        (siteImported
          ? subtabs.join("|") === "Site model|Single line diagram|Readiness"
          : subtabs.length === 0) && contentsRow === undefined,
        subtabs.join(" | ") || "no view row",
      ],
      [
        siteImported
          ? "no enabled action renders except the imported Site's Publish reserve change and Publish binding change"
          : "no enabled action renders",
        foundation.buttons.every(
          (b) => b.disabled || (siteImported && IMPORTED_SITE_ACTIONS.has(b.label)),
        ),
        foundation.buttons.length === 0
          ? "no action rendered"
          : foundation.buttons.map((b) => `${b.label}${b.disabled ? " (disabled)" : ""}`).join(", "),
      ],
      ...(siteImported
        ? [
            [
              `Publish reserve change renders, enabled, ${foundationView.reserve} time(s) on this view`,
              foundation.buttons.filter((b) => b.label === PUBLISH_RESERVE_LABEL && !b.disabled).length ===
                foundationView.reserve,
              `${foundation.buttons.filter((b) => b.label === PUBLISH_RESERVE_LABEL).length} found`,
            ],
            [
              `Publish binding change renders at most ${foundationView.binding} time(s) on this view`,
              foundation.buttons.filter((b) => b.label === PUBLISH_BINDING_LABEL).length <= foundationView.binding,
              `${foundation.buttons.filter((b) => b.label === PUBLISH_BINDING_LABEL).length} found`,
            ],
          ]
        : []),
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
      ...(width <= 640 && foundationView.dense
        ? [
            [
              "at least one table overflows here, so the claim above is not vacuous",
              foundation.scrollers.some((s) => s.overflows),
              `${foundation.scrollers.filter((s) => s.overflows).length} of ${foundation.scrollers.length} overflow`,
            ],
          ]
        : []),
      ...(width <= 640 && foundationView.diagram
        ? [
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
      ...(foundationView.diagram
        ? [
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
          ]
        : [
            [
              "no diagram is drawn on a view that is not the diagram",
              foundation.diagrams.length === 0,
              `${foundation.diagrams.length} diagram regions`,
            ],
          ]),
    ]) && allPass;
  }
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
        // Measured over buttons. The enabled controls this screen carries are
        // links (Create Draft Run and the back links), deliberately outside
        // this set; T025g removed the target-site link.
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
              // T027: the Commit control renders on every Draft and is
              // disabled with its reason until the run completes; it is not a
              // run action, so it is held to "disabled" rather than "absent".
              "a blocked draft offers no run action at all, and Commit is disabled",
              run.buttons.every((b) => b.label === "Commit and release" && b.disabled),
              run.buttons.map((b) => `${b.label}:${b.disabled ? "disabled" : "ENABLED"}`).join(", ") ||
                "no button rendered",
            ]
          : [
              // T022 replaced the one disabled "Run this draft" control with
              // three real ones. The claim moves with it: a closed set by NAME,
              // and at least one of them enabled - because a ready draft whose
              // controls were all disabled would satisfy a count and assert
              // nothing about a Lab that can execute. T025d adds exactly two:
              // auto-play of the guarded Step, and its pause.
              // T027 adds the Commit control, disabled until the run completes.
              "a ready draft offers exactly the three execution controls and auto-play's two, at least one enabled, and a disabled Commit",
              run.buttons.filter((b) => b.label !== "Commit and release").map((b) => b.label).join("|") ===
                "Start this run|Step|Run to the end|Play|Pause" &&
                run.buttons.some((b) => b.label !== "Commit and release" && !b.disabled) &&
                run.buttons.filter((b) => b.label === "Commit and release").length === 1 &&
                run.buttons.every((b) => b.label !== "Commit and release" || b.disabled),
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
      // fails this claim. T025e: the Applied timeline's "at T min" buttons
      // move the history cursor (a read); they are excluded the same way.
      // T027: Commit and release is the commit act a completed run offers,
      // not an execution control; the T027 section measures it.
      "a terminal run offers no enabled execution control",
      finished.buttons.some((b) => !/^(Show envelope \d+|at \d+ min|Commit and release)$/.test(b.label)) &&
        finished.buttons
          .filter((b) => !/^(Show envelope \d+|at \d+ min|Commit and release)$/.test(b.label))
          .every((b) => b.disabled),
      finished.buttons
        .filter((b) => !/^(Show envelope \d+|at \d+ min|Commit and release)$/.test(b.label))
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

// S1-01 (Architect, 2026-10-08): once the Kobo Site is imported into the
// stored Foundation, the Lab refuses new Drafts, execution and Commit against
// it until S2 restores the registered Lab path. Every section from here on
// (T024-T028) creates, drives or commits a Kobo Draft, or reads the Kobo
// product screens those commits fill, so they are reported as inapplicable -
// not passed, not deleted - and run again unchanged when Kobo is not imported.
if ((await configurationStore(process.env.ASSETOPS_KOBO_SITE ?? "KOBO-001")) === "POSTGRES") {
  console.log(
    "\n=== Kobo Lab run and Commit sections (T024-T028) ===\n" +
      "  SKIP  inapplicable until S2: KOBO-001 is imported into the stored Foundation and the Lab " +
      "refuses Draft setup, start, step, run-to-end and Commit against it (S1-01). Not counted as passed.",
  );
  finishRun();
}

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
  const radio = Array.from(document.querySelectorAll('input[name="run-setup-site"]')).find(
    (item) => item.value === ${JSON.stringify(KOBO_SITE)},
  );
  if (radio) radio.click();
  const filled =
    !!radio &&
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

// T026: the same Draft setup against `mini-grid` v3 under publication profile 5
// (records, gaps and delays published; the generator status staged).
const submitV3Setup = (start, end) =>
  submitV2Setup(start, end)
    .replace('"mini-grid@2"', '"mini-grid@3"')
    .replace('"simulator-lab-publication@4"', '"simulator-lab-publication@5"');

// Which signals a run's stage lists as "observed, not staged", by publication
// profile: profile 4 does not stage the generator status, profile 5 does.
const EXPECT_UNSTAGED = { 4: ["generator-controller:status"], 5: [] };

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
          "profile 4 discloses the status as observed and not staged, and it is read as a member",
          read.unstaged.join(",") === EXPECT_UNSTAGED[4].join(",") &&
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

// --- T025c: the recorded day curves of the completed changed-policy run ----
//
// The stop-60 run T025b just completed, drawn at three widths. The first
// invocation also records the run, its fingerprint and its artifact digest for
// the `--readback` pass made after a host restart.
{
  await cdp.send("Page.addScriptToEvaluateOnNewDocument", { source: CHARTS_TIMER });
  const href = v2Runs["kobo-mini-grid-stop-60"];
  let previous = null;
  const reads = [];
  for (const [label, width, height] of [
    ["1280x800, the committed minimum", 1280, 800],
    ["1000x700", 1000, 700],
    ["640x700", 640, 700],
  ]) {
    await visit(cdp, href, width, height, "[data-chart-panel]");
    const page = await settledCockpit(cdp);
    const read = await readCharts(cdp);
    reads.push(read);
    allPass =
      report(`T025c recorded day curves, kobo-mini-grid-stop-60 completed, at ${label}`, page, [
        ...chartClaims(read, page, width),
        [
          "the selection opens at the last recorded boundary on every chart and in the inspector",
          read.cursors.join(",") === "480" && read.selected === "480",
          `cursor ${read.cursors.join(",")}; inspector ${read.selected}`,
        ],
        [
          "the same record fingerprints the same at every width",
          read.fingerprint.length > 0 && (previous === null || read.fingerprint === previous),
          `${read.fingerprint.length} characters`,
        ],
        ...(width <= 640
          ? [
              [
                "the charts overflow their regions here, so the scrolling claim above is not vacuous",
                read.panels.some((p) => p.overflows),
                `${read.panels.filter((p) => p.overflows).length} overflow`,
              ],
            ]
          : []),
      ]) && allPass;
    previous = read.fingerprint;
  }
  await pressOnCursor(cdp, "ArrowLeft", 37);
  const left = await readCharts(cdp);
  await pressOnCursor(cdp, "Home", 36);
  const home = await readCharts(cdp);
  const moved = await cursorMoveCost(cdp, 48);
  allPass =
    report("T025c the shared cursor, by keyboard, reads and never executes", null, [
      [
        "ArrowLeft moves every chart and the inspector to the previous boundary",
        left.cursors.join(",") === "475" && left.selected === "475",
        `cursor ${left.cursors.join(",")}; inspector ${left.selected}`,
      ],
      [
        "Home moves them to the first boundary, where no step has ended yet",
        home.cursors.join(",") === "0" && home.selected === "0" && home.valueRows > 0,
        `cursor ${home.cursors.join(",")}; ${home.valueRows} exact-value rows`,
      ],
      [
        "browsing did not move the run: still completed at the same boundary count",
        home.status === "COMPLETED" && home.boundaries === reads[0].boundaries,
        `${home.status}; ${home.boundaries}`,
      ],
      [
        "render cost: one selection change re-renders every chart within 250 ms",
        moved.ms < 250 && moved.cursor === "240",
        `cursor move to 240 in ${moved.ms} ms; ${mountNote(reads)}`,
      ],
    ]) && allPass;
  const runId = href.split("/").pop();
  writeFileSync(
    READBACK_FILE,
    JSON.stringify({
      href,
      fingerprint: previous,
      boundaries: reads[0].boundaries,
      artifact: artifactDigest(runId),
    }),
  );
  console.log(`\n  T025c: recorded ${href} for the --readback pass in ${READBACK_FILE}`);
}

// --- T025d: one selected interval explained, and guarded auto-play ----------
//
// On the completed stop-60 run: the interval that ended at 65, [60, 65), is a
// PCS-limited discharge inside the reporting gap; [130, 135) is a PCS-limited
// charge. The drawing, the control panel and the timeline are measured at
// three widths there, the battery branch is checked to reverse, and the
// keyboard moves the whole inspection. Then a fresh Draft of the same recipe is
// auto-played, paused, reloaded and run to the end, and its digests compared
// with the completed run's.
const t025d = {};
{
  const href = v2Runs["kobo-mini-grid-stop-60"];
  const reads = [];
  for (const [label, width, height] of [
    ["1280x800, the committed minimum", 1280, 800],
    ["1000x700", 1000, 700],
    ["640x700", 640, 700],
  ]) {
    await visit(cdp, href, width, height, "[data-drawing-boundary]");
    await settledCockpit(cdp);
    const moved = await selectBoundary(cdp, 13, 65);
    await sleep(300);
    const read = await readInspection(cdp);
    reads.push(read);
    allPass =
      report(`T025d the interval [60, 65) of the completed stop-60 run at ${label}`, null, [
        ...inspectionClaims(read, width),
        [
          "the selected boundary is 65 on the cursor, the inspector and the drawing",
          moved.follows && read.selected === "65" && read.drawingBoundary === "65",
          `inspector ${read.selected}; drawing ${read.drawingBoundary}`,
        ],
        [
          "the battery request differs from what was accepted (the PCS limit), and says so",
          read.controls.some((c) => c.startsWith("battery-power at battery-state-of-charge@battery:") && c.endsWith(":yes")),
          read.controls.join("; "),
        ],
        [
          "the PCS branch is drawn with a direction at this interval",
          ["ALONG", "AGAINST"].includes(read.directions["pcs-to-bus"]),
          `pcs-to-bus ${read.directions["pcs-to-bus"]}`,
        ],
        ...(width <= 640
          ? [
              [
                "at 640 the timeline or balance tables overflow their own regions, so the containment claim is not vacuous",
                read.timelineRegions.some((r) => r && r.overflows) ||
                  (read.balanceRegion !== null && read.balanceRegion.overflows),
                `timeline ${read.timelineRegions.map((r) => (r && r.overflows ? "overflows" : "fits")).join(",")}; balance ${read.balanceRegion && read.balanceRegion.overflows ? "overflows" : "fits"}`,
              ],
            ]
          : []),
      ]) && allPass;
  }
  t025d.inspection = reads[0].fingerprint;
  const discharge = reads[0];
  const charge = (await selectBoundary(cdp, 27, 135), await sleep(300), await readInspection(cdp));
  await selectBoundary(cdp, 13, 65);
  await sleep(200);
  await pressOnCursor(cdp, "ArrowRight", 39);
  const next = await readInspection(cdp);
  const cost = await selectBoundary(cdp, 48, 240);
  allPass =
    report("T025d reversal, keyboard and cost on the completed run", null, [
      [
        "the battery branch reverses between [60, 65) and [130, 135)",
        ["ALONG", "AGAINST"].includes(discharge.directions["pcs-to-bus"]) &&
          ["ALONG", "AGAINST"].includes(charge.directions["pcs-to-bus"]) &&
          discharge.directions["pcs-to-bus"] !== charge.directions["pcs-to-bus"],
        `pcs-to-bus ${discharge.directions["pcs-to-bus"]} then ${charge.directions["pcs-to-bus"]}`,
      ],
      [
        "ArrowRight on the cursor moves the drawing and the control panel to [65, 70), the reserve-limited interval",
        next.drawingBoundary === "70" &&
          next.selected === "70" &&
          next.controls.some((c) => c.startsWith("battery-power at battery-state-of-charge@battery:") && c.endsWith(":yes")) &&
          next.fingerprint !== discharge.fingerprint,
        `drawing ${next.drawingBoundary}; ${next.controls.join("; ")}`,
      ],
      [
        "browsing did not move the run",
        next.status === "COMPLETED" && next.boundaries === discharge.boundaries,
        `${next.status}; ${next.boundaries}`,
      ],
      [
        "render cost: one selection re-renders the drawing, panels and charts within 250 ms",
        cost.follows && cost.ms < 250,
        `${cost.ms} ms to boundary 240`,
      ],
    ]) && allPass;
  t025d.completed = { trajectory: discharge.trajectory, readings: discharge.readings, inputs: discharge.inputs };
}

{
  // A fresh Draft of the same recipe and window, auto-played.
  await cdp.send("Page.addScriptToEvaluateOnNewDocument", { source: STEP_COUNTER });
  await visit(cdp, "/simulator-lab/scenarios/kobo-mini-grid-stop-60/run-setup", 1280, 800, "form", {
    script: submitV2Setup("2026-09-22T03:00:00Z", "2026-09-22T11:00:00Z"),
    waitFor: ".data-table__scroll",
  });
  const listed = await visit(cdp, "/simulator-lab/runs", 1280, 800, "table");
  const href = listed.runRows.find((row) => row.status === "READY")?.href ?? null;
  if (href === null || Object.values(v2Runs).includes(href)) {
    throw new Error("No new READY stop-60 Draft was found for the T025d auto-play pass.");
  }
  await visit(cdp, href, 1280, 800, "[data-execution-status]", {
    script: clickControl("Start this run"),
    waitFor: "[data-execution-status='RUNNING']",
  });
  const fresh = await readInspection(cdp);
  await cdp.send("Runtime.evaluate", { expression: selectDelay(250) });
  await sleep(200);
  const historyBefore = (await readInspection(cdp)).steps.historyReads;
  await cdp.send("Runtime.evaluate", { expression: clickControl("Play") });
  await sleep(300);
  const playing = await readInspection(cdp);
  const manualDisabled = (
    await cdp.send("Runtime.evaluate", {
      expression: `Array.from(document.querySelectorAll('main button')).filter((b) => ['Step', 'Run to the end'].includes((b.textContent || '').trim())).every((b) => b.disabled)`,
      returnByValue: true,
    })
  ).result.value;
  await sleep(2500);
  const midway = await readInspection(cdp);
  await cdp.send("Runtime.evaluate", { expression: clickControl("Pause") });
  await waitForSelector(cdp, "[data-playback-reason='PAUSED']");
  await sleep(300);
  const paused = await readInspection(cdp);
  await sleep(1500);
  const later = await readInspection(cdp);
  allPass =
    report("T025d auto-play of a fresh stop-60 Draft (0.25 s wall delay)", null, [
      [
        "a page that has not been told to play is paused, over a RUNNING execution",
        fresh.playbackState === "stopped" && fresh.playbackReason === "" && fresh.status === "RUNNING",
        `playback ${fresh.playbackState}/${fresh.playbackReason || "none"}; execution ${fresh.status}`,
      ],
      [
        "while it plays, Step and Run to the end are unavailable",
        playing.playbackState === "playing" && manualDisabled === true,
        `playback ${playing.playbackState}; manual disabled ${manualDisabled}`,
      ],
      [
        "it sent several steps, never more than one in flight",
        midway.steps.count >= 3 && midway.steps.maxOpen === 1,
        `${midway.steps.count} steps; at most ${midway.steps.maxOpen} in flight`,
      ],
      [
        "T025e: the recorded history follows each step by a delta, never a full read per step",
        midway.steps.historyReads === historyBefore && (midway.steps.deltaReads || 0) >= midway.steps.count - 1,
        `${historyBefore} full reads before play, ${midway.steps.historyReads} while playing; ${midway.steps.deltaReads || 0} delta reads for ${midway.steps.count} steps`,
      ],
      [
        "pause stops scheduling: nothing is sent and the position holds",
        paused.playbackReason === "PAUSED" &&
          later.steps.count === paused.steps.count &&
          later.boundaries === paused.boundaries &&
          later.status === "RUNNING",
        `paused at ${paused.boundaries} after ${paused.steps.count} steps; 1.5 s later ${later.boundaries}, ${later.steps.count} steps`,
      ],
      [
        "T025e: stopping makes no history read (read-on-stop retired by live follow)",
        later.steps.historyReads === historyBefore,
        `${later.steps.historyReads} full history reads`,
      ],
    ]) && allPass;

  await visit(cdp, href, 1280, 800, "[data-execution-status]");
  await settledCockpit(cdp).catch(() => null);
  const reloaded = await readInspection(cdp);
  allPass =
    report("T025d a reload starts paused and the host still holds the run", null, [
      [
        "after reload: paused, at the paused position, and Play is offered because the execution is live",
        reloaded.playbackState === "stopped" &&
          reloaded.playbackReason === "" &&
          reloaded.status === "RUNNING" &&
          reloaded.boundaries === paused.boundaries &&
          reloaded.playEnabled === true &&
          reloaded.steps.count === 0,
        `${reloaded.playbackState}/${reloaded.playbackReason || "none"}; ${reloaded.status} at ${reloaded.boundaries}; Play ${reloaded.playEnabled}; ${reloaded.steps.count} steps sent`,
      ],
    ]) && allPass;

  // Paced differently (auto-play, then one Run to the end) from the completed
  // run (Run to the end at once): same frozen recipe, so same digests.
  await visit(cdp, href, 1280, 800, "[data-execution-status]", {
    script: clickControl("Run to the end"),
    waitFor: "[data-execution-status='COMPLETED']",
  });
  await settledCockpit(cdp).catch(() => null);
  const finished = await readInspection(cdp);
  allPass =
    report("T025d pacing changes nothing physical or observed", null, [
      // The trajectory digest is bound to the run identity, so two Drafts
      // never share one; the same run paced three ways is compared on it in
      // host/tests/test_lab_cockpit_window.py. Across Drafts the frozen
      // inputs identity and the reading series digest are run-independent.
      [
        "the two Drafts froze the same inputs, so the comparison below is meaningful",
        /^[0-9a-f]{64}$/.test(finished.inputs ?? "") && finished.inputs === t025d.completed.inputs,
        `${finished.inputs} vs ${t025d.completed.inputs}`,
      ],
      [
        "the auto-played run's reading series digest equals the run completed in one request",
        /^[0-9a-f]{64}$/.test(finished.readings ?? "") && finished.readings === t025d.completed.readings,
        `${finished.readings} vs ${t025d.completed.readings}`,
      ],
      [
        "both reached an outcome with a trajectory digest (run-bound, compared per run on the host)",
        /^[0-9a-f]{64}$/.test(finished.trajectory ?? "") && /^[0-9a-f]{64}$/.test(t025d.completed.trajectory ?? ""),
        `${finished.trajectory}; ${t025d.completed.trajectory}`,
      ],
    ]) && allPass;
  t025d.played = href;
}

// --- T025e: the organised cockpit, live follow and no intermediate frames ---
//
// AC12. A fresh degraded-evidence Draft (`mini-grid` v3 / publication profile 5,
// 8 h at 5 min, so records, a gap and a held publication are in every capture;
// T026 AC15 re-measures it with those rows) is auto-played at the
// 0.25 s delay for at least 20 steps with the history cursor live, sampled on
// every animation frame; then with the cursor pinned, watched by a
// MutationObserver. Delta bytes, the client commit time and the server's
// delta time at the window's last live boundary are measured over HTTP on the
// running app. Disclosures are opened before anything is measured.

/** Sample the cockpit on every animation frame and summarise in the page. */
const T025E_SAMPLER = `(() => {
  const S = window.__t025e = { running: true, frames: 0, cockpit: new Set(), stage: new Set(), cursorBox: new Set(),
    charts: new Set(), xTicks: new Set(), yTicks: {}, disagree: 0, disagreeExample: null, empty: 0,
    drawingBoundaries: new Set(), firstRecorded: null, lastRecorded: null };
  const box = (el) => { if (!el) return 'none'; const b = el.getBoundingClientRect();
    return [Math.round(b.top + window.scrollY), Math.round(b.height), Math.round(b.left), Math.round(b.width)].join(','); };
  const attr = (sel, name) => { const el = document.querySelector(sel); return el ? el.getAttribute(name) : null; };
  const tick = () => {
    if (!S.running) return;
    S.frames += 1;
    S.cockpit.add(box(document.querySelector('[data-cockpit]')));
    S.stage.add(box(document.querySelector('.run-cockpit__drawing')) + '|' + box(document.querySelector('.run-cockpit__inspection')));
    S.cursorBox.add(box(document.querySelector('[data-history-cursor]')));
    const panels = Array.from(document.querySelectorAll('[data-chart-panel]'));
    S.charts.add(panels.map((f) => f.getAttribute('data-chart-panel') + ':' + box(f)).join('|'));
    S.xTicks.add(panels.map((f) => Array.from(f.querySelectorAll('text.history-chart__label[text-anchor="middle"]')).map((t) => t.textContent).join(',')).join('|'));
    for (const f of panels) {
      const id = f.getAttribute('data-chart-panel');
      const y = Array.from(f.querySelectorAll('text.history-chart__label[text-anchor="end"]')).map((t) => t.textContent).join(',');
      const seen = S.yTicks[id] || (S.yTicks[id] = { last: y, changes: [] });
      if (seen.last !== y) { seen.changes.push(seen.last + ' -> ' + y); seen.last = y; }
    }
    const four = [attr('[data-drawing-boundary]', 'data-drawing-boundary'), attr('[data-chart-cursor]', 'data-chart-cursor'),
      attr('[data-timeline-boundary]', 'data-timeline-boundary'), attr('[data-inspection-boundary]', 'data-inspection-boundary')];
    if (four.some((v) => v === null) || new Set(four).size !== 1) { S.disagree += 1; if (S.disagreeExample === null) S.disagreeExample = four.join('/'); }
    S.drawingBoundaries.add(four[0]);
    const paths = Array.from(document.querySelectorAll('[data-chart-series]')).filter((p) => (p.getAttribute('d') || '').length > 0).length;
    if (paths === 0 || document.querySelector('[data-drawing-bound] svg') === null) S.empty += 1;
    const recorded = (document.querySelector('[data-history-recorded]') || {}).textContent || null;
    if (S.firstRecorded === null) S.firstRecorded = recorded;
    S.lastRecorded = recorded;
    requestAnimationFrame(tick);
  };
  requestAnimationFrame(tick);
  return true;
})()`;

const T025E_STOP_SAMPLER = `(() => {
  const S = window.__t025e; S.running = false;
  const list = (set) => Array.from(set);
  const yChanges = Object.fromEntries(Object.entries(S.yTicks).map(([id, v]) => [id, v.changes]));
  return { frames: S.frames, cockpit: list(S.cockpit), stage: list(S.stage), cursorBox: list(S.cursorBox), charts: list(S.charts).length,
    chartsFirst: list(S.charts)[0], xTicks: list(S.xTicks).length, yChanges, disagree: S.disagree, disagreeExample: S.disagreeExample,
    empty: S.empty, drawingBoundaries: S.drawingBoundaries.size, firstRecorded: S.firstRecorded, lastRecorded: S.lastRecorded };
})()`;

/** Watch the pinned drawing and inspection, and the charts as a control. */
const T025E_OBSERVE_PINNED = `(() => {
  const P = window.__t025ePinned = { sld: 0, inspection: 0, charts: 0 };
  const watch = (sel, key) => new MutationObserver((m) => { P[key] += m.length; })
    .observe(document.querySelector(sel), { subtree: true, childList: true, attributes: true, characterData: true });
  watch('.run-cockpit__drawing', 'sld');
  watch('.run-cockpit__inspection', 'inspection');
  watch('.run-cockpit__charts', 'charts');
  return true;
})()`;

/** Timings and bytes the page recorded, read once. */
const T025E_TIMINGS = `(() => {
  const deltas = performance.getEntriesByType('resource').filter((e) => e.name.includes('since_boundary='));
  const commits = performance.getEntriesByName('run-frame-commit').map((e) => e.duration);
  return {
    deltaBytes: deltas.map((e) => e.decodedBodySize),
    deltaTransfer: deltas.map((e) => e.transferSize),
    deltaUrl: deltas.length ? deltas[deltas.length - 1].name : null,
    commits,
    steps: window.__t025dSteps,
  };
})()`;

const percentile = (values, p) => {
  if (values.length === 0) return null;
  const sorted = [...values].sort((a, b) => a - b);
  return sorted[Math.min(sorted.length - 1, Math.ceil((p / 100) * sorted.length) - 1)];
};

const setStepCount = (count) => `(() => {
  const size = document.getElementById('run-step-boundaries');
  if (!size) return 'controls-missing';
  const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
  setter.call(size, '${count}');
  size.dispatchEvent(new Event('input', { bubbles: true }));
  return true;
})()`;

async function evaluate(expression, awaitPromise = false) {
  return (await cdp.send("Runtime.evaluate", { expression, returnByValue: true, awaitPromise })).result.value;
}

async function waitUntil(expression, timeoutMs) {
  const until = Date.now() + timeoutMs;
  while (Date.now() < until) {
    if ((await evaluate(expression)) === true) return true;
    await sleep(100);
  }
  return false;
}

async function clickAndWait(label) {
  for (let attempt = 0; attempt < 40; attempt += 1) {
    const answer = await evaluate(clickControl(label));
    if (answer === true) return true;
    if (answer === "controls-missing") return false;
    await sleep(150);
  }
  return false;
}

const clock = `Number(document.querySelector('[data-execution-clock]')?.getAttribute('data-execution-clock') ?? -1)`;

{
  await cdp.send("Page.addScriptToEvaluateOnNewDocument", {
    source: "try { performance.setResourceTimingBufferSize(10000); } catch (e) {}",
  });
  await visit(cdp, "/simulator-lab/scenarios/kobo-mini-grid-degraded-evidence/run-setup", 1280, 800, "form", {
    script: submitV3Setup("2026-09-22T03:00:00Z", "2026-09-22T11:00:00Z"),
    waitFor: ".data-table__scroll",
  });
  const listed = await visit(cdp, "/simulator-lab/runs", 1280, 800, "table");
  const href = listed.runRows.find((row) => row.status === "READY")?.href ?? null;
  if (href === null || Object.values(v2Runs).includes(href) || href === t025d.played) {
    throw new Error("No new READY degraded-evidence Draft was found for the T025e pass.");
  }
  await visit(cdp, href, 1280, 800, "[data-execution-status]");
  await waitForSelector(cdp, "[data-cockpit]");
  const geometry = `(() => {
    const box = (sel) => { const el = document.querySelector(sel); if (!el) return null; const b = el.getBoundingClientRect();
      return { top: Math.round(b.top + window.scrollY), height: Math.round(b.height) }; };
    const main = document.querySelector('main');
    const strip = box('[data-control-strip]');
    return { cockpit: box('[data-cockpit]'), strip, stage: box('.run-cockpit__stage'), cursor: box('[data-history-cursor]'),
      charts: box('.run-cockpit__charts'), timeline: box('.run-cockpit__timeline'),
      mainTop: main ? Math.round(main.getBoundingClientRect().top + window.scrollY) : null,
      viewport: window.innerHeight,
      openDisclosures: Array.from(document.querySelectorAll('details')).filter((d) => d.open).length,
      disclosures: document.querySelectorAll('details[data-disclosure]').length };
  })()`;
  // `visit` opened every disclosure to measure it; the first viewport is
  // judged as a reader first sees it, with every disclosure closed.
  await evaluate("document.querySelectorAll('details').forEach((d) => { d.open = false; }); true");
  await sleep(200);
  const beforeStart = await evaluate(geometry);
  await clickAndWait("Start this run");
  await waitForSelector(cdp, "[data-execution-status='RUNNING']");
  await sleep(600);
  const afterStart = await evaluate(geometry);
  await evaluate(setStepCount(1));
  await clickAndWait("Step");
  await waitUntil(`${clock} >= 2`, 15000);
  await sleep(600);
  const afterFirst = await evaluate(geometry);
  await clickAndWait("Step");
  await waitUntil(`${clock} >= 3`, 15000);
  await sleep(600);
  const afterSecond = await evaluate(geometry);
  allPass =
    report("T025e the first viewport at 1280 is the organised cockpit", null, [
      [
        "the page opens with every disclosure closed, and there are some",
        beforeStart.openDisclosures === 0 && beforeStart.disclosures >= 8,
        `${beforeStart.disclosures} disclosures, ${beforeStart.openDisclosures} open`,
      ],
      [
        "the control strip and the drawing-and-inspection row start inside the first 800 px viewport, the history cursor right under them",
        afterStart.strip !== null && afterStart.stage !== null && afterStart.cursor !== null &&
          afterStart.strip.top < 800 && afterStart.stage.top < 800 &&
          afterStart.cursor.top - (afterStart.stage.top + afterStart.stage.height) < 40,
        `strip at ${afterStart.strip?.top} (${afterStart.strip?.height} px); stage at ${afterStart.stage?.top} (${afterStart.stage?.height} px); cursor at ${afterStart.cursor?.top}; charts at ${afterStart.charts?.top}`,
      ],
      [
        "Start, the first step and the second step do not move the cockpit, its drawing row or the cursor",
        [afterStart, afterFirst, afterSecond].every(
          (g) => g.cockpit.top === beforeStart.cockpit.top && g.stage.top === beforeStart.stage.top &&
            g.stage.height === beforeStart.stage.height && g.cursor.top === beforeStart.cursor.top,
        ),
        [beforeStart, afterStart, afterFirst, afterSecond].map((g) => `cockpit ${g.cockpit.top}, stage ${g.stage.top}+${g.stage.height}, cursor ${g.cursor.top}, charts ${g.charts.height}, timeline ${g.timeline.top}`).join(" | "),
      ],
    ]) && allPass;

  // Live: at least 20 auto-played steps at 0.25 s, every animation frame,
  // with every disclosure open - the harder case: their per-step tables grow
  // below the cockpit and "How playback works" sits inside the strip.
  await evaluate("document.querySelectorAll('details').forEach((d) => { d.open = true; }); true");
  await sleep(300);
  await evaluate(selectDelay(250));
  await sleep(200);
  await evaluate("performance.clearMeasures('run-frame-commit'); true");
  const fullBefore = (await evaluate("window.__t025dSteps.historyReads"));
  const stepsBefore = (await evaluate("window.__t025dSteps.count"));
  await evaluate(T025E_SAMPLER);
  await clickAndWait("Play");
  const reached = await waitUntil(`window.__t025dSteps.count >= ${stepsBefore + 22}`, 90000);
  await clickAndWait("Pause");
  await waitForSelector(cdp, "[data-playback-reason='PAUSED']");
  await sleep(400);
  const live = await evaluate(T025E_STOP_SAMPLER);
  const liveTimings = await evaluate(T025E_TIMINGS);
  const liveSteps = liveTimings.steps.count - stepsBefore;
  const yWorst = Math.max(0, ...Object.values(live.yChanges).map((c) => c.length));
  allPass =
    report("T025e live follow at 0.25 s, sampled on every animation frame", null, [
      [
        "at least 20 steps were auto-played and the cursor followed through them, so the claims below are not vacuous",
        reached && liveSteps >= 20 && live.drawingBoundaries >= 20 && live.frames > liveSteps,
        `${liveSteps} steps; ${live.drawingBoundaries} distinct drawing boundaries; ${live.frames} frames; recorded ${live.firstRecorded} -> ${live.lastRecorded}`,
      ],
      [
        "the cockpit's top edge and height never moved",
        live.cockpit.length === 1,
        live.cockpit.join(" ; "),
      ],
      [
        "the drawing and inspection boxes and the history cursor never moved",
        live.stage.length === 1 && live.cursorBox.length === 1,
        `${live.stage.join(" ; ")} / ${live.cursorBox.join(" ; ")}`,
      ],
      [
        "no chart box moved",
        live.charts === 1,
        `${live.charts} distinct chart layouts; ${live.chartsFirst}`,
      ],
      [
        "the x-axis ticks were identical in every frame",
        live.xTicks === 1,
        `${live.xTicks} distinct x tick sets`,
      ],
      [
        "the y-axis ticks changed only at logged ratchets, at most 3 per panel",
        yWorst <= 3,
        Object.entries(live.yChanges).filter(([, c]) => c.length > 0).map(([id, c]) => `${id}: ${c.join(" ; ")}`).join(" | ") || "no ratchet",
      ],
      [
        "the drawing, chart cursor, timeline and inspection named the same boundary in every frame",
        live.disagree === 0,
        live.disagree === 0 ? `${live.frames} frames agree` : `${live.disagree} frames disagree, e.g. ${live.disagreeExample}`,
      ],
      [
        "no frame had an empty drawing or empty charts",
        live.empty === 0,
        `${live.empty} empty frames`,
      ],
      [
        "no full history read between the first step and the terminal answer",
        liveTimings.steps.historyReads === fullBefore,
        `${fullBefore} full reads before play; ${liveTimings.steps.historyReads} after ${liveSteps} steps`,
      ],
    ]) && allPass;

  // Pinned: an earlier boundary held while play continues.
  await evaluate(`(() => {
    const range = document.getElementById('history-cursor-range');
    const setter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set;
    setter.call(range, '5');
    range.dispatchEvent(new Event('input', { bubbles: true }));
    return true;
  })()`);
  await sleep(400);
  const pinnedAt = await evaluate("document.querySelector('[data-drawing-boundary]')?.getAttribute('data-drawing-boundary')");
  await evaluate(T025E_OBSERVE_PINNED);
  const pinnedFrom = await evaluate("window.__t025dSteps.count");
  await clickAndWait("Resume");
  await waitUntil(`window.__t025dSteps.count >= ${pinnedFrom + 6}`, 30000);
  await clickAndWait("Pause");
  await waitForSelector(cdp, "[data-playback-reason='PAUSED']");
  await sleep(400);
  const pinned = await evaluate(`({ ...window.__t025ePinned, at: document.querySelector('[data-drawing-boundary]')?.getAttribute('data-drawing-boundary'),
    mode: document.querySelector('[data-history-cursor]')?.getAttribute('data-history-cursor') })`);
  const pinnedSteps = (await evaluate("window.__t025dSteps.count")) - pinnedFrom;
  allPass =
    report("T025e a pinned cursor holds while play continues", null, [
      [
        "play went on while pinned, and the charts did change (so the observer was live)",
        pinnedSteps >= 5 && pinned.charts > 0 && pinned.mode === "pinned" && pinned.at === pinnedAt,
        `${pinnedSteps} steps pinned at ${pinnedAt}; ${pinned.charts} chart mutations; cursor ${pinned.mode} at ${pinned.at}`,
      ],
      [
        "zero mutations on the pinned drawing and inspection nodes",
        pinned.sld === 0 && pinned.inspection === 0,
        `${pinned.sld} drawing, ${pinned.inspection} inspection mutations`,
      ],
    ]) && allPass;

  // Every delta so far covered one boundary: auto-played or a Step of one.
  const followed = await evaluate(T025E_TIMINGS);
  // To the window's last live boundary, then the server's delta time there.
  const at = await evaluate(clock);
  await evaluate("document.querySelector('[data-return-to-live-slot] button')?.click(); true");
  await evaluate(setStepCount(96 - at));
  await clickAndWait("Step");
  await waitUntil(`${clock} === 96`, 60000);
  await sleep(800);
  const server = await evaluate(`(async () => {
    const recorded = Number((document.querySelector('[data-history-recorded]').textContent || '').split(' ')[0]);
    const url = performance.getEntriesByType('resource').filter((e) => e.name.includes('since_boundary=')).pop().name.replace(/since_boundary=[0-9]+/, 'since_boundary=' + (recorded - 1));
    const wall = [];
    let bytes = 0;
    for (let i = 0; i < 40; i += 1) {
      const t0 = performance.now();
      const response = await fetch(url);
      const body = await response.text();
      wall.push(performance.now() - t0);
      bytes = body.length;
    }
    const entries = performance.getEntriesByType('resource').filter((e) => e.name === url).slice(-40);
    return { recorded, url, wall, ttfb: entries.map((e) => e.responseStart - e.requestStart), bytes };
  })()`, true);
  await clickAndWait("Step");
  await waitForSelector(cdp, "[data-execution-status='COMPLETED']");
  await sleep(1500);
  const done = await evaluate(T025E_TIMINGS);
  const oneBoundary = followed.deltaBytes.filter((b) => b > 0);
  const commits = liveTimings.commits;
  const serverP95 = percentile(server.wall, 95);
  allPass =
    report("T025e budgets, measured over HTTP on the running production build", null, [
      [
        "every delta response is at most 32 KB (32,768 B), and there are some",
        oneBoundary.length >= 20 && Math.max(...oneBoundary) <= 32768,
        `${oneBoundary.length} one-boundary deltas; max ${Math.max(...oneBoundary)} B; median ${percentile(oneBoundary, 50)} B (decoded); transfer max ${Math.max(...followed.deltaTransfer)} B`,
      ],
      [
        "the server answers a delta at the window's last live boundary in at most 50 ms at p95",
        server.recorded === 96 && serverP95 !== null && serverP95 <= 50,
        `boundary ${server.recorded}; 40 reads of ${server.bytes} B; wall p50 ${percentile(server.wall, 50)?.toFixed(1)} ms, p95 ${serverP95?.toFixed(1)} ms, max ${Math.max(...server.wall).toFixed(1)} ms; server wait (responseStart - requestStart) p95 ${percentile(server.ttfb, 95)?.toFixed(1)} ms`,
      ],
      [
        "a tick commits in at most 50 ms at p95 and 100 ms at worst",
        commits.length >= 20 && percentile(commits, 95) <= 50 && Math.max(...commits) <= 100,
        `${commits.length} commits; p50 ${percentile(commits, 50)?.toFixed(1)} ms, p95 ${percentile(commits, 95)?.toFixed(1)} ms, max ${Math.max(...commits).toFixed(1)} ms`,
      ],
      [
        "the terminal answer made exactly one full read, and none happened between the first step and it",
        done.steps.historyReads === fullBefore + 1,
        `${fullBefore} full reads before play; ${done.steps.historyReads} after the terminal step`,
      ],
    ]) && allPass;
}

// The completed profile-5 run T026 measures is the one T027 commits.
const t027 = { run: null };

// --- T026: the dispatch-capable evidence on the Lab screen ------------------
//
// A degraded-evidence Draft (`mini-grid` v3 / publication profile 5: a
// discharge-capability gap, the SOC publication held 07:00Z -> 07:10Z, the
// override record missing) run to its end, at two widths. The status staging
// claim follows the run's frozen mapping: profile 4 names the status
// "observed, not staged" (measured above); profile 5 stages it, so that line
// is absent and the staged statement stands in its place. Every claim about
// content is paired with a count so it cannot pass on an empty set.
const READ_T026 = `(() => {
  const all = (selector) => Array.from(document.querySelectorAll(selector));
  const text = (element) => (element ? (element.textContent || '').trim() : '');
  const attempts = all('[data-history-attempt]');
  const table = attempts[0] ? attempts[0].closest('table') : null;
  const go = document.querySelector('[data-timeline-entry="Publication delay"] [data-timeline-go]');
  return {
    status: document.querySelector('[data-execution-status]')?.getAttribute('data-execution-status') ?? null,
    families: /families recorded \\d+ of \\d+/.test(document.body.innerText),
    unstaged: all('[data-stage-unstaged-signal]').map((i) => i.getAttribute('data-stage-unstaged-signal')),
    stagedStatement: /stages it as a typed member in the run's source envelopes/.test(document.body.innerText),
    entryKinds: Array.from(new Set(all('[data-timeline-entry]').map((r) => r.getAttribute('data-timeline-entry')))),
    entries: all('[data-timeline-entry]').length,
    stageRows: all('[data-staged-envelope]').length,
    recordRows: all('[data-staged-quality="RECORD"]').length,
    reportedSquare: all('[data-chart-reported-mark="square"]').length,
    panels: all('[data-chart-panel]').length,
    attemptRows: attempts.length,
    attemptColumns: table ? table.querySelectorAll('thead th').length : 0,
    attemptPublication: attempts.map((r) => text(r)).filter((t) => /Sensor gap: |Publication delay: source|No publication delay recorded/.test(t)).length,
    delayedCells: attempts.map((r) => text(r)).filter((t) => /Publication delay: source/.test(t)).length,
    goDelay: go ? go.getAttribute('data-timeline-go') : null,
  };
})()`;

{
  await visit(cdp, "/simulator-lab/scenarios/kobo-mini-grid-degraded-evidence/run-setup", 1280, 800, "form", {
    script: submitV3Setup("2026-09-22T03:00:00Z", "2026-09-22T11:00:00Z"),
    waitFor: ".data-table__scroll",
  });
  const listed = await visit(cdp, "/simulator-lab/runs", 1280, 800, "table");
  const href = listed.runRows.find((row) => row.status === "READY")?.href ?? null;
  if (href === null || Object.values(v2Runs).includes(href) || href === t025d.played) {
    throw new Error("No new READY degraded-evidence Draft was found for the T026 pass.");
  }
  await visit(cdp, href, 1280, 800, "[data-execution-status]", {
    script: clickControl("Start this run"),
    waitFor: "[data-execution-status='RUNNING']",
  });
  await visit(cdp, href, 1280, 800, "[data-execution-status]", {
    script: clickControl("Run to the end"),
    waitFor: "[data-execution-status='COMPLETED']",
  });
  for (const [label, width, height] of [["1280x800", 1280, 800], ["640x700", 640, 700]]) {
    const page = await visit(cdp, href, width, height, "[data-cockpit]");
    await sleep(500);
    const read = await evaluate(READ_T026);
    allPass =
      report(`T026 degraded-evidence run (profile 5), completed, at ${label}`, page, [
        ["the run completed", read.status === "COMPLETED", `${read.status}`],
        [
          "profile 5 stages the status: no 'observed, not staged' line, the staged statement is shown",
          read.unstaged.join(",") === EXPECT_UNSTAGED[5].join(",") && read.stagedStatement,
          `unstaged ${read.unstaged.join(",") || "none"}; staged statement ${read.stagedStatement}`,
        ],
        [
          "the header states family coverage, and there are staged rows, record rows and entries",
          read.families && read.stageRows > 0 && read.recordRows > 0 && read.entries > 0,
          `coverage text ${read.families}; ${read.stageRows} envelopes, ${read.recordRows} record rows, ${read.entries} timeline entries (${read.entryKinds.join(", ")})`,
        ],
        [
          "the reported-run charts draw a second reported track as square marks, and there are some",
          read.reportedSquare > 0 && read.panels > 0,
          `${read.reportedSquare} square marks in ${read.panels} panels`,
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
      ]) && allPass;
  }
  t027.run = href;
  // The cursor goes through the held publication (07:00Z held, released 07:10Z:
  // boundaries 48 to 51): the inspector's attempts table has five columns, the
  // Applied timeline offers the delay, and the delayed reading is named.
  await visit(cdp, href, 1280, 800, "[data-cockpit]");
  await sleep(300);
  const seen = [];
  for (const boundary of [48, 49, 50, 51]) {
    await evaluate(`(() => {
      const range = document.getElementById('history-cursor-range');
      const setter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set;
      setter.call(range, '${boundary}');
      range.dispatchEvent(new Event('input', { bubbles: true }));
      return true;
    })()`);
    await sleep(600);
    seen.push({ boundary, ...(await evaluate(READ_T026)) });
  }
  const columns = Math.max(...seen.map((r) => r.attemptColumns));
  allPass =
    report("T026 inspector through the held publication, 1280", null, [
      [
        "the cursor reached the hold, with attempt rows and a Publication delay entry",
        seen.some((r) => r.attemptRows > 0) && seen.some((r) => r.entryKinds.includes("Publication delay")),
        seen.map((r) => `${r.boundary}: ${r.attemptRows} rows, kinds ${r.entryKinds.join("/") || "none"}`).join("; "),
      ],
      [
        "the attempts table has five columns, and a delayed reading is named",
        columns === 5 && seen.some((r) => r.delayedCells > 0),
        `${columns} columns; delayed rows ${seen.map((r) => `${r.boundary}:${r.delayedCells}`).join(", ")}; publication states ${seen.map((r) => `${r.boundary}:${r.attemptPublication}`).join(", ")}`,
      ],
    ]) && allPass;
}

// --- T027 phase 1: Commit, ingestion and Site > Evidence --------------------
//
// The completed profile-5 run measured above is committed through the Lab
// Commit panel; its Open in AssetOps link must land on Site > Evidence for the
// run's Site (KOBO_SITE), which is then measured populated at the dense-table
// widths, with the record inspector open. A Site with no accepted evidence
// (SITE) is measured empty. Every content claim carries a count so it cannot
// pass on an empty set.
const READ_T027_COMMIT = `(() => {
  const panel = document.querySelector('[data-run-commit]');
  const link = document.querySelector('[data-commit-open-in-assetops]');
  const release = document.querySelector('[data-release-status]');
  return {
    panel: panel !== null,
    labelled: document.querySelector('section[aria-labelledby="run-commit-heading"] [data-run-commit]') !== null,
    commitState: document.querySelector('[data-commit-state]')?.getAttribute('data-commit-state') ?? null,
    release: release ? release.getAttribute('data-release-status') : null,
    processed: release ? release.getAttribute('data-release-processed') : null,
    total: release ? release.getAttribute('data-release-total') : null,
    href: link ? link.getAttribute('href') : null,
  };
})()`;

const READ_T027_EVIDENCE = `(() => {
  const all = (selector) => Array.from(document.querySelectorAll(selector));
  const root = document.querySelector('.site-evidence');
  const section = (id) => document.querySelector('[aria-labelledby="' + id + '"]');
  const contained = (id) => {
    const s = section(id);
    const table = s ? s.querySelector('table') : null;
    const region = table ? table.closest('.data-table__scroll') : null;
    if (!table || !region) return { table: table !== null, region: false };
    const r = region.getBoundingClientRect();
    return {
      table: true,
      region: true,
      columns: table.querySelectorAll('thead th').length,
      regionInsideViewport: r.left >= -1 && r.right <= document.documentElement.clientWidth + 1,
      overflows: region.scrollWidth > region.clientWidth + 1,
    };
  };
  return {
    state: root ? root.getAttribute('data-evidence-state') : null,
    sources: all('[data-evidence-source]').length,
    batches: all('[data-evidence-batch]').length,
    coverage: all('[data-evidence-coverage]').map((r) => ({
      key: r.getAttribute('data-evidence-coverage'),
      status: r.getAttribute('data-coverage-status'),
    })),
    gaps: all('[data-coverage-gap]').length,
    headings: ['site-evidence-sources-heading', 'site-evidence-coverage-heading', 'site-evidence-basis-heading', 'site-evidence-rejections-heading']
      .filter((id) => document.getElementById(id) !== null),
    sourcesTable: contained('site-evidence-sources-heading'),
    coverageTable: contained('site-evidence-coverage-heading'),
    inspector: document.getElementById('site-evidence-inspector') !== null,
    records: all('[data-evidence-record]').map((r) => r.getAttribute('data-evidence-record')),
    detail: document.querySelector('[data-evidence-record-detail]') !== null,
    times: all('[data-record-time]').map((t) => ({ kind: t.getAttribute('data-record-time'), text: (t.textContent || '').trim() })),
    currentTab: (document.querySelector('.site-tabs__list [aria-current="page"]')?.textContent || '').trim(),
    // What sets the page wider than the viewport, if anything: the innermost
    // elements past the right edge that are not inside a table scroll region.
    wide: all('main *')
      .filter((e) => e.getBoundingClientRect().right > document.documentElement.clientWidth + 1 && !e.closest('.data-table__scroll'))
      .filter((e) => !Array.from(e.children).some((c) => c.getBoundingClientRect().right > document.documentElement.clientWidth + 1))
      .slice(0, 3)
      .map((e) => e.tagName.toLowerCase() + (e.id ? '#' + e.id : '') + (e.className && typeof e.className === 'string' ? '.' + e.className.split(' ')[0] : '')),
  };
})()`;

if (t027.run === null) {
  throw new Error("The T026 pass left no completed run for T027 to commit.");
}
{
  await visit(cdp, t027.run, 1280, 800, "[data-commit-state='NOT_COMMITTED']", {
    script: clickControl("Commit and release"),
    waitFor: "[data-commit-open-in-assetops]",
  });
  const lab = await visit(cdp, t027.run, 1280, 800, "[data-commit-open-in-assetops]");
  const commit = await evaluate(READ_T027_COMMIT);
  allPass =
    report("T027 Lab Commit panel after Commit and release, 1280x800", lab, [
      [
        "the Commit panel renders under its heading, sealed, with a release",
        commit.panel &&
          commit.labelled &&
          commit.commitState === "COMMITTED" &&
          commit.release !== null &&
          commit.release !== "NONE",
        `panel ${commit.panel}, labelled ${commit.labelled}, commit ${commit.commitState}, release ${commit.release} (${commit.processed} of ${commit.total})`,
      ],
      [
        "Open in AssetOps targets this Site's Evidence tab",
        commit.href === `/sites/${KOBO_SITE}/evidence` ||
          (commit.href ?? "").startsWith(`/sites/${KOBO_SITE}/evidence?`),
        `href ${commit.href}`,
      ],
    ]) && allPass;
  // Follow the link the way an operator would: a click, not a typed URL.
  await visit(cdp, t027.run, 1280, 800, "[data-commit-open-in-assetops]", {
    script: `(() => { document.querySelector('[data-commit-open-in-assetops]').click(); return true; })()`,
    waitFor: ".site-evidence[data-evidence-state]",
  });
  const landed = await evaluate(
    `({ path: window.location.pathname, state: document.querySelector('.site-evidence')?.getAttribute('data-evidence-state') ?? null })`,
  );
  allPass =
    report("T027 Open in AssetOps lands on Site > Evidence", null, [
      [
        "the link lands on Site > Evidence for the run's Site, populated",
        landed.path === `/sites/${KOBO_SITE}/evidence` && landed.state === "populated",
        `${landed.path}, ${landed.state}`,
      ],
    ]) && allPass;

  const base = `/sites/${KOBO_SITE}/evidence`;
  let pick = null;
  for (const [label, width, height] of [
    ["1280x800", 1280, 800],
    ["1000x700", 1000, 700],
    ["640x700", 640, 700],
  ]) {
    // T028 presentation cp1 moved source health and coverage to the Evidence
    // tab's local Analysis view (`?view=analysis`); the T027 claims hold there.
    const page = await visit(cdp, `${base}?view=analysis`, width, height, ".site-evidence[data-evidence-state]");
    await sleep(300);
    const read = await evaluate(READ_T027_EVIDENCE);
    pick = pick ?? read.coverage.find((r) => r.status === "REPORTED")?.key ?? null;
    allPass =
      report(`T027 Site > Evidence populated, ${KOBO_SITE}, at ${label}`, page, [
        ["the Evidence body is populated", read.state === "populated", `${read.state}`],
        [
          "exactly Overview|Foundation|Performance|Findings|Evidence, Evidence current, then its local views Overview|Analysis",
          page.tabLabels.slice(0, 5).join("|") === "Overview|Foundation|Performance|Findings|Evidence" &&
            page.tabLabels.slice(5).join("|") === "Overview|Analysis" && read.currentTab === "Evidence",
          `${page.tabLabels.join(" | ")}; current ${read.currentTab}`,
        ],
        [
          "source health and coverage have rows, and all four sections render",
          read.sources > 0 && read.batches > 0 && read.coverage.length > 0 && read.headings.length === 4,
          `${read.sources} sources, ${read.batches} batches, ${read.coverage.length} coverage rows (${read.coverage.filter((r) => r.status === "REPORTED").length} reported, ${read.coverage.filter((r) => r.status === "NOT_REPORTED").length} not reported), ${read.gaps} gaps, ${read.headings.length} sections`,
        ],
        [
          "both dense tables sit in scroll regions that stay inside the viewport",
          [read.sourcesTable, read.coverageTable].every((t) => t.table && t.region && t.regionInsideViewport),
          `sources ${read.sourcesTable.columns} cols, overflows ${read.sourcesTable.overflows}; coverage ${read.coverageTable.columns} cols, overflows ${read.coverageTable.overflows}`,
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
                "at 640 at least one evidence table overflows, so containment is measured on a non-empty set",
                read.sourcesTable.overflows || read.coverageTable.overflows,
                `sources overflows ${read.sourcesTable.overflows}, coverage overflows ${read.coverageTable.overflows}`,
              ],
            ]
          : []),
      ]) && allPass;
  }

  if (pick === null) {
    allPass = report("T027 record inspector", null, [["a reported signal exists to inspect", false, "none"]]) && false;
  } else {
    const q = `signal=${encodeURIComponent(pick)}`;
    await visit(cdp, `${base}?${q}`, 1280, 800, "#site-evidence-inspector [data-evidence-record]");
    const list = await evaluate(READ_T027_EVIDENCE);
    const record = list.records[0];
    for (const [label, width, height] of [
      ["1280x800", 1280, 800],
      ["640x700", 640, 700],
    ]) {
      const page = await visit(
        cdp,
        `${base}?${q}&record=${encodeURIComponent(record)}`,
        width,
        height,
        "[data-evidence-record-detail]",
      );
      await sleep(300);
      const read = await evaluate(READ_T027_EVIDENCE);
      const kinds = read.times.map((t) => t.kind).sort().join(",");
      allPass =
        report(`T027 record inspector, ${pick} record ${record}, at ${label}`, page, [
          ["the inspector lists records", read.inspector && read.records.length > 0, `${read.records.length} records`],
          [
            "the record detail shows source, published and received times, each non-empty",
            read.detail && kinds === "published,received,source" && read.times.every((t) => t.text.length > 0),
            read.times.map((t) => `${t.kind}: ${t.text}`).join("; "),
          ],
          ["Evidence stays the current tab", read.currentTab === "Evidence", read.currentTab],
          [
            "the page does not scroll horizontally",
            !page.pageScrollsHorizontally,
            `scrollWidth ${page.pageScrollWidth} vs clientWidth ${page.pageClientWidth}; past the edge: ${read.wide.join(", ") || "nothing"}`,
          ],
        ]) && allPass;
    }
  }

  for (const [label, width, height] of [
    ["1280x800", 1280, 800],
    ["640x700", 640, 700],
  ]) {
    const page = await visit(cdp, `/sites/${SITE}/evidence`, width, height, ".site-evidence[data-evidence-state]");
    const read = await evaluate(READ_T027_EVIDENCE);
    allPass =
      report(`T027 Site > Evidence empty, ${SITE}, at ${label}`, page, [
        [
          // The needed-signal coverage still lists what the Site needs, every
          // row NOT_REPORTED: nothing was accepted, and the gap is the point.
          "the empty state renders: no source rows, and every needed signal reads not reported",
          read.state === "empty" &&
            read.sources === 0 &&
            read.coverage.every((r) => r.status === "NOT_REPORTED"),
          `${read.state}; ${read.sources} sources, ${read.coverage.length} coverage rows, ${read.coverage.filter((r) => r.status === "NOT_REPORTED").length} not reported`,
        ],
        [
          "exactly Overview|Foundation|Performance|Findings|Evidence, Evidence current, then its local views Overview|Analysis",
          page.tabLabels.slice(0, 5).join("|") === "Overview|Foundation|Performance|Findings|Evidence" &&
            page.tabLabels.slice(5).join("|") === "Overview|Analysis" && read.currentTab === "Evidence",
          `${page.tabLabels.join(" | ")}; current ${read.currentTab}`,
        ],
        [
          "the page does not scroll horizontally",
          !page.pageScrollsHorizontally,
          `scrollWidth ${page.pageScrollWidth} vs clientWidth ${page.pageClientWidth}`,
        ],
      ]) && allPass;
  }
}

// --- T027 phase 2: the mini-grid Site Overview -----------------------------
//
// The committed run's Site (KOBO_SITE) populated at 1280, 1000 and 640, and
// SITE (no accepted evidence) empty at 1280 and 640. jsdom cannot see any of
// this: card grid wrap, the timeline's scaled svg and its region, and whether
// the page ever scrolls sideways. An Overview evidence link is clicked once and
// must land on the Site > Evidence inspector with that record open.

const READ_T027_OVERVIEW = `(() => {
  const root = document.querySelector(".site-overview");
  const cards = Array.from(document.querySelectorAll("[data-overview-card]")).map((el) => ({
    id: el.getAttribute("data-overview-card"),
    gaps: Number(el.getAttribute("data-overview-gaps")),
    values: Number(el.getAttribute("data-overview-values")),
    text: el.closest("section")?.innerText ?? "",
  }));
  const charts = Array.from(document.querySelectorAll(".overview-timeline__chart")).map((svg) => {
    const box = svg.getBoundingClientRect();
    const scroller = svg.closest(".overview-timeline__scroll");
    const region = scroller.getBoundingClientRect();
    return { width: Math.round(box.width), right: Math.round(box.right), regionRight: Math.round(region.right),
             overflows: scroller.scrollWidth > scroller.clientWidth,
             overflowX: getComputedStyle(scroller).overflowX,
             marks: svg.querySelectorAll("g line, g circle").length };
  });
  const links = Array.from(document.querySelectorAll("[data-overview-evidence]")).map((a) => a.getAttribute("href"));
  const row = document.querySelector('.site-tabs__list [aria-current="page"]');
  return {
    state: root?.getAttribute("data-overview-state") ?? null,
    cards, charts, links,
    currentTab: (row?.textContent || "").trim(),
    text: root?.innerText ?? "",
    viewport: document.documentElement.clientWidth,
  };
})()`;

{
  let firstLink = null;
  for (const [label, width, height] of [
    ["1280x800", 1280, 800],
    ["1000x700", 1000, 700],
    ["640x700", 640, 700],
  ]) {
    const page = await visit(cdp, `/sites/${KOBO_SITE}`, width, height, ".site-overview[data-overview-state]");
    await sleep(300);
    const read = await evaluate(READ_T027_OVERVIEW);
    firstLink = firstLink ?? read.links[0] ?? null;
    const order = read.cards.map((c) => c.id).join("|");
    allPass =
      report(`T027 Site Overview populated, ${KOBO_SITE}, at ${label}`, page, [
        ["the Overview body is populated", read.state === "populated", `${read.state}`],
        [
          "cards Service|Dispatch|Battery|Fuel|Renewable, in the profile's order",
          order === "Service|Dispatch|Battery|Fuel|Renewable",
          order,
        ],
        [
          // T028: the Dispatch card carries the backend's dispatch assessment
          // once the committed run is assessed; the other four still read
          // No assessment yet.
          "Service, Battery, Fuel, Renewable read No assessment yet; Dispatch carries the backend assessment; nothing reads Unknown",
          read.cards.filter((c) => c.id !== "Dispatch").length === 4 &&
            read.cards.filter((c) => c.id !== "Dispatch").every((c) => c.text.includes("No assessment yet")) &&
            read.cards.some((c) => c.id === "Dispatch" && c.text.includes("Dispatch assessment:")) &&
            !/unknown/i.test(read.text),
          `${read.cards.filter((c) => c.text.includes("No assessment yet")).map((c) => c.id).join(",")} read No assessment yet; Dispatch slot ${read.cards.some((c) => c.id === "Dispatch" && c.text.includes("Dispatch assessment:")) ? "assessed" : "not assessed"}`,
        ],
        [
          "measured values exist (non-empty set), and each uncovered card names its gap",
          read.cards.some((c) => c.values > 0) &&
            read.cards.filter((c) => c.gaps > 0).every((c) => c.text.includes("Coverage gap:")),
          read.cards.map((c) => `${c.id}: ${c.values} values, ${c.gaps} gaps`).join("; "),
        ],
        [
          "evidence links address the record inspector",
          read.links.length > 0 && read.links.every((h) => /\/evidence\?signal=[^&]+\/[^&]+&record=/.test(h)),
          `${read.links.length} links; first ${read.links[0] ?? "none"}`,
        ],
        [
          // The chart scales to its column down to a 20rem floor; below that
          // its own region scrolls it (overflow-x auto), and the region never
          // leaves the viewport.
          "the timeline draws marks; each chart fits its region or its region scrolls it, inside the viewport",
          read.charts.length > 0 &&
            read.charts.every(
              (c) =>
                c.marks > 0 &&
                c.regionRight <= read.viewport &&
                (c.right <= c.regionRight + 1 || (c.overflows && c.overflowX === "auto")),
            ),
          read.charts.map((c) => `${c.width}px, ${c.marks} marks, right ${c.right}/${c.regionRight}/${read.viewport}, region ${c.overflows ? `overflows (${c.overflowX})` : "fits"}`).join("; "),
        ],
        [
          "exactly Overview|Foundation|Performance|Findings|Evidence, Overview current",
          page.tabLabels.join("|") === "Overview|Foundation|Performance|Findings|Evidence" && read.currentTab === "Overview",
          `${page.tabLabels.join(" | ")}; current ${read.currentTab}`,
        ],
        [
          "the page does not scroll horizontally",
          !page.pageScrollsHorizontally,
          `scrollWidth ${page.pageScrollWidth} vs clientWidth ${page.pageClientWidth}`,
        ],
      ]) && allPass;
  }

  if (firstLink !== null) {
    const record = decodeURIComponent(firstLink.split("record=")[1] ?? "");
    const page = await visit(cdp, firstLink, 1280, 800, `[data-evidence-record-detail]`);
    const opened = await evaluate(`(() => ({
      detail: document.querySelector("[data-evidence-record-detail]")?.getAttribute("data-evidence-record-detail") ?? null,
      path: location.pathname,
      current: (document.querySelector('.site-tabs__list [aria-current="page"]')?.textContent || "").trim(),
    }))()`);
    allPass =
      report("T027 Overview evidence link opens the record inspector", page, [
        [
          "the linked record is open in Site > Evidence, Evidence current, same Site root",
          opened.detail === record && opened.path === `/sites/${KOBO_SITE}/evidence` && opened.current === "Evidence",
          `${opened.path}; record ${opened.detail}; current ${opened.current}`,
        ],
      ]) && allPass;
  } else {
    allPass = report("T027 Overview evidence link", null, [["an evidence link exists", false, "none"]]) && false;
  }

  for (const [label, width, height] of [
    ["1280x800", 1280, 800],
    ["640x700", 640, 700],
  ]) {
    const page = await visit(cdp, `/sites/${SITE}`, width, height, ".site-overview[data-overview-state]");
    const read = await evaluate(READ_T027_OVERVIEW);
    allPass =
      report(`T027 Site Overview empty, ${SITE}, at ${label}`, page, [
        [
          "empty: five cards, every one No assessment yet with a named gap and no value, no chart",
          read.state === "empty" &&
            read.cards.length === 5 &&
            read.cards.every((c) => c.gaps > 0 && c.values === 0 && c.text.includes("No assessment yet")) &&
            read.charts.length === 0 &&
            !/unknown/i.test(read.text),
          `${read.state}; ${read.cards.map((c) => `${c.id} ${c.gaps} gaps ${c.values} values`).join("; ")}; ${read.charts.length} charts`,
        ],
        [
          "the page does not scroll horizontally",
          !page.pageScrollsHorizontally,
          `scrollWidth ${page.pageScrollWidth} vs clientWidth ${page.pageClientWidth}`,
        ],
      ]) && allPass;
  }
}

// --- T028: Dispatch, Finding detail, Overview card, Findings, Site Evidence ---
//
// Presentation checkpoint 2b (D-2026-10-04-plain-language-analysis-views,
// spec section 5): the plain default views, the Analysis views and the four
// graphics, measured on the committed Site (KOBO_SITE). The checkpoint 1 and
// earlier claims about `.segment-strip`, the six-part hierarchy and closed
// disclosures are gone with those elements. Every content claim carries a
// count, so an absent graphic or table fails rather than passing on an empty
// set; narrow claims run at 640 and 480 px. The live vocabulary scan
// (`t028Journey`, below) reads the backend's own text on every T028 surface.

const READ_T028_RAIL = `(() => {
  const nav = document.querySelector('nav[aria-label="Operator routes"]');
  const side = document.querySelector(".app-frame__side");
  const groups = nav ? Array.from(nav.querySelectorAll(".nav-rail__group")).map((g) => {
    const header = g.querySelector(".nav-rail__group-label");
    const hb = header ? header.getBoundingClientRect() : null;
    const items = Array.from(g.querySelectorAll("li")).map((li) => {
      const b = li.getBoundingClientRect();
      return { label: (li.textContent || "").trim(), top: Math.round(b.top), right: Math.round(b.right), height: Math.round(b.height) };
    });
    return {
      header: header ? (header.textContent || "").trim() : null,
      headerHeight: hb ? Math.round(hb.height) : 0,
      headerBottom: hb ? Math.round(hb.bottom) : null,
      headerRight: hb ? Math.round(hb.right) : null,
      items,
    };
  }) : [];
  return { groups, sideRight: side ? Math.round(side.getBoundingClientRect().right) : null };
})()`;

// Every assessment graphic and graphic table on the page, with the region
// that contains it. A region is contained when it scrolls on its own
// (overflow-x auto or scroll) and its right edge is inside the viewport.
const READ_T028_GRAPHICS = `(() => {
  const vw = document.documentElement.clientWidth;
  const box = (el) => { const b = el.getBoundingClientRect(); return { left: Math.round(b.left), right: Math.round(b.right), width: Math.round(b.width), height: Math.round(b.height) }; };
  const region = (el) => {
    const r = el.closest(".data-table__scroll") || el.closest(".assessment-graphic");
    if (!r) return { overflow: null, right: null, contained: false };
    const o = getComputedStyle(r).overflowX;
    const right = Math.round(r.getBoundingClientRect().right);
    return { overflow: o, right, contained: (o === "auto" || o === "scroll") && right <= vw };
  };
  const timelines = Array.from(document.querySelectorAll('figure[data-graphic="assessed-period-timeline"]')).map((f) => {
    const bar = f.querySelector("svg.period-timeline__bar");
    const bb = bar ? bar.getBoundingClientRect() : null;
    const fb = f.getBoundingClientRect();
    const bands = bar ? Array.from(bar.querySelectorAll("rect[data-band]")).map((r) => ({
      kind: r.getAttribute("data-band-kind"),
      expected: Number(r.getAttribute("data-width")) * bb.width,
      actual: r.getBoundingClientRect().width,
      expectedLeft: bb.left + Number(r.getAttribute("data-x")) * bb.width,
      left: r.getBoundingClientRect().left,
    })) : [];
    const legend = Array.from(f.querySelectorAll("[data-legend]")).map((li) => box(li));
    return {
      assessment: f.getAttribute("data-graphic-assessment"),
      compact: f.getAttribute("data-compact") === "true",
      figure: box(f),
      bar: bb ? { width: Math.round(bb.width), right: Math.round(bb.right) } : null,
      bands,
      geometryOk: bands.length > 0 && bands.every((b) => Math.abs(b.actual - b.expected) <= 1.5 && Math.abs(b.left - b.expectedLeft) <= 1.5),
      legend,
      legendInside: legend.every((l) => l.right <= Math.round(fb.right) + 1 && l.left >= Math.round(fb.left) - 1),
      captionHeight: f.querySelector("figcaption") ? Math.round(f.querySelector("figcaption").getBoundingClientRect().height) : 0,
      region: region(f),
    };
  });
  const tables = (sel) => Array.from(document.querySelectorAll(sel)).map((t) => ({
    rows: t.querySelectorAll("tbody tr").length,
    region: region(t.querySelector("table") || t),
  }));
  return {
    viewport: vw,
    timelines,
    partsTables: tables("[data-timeline-table]"),
    valueTables: tables("[data-value-bars]"),
    coverageTables: tables("[data-coverage-table]"),
    fuel: Array.from(document.querySelectorAll('[data-graphic="fuel-range"]')).map((g) => ({
      unavailable: g.getAttribute("data-fuel-unavailable"),
      svgWidth: g.querySelector("svg") ? Math.round(g.querySelector("svg").getBoundingClientRect().width) : 0,
      right: Math.round(g.getBoundingClientRect().right),
    })),
  };
})()`;

const READ_T028_DISPATCH = `(() => {
  const sub = document.querySelector('nav[aria-label="Performance sections"]');
  const views = document.querySelector('nav[aria-label="Dispatch views"]');
  const table = document.querySelector('[aria-labelledby="site-dispatch-heading"] table');
  const region = table ? table.closest(".data-table__scroll") : null;
  const rows = Array.from(document.querySelectorAll("[data-dispatch-interval]")).map((tr) => {
    const bar = tr.querySelector("svg.period-timeline__bar");
    return {
      id: tr.getAttribute("data-dispatch-interval"),
      level: tr.getAttribute("data-claim-level"),
      finding: tr.querySelector("[data-dispatch-finding-link]")?.getAttribute("href") ?? null,
      bar: bar ? Math.round(bar.getBoundingClientRect().width) : 0,
      drawn: tr.querySelector('figure[data-graphic-assessment="' + tr.getAttribute("data-dispatch-interval") + '"]') !== null,
    };
  });
  return {
    subtabs: sub ? Array.from(sub.querySelectorAll("li")).map((li) => (li.textContent || "").trim()) : [],
    views: views ? Array.from(views.querySelectorAll("a")).map((a) => (a.textContent || "").trim()) : [],
    rows,
    contained: region ? getComputedStyle(region).overflowX : null,
    regionRight: region ? Math.round(region.getBoundingClientRect().right) : null,
    viewport: document.documentElement.clientWidth,
  };
})()`;

const READ_T028_FINDING = `(() => {
  const tabs = document.querySelector('nav[aria-label="Finding sections"]');
  const drawer = document.querySelector("[data-claim-drawer]");
  const db = drawer ? drawer.getBoundingClientRect() : null;
  return {
    finding: document.querySelector("[data-finding]")?.getAttribute("data-finding") ?? null,
    tabs: tabs ? Array.from(tabs.querySelectorAll("li")).map((li) => (li.textContent || "").trim()) : [],
    current: tabs ? (tabs.querySelector('[aria-current="page"]')?.textContent || "").trim() : null,
    claims: document.querySelectorAll("[data-claim-segment]").length,
    links: document.querySelectorAll("[data-evidence-link]").length,
    drawer: drawer ? drawer.getAttribute("data-claim-drawer") : null,
    drawerRecord: drawer ? (drawer.querySelector("[data-evidence-record-detail]")?.getAttribute("data-evidence-record-detail") ?? null) : null,
    drawerBox: db ? { left: Math.round(db.left), right: Math.round(db.right), width: Math.round(db.width) } : null,
    path: location.pathname,
    railCurrent: (document.querySelector('nav[aria-label="Operator routes"] [aria-current="page"]')?.textContent || "").trim(),
    viewport: document.documentElement.clientWidth,
  };
})()`;

const CLICK_FIRST_EVIDENCE_LINK = `(() => {
  const b = document.querySelector("[data-evidence-link]");
  if (!b) return null;
  b.click();
  return b.getAttribute("data-evidence-link");
})()`;

const READ_T028_INDEX = `(() => {
  const table = document.querySelector('[data-findings-index] table');
  const region = table ? table.closest('.data-table__scroll') : null;
  return {
    rows: Array.from(document.querySelectorAll('[data-finding-row]')).map((r) => r.getAttribute('data-finding-row')),
    analysisLinks: Array.from(document.querySelectorAll('[data-finding-row] a')).filter((a) => /\\/analysis$/.test(a.getAttribute('href') || '')).length,
    empty: document.querySelector('[data-findings-empty]') !== null,
    overflowX: region ? getComputedStyle(region).overflowX : null,
    current: (document.querySelector('nav[aria-label="Operator routes"] [aria-current="page"]')?.textContent || '').trim(),
  };
})()`;

const READ_T028_CARD = `(() => {
  const host = document.querySelector("[data-overview-card-timeline]");
  const card = host ? host.closest("article, section, li, div.overview-card") : null;
  const bar = host ? host.querySelector("svg.period-timeline__bar") : null;
  const link = Array.from(document.querySelectorAll("a")).find((a) => (a.textContent || "").trim() === "View analysis") || null;
  return {
    lead: host ? host.getAttribute("data-overview-card-timeline") : null,
    figure: host ? host.querySelector("figure")?.getAttribute("data-graphic-assessment") ?? null : null,
    bar: bar ? Math.round(bar.getBoundingClientRect().width) : 0,
    barRight: bar ? Math.round(bar.getBoundingClientRect().right) : null,
    cardRight: card ? Math.round(card.getBoundingClientRect().right) : null,
    analysisHref: link ? link.getAttribute("href") : null,
  };
})()`;

const noScroll480 = (page, width) => (width < 640 ? [] : [noScroll(page)]);

const noScroll = (page) => [
  "the page does not scroll horizontally",
  !page.pageScrollsHorizontally,
  `scrollWidth ${page.pageScrollWidth} vs clientWidth ${page.pageClientWidth}`,
];

const tablesClaim = (name, list) => [
  `${name}: at least one, each with rows, each in its own contained scroll region`,
  list.length > 0 && list.every((t) => t.rows > 0 && t.region.contained),
  list.map((t) => `${t.rows} rows, overflow-x ${t.region.overflow}, right ${t.region.right}`).join("; ") || "none",
];

const timelineClaims = (g, { compact }) => {
  const set = g.timelines.filter((t) => t.compact === compact);
  return [
    [
      `${compact ? "compact" : "full"} period timeline drawn, its parts at the widths and offsets their times give (within 1.5 px)`,
      set.length > 0 && set.every((t) => t.bar !== null && t.bar.width > 0 && t.geometryOk),
      set.map((t) => `${t.assessment}: bar ${t.bar?.width}px, ${t.bands.length} parts (${t.bands.map((b) => `${b.kind} ${b.actual.toFixed(1)}/${b.expected.toFixed(1)}`).join(", ")})`).join("; ") || "none",
    ],
    [
      `${compact ? "compact" : "full"} timeline caption and key stay inside the graphic, the key wrapping rather than overflowing`,
      set.length > 0 && set.every((t) => t.captionHeight > 0 && t.legend.length > 0 && t.legendInside && t.region.contained),
      set.map((t) => `caption ${t.captionHeight}px; ${t.legend.length} key items inside ${t.legendInside}; region ${t.region.overflow} right ${t.region.right} vs ${g.viewport}`).join("; ") || "none",
    ],
  ];
};

let t028FindingHref = null;
let t028AnyAssessment = null;
{
  for (const [label, width, height] of [
    ["1280x800", 1280, 800],
    ["1000x700", 1000, 700],
    ["640x700", 640, 700],
    ["480x800", 480, 800],
  ]) {
    const page = await visit(cdp, `/sites/${KOBO_SITE}/performance`, width, height, "[data-dispatch-interval], [data-dispatch-empty]");
    await sleep(300);
    const rail = await evaluate(READ_T028_RAIL);
    const read = await evaluate(READ_T028_DISPATCH);
    t028FindingHref = t028FindingHref ?? read.rows.find((r) => r.finding !== null)?.finding ?? null;
    t028AnyAssessment = t028AnyAssessment ?? read.rows[0]?.id ?? null;
    const groups = rail.groups.map((g) => `${g.header}: ${g.items.map((i) => i.label).join(",")}`).join("; ");
    const claims = [
      [
        "Site tabs Overview|Foundation|Performance|Findings|Evidence; Dispatch the only Performance subtab; Dispatch views Overview|Analysis",
        page.tabLabels.slice(0, 5).join("|") === "Overview|Foundation|Performance|Findings|Evidence" &&
          read.subtabs.join("|") === "Dispatch assessment" && read.views.join("|") === "Overview|Analysis",
        `${page.tabLabels.join(" | ")}; subtabs ${read.subtabs.join(",")}; views ${read.views.join("|")}`,
      ],
      [
        "every assessed period row draws its own compact timeline, at least 120 px wide, in the contained table",
        read.rows.length > 0 && read.rows.every((r) => r.drawn && r.bar >= 119) &&
          (read.contained === "auto" || read.contained === "scroll") && read.regionRight <= read.viewport,
        `${read.rows.length} rows (${read.rows.map((r) => r.level).join(",")}); bars ${read.rows.map((r) => r.bar).join(",")}; overflow-x ${read.contained}; region right ${read.regionRight} vs ${read.viewport}`,
      ],
      ...noScroll480(page, width),
    ];
    if (width >= 640) {
      claims.unshift(
        [
          "rail is exactly OPERATE: Sites; INTELLIGENCE: Findings, each one-item group headed",
          groups === "OPERATE: Sites; INTELLIGENCE: Findings" &&
            rail.groups.every((g) => g.headerHeight > 0 && g.items.length === 1 && g.items[0].height > 0 && g.headerBottom <= g.items[0].top),
          `${groups}; header heights ${rail.groups.map((g) => g.headerHeight).join(",")}`,
        ],
        [
          "rail headers and items stay inside the rail column",
          rail.groups.every((g) => g.headerRight <= rail.sideRight && g.items.every((i) => i.right <= rail.sideRight)),
          `side right ${rail.sideRight}`,
        ],
      );
    }
    allPass = report(`T028 rail and Performance > Dispatch Overview, ${KOBO_SITE}, at ${label}`, page, claims) && allPass;
  }

  const target = t028FindingHref ?? (t028AnyAssessment === null ? null : `/findings/${KOBO_SITE}/${t028AnyAssessment}`);
  if (target === null) {
    allPass = report("T028 Finding detail", null, [["an assessed period exists on " + KOBO_SITE, false, "none"]]) && false;
  } else {
    for (const [label, width, height] of [
      ["1280x800", 1280, 800],
      ["640x700", 640, 700],
      ["480x800", 480, 800],
    ]) {
      const page = await visit(cdp, target, width, height, 'figure[data-graphic="assessed-period-timeline"]');
      const over = await evaluate(READ_T028_FINDING);
      const g = await evaluate(READ_T028_GRAPHICS);
      allPass =
        report(`T028 Finding Overview, ${target}${t028FindingHref === null ? " (no Finding raised: Needed period)" : ""}, at ${label}`, page, [
          [
            "tabs exactly Overview|Analysis|Evidence|Alternatives, Overview current; root is Findings",
            over.tabs.join("|") === "Overview|Analysis|Evidence|Alternatives" && over.current === "Overview" && over.railCurrent === "Findings",
            `${over.tabs.join("|")}; current ${over.current}; rail ${over.railCurrent}`,
          ],
          ...timelineClaims(g, { compact: false }),
          [
            "the fuel graphic draws a range or states why it cannot, inside the viewport",
            g.fuel.length > 0 && g.fuel.every((f) => (f.unavailable !== null || f.svgWidth > 0) && f.right <= g.viewport),
            g.fuel.map((f) => f.unavailable === null ? `range ${f.svgWidth}px` : `unavailable: ${f.unavailable}`).join("; ") || "none",
          ],
          ...noScroll480(page, width),
        ]) && allPass;

      const analysis = await visit(cdp, `${target}/analysis`, width, height, "[data-timeline-table]");
      const ga = await evaluate(READ_T028_GRAPHICS);
      allPass =
        report(`T028 Finding Analysis, at ${label}`, analysis, [
          ...timelineClaims(ga, { compact: false }),
          tablesClaim("assessed parts table", ga.partsTables),
          tablesClaim("reported value tables of the selected part", ga.valueTables),
          tablesClaim("coverage by input table", ga.coverageTables),
          ...noScroll480(analysis, width),
        ]) && allPass;

      if (width === 480) continue;
      const evidencePath = `${target}/evidence`;
      await visit(cdp, evidencePath, width, height, "[data-claim-segment]");
      const clicked = await evaluate(CLICK_FIRST_EVIDENCE_LINK);
      await sleep(800);
      const opened = await evaluate(READ_T028_FINDING);
      const after = await evaluate(MEASURE);
      allPass =
        report(`T028 Finding Evidence tab and record drawer, at ${label}`, null, [
          ["claims listed with evidence links", opened.claims > 0 && opened.links > 0, `${opened.claims} claims, ${opened.links} links`],
          [
            "the drawer opens the clicked record through the inspector, path and root unchanged",
            clicked !== null && opened.drawer === clicked && opened.drawerRecord === clicked &&
              opened.path === evidencePath && opened.railCurrent === "Findings",
            `clicked ${clicked}; drawer ${opened.drawer}; record ${opened.drawerRecord}; path ${opened.path}; rail ${opened.railCurrent}`,
          ],
          [
            "the drawer sits inside the viewport",
            opened.drawerBox !== null && opened.drawerBox.left >= 0 && opened.drawerBox.right <= opened.viewport && opened.drawerBox.width > 200,
            `${JSON.stringify(opened.drawerBox)} vs ${opened.viewport}`,
          ],
          noScroll(after),
        ]) && allPass;
    }

    for (const id of [t028AnyAssessment]) {
      for (const [label, width, height] of [
        ["1280x800", 1280, 800],
        ["480x800", 480, 800],
      ]) {
        const page = await visit(cdp, `/sites/${KOBO_SITE}/performance/dispatch?interval=${id}&view=analysis`, width, height, "[data-timeline-table]");
        const g = await evaluate(READ_T028_GRAPHICS);
        allPass =
          report(`T028 Dispatch Analysis of ${id}, at ${label}`, page, [
            ...timelineClaims(g, { compact: false }),
            tablesClaim("assessed parts table", g.partsTables),
            tablesClaim("coverage by input table", g.coverageTables),
            ...noScroll480(page, width),
          ]) && allPass;
      }
      for (const [label, width, height] of [
        ["1280x800", 1280, 800],
        ["640x700", 640, 700],
      ]) {
        const page = await visit(cdp, `/sites/${KOBO_SITE}/evidence?view=analysis&assessment=${id}`, width, height, "[data-evidence-assessment-coverage], [data-evidence-state]");
        await waitUntil(`!!document.querySelector("[data-evidence-assessment-coverage] [data-coverage-table] tbody tr")`, 15000);
        const g = await evaluate(READ_T028_GRAPHICS);
        allPass =
          report(`T028 Site Evidence Analysis, one assessed period's coverage (${id}), at ${label}`, page, [
            tablesClaim("coverage by input table", g.coverageTables),
            noScroll(page),
          ]) && allPass;
      }
    }
  }

  for (const [label, width, height] of [
    ["1280x800", 1280, 800],
    ["640x700", 640, 700],
    ["480x800", 480, 800],
  ]) {
    const page = await visit(cdp, `/sites/${KOBO_SITE}`, width, height, "[data-overview-card-timeline], [data-overview-card]");
    await sleep(300);
    const card = await evaluate(READ_T028_CARD);
    const g = await evaluate(READ_T028_GRAPHICS);
    allPass =
      report(`T028 Site Overview Dispatch card, ${KOBO_SITE}, at ${label}`, page, [
        [
          "the card draws the compact timeline of the lead period it links to, at least 120 px, inside the card",
          card.lead !== null && card.figure === card.lead && card.bar >= 119 && card.cardRight !== null && card.barRight <= card.cardRight &&
            card.analysisHref !== null && card.analysisHref.includes(card.lead),
          `lead ${card.lead}; drawn ${card.figure}; bar ${card.bar}px right ${card.barRight} vs card ${card.cardRight}; View analysis ${card.analysisHref}`,
        ],
        ...timelineClaims(g, { compact: true }),
        ...noScroll480(page, width),
      ]) && allPass;
  }

  for (const [label, width, height] of [
    ["1280x800", 1280, 800],
    ["640x700", 640, 700],
  ]) {
    const page = await visit(cdp, "/findings", width, height, "[data-findings-index]");
    const read = await evaluate(READ_T028_INDEX);
    const findingId = t028FindingHref === null ? null : t028FindingHref.split("/").pop();
    allPass =
      report(`T028 Findings rail root, at ${label}`, page, [
        [
          "Findings is the current root; the index lists the Dispatch Finding, each row with a View analysis link",
          read.current === "Findings" &&
            (findingId === null ? read.rows.length > 0 || read.empty : read.rows.includes(findingId) && read.analysisLinks === read.rows.length),
          `${read.rows.length} rows, ${read.analysisLinks} analysis links; Dispatch Finding ${findingId ?? "none on " + KOBO_SITE}; current ${read.current}`,
        ],
        [
          "the index table is contained (or the empty state is stated)",
          read.empty || read.overflowX === "auto" || read.overflowX === "scroll",
          `overflow-x ${read.overflowX}; empty ${read.empty}`,
        ],
        noScroll(page),
      ]) && allPass;
  }

  allPass = (await t028Journey({ labOff: false })) && allPass;
}

// --- T028 phase 3: Site > Evidence capability table (AC20) -------------------
//
// On the committed Site: exactly one capability row (dispatch) above the T027
// Source health section, with a readiness the backend scored (Full, Limited or
// None), a claim ceiling and its missing-evidence cell; the table contained
// and the page not scrolling at any width. The row count is the non-empty
// proof: an absent table fails the claim rather than passing on an empty set.

const READ_T028_CAPABILITY = `(() => {
  const heading = document.getElementById("site-evidence-capability-heading");
  const sources = document.getElementById("site-evidence-sources-heading");
  const table = heading ? heading.closest("section")?.querySelector("table") ?? null : null;
  const region = table ? table.closest(".data-table__scroll") : null;
  const rows = Array.from(document.querySelectorAll("[data-capability]")).map((tr) => {
    const b = tr.getBoundingClientRect();
    return {
      id: tr.getAttribute("data-capability"),
      readiness: tr.getAttribute("data-capability-readiness"),
      ceiling: tr.querySelector("[data-capability-ceiling]")?.getAttribute("data-capability-ceiling") ?? null,
      missing: tr.querySelectorAll("[data-capability-missing]").length,
      height: Math.round(b.height),
    };
  });
  return {
    rows,
    above: heading && sources ? Math.round(heading.getBoundingClientRect().top) < Math.round(sources.getBoundingClientRect().top) : false,
    overflowX: region ? getComputedStyle(region).overflowX : null,
    regionRight: region ? Math.round(region.getBoundingClientRect().right) : null,
    viewport: document.documentElement.clientWidth,
  };
})()`;

for (const [label, width, height] of [
  ["1280x800", 1280, 800],
  ["1000x700", 1000, 700],
  ["640x700", 640, 700],
]) {
  const page = await visit(cdp, `/sites/${KOBO_SITE}/evidence`, width, height, "[data-capability], [data-evidence-state]");
  await sleep(300);
  const read = await evaluate(READ_T028_CAPABILITY);
  allPass =
    report(`T028 Site > Evidence capability table, ${KOBO_SITE}, at ${label}`, page, [
      [
        "exactly one row (dispatch), scored Full, Limited or None, with a ceiling and a missing-evidence cell",
        read.rows.length === 1 && read.rows[0].id === "dispatch" &&
          ["FULL", "LIMITED", "NONE"].includes(read.rows[0].readiness) &&
          read.rows[0].ceiling !== null && read.rows[0].missing > 0 && read.rows[0].height > 0,
        read.rows.map((r) => `${r.id} ${r.readiness} ceiling ${r.ceiling}, ${r.missing} missing-evidence item(s), ${r.height}px`).join("; ") || "no row",
      ],
      ["the capability table sits above Source health", read.above, `above ${read.above}`],
      [
        "the table is contained",
        (read.overflowX === "auto" || read.overflowX === "scroll") && read.regionRight !== null && read.regionRight <= read.viewport,
        `overflow-x ${read.overflowX}; region right ${read.regionRight} vs ${read.viewport}`,
      ],
      [
        "the page does not scroll horizontally",
        !page.pageScrollsHorizontally,
        `scrollWidth ${page.pageScrollWidth} vs clientWidth ${page.pageClientWidth}`,
      ],
    ]) && allPass;
}

{
  // A third Draft, left RUNNING, for the --readback pass: after the host is
  // restarted it must read INTERRUPTED with Play unavailable.
  await visit(cdp, "/simulator-lab/scenarios/kobo-mini-grid-stop-60/run-setup", 1280, 800, "form", {
    script: submitV2Setup("2026-09-22T03:00:00Z", "2026-09-22T11:00:00Z"),
    waitFor: ".data-table__scroll",
  });
  const listed = await visit(cdp, "/simulator-lab/runs", 1280, 800, "table");
  const href = listed.runRows.find((row) => row.status === "READY")?.href ?? null;
  if (href !== null) {
    await visit(cdp, href, 1280, 800, "[data-execution-status]", {
      script: clickControl("Start this run"),
      waitFor: "[data-execution-status='RUNNING']",
    });
    t025d.live = href;
  }
}

{
  const saved = JSON.parse(readFileSync(READBACK_FILE, "utf-8"));
  saved.t025d = { inspection: t025d.inspection, live: t025d.live, played: t025d.played };
  writeFileSync(READBACK_FILE, JSON.stringify(saved));
}

// --- T028 journey and product vocabulary, live backend text ------------------
//
// Spec section 4: rendered application-authored text and accessible labels on
// the five T028 surfaces, in their Analysis, Evidence, Alternatives and drawer
// states and unknown-item states, checked against the versioned list in
// frontend/src/test/productVocabulary.json - here against the running
// backend's own text, which the frontend suite's fixtures cannot reach. The
// in-browser scan is the same rule as `frontend/src/test/productVocabulary.ts`
// (word boundaries; text nodes plus aria-label, aria-description,
// aria-roledescription, title, alt, placeholder; only single-value elements
// marked data-vocabulary-exempt with a named reason are skipped).
// A planted backend-style sentence proves the browser scan can fail.
//
// A function declaration so ASSETOPS_LAYOUT_T028_JOURNEY_ONLY=1 can run it
// alone against a Lab-off build; it reads no module constant declared below
// the early exit.
async function t028Journey({ labOff }) {
  const site = process.env.ASSETOPS_KOBO_SITE ?? "KOBO-001";
  const CLICK_EVIDENCE = `(() => {
    const b = document.querySelector("[data-evidence-link]");
    if (!b) return null;
    b.click();
    return "opened " + b.getAttribute("data-evidence-link");
  })()`;
  const list = JSON.parse(readFileSync(new URL("../frontend/src/test/productVocabulary.json", import.meta.url), "utf-8"));
  const SCAN = (root) => `((list) => {
    const esc = (t) => t.replace(/[.*+?^\${}()|[\\]\\\\]/g, "\\\\$&");
    const terms = list.terms.map((t) => ({ phrase: t.phrase, re: new RegExp("(?<![\\\\p{L}\\\\p{N}])" + esc(t.phrase).replace(/ /g, "\\\\s+") + "(?![\\\\p{L}\\\\p{N}])", t.caseSensitive ? "u" : "iu") }));
    const glosses = list.glosses.map((g) => new RegExp(esc(g.text), "giu"));
    const reasons = Object.keys(list.exemptions);
    const find = (text) => { let s = text; for (const g of glosses) s = s.replace(g, " "); return terms.filter((t) => t.re.test(s)).map((t) => t.phrase); };
    const root = ${root};
    const out = []; let scanned = 0;
    for (const el of root.querySelectorAll("[data-vocabulary-exempt]")) {
      const r = el.getAttribute("data-vocabulary-exempt");
      if (!reasons.includes(r)) out.push({ phrase: "unknown exemption " + r, text: el.outerHTML.slice(0, 120) });
      else if (el.children.length > 0) out.push({ phrase: "exemption wraps more than one value", text: el.outerHTML.slice(0, 120) });
    }
    const exempt = (el) => el !== null && el.closest("[data-vocabulary-exempt]") !== null;
    const shape = /^[A-Za-z0-9._-]+(?: \\/ [A-Za-z0-9._-]+)*(?: v\\d+)?$/;
    const refs = (el) => ((el && el.closest("[data-vocabulary-reference]")?.getAttribute("data-vocabulary-reference")) || "").split(" | ").filter((v) => v && shape.test(v));
    const strip = (text, el) => refs(el).reduce((t, v) => t.split(v).join(" "), text);
    for (const el of root.querySelectorAll("[data-vocabulary-reference]")) {
      for (const v of el.getAttribute("data-vocabulary-reference").split(" | ")) {
        if (!shape.test(v)) out.push({ phrase: "a reference value is not an identifier", where: "data-vocabulary-reference", text: v });
      }
    }
    const w = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
    for (let n = w.nextNode(); n; n = w.nextNode()) {
      const t = (n.textContent || "").trim();
      if (!t || ["SCRIPT", "STYLE", "NOSCRIPT"].includes(n.parentElement?.tagName) || exempt(n.parentElement)) continue;
      scanned += 1;
      for (const p of find(strip(t, n.parentElement))) out.push({ phrase: p, where: "text", text: t.slice(0, 160) });
    }
    for (const el of [root, ...root.querySelectorAll("*")]) {
      if (exempt(el)) continue;
      for (const a of ["aria-label", "aria-description", "aria-roledescription", "title", "alt", "placeholder"]) {
        const v = el.getAttribute(a);
        if (!v || !v.trim()) continue;
        scanned += 1;
        for (const p of find(strip(v, el))) out.push({ phrase: p, where: a, text: v.slice(0, 160) });
      }
    }
    return { scanned, violations: out };
  })(${JSON.stringify({ terms: list.terms, glosses: list.glosses, exemptions: list.exemptions })})`;
  const SETTLED = `(() => !!document.querySelector("main") && !/Loading/.test(document.body.innerText))()`;
  const scanPath = async (name, path, waitFor = "main", act = null) => {
    await visit(cdp, path, 1280, 800, waitFor);
    await waitUntil(SETTLED, 10000);
    let extra = "";
    if (act !== null) {
      extra = (await evaluate(act)) ?? "";
      await sleep(800);
      await waitUntil(SETTLED, 10000);
    }
    const result = await evaluate(SCAN("document.body"));
    return { name: `${name} (${path}${extra ? ` + ${extra}` : ""})`, ...result };
  };

  // Discover the periods, the Finding and a supporting record from the page.
  await visit(cdp, `/sites/${site}/performance/dispatch`, 1280, 800, "[data-dispatch-interval], [data-dispatch-empty]");
  const rows = await evaluate(`Array.from(document.querySelectorAll("[data-dispatch-interval]")).map((tr) => ({ id: tr.getAttribute("data-dispatch-interval"), finding: tr.querySelector("[data-dispatch-finding-link]")?.getAttribute("href") ?? null }))`);
  const finding = rows.find((r) => r.finding !== null)?.finding ?? null;
  const ids = rows.map((r) => r.id).slice(0, 3);
  await visit(cdp, `/sites/${site}/performance/dispatch?interval=${ids[0]}&view=analysis`, 1280, 800, "main");
  await waitUntil(`!!document.querySelector("[data-analysis-record]")`, 15000);
  const recordHref = await evaluate(`document.querySelector("[data-analysis-record]")?.getAttribute("href") ?? null`);

  const pages = [
    ["Site Overview", `/sites/${site}`],
    ["Dispatch Overview", `/sites/${site}/performance/dispatch`],
    ...ids.map((id) => ["Dispatch Overview, a period selected", `/sites/${site}/performance/dispatch?interval=${id}`]),
    ...ids.map((id) => ["Dispatch Analysis", `/sites/${site}/performance/dispatch?interval=${id}&view=analysis`]),
    ["Dispatch Analysis, unknown period", `/sites/${site}/performance/dispatch?interval=dispatch-gone&view=analysis`],
    ...(finding === null ? [] : [
      ["Finding Overview", finding],
      ["Finding Analysis", `${finding}/analysis`],
      ["Finding Evidence", `${finding}/evidence`],
      ["Finding Evidence, record drawer", `${finding}/evidence`, "[data-evidence-link]", CLICK_EVIDENCE],
      ["Finding Alternatives", `${finding}/alternatives`],
    ]),
    ["Finding, unknown assessment", `/findings/${site}/dispatch-nope`],
    ["Findings index", "/findings"],
    ["Site Findings", `/sites/${site}/findings`],
    ["Site Evidence Overview", `/sites/${site}/evidence`],
    ["Site Evidence Analysis", `/sites/${site}/evidence?view=analysis`],
    ...ids.slice(0, 1).map((id) => ["Site Evidence Analysis, one assessed period", `/sites/${site}/evidence?view=analysis&assessment=${id}`]),
    ...(recordHref === null ? [] : [["Site Evidence, record drawer", recordHref, "[data-evidence-record-detail]"]]),
  ];
  const results = [];
  for (const [name, path, waitFor, act] of pages) {
    results.push(await scanPath(name, path, waitFor ?? "main", act ?? null));
  }
  const violations = results.flatMap((r) => r.violations.map((v) => `${r.name}: "${v.phrase}" in ${v.where}: ${v.text}`));

  // Non-vacuity: a sentence delivered as backend text into the live page.
  await evaluate(`(() => { const p = document.createElement("p"); p.textContent = "The binding constraint held for the whole run."; document.querySelector("main").appendChild(p); return true; })()`);
  const planted = await evaluate(SCAN("document.body"));

  const checks = [
    [
      `every surface and state was found and scanned (${pages.length} pages: a Finding, ${ids.length} periods and a supporting record among them)`,
      finding !== null && ids.length > 0 && recordHref !== null && results.every((r) => r.scanned > 5),
      results.map((r) => `${r.name} ${r.scanned}`).join("; "),
    ],
    [
      `no rendered text or accessible label uses a phrase on the list (version ${list.version})`,
      violations.length === 0,
      violations.length === 0 ? `${results.reduce((n, r) => n + r.scanned, 0)} pieces scanned` : violations.join(" | "),
    ],
    [
      "a planted backend-style sentence is caught, naming its phrases",
      planted.violations.some((v) => v.phrase === "binding") && planted.violations.some((v) => v.phrase === "run"),
      planted.violations.map((v) => v.phrase).join(","),
    ],
  ];
  if (labOff) {
    await visit(cdp, "/simulator-lab", 1280, 800, "main");
    const lab = await evaluate(`(document.querySelector("main h1")?.textContent || "").trim()`);
    checks.push(["with the Lab off, the Lab address is not served", lab === "Page not available", `heading ${lab}`]);
  }
  return report(`T028 journey and product vocabulary, live backend text, ${site}, Lab ${labOff ? "off" : "on"}`, null, checks);
}

finishRun();

function finishRun() {
  console.log(`\n${allPass ? "ALL CLAIMS HOLD" : "AT LEAST ONE CLAIM FAILED"}\n`);
  ws.close();
  chrome.kill();
  try {
    rmSync(profile, { recursive: true, force: true });
  } catch {
    /* Windows sometimes holds the profile briefly */
  }
  process.exit(allPass ? 0 : 1);
}

/** S1-01: which store answers for a Site (`POSTGRES` once imported), or null. */
async function configurationStore(site) {
  try {
    const response = await fetch(`${BASE}/api/sites/${encodeURIComponent(site)}`);
    if (!response.ok) return null;
    const body = await response.json();
    return body.configuration_store ?? null;
  } catch {
    return null;
  }
}
