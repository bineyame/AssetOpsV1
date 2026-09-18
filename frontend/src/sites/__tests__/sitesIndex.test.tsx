import { render, screen, within } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";

import { SitesIndex } from "../SitesIndex";
import type { SiteDirectoryClient } from "../siteDirectoryClient";
import type { SiteListResult, SiteSummary } from "../siteReadModel";
import { deriveSiteView } from "../siteViewModel";

/**
 * Tests for the shared Site presentation substrate.
 *
 * The substrate is rendered directly here, over records, with no shell around
 * it. That is the point: nothing in `frontend/src/sites/` may depend on which
 * shell is rendering it, so nothing in these tests supplies a shell, a mode,
 * or a flag.
 *
 * The load-bearing assertion is the one about independence. In M1 every
 * user-created site also has simulated source mode, because the Simulator Lab
 * is the only creation path, which is exactly the condition under which
 * somebody derives one fact from the other. So two fixture sites are rendered
 * with the combinations that M1 cannot reach, and both facts must render
 * correctly for each.
 */

const USER_SIMULATED_SITE: SiteSummary = {
  site_id: "MG-002",
  display_name: "Kalangala Mini-Grid",
  site_type: "MINIGRID",
  location: { country: "Uganda", locality: "Kalangala" },
  timezone: "Africa/Kampala",
  lifecycle_status: "PLANNED",
  origin: "USER",
  source: { mode: "SIMULATED" },
  template: { template_id: "hybrid-mini-grid-100kw", template_version: 1 },
};

/** `USER` with `LIVE`: a site registered against a real integration. */
const USER_LIVE_SITE: SiteSummary = {
  ...USER_SIMULATED_SITE,
  site_id: "MG-003",
  display_name: "Buvuma Mini-Grid",
  lifecycle_status: "ACTIVE",
  source: { mode: "LIVE" },
};

/** `SHIPPED` with `SIMULATED`: a shipped demo site. */
const SHIPPED_SIMULATED_SITE: SiteSummary = {
  site_id: "CC-001",
  display_name: "Mbale Cold Room",
  site_type: "COLDCHAIN",
  location: { country: "Uganda", locality: "Mbale" },
  timezone: "Africa/Kampala",
  lifecycle_status: "COMMISSIONED",
  origin: "SHIPPED",
  source: { mode: "SIMULATED" },
  template: null,
};

const INTERACTIVE_SELECTOR = [
  "a[href]",
  "button",
  "input",
  "select",
  "textarea",
  "form",
  "details",
  "summary",
  "[onclick]",
  "[role='button']",
  "[role='link']",
  "[role='menuitem']",
  "[role='tab']",
  "[contenteditable='true']",
].join(", ");

/** Controls M1 has decided not to have. Absent from the DOM, not disabled. */
const FORBIDDEN_ACTION_PATTERN =
  /\b(edit|save|publish|rename|duplicate|clone|delete|remove|archive|approve|diff|history|rollback|revert|version history)\b/i;

function directoryWith(result: SiteListResult): SiteDirectoryClient {
  return { listSites: () => Promise.resolve(result) };
}

/**
 * The address of one site's page, supplied the way a shell supplies it.
 *
 * The substrate takes the address as data rather than importing one. It is not
 * a mode and nothing branches on it: it is where the composing shell puts a
 * site page.
 */
const siteHref = (siteId: string) => `/sites/${encodeURIComponent(siteId)}`;

function renderIndex(result: SiteListResult) {
  return render(
    <MemoryRouter>
      <SitesIndex directory={directoryWith(result)} siteHref={siteHref} />
    </MemoryRouter>,
  );
}

/** Every digit run in a string, so screen values can be traced to a record. */
function digitRuns(text: string): string[] {
  return text.match(/\d+(?:\.\d+)?/g) ?? [];
}

describe("sites index states", () => {
  it("states that no site is configured without fabricating a row or a count", async () => {
    const { container } = renderIndex({ status: "loaded", sites: [] });

    expect(
      await screen.findByRole("heading", { level: 2, name: "No sites configured" }),
    ).toBeInTheDocument();
    expect(container.querySelectorAll("table")).toHaveLength(0);
    expect(container.textContent).not.toMatch(/\d/);
  });

  it("states an unreadable store rather than showing an empty one", async () => {
    const { container } = renderIndex({ status: "unavailable" });

    expect(
      await screen.findByRole("heading", { level: 2, name: "Sites unavailable" }),
    ).toBeInTheDocument();
    expect(container.textContent).not.toMatch(/No sites configured/i);
  });
});

