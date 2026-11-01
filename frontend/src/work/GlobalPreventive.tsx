/**
 * W6-01b B3: the global Maintenance root, Preventive view (v6.9 `maintenance-preventive`), read from
 * `GET /api/work/preventive` (`global-work-index-1`). The mock's slots, in order (`index.html:962-965`): breadcrumb,
 * h1 and subtitle, the `Corrective` / `Preventive · scheduled` view tabs, the date bar, the status strip, the four
 * cards, the `Preventive plan` panel and the blue notice. Copy follows `.agent/W6-01-build-spec.md` section 2, section
 * 3.1 (A2Q1, A2Q4-A2Q7, A2Q10, X1-X8, CL3-1) and the "B1-B3 pre-flight rulings" P-B3-3..9, which supersede them.
 *
 * MOCK DEVIATIONS (P-B3-3..6): the status badge `2 overdue` becomes `Due status not assessed` (no due evaluator); the
 * strip's `Assets →` is an unavailable entry (no live global Assets root); Trigger shows the stored trigger kind and
 * State a `Draft` badge (no recurrence rule or due evaluator); the asset label is plain text (no general Asset route);
 * the panel footer and the notice keep their slots with bounded copy (no plan-completion command; the mock incident
 * story cannot be attributed to stored plans). A refusal, a read failure or a changed list is stated, never zero.
 *
 * POLISH P-09 (§1.4, PB-3): the cards, the strip badge and a per-row chip read the optional wire `summary` and
 * `due_state`; an older build without them states that the counts were not sent, never zero. Due dates use the Site zone
 * (`site_time_zone`) when sent, else UTC (Addendum 12 Q2). The DRAFT state reads "Not yet approved" (Addendum 12 Q4).
 */
import { displayCode } from "../ui/displayCode";
import { TechnicalDetails, TechnicalReferenceList } from "../ui/TechnicalDetails";
import { formatDay } from "../ui/time";
import { Breadcrumbs, DataTable, MetricCard, MetricCards, Notice, PageHeader, Panel, StatusBar } from "../ui";
import { UnavailableInline } from "../ui/UnavailableEntry";
import { CellDisclosure } from "./CellDisclosure";
import { MaintenanceViews } from "./GlobalMaintenance";
import {
  globalWorkHref,
  type GlobalPreventiveBody,
  type GlobalPreventiveDueState,
  type GlobalPreventiveRow,
  type GlobalPreventiveSummary,
  type GlobalWorkClient,
} from "./globalWorkClient";
import {
  CHANGE_WINDOW,
  Clamp,
  GlobalWorkBar,
  GlobalWorkSlot,
  LinkOrText,
  Pager,
  SCROLL_TABLE,
  WorkSourceLine,
  useGlobalWorkPage,
} from "./globalWorkParts";
import "./globalWork.css";

/** The page path; the route constant `MAINTENANCE_PREVENTIVE_PATH` in `shell/operatorSiteRoutes.ts` has the same value. */
const PAGE_PATH = "/maintenance/preventive";
const CORRECTIVE_PATH = "/maintenance";
export const GLOBAL_PREVENTIVE_HEADING_ID = "global-preventive-heading";
const TABLE_HEADING_ID = "global-preventive-plan-heading";

