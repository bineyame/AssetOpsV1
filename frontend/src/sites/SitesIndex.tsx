import { useEffect, useState } from "react";

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
 * Rows are not links. A site is addressed by `site_id` at a route that does
 * not exist yet, and a destination must not appear before the route behind it
 * renders a truthful surface.
 */
export interface SitesIndexProps {
  directory: SiteDirectoryClient;
}

export function SitesIndex({ directory }: SitesIndexProps) {
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
      <section aria-labelledby="sites-unavailable-heading">
        <h2 id="sites-unavailable-heading">Sites unavailable</h2>
        <p>
          The site store could not be read, so no site can be listed. This is a
          statement about the store, not a statement that no site is
          configured.
        </p>
      </section>
    );
  }

  if (result.sites.length === 0) {
    return (
      <section aria-labelledby="sites-empty-heading">
        <h2 id="sites-empty-heading">No sites configured</h2>
        <p>
          No site has been configured, so there is nothing to list. This is the
          real state of this build rather than a placeholder: no row, no count,
          and no example site stands in for one.
        </p>
      </section>
    );
  }

  return (
    <section aria-labelledby="sites-list-heading">
      <h2 id="sites-list-heading">Configured sites</h2>
      <SiteTable sites={result.sites} />
    </section>
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
}

export function SiteTable({ sites }: SiteTableProps) {
  return (
    <table aria-labelledby="sites-list-heading">
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
          <SiteRow key={site.site_id} site={site} />
        ))}
      </tbody>
    </table>
  );
}

export interface SiteRowProps {
  site: SiteSummary;
}

export function SiteRow({ site }: SiteRowProps) {
  const view = deriveSiteView(site);

  return (
    <tr>
      <td>{view.siteId}</td>
      <td>{view.displayName}</td>
      <td>{view.siteType}</td>
      <td>{view.location}</td>
      <td>{view.lifecycleStatus}</td>
      <td>{view.sourceMode}</td>
      <td>{view.configurationOrigin}</td>
      <td>{view.templateProvenance}</td>
    </tr>
  );
}
