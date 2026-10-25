/**
 * W6-01a A2: the global Incidents root (v6.9 `incidents`), read from `GET /api/work/incidents`
 * (`global-work-index-1`). The mock's slots, in order: page header, the four cards, the `Incident cases` panel and
 * the `Case boundaries` panel (`screens.js:514-517`). Copy follows `.agent/W6-01-build-spec.md` section 2 and the
 * section 3.1 A2Q rulings: cards from `state_counts` (A2Q1), the work provenance line (A2Q4), a URL-only cutoff
 * (A2Q5), the refusal table (A2Q6), the footer as the panel sub-line (A2Q7), the cell literals (A2Q8) and the
 * cursor plus `globalWorkTrail` pager (A2Q10). W6-01b P-B2-1 moved the shared parts to `globalWorkParts.tsx`.
 *
 * A refusal, a read failure, an empty scope or a changed list is stated and never shown as zero. Severity is not
 * recorded on work cases. No mock case or ID is rendered.
 */
import { Link } from "react-router-dom";
import { stateTone } from "../sites/siteWorkCases";
import { Breadcrumbs, DataTable, MetricCard, MetricCards, PageHeader, Panel } from "../ui";
import {
  globalWorkUtc,
  type GlobalIncidentRow,
  type GlobalIncidentState,
  type GlobalIncidentsBody,
  type GlobalWorkClient,
} from "./globalWorkClient";
import {
  CHANGE_WINDOW,
  Clamp,
  GlobalWorkBar,
  GlobalWorkSlot,
  LinkOrText,
  MockDeviation,
  findingLinks,
  Pager,
  SCROLL_TABLE,
  WorkSourceLine,
  joined,
  useGlobalWorkPage,
} from "./globalWorkParts";
import "./globalWork.css";

// W6-01b P-B2-1: the shared parts moved to `globalWorkParts.tsx`; these names stay importable from this page.
export { NO_ACCESSIBLE_SITES, CHANGE_WINDOW, SCROLL_TABLE, WORK_PROVENANCE_WORDS, WorkSourceLine } from "./globalWorkParts";

/** The page path; the route constant `INCIDENTS_PATH` in `shell/operatorSiteRoutes.ts` has the same value. */
const PAGE_PATH = "/incidents";
export const GLOBAL_INCIDENTS_HEADING_ID = "global-incidents-heading";
const TABLE_HEADING_ID = "global-incidents-cases-heading";

export const GLOBAL_INCIDENTS_SUBTITLE = "Operational event cases · linked Findings and work";
export const GLOBAL_INCIDENTS_LOADING = "Loading the incidents across the estate.";
export const INCIDENT_CASES_FOOTER = "An incident connects authored events and linked records; a gap alone does not create a case.";
export const CASE_BOUNDARIES_TEXT = "A closed case records a workflow step. Cause and outcome need their own evidence.";
export const NO_INCIDENT_CASES = "No incident cases in this window.";
/** Post-W6 W6 Q7: the stored time that places an Incident in the window. */
export const INCIDENTS_MEMBERSHIP = "Listed by incident start time.";

/** A2Q8: copied, because `STATE_LABEL` in `siteWorkCases.tsx` is not exported. */
const STATE_LABEL: Readonly<Record<GlobalIncidentState, string>> = {
  OPEN: "Open",
  IN_PROGRESS: "In progress",
  CLOSED: "Closed",
};

function FindingsWork({ row }: { row: GlobalIncidentRow }) {
  const links = [...findingLinks(row.finding_links, row.site_domain), ...row.action_links];
  if (links.length === 0 && row.linked_requests.length === 0) return <Clamp>None linked</Clamp>;
  const linkParts = links.map((link, index) => (
    <LinkOrText key={`${link.label}-${index}`} link={link} data={{ "data-global-work-link": "" }} />
  ));
  // Post-W6 W6 Q4 (R359): each linked request code opens that request's exact Overview, or stays legible as text.
  const requestParts = row.linked_requests.map((link, index) => (
    <LinkOrText key={`${link.label}-${index}`} link={link} data={{ "data-global-work-request-link": "" }} />
  ));
  return (
    <Clamp data={{ "data-global-work-findings": "" }}>
      {joined(linkParts, " · ")}
      {requestParts.length > 0 ? (
        <>
          {links.length > 0 ? " / " : null}
          <span data-global-work-request-codes>{joined(requestParts, " · ")}</span>
        </>
      ) : null}
    </Clamp>
  );
}

/** A2Q8: the Site Work chip (same badge class and `stateTone`), with the copied label map. */
function StateChip({ state }: { state: GlobalIncidentState }) {
  const tone = stateTone("incidents", state);
  return (
    <span
      className={`w1f4-action-badge${tone === "neutral" ? "" : ` w1f4-action-badge--${tone}`}`}
      data-global-work-state={state}
      data-global-work-tone={tone}
    >
      {STATE_LABEL[state] ?? state}
    </span>
  );
}

