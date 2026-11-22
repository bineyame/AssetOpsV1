/**
 * IA-P P2 (spec §5.2, D-IAP.6): the three estate lists on the home-list component: Decisions (one row per placed
 * Finding, D-IAP.3), Findings and Actions. Each def maps one read's rows to the component's model; every word is a
 * reused function's or the spec's. The page frames read every page through the shared cache (`estateReadCache.tsx`).
 */
import { useMemo } from "react";
import { useSearchParams } from "react-router-dom";

import { PageHeader } from "../ui";
import { HomeList, type HomeListDef } from "../ui/HomeList";
import { formatDay } from "../ui/time";
import { RangePartNote } from "../ui/RangePartNote";
import { readSharedRange } from "../ui/sharedRange";
import { linkFor } from "../shell/operatorSiteRoutes";
import {
  EstateCutoffLine,
  EstateRefusal,
  estateHref,
  queryFromParams,
} from "./estateShared";
import { createEstateClient, type EstateActionRow, type EstateClient, type EstateCoverageSite, type EstateFindingRow, type EstatePortfolioBody, type EstatePortfolioRow } from "./estateClient";
import { TRUNCATED_LINE, useEstateRead } from "./estateReadCache";
import { barBody, consequenceFirst } from "./EstatePortfolio";
import { DECISIONS_PATH, DOMAIN_WORD, PLACEMENT_GROUP_LABEL } from "./portfolioWords";
import { LIFECYCLE_WORDS, findingLinkLive } from "./findingIndex";
import { actionRowTitle } from "./actionIndex";

export { DECISIONS_PATH };
export const FINDINGS_LIST_PATH = "/findings";
export const ACTIONS_LIST_PATH = "/actions";
export const NOT_AVAILABLE_YET = "Not available yet";

// ---- Decisions ---------------------------------------------------------------------------------------------------

export type DecisionState = "waiting" | "watching" | "underway";
export const DECISION_STATE_WORD: Readonly<Record<DecisionState, string>> = {
  waiting: "Waiting for a choice",
  watching: "Being watched",
  underway: "Under way",
};

/** D-IAP.29: `underway` when an Action is set; else `watching` when the placement is `MONITOR`; else `waiting`. */
export function decisionStateKey(row: Pick<EstatePortfolioRow, "action_id" | "placement">): DecisionState {
  if (row.action_id !== null) return "underway";
  return row.placement.group === "MONITOR" ? "watching" : "waiting";
}

export interface DecisionItem {
  row: EstatePortfolioRow;
  state: DecisionState;
  stake: string;
  /** The row's one target, or null (a row that fails `findingLinkLive` is text). */
  target: string | null;
}

const LIFECYCLE_ORDER = ["SUPPORTED", "UNCONFIRMED", "NO_LONGER_SUPPORTED", "MERGED"] as const;
const LENS_VALUE: Readonly<Record<string, string>> = { COST: "cost", RISK: "risks", OPPORTUNITY: "opportunities" };
const LENS_OPTIONS = [
  { value: "cost", word: "Cost" },
  { value: "risks", word: "Risks" },
  { value: "opportunities", word: "Opportunities" },
];

/** Mini-grid Sites: coverage reports a matcher state for them; cold and EV Sites report `NOT_APPLICABLE` (as the Findings list does). */
function miniGridIds(sites: readonly EstateCoverageSite[]): ReadonlySet<string> {
  return new Set(sites.filter((s) => s.match_state !== "NOT_APPLICABLE").map((s) => s.site_id));
}

/** I8: `recommendation` only on a mini-grid `FINDING` Ref; a `FUEL_FINDING` and a windowed cold or EV Ref link as sent. */
function decisionTarget(row: EstatePortfolioRow, mini: ReadonlySet<string>): string | null {
  if (!findingLinkLive(row, mini)) return null;
  const ref = row.link_refs?.finding;
  if (ref === null || ref === undefined) return null;
  return ref.kind === "FINDING" && mini.has(row.site_id) ? linkFor({ ...ref, view: "recommendation" }) : linkFor(ref);
}

