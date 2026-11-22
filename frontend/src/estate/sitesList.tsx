/**
 * IA-P P4b (spec §5.2 "sites", §6 P4b; handshake R3, R6; pre-flight Q1 to Q8): the Sites list on the one list component.
 * The rows are E1's (`GET /api/portfolio/sites`), in E1's order, for the Overview's whole months in the range; the
 * "Waiting for a choice" cell is E0's `waiting_by_site` from the estate portfolio read (the 31-day window, P0, said in
 * the column's heading). Every figure and sentence is served; the browser sums nothing and re-formats nothing.
 * The same def draws `/sites` and the Portfolio's Outcomes L2.
 */
import { useEffect, useMemo, useState, type ReactNode } from "react";
import { useSearchParams } from "react-router-dom";

import { PageHeader } from "../ui";
import { HomeList, type HomeListDef, type HomeListTile } from "../ui/HomeList";
import { rangePartWords } from "../ui/RangePartNote";
import { linkBound, readSharedRange } from "../ui/sharedRange";
import { siteDetailHref } from "../shell/operatorSiteRoutes";
import type { SiteDirectoryClient } from "../sites/siteDirectoryClient";
import type { SiteSummary } from "../sites/siteReadModel";
import { deriveSiteView } from "../sites/siteViewModel";
import { DD_COPY } from "./DeepDiveMonth";
import { createEstateClient, type EstateClient } from "./estateClient";
import { useEstateRead } from "./estateReadCache";
import { queryFromParams } from "./estateShared";
import { createPortfolioSitesClient, type PortfolioSiteRow, type PortfolioSites, type PortfolioSitesClient, type PortfolioSitesResult } from "./portfolioSitesClient";
import { DOMAIN_WORD } from "./portfolioWords";

export const SITES_LIST_PATH = "/sites";
const NA = "Not available yet";
/** spec §6 P4b (R6, MD-IAP-13): the gap tile's line when the view is not every Site. */
export const FOR_EVERY_SITE_ONLY = "For every Site only";
export const SITES_LOADING = "Loading Sites…";

/**
 * A row of the list: an E1 row, or a directory Site E1 does not hold (D-IAP.35 Q1: its Group from `site_type`, its waiting
 * count from E0, every other cell "Not available yet").
 */
export interface SiteItem {
  code: string;
  name: string;
  row: PortfolioSiteRow | null;
  /** The Group word: E1's, or `DOMAIN_WORD` of the directory `site_type` (null when unmapped). */
  group: string | null;
  /** E0's count as text: the count, 0 for a Site with no member, or "Not available yet" without E0. */
  waiting: string;
}

/** The domain of an E1 group word: `DOMAIN_WORD` inverted (P.8 test 2 pins their equality; pre-flight Q4). */
const DOMAIN_OF_WORD: Readonly<Record<string, string>> = Object.fromEntries(Object.entries(DOMAIN_WORD).map(([domain, word]) => [word, domain]));

export function siteItems(
  body: PortfolioSites,
  waitingBySite: Record<string, number> | null | undefined,
  directory: readonly SiteSummary[] = [],
): SiteItem[] {
  const waiting = (code: string) => (waitingBySite === null || waitingBySite === undefined ? NA : String(waitingBySite[code] ?? 0));
  const items: SiteItem[] = body.rows.map((row) => ({ code: row.site_code, name: row.site, row, group: row.group, waiting: waiting(row.site_code) }));
  // Site identity is case-blind (`site_id_key`): a directory Site already in E1 is not listed twice.
  const held = new Set(body.rows.map((r) => r.site_code.toLowerCase()));
  for (const site of directory) {
    if (held.has(site.site_id.toLowerCase())) continue;
    const group = (DOMAIN_WORD as Record<string, string>)[site.site_type] ?? null;
    items.push({ code: site.site_id, name: site.display_name, row: null, group, waiting: waiting(site.site_id) });
  }
  return items;
}

function cell(text: string, small: string | null | undefined): ReactNode {
  return (
    <>
      {text}
      {small ? <small>{small}</small> : null}
    </>
  );
}

/**
 * D-IAP.44: the lifecycle word of each directory Site that is not Active (the `deriveSiteView` word), by its code in
 * lower case (Site identity is case-blind). The join is by `site_code`; a refused directory read gives none.
 */
export function lifecycleWords(directory: readonly SiteSummary[]): Record<string, string> {
  const out: Record<string, string> = {};
  for (const site of directory) {
    if (site.lifecycle_status === "ACTIVE") continue;
    out[site.site_id.toLowerCase()] = deriveSiteView(site).lifecycleStatus;
  }
  return out;
}

/** The directory read the Sites list makes; only a loaded read lists Sites (a refused one leaves the rows alone). */
export function useDirectorySites(directory: SiteDirectoryClient | undefined): readonly SiteSummary[] {
  const [listed, setListed] = useState<readonly SiteSummary[]>([]);
  useEffect(() => {
    if (directory === undefined) return;
    let live = true;
    // A refused directory read leaves E1's rows alone (pre-flight Q1).
    void directory.listSites().then((r) => {
      if (live && r.status === "loaded") setListed(r.sites);
    });
    return () => {
      live = false;
    };
  }, [directory]);
  return listed;
}