export const GLOBAL_PREVENTIVE_SUBTITLE = "Scheduled maintenance by calendar or hours of use";
export const GLOBAL_PREVENTIVE_LOADING = "Loading the preventive plans across the estate.";
/** POLISH P-09: the strip badge before the summary is read, or when this build does not send it. */
export const PREVENTIVE_STRIP_BADGE_UNAVAILABLE = "Due status not sent with this list";
export const PREVENTIVE_STRIP_TEXT = "Scheduled by calendar or hours of use · due dates as set in each plan";
export const PREVENTIVE_PLAN_FOOTER = "Plans can't be completed from this page yet.";
export const PREVENTIVE_NOTICE = "These plans are not yet approved, and none is linked to an incident or a cause.";
export const NO_PREVENTIVE_PLANS = "No preventive plans in this window.";
/** Post-W6 W6 Q7: the stored time that places a plan in the window. */
export const PREVENTIVE_MEMBERSHIP = "Listed in the order plans were added.";
/** POLISH Addendum 12 Q4: the stored DRAFT state, in plain words (neutral tone). */
export const PLAN_NOT_APPROVED = "Not yet approved";
const DUE_NOT_AVAILABLE = "Not shown";
const DUE_COUNTS_NOT_AVAILABLE = "This list did not include the due counts";
const DAY_MS = 86_400_000;
const SOON_DAYS = 14;

/** POLISH P-09: the per-row chip; NOT_DUE shows none. */
const DUE_CHIP: Readonly<Partial<Record<GlobalPreventiveDueState, { label: string; tone: "amber" | "blue" | "neutral" }>>> = {
  OVERDUE: { label: "Overdue", tone: "amber" },
  DUE_SOON: { label: "Due soon", tone: "blue" },
  NOT_ASSESSED: { label: "No date", tone: "neutral" },
};

/** `1 plan` / `{n} plans`. */
const planCount = (n: number): string => `${n} ${n === 1 ? "plan" : "plans"}`;

/** The optional wire summary, only when every count is a non-negative number (else the not-sent wording). */
function summaryOf(body: GlobalPreventiveBody | null): GlobalPreventiveSummary | null {
  const summary: unknown = body?.summary;
  if (typeof summary !== "object" || summary === null) return null;
  const s = summary as Record<string, unknown>;
  const counts = [s.overdue_count, s.due_soon_count, s.not_assessed_count];
  return counts.every((n) => typeof n === "number" && Number.isFinite(n) && n >= 0) ? (summary as GlobalPreventiveSummary) : null;
}

function trigger(row: GlobalPreventiveRow): string {
  if (row.trigger_kind === "CALENDAR") return "Calendar";
  return row.next_due_hours === null ? "Hours of use" : `Every ${row.next_due_hours} hours of use`;
}

/** Addendum 12 Q2: a due date on the Site's own calendar day when its zone is sent, else the UTC day. */
function nextDue(row: GlobalPreventiveRow): string {
  if (row.next_due_at !== null) return formatDay(row.next_due_at, { timeZone: row.site_time_zone ?? null });
  if (row.next_due_hours !== null) return `At ${row.next_due_hours} hours of use`;
  return "Not set";
}

function DueChip({ state }: { state: GlobalPreventiveDueState | undefined }) {
  const chip = state === undefined ? undefined : DUE_CHIP[state];
  if (chip === undefined) return null;
  const tone = chip.tone === "neutral" ? "" : ` w1f4-action-badge--${chip.tone}`;
  return (
    <span className={`w1f4-action-badge${tone}`} data-global-work-due-state={state} data-global-work-tone={chip.tone}>
      {chip.label}
    </span>
  );
}