export function decisionItems(body: EstatePortfolioBody, rows: readonly EstatePortfolioRow[]): DecisionItem[] {
  const sites = new Map<string, EstateCoverageSite>(body.coverage.sites.map((s) => [s.site_id, s]));
  const mini = miniGridIds(body.coverage.sites);
  return rows.map((row) => ({
    row,
    state: decisionStateKey(row),
    stake: consequenceFirst(row, sites.get(row.site_id)),
    target: decisionTarget(row, mini),
  }));
}

function bySite<T>(name: (i: T) => string) {
  return (a: T, b: T) => name(a).localeCompare(name(b));
}

/**
 * IA-P P6 (D-IAP.37 Q13): the one waiting total. The Decisions tile "Waiting for a choice" and the shell's "Waiting for
 * you" badge both read it, so badge = tile in every case: `total` (the server's `waiting_count`, given when the read
 * was truncated) when set, else the rows in `waiting`. 6f1 U2 (tile = E0, D-P6.78) re-sources this one function.
 */
export function waitingForAChoice(items: readonly DecisionItem[], total: number | null): number {
  return total !== null ? total : items.filter((i) => i.state === "waiting").length;
}

/** The `total` `waitingForAChoice` takes for a loaded Decisions read: `waiting_count` when the read was truncated. */
export function waitingTotalOf(loaded: { truncated: boolean; first: EstatePortfolioBody }): number | null {
  return loaded.truncated ? (loaded.first.summary.waiting_count ?? null) : null;
}

/** `waitingTotal`: the server's `waiting_count`, used by the tile when the read was truncated. */
export function decisionsDef(waitingTotal: number | null = null): HomeListDef<DecisionItem> {
  return {
    key: "decisions",
    path: DECISIONS_PATH,
    plural: "decisions",
    tileLabel: "Decisions",
    rowKey: (i) => i.row.finding_id,
    title: (i) => i.row.title,
    small: (i) => <small>{PLACEMENT_GROUP_LABEL[i.row.placement.group]}</small>,
    target: (i) => i.target,
    firstColumn: "Decision",
    columns: [
      { label: "Site", cell: (i) => i.row.site_name },
      { label: "State", cell: (i) => DECISION_STATE_WORD[i.state] },
      { label: "At stake", cell: (i) => i.stake },
      { label: "Due", cell: () => NOT_AVAILABLE_YET },
      { label: "Who decides", cell: () => NOT_AVAILABLE_YET },
    ],
    facets: [
      {
        key: "state",
        label: "State",
        options: (Object.keys(DECISION_STATE_WORD) as DecisionState[]).map((value) => ({ value, word: DECISION_STATE_WORD[value] })),
        all: "All states",
        of: (i) => i.state,
      },
      { key: "lens", label: "Finding type", options: LENS_OPTIONS, all: "All findings", of: (i) => i.row.lens_flags.map((f) => LENS_VALUE[f]) },
    ],
    sorts: [
      { key: "priority", label: "Priority" },
      { key: "site", label: "Site", compare: bySite((i) => i.row.site_name) },
    ],
    text: (i) => `${i.row.title} ${i.row.site_name} ${DECISION_STATE_WORD[i.state]} ${i.stake}`,
    site: (i) => i.row.site_code,
    domain: (i) => i.row.domain,
    scopeWord: (s) => (s.startsWith("group:") ? (DOMAIN_WORD as Record<string, string>)[s.slice(6)] ?? s : s.slice(5)),
    tiles: (_m, rows, whole) => [
      { label: "Waiting for a choice", role: "part" as const, value: waitingForAChoice(rows, whole ? waitingTotal : null) },
    ],
    none: "No decisions in this range.",
  };
}

// ---- Findings ----------------------------------------------------------------------------------------------------

export interface FindingItem {
  row: EstateFindingRow;
  decision: DecisionItem | null;
  target: string | null;
}

export function findingItems(
  rows: readonly EstateFindingRow[],
  coverage: { site_id: string; match_state: string }[],
  decisions: readonly DecisionItem[],
): FindingItem[] {
  const mini = new Set(coverage.filter((s) => s.match_state !== "NOT_APPLICABLE").map((s) => s.site_id));
  const byId = new Map(decisions.map((d) => [d.row.finding_id, d]));
  return rows.map((row) => ({
    row,
    decision: byId.get(row.finding_id) ?? null,
    target: findingLinkLive(row, mini) ? linkFor(row.link_refs?.finding) : null,
  }));
}

