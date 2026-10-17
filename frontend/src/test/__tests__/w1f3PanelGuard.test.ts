/**
 * W1-F3: non-vacuity of the v69 panel guard on the six findings and money
 * screens. Each screen's approved panel list passes; a planted extra panel, a
 * leading notice and a block inside the status strip each fail.
 */
import { afterEach, describe, expect, it } from "vitest";

import { expectV69Panels } from "../panelStructure";
import { expectedPanelTitles } from "../v69PanelTitles";

const SCREENS = ["sitefindings", "finding", "finding-evidence", "finding-history", "financials", "assumptions"] as const;
const CHROME = `<nav aria-label="Breadcrumb"><ol><li>Sites</li></ol></nav><header class="page-header"><h1>Kobo</h1></header>`;
const STRIP = `<div class="status-strip status-strip--line"><span class="status-strip__state">Open</span></div>`;

/** Dynamic titles take the selected read's values (finding-evidence names the Finding). */
const VALUES: Record<string, string> = { finding: "Generator support merits review" };

function panels(screen: string): string {
  return expectedPanelTitles(screen, VALUES)
    .map((title) => `<section class="panel"><h2>${title}</h2><p class="note">In-panel line.</p></section>`)
    .join("");
}

function mount(body: string): void {
  document.body.innerHTML = `<main>${body}</main>`;
}

describe("W1-F3 v69 panel guard", () => {
  afterEach(() => {
    document.body.innerHTML = "";
  });

  it.each(SCREENS)("%s: the approved panels pass", (screen) => {
    expect(expectedPanelTitles(screen, VALUES).length).toBeGreaterThan(0);
    mount(CHROME + STRIP + panels(screen));
    expect(() => expectV69Panels(screen, VALUES)).not.toThrow();
  });

  it.each(SCREENS)("%s: a planted extra panel fails", (screen) => {
    mount(CHROME + STRIP + panels(screen) + `<section class="panel"><h2>Planted extra panel</h2></section>`);
    expect(() => expectV69Panels(screen, VALUES)).toThrow(/panel structure/);
  });

  it.each(SCREENS)("%s: a notice before panel 1 fails", (screen) => {
    mount(CHROME + `<div class="notice v69-notice">Planted leading notice.</div>` + panels(screen));
    expect(() => expectV69Panels(screen, VALUES)).toThrow(/elements before panel 1/);
  });

  it.each(SCREENS)("%s: a block inside the status strip fails", (screen) => {
    mount(
      CHROME +
        `<div class="status-strip status-strip--line"><div class="product-status"><p>State</p><p>Sentence.</p></div></div>` +
        panels(screen),
    );
    expect(() => expectV69Panels(screen, VALUES)).toThrow(/blocks inside the status strip/);
  });
});