function PlanRow({ row }: { row: GlobalPreventiveRow }) {
  return (
    <tr data-global-work-row={row.root_id}>
      <td>
        <Clamp data={{ "data-global-work-title": "" }}>{`${displayCode(row.code)} · ${row.title}`}</Clamp>
        <details className="global-work-details" data-global-work-full-title>
          <summary>Full title text</summary>
          {row.title}
        </details>
        {row.correction_reason !== null ? (
          <>
            <CellDisclosure column="Plan item correction" row={row.code} data={{ "data-global-work-correction": "" }}>
              {`Correction: ${row.correction_reason}`}
            </CellDisclosure>
            {row.supersedes_plan_id !== null ? (
              <div data-global-work-supersedes>
                <TechnicalDetails name={`preventive-supersedes-${row.root_id}`}>
                  <TechnicalReferenceList references={[{ label: "Earlier plan version", value: row.supersedes_plan_id }]} />
                </TechnicalDetails>
              </div>
            ) : null}
          </>
        ) : null}
        <WorkSourceLine provenance={row.source_provenance} />
      </td>
      <td>
        <CellDisclosure column="Asset / site" row={row.code} data={{ "data-global-work-asset-site": "" }}>
          {row.asset_label ?? "No asset recorded"}
          {" · "}
          <LinkOrText link={row.links.site} data={{ "data-global-work-site": row.site_code }} />
        </CellDisclosure>
      </td>
      <td>
        <CellDisclosure column="Trigger" row={row.code} data={{ "data-global-work-trigger": "" }}>
          {trigger(row)}
        </CellDisclosure>
      </td>
      <td>
        <CellDisclosure column="Last done" row={row.code}>
          Not linked
        </CellDisclosure>
      </td>
      <td>
        <CellDisclosure column="Next due" row={row.code} data={{ "data-global-work-due": "" }}>
          {nextDue(row)}
        </CellDisclosure>
        <DueChip state={row.due_state} />
      </td>
      <td>
        <span className="w1f4-action-badge" data-global-work-state={row.state} data-global-work-tone="neutral">
          {PLAN_NOT_APPROVED}
        </span>
      </td>
      <td>
        <CellDisclosure column="What it proves" row={row.code}>
          No completed work confirmed yet
        </CellDisclosure>
      </td>
    </tr>
  );
}

const COLUMNS = ["Plan item", "Asset / site", "Trigger", "Last done", "Next due", "State", "What it proves"];
const WIDTHS = [24, 16, 14, 10, 12, 8, 16];

function PlanTable({ body }: { body: GlobalPreventiveBody }) {
  return (
    <DataTable labelledBy={TABLE_HEADING_ID}>
      <colgroup>
        {WIDTHS.map((width, index) => (
          <col key={index} style={{ width: `${width}%` }} />
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
          <PlanRow key={`${row.site_id}/${row.root_id}`} row={row} />
        ))}
      </tbody>
    </DataTable>
  );
}

function Cards({ body }: { body: GlobalPreventiveBody }) {
  const summary = summaryOf(body);
  const to = Date.parse(body.window.to);
  const before = formatDay(body.window.to);
  const by = Number.isNaN(to) ? DUE_NOT_AVAILABLE : formatDay(to + SOON_DAYS * DAY_MS);
  return (
    <>
    <MetricCards label="Preventive summary" data={{ "data-global-work-cards": "" }}>
      <MetricCard
        label="Scheduled items"
        value={String(body.total_count)}
        note={`Across ${body.scope.covered_site_count} sites`}
        data={{ "data-global-work-card": "scheduled_items" }}
      />
      {summary !== null ? (
        <MetricCard
          label="Overdue"
          value={String(summary.overdue_count)}
          tone={summary.overdue_count > 0 ? "amber" : undefined}
          note={`Calendar plans due before ${before}`}
          data={{ "data-global-work-card": "overdue" }}
        />
      ) : (
        <MetricCard label="Overdue" value={DUE_NOT_AVAILABLE} word note={DUE_COUNTS_NOT_AVAILABLE} data={{ "data-global-work-card": "overdue" }} />
      )}
      {summary !== null ? (
        <MetricCard
          label="Due in the next 14 days"
          value={String(summary.due_soon_count)}
          note={`Calendar plans due by ${by}`}
          data={{ "data-global-work-card": "due_14" }}
        />
      ) : (
        <MetricCard
          label="Due in the next 14 days"
          value={DUE_NOT_AVAILABLE}
          word
          note={DUE_COUNTS_NOT_AVAILABLE}
          data={{ "data-global-work-card": "due_14" }}
        />
      )}
      <MetricCard
        label="Feeds evidence"
        value="Not established"
        word
        note="No linked evidence yet"
        data={{ "data-global-work-card": "feeds_evidence" }}
      />
    </MetricCards>
    {summary !== null && summary.not_assessed_count > 0 ? (
      <p className="v69-chart-note" data-global-work-not-assessed>
        {`${planCount(summary.not_assessed_count)} based on hours of use; not checked here yet`}
      </p>
    ) : null}
    </>
  );
}