function IncidentRow({ row }: { row: GlobalIncidentRow }) {
  const text = `${row.code} · ${row.title}`;
  return (
    <tr data-global-work-row={row.case_id}>
      <td>
        <Clamp data={{ "data-global-work-title": "" }}>
          {row.links.site_incidents.href ? <Link to={row.links.site_incidents.href}>{text}</Link> : text}
        </Clamp>
        <details className="global-work-details" data-global-work-full-title>
          <summary>Full title text</summary>
          {row.title}
        </details>
        <WorkSourceLine provenance={row.source_provenance} />
      </td>
      <td>
        <Clamp>
          <LinkOrText link={row.links.site} data={{ "data-global-work-site": row.site_code }} />
        </Clamp>
      </td>
      <td>
        <Clamp>{globalWorkUtc(row.occurred_at)}</Clamp>
      </td>
      <td>
        <Clamp>Not recorded</Clamp>
      </td>
      <td>
        <StateChip state={row.state} />
      </td>
      <td>
        <Clamp data={{ "data-global-work-owner": "" }}>{row.owner ?? "Not assigned"}</Clamp>
      </td>
      <td>
        <FindingsWork row={row} />
      </td>
    </tr>
  );
}

const COLUMNS = ["Incident", "Site", "Start", "Severity", "State", "Owner", "Findings / work"];
const WIDTHS = [26, 12, 13, 10, 10, 13, 16];

function IncidentTable({ body }: { body: GlobalIncidentsBody }) {
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
          <IncidentRow key={`${row.site_id}/${row.case_id}`} row={row} />
        ))}
      </tbody>
    </DataTable>
  );
}

function Cards({ body }: { body: GlobalIncidentsBody }) {
  const open = body.state_counts.OPEN + body.state_counts.IN_PROGRESS;
  return (
    <MetricCards label="Incidents summary" data={{ "data-global-work-cards": "" }}>
      <MetricCard
        label="Open incidents"
        value={String(open)}
        note="Open or in progress in this window"
        data={{ "data-global-work-card": "open" }}
      />
      <MetricCard
        label="High severity"
        value="Not assessed"
        word
        note="Severity is not recorded on work cases"
        data={{ "data-global-work-card": "high_severity" }}
      />
      <MetricCard
        label="Awaiting evidence"
        value="Not assessed"
        word
        note="No case evidence review state"
        data={{ "data-global-work-card": "awaiting_evidence" }}
      />
      <MetricCard
        label="Closed verified"
        value="Not assessed"
        word
        note="Closed does not verify an outcome"
        data={{ "data-global-work-card": "closed_verified" }}
      />
    </MetricCards>
  );
}

export function GlobalIncidentsPage({ client }: { client?: GlobalWorkClient }) {
  const page = useGlobalWorkPage<GlobalIncidentsBody>(PAGE_PATH, client, (reads, query) => reads.incidents(query));
  const { body, shown, query, trail } = page;

  return (
    <div className="global-work" data-global-work-root="incidents">
      {/* Post-W6 W6 (R357): the same one-level trail as Maintenance. */}
      <Breadcrumbs trail={[{ label: "Incidents" }]} />
      <PageHeader title="Incidents" headingId={GLOBAL_INCIDENTS_HEADING_ID} subtitle={GLOBAL_INCIDENTS_SUBTITLE} />
      {/* The shared control bar and the status line sit in the page's date-bar slot (estate precedent). */}
      <GlobalWorkBar page={page} label="Incidents window" membership={INCIDENTS_MEMBERSHIP} />
      <GlobalWorkSlot
        page={page}
        loading={GLOBAL_INCIDENTS_LOADING}
        cards={(value) => <Cards body={value} />}
      />
      <Panel heading="Incident cases" headingId={TABLE_HEADING_ID} description={INCIDENT_CASES_FOOTER}>
        {shown && body !== null ? (
          body.total_count === 0 ? (
            <div className="global-work-empty" data-global-work-zero>
              <p>{NO_INCIDENT_CASES}</p>
              <p>{CHANGE_WINDOW}</p>
            </div>
          ) : (
            <>
              <p className="global-work-scroll-hint" data-global-work-scroll-hint>
                {SCROLL_TABLE}
              </p>
              <IncidentTable body={body} />
              <Pager
                label="Incident pages"
                body={body}
                trail={trail}
                cursor={query?.cursor ?? null}
                onPage={(cursor, nextTrail) => query && page.go(query, cursor, nextTrail)}
              />
              {/* MOCK DEVIATION D1 (R73, extended to this screen with its R85 companion): the INC code opens the
                  Site's incidents window, not an Incident detail, because no Incident detail route is mounted. */}
              <MockDeviation category="D1" id="R73" />
            </>
          )
        ) : null}
        {/* MOCK DEVIATION D1 (R358): cards 2-4 and the Severity column state "Not assessed" / "Not recorded"
            because work cases record no severity or evidence review state. */}
        {shown ? <MockDeviation category="D1" id="R358" /> : null}
      </Panel>
      <Panel heading="Case boundaries" headingId="global-incidents-boundaries-heading">
        <p className="prose global-work-prose" data-global-work-boundaries>
          {CASE_BOUNDARIES_TEXT}
        </p>
      </Panel>
    </div>
  );
}

/** The routed frame: the page in its `<main>` landmark, named by the page heading. */
export function GlobalIncidentsFrame({ client }: { client?: GlobalWorkClient }) {
  return (
    <main aria-labelledby={GLOBAL_INCIDENTS_HEADING_ID}>
      <GlobalIncidentsPage client={client} />
    </main>
  );
}