describe("sites index rows", () => {
  it("keys a row by site ID and shows its configuration", async () => {
    renderIndex({ status: "loaded", sites: [USER_SIMULATED_SITE] });

    const row = within(await screen.findByRole("table")).getAllByRole("row")[1];

    expect(within(row).getByText("MG-002")).toBeInTheDocument();
    expect(within(row).getByText("Kalangala Mini-Grid")).toBeInTheDocument();
    expect(within(row).getByText("Mini-grid")).toBeInTheDocument();
    expect(within(row).getByText("Kalangala, Uganda")).toBeInTheDocument();
    expect(within(row).getByText("Planned")).toBeInTheDocument();
    expect(within(row).getByText("Simulated")).toBeInTheDocument();
    expect(within(row).getByText("User")).toBeInTheDocument();
    expect(
      within(row).getByText("hybrid-mini-grid-100kw v1"),
    ).toBeInTheDocument();
  });

  it("renders no value the record does not supply", async () => {
    const sites = [USER_SIMULATED_SITE, SHIPPED_SIMULATED_SITE];
    renderIndex({ status: "loaded", sites });
    await screen.findByRole("table");

    const fromRecords = new Set(digitRuns(JSON.stringify(sites)));
    const onScreen = digitRuns(
      screen.getByRole("table").textContent ?? "",
    );

    expect(onScreen.length).toBeGreaterThan(0);
    for (const value of onScreen) {
      expect(fromRecords).toContain(value);
    }
  });

  it("says plainly when a site came from no template", async () => {
    renderIndex({ status: "loaded", sites: [SHIPPED_SIMULATED_SITE] });

    expect(
      await screen.findByText("Not created from a template"),
    ).toBeInTheDocument();
  });

  it("opens the site from its row, and adds no other destination", async () => {
    /**
     * T006 asserted that no row was a link, because the route behind one did
     * not exist. It exists now, so the assertion is replaced rather than
     * dropped: the row link is pinned to the site's own address, and it is
     * still the only destination the listing offers.
     */
    const { container } = renderIndex({
      status: "loaded",
      sites: [USER_SIMULATED_SITE, SHIPPED_SIMULATED_SITE],
    });
    await screen.findByRole("table");

    const links = Array.from(container.querySelectorAll("a")).map((link) => [
      link.getAttribute("href"),
      link.textContent,
    ]);

    // T011 puts the name and the identity in one cell and adds a `View`
    // action, so a row now offers two links. Both resolve to the same place,
    // so the claim this test makes - that the listing offers exactly one
    // destination per site and no other - is unchanged, and is now asserted on
    // the set of destinations rather than on the number of anchors.
    expect(links).toEqual([
      ["/sites/MG-002", "Kalangala Mini-Grid"],
      ["/sites/MG-002", "View"],
      ["/sites/CC-001", "Mbale Cold Room"],
      ["/sites/CC-001", "View"],
    ]);
    expect(new Set(links.map(([href]) => href))).toEqual(
      new Set(["/sites/MG-002", "/sites/CC-001"]),
    );
  });

  it("addresses a row by site ID and never by name or template", async () => {
    const { container } = renderIndex({
      status: "loaded",
      sites: [USER_SIMULATED_SITE],
    });
    await screen.findByRole("table");

    const href = container.querySelector("a")?.getAttribute("href") ?? "";

    expect(href).toBe("/sites/MG-002");
    expect(href).not.toMatch(/Kalangala/i);
    expect(href).not.toMatch(/hybrid-mini-grid/i);
  });
});

