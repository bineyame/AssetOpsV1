/**
 * W6-01b B2: the global Maintenance root, Corrective view (v6.9 `maintenance`), read from `GET /api/work/maintenance`
 * (`global-work-index-1`). The mock's slots, in order (`index.html:959-961`): breadcrumb, h1 and subtitle, the
 * `Corrective` / `Preventive · scheduled` view tabs, the date bar, the four cards, the `Corrective work requests`
 * panel and the blue lifecycle notice. Copy follows `.agent/W6-01-build-spec.md` section 2, section 3.1 (A2Q1,
 * A2Q4-A2Q7, A2Q10, X1-X8, CL3-1) and the "B1-B3 pre-flight rulings" P-B2-3..11, which supersede them.
 *
 * MOCK DEVIATION (P-B2-3..8): the lifecycle notice copy changes, because W4 has no work-outcome evaluator or
 * automated follow-up. W6-01c C2 (P-C2-12) mounted the exact request Overview: the primary Work request link is
 * the API `links.detail` (Site code and explicit cutoff kept), with the Site maintenance window only as a fallback. W6-01b B3 (CL3-2, P-B2-4, P-B3-8) made the Preventive tab and the third card's separate
 * `View detail →` link live, both to `/maintenance/preventive` with the effective window and cutoff, never a cursor. A refusal, a read failure, an empty scope or a changed list is stated, never zero.
 */
import { Link } from "react-router-dom";
import type { EstateClient } from "../estate/estateClient";
import { useOutcomeSummary } from "../estate/useOutcomeSummary";
import { CellDisclosure } from "./CellDisclosure";
import { stateTone } from "../sites/siteWorkCases";
import { Breadcrumbs, DataTable, MetricCard, MetricCards, Notice, PageHeader, Panel } from "../ui";
import {
  type GlobalMaintenanceBody,
  type GlobalMaintenanceRow,
  type GlobalMaintenanceState,
  globalWorkHref,
  type GlobalWorkClient,
  type GlobalWorkQuery,
} from "./globalWorkClient";
import {
  CHANGE_WINDOW,
  Clamp,
  GlobalWorkBar,
  GlobalWorkSlot,
  LinkOrText,
  MockDeviation,
  Pager,
  SCROLL_TABLE,
  WorkSourceLine,
  assetLabelWords,
  findingLinks,
  joined,
  requestCount,
  useGlobalWorkPage,
} from "./globalWorkParts";
import "./globalWork.css";

/** The page path; the route constant `MAINTENANCE_PATH` in `shell/operatorSiteRoutes.ts` has the same value. */
const PAGE_PATH = "/maintenance";
export const GLOBAL_MAINTENANCE_HEADING_ID = "global-maintenance-heading";
const TABLE_HEADING_ID = "global-maintenance-requests-heading";

export const GLOBAL_MAINTENANCE_SUBTITLE = "Physical maintenance work and outcome verification";
export const GLOBAL_MAINTENANCE_LOADING = "Loading the work requests across the estate.";
export const CORRECTIVE_REQUESTS_FOOTER = "Completed is activity evidence only; outcome is verified separately";
export const MAINTENANCE_NOTICE = "A completed request records activity; an equipment outcome remains unverified.";
export const NO_WORK_REQUESTS = "No work requests in this window.";
export const NO_LINKED_FINDING_OR_ACTION = "No linked Finding or Action";
/** Post-W6 W6 Q7: the stored time that places a request in the window. */
export const MAINTENANCE_MEMBERSHIP = "Listed by the time each request was opened.";

const STATE_LABEL: Readonly<Record<GlobalMaintenanceState, string>> = {
  OPEN: "Open",
  IN_PROGRESS: "In progress",
  COMPLETED: "Completed",
  CANCELLED: "Cancelled",
};

const CORRECTIVE_PATH = PAGE_PATH;
const PREVENTIVE_PATH = "/maintenance/preventive";

/** A view href with the effective `from`/`to`/`known_at` (the seven-day default when the URL has none), no cursor. */
function viewHref(path: string, query: Pick<GlobalWorkQuery, "from" | "to" | "known_at"> | null): string {
  return query === null ? path : globalWorkHref(path, query);
}

