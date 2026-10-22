/**
 * W6-01a A2: the global Incidents root (v6.9 `incidents`), read from `GET /api/work/incidents`
 * (`global-work-index-1`). The mock's slots, in order: page header, the four cards, the `Incident cases` panel and
 * the `Case boundaries` panel (`screens.js:514-517`). Copy follows `.agent/W6-01-build-spec.md` section 2 and the
 * section 3.1 A2Q rulings: cards from `state_counts` (A2Q1), the work provenance line (A2Q4), a URL-only cutoff
 * (A2Q5), the refusal table (A2Q6), the footer as the panel sub-line (A2Q7), the cell literals (A2Q8) and the
 * cursor plus `globalWorkTrail` pager (A2Q10).
 *
 * A refusal, a read failure, an empty scope or a changed list is stated and never shown as zero. Severity is not
 * recorded on work cases. No mock case or ID is rendered.
 */
import { useEffect, useMemo, useState, type FormEvent, type ReactNode } from "react";
import { Link, useLocation, useNavigate, useSearchParams } from "react-router-dom";
import { stateTone } from "../sites/siteWorkCases";
import { DataTable, MetricCard, MetricCards, PageHeader, Panel } from "../ui";
import {
  GLOBAL_WORK_FIRST_PAGE_CODES,
  GLOBAL_WORK_PAGE_LIMIT,
  GLOBAL_WORK_REFUSAL_COPY,
  createGlobalWorkClient,
  globalWorkHref,
  globalWorkPageQuery,
  globalWorkUtc,
  type GlobalIncidentRow,
  type GlobalIncidentState,
  type GlobalIncidentsBody,
  type GlobalWorkClient,
  type GlobalWorkLink,
  type GlobalWorkProvenance,
  type GlobalWorkQuery,
  type GlobalWorkRefusalCode,
  type GlobalWorkResult,
} from "./globalWorkClient";
import "./globalWork.css";

/** The page path; the route constant `INCIDENTS_PATH` in `shell/operatorSiteRoutes.ts` has the same value. */
const PAGE_PATH = "/incidents";
export const GLOBAL_INCIDENTS_HEADING_ID = "global-incidents-heading";
const TABLE_HEADING_ID = "global-incidents-cases-heading";

export const GLOBAL_INCIDENTS_SUBTITLE = "Operational event cases · linked Findings and work";
export const GLOBAL_INCIDENTS_LOADING = "Loading the incidents across the estate.";
export const INCIDENT_CASES_FOOTER = "An incident connects authored events and linked records; a gap alone does not create a case.";
export const CASE_BOUNDARIES_TEXT = "A closed case records a workflow step. Cause and outcome need their own evidence.";
export const NO_ACCESSIBLE_SITES = "No accessible Sites.";
export const NO_INCIDENT_CASES = "No incident cases in this window.";
export const CHANGE_WINDOW = "Change the UTC window or open a Site record.";
export const SCROLL_TABLE = "Scroll table horizontally";

/** Section 2: the four work provenance pairs, chosen by `source_provenance.classification` (A2Q4). */
export const WORK_PROVENANCE_WORDS: Readonly<Record<string, [string, string]>> = {
  AUTHORED_DEMONSTRATION: [
    "Prepared example data",
    "These authored work records were prepared for an example. They are not physical equipment readings.",
  ],
  REGISTERED_SIMULATION: [
    "Generated test data",
    "These authored work records came from a registered simulation. They are not physical equipment readings.",
  ],
  MIXED: ["Sources do not agree", "The selected links do not establish one work source. No work outcome is verified."],
  UNKNOWN: [
    "Source unverified",
    "The origin of this authored work record is not established. No work outcome is verified.",
  ],
};

/** A2Q8: copied, because `STATE_LABEL` in `siteWorkCases.tsx` is not exported. */
const STATE_LABEL: Readonly<Record<GlobalIncidentState, string>> = {
  OPEN: "Open",
  IN_PROGRESS: "In progress",
  CLOSED: "Closed",
};

/** Earlier pages' cursors (null is page one), newest last; history state `globalWorkTrail` (A2Q10). */
type Trail = (string | null)[];

function readTrail(state: unknown): Trail {
  const trail = (state as { globalWorkTrail?: unknown } | null)?.globalWorkTrail;
  return Array.isArray(trail) && trail.every((c) => c === null || typeof c === "string") ? (trail as Trail) : [];
}

function Clamp({ children, data }: { children: ReactNode; data?: Record<string, string> }) {
  return (
    <div className="global-work-clamp" {...data}>
      {children}
    </div>
  );
}

