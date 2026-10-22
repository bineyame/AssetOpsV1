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
 */
import { Breadcrumbs, DataTable, MetricCard, MetricCards, Notice, PageHeader, Panel, StatusBar } from "../ui";
import { UnavailableInline } from "../ui/UnavailableEntry";
import { MaintenanceViews } from "./GlobalMaintenance";
import {
  globalWorkHref,
  type GlobalPreventiveBody,
  type GlobalPreventiveRow,
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

export const GLOBAL_PREVENTIVE_SUBTITLE = "Scheduled maintenance by calendar or running hours";
export const GLOBAL_PREVENTIVE_LOADING = "Loading the preventive plans across the estate.";
export const PREVENTIVE_STRIP_BADGE = "Due status not assessed";
export const PREVENTIVE_STRIP_TEXT = "Scheduled by calendar or running hours · due dates are plan facts";
export const PREVENTIVE_PLAN_FOOTER =
  "Completing a draft plan here is unavailable; a performed record and later evidence are separate.";
export const PREVENTIVE_NOTICE = "No incident link or cause is established by these draft plans.";
export const NO_DRAFT_PLANS = "No draft plans in this window.";

const DATE_ONLY = new Intl.DateTimeFormat("en-GB", { day: "numeric", month: "short", year: "numeric", timeZone: "UTC" });

/** P-B3-6: `29 Oct 2026` (en-GB, UTC date of the authored due instant, no local-zone conversion). */
function dueDate(instant: string): string {
  const ms = Date.parse(instant);
  return Number.isNaN(ms) ? instant : DATE_ONLY.format(new Date(ms));
}

function trigger(row: GlobalPreventiveRow): string {
  if (row.trigger_kind === "CALENDAR") return "Calendar";
  return row.next_due_hours === null ? "Running hours" : `Every ${row.next_due_hours} running hours`;
}

function nextDue(row: GlobalPreventiveRow): string {
  if (row.next_due_at !== null) return dueDate(row.next_due_at);
  if (row.next_due_hours !== null) return `${row.next_due_hours} running hours`;
  return "Not set";
}

function PlanRow({ row }: { row: GlobalPreventiveRow }) {
  return (
    <tr data-global-work-row={row.root_id}>
      <td>
        <Clamp data={{ "data-global-work-title": "" }}>{`${row.code} · ${row.title}`}</Clamp>
        <details className="global-work-details" data-global-work-full-title>
          <summary>Full title text</summary>
          {row.title}
        </details>
        {row.correction_reason !== null ? (
          <>
            <Clamp data={{ "data-global-work-correction": "" }}>{`Correction: ${row.correction_reason}`}</Clamp>
            {row.supersedes_plan_id !== null ? (
              <details className="global-work-details" data-global-work-supersedes>
                <summary>Earlier plan version</summary>
                {row.supersedes_plan_id}
              </details>
            ) : null}
          </>
        ) : null}
        <WorkSourceLine provenance={row.source_provenance} />
      </td>
      <td>
        <Clamp data={{ "data-global-work-asset-site": "" }}>
          {row.asset_label ?? "No asset recorded"}
          {" · "}
          <LinkOrText link={row.links.site} data={{ "data-global-work-site": row.site_code }} />
        </Clamp>
      </td>
      <td>
        <Clamp data={{ "data-global-work-trigger": "" }}>{trigger(row)}</Clamp>
      </td>
      <td>
        <Clamp>Not linked</Clamp>
      </td>
      <td>
        <Clamp data={{ "data-global-work-due": "" }}>{nextDue(row)}</Clamp>
      </td>
      <td>
        <span className="w1f4-action-badge" data-global-work-state={row.state} data-global-work-tone="neutral">
          Draft
        </span>
      </td>
      <td>
        <Clamp>Nothing verified by this plan</Clamp>
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
  return (
    <MetricCards label="Preventive summary" data={{ "data-global-work-cards": "" }}>
      <MetricCard
        label="Scheduled items"
        value={String(body.total_count)}
        note={`Across ${body.scope.covered_site_count} sites`}
        data={{ "data-global-work-card": "scheduled_items" }}
      />
      <MetricCard
        label="Overdue"
        value="Not assessed"
        assessment
        tone="amber"
        note="No due evaluator"
        data={{ "data-global-work-card": "overdue" }}
      />
      <MetricCard label="Due in 14 days" value="Not assessed" word note="No due evaluator" data={{ "data-global-work-card": "due_14" }} />
      <MetricCard
        label="Feeds evidence"
        value="Not established"
        word
        note="No accepted-evidence link"
        data={{ "data-global-work-card": "feeds_evidence" }}
      />
    </MetricCards>
  );
}

/** P-B3-4: the mock status strip between the date bar and the cards; its right `Assets` slot is unavailable. */
function PreventiveStrip() {
  return (
    <StatusBar
      label="Preventive status"
      other={PREVENTIVE_STRIP_TEXT}
      action={<UnavailableInline label="Assets" />}
      data={{ "data-global-work-strip": "" }}
    >
      <span className="w1f4-action-badge w1f4-action-badge--amber" data-global-work-tone="amber">
        {PREVENTIVE_STRIP_BADGE}
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
      <GlobalWorkBar page={page} label="Preventive window" />
      <PreventiveStrip />
      <GlobalWorkSlot page={page} loading={GLOBAL_PREVENTIVE_LOADING} cards={(value) => <Cards body={value} />} />
      <Panel heading="Preventive plan" headingId={TABLE_HEADING_ID} description={PREVENTIVE_PLAN_FOOTER}>
        {shown && body !== null ? (
          body.total_count === 0 ? (
            <div className="global-work-empty" data-global-work-zero>
              <p>{NO_DRAFT_PLANS}</p>
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
