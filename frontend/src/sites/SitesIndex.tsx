import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";

import { Badge, DataTable, Panel } from "../ui";
import type { SiteDirectoryClient } from "./siteDirectoryClient";
import type { SiteListResult, SiteSummary } from "./siteReadModel";
import { deriveSiteView } from "./siteViewModel";
import {
  useSiteTemplateLineage,
  type SiteTemplateLineageClient,
  type SiteTemplateLineageReadModel,
} from "./siteTemplateLineage";
import { TemplateProvenanceText } from "./TemplateProvenanceText";

type LineageAnswers = ReadonlyMap<string, SiteTemplateLineageReadModel> | null;

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
 * - Site (name, identity and location), Type and Mode are the compact primary
 *   row (V-01a round 2, `D-2026-10-12-v01a-owner-visual-rulings`). Mode is
 *   provenance, never status.
 * - Lifecycle, configuration origin and template provenance are three
 *   independent facts, kept as three labelled entries in the row's "Setup
 *   details" disclosure. The canonical mockup puts `Simulated` and `Planned`
 *   in one `Status` column, which collapses provenance into status; that is a
 *   mockup error to correct rather than copy.
 * - Template provenance says which template the foundation was copied from. It
 *   is provenance, not identity: the site is addressed by its site ID and
 *   never by the template it came from.
 *
 * What it does not show: the mock's Assessment, Top issue, Evidence limit and
 * Last analysed columns. Each needs a selected-window, freshness or ranking
 * contract this directory does not have (S2 Evidence and S3 assessment are
 * per Site and window; S4-01 is Finding detail, not a ranked index). A
 * sentence beside the table says so instead of a column of dashes.
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
  /**
   * The gated template-lineage read, passed only when the composing shell's
   * gate is open. Absent, "Created from template" shows the recorded lineage
   * alone; present, it adds the advisory note when the record is behind.
   */
  templateLineage?: SiteTemplateLineageClient;
}

export function SitesIndex({
  directory,
  siteHref,
  templateLineage,
}: SitesIndexProps) {
  const [result, setResult] = useState<SiteListResult | null>(null);
  const lineage = useSiteTemplateLineage(templateLineage);

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
    <Panel
      heading="Site inventory"
      headingId="sites-list-heading"
      description="Mode is provenance. A row is a configured Site, never a simulation run."
      flush
    >
      <SiteFilters sites={result.sites} siteHref={siteHref} lineage={lineage} />
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
  lineage: LineageAnswers;
}

function SiteFilters({ sites, siteHref, lineage }: SiteFiltersProps) {
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
        <SiteTable sites={matching} siteHref={siteHref} lineage={lineage} />
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
  /** Lineage answers by `site_id`; see `SitesIndexProps.templateLineage`. */
  lineage?: LineageAnswers;
}

/**
 * The column set, in one place so a test can assert it and a reader can see it
 * whole.
 *
 * Compact on purpose (owner feedback, V-01a round 2): the three primary facts,
 * the setup disclosure holding lifecycle, origin and template as separate
 * labelled entries, and the row's View link. No analytical column: see
 * `DIRECTORY_ANALYSIS_ABSENT`.
 */
const COLUMNS = ["Site", "Type", "Mode", "Setup details", "Actions"] as const;

/** Why the mock's four analytical columns are absent from this directory. */
export const DIRECTORY_ANALYSIS_ABSENT =
  "Assessment, top issue, evidence limit and last analysis are not available in this directory. Open a Site for its selected-window evidence and assessments.";

export function SiteTable({ sites, siteHref, lineage = null }: SiteTableProps) {
  return (
    <>
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
            <SiteRow
              key={site.site_id}
              site={site}
              siteHref={siteHref}
              lineage={lineage?.get(site.site_id)}
            />
          ))}
        </tbody>
      </DataTable>
      <p className="panel__body panel__note" data-testid="sites-analysis-absent">
        {DIRECTORY_ANALYSIS_ABSENT}
      </p>
    </>
  );
}

export interface SiteRowProps {
  site: SiteSummary;
  siteHref: (siteId: string) => string;
  lineage?: SiteTemplateLineageReadModel;
}

export function SiteRow({ site, siteHref, lineage }: SiteRowProps) {
  const view = deriveSiteView(site);

  return (
    <tr>
      {/*
       * Name, identity and location in one cell, as canonical screen 1 draws
       * it. The link is built from `site_id` and nothing else: a site is
       * addressed by its identity, and the display name is what a reader
       * recognises rather than what resolves.
       */}
      <td>
        <Link to={siteHref(view.siteId)}>{view.displayName}</Link>
        <span className="cell-secondary">
          <span>{view.siteId}</span>
          {" · "}
          <span>{view.location}</span>
        </span>
      </td>
      <td>{view.siteType}</td>
      <td>
        <Badge tone="provenance">{view.sourceMode}</Badge>
      </td>
      {/*
       * Three vocabularies, three labelled entries, three tones, and never one
       * status pill. Template provenance is deliberately not a badge: a site
       * that came from no template renders `Not created from a template`, and a
       * badge around an absence dresses it as a state the site is in.
       */}
      <td>
        <details className="site-setup">
          <summary className="site-setup__summary">Setup details</summary>
          <dl className="site-setup__facts">
            <div>
              <dt>Lifecycle</dt>
              <dd>
                <Badge tone="lifecycle">{view.lifecycleStatus}</Badge>
              </dd>
            </div>
            <div>
              <dt>Configuration origin</dt>
              <dd>
                <Badge tone="origin">{view.configurationOrigin}</Badge>
              </dd>
            </div>
            <div>
              <dt>Created from template</dt>
              <dd>
                <TemplateProvenanceText
                  site={site}
                  provenance={view.templateProvenance}
                  lineage={lineage}
                />
              </dd>
            </div>
          </dl>
        </details>
      </td>
      <td>
        <Link to={siteHref(view.siteId)}>View</Link>
      </td>
    </tr>
  );
}