describe("configuration origin, source mode, and lifecycle stay separate", () => {
  it("renders both facts correctly for combinations M1 cannot reach", async () => {
    const sites = [USER_LIVE_SITE, SHIPPED_SIMULATED_SITE];
    renderIndex({ status: "loaded", sites });

    const rows = within(await screen.findByRole("table")).getAllByRole("row");
    const userLive = rows.find((row) =>
      row.textContent?.includes("MG-003"),
    ) as HTMLElement;
    const shippedSimulated = rows.find((row) =>
      row.textContent?.includes("CC-001"),
    ) as HTMLElement;

    // Origin USER with mode LIVE: neither is derived from the other.
    expect(within(userLive).getByText("User")).toBeInTheDocument();
    expect(within(userLive).getByText("Live")).toBeInTheDocument();
    expect(within(userLive).queryByText("Simulated")).toBeNull();

    // Origin SHIPPED with mode SIMULATED: the mirror case.
    expect(within(shippedSimulated).getByText("Shipped")).toBeInTheDocument();
    expect(within(shippedSimulated).getByText("Simulated")).toBeInTheDocument();
    expect(within(shippedSimulated).queryByText("User")).toBeNull();
  });

  it("gives mode, lifecycle, and origin three separate columns", async () => {
    renderIndex({ status: "loaded", sites: [USER_SIMULATED_SITE] });

    const headers = within(await screen.findByRole("table"))
      .getAllByRole("columnheader")
      .map((header) => header.textContent);

    // The canonical column set. Nine, not the settled inventory's seven: that
    // inventory omits configuration origin and template provenance, while the
    // T006 user-review checkpoint accepted them as two of four separate
    // provenance columns, and a checkpoint settles a surface.
    //
    // Mode and Lifecycle are adjacent and distinct, which is the assertion
    // that matters here. The mockup's single `Status` column is the error this
    // screen exists to correct.
    expect(headers).toEqual([
      "Name",
      "Type",
      "Location",
      "Mode",
      "Lifecycle",
      "Configuration origin",
      "Created from template",
      "Last analysed",
      "Actions",
    ]);

    // No header carries both vocabularies, and none is called `Status`.
    for (const header of headers) {
      expect(header).not.toMatch(/^status$/i);
      expect(header).not.toMatch(/mode.*lifecycle|lifecycle.*mode/i);
    }

    // The canonical mockup collapses provenance into a `Status` column. That
    // is a mockup error to correct rather than copy.
    expect(headers).not.toContain("Status");
  });

  it("derives neither fact from the other in the view model", () => {
    expect(deriveSiteView(USER_LIVE_SITE).configurationOrigin).toBe("User");
    expect(deriveSiteView(USER_LIVE_SITE).sourceMode).toBe("Live");
    expect(deriveSiteView(SHIPPED_SIMULATED_SITE).configurationOrigin).toBe(
      "Shipped",
    );
    expect(deriveSiteView(SHIPPED_SIMULATED_SITE).sourceMode).toBe("Simulated");
  });

  it("shows an unrecognised value as it arrived rather than inventing a label", () => {
    const view = deriveSiteView({
      ...USER_SIMULATED_SITE,
      lifecycle_status: "MOTHBALLED",
      source: { mode: "REPLAYED" },
    });

    expect(view.lifecycleStatus).toBe("MOTHBALLED");
    expect(view.sourceMode).toBe("REPLAYED");
  });
});

