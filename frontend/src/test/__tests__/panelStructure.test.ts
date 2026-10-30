/**
 * Non-vacuity of the v69 panel guard (W1-F1 review finding 1): a leading
 * answer card fails even when it has no h2 and no `.panel` class.
 */
import { afterEach, describe, expect, it } from "vitest";

import { expectV69Panels, leadingIntruders, stripIntruders, strayBetweenPanels, strayOutsidePanels } from "../panelStructure";

const CHROME = `
  <nav class="breadcrumbs" aria-label="Breadcrumb"><ol><li>Sites</li></ol></nav>
  <header class="page-header"><h1>Sites</h1><p>Find and compare sites</p></header>`;
const LEADING = `
  <div class="v69-chips"><button class="v69-chip" aria-pressed="true">All sites</button></div>
  <div class="v69-cards"><div class="v69-metric"><h3>Sites</h3><p>3</p></div></div>`;
const PANELS = `
  <section class="panel"><h2>Site inventory</h2><table><tr><td>Kobo</td></tr></table></section>
  <section class="panel"><h2>In setup</h2><p>Setup history not available.</p></section>`;

function mount(body: string): void {
  document.body.innerHTML = `<main>${body}</main>`;
}

describe("v69 panel guard", () => {
  afterEach(() => {
    document.body.innerHTML = "";
  });

  it("passes the mock's chrome, leading patterns and panels", () => {
    mount(CHROME + LEADING + PANELS);
    expect(() => expectV69Panels("sites")).not.toThrow();
  });

  it("fails a planted h3 answer card before panel 1", () => {
    mount(CHROME + `<section class="callout"><h3>What is configured?</h3><p>Big verdict.</p></section>` + PANELS);
    expect(leadingIntruders()).toEqual([expect.stringContaining("What is configured?")]);
    expect(() => expectV69Panels("sites")).toThrow(/elements before panel 1/);
  });

  it("fails a planted callout or card with no heading before panel 1", () => {
    mount(CHROME + LEADING + `<div class="callout"><p>Registered sites, not ranked</p></div>` + PANELS);
    expect(() => expectV69Panels("sites")).toThrow(/elements before panel 1/);
    mount(CHROME + `<div class="card"><h4>Second planted card</h4></div>` + PANELS);
    expect(() => expectV69Panels("sites")).toThrow(/elements before panel 1/);
  });

  it("fails a stray h3 subsection outside every panel", () => {
    mount(CHROME + PANELS + `<div class="subsection"><h3>Former panel</h3></div>`);
    expect(strayOutsidePanels()).toEqual([expect.stringContaining("Former panel")]);
    expect(() => expectV69Panels("sites")).toThrow(/sections outside the panels/);
  });

  it("ignores hidden content before panel 1", () => {
    mount(CHROME + `<div hidden><h3>Hidden</h3></div>` + PANELS);
    expect(() => expectV69Panels("sites")).not.toThrow();
  });

  it("passes a one-line status strip made of status-strip parts", () => {
    mount(CHROME + `<div class="status-strip status-strip--line"><span class="status-strip__item">Foundation v10</span><a href="#">Links</a></div>` + PANELS);
    expect(() => expectV69Panels("sites")).not.toThrow();
  });

  it("fails bulk planted inside the status strip", () => {
    mount(CHROME + `<div class="status-strip"><span class="status-strip__lead">Set up</span><div style="padding:28px"><b>Verdict</b><p>One sentence. Another sentence.</p></div></div>` + PANELS);
    expect(stripIntruders()).not.toEqual([]);
    expect(() => expectV69Panels("sites")).toThrow(/blocks inside the status strip/);
  });

  it("fails a stray unpanelled content block between panels", () => {
    mount(CHROME + `<section class="panel"><h2>Site inventory</h2></section><div><b>Configuration readiness</b> Set up to report, long text.</div><section class="panel"><h2>In setup</h2></section>`);
    expect(strayBetweenPanels()).toEqual([expect.stringContaining("Configuration readiness")]);
    expect(() => expectV69Panels("sites")).toThrow(/content blocks between panels/);
  });

  it("allows a trailing notice between panels", () => {
    mount(CHROME + `<section class="panel"><h2>Site inventory</h2></section><p class="notice">Scope note.</p><section class="panel"><h2>In setup</h2></section>`);
    expect(strayBetweenPanels()).toEqual([]);
  });
  // OUT-B B5 (R540): the v7.0 outcome board leads the three Site overview screens only, and only before panel 1.
  const BOARD = `<section class="ob-board" aria-label="Outcomes at this site"><div class="ob-board-head"><h2>How this site is doing</h2></div><details class="ob" open><summary class="ob-sum">Grow revenue</summary><div class="ob-body"><h3>Issues</h3></div></details></section>`;
  it("admits the outcome board before panel 1 on an overview screen and keeps its heading out of the panel titles", () => {
    mount(CHROME + BOARD + PANELS);
    expect(leadingIntruders(undefined, "cold")).toEqual([]);
    expect(strayOutsidePanels()).toEqual([]);
    expect(strayBetweenPanels()).toEqual([]);
  });

  it("fails the outcome board on another screen, or after a panel", () => {
    mount(CHROME + BOARD + PANELS);
    expect(leadingIntruders(undefined, "sites")).toEqual([expect.stringContaining("How this site is doing")]);
    document.body.innerHTML = "";
    mount(CHROME + `<section class="panel"><h2>Site inventory</h2></section>` + BOARD + `<section class="panel"><h2>In setup</h2></section>`);
    expect(strayBetweenPanels()).toEqual([expect.stringContaining("How this site is doing")]);
  });
});
