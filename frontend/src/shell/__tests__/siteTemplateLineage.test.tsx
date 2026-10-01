import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

import { App } from "../../App";
import { featureFlagsWith, type FeatureFlags } from "../../config/featureFlags";
import type { SiteDetailReadModel, SiteSummary } from "../../sites/siteReadModel";
import {
  templateLineageNote,
  type SiteTemplateLineageClient,
  type SiteTemplateLineageReadModel,
} from "../../sites/siteTemplateLineage";
import { settledScreen } from "../../test/settled";
import { siteDetailHref, siteFoundationHref } from "../operatorSiteRoutes";
import koboDetail from "./kobo-site-detail.json";

/**
 * T025f: the advisory lineage note beside "Created from template".
 *
 * In-process fixtures only. `MG-OLD` records the Kobo template at v1 and
 * `MG-NEW` at v2; the lineage client answers as the backend would with the
 * shipped catalog at v2.
 */

const ENABLED = featureFlagsWith(true);
const DISABLED = featureFlagsWith(false);
const BEHIND_NOTE = "Created from v1; current template is v2";

function detail(siteId: string, version: number): SiteDetailReadModel {
  const base = koboDetail as unknown as SiteDetailReadModel;
  return {
    ...base,
    site_id: siteId,
    display_name: `Site ${siteId}`,
    template: { template_id: "kobo-mini-grid-60kw", template_version: version },
  };
}

const OLD = detail("MG-OLD", 1);
const NEW = detail("MG-NEW", 2);
const PLAIN: SiteDetailReadModel = { ...detail("MG-PLAIN", 1), template: null };

function lineageFor(site: SiteSummary): SiteTemplateLineageReadModel {
  if (site.template === null) {
    return {
      site_id: site.site_id,
      template: null,
      state: "NO_TEMPLATE",
      current_template_version: null,
    };
  }
  return {
    site_id: site.site_id,
    template: site.template,
    state: site.template.template_version < 2 ? "BEHIND" : "CURRENT",
    current_template_version: 2,
  };
}

function lineageClient(sites: SiteSummary[]) {
  const listLineage = vi.fn(async () => ({
    status: "loaded" as const,
    sites: sites.map(lineageFor),
  }));
  return { client: { listLineage } satisfies SiteTemplateLineageClient, listLineage };
}

function renderAt(path: string, flags: FeatureFlags, lineage: SiteTemplateLineageClient) {
  const sites = [OLD, NEW, PLAIN];
  return render(
    <MemoryRouter initialEntries={[path]}>
      <App
        flags={flags}
        siteDirectory={{ listSites: async () => ({ status: "loaded", sites }) }}
        siteDetail={{
          getSite: async (siteId) => {
            const found = sites.find((site) => site.site_id === siteId);
            return found === undefined
              ? { status: "not_found" }
              : { status: "loaded", site: found };
          },
        }}
        siteTemplateLineage={lineage}
      />
    </MemoryRouter>,
  );
}

function factValueElement(term: string): HTMLElement {
  const match = Array.from(document.querySelectorAll("dt")).find(
    (entry) => entry.textContent === term,
  );
  expect(match, `no fact named ${term}`).toBeDefined();
  return (match as HTMLElement).nextElementSibling as HTMLElement;
}

describe("the template lineage note on the operator site surfaces", () => {
  it("says a v1 site is behind the current v2 template on its Overview", async () => {
    const { client } = lineageClient([OLD, NEW, PLAIN]);
    renderAt(siteDetailHref("MG-OLD"), ENABLED, client);
    await settledScreen();

    const note = await screen.findByText(BEHIND_NOTE);
    const value = factValueElement("Created from template");
    expect(value.contains(note)).toBe(true);
    expect(value.textContent).toBe(`kobo-mini-grid-60kw v1${BEHIND_NOTE}`);
    // Plain provenance text: not a badge, a button or a link.
    expect(note.tagName).toBe("SPAN");
    expect(note.className).toBe("cell-secondary");
    expect(value.querySelector("button, a, [class*='badge']")).toBeNull();
  });

  it("says the same on the Foundation", async () => {
    const { client } = lineageClient([OLD, NEW, PLAIN]);
    renderAt(siteFoundationHref("MG-OLD"), ENABLED, client);
    await settledScreen();

    const note = await screen.findByText(BEHIND_NOTE);
    expect(factValueElement("Created from template").contains(note)).toBe(true);
  });

  it("shows no note for a site recorded at the current version", async () => {
    const { client, listLineage } = lineageClient([OLD, NEW, PLAIN]);
    renderAt(siteDetailHref("MG-NEW"), ENABLED, client);
    await settledScreen();
    await vi.waitFor(() => expect(listLineage).toHaveBeenCalled());
    await listLineage.mock.results[0]?.value;

    expect(factValueElement("Created from template").textContent).toBe(
      "kobo-mini-grid-60kw v2",
    );
    expect(document.querySelector("[data-template-lineage-note]")).toBeNull();
  });

  it("puts the note only in the behind site's row of the Sites index", async () => {
    const { client } = lineageClient([OLD, NEW, PLAIN]);
    renderAt("/sites", ENABLED, client);
    await settledScreen();

    const note = await screen.findByText(BEHIND_NOTE);
    expect(note.closest("tr")?.textContent).toContain("MG-OLD");
    expect(document.querySelectorAll("[data-template-lineage-note]")).toHaveLength(1);
  });

  it("does not read lineage and shows no note with the Lab gate closed", async () => {
    const { client, listLineage } = lineageClient([OLD, NEW, PLAIN]);
    renderAt(siteDetailHref("MG-OLD"), DISABLED, client);
    await settledScreen();

    expect(factValueElement("Created from template").textContent).toBe(
      "kobo-mini-grid-60kw v1",
    );
    expect(listLineage).not.toHaveBeenCalled();
    expect(document.querySelector("[data-template-lineage-note]")).toBeNull();
  });
});

describe("templateLineageNote", () => {
  const site = OLD as SiteSummary;
  const at = (
    state: string,
    current: number | null,
    template = site.template,
  ): SiteTemplateLineageReadModel => ({
    site_id: site.site_id,
    template,
    state,
    current_template_version: current,
  });

  it("names both versions when the record is behind", () => {
    expect(templateLineageNote(site, at("BEHIND", 2))).toBe(BEHIND_NOTE);
  });

  it("says a template no longer shipped is not current", () => {
    expect(templateLineageNote(site, at("NOT_SHIPPED", null))).toBe(
      "This template is no longer shipped",
    );
  });

  it("says nothing for a current record, a missing answer or a site with no template", () => {
    expect(templateLineageNote(site, at("CURRENT", 1))).toBeNull();
    expect(templateLineageNote(site, undefined)).toBeNull();
    expect(templateLineageNote(PLAIN as SiteSummary, at("NO_TEMPLATE", null, null))).toBeNull();
  });

  it("ignores an answer made about a different recorded lineage", () => {
    expect(
      templateLineageNote(
        site,
        at("BEHIND", 3, { template_id: "kobo-mini-grid-60kw", template_version: 2 }),
      ),
    ).toBeNull();
  });
});