/** A compared row carries its figure word (P.8: a row not compared has `gap_word` null; pre-flight Q3). */
const compared = (i: SiteItem) => i.row !== null && i.row.gap_word !== null;

export function sitesDef(
  body: PortfolioSites,
  waitingNote: string | null = null,
  lifecycle: Readonly<Record<string, string>> = {},
): HomeListDef<SiteItem> {
  const none = body.mode === "none";
  return {
    key: "sites",
    path: SITES_LIST_PATH,
    plural: "Sites",
    tileLabel: "Sites",
    rowKey: (i) => i.code,
    title: (i) => i.name,
    // D-IAP.44: a Site that is not Active carries its lifecycle word as the title's small.
    small: (i) => {
      const word = lifecycle[i.code.toLowerCase()];
      return word === undefined ? null : <small data-lifecycle>{word}</small>;
    },
    target: (i) => siteDetailHref(i.code),
    firstColumn: "Site",
    columns: [
      { label: "Group", cell: (i) => i.group ?? NA },
      { label: "Contribution", cell: (i) => (i.row === null ? NA : cell(i.row.contribution, i.row.months_text)) },
      { label: "Gap to target", cell: (i) => (i.row === null ? NA : cell(i.row.gap, i.row.gap_word)) },
      { label: "Largest driver against target", cell: (i) => (i.row === null ? NA : cell(i.row.driver, i.row.driver_heading)) },
      { label: "Waiting for a choice", cell: (i) => i.waiting, note: waitingNote },
    ],
    // Mode none: no Site is compared, so the target facet is not offered (spec §6 P4b).
    facets: none
      ? []
      : [
          {
            key: "target",
            label: "Target",
            options: [
              { value: "below", word: "Below target" },
              { value: "on", word: "On or above target" },
            ],
            all: "Above and below target",
            of: (i) => (!compared(i) ? null : i.row!.below ? "below" : "on"),
          },
        ],
    sorts: [
      { key: "gap", label: "Gap to target" },
      { key: "name", label: "Name", compare: (a, b) => a.name.localeCompare(b.name) },
    ],
    text: (i) => [i.name, i.group, i.row?.contribution, i.row?.gap, i.row?.driver].filter(Boolean).join(" "),
    site: (i) => i.code,
    domain: (i) => (i.group === null ? null : DOMAIN_OF_WORD[i.group] ?? null),
    scopeWord: (s) => (s.startsWith("group:") ? (DOMAIN_WORD as Record<string, string>)[s.slice(6)] ?? s : s.slice(5)),
    tiles: (_m, rows, whole): HomeListTile[] => [
      { label: "Below target", role: "part", value: none ? NA : rows.filter((i) => i.row?.below === true).length },
      // R6 (MD-IAP-13): the server's total only for every Site, unfiltered; never a browser sum.
      whole && body.total !== null
        ? { label: "Gap to target", role: "total", value: body.total.gap, ...(body.without_target.text ? { note: body.without_target.text } : {}) }
        : { label: "Gap to target", role: "total", value: NA, ...(none ? {} : { note: FOR_EVERY_SITE_ONLY }) },
    ],
    // D-IAP.35 Q5: two strings, singular and plural.
    more: (hidden) => (hidden.length === 1 ? "Not shown: 1 Site." : `Not shown: ${hidden.length} Sites.`),
    none: "No Sites in this scope.",
  };
}