/** M2: the Decisions read behind the Findings list is `loading`, `unavailable` (refused) or `ready`; never a false none. */
export type DecisionsReadState = "loading" | "unavailable" | "ready";

export function findingsDef(decisions: DecisionsReadState = "ready"): HomeListDef<FindingItem> {
  const heading = (i: FindingItem) => {
    const labels = i.row.categories?.state === "MAPPED" ? i.row.categories.items.map((c) => c.label) : [];
    return labels.length > 0 ? labels.join(" · ") : NOT_AVAILABLE_YET;
  };
  const decision = (i: FindingItem) =>
    decisions === "loading" ? "Loading…" : decisions === "unavailable" ? NOT_AVAILABLE_YET : i.decision === null ? "No decision open" : DECISION_STATE_WORD[i.decision.state];
  return {
    key: "findings",
    path: FINDINGS_LIST_PATH,
    plural: "Findings",
    tileLabel: "Findings",
    rowKey: (i) => i.row.finding_id,
    title: (i) => i.row.title,
    small: (i) => <small>{i.row.finding_label}</small>,
    target: (i) => i.target,
    firstColumn: "Finding",
    columns: [
      { label: "Site", cell: (i) => i.row.site_name },
      { label: "Heading", cell: heading },
      { label: "Its decision", cell: decision },
    ],
    facets: [
      { key: "lens", label: "Finding type", options: LENS_OPTIONS, all: "All findings", of: (i) => i.row.lens_flags.map((f) => LENS_VALUE[f]) },
      {
        key: "state",
        label: "State",
        options: LIFECYCLE_ORDER.map((l) => ({ value: LIFECYCLE_WORDS[l].filter, word: LIFECYCLE_WORDS[l].text })),
        all: "All states",
        of: (i) => LIFECYCLE_WORDS[i.row.lifecycle].filter,
      },
    ],
    sorts: [
      { key: "priority", label: "Priority" },
      { key: "site", label: "Site", compare: bySite((i) => i.row.site_name) },
    ],
    text: (i) => `${i.row.title} ${i.row.finding_label} ${i.row.site_name} ${heading(i)} ${decision(i)}`,
    site: (i) => i.row.site_code,
    scopeWord: (s) => s.slice(s.indexOf(":") + 1),
    tiles: (_m, rows) => [
      {
        label: "Decision waiting for a choice",
        role: "part" as const,
        value: decisions === "loading" ? "Loading…" : decisions === "unavailable" ? NOT_AVAILABLE_YET : rows.filter((i) => i.decision?.state === "waiting").length,
      },
    ],
    none: "No Findings in this range.",
  };
}

// ---- Actions -----------------------------------------------------------------------------------------------------

export const APPLICATION_STATE_WORD: Readonly<Record<EstateActionRow["application_state"], string>> = {
  PENDING: "Pending",
  APPLIED: "Applied",
  NONE_AT_CUTOFF: "No action yet",
};
const APPLICATION_ORDER = ["PENDING", "APPLIED", "NONE_AT_CUTOFF"] as const;

export interface ActionsSummary {
  open_actions: number | null;
  due_overdue: number | null;
  verification_window: number | null;
  verified_in_30_days: number | null;
}

/** Today's four server figures, kept as one caption line (MOCK DEVIATION D2, MD-IAP-6). */
export function actionsCaption(summary: ActionsSummary): string {
  const f = (v: number | null) => (v === null ? "Some data missing" : String(v));
  return `Open actions ${f(summary.open_actions)} · Due / overdue ${summary.due_overdue === null ? "Not set" : summary.due_overdue} · Verification window ${f(summary.verification_window)} · Verified in 30 days ${f(summary.verified_in_30_days)}`;
}