const VIEWS = [
  { view: "corrective", label: "Corrective", path: CORRECTIVE_PATH },
  { view: "preventive", label: "Preventive · scheduled", path: PREVENTIVE_PATH },
] as const;

/**
 * The `Maintenance views` tab row between the header and the date bar (P-B2-9, P-B3-8, mock `MAINT_GTABS`). The
 * current view is plain text with `aria-current`; the other is a link that keeps the effective window and cutoff.
 */
export function MaintenanceViews({
  current,
  query,
}: {
  current: "corrective" | "preventive";
  query: Pick<GlobalWorkQuery, "from" | "to" | "known_at"> | null;
}) {
  return (
    <nav aria-label="Maintenance views" className="site-tabs global-work-tabs" data-global-work-tabs>
      <ul className="site-tabs__list">
        {VIEWS.map((tab) => (
          <li className="site-tabs__item" key={tab.view}>
            {tab.view === current ? (
              <span className="site-tabs__link" aria-current="page" data-global-work-tab={tab.view}>
                {tab.label}
              </span>
            ) : (
              <Link className="site-tabs__link" to={viewHref(tab.path, query)} data-global-work-tab={tab.view}>
                {tab.label}
              </Link>
            )}
          </li>
        ))}
      </ul>
    </nav>
  );
}

function Badge({ tone, children, data }: { tone: "red" | "amber" | "blue" | "neutral"; children: string; data?: Record<string, string> }) {
  return (
    <span className={`w1f4-action-badge${tone === "neutral" ? "" : ` w1f4-action-badge--${tone}`}`} data-global-work-tone={tone} {...data}>
      {children}
    </span>
  );
}

function WorkRequestCell({ row }: { row: GlobalMaintenanceRow }) {
  const text = `${row.code} · ${row.title}`;
  // W6-01c C2: the primary link is the exact request Overview (`links.detail`); Site maintenance is the fallback.
  const href = row.links.detail?.href ?? row.links.site_maintenance.href;
  // Post-W6 W6 Q2 (R352): cold and EV Findings are plain `Finding {id8}`; a mini-grid Finding keeps its link.
  const links = [...findingLinks(row.finding_links, row.site_domain), ...row.action_links];
  return (
    <>
      <Clamp data={{ "data-global-work-title": "" }}>{href ? <Link to={href}>{text}</Link> : text}</Clamp>
      <details className="global-work-details" data-global-work-full-title>
        <summary>Full title text</summary>
        {row.title}
      </details>
      <CellDisclosure
        column="Work request links"
        row={row.code}
        data={{ "data-global-work-lineage": links.length > 0 ? "linked" : "none" }}
      >
        {links.length > 0
          ? joined(
              links.map((link, index) => (
                <LinkOrText key={`${link.label}-${index}`} link={link} data={{ "data-global-work-link": "" }} />
              )),
              " · ",
            )
          : NO_LINKED_FINDING_OR_ACTION}
      </CellDisclosure>
      <WorkSourceLine provenance={row.source_provenance} />
    </>
  );
}

function RequestRow({ row }: { row: GlobalMaintenanceRow }) {
  return (
    <tr data-global-work-row={row.case_id}>
      <td>
        <WorkRequestCell row={row} />
      </td>
      <td>
        <CellDisclosure column="Asset / site" row={row.code} data={{ "data-global-work-asset-site": "" }}>
          {assetLabelWords(row.asset_label) ?? "No asset recorded"}
          {" · "}
          <LinkOrText link={row.links.site} data={{ "data-global-work-site": row.site_code }} />
        </CellDisclosure>
      </td>
      <td>
        <CellDisclosure column="Owner" row={row.code} data={{ "data-global-work-owner": "" }}>
          {row.owner ?? "Not assigned"}
        </CellDisclosure>
      </td>
      <td>
        <Badge tone={stateTone("maintenance", row.state)} data={{ "data-global-work-state": row.state }}>
          {STATE_LABEL[row.state] ?? row.state}
        </Badge>
      </td>
      <td>
        <Badge tone="amber" data={{ "data-global-work-verification": "" }}>
          Not established
        </Badge>
      </td>
      <td>
        <Badge tone="neutral" data={{ "data-global-work-warranty": "" }}>
          Not recorded
        </Badge>
      </td>
    </tr>
  );
}