function LinkOrText({ link, data }: { link: GlobalWorkLink; data?: Record<string, string> }) {
  return link.href ? (
    <Link to={link.href} {...data}>
      {link.label}
    </Link>
  ) : (
    <span {...data}>{link.label}</span>
  );
}

export function WorkSourceLine({ provenance }: { provenance: GlobalWorkProvenance }) {
  const [label, explanation] = WORK_PROVENANCE_WORDS[provenance.classification] ?? WORK_PROVENANCE_WORDS.UNKNOWN;
  return (
    <details className="global-work-details" data-global-work-source={provenance.classification}>
      <summary>{label}</summary>
      {explanation}
    </details>
  );
}

function joined(parts: ReactNode[], separator: string): ReactNode[] {
  return parts.flatMap((part, index) => (index === 0 ? [part] : [separator, part]));
}

function FindingsWork({ row }: { row: GlobalIncidentRow }) {
  const links = [...row.finding_links, ...row.action_links];
  if (links.length === 0 && row.linked_request_codes.length === 0) return <Clamp>None linked</Clamp>;
  const linkParts = links.map((link, index) => (
    <LinkOrText key={`${link.label}-${index}`} link={link} data={{ "data-global-work-link": "" }} />
  ));
  return (
    <Clamp data={{ "data-global-work-findings": "" }}>
      {joined(linkParts, " · ")}
      {row.linked_request_codes.length > 0 ? (
        <>
          {links.length > 0 ? " / " : null}
          <span data-global-work-request-codes>{row.linked_request_codes.join(" · ")}</span>
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

/** A2Q6: one refusal sentence, with `Reload the first page` for a changed list or a stale cursor. */
function RefusalBlock({ code, firstPage }: { code: GlobalWorkRefusalCode; firstPage: string }) {
  return (
    <div className="notice v69-notice global-work-state" data-global-work-refusal={code} data-page-refusal={code}>
      <p>{GLOBAL_WORK_REFUSAL_COPY[code]}</p>
      {GLOBAL_WORK_FIRST_PAGE_CODES.has(code) ? (
        <p>
          <Link to={firstPage} data-global-work-first-page>
            Reload the first page
          </Link>
        </p>
      ) : null}
    </div>
  );
}

function dateOf(instant: string | null): string {
  return instant && /^\d{4}-\d{2}-\d{2}T/.test(instant) ? instant.slice(0, 10) : "";
}

/** The shared control bar (section 2): `From (UTC)`, `To (UTC, exclusive)`, `Show records`, `Reload`. */
function ControlBar({
  from,
  to,
  onShow,
  onReload,
}: {
  from: string;
  to: string;
  onShow: (from: string, to: string) => void;
  onReload: () => void;
}) {
  const [first, setFirst] = useState(from);
  const [last, setLast] = useState(to);
  const submit = (event: FormEvent) => {
    event.preventDefault();
    if (!first || !last) return;
    onShow(`${first}T00:00:00Z`, `${last}T00:00:00Z`);
  };
  return (
    <form className="global-work-controls" onSubmit={submit} data-global-work-controls aria-label="Incidents window">
      <label className="global-work-controls__field">
        {"From (UTC) "}
        <input className="v69-chip-control" type="date" value={first} onChange={(e) => setFirst(e.target.value)} />
      </label>
      <label className="global-work-controls__field">
        {"To (UTC, exclusive) "}
        <input className="v69-chip-control" type="date" value={last} onChange={(e) => setLast(e.target.value)} />
      </label>
      <button className="button" type="submit" data-global-work-show>
        Show records
      </button>
      <button className="button" type="button" onClick={onReload} data-global-work-reload>
        Reload
      </button>
    </form>
  );
}

function StatusLine({ body }: { body: GlobalIncidentsBody }) {
  const text =
    body.status === "HISTORICAL" ? `Historical as of ${globalWorkUtc(body.known_at)}` : `As known at ${globalWorkUtc(body.known_at)}`;
  return (
    <p className="global-work-status" data-global-work-status={body.status}>
      {text}
    </p>
  );
}

function Pager({
  body,
  trail,
  cursor,
  onPage,
}: {
  body: GlobalIncidentsBody;
  trail: Trail;
  cursor: string | null;
  onPage: (cursor: string | null, trail: Trail) => void;
}) {
  const a = trail.length * GLOBAL_WORK_PAGE_LIMIT + 1;
  const b = a + body.rows.length - 1;
  return (
    <nav className="global-work-pager" aria-label="Incident pages" data-global-work-pager>
      <span data-global-work-showing>{`Showing ${a}–${b} of ${body.total_count}`}</span>
      {cursor !== null ? (
        <button
          type="button"
          className="link-button"
          data-global-work-previous
          onClick={() => onPage(trail.length > 0 ? trail[trail.length - 1] : null, trail.slice(0, -1))}
        >
          Previous
        </button>
      ) : null}
      {body.next_cursor !== null ? (
        <button
          type="button"
          className="link-button"
          data-global-work-next
          onClick={() => onPage(body.next_cursor, [...trail, cursor])}
        >
          Next
        </button>
      ) : null}
    </nav>
  );
}

type Read = GlobalWorkResult<GlobalIncidentsBody>;

export function GlobalIncidentsPage({ client }: { client?: GlobalWorkClient }) {
  const reads = useMemo(() => client ?? createGlobalWorkClient(), [client]);
  const [params] = useSearchParams();
  const location = useLocation();
  const navigate = useNavigate();
  const parsed = globalWorkPageQuery(params);
  const query: GlobalWorkQuery | null = parsed.status === "valid" ? parsed.query : null;
  const trail = readTrail(location.state);
  const key = query === null ? "" : JSON.stringify(query);
  const [nonce, setNonce] = useState(0);
  const [result, setResult] = useState<{ key: string; nonce: number; read: Read } | null>(null);

  useEffect(() => {
    if (query === null) return undefined;
    let live = true;
    void reads.incidents(query).then((read) => {
      if (live) setResult({ key, nonce, read });
    });
    return () => {
      live = false;
    };
    // `key` carries the whole page query; `nonce` is a Reload of the same query.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [reads, key, nonce]);

  const go = (next: Pick<GlobalWorkQuery, "from" | "to" | "known_at">, cursor: string | null, nextTrail: Trail) =>
    navigate(globalWorkHref(PAGE_PATH, next, cursor), { state: { globalWorkTrail: nextTrail } });

  const read = query !== null && result?.key === key && result.nonce === nonce ? result.read : null;
  const body = read?.status === "loaded" ? read.value : null;
  const shown = body !== null && (body.status === "CURRENT" || body.status === "HISTORICAL");
  const firstPage = query === null ? PAGE_PATH : globalWorkHref(PAGE_PATH, query);
  const rawFrom = params.get("from");
  const rawTo = params.get("to");

  let slot: ReactNode;
  if (parsed.status === "invalid") {
    slot = <RefusalBlock code={parsed.code} firstPage={firstPage} />;
  } else if (read === null) {
    slot = (
      <p className="global-work-loading" data-global-work-loading>
        {GLOBAL_INCIDENTS_LOADING}
      </p>
    );
  } else if (read.status === "refused") {
    slot = <RefusalBlock code={read.code} firstPage={firstPage} />;
  } else if (read.value.status === "EMPTY_SCOPE") {
    slot = (
      // `data-page-refusal` is the panel-structure test's leading-state hook; EMPTY_SCOPE is stated, never a zero.
      <div className="notice v69-notice global-work-state" data-global-work-empty-scope data-page-refusal="EMPTY_SCOPE">
        <p>{NO_ACCESSIBLE_SITES}</p>
      </div>
    );
  } else if (shown) {
    slot = <Cards body={read.value} />;
  } else {
    // A status this read never produces (PARTIAL is reserved): stated, never shown as zero.
    slot = <RefusalBlock code="WORK_STORE_UNAVAILABLE" firstPage={firstPage} />;
  }

  return (
    <div className="global-work" data-global-work-root="incidents">
      <PageHeader title="Incidents" headingId={GLOBAL_INCIDENTS_HEADING_ID} subtitle={GLOBAL_INCIDENTS_SUBTITLE} />
      {/* The shared control bar and the status line sit in the page's date-bar slot (estate precedent). */}
      <div className="site-date-bar global-work-bar" data-global-work-bar>
        <ControlBar
          key={`${rawFrom ?? query?.from ?? ""}|${rawTo ?? query?.to ?? ""}`}
          from={query ? dateOf(query.from) : dateOf(rawFrom)}
          to={query ? dateOf(query.to) : dateOf(rawTo)}
          onShow={(from, to) => go({ from, to, known_at: query?.known_at ?? null }, null, [])}
          onReload={() => {
            if (query === null) return;
            if (query.cursor === null && trail.length === 0) setNonce((n) => n + 1);
            else go(query, null, []);
          }}
        />
        {body !== null ? <StatusLine body={body} /> : null}
      </div>
      {slot}
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
                body={body}
                trail={trail}
                cursor={query?.cursor ?? null}
                onPage={(cursor, nextTrail) => query && go(query, cursor, nextTrail)}
              />
            </>
          )
        ) : null}
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
