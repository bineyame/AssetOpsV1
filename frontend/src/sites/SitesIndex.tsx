import { useEffect, useMemo, useState } from "react";
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
 * - `Last analysed` is evidence-derived and renders `--` for every site,
 *   because no evidence has been analysed in any window. Until T011 this
 *   column was absent on the grounds that a column of dashes teaches a
 *   capability the product lacks. v6.9 renders exactly that dash for a site
 *   with no data in the window, so the column states a fact about this build
 *   rather than promising one; what it replaces, the mockup's `Last Data`
 *   timestamps, would have been the fabrication.
 *
 * What it still does not show: canonical assessment, top issue, evidence
 * readiness, source health, charts, analytics, Replay, findings. Each needs an
 * accepted-evidence model that does not exist, and each arrives with the
 * evidence that fills it.
 *
 * No edit, save, publish, rename, duplicate, delete, approve, diff, history,
 * or rollback control appears here, enabled or disabled, and the Actions
 * column holds `View` and no overflow menu. M1 has decided configuration is
 * fixed at creation, so a greyed-out control would make a promise the product
 * has declined to make, and an overflow menu would open onto nothing.
 *
 * Each row opens that site, from two places in the row: the name and the
 * `View` action. Both resolve through `site_id` and nothing else, so a site is
 * still addressed by its identity while a reader recognises it by its name.
 * The address is supplied by whichever shell composes this, because where a
 * site page lives is a shell's fact about its own routes, not a fact about a
 * site. It is an address, not a mode: nothing here branches on it.
 */
/** The "no filter" value. Not a site type, mode or lifecycle state, so it
 *  cannot collide with one a record carries. */
const ANY = "__any__";

/** The distinct values present, in order, for building a filter's options. */
function distinct(values: string[]): string[] {
  return Array.from(new Set(values)).sort();
}

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
      <SiteFilters sites={result.sites} siteHref={siteHref} />
    </Panel>
  );
}

/**
 * Search and the three filters, over the sites actually in the store.
 *
 * Every filter's options are derived from the records present rather than from
 * the M1 schema's permitted values. That is the same rule the Lab's template
 * catalog follows and it matters more here: offering `DECOMMISSIONED` when no
 * site is decommissioned teaches a fleet this build does not have, and a
 * reader cannot tell an empty filter result from a state the product never
 * reaches.
 *
 * There is no sort, no saved view and no bulk selection. Each is a real
 * capability rather than chrome, and none of them exists.
 */
interface SiteFiltersProps {
  sites: SiteSummary[];
  siteHref: (siteId: string) => string;
}

function SiteFilters({ sites, siteHref }: SiteFiltersProps) {
  const [search, setSearch] = useState("");
  const [siteType, setSiteType] = useState(ANY);
  const [mode, setMode] = useState(ANY);
  const [lifecycle, setLifecycle] = useState(ANY);

  const views = useMemo(() => sites.map(deriveSiteView), [sites]);

  const options = useMemo(
    () => ({
      siteType: distinct(views.map((view) => view.siteType)),
      mode: distinct(views.map((view) => view.sourceMode)),
      lifecycle: distinct(views.map((view) => view.lifecycleStatus)),
    }),
    [views],
  );

  const matching = useMemo(() => {
    const needle = search.trim().toLowerCase();
    return sites.filter((site) => {
      const view = deriveSiteView(site);
      if (siteType !== ANY && view.siteType !== siteType) return false;
      if (mode !== ANY && view.sourceMode !== mode) return false;
      if (lifecycle !== ANY && view.lifecycleStatus !== lifecycle) return false;
      if (needle === "") return true;
      return (
        view.displayName.toLowerCase().includes(needle) ||
        view.siteId.toLowerCase().includes(needle)
      );
    });
  }, [sites, search, siteType, mode, lifecycle]);

  return (
    <>
      <div className="toolbar">
        <p className="toolbar__field toolbar__field--grow">
          <label className="field-label" htmlFor="sites-search">
            Search sites
          </label>
          <input
            className="control"
            id="sites-search"
            type="search"
            value={search}
            placeholder="Name or site ID"
            onChange={(event) => setSearch(event.target.value)}
          />
        </p>

        <SiteFilter
          id="sites-type"
          label="Type"
          anyLabel="All types"
          value={siteType}
          options={options.siteType}
          onChange={setSiteType}
        />
        <SiteFilter
          id="sites-mode"
          label="Mode"
          anyLabel="All modes"
          value={mode}
          options={options.mode}
          onChange={setMode}
        />
        <SiteFilter
          id="sites-lifecycle"
          label="Lifecycle"
          anyLabel="All lifecycle states"
          value={lifecycle}
          options={options.lifecycle}
          onChange={setLifecycle}
        />
      </div>

      {matching.length === 0 ? (
        <p className="panel__body">
          No configured site matches this search and these filters. This is a
          statement about the filters, not about the store:{" "}
          {sites.length === 1
            ? "one site is configured"
            : `${sites.length} sites are configured`}
          .
        </p>
      ) : (
        <SiteTable sites={matching} siteHref={siteHref} />
      )}
    </>
  );
}