export function actionsDef(summary: ActionsSummary | null = null): HomeListDef<EstateActionRow> {
  return {
    key: "actions",
    path: ACTIONS_LIST_PATH,
    plural: "Actions",
    tileLabel: "Actions",
    rowKey: (r) => r.action_id,
    title: actionRowTitle,
    small: (r) => (r.success_criterion === null ? null : <small>{r.success_criterion}</small>),
    target: (r) => linkFor(r.link_refs?.action),
    firstColumn: "Action",
    columns: [
      { label: "Owner", cell: (r) => r.owner ?? "Not recorded" },
      { label: "Due", cell: (r) => (r.due_at === null ? "No deadline" : formatDay(r.due_at)) },
      { label: "State", cell: (r) => APPLICATION_STATE_WORD[r.application_state] },
    ],
    facets: [
      {
        key: "state",
        label: "State",
        options: APPLICATION_ORDER.map((value) => ({ value, word: APPLICATION_STATE_WORD[value] })),
        all: "All states",
        of: (r) => r.application_state,
      },
    ],
    sorts: [
      { key: "priority", label: "Priority" },
      { key: "due", label: "Due date", compare: (a, b) => (a.due_at === null ? (b.due_at === null ? 0 : 1) : b.due_at === null ? -1 : a.due_at < b.due_at ? -1 : a.due_at > b.due_at ? 1 : 0) },
      { key: "site", label: "Site", compare: bySite((r) => r.site_name) },
    ],
    text: (r) => `${r.action_title} ${r.action_code} ${r.site_name} ${r.owner ?? ""} ${r.success_criterion ?? ""}`,
    site: (r) => r.site_code,
    scopeWord: (s) => s.slice(s.indexOf(":") + 1),
    tiles: (_m, rows) =>
      APPLICATION_ORDER.filter((s) => rows.some((r) => r.application_state === s)).map((s) => ({
        label: APPLICATION_STATE_WORD[s],
        role: "part" as const,
        value: rows.filter((r) => r.application_state === s).length,
      })),
    caption: summary === null ? undefined : () => actionsCaption(summary),
    none: "No Actions in this range.",
  };
}

// ---- The page frames ---------------------------------------------------------------------------------------------

function ListPage({
  root,
  title,
  loading,
  children,
  refused,
  cutoff,
}: {
  root: string;
  title: string;
  loading: string | null;
  children: React.ReactNode;
  refused: { code: string; copy: string; to: string } | null;
  cutoff: React.ReactNode;
}) {
  const [params] = useSearchParams();
  const query = queryFromParams(params);
  return (
    <div className="estate-page" data-estate-root={root}>
      <PageHeader title={title} />
      {cutoff}
      {loading !== null ? (
        <p className="estate-loading">{loading}</p>
      ) : refused !== null ? (
        <EstateRefusal code={refused.code} copy={refused.copy} window={query} firstPage={refused.to} />
      ) : (
        children
      )}
    </div>
  );
}

function Truncated({ truncated }: { truncated: boolean }) {
  return truncated ? (
    <p className="estate-partial" data-estate-partial>
      {TRUNCATED_LINE}
    </p>
  ) : null;
}

export function DecisionsListPage({ client }: { client?: EstateClient }) {
  const reads = useMemo(() => client ?? createEstateClient(), [client]);
  const [params] = useSearchParams();
  const query = queryFromParams(params);
  const read = useEstateRead(reads, "portfolio", query);
  const loaded = read?.status === "loaded" ? read.value : null;
  const items = useMemo(() => (loaded === null ? [] : decisionItems(loaded.first, loaded.rows)), [loaded]);
  const def = useMemo(() => decisionsDef(loaded === null ? null : waitingTotalOf(loaded)), [loaded]);
  return (
    <ListPage
      root="decisions"
      title="Decisions"
      loading={read === null ? "Loading Decisions…" : null}
      refused={read?.status === "refused" ? { code: read.code, copy: read.copy, to: estateHref(DECISIONS_PATH, query) } : null}
      cutoff={<EstateCutoffLine query={query} body={loaded === null ? null : barBody(loaded.first)} windowRefused={read?.status === "refused" && read.code === "INVALID_WINDOW"} />}
    >
      {loaded !== null ? (
        <>
          <HomeList def={def} items={items} total={loaded.first.total_count} />
          <Truncated truncated={loaded.truncated} />
        </>
      ) : null}
    </ListPage>
  );
}