/** P-B3-4: the mock status strip between the date bar and the cards; its right `Assets` slot is unavailable. */
function PreventiveStrip({ summary }: { summary: GlobalPreventiveSummary | null }) {
  const overdue = summary?.overdue_count ?? null;
  const badge =
    overdue === null ? PREVENTIVE_STRIP_BADGE_UNAVAILABLE : overdue === 0 ? "None overdue" : `${overdue} overdue`;
  const tone = overdue !== null && overdue > 0 ? "amber" : "neutral";
  return (
    <StatusBar
      label="Preventive status"
      other={PREVENTIVE_STRIP_TEXT}
      action={<UnavailableInline label="Assets" />}
      data={{ "data-global-work-strip": "" }}
    >
      <span
        className={`w1f4-action-badge${tone === "amber" ? " w1f4-action-badge--amber" : ""}`}
        data-global-work-tone={tone}
        data-global-work-strip-badge=""
      >
        {badge}
      </span>
    </StatusBar>
  );
}

export function GlobalPreventivePage({ client }: { client?: GlobalWorkClient }) {
  const page = useGlobalWorkPage<GlobalPreventiveBody>(PAGE_PATH, client, (reads, query) =>
    reads.preventive ? reads.preventive(query) : null,
  );
  const { body, shown, query, trail } = page;
  const corrective = query === null ? CORRECTIVE_PATH : globalWorkHref(CORRECTIVE_PATH, query);

  return (
    <div className="global-work global-work--preventive" data-global-work-root="preventive">
      <Breadcrumbs trail={[{ label: "Maintenance", to: corrective }, { label: "Preventive · scheduled" }]} />
      <PageHeader title="Maintenance" headingId={GLOBAL_PREVENTIVE_HEADING_ID} subtitle={GLOBAL_PREVENTIVE_SUBTITLE} />
      <MaintenanceViews current="preventive" query={query} />
      <GlobalWorkBar page={page} label="Preventive window" membership={PREVENTIVE_MEMBERSHIP} dueDates />
      <PreventiveStrip summary={shown ? summaryOf(body) : null} />
      <GlobalWorkSlot page={page} loading={GLOBAL_PREVENTIVE_LOADING} cards={(value) => <Cards body={value} />} />
      <Panel heading="Preventive plan" headingId={TABLE_HEADING_ID} description={PREVENTIVE_PLAN_FOOTER}>
        {shown && body !== null ? (
          body.total_count === 0 ? (
            <div className="global-work-empty" data-global-work-zero>
              <p>{NO_PREVENTIVE_PLANS}</p>
              <p>{CHANGE_WINDOW}</p>
            </div>
          ) : (
            <>
              <p className="global-work-scroll-hint" data-global-work-scroll-hint>
                {SCROLL_TABLE}
              </p>
              <PlanTable body={body} />
              <Pager
                label="Preventive pages"
                body={body}
                trail={trail}
                cursor={query?.cursor ?? null}
                onPage={(cursor, nextTrail) => query && page.go(query, cursor, nextTrail)}
              />
            </>
          )
        ) : null}
      </Panel>
      <Notice tone="blue" data={{ "data-global-work-notice": "" }}>
        <p>{PREVENTIVE_NOTICE}</p>
      </Notice>
    </div>
  );
}

/** The routed frame: the page in its `<main>` landmark, named by the page heading. */
export function GlobalPreventiveFrame({ client }: { client?: GlobalWorkClient }) {
  return (
    <main aria-labelledby={GLOBAL_PREVENTIVE_HEADING_ID}>
      <GlobalPreventivePage client={client} />
    </main>
  );
}
