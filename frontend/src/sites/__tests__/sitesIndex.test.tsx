import { fireEvent, render, screen, within } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";

import { SitesIndex } from "../SitesIndex";
import type { SiteDirectoryClient } from "../siteDirectoryClient";
import type { SiteListResult, SiteSummary } from "../siteReadModel";
import { deriveSiteView } from "../siteViewModel";
import { spacedText } from "../../test/text";
import { describeViolations, scanDisclosureVocabulary, scanProductVocabulary } from "../../test/productVocabulary";
import { settledScreen } from "../../test/settled";

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
    expect(spacedText(container)).not.toMatch(/\d/);
  });

  it("states an unreadable store rather than showing an empty one", async () => {
    const { container } = renderIndex({ status: "unavailable" });

    expect(
      await screen.findByRole("heading", { level: 2, name: "Sites unavailable" }),
    ).toBeInTheDocument();
    expect(spacedText(container)).not.toMatch(/No sites configured/i);
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
    expect(within(row).getByText("Demonstration data")).toBeInTheDocument();
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

describe("the index filters over the sites it actually has", () => {
  const THREE = [USER_SIMULATED_SITE, USER_LIVE_SITE, SHIPPED_SIMULATED_SITE];

  function rowNames(): string[] {
    return within(screen.getByRole("table"))
      .getAllByRole("row")
      .slice(1)
      .map((row) => {
        const cell = within(row).getAllByRole("cell")[0];
        // Name plus identity; the location shares the secondary line.
        const link = cell.querySelector("a")?.textContent ?? "";
        const id = cell.querySelector(".cell-secondary span")?.textContent ?? "";
        return link + id;
      });
  }

  function optionsOf(id: string): string[] {
    return within(document.getElementById(id) as HTMLElement)
      .getAllByRole("option")
      .map((option) => option.textContent ?? "");
  }

  it("offers only the values the configured sites carry", async () => {
    renderIndex({ status: "loaded", sites: THREE });
    await screen.findByRole("table");

    // No DECOMMISSIONED, no ARCHIVED, no site type nothing is. The M1 schema
    // permits more than these; a filter offering one teaches a fleet this
    // build does not have, and an empty result for it would be
    // indistinguishable from a state the product never reaches.
    expect(optionsOf("sites-type")).toEqual([
      "All types",
      "Cold chain",
      "Mini-grid",
    ]);
    expect(optionsOf("sites-mode")).toEqual(["All modes", "Demonstration data", "Live"]);
    expect(optionsOf("sites-lifecycle")).toEqual([
      "All lifecycle states",
      "Active",
      "Commissioned",
      "Planned",
    ]);
  });

  it("narrows by mode and by lifecycle independently", async () => {
    renderIndex({ status: "loaded", sites: THREE });
    await screen.findByRole("table");

    fireEvent.change(screen.getByLabelText("Mode"), {
      target: { value: "Live" },
    });
    expect(rowNames()).toEqual([USER_LIVE_SITE.display_name + "MG-003"]);

    fireEvent.change(screen.getByLabelText("Mode"), {
      target: { value: "__any__" },
    });
    fireEvent.change(screen.getByLabelText("Lifecycle"), {
      target: { value: "Commissioned" },
    });

    // A different site, which is the point: the two filters select on
    // different facts and neither is a proxy for the other.
    expect(rowNames()).toEqual([
      SHIPPED_SIMULATED_SITE.display_name + "CC-001",
    ]);
  });

  it("searches over the name and the identity", async () => {
    renderIndex({ status: "loaded", sites: THREE });
    await screen.findByRole("table");

    const search = screen.getByLabelText("Search sites");

    fireEvent.change(search, { target: { value: "buvuma" } });
    expect(rowNames()).toEqual([USER_LIVE_SITE.display_name + "MG-003"]);

    fireEvent.change(search, { target: { value: "cc-001" } });
    expect(rowNames()).toEqual([
      SHIPPED_SIMULATED_SITE.display_name + "CC-001",
    ]);
  });

  it("says an empty result is about the filters, never about the store", async () => {
    renderIndex({ status: "loaded", sites: THREE });
    await screen.findByRole("table");

    fireEvent.change(screen.getByLabelText("Search sites"), {
      target: { value: "no-such-site" },
    });

    expect(screen.queryByRole("table")).toBeNull();

    // The distinction T006 settled: an empty store and a filter that matched
    // nothing are different facts, and the first-run copy must not be reused
    // for the second.
    const text = document.body.textContent ?? "";
    expect(text).toMatch(/statement about the filters/i);
    expect(text).toMatch(/3 sites are configured/);
    expect(text).not.toMatch(/No site has been configured/i);
  });
});

describe("the Actions column offers only what exists", () => {
  it("contains View and nothing else, with no overflow menu", async () => {
    renderIndex({ status: "loaded", sites: [USER_SIMULATED_SITE] });
    await screen.findByRole("table");

    const table = screen.getByRole("table");
    const headers = within(table)
      .getAllByRole("columnheader")
      .map((header) => (header.textContent ?? "").trim());
    const column = headers.indexOf("Actions");
    const cell = within(within(table).getAllByRole("row")[1]).getAllByRole(
      "cell",
    )[column];

    expect((cell.textContent ?? "").trim()).toBe("View");
    expect(within(cell).getAllByRole("link")).toHaveLength(1);

    // The mockup draws an overflow beside View. It would open onto nothing:
    // every action it could hold is one M1 has decided not to have, and a
    // disabled one would read as "soon".
    expect(cell.querySelectorAll("button, [role='menu'], details")).toHaveLength(
      0,
    );
    expect((cell.textContent ?? "")).not.toMatch(/\.\.\.|…/);
  });

  it.each(["Edit", "Duplicate Site", "Delete Site", "Archive"])(
    "does not render %s anywhere, disabled or otherwise",
    async (label) => {
      const { container } = renderIndex({
        status: "loaded",
        sites: [USER_SIMULATED_SITE],
      });
      await screen.findByRole("table");

      // Absence from the DOM, not disabled state: disabled reads as soon, and
      // none of these is coming.
      expect(screen.queryByRole("button", { name: label })).toBeNull();
      expect(screen.queryByRole("link", { name: label })).toBeNull();
      expect(screen.queryByText(label)).toBeNull();
      expect(container.querySelectorAll("[disabled], [aria-disabled='true']"))
        .toHaveLength(0);
    },
  );
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
    expect(within(userLive).queryByText("Demonstration data")).toBeNull();

    // Origin SHIPPED with mode SIMULATED: the mirror case.
    expect(within(shippedSimulated).getByText("Shipped")).toBeInTheDocument();
    expect(within(shippedSimulated).getByText("Demonstration data")).toBeInTheDocument();
    expect(within(shippedSimulated).queryByText("User")).toBeNull();
  });

  it("keeps mode primary and lifecycle, origin and template as separate labelled setup facts", async () => {
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
      "Site",
      "Type",
      "Mode",
      "Operating view",
      "Setup details",
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
    expect(deriveSiteView(SHIPPED_SIMULATED_SITE).sourceMode).toBe("Demonstration data");
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
      // W1-UX-02: the answer card's closed exact-reference disclosure (site
      // references only), named here so any other control still fails.
      ["DETAILS", null],
      ["SUMMARY", null],
      ["INPUT", "sites-search"],
      ["SELECT", "sites-type"],
      ["SELECT", "sites-mode"],
      ["SELECT", "sites-lifecycle"],
      ["A", "/sites/MG-002"],
      ["DETAILS", null],
      ["SUMMARY", null],
      ["A", "/sites/MG-002"],
    ]);
    expect(spacedText(container)).not.toMatch(FORBIDDEN_ACTION_PATTERN);
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
    expect(spacedText(container)).not.toMatch(
      /single line diagram|diagram|signal/i,
    );
  });

  it("has no Last analysed dash column and explains the absent analytical columns", async () => {
    renderIndex({
      status: "loaded",
      sites: [USER_SIMULATED_SITE, SHIPPED_SIMULATED_SITE],
    });
    await screen.findByRole("table");

    const table = screen.getByRole("table");
    const headers = within(table)
      .getAllByRole("columnheader")
      .map((header) => (header.textContent ?? "").trim());
    expect(headers).not.toContain("Last analysed");
    for (const header of headers) {
      expect(header).not.toMatch(/assessment|top issue|evidence|last analys/i);
    }
    // No cell is a bare dash standing in for an analysis that never happened.
    for (const cell of within(table).getAllByRole("cell")) {
      expect((cell.textContent ?? "").trim()).not.toBe("--");
    }
    // The four mock columns are explained once, beside the table, without a
    // value, a count or a health word.
    const note = screen.getByTestId("sites-analysis-absent");
    expect(note.textContent).toBe(
      "Assessment, top issue, evidence limit and last analysis are not available in this directory. Open a Site for its selected-window evidence and assessments.",
    );
    expect(note.textContent).not.toMatch(/\d|healthy|no issue/i);
  });

  it("states one grouped Operating view cell per Site as not available yet, and the aggregate gap once (V-01a round 3)", async () => {
    renderIndex({
      status: "loaded",
      sites: [USER_SIMULATED_SITE, SHIPPED_SIMULATED_SITE],
    });
    const table = await screen.findByRole("table");
    const headers = within(table).getAllByRole("columnheader").map((h) => (h.textContent ?? "").trim());
    expect(headers).toEqual(["Site", "Type", "Mode", "Operating view", "Setup details", "Actions"]);
    const cells = Array.from(table.querySelectorAll("[data-operating-view]"));
    expect(cells).toHaveLength(2);
    for (const cell of cells) {
      expect(cell.querySelector(".not-available-yet")?.textContent).toBe("Not available yet");
      expect(cell.querySelector(".cell-secondary")?.textContent).toBe("Assessment · top issue · evidence limit · last analysed");
      expect(cell.textContent).not.toMatch(/\d|healthy|needs attention|limited/i);
    }
    const aggregate = screen.getByTestId("sites-aggregate-absent");
    expect(aggregate.textContent).toBe(
      "2 registered Sites listed. Needs attention and Evidence limited counts across Sites are not available yet: there is no common window or aggregation contract for them. Setup progress not tracked yet.",
    );
  });

  it("tags each Sites missing claim with its own catalogued gap, and none in the empty or unreadable states (G-02)", async () => {
    const pairs = (root: ParentNode) =>
      [...new Set([...root.querySelectorAll("[data-gap-id]")].map((el) => `${el.getAttribute("data-gap-id")}@${el.getAttribute("data-gap-placement")}`))].sort();
    const TEXT: Record<string, string> = {
      "sites.inventory.operating-view": "Not available yetAssessment · top issue · evidence limit · last analysed",
      "sites.inventory.analysis-note":
        "Assessment, top issue, evidence limit and last analysis are not available in this directory. Open a Site for its selected-window evidence and assessments.",
      "sites.inventory.attention-counts":
        "Needs attention and Evidence limited counts across Sites are not available yet: there is no common window or aggregation contract for them.",
      "sites.inventory.setup-progress": "Setup progress not tracked yet.",
    };
    const view = renderIndex({ status: "loaded", sites: [USER_SIMULATED_SITE, SHIPPED_SIMULATED_SITE] });
    await screen.findByRole("table");
    expect(pairs(document)).toEqual([
      "G-sites-attention-counts@sites.inventory.attention-counts",
      "G-sites-operating-view@sites.inventory.analysis-note",
      "G-sites-operating-view@sites.inventory.operating-view",
      "G-sites-setup-progress@sites.inventory.setup-progress",
    ]);
    const tagged = [...document.querySelectorAll("[data-gap-id]")];
    expect(document.querySelectorAll('[data-gap-placement="sites.inventory.operating-view"]')).toHaveLength(2);
    for (const el of tagged) {
      expect(el.textContent).toBe(TEXT[el.getAttribute("data-gap-placement") as string]);
      expect(el.getAttribute("data-gap-status")).toBe("open");
      expect(el.querySelector("[data-gap-id]")).toBeNull();
    }
    // The aggregate note's two claims are separate elements; the registered count stays outside both.
    const aggregate = screen.getByTestId("sites-aggregate-absent");
    expect(aggregate.querySelectorAll("[data-gap-id]")).toHaveLength(2);
    expect(document.body.textContent).not.toMatch(/G-sites-/);
    view.unmount();

    for (const result of [{ status: "loaded" as const, sites: [] }, { status: "unavailable" as const }]) {
      const other = renderIndex(result);
      await screen.findByRole("heading", { level: 2, name: result.status === "loaded" ? "No sites configured" : "Sites unavailable" });
      expect(document.querySelector("[data-gap-id]")).toBeNull();
      other.unmount();
    }
  });

  it("puts identity and location in the Site cell's secondary line", async () => {
    renderIndex({ status: "loaded", sites: [USER_SIMULATED_SITE] });
    const row = within(await screen.findByRole("table")).getAllByRole("row")[1];
    const siteCell = within(row).getAllByRole("cell")[0];
    expect(siteCell.querySelector(".cell-secondary")?.textContent).toBe(
      "MG-002 · Kalangala, Uganda",
    );
    const details = within(row).getByText("Setup details").closest("details");
    expect(details).not.toBeNull();
    const terms = Array.from(details!.querySelectorAll("dt")).map((dt) => dt.textContent);
    expect(terms).toEqual(["Lifecycle", "Configuration origin", "Created from template"]);
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

/** The explicit closed-disclosure checks for a state line whose read carries no time. */
function expectUntimedStateLine(card: Element, label: string) {
  const status = card.querySelector("[data-product-status]") as HTMLElement;
  expect(status, "a shared state line is rendered").not.toBeNull();
  for (const details of Array.from(card.querySelectorAll<HTMLDetailsElement>("details[data-exact-references]"))) {
    expect(details.open).toBe(false);
  }
  expect(status.querySelector("[data-product-status-label]")?.textContent).toBe(label);
  expect((status.querySelector(".product-status__sentence")?.textContent ?? "").trim().length).toBeGreaterThan(0);
  expect(status.querySelector("[data-product-status-scope]")?.textContent).toBe("All registered sites");
  expect(status.querySelector("[data-product-status-as-of]")?.textContent).toBe("As of: time not recorded");
  expect(status.closest("details")).toBeNull();
}

describe("W1-UX-02: the Sites directory (sites) on the W1 set", () => {
  it("answers which site to open by identity only, with registered scope, a closed exact-reference disclosure and no attention claim", async () => {
    const { container } = renderIndex({
      status: "loaded",
      sites: [USER_SIMULATED_SITE, { ...SHIPPED_SIMULATED_SITE, configuration_store: "POSTGRES" }],
    });
    await screen.findByRole("table");
    await settledScreen();
    const card = container.querySelector('[data-headline-card="sites-directory"]') as HTMLElement;
    expect(card).not.toBeNull();
    expect(card.querySelector(".headline-card__question")?.textContent).toBe("Which site should I open?");
    expect(card.querySelector(".headline-card__headline")?.textContent).toBe("2 registered sites: open one by name below.");
    expectUntimedStateLine(card, "Registered sites, not ranked");
    // The material limit sits beside the answer, outside any disclosure.
    expect(card.querySelector(".product-status__sentence")?.textContent).toContain("does not judge how any site is operating");
    expect(card.querySelector("[data-sites-scope]")?.textContent).toContain("Mini-grid: 1");
    expect(card.querySelector("[data-sites-scope]")?.textContent).toContain("Demonstration data: 2");
    expect(card.querySelector("[data-sites-scope-limit]")?.textContent).toContain("Not judged in this list");
    // No condition, ranking or attention is claimed anywhere on the card.
    expect(card.textContent).not.toMatch(/needs attention|healthy|top issue|degraded/i);
    // Exact references: each site's reference and registration store, labelled, in the closed disclosure.
    const details = card.querySelector("details[data-exact-references]") as HTMLDetailsElement;
    expect(details.open).toBe(false);
    const codes = Array.from(details.querySelectorAll("code")).map((c) => c.textContent);
    expect(codes).toEqual(["MG-002", "CC-001", "POSTGRES"]);
    expect(details.textContent).toContain("Kalangala Mini-Grid: registration storenot recorded");
    const w1 = scanProductVocabulary(container, "sites directory (W1)", { set: "w1" });
    expect(w1.scanned).toBeGreaterThan(20);
    expect(w1.violations, describeViolations(w1.violations)).toEqual([]);
    const d = scanDisclosureVocabulary(card, "sites directory disclosure");
    expect(d.disclosures).toBe(1);
    expect(d.scanned).toBeGreaterThan(2);
    expect(d.violations, describeViolations(d.violations)).toEqual([]);
    // The three missing claims stay unchanged beside the inventory.
    expect(container.querySelectorAll("[data-gap-id]")).toHaveLength(5);
  });

  it("the empty and unreadable directories state themselves on the same card, distinctly, with no count", async () => {
    const empty = renderIndex({ status: "loaded", sites: [] });
    await screen.findByRole("heading", { level: 2, name: "No sites configured" });
    const emptyCard = empty.container.querySelector('[data-headline-card="sites-directory"]') as HTMLElement;
    expectUntimedStateLine(emptyCard, "No sites registered");
    expect(emptyCard.querySelector("[data-product-status]")?.getAttribute("data-product-status")).toBe("neutral");
    const emptyScan = scanProductVocabulary(empty.container, "sites empty (W1)", { set: "w1" });
    expect(emptyScan.violations, describeViolations(emptyScan.violations)).toEqual([]);
    empty.unmount();

    const unreadable = renderIndex({ status: "unavailable" });
    await screen.findByRole("heading", { level: 2, name: "Sites unavailable" });
    const card = unreadable.container.querySelector('[data-headline-card="sites-directory"]') as HTMLElement;
    expectUntimedStateLine(card, "This could not be read right now");
    expect(card.querySelector(".product-status__sentence")?.textContent).toContain("It is not empty");
    expect(card.textContent).not.toMatch(/No sites registered/);
    const scan = scanProductVocabulary(unreadable.container, "sites unreadable (W1)", { set: "w1" });
    expect(scan.violations, describeViolations(scan.violations)).toEqual([]);
  });

  it("a loaded directory with one site uses the singular and stays unranked", async () => {
    const { container } = renderIndex({ status: "loaded", sites: [USER_SIMULATED_SITE] });
    await screen.findByRole("table");
    const card = container.querySelector('[data-headline-card="sites-directory"]') as HTMLElement;
    expect(card.querySelector(".headline-card__headline")?.textContent).toBe("1 registered site: open one by name below.");
    expect(card.querySelector("[data-product-status]")?.getAttribute("data-product-status")).not.toBe("positive");
  });
});
