/**
 * W6-01b B2: the global Maintenance root, Corrective view (v6.9 `maintenance`), read from `GET /api/work/maintenance`
 * (`global-work-index-1`). The mock's slots, in order (`index.html:959-961`): breadcrumb, h1 and subtitle, the
 * `Corrective` / `Preventive · scheduled` view tabs, the date bar, the four cards, the `Corrective work requests`
 * panel and the blue lifecycle notice. Copy follows `.agent/W6-01-build-spec.md` section 2, section 3.1 (A2Q1,
 * A2Q4-A2Q7, A2Q10, X1-X8, CL3-1) and the "B1-B3 pre-flight rulings" P-B2-3..11, which supersede them.
 *
 * MOCK DEVIATION (P-B2-3..8): the lifecycle notice copy changes, because W4 has no work-outcome evaluator or
 * automated follow-up; the primary Work request link opens the same-window Site maintenance page until W6-01c mounts
 * the exact request Overview. A refusal, a read failure, an empty scope or a changed list is stated, never zero.
 */
import { Link } from "react-router-dom";
import { stateTone } from "../sites/siteWorkCases";
import { Breadcrumbs, DataTable, MetricCard, MetricCards, Notice, PageHeader, Panel } from "../ui";
import { UnavailableInline, UnavailableTab } from "../ui/UnavailableEntry";
import {
  type GlobalMaintenanceBody,
  type GlobalMaintenanceRow,
  type GlobalMaintenanceState,
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
  joined,
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

const STATE_LABEL: Readonly<Record<GlobalMaintenanceState, string>> = {
  OPEN: "Open",
  IN_PROGRESS: "In progress",
  COMPLETED: "Completed",
  CANCELLED: "Cancelled",
};

/**
 * The `Maintenance views` tab row between the header and the date bar (P-B2-9, mock `MAINT_GTABS`). Corrective is
 * the current view (plain text, `aria-current`); until W6-01b B3 the Preventive view is one `UnavailableTab` (F4: the
 * label is written with the HTML entity so the navigation guard compares ASCII).
 */
export function MaintenanceViews() {
  return (
    <nav aria-label="Maintenance views" className="site-tabs global-work-tabs" data-global-work-tabs>
      <ul className="site-tabs__list">
        <li className="site-tabs__item">
          <span className="site-tabs__link" aria-current="page" data-global-work-tab="corrective">
            Corrective
          </span>
        </li>
        <UnavailableTab label="Preventive &middot; scheduled" />
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
  // Until W6-01c mounts the exact request, the primary link opens the same-window Site maintenance page (X8).
  const href = row.links.detail?.href ?? row.links.site_maintenance.href;
  const links = [...row.finding_links, ...row.action_links];
  return (
    <>
      <Clamp data={{ "data-global-work-title": "" }}>{href ? <Link to={href}>{text}</Link> : text}</Clamp>
      <details className="global-work-details" data-global-work-full-title>
        <summary>Full title text</summary>
        {row.title}
      </details>
      <Clamp data={{ "data-global-work-lineage": links.length > 0 ? "linked" : "none" }}>
        {links.length > 0
          ? joined(
              links.map((link, index) => (
                <LinkOrText key={`${link.label}-${index}`} link={link} data={{ "data-global-work-link": "" }} />
              )),
              " · ",
            )
          : NO_LINKED_FINDING_OR_ACTION}
      </Clamp>
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
        <Clamp data={{ "data-global-work-asset-site": "" }}>
          {row.asset_label ?? "No asset recorded"}
          {" · "}
          <LinkOrText link={row.links.site} data={{ "data-global-work-site": row.site_code }} />
        </Clamp>
      </td>
      <td>
        <Clamp data={{ "data-global-work-owner": "" }}>{row.owner ?? "Not assigned"}</Clamp>
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

/** P-B2-4: the mock's separate `View detail →` slot on the third card; unavailable until Preventive is live. */
function PreventiveCardNote() {
  return (
    <>
      <span data-global-work-preventive-note>See Preventive</span>
      <span className="global-work-card-link" data-global-work-preventive-link>
        <UnavailableInline label="View detail" />
      </span>
    </>
  );
}

function Cards({ body }: { body: GlobalMaintenanceBody }) {
  const open = body.state_counts.OPEN + body.state_counts.IN_PROGRESS;
  return (
    <MetricCards label="Maintenance summary" data={{ "data-global-work-cards": "" }}>
      <MetricCard
        label="Open work"
        value={String(open)}
        note={`${open} requests in progress or open`}
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
        note={<PreventiveCardNote />}
        data={{ "data-global-work-card": "preventive_due" }}
      />
      <MetricCard
        label="Repeat findings"
        value="Not assessed"
        word
        note="No repeat-finding assessment"
        data={{ "data-global-work-card": "repeat_findings" }}
      />
    </MetricCards>
  );
}

export function GlobalMaintenancePage({ client }: { client?: GlobalWorkClient }) {
  const page = useGlobalWorkPage<GlobalMaintenanceBody>(PAGE_PATH, client, (reads, query) =>
    reads.maintenance ? reads.maintenance(query) : null,
  );
  const { body, shown, query, trail } = page;

  return (
    <div className="global-work global-work--maintenance" data-global-work-root="maintenance">
      <Breadcrumbs trail={[{ label: "Maintenance" }]} />
      <PageHeader title="Maintenance" headingId={GLOBAL_MAINTENANCE_HEADING_ID} subtitle={GLOBAL_MAINTENANCE_SUBTITLE} />
      <MaintenanceViews />
      <GlobalWorkBar page={page} label="Maintenance window" />
      <GlobalWorkSlot page={page} loading={GLOBAL_MAINTENANCE_LOADING} cards={(value) => <Cards body={value} />} />
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
            </>
          )
        ) : null}
      </Panel>
      <Notice tone="blue" data={{ "data-global-work-notice": "" }}>
        <p>{MAINTENANCE_NOTICE}</p>
      </Notice>
    </div>
  );
}

/** The routed frame: the page in its `<main>` landmark, named by the page heading. */
export function GlobalMaintenanceFrame({ client }: { client?: GlobalWorkClient }) {
  return (
    <main aria-labelledby={GLOBAL_MAINTENANCE_HEADING_ID}>
      <GlobalMaintenancePage client={client} />
    </main>
  );
}
