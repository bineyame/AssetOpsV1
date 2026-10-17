import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";

import {
  Badge,
  DataTable,
  ExactReferences,
  MetricCard,
  MetricCards,
  MissingClaim,
  Panel,
  ProductStatus,
  readResultWords,
  type ProductWords,
} from "../ui";
import type { SiteDirectoryClient } from "./siteDirectoryClient";
import type { SiteListResult, SiteSummary } from "./siteReadModel";
import { deriveSiteView } from "./siteViewModel";
import {
  useSiteTemplateLineage,
  type SiteTemplateLineageClient,
  type SiteTemplateLineageReadModel,
} from "./siteTemplateLineage";
import { TemplateProvenanceText } from "./TemplateProvenanceText";
import "./w1ux02-site.css";

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

  // W1-F1 (D-2026-10-17-mockup-layout-spec): the v69 `sites` layout in every
  // state: type chips, three metric cards, then "Site inventory" and "In setup".
  // An unreadable or empty directory keeps both panels, with the state inside.
  if (result.status === "unavailable") {
    return (
      <>
        <SitesMetrics count={null} />
        <Panel heading="Site inventory" headingId="sites-list-heading" description={INVENTORY_DESCRIPTION}>
          <div data-sites-state="unavailable">
            <p>
              <strong>Sites unavailable</strong>
            </p>
            <ProductStatus words={readResultWords("unavailable")} scope={SITES_SCOPE} asOf={null} />
            <p>
              The site store could not be read, so no site can be listed. This is a statement about the store, not a
              statement that no site is configured.
            </p>
          </div>
        </Panel>
        <SetupPanel sites={null} />
      </>
    );
  }

  if (result.sites.length === 0) {
    return (
      <>
        <SitesMetrics count={0} />
        <Panel heading="Site inventory" headingId="sites-list-heading" description={INVENTORY_DESCRIPTION}>
          <div data-sites-state="empty">
            <p>
              <strong>No sites configured</strong>
            </p>
            <ProductStatus words={NO_SITES_WORDS} scope={SITES_SCOPE} asOf={null} />
            <p>
              No site has been configured, so there is nothing to list. This is the real state of this build rather
              than a placeholder: no row and no example site stands in for one.
            </p>
          </div>
        </Panel>
        <SetupPanel sites={[]} />
      </>
    );
  }

  return <SitesDirectory sites={result.sites} siteHref={siteHref} lineage={lineage} />;
}

/** The v69 `sites` question. The directory answers it by identity only. */
export const SITES_QUESTION = "Which site should I open?";
const SITES_SCOPE = "All registered sites";
const INVENTORY_DESCRIPTION =
  "Mode says where a site's readings come from. It is not a measure of how the site is operating.";

/** A loaded directory with no site: a domain state the shared map does not own. */
const NO_SITES_WORDS: ProductWords = {
  label: "No sites registered",
  sentence: "The site list was read and holds no site. Nothing is listed in its place.",
  tone: "neutral",
  code: null,
  unrecognised: false,
};

/**
 * A loaded directory: registered identity only. It reads no condition, so it
 * names no site as needing attention and ranks none (W1-UX-02).
 */
export const SITES_LISTED_WORDS: ProductWords = {
  label: "Registered sites, not ranked",
  sentence:
    "This list shows which sites are registered. It does not judge how any site is operating, and it holds no assessment or evidence limit for any site.",
  next: "Open a site to see its selected day: what was assessed, what the readings can support and any Finding.",
  tone: "neutral",
  code: null,
  unrecognised: false,
};

/** Why the mock's attention and evidence-limit counts are absent from this list. */
export const SITES_COUNT_NOT_AVAILABLE =
  "Not available from this list: there is no common window or aggregation contract for this count.";
/** Why the mock setup columns are absent (worded without "history": the index offers no history control). */
export const SITES_SETUP_PROGRESS_NOT_AVAILABLE = "Setup progress not available: no read returns who set up a site, its next step or when it was registered.";

/**
 * The mock's three metric cards. Only the registered count is supported, and
 * only from a read that succeeded (`count` null = the store was not read).
 */
function SitesMetrics({ count }: { count: number | null }) {
  return (
    <MetricCards columns={3} label="Site counts" data={{ "data-sites-metrics": "" }}>
      <MetricCard
        label="Sites"
        value={count === null ? "Unavailable" : count === 0 ? "None" : String(count)}
        word={count === null || count === 0}
        tone={count === null ? "muted" : undefined}
        note={
          count === null
            ? "The site list could not be read."
            : count === 0
              ? "The site list was read and holds no site."
              : "Registered site identities"
        }
        data={{ "data-site-metric": "count" }}
      />
      <MetricCard
        word
        tone="muted"
        label="Needs attention"
        value="Not available"
        note={
          <MissingClaim gapId="G-sites-attention-counts" placement="sites.metrics.needs-attention">
            {SITES_COUNT_NOT_AVAILABLE}
          </MissingClaim>
        }
        data={{ "data-site-metric": "needs-attention" }}
      />
      <MetricCard
        word
        tone="muted"
        label="Evidence limited"
        value="Not available"
        note={
          <MissingClaim gapId="G-sites-attention-counts" placement="sites.metrics.evidence-limited">
            {SITES_COUNT_NOT_AVAILABLE}
          </MissingClaim>
        }
        data={{ "data-site-metric": "evidence-limited" }}
      />
    </MetricCards>
  );
}