/** E1 for the address's whole range (a whole-range page, P0), read again on "Try again". */
export function usePortfolioSites(client?: PortfolioSitesClient): { result: PortfolioSitesResult | null; retry(): void } {
  const reads = useMemo(() => client ?? createPortfolioSitesClient(), [client]);
  const [params] = useSearchParams();
  const range = readSharedRange(params);
  const from = range.status === "set" ? range.from : (linkBound(params, "from") ?? "");
  const to = range.status === "set" ? range.to : (linkBound(params, "to") ?? "");
  const [attempt, setAttempt] = useState(0);
  const key = `${from}|${to}|${attempt}`;
  const [read, setRead] = useState<{ key: string; result: PortfolioSitesResult } | null>(null);
  useEffect(() => {
    let live = true;
    void reads.fetchSites(from, to).then((result) => {
      if (live) setRead({ key, result });
    });
    return () => {
      live = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [reads, key]);
  return { result: read?.key === key ? read.result : null, retry: () => setAttempt((n) => n + 1) };
}

/** The waiting column's note: the estate read's 31-day window, when it is not the range (P0). */
function useWindowNote(): string | null {
  const [params] = useSearchParams();
  const range = readSharedRange(params);
  return rangePartWords(range.status === "set" ? range : null);
}

/** E0 on `/sites`: the estate portfolio read through the shared cache (its 31-day window, P0). */
function useWaiting(estate?: EstateClient): { bySite: Record<string, number> | null | undefined; note: string | null } {
  const reads = useMemo(() => estate ?? createEstateClient(), [estate]);
  const [params] = useSearchParams();
  const read = useEstateRead(reads, "portfolio", queryFromParams(params));
  const bySite = read?.status === "loaded" ? read.value.first.summary.waiting_by_site : null;
  return { bySite, note: useWindowNote() };
}

/** A refused E1, as the Overview shows a refused E2 (pre-flight Q8). */
export function SitesRefusal({ result, retry }: { result: Extract<PortfolioSitesResult, { status: "refused" }>; retry(): void }) {
  if (result.httpStatus === 401) return <p className="dd-state">{DD_COPY.signIn}</p>;
  return (
    <div className="dd-state">
      <p>{result.text ?? DD_COPY.unreadable}</p>
      {result.httpStatus !== 422 ? (
        <button type="button" className="dd-button" onClick={retry}>
          {DD_COPY.tryAgain}
        </button>
      ) : null}
    </div>
  );
}

export function SitesNotes({ notes }: { notes: readonly string[] }) {
  if (notes.length === 0) return null;
  return (
    <div className="sites-notes" data-sites-notes>
      {notes.map((n) => (
        <p key={n} role="note">
          {n}
        </p>
      ))}
    </div>
  );
}

/** The `/sites` page: the list under the page header, E1's notes under it (spec §5.3, §6 P4b). */
export function SitesListPage({
  sites,
  estate,
  directory,
  actions,
}: {
  sites?: PortfolioSitesClient;
  estate?: EstateClient;
  directory: SiteDirectoryClient;
  actions?: ReactNode;
}) {
  const { result, retry } = usePortfolioSites(sites);
  const waiting = useWaiting(estate);
  const listed = useDirectorySites(directory);
  const body = result?.status === "loaded" ? result.body : null;
  const items = useMemo(() => (body === null ? [] : siteItems(body, waiting.bySite, listed)), [body, waiting.bySite, listed]);
  const lifecycle = useMemo(() => lifecycleWords(listed), [listed]);
  const def = useMemo(() => (body === null ? null : sitesDef(body, waiting.note, lifecycle)), [body, waiting.note, lifecycle]);
  return (
    <div className="estate-page" data-estate-root="sites">
      <PageHeader title="Sites" headingId="sites-heading" actions={actions} />
      {body !== null ? <SitesNotes notes={body.notes} /> : null}
      {result === null ? (
        <p className="estate-loading">{SITES_LOADING}</p>
      ) : result.status === "refused" ? (
        <SitesRefusal result={result} retry={retry} />
      ) : (
        <HomeList def={def!} items={items} options={{ labelledBy: "sites-heading" }} />
      )}
    </div>
  );
}

/**
 * The Portfolio's Outcomes L1 and L2 (spec §6 P4b): E1's headline (or, in mode `none`, its notes), then the Sites rows
 * on the same def with no tools and no tiles, "Show all" to `/sites?show=all` with the range.
 */
export function OutcomesSites({
  sites,
  waitingBySite,
  directory,
}: {
  sites?: PortfolioSitesClient;
  /** D-IAP.44: the directory read, for the lifecycle word only (Outcomes L2 lists E1's rows alone). */
  directory?: SiteDirectoryClient;
  /** E0 from the Outcomes tab's own estate portfolio read (the same query; no second read). */
  waitingBySite: Record<string, number> | null | undefined;
}) {
  const { result, retry } = usePortfolioSites(sites);
  const note = useWindowNote();
  const body = result?.status === "loaded" ? result.body : null;
  const listed = useDirectorySites(directory);
  const items = useMemo(() => (body === null ? [] : siteItems(body, waitingBySite)), [body, waitingBySite]);
  const lifecycle = useMemo(() => lifecycleWords(listed), [listed]);
  const def = useMemo(() => (body === null ? null : sitesDef(body, note, lifecycle)), [body, note, lifecycle]);
  if (result === null) return <p className="estate-loading">{SITES_LOADING}</p>;
  if (result.status === "refused") return <SitesRefusal result={result} retry={retry} />;
  return (
    <>
      <div data-level="L1" className="pf-outcomes-lead">
        {body!.headline !== null ? (
          <p className="pf-outcomes-headline" data-sites-headline>
            {body!.headline.text}
            {body!.headline.evidence.map((w) => (
              <small key={w}>{w}</small>
            ))}
          </p>
        ) : (
          <SitesNotes notes={body!.notes} />
        )}
        {body!.headline !== null && body!.without_target.text ? <p className="pf-outcomes-line">{body!.without_target.text}</p> : null}
      </div>
      <div data-level="L2">
        <HomeList def={def!} items={items} options={{ tools: false, tiles: false }} />
      </div>
    </>
  );
}