const COLUMNS = ["Work request", "Asset / site", "Owner", "State", "Verification", "Warranty"];
/** P-B2-7: the maintenance column minimum widths (px); the table scrolls inside its panel below their sum. */
const MIN_WIDTHS = [220, 210, 160, 120, 170, 150];

function RequestTable({ body }: { body: GlobalMaintenanceBody }) {
  return (
    <DataTable labelledBy={TABLE_HEADING_ID}>
      <colgroup>
        {MIN_WIDTHS.map((width, index) => (
          <col key={index} style={{ width: `${width}px` }} />
        ))}
      </colgroup>
      <thead>
        <tr>
          {COLUMNS.map((h) => (
            <th key={h} scope="col">
              {h}
            </th>
          ))}
        </tr>
      </thead>
      <tbody>
        {body.rows.map((row) => (
          <RequestRow key={`${row.site_id}/${row.case_id}`} row={row} />
        ))}
      </tbody>
    </DataTable>
  );
}

/** P-B2-4: the mock's separate `View detail →` link on the third card, to the Preventive view (B3). */
function PreventiveCardNote({ query }: { query: GlobalWorkQuery | null }) {
  return (
    <>
      <span data-global-work-preventive-note>See Preventive</span>
      <span className="global-work-card-link" data-global-work-preventive-link>
        <Link to={viewHref(PREVENTIVE_PATH, query)}>View detail →</Link>
      </span>
    </>
  );
}

const DAY_MS = 86_400_000;
/** OUT-C U6: the estate summary's own maximum window (days). */
const SUMMARY_MAX_DAYS = 31;
export const REPEAT_VISITS_LABEL = "Repeat visits without a result";
export const REPEAT_VISITS_NONE = "None in the last 60 days";
export const REPEAT_VISITS_UNCHECKED = "Repeat visits could not be checked for this window";
const REPEATED_KIND = "REPEATED_MAINTENANCE_NO_RESULT";

/**
 * OUT-C U6: the covering UTC days of the page window, `[floor(from), ceil(to))`; null when the instants do not parse
 * or the covering window is longer than the summary allows.
 */
export function coveringUtcDays(query: GlobalWorkQuery | null): { from: string; to: string } | null {
  if (query === null) return null;
  const from = Date.parse(query.from);
  const to = Date.parse(query.to);
  if (Number.isNaN(from) || Number.isNaN(to) || to <= from) return null;
  const lo = Math.floor(from / DAY_MS) * DAY_MS;
  const hi = Math.ceil(to / DAY_MS) * DAY_MS;
  if (hi - lo > SUMMARY_MAX_DAYS * DAY_MS) return null;
  const iso = (ms: number) => `${new Date(ms).toISOString().slice(0, 10)}T00:00:00Z`;
  return { from: iso(lo), to: iso(hi) };
}

/** OUT-C U6 (replaces the retired "Repeat findings" card): REPEATED warnings in the estate summary. */
function RepeatVisitsCard({ estate, query }: { estate: Pick<EstateClient, "getOutcomeSummary">; query: GlobalWorkQuery | null }) {
  const days = coveringUtcDays(query);
  const summary = useOutcomeSummary(estate, days === null ? null : { ...days, known_at: query?.known_at ?? null });
  const data = { "data-global-work-card": "repeat_visits" };
  if (days === null || summary === null || summary.status !== "loaded") {
    return <MetricCard label={REPEAT_VISITS_LABEL} value="Not assessed" word note={REPEAT_VISITS_UNCHECKED} data={data} />;
  }
  const repeated = summary.value.warnings.filter((w) => w.kind === REPEATED_KIND);
  const first = repeated[0];
  const note =
    first === undefined ? (
      REPEAT_VISITS_NONE
    ) : (
      <LinkOrText
        link={{ label: `${first.subject_label ?? ""} · ${first.count ?? ""} visits, linked finding still open`, href: first.href }}
        data={{ "data-global-work-repeat-link": "" }}
      />
    );
  return <MetricCard label={REPEAT_VISITS_LABEL} value={String(repeated.length)} note={note} data={data} />;
}

