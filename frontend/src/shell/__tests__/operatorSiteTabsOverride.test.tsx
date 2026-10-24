import { cleanup, render, screen, within } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, describe, expect, it } from "vitest";

import { EV_SITE_TAB_HREFS } from "../evSiteRoutes";
import { OPERATOR_SITE_TABS, OperatorSiteTabs, operatorSiteTabHref } from "../operatorSiteTabs";

afterEach(cleanup);

const hrefs = () =>
  within(screen.getByRole("navigation", { name: "Site sections" }))
    .getAllByRole("link")
    .map((a) => [a.textContent, a.getAttribute("href")]);

describe("post-W6 W2-EV: OperatorSiteTabs href override and selected-window query", () => {
  it("keeps the canonical hrefs when nothing is overridden", () => {
    render(
      <MemoryRouter>
        <OperatorSiteTabs siteId="MG-002" current="Overview" />
      </MemoryRouter>,
    );
    expect(hrefs()).toEqual(OPERATOR_SITE_TABS.map((t) => [t.label, t.href("MG-002")]));
  });

  it("sends EV Overview, Evidence and Financials to the built EV pages and carries the window on every tab", () => {
    const search = "?from=2026-10-20T00%3A00%3A00Z&to=2026-10-21T00%3A00%3A00Z&known_at=2026-10-21T00%3A00%3A00Z";
    render(
      <MemoryRouter>
        <OperatorSiteTabs siteId="EV-LAB-001" current="Evidence" hrefs={EV_SITE_TAB_HREFS} search={search} />
      </MemoryRouter>,
    );
    const map = Object.fromEntries(hrefs());
    expect(map.Overview).toBe(`/sites/EV-LAB-001/ev${search}`);
    expect(map.Evidence).toBe(`/sites/EV-LAB-001/ev/evidence${search}`);
    expect(map.Financials).toBe(`/sites/EV-LAB-001/ev/financials${search}`);
    expect(map.Foundation).toBe(`/sites/EV-LAB-001/foundation${search}`);
    for (const [, href] of hrefs()) {
      expect(href).not.toMatch(/^\/sites\/EV-LAB-001\/(evidence|financials)(\?|$)/);
      expect(href).toContain("known_at=");
    }
  });

  it("carries no query without a selected window and joins onto an existing query", () => {
    const tab = { label: "Overview", capability: true, href: () => "/x?a=1" };
    expect(operatorSiteTabHref(tab, "S", undefined, "")).toBe("/x?a=1");
    expect(operatorSiteTabHref(tab, "S", undefined, undefined)).toBe("/x?a=1");
    expect(operatorSiteTabHref(tab, "S", undefined, "?from=a&to=b")).toBe("/x?a=1&from=a&to=b");
    expect(operatorSiteTabHref(tab, "S", { Overview: (s) => `/sites/${s}/ev` }, "from=a")).toBe("/sites/S/ev?from=a");
  });
});
