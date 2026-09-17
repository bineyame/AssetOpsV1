import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { Badge, DataTable, Panel } from "../ui";
import type { SiteDirectoryClient } from "./siteDirectoryClient";
import type { SiteListResult, SiteSummary } from "./siteReadModel";
import { deriveSiteView } from "./siteViewModel";

/**
 * The Sites index, presented from the shared substrate.
 *
 * This component is the shared region. A shell composes it and may add around
 * it; it adds nothing to what is rendered here, and this component knows
 * nothing about which shell is rendering it. There is no `variant`, `mode`,
 * `shell`, or `isLab` prop, and no extension slot is declared yet, because
 * nothing fills one in this slice.
 *
 * What it shows, and why each column exists separately:
 *
 * - Configuration origin, source mode, and lifecycle status are three
 *   independent facts in three separate columns. The canonical mockup puts
 *   `Simulated` and `Planned` in one `Status` column, which collapses
 *   provenance into status; that is a mockup error to correct rather than
 *   copy.
 * - Template provenance says which template the foundation was copied from. It
 *   is provenance, not identity: the site is addressed by its site ID and
 *   never by the template it came from.
 *
 * What it deliberately does not show: any evidence-derived column. No last
 * data, no last analysed, no source health, no charts, no analytics, no
 * Replay, no findings. A configuration-only site has none of those, and a
 * column of dashes teaches a capability the product does not have yet. Each
 * arrives with the evidence that fills it.
 *
 * No edit, save, publish, rename, duplicate, delete, approve, diff, history,
 * or rollback control appears here, enabled or disabled. M1 has decided
 * configuration is fixed at creation, so a greyed-out control would make a
 * promise the product has declined to make.
 *
 * Each row opens that site. The row is the destination: a site is addressed by
 * `site_id`, so the site ID cell is the link and nothing else on the row is.
 * The address is supplied by whichever shell composes this, because where a
 * site page lives is a shell's fact about its own routes, not a fact about a
 * site. It is an address, not a mode: nothing here branches on it.
 */
export interface SitesIndexProps {
  directory: SiteDirectoryClient;
  /** The address of one site's page, built from its identity. */
  siteHref: (siteId: string) => string;
}

export function SitesIndex({ directory, siteHref }: SitesIndexProps) {
  const [result, setResult] = useState<SiteListResult | null>(null);

  useEffect(() => {
    let active = true;

    void directory.listSites().then((loaded) => {
      if (active) {
        setResult(loaded);
      }
    });

    return () => {
      active = false;
    };
  }, [directory]);

  if (result === null) {
    return <p>Loading configured sites.</p>;
  }

  if (result.status === "unavailable") {
    return (
      <Panel heading="Sites unavailable" headingId="sites-unavailable-heading">
        <p>
          The site store could not be read, so no site can be listed. This is a
          statement about the store, not a statement that no site is
          configured.
        </p>
      </Panel>
    );
  }

  if (result.sites.length === 0) {
    return (
      <Panel heading="No sites configured" headingId="sites-empty-heading">
        <p>
          No site has been configured, so there is nothing to list. This is the
          real state of this build rather than a placeholder: no row, no count,
          and no example site stands in for one.
        </p>
      </Panel>
    );
  }

  return (
    <Panel heading="Configured sites" headingId="sites-list-heading" flush>
      <SiteTable sites={result.sites} siteHref={siteHref} />
    </Panel>
  );
}

/**
 * The listing itself.
 *
 * Split out so the substrate has one table definition rather than one per
 * shell, and so the row rendering can be exercised directly over records.
 */
export interface SiteTableProps {
  sites: SiteSummary[];
  siteHref: (siteId: string) => string;
}

export function SiteTable({ sites, siteHref }: SiteTableProps) {
  return (
    <DataTable labelledBy="sites-list-heading">
      <thead>
        <tr>
          <th scope="col">Site ID</th>
          <th scope="col">Name</th>
          <th scope="col">Type</th>
          <th scope="col">Location</th>
          <th scope="col">Lifecycle status</th>
          <th scope="col">Mode</th>
          <th scope="col">Configuration origin</th>
          <th scope="col">Created from template</th>
        </tr>
      </thead>
      <tbody>
        {sites.map((site) => (
          <SiteRow key={site.site_id} site={site} siteHref={siteHref} />
        ))}
      </tbody>
    </DataTable>
  );
}

export interface SiteRowProps {
  site: SiteSummary;
  siteHref: (siteId: string) => string;
}

export function SiteRow({ site, siteHref }: SiteRowProps) {
  const view = deriveSiteView(site);

  return (
    <tr>
      <td>
        <Link to={siteHref(view.siteId)}>{view.siteId}</Link>
      </td>
      <td>{view.displayName}</td>
      <td>{view.siteType}</td>
      <td>{view.location}</td>
      {/*
       * Three vocabularies, three tones, never one status pill. Each of these
       * is derived from a field the record always carries, which is why each
       * can be a badge at all.
       *
       * Template provenance below is deliberately not one: a site that came
       * from no template renders `Not created from a template`, and that is an
       * absence rather than a value. A badge around it would dress the absence
       * as a state the site is in.
       */}
      <td>
        <Badge tone="lifecycle">{view.lifecycleStatus}</Badge>
      </td>
      <td>
        <Badge tone="provenance">{view.sourceMode}</Badge>
      </td>
      <td>
        <Badge tone="origin">{view.configurationOrigin}</Badge>
      </td>
      <td>{view.templateProvenance}</td>
    </tr>
  );
}