export function FindingsListPage({ client }: { client?: EstateClient }) {
  const reads = useMemo(() => client ?? createEstateClient(), [client]);
  const [params] = useSearchParams();
  const query = queryFromParams(params);
  const read = useEstateRead(reads, "findings", query);
  const decisions = useEstateRead(reads, "portfolio", query);
  const loaded = read?.status === "loaded" ? read.value : null;
  const dec = decisions?.status === "loaded" ? decisions.value : null;
  const decided = useMemo(() => (dec === null ? [] : decisionItems(dec.first, dec.rows)), [dec]);
  const items = useMemo(() => (loaded === null ? [] : findingItems(loaded.rows, loaded.first.coverage.sites, decided)), [loaded, decided]);
  const decisionsState: DecisionsReadState = dec !== null ? "ready" : decisions?.status === "refused" ? "unavailable" : "loading";
  const def = useMemo(() => findingsDef(decisionsState), [decisionsState]);
  return (
    <ListPage
      root="findings"
      title="Findings"
      loading={read === null ? "Loading Findings…" : null}
      refused={read?.status === "refused" ? { code: read.code, copy: read.copy, to: estateHref(FINDINGS_LIST_PATH, query) } : null}
      cutoff={<EstateCutoffLine query={query} body={loaded?.first ?? null} windowRefused={read?.status === "refused" && read.code === "INVALID_WINDOW"} />}
    >
      {loaded !== null ? (
        <>
          <HomeList def={def} items={items} total={loaded.first.total_count} />
          <Truncated truncated={loaded.truncated} />
        </>
      ) : null}
    </ListPage>
  );
}

export function ActionsListPage({ client }: { client?: EstateClient }) {
  const reads = useMemo(() => client ?? createEstateClient(), [client]);
  const [params] = useSearchParams();
  const query = queryFromParams(params);
  const read = useEstateRead(reads, "actions", query);
  const loaded = read?.status === "loaded" ? read.value : null;
  const def = useMemo(() => actionsDef(loaded?.first.summary ?? null), [loaded]);
  return (
    <ListPage
      root="actions"
      title="Actions"
      loading={read === null ? "Loading Actions…" : null}
      refused={read?.status === "refused" ? { code: read.code, copy: read.copy, to: estateHref(ACTIONS_LIST_PATH, query) } : null}
      cutoff={<EstateCutoffLine query={query} body={loaded?.first ?? null} windowRefused={read?.status === "refused" && read.code === "INVALID_WINDOW"} />}
    >
      {loaded !== null ? (
        <>
          <HomeList def={def} items={loaded.rows} total={loaded.first.total_count} />
          <Truncated truncated={loaded.truncated} />
        </>
      ) : null}
    </ListPage>
  );
}


/** IA-P P3b (spec §3 "Overview L2"): the Decisions rows on the Overview are capped at six. */
export const OVERVIEW_DECISIONS_CAP = 6;

/**
 * IA-P P3b (spec §3, §6 P3b): the Overview's L2 Decisions panel. The Decisions list's rows for the range, through the
 * one list component with no tools and no tiles, capped at six, then "View all {n}" to `/decisions` with the range.
 * The rows come from the same cached read as the Decisions list (31-day window, P0); the block says so on a longer
 * range (`RangePartNote`). The title is the caller's (5c's served panel title in mode `month`).
 */
export function DecisionsRows({ client, title }: { client?: EstateClient; title: string }) {
  const reads = useMemo(() => client ?? createEstateClient(), [client]);
  const [params] = useSearchParams();
  const query = queryFromParams(params);
  const read = useEstateRead(reads, "portfolio", query);
  const loaded = read?.status === "loaded" ? read.value : null;
  const items = useMemo(() => (loaded === null ? [] : decisionItems(loaded.first, loaded.rows)), [loaded]);
  const def = useMemo(() => decisionsDef(loaded === null ? null : waitingTotalOf(loaded)), [loaded]);
  const range = readSharedRange(params);
  return (
    <section className="dd-panel" aria-labelledby="dd-decisions-h" data-overview-decisions>
      <h2 id="dd-decisions-h">{title}</h2>
      <RangePartNote range={range.status === "set" ? range : null} />
      {read === null ? (
        <p className="estate-loading">Loading Decisions…</p>
      ) : read.status === "refused" ? (
        <EstateRefusal code={read.code} copy={read.copy} window={query} firstPage={estateHref(DECISIONS_PATH, query)} />
      ) : (
        <HomeList def={def} items={items} total={read.value.first.total_count} options={{ tools: false, tiles: false, cap: OVERVIEW_DECISIONS_CAP }} />
      )}
    </section>
  );
}