interface SiteFilterProps {
  id: string;
  label: string;
  anyLabel: string;
  value: string;
  options: string[];
  onChange: (value: string) => void;
}

function SiteFilter({
  id,
  label,
  anyLabel,
  value,
  options,
  onChange,
}: SiteFilterProps) {
  return (
    <p className="toolbar__field">
      <label className="field-label" htmlFor={id}>
        {label}
      </label>
      <select
        className="control"
        id={id}
        value={value}
        onChange={(event) => onChange(event.target.value)}
      >
        <option value={ANY}>{anyLabel}</option>
        {options.map((option) => (
          <option key={option} value={option}>
            {option}
          </option>
        ))}
      </select>
    </p>
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

/**
 * The column set, in one place so a test can assert it and a reader can see it
 * whole.
 *
 * Nine columns, which is two more than the settled Sites index inventory in
 * `.ai/FEATURE_MAP.md` lists. The inventory names seven and omits configuration
 * origin and template provenance entirely; the T006 user-review checkpoint
 * accepted "the eight Sites index columns with mode, lifecycle, configuration
 * origin, and template provenance as four separate columns". Where a user
 * review has already settled a surface, that decision settles it, so the two
 * the checkpoint named are kept.
 *
 * What is absent, and why, is as much the point as what is here. Canonical
 * assessment, top issue and evidence readiness are v6.9 columns with no source
 * in M1: no accepted evidence, no assessment derivation, no finding model. The
 * mockup's `Last Data` timestamps are evidence too, which is why the column
 * that replaces it renders `--` instead.
 */
const COLUMNS = [
  "Name",
  "Type",
  "Location",
  "Mode",
  "Lifecycle",
  "Configuration origin",
  "Created from template",
  "Last analysed",
  "Actions",
] as const;

export function SiteTable({ sites, siteHref }: SiteTableProps) {
  return (
    <DataTable labelledBy="sites-list-heading">
      <thead>
        <tr>
          {COLUMNS.map((column) => (
            <th scope="col" key={column}>
              {column}
            </th>
          ))}
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
      {/*
       * Name and identity in one cell, as canonical screen 1 draws it. The
       * link is still built from `site_id` and from nothing else: a site is
       * addressed by its identity, and the display name is what a reader
       * recognises rather than what resolves.
       */}
      <td>
        <Link to={siteHref(view.siteId)}>{view.displayName}</Link>
        <span className="cell-secondary">{view.siteId}</span>
      </td>
      <td>{view.siteType}</td>
      <td>{view.location}</td>
      {/*
       * Three vocabularies, three columns, three tones, and never one status
       * pill. The canonical mockup puts `Simulated` and `Planned` in a single
       * `Status` column; that collapses provenance into status, which v6.9
       * forbids three separate times, and correcting it is the most
       * consequential thing this screen does. A reader who learns
       * `Status: Simulated` here carries that model into every screen after it.
       *
       * Each of the three is a badge because each is derived from a field the
       * record always carries. Template provenance below is deliberately not:
       * a site that came from no template renders `Not created from a
       * template`, and a badge around an absence dresses it as a state the
       * site is in.
       */}
      <td>
        <Badge tone="provenance">{view.sourceMode}</Badge>
      </td>
      <td>
        <Badge tone="lifecycle">{view.lifecycleStatus}</Badge>
      </td>
      <td>
        <Badge tone="origin">{view.configurationOrigin}</Badge>
      </td>
      <td>{view.templateProvenance}</td>
      {/*
       * Evidence-derived, and there is no evidence. `--` is v6.9's rendering
       * for a site with no data in the window, not a placeholder for a
       * timestamp arriving later.
       */}
      <td className="muted">{view.lastAnalysed}</td>
      <td>
        <Link to={siteHref(view.siteId)}>View</Link>
      </td>
    </tr>
  );
}