describe("the index shows no capability the product lacks", () => {
  it("offers no edit, save, publish, rename, duplicate, delete, or history control", async () => {
    const { container } = renderIndex({
      status: "loaded",
      sites: [USER_SIMULATED_SITE],
    });
    await screen.findByRole("table");

    // Not merely "no enabled control": deferred-by-decision capabilities are
    // absent from the DOM rather than rendered disabled. Rows are links now,
    // so the assertion is pinned to exactly that one kind of control rather
    // than relaxed: every interactive element is a link to a site page, and
    // nothing else of any kind is interactive.
    const interactive = Array.from(
      container.querySelectorAll<HTMLElement>(INTERACTIVE_SELECTOR),
    );

    // T011 gives the index a search field and three filters, all of which only
    // narrow what is already listed. So the controls are named rather than
    // counted: anything that is not one of these four, or a link to a site
    // page, still fails - stronger than a count, because it also fails for a
    // different control that happens to keep the total the same.
    expect(
      interactive.map((control) => [
        control.tagName,
        control.getAttribute("id") ?? control.getAttribute("href"),
      ]),
    ).toEqual([
      ["INPUT", "sites-search"],
      ["SELECT", "sites-type"],
      ["SELECT", "sites-mode"],
      ["SELECT", "sites-lifecycle"],
      ["A", "/sites/MG-002"],
      ["A", "/sites/MG-002"],
    ]);
    expect(container.textContent ?? "").not.toMatch(FORBIDDEN_ACTION_PATTERN);
  });

  it("shows no evidence-derived column, chart, health, or finding", async () => {
    const { container } = renderIndex({
      status: "loaded",
      sites: [USER_SIMULATED_SITE],
    });
    await screen.findByRole("table");

    expect(container.querySelectorAll("svg, canvas, img")).toHaveLength(0);
    expect(screen.queryAllByRole("figure")).toHaveLength(0);

    const headers = within(screen.getByRole("table"))
      .getAllByRole("columnheader")
      .map((header) => (header.textContent ?? "").trim());

    expect(headers.length).toBeGreaterThan(0);
    for (const header of headers) {
      // `last analysed` left this list in T011, which requires the column.
      // What the list was protecting is unchanged and is asserted directly in
      // the test below instead: the column may exist, but it may never carry
      // a value. The mockup's `Last Data` stays banned, because its content is
      // timestamps the product does not have.
      expect(header).not.toMatch(
        /\b(last data|health|evidence|telemetry|analytics|replay|findings?|quality|readiness)\b/i,
      );
    }
  });

  it("renders no single line diagram, diagram frame, or signal selector", async () => {
    const { container } = renderIndex({
      status: "loaded",
      sites: [USER_SIMULATED_SITE],
    });
    await screen.findByRole("table");

    expect(container.querySelectorAll("svg, canvas")).toHaveLength(0);

    // This banned every `select` and every combobox as a proxy for the signal
    // selector that sits above a single line diagram. The proxy held while the
    // index had no controls; it stops being about diagrams the moment the
    // screen has legitimate filters, and T011 gives it three. So the
    // comboboxes are identified instead of forbidden: a signal selector would
    // be a fourth, or one of these renamed, and either fails.
    expect(
      screen.queryAllByRole("combobox").map((el) => el.getAttribute("id")),
    ).toEqual(["sites-type", "sites-mode", "sites-lifecycle"]);

    // The vocabulary rule is untouched and is what actually names the
    // deferred capability.
    expect(container.textContent ?? "").not.toMatch(
      /single line diagram|diagram|signal/i,
    );
  });

  it("renders Last analysed as a dash for every site, never a timestamp", async () => {
    renderIndex({
      status: "loaded",
      sites: [USER_SIMULATED_SITE, SHIPPED_SIMULATED_SITE],
    });
    await screen.findByRole("table");

    const table = screen.getByRole("table");
    const headers = within(table)
      .getAllByRole("columnheader")
      .map((header) => (header.textContent ?? "").trim());
    const column = headers.indexOf("Last analysed");
    expect(column).toBeGreaterThan(-1);

    const cells = within(table)
      .getAllByRole("row")
      .slice(1)
      .map((row) => (within(row).getAllByRole("cell")[column].textContent ?? "").trim());

    // Every site, not just the first. `--` is v6.9's rendering for a site with
    // no data in the window; the mockup's timestamps are evidence this build
    // does not have, and reproducing one would be the clearest case of a
    // mockup literal becoming content.
    expect(cells).toEqual(["--", "--"]);
    for (const cell of cells) {
      expect(cell).not.toMatch(/\d/);
      expect(cell).not.toMatch(/ago|min|hour|day|:/i);
    }
  });
});

describe("the substrate is a leaf with no shell discriminant", () => {
  it("renders identically whichever shell composes it", async () => {
    const first = renderIndex({
      status: "loaded",
      sites: [USER_SIMULATED_SITE],
    });
    await within(first.container).findByRole("table");
    const firstMarkup = first.container.innerHTML;
    first.unmount();

    const second = renderIndex({
      status: "loaded",
      sites: [USER_SIMULATED_SITE],
    });
    await within(second.container).findByRole("table");

    // There is no shell, mode, or variant prop to vary, which is why this can
    // only be a same-input assertion today. The real render-equivalence guard
    // needs a second consumer and ships with the Lab's site view.
    expect(second.container.innerHTML).toBe(firstMarkup);
  });
});