/**
 * The mock's "In setup" panel. The directory returns each site's recorded
 * lifecycle, so a site whose lifecycle is not Active is listed with that state;
 * who set it up, its next step and when are setup progress, which no read
 * returns. `sites` null = the store was not read, so nothing is listed.
 */
function SetupPanel({ sites }: { sites: SiteSummary[] | null }) {
  const views = (sites ?? []).map(deriveSiteView).filter((view) => view.lifecycleStatus !== "Active");
  return (
    <Panel heading="In setup" headingId="sites-setup-heading" description="Sites whose recorded lifecycle is not yet Active">
      {sites === null ? (
        <p data-sites-setup="unavailable">The site list could not be read, so no site in setup can be listed.</p>
      ) : views.length === 0 ? (
        <p data-sites-setup="none">
          {sites.length === 0 ? "No site is registered." : "Every listed site's recorded lifecycle is Active."}
        </p>
      ) : (
        <DataTable labelledBy="sites-setup-heading">
          <thead>
            <tr>
              <th scope="col">Site</th>
              <th scope="col">Type</th>
              <th scope="col">Lifecycle</th>
            </tr>
          </thead>
          <tbody>
            {views.map((view) => (
              <tr key={view.siteId} data-sites-setup-row={view.siteId}>
                <td>
                  <strong>{view.displayName}</strong>
                  <span className="cell-secondary">{view.siteId}</span>
                </td>
                <td>{view.siteType}</td>
                <td>
                  <Badge tone="lifecycle">{view.lifecycleStatus}</Badge>
                </td>
              </tr>
            ))}
          </tbody>
        </DataTable>
      )}
      <MissingClaim as="p" className="not-available-yet" gapId="G-sites-setup-progress" placement="sites.setup.progress">
        {SITES_SETUP_PROGRESS_NOT_AVAILABLE}
      </MissingClaim>
    </Panel>
  );
}

/**
 * A loaded directory: the type chips and metric cards, then the inventory
 * (state line, exact references, filters, table) and the setup panel. The
 * registered count and each site's type and data source come straight off the
 * records; nothing about operation, evidence or attention is inferred. The list
 * read carries no read instant, so the bound says the time is not recorded.
 */
function SitesDirectory({ sites, siteHref, lineage }: SiteFiltersProps) {
  const [siteType, setSiteType] = useState(ANY);
  const types = useMemo(() => distinct(sites.map((site) => deriveSiteView(site).siteType)), [sites]);
  return (
    <>
      <div className="v69-chips" role="group" aria-label="Site type" data-filter-group="sites">
        {[ANY, ...types].map((type) => (
          <button
            type="button"
            className="v69-chip"
            key={type}
            aria-pressed={siteType === type}
            data-site-filter={type === ANY ? "all" : type}
            onClick={() => setSiteType(type)}
          >
            {type === ANY ? "All sites" : type}
          </button>
        ))}
      </div>
      <SitesMetrics count={sites.length} />
      <Panel heading="Site inventory" headingId="sites-list-heading" description={INVENTORY_DESCRIPTION} flush>
        <div className="panel__body" data-sites-state="listed">
          <ProductStatus words={SITES_LISTED_WORDS} scope={SITES_SCOPE} asOf={null} />
          <ExactReferences
            name="sites-directory"
            references={sites.flatMap((site) => [
              { label: `${site.display_name}: site reference`, value: site.site_id },
              { label: `${site.display_name}: registration store`, value: site.configuration_store ?? null },
            ])}
          />
        </div>
        <SiteFilters sites={sites} siteHref={siteHref} lineage={lineage} siteType={siteType} />
      </Panel>
      <SetupPanel sites={sites} />
    </>
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

/** W1-F1: the site type is chosen with the v69 chip group above the cards. */
function SiteFilters({ sites, siteHref, lineage, siteType }: SiteFiltersProps & { siteType: string }) {
  const [search, setSearch] = useState("");
  const [mode, setMode] = useState(ANY);
  const [lifecycle, setLifecycle] = useState(ANY);

  const views = useMemo(() => sites.map(deriveSiteView), [sites]);

  const options = useMemo(
    () => ({
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
const COLUMNS = ["Site", "Type", "Mode", "Operating view", "Setup details", "Actions"] as const;

/** Why the mock's four analytical columns are absent from this directory. */
export const DIRECTORY_ANALYSIS_ABSENT =
  "Assessment, top issue, evidence limit and last analysis are not available in this directory. Open a Site for its selected-window evidence and assessments.";

/**
 * V-01a round 3 addendum: one grouped cell per Site names what is missing,
 * instead of four identical placeholder columns or an invented value.
 */
export const OPERATING_VIEW_NOT_AVAILABLE = "Not available yet";
export const OPERATING_VIEW_PARTS = "Assessment · top issue · evidence limit · last analysed";

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
        <MissingClaim gapId="G-sites-operating-view" placement="sites.inventory.analysis-note">
          {DIRECTORY_ANALYSIS_ABSENT}
        </MissingClaim>
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
      <td data-operating-view="not-available">
        <MissingClaim gapId="G-sites-operating-view" placement="sites.inventory.operating-view">
          <span className="not-available-yet">{OPERATING_VIEW_NOT_AVAILABLE}</span>
          <span className="cell-secondary">{OPERATING_VIEW_PARTS}</span>
        </MissingClaim>
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