function Cards({
  body,
  query,
  estate,
}: {
  body: GlobalMaintenanceBody;
  query: GlobalWorkQuery | null;
  estate: Pick<EstateClient, "getOutcomeSummary">;
}) {
  const open = body.state_counts.OPEN + body.state_counts.IN_PROGRESS;
  return (
    <MetricCards label="Maintenance summary" data={{ "data-global-work-cards": "" }}>
      <MetricCard
        label="Open work"
        value={String(open)}
        note={`${requestCount(open)} in progress or open`}
        data={{ "data-global-work-card": "open" }}
      />
      <MetricCard
        label="Verification overdue"
        value="Not assessed"
        assessment
        tone="amber"
        note="No work-outcome verification clock"
        data={{ "data-global-work-card": "verification_overdue" }}
      />
      <MetricCard
        label="Preventive due in 30 days"
        value="Not assessed"
        word
        note={<PreventiveCardNote query={query} />}
        data={{ "data-global-work-card": "preventive_due" }}
      />
      <RepeatVisitsCard estate={estate} query={query} />
    </MetricCards>
  );
}

const NO_SUMMARY: Pick<EstateClient, "getOutcomeSummary"> = {};

export function GlobalMaintenancePage({ client, estate = NO_SUMMARY }: { client?: GlobalWorkClient; estate?: Pick<EstateClient, "getOutcomeSummary"> }) {
  const page = useGlobalWorkPage<GlobalMaintenanceBody>(PAGE_PATH, client, (reads, query) =>
    reads.maintenance ? reads.maintenance(query) : null,
  );
  const { body, shown, query, trail } = page;

  return (
    <div className="global-work global-work--maintenance" data-global-work-root="maintenance">
      <Breadcrumbs trail={[{ label: "Maintenance" }]} />
      <PageHeader title="Maintenance" headingId={GLOBAL_MAINTENANCE_HEADING_ID} subtitle={GLOBAL_MAINTENANCE_SUBTITLE} />
      <MaintenanceViews current="corrective" query={query} />
      <GlobalWorkBar page={page} label="Maintenance window" membership={MAINTENANCE_MEMBERSHIP} />
      <GlobalWorkSlot
        page={page}
        loading={GLOBAL_MAINTENANCE_LOADING}
        cards={(value) => <Cards body={value} query={query} estate={estate} />}
      />
      <Panel heading="Corrective work requests" headingId={TABLE_HEADING_ID} description={CORRECTIVE_REQUESTS_FOOTER}>
        {shown && body !== null ? (
          body.total_count === 0 ? (
            <div className="global-work-empty" data-global-work-zero>
              <p>{NO_WORK_REQUESTS}</p>
              <p>{CHANGE_WINDOW}</p>
            </div>
          ) : (
            <>
              <p className="global-work-scroll-hint" data-global-work-scroll-hint>
                {SCROLL_TABLE}
              </p>
              <RequestTable body={body} />
              <Pager
                label="Maintenance pages"
                body={body}
                trail={trail}
                cursor={query?.cursor ?? null}
                onPage={(cursor, nextTrail) => query && page.go(query, cursor, nextTrail)}
              />
              {/* MOCK DEVIATION D1 (R355): the table keeps the panel's height budget with an inner scroll, so every
                  row stays reachable inside it. */}
              <MockDeviation category="D1" id="R355" />
            </>
          )
        ) : null}
        {/* MOCK DEVIATION D1 (R358): cards 2-3 state "Not assessed" where no stored assessment exists (OUT-C: card 4
            is the repeat-visit count). */}
        {shown ? <MockDeviation category="D1" id="R358" /> : null}
      </Panel>
      <Notice tone="blue" data={{ "data-global-work-notice": "" }}>
        <p>{MAINTENANCE_NOTICE}</p>
      </Notice>
    </div>
  );
}

/** The routed frame: the page in its `<main>` landmark, named by the page heading. */
export function GlobalMaintenanceFrame({ client, estate }: { client?: GlobalWorkClient; estate?: EstateClient }) {
  return (
    <main aria-labelledby={GLOBAL_MAINTENANCE_HEADING_ID}>
      <GlobalMaintenancePage client={client} estate={estate} />
    </main>
  );
}
