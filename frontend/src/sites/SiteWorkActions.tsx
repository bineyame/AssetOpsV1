/**
 * S6-03 (`sitework:1#a`, `I-sitework-ui`): Site > Work > Actions over the
 * Site Action index read (`GET /api/sites/{site}/action-index`).
 *
 * Follows v6.9's Site Work screen: a scope line, one "Actions at this site"
 * table and a note that opening a record moves to its own page. The window
 * (UTC days, end excluded) and page cursor live in the URL, owned by the frame.
 *
 * - No window in the URL: a choose-window state; nothing is read or counted.
 * - A loaded read: rows newest-created first, or an explicit zero that says
 *   only "no Action was created here in this window".
 * - A refusal (changed list, invalid window, sign-in, access, unavailable or
 *   inconsistent store) shows no rows and no count, and never reads as zero.
 *
 * W1-F4 (`D-2026-10-17-mockup-layout-spec`): the v69 `sitework` layout. A
 * one-line status strip ("Scoped to <site> · N Actions", the read state and
 * read time), then the single "Actions at this site" panel holding the window
 * chips (in the panel header), the table or the in-panel state, and one
 * panel-foot note. Past four rows the rest stay in the page, hidden behind a
 * "Show all N Actions" toggle. The former
 * W1-UX-04 answer card is merged into the strip and the panel; there is no
 * separate top card. There is no global Actions list in this build, so the
 * strip has no "Manage in Actions" link.
 *
 * The default reading is plain; IDs, the selection rule and the list's fence
 * sit in a "What this list is based on" disclosure. Owner, due date, priority,
 * success criterion and any verification verdict are not shown: this read has
 * none of them, and the list derives none.
 */
import { useEffect, useRef, useState, type FormEvent, type ReactNode } from "react";
import { Link } from "react-router-dom";

import { ChartNote, DataTable, Disclosure, Fact, FactList, Notice, Panel, RailIcon, readResultWords, type ProductWords } from "../ui";
import type { ActionIndexBody, ActionIndexClient, ActionIndexResult, ActionIndexRow, ActionIndexScope } from "./actionIndexClient";
import {
  COLD_DOMAIN,
  EV_DOMAIN,
  invalidScope,
  isUtcInstant,
  type DomainActionClient,
  type DomainActionDomain,
  type DomainIndexBody,
  type DomainIndexResult,
  type DomainIndexRow,
  type DomainIndexScope,
  type DomainStatus,
} from "./domainActionClient";
import {
  COLD_CRITERION_MISSING,
  COLD_DUE_MISSING,
  COLD_OWNER_MISSING,
  COLD_STATE_OPEN,
  COLD_WORK_DUE_UNSET,
  COLD_WORK_EMPTY,
  COLD_WORK_GLOBAL_GAP,
  COLD_WORK_LOADING,
  COLD_WORK_PANEL_TITLE,
  COLD_WORK_RETRY,
  COLD_WORK_STRIP_DETAIL,
  COLD_WORK_UNAVAILABLE,
  READ_FULL_TEXT,
  coldActionCount,
  coldCurrentnessNotice,
  coldCurrentnessTone,
  coldDueText,
  coldShowAll,
  isLongText,
} from "./coldWorkPresentation";
import {
  EV_CRITERION_MISSING,
  EV_ACTION_LINK_LIVE,
  evActionHref,
  EV_DUE_MISSING,
  EV_OWNER_MISSING,
  EV_SOURCE_FINDING_UNAVAILABLE,
  EV_STATE_OPEN,
  EV_WORK_DUE_UNSET,
  EV_WORK_EMPTY,
  EV_WORK_GLOBAL_GAP,
  EV_WORK_LOADING,
  EV_WORK_PANEL_TITLE,
  EV_WORK_RETRY,
  EV_WORK_STRIP_DETAIL,
  EV_WORK_UNAVAILABLE,
  evActionCount,
  evShowAll,
} from "./evWorkPresentation";
import { WORK_CONTEXT_NOTICE_DOMAIN, shortName } from "./siteWorkCases";
import "./w1f4-action.css";
import "./w1f4-changes-work.css";
import "./w4-work-cases.css";

export interface SiteWorkLinks {
  /** The same page at another scope (a new window, page one, or the next page). */
  scope: (scope: ActionIndexScope) => string;
  /** One Action's own page, at an exact event when given. */
  action: (actionId: string, eventId?: string | null) => string;
  /** The Action's history at an exact event. */
  history: (actionId: string, eventId: string) => string;
  /** One Finding at an exact revision. */
  finding: (findingId: string, revisionId: string) => string;
}

export interface SiteWorkActionsProps {
  siteId: string;
  siteName: string;
  client: ActionIndexClient;
  /** Null when the URL names no window: the choose-window state. */
  scope: ActionIndexScope | null;
  links: SiteWorkLinks;
  /** Apply a new window (a navigation, so reload and back keep it). */
  onScope: (scope: ActionIndexScope) => void;
}

const HEADING_ID = "site-work-actions-heading";
/** The v69 `sitework:1` panel title (`v69-rendered-panels.json`). */
export const SITE_WORK_PANEL_TITLE = "Actions at this site";

/** `2026-11-01 00:05 UTC` from an ISO instant. */
export function utcText(instant: string | null | undefined): string {
  if (!instant) return "none";
  const date = new Date(instant);
  if (Number.isNaN(date.getTime())) return instant;
  return `${date.toISOString().slice(0, 16).replace("T", " ")} UTC`;
}

/** `1 Nov 2026` for a UTC day. */
function dayText(instant: string): string {
  const date = new Date(instant);
  if (Number.isNaN(date.getTime())) return instant;
  return date.toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric", timeZone: "UTC" });
}

const dayOf = (instant: string) => new Date(instant).toISOString().slice(0, 10);
const lastDayOf = (to: string) => new Date(new Date(to).getTime() - 1).toISOString().slice(0, 10);

/** The recorded step, in plain words. Resolution steps are what the verification check recorded, not a list verdict. */
export const STEP_WORDS: Record<string, string> = {
  ACCEPTED: "Accepted",
  APPLIED: "Applied to the site setup",
  FAILED: "Apply attempt failed",
  OBSERVED: "Review note added",
  RESOLVED: "Trial closed by the verification check",
  RESOLUTION_WITHDRAWN: "Trial closure withdrawn; being checked again",
};

/** Where the Action stands, from the same lifecycle the Action page shows. */
export function stateWords(row: Pick<ActionIndexRow, "state">): string {
  const { state } = row;
  if (state.resolution?.state === "RESOLVED") return "Trial closed";
  if (state.resolution?.state === "RESOLUTION_WITHDRAWN") return "Being checked again";
  if (state.application === "APPLIED") return "Applied · result not checked yet";
  if (state.application === "PENDING") {
    return state.failed_attempts > 0
      ? `Accepted · not applied (${state.failed_attempts} failed ${state.failed_attempts === 1 ? "attempt" : "attempts"})`
      : "Accepted · not applied";
  }
  return state.application;
}

/** The State badge tone: closed is green, waiting on a step is amber, applied is blue. */
function stateTone(row: Pick<ActionIndexRow, "state">): "green" | "amber" | "blue" {
  if (row.state.resolution?.state === "RESOLVED") return "green";
  if (row.state.resolution?.state === "RESOLUTION_WITHDRAWN") return "amber";
  return row.state.application === "APPLIED" ? "blue" : "amber";
}

/** A default window for the chooser: the 30 UTC days ending today. */
function suggestedDays(now: Date = new Date()): { first: string; last: string } {
  const last = now.toISOString().slice(0, 10);
  const first = new Date(`${last}T00:00:00Z`);
  first.setUTCDate(first.getUTCDate() - 29);
  return { first: first.toISOString().slice(0, 10), last };
}

function WindowForm({ scope, onScope }: { scope: ActionIndexScope | null; onScope: (scope: ActionIndexScope) => void }) {
  const valid = scope !== null && !Number.isNaN(new Date(scope.from).getTime()) && !Number.isNaN(new Date(scope.to).getTime());
  const initial = valid && scope ? { first: dayOf(scope.from), last: lastDayOf(scope.to) } : suggestedDays();
  const [first, setFirst] = useState(initial.first);
  const [last, setLast] = useState(initial.last);
  useEffect(() => {
    if (valid && scope) {
      setFirst(dayOf(scope.from));
      setLast(lastDayOf(scope.to));
    }
  }, [scope, valid]);
  const submit = (event: FormEvent) => {
    event.preventDefault();
    if (!first || !last) return;
    const to = new Date(`${last}T00:00:00Z`);
    to.setUTCDate(to.getUTCDate() + 1);
    onScope({ from: `${first}T00:00:00Z`, to: `${to.toISOString().slice(0, 10)}T00:00:00Z`, limit: scope?.limit ?? null, cursor: null });
  };
  return (
    <form onSubmit={submit} className="v69-chips w1f4-work-window" data-site-work-window aria-label="Actions window">
      <label className="w1f4-work-window__field">
        {"Created from "}
        <input className="v69-chip-control" type="date" value={first} onChange={(event) => setFirst(event.target.value)} />
      </label>
      <label className="w1f4-work-window__field">
        {"to (included) "}
        <input className="v69-chip-control" type="date" value={last} onChange={(event) => setLast(event.target.value)} />
      </label>
      <button className="button" type="submit">
        Show Actions
      </button>
    </form>
  );
}

function Basis({ body }: { body: ActionIndexBody }) {
  return (
    <Disclosure name="site-work-basis" summary="What this list is based on">
      <FactList>
        <Fact term="Read at">{utcText(body.read_at)}</Fact>
        <Fact term="Window">
          {utcText(body.window.from)} to {utcText(body.window.to)} {body.window.bounds}; {body.window.membership}
        </Fact>
        <Fact term="Latest Action created">{utcText(body.fence.max_created_at)}</Fact>
        <Fact term="Latest step recorded">{utcText(body.fence.max_event_recorded_at)}</Fact>
        <Fact term="Actions and steps read">
          <span data-site-work-fence-counts>
            {body.fence.action_count} Actions, {body.fence.event_count} recorded steps
            {body.fence.zero_rows ? " (an explicit zero)" : ""}
          </span>
        </Fact>
        <Fact term="Order">
          <code data-vocabulary-exempt="source-reference">{body.order}</code>
        </Fact>
        <Fact term="Step shown">
          <code data-vocabulary-exempt="source-reference">{body.selection}</code>
        </Fact>
        <Fact term="List fence">
          <code data-site-work-fence data-vocabulary-exempt="source-reference">{body.fence.token}</code>
        </Fact>
      </FactList>
      {body.rows.length > 0 && (
        <DataTable labelledBy="site-work-ids-heading">
          <caption id="site-work-ids-heading">Record IDs on this page</caption>
          <thead>
            <tr>
              <th scope="col">Action</th>
              <th scope="col">Action ID</th>
              <th scope="col">Finding version ID</th>
              <th scope="col">Step ID</th>
            </tr>
          </thead>
          <tbody>
            {body.rows.map((row) => (
              <tr key={row.action_id}>
                <td>{row.action_code}</td>
                <td>
                  <code data-vocabulary-exempt="source-reference">{row.action_id}</code>
                </td>
                <td>
                  <code data-vocabulary-exempt="source-reference">{row.origin.finding_revision_id}</code>
                </td>
                <td>
                  <code data-vocabulary-exempt="source-reference">{row.selected_event.id}</code> (<code data-vocabulary-exempt="source-reference">{row.selected_event.kind}</code>)
                </td>
              </tr>
            ))}
          </tbody>
        </DataTable>
      )}
      <p>{body.not_included}</p>
    </Disclosure>
  );
}

/** Rows shown before "Show all": the mock's short table. The rest stay in the page, hidden until asked for. */
export const SITE_WORK_VISIBLE_ROWS = 4;

function Rows({ body, links, all }: { body: ActionIndexBody; links: SiteWorkLinks; all: boolean }) {
  return (
    <DataTable labelledBy={HEADING_ID}>
      <thead>
        <tr>
          <th scope="col">Action</th>
          <th scope="col">Source</th>
          <th scope="col">Owner</th>
          <th scope="col">Due</th>
          <th scope="col">State</th>
          <th scope="col">Success criterion</th>
        </tr>
      </thead>
      <tbody>
        {body.rows.map((row, index) => (
          <tr
            key={row.action_id}
            hidden={!all && index >= SITE_WORK_VISIBLE_ROWS}
            data-site-work-row={row.action_id}
            data-site-work-event={row.selected_event.id}
            data-site-work-revision={row.origin.finding_revision_id}
          >
            <td>
              <Link to={links.action(row.action_id)} data-site-work-action-link>
                {row.action_code} · Battery reserve trial
              </Link>
            </td>
            <td>
              <Link to={links.finding(row.origin.finding_id, row.origin.finding_revision_id)} data-site-work-finding-link>
                Finding, version {row.origin.revision_no}
              </Link>
            </td>
            <td>Not recorded</td>
            <td>Not set</td>
            <td>
              <span className={`w1f4-action-badge w1f4-action-badge--${stateTone(row)}`} data-site-work-row-state={row.state.application}>
                {stateWords(row)}
              </span>
              <small className="w1f4-work-subline muted">
                Latest step:{" "}
                <Link
                  to={links.history(row.action_id, row.selected_event.id)}
                  data-site-work-event-link
                  title={`Created ${utcText(row.created_at)} · step recorded ${utcText(row.selected_event.recorded_at)}`}
                >
                  {STEP_WORDS[row.selected_event.kind] ?? row.selected_event.kind}
                </Link>
              </small>
            </td>
            <td>Not recorded</td>
          </tr>
        ))}
      </tbody>
    </DataTable>
  );
}

const LISTED_WORDS: ProductWords = {
  label: "Every Action created here in this window",
  sentence:
    "The list was read in full for this site and window. Where each Action stands is its last recorded step, not a judgement of whether it worked.",
  next: "Open an Action that is not applied or not yet checked to see its next step.",
  tone: "neutral",
  code: "CURRENT",
  unrecognised: false,
};

/** The refused or unread list, as state-line words: never a zero. */
function refusedWords(result: ActionIndexResult): ProductWords {
  switch (result.status) {
    case "unauthenticated":
    case "forbidden":
      return readResultWords("refused");
    case "not_found":
      return readResultWords("not-found");
    case "basis_changed":
      return {
        label: "This list changed while it was open",
        sentence: "Actions in this window changed, so the next page cannot continue from the earlier one. This is not zero.",
        next: "Start again from the first page.",
        tone: "waiting",
        code: result.status,
        unrecognised: false,
      };
    case "invalid":
      return {
        label: "This window cannot be shown",
        sentence: "Windows are whole UTC days, at most 31 days long. Nothing was counted.",
        next: "Choose another window.",
        tone: "limited",
        code: result.status,
        unrecognised: false,
      };
    default:
      return readResultWords("unavailable");
  }
}

/** An in-panel state: one bold line and one note line, never a nested panel or a zero. */
function PanelState({
  state,
  title,
  children,
  data,
}: {
  state: string;
  title: string;
  children: ReactNode;
  data?: Record<string, string>;
}) {
  return (
    <div className="w1f4-work-state" data-site-work-state={state} data-panel-gap={HEADING_ID} {...data}>
      <p className="w1f4-work-state__title">
        <strong>{title}</strong>
      </p>
      {children}
    </div>
  );
}

function Refused({ result, scope, links }: { result: ActionIndexResult; scope: ActionIndexScope; links: SiteWorkLinks }) {
  switch (result.status) {
    case "basis_changed":
      return (
        <PanelState state="basis-changed" title="This list changed" data={{ "data-site-work-reason": result.reason ?? "" }}>
          <ChartNote>Actions in this window changed after this page was opened, so the next page cannot continue from it.</ChartNote>
          <p>
            <Link to={links.scope({ ...scope, cursor: null })} data-site-work-restart>
              Start again from the first page
            </Link>
          </p>
        </PanelState>
      );
    case "invalid":
      return (
        <PanelState state="invalid" title="This window cannot be shown" data={{ "data-site-work-code": result.code ?? "" }}>
          <ChartNote>
            {result.message ?? "The requested window is not valid."} Windows are whole UTC days, at most 31 days long.
          </ChartNote>
        </PanelState>
      );
    case "unauthenticated":
      return (
        <PanelState state="unauthenticated" title="Sign in to see Actions">
          <ChartNote>{result.message ?? "Sign in to read Actions."}</ChartNote>
        </PanelState>
      );
    case "forbidden":
      return (
        <PanelState state="forbidden" title="No access to this site's Actions">
          <ChartNote>{result.message ?? "You do not have access to this site."}</ChartNote>
        </PanelState>
      );
    case "not_found":
      return (
        <PanelState state="not-found" title="No Actions record for this site">
          <ChartNote>
            This site has no imported record, so it has no Action list. This is not a statement that it has no work.
          </ChartNote>
        </PanelState>
      );
    default:
      return (
        <PanelState state={result.status === "inconsistent" ? "inconsistent" : "unavailable"} title="Actions not known right now">
          <ChartNote>
            The Action list could not be read, so nothing is listed and no count is given. This is not a statement that
            the site has no Actions. Try again shortly.
          </ChartNote>
        </PanelState>
      );
  }
}

function Loaded({ body, scope, links }: { body: ActionIndexBody; scope: ActionIndexScope; links: SiteWorkLinks }) {
  if (body.total_count === 0) {
    return (
      <div className="w1f4-work-state" data-site-work-state="current-empty">
        <p className="w1f4-work-state__title">
          <strong data-site-work-proved-zero={body.read_at}>No Actions created at this site in this window</strong>
        </p>
        <ChartNote>
          The full list for this site and window was read at {utcText(body.read_at)} and holds no Action. It says nothing
          about other windows, incidents or maintenance work.
        </ChartNote>
        <Basis body={body} />
      </div>
    );
  }
  return <LoadedRows body={body} scope={scope} links={links} />;
}

function LoadedRows({ body, scope, links }: { body: ActionIndexBody; scope: ActionIndexScope; links: SiteWorkLinks }) {
  const [all, setAll] = useState(false);
  const folded = body.rows.length > SITE_WORK_VISIBLE_ROWS;
  return (
    <div data-site-work-state="current-rows">
      <Rows body={body} links={links} all={all} />
      <div className="w1f4-work-foot">
      <nav aria-label="Actions pages" data-site-work-pages className="w1f4-work-pages">
        <span>
          Showing {body.rows.length} of {body.total_count}. Newest first.
        </span>{" "}
        {folded ? (
          <button type="button" className="link-button" aria-expanded={all} onClick={() => setAll((open) => !open)} data-site-work-show-all>
            {all ? `Show the first ${SITE_WORK_VISIBLE_ROWS}` : `Show all ${body.rows.length} Actions`}
          </button>
        ) : null}{" "}
        {scope.cursor ? (
          <Link to={links.scope({ ...scope, cursor: null })} data-site-work-first>
            First page
          </Link>
        ) : null}{" "}
        {body.next_cursor ? (
          <Link to={links.scope({ ...scope, cursor: body.next_cursor })} data-site-work-next>
            Next page
          </Link>
        ) : null}
      </nav>
      <Basis body={body} />
      </div>
    </div>
  );
}

/** The one-line strip: scope and count, the read state, the window's read time. */
function WorkStrip({
  siteName,
  scope,
  result,
}: {
  siteName: string;
  scope: ActionIndexScope | null;
  result: ActionIndexResult | null;
}) {
  let count: string;
  let words: ProductWords | null = null;
  let detail: string | null = null;
  if (scope === null) {
    count = "no window chosen";
    detail = "Nothing is listed until a window is chosen";
  } else if (result === null) {
    count = "reading";
  } else if (result.status === "loaded") {
    const body = result.value;
    const days = `${dayText(body.window.from)} to ${dayText(lastDayOf(body.window.to))}`;
    count = `${body.total_count} ${body.total_count === 1 ? "Action" : "Actions"} created ${days}`;
    words = body.total_count === 0 ? readResultWords("proved-empty") : LISTED_WORDS;
    detail = `Read ${utcText(body.read_at)}`;
  } else {
    count = "no count";
    words = refusedWords(result);
    detail = "Read time not recorded";
  }
  return (
    <div className="status-strip status-strip--line" aria-label="Actions at this site, scope">
      <span className="status-strip__lead" data-site-work-scope>
        <strong>Scoped to {siteName}</strong> · {count}
      </span>
      {words === null ? null : (
        <span className="status-strip__state" data-site-work-status={words.tone}>
          {words.label}
        </span>
      )}
      {detail === null ? null : (
        <span className="muted status-strip__item" data-site-work-read-at>
          {detail}
        </span>
      )}
    </div>
  );
}

export function SiteWorkActions({ siteId, siteName, client, scope, links, onScope }: SiteWorkActionsProps) {
  const [result, setResult] = useState<ActionIndexResult | null>(null);
  const from = scope?.from;
  const to = scope?.to;
  const limit = scope?.limit;
  const cursor = scope?.cursor;
  useEffect(() => {
    if (from === undefined || to === undefined) return undefined;
    let active = true;
    setResult(null);
    void client.getActionIndex(siteId, { from, to, limit, cursor }).then((loaded) => {
      if (active) setResult(loaded);
    });
    return () => {
      active = false;
    };
  }, [client, siteId, from, to, limit, cursor]);
  const shown = scope === null ? null : result;
  const rows = shown !== null && shown.status === "loaded" && shown.value.total_count > 0;
  return (
    <div className="w1f4-changes-work" data-site-work="actions">
      <WorkStrip siteName={siteName} scope={scope} result={shown} />
      <Panel
        heading={SITE_WORK_PANEL_TITLE}
        headingId={HEADING_ID}
        actions={<WindowForm scope={scope} onScope={onScope} />}
      >
        {scope === null ? (
          <PanelState state="choose-window" title="Choose a window">
            <ChartNote>
              Pick the days the Actions were created in (at most 31) and select Show Actions. Nothing is listed until a
              window is chosen.
            </ChartNote>
          </PanelState>
        ) : result === null ? (
          <p data-site-work-state="loading">Loading the site&apos;s Actions.</p>
        ) : result.status === "loaded" ? (
          <Loaded body={result.value} scope={scope} links={links} />
        ) : (
          <Refused result={result} scope={scope} links={links} />
        )}
        <ChartNote data={{ "data-site-work-not-included": "" }}>
          {rows
            ? "Applied or closed is a recorded step, not proof that a trial worked; each Action's Verification shows whether it met its goal. "
            : null}
          This list holds Actions only. Incidents and maintenance work are not part of it.
        </ChartNote>
      </Panel>
      <p className="notice notice--info">Opening an Action moves you to its own page; the breadcrumb keeps this site.</p>
    </div>
  );
}

/* ---------- W5-02 K2a / W5-04 V2a: the domain Site Actions tab (v69 `cold-work`, `ev-work`) ---------- */

/**
 * W5-02 K2a (spec "Shared Site UI and mock slots", U3, P-K2a-33..44) and W5-04 V2a (readiness rulings 14, 19, 20,
 * 44-46): Site > Work > Actions on a COLDCHAIN or EV_CHARGING Site, over the union Site Action index
 * (`domainActionClient.ts`). The v69 `cold-work` / `ev-work` slots are identical (`index.html:334-343`): the scope
 * strip, the currentness notice below it, the one "Actions at this site" panel with the six mock columns, and the blue
 * context notice. The window and cutoff come from the URL (the frame defaults the window); there is no W1 date form,
 * helper line or "What this list is based on" disclosure here, because those describe W1-only fields.
 *
 * Ruling 45: every element carries `data-domain-work-*`; the cold surface also keeps its K2 `data-cold-work*`
 * attributes, classes and disclosure names for the K2/K5 regressions, and an EV surface never receives a cold name.
 */
export interface DomainSiteWorkLinks {
  /** The same tab at another page of the same window and cutoff. */
  page: (scope: DomainIndexScope) => string;
}

/** The per-domain words and switches of the domain Actions tab (cold literals stay in `coldWorkPresentation.ts`). */
export interface DomainWorkPresentation {
  domain: DomainActionDomain;
  /** True only for COLDCHAIN: also emit the K2 `data-cold-work*` attributes, `cold-work-*` classes and names. */
  legacyCold: boolean;
  headingId: string;
  panelTitle: string;
  stripDetail: string;
  globalGap: string;
  dueUnset: string;
  empty: readonly [string, string];
  loading: string;
  unavailable: string;
  retry: string;
  ownerMissing: string;
  dueMissing: string;
  criterionMissing: string;
  stateOpen: string;
  count: (n: number) => string;
  showAll: (n: number) => string;
  /** R113 (ruling 46): whether a domain row's Action code is a live link to its detail route. */
  domainActionLink: boolean;
  /**
   * W5-04 V4a (readiness ruling 67): the domain row's detail address from the server `links.action` and the selected
   * Work scope. Cold keeps the server href unchanged; EV appends `from,to` and an explicit `known_at`, never the cursor.
   */
  actionHref: (serverHref: string, scope: DomainIndexScope) => string;
  /** R75: the note inside the `Finding version` disclosure, or none (cold keeps its K2 cell unchanged). */
  sourceUnavailable: string | null;
  notice: (status: DomainStatus, knownAt: string) => string | null;
  tone: (status: DomainStatus) => "blue" | "amber";
}

export const COLD_WORK_HEADING_ID = "cold-work-actions-heading";
export const EV_WORK_HEADING_ID = "ev-work-actions-heading";

export const COLD_WORK_PRESENTATION: DomainWorkPresentation = {
  domain: COLD_DOMAIN,
  legacyCold: true,
  headingId: COLD_WORK_HEADING_ID,
  panelTitle: COLD_WORK_PANEL_TITLE,
  stripDetail: COLD_WORK_STRIP_DETAIL,
  globalGap: COLD_WORK_GLOBAL_GAP,
  dueUnset: COLD_WORK_DUE_UNSET,
  empty: COLD_WORK_EMPTY,
  loading: COLD_WORK_LOADING,
  unavailable: COLD_WORK_UNAVAILABLE,
  retry: COLD_WORK_RETRY,
  ownerMissing: COLD_OWNER_MISSING,
  dueMissing: COLD_DUE_MISSING,
  criterionMissing: COLD_CRITERION_MISSING,
  stateOpen: COLD_STATE_OPEN,
  count: coldActionCount,
  showAll: coldShowAll,
  domainActionLink: true,
  actionHref: (serverHref) => serverHref,
  sourceUnavailable: null,
  notice: coldCurrentnessNotice,
  tone: coldCurrentnessTone,
};

/**
 * W5-04 V2a: the EV Actions tab. R04 strip, R76 subtitle, R79 count, R80 notice placement and R104 tone (the cold
 * currentness literals and tone reused), R108 fold, R113 plain Action code, R74/R75 Finding source.
 */
export const EV_WORK_PRESENTATION: DomainWorkPresentation = {
  domain: EV_DOMAIN,
  legacyCold: false,
  headingId: EV_WORK_HEADING_ID,
  panelTitle: EV_WORK_PANEL_TITLE,
  stripDetail: EV_WORK_STRIP_DETAIL,
  globalGap: EV_WORK_GLOBAL_GAP,
  dueUnset: EV_WORK_DUE_UNSET,
  empty: EV_WORK_EMPTY,
  loading: EV_WORK_LOADING,
  unavailable: EV_WORK_UNAVAILABLE,
  retry: EV_WORK_RETRY,
  ownerMissing: EV_OWNER_MISSING,
  dueMissing: EV_DUE_MISSING,
  criterionMissing: EV_CRITERION_MISSING,
  stateOpen: EV_STATE_OPEN,
  count: evActionCount,
  showAll: evShowAll,
  domainActionLink: EV_ACTION_LINK_LIVE,
  actionHref: evActionHref,
  sourceUnavailable: EV_SOURCE_FINDING_UNAVAILABLE,
  notice: coldCurrentnessNotice,
  tone: coldCurrentnessTone,
};

/** The presentation a Site type selects; null for a Site type without a domain Work surface (mini-grid stays W1). */
export function domainWorkPresentation(siteType: string): DomainWorkPresentation | null {
  if (siteType === COLD_DOMAIN) return COLD_WORK_PRESENTATION;
  if (siteType === EV_DOMAIN) return EV_WORK_PRESENTATION;
  return null;
}

/**
 * Ruling 45: `data-domain-work-{name}`, plus the cold K2 `data-cold-work-{name}` on the cold surface only. Without a
 * value the attribute is presence-only: the cold name keeps the K2 boolean-prop rendering `="true"` byte-for-byte
 * (V2a review Low-1) and the domain name renders empty.
 */
function workAttrs(legacyCold: boolean, name: string, value?: string): Record<string, string> {
  const suffix = name === "" ? "" : `-${name}`;
  const attrs: Record<string, string> = { [`data-domain-work${suffix}`]: value ?? "" };
  if (legacyCold) attrs[`data-cold-work${suffix}`] = value ?? "true";
  return attrs;
}

/** `domain-work-{name}` classes, plus the cold K2 `cold-work-{name}` on the cold surface only. */
function workClass(legacyCold: boolean, name: string): string {
  return legacyCold ? `cold-work-${name} domain-work-${name}` : `domain-work-${name}`;
}

/** The disclosure-name prefix: cold keeps its K2 `cold-work`, EV uses `domain-work`. */
const namePrefix = (legacyCold: boolean) => (legacyCold ? "cold-work" : "domain-work");

/** The `[from,to)` window and explicit cutoff the domain Work URL carries (no cursor). */
export interface DomainWorkWindowScope {
  from: string;
  to: string;
  knownAt: string | null;
}

const utcDay = (instant: string) => (isUtcInstant(instant) ? new Date(instant).toISOString().slice(0, 10) : "");

/**
 * W5-02 K2 ruling 1 (P-K2a-39), extended to EV by W5-04 readiness ruling 14: the compact page-local `Window` control on
 * domain Site Work, immediately after the Work subtabs and before the scope strip. It displays the selected `from` and
 * `to` UTC dates (the frame's seven-UTC-day default when the URL has no pair) and, on Apply, writes a nonempty strict
 * UTC half-open `[from,to)` of at most 31 days with `from < to`; the frame keeps an explicit `known_at`, drops the
 * cursor and reads page one. Invalid input stays on the page with the existing window error and makes no new read.
 *
 * MOCK DEVIATION (D1) R88 (cold) / R112 (EV): the v69 `cold-work` / `ev-work` topbar range picker
 * (`index.html:782,1138`; `340-343`) cannot live in the absent app topbar; this page-local control keeps the mock's
 * ability to select a range. MOCK DEVIATION (D4) R77 (EV): the mock's fixed EAT example is replaced by the UTC
 * labels; the EV-LAB-001 fixture zone is `Etc/UTC`.
 */
export function DomainWorkWindow({
  scope,
  onApply,
  legacyCold,
}: {
  scope: DomainWorkWindowScope;
  onApply: (next: DomainWorkWindowScope) => void;
  /** True on a COLDCHAIN Site: keep the K2 `data-cold-work-window*` attributes and classes. */
  legacyCold: boolean;
}) {
  const [first, setFirst] = useState(utcDay(scope.from));
  const [last, setLast] = useState(utcDay(scope.to));
  const [error, setError] = useState<string | null>(null);
  useEffect(() => {
    setFirst(utcDay(scope.from));
    setLast(utcDay(scope.to));
    setError(null);
  }, [scope.from, scope.to]);
  const submit = (event: FormEvent) => {
    event.preventDefault();
    const next = { from: first ? `${first}T00:00:00Z` : "", to: last ? `${last}T00:00:00Z` : "", knownAt: scope.knownAt };
    // The client's own window check (the server's INVALID_WINDOW literal); nothing is navigated or read when it fails.
    const invalid = invalidScope({ from: next.from, to: next.to, knownAt: null, cursor: null });
    if (invalid !== null) {
      setError(invalid.message);
      return;
    }
    setError(null);
    onApply(next);
  };
  return (
    <form className={`site-date-bar ${workClass(legacyCold, "window")}`} onSubmit={submit} aria-label="Window" {...workAttrs(legacyCold, "window")}>
      <span className={workClass(legacyCold, "window__lead")}>Window</span>
      <label className={workClass(legacyCold, "window__field")}>
        {"From (UTC) "}
        <input
          className="v69-chip-control"
          type="date"
          value={first}
          onChange={(event) => setFirst(event.target.value)}
          {...workAttrs(legacyCold, "window-from")}
        />
      </label>
      <label className={workClass(legacyCold, "window__field")}>
        {"To (UTC, exclusive) "}
        <input
          className="v69-chip-control"
          type="date"
          value={last}
          onChange={(event) => setLast(event.target.value)}
          {...workAttrs(legacyCold, "window-to")}
        />
      </label>
      <button className="button" type="submit" {...workAttrs(legacyCold, "window-apply")}>
        Apply
      </button>
      {error === null ? null : (
        <span className={workClass(legacyCold, "window__error")} role="alert" {...workAttrs(legacyCold, "window-error")}>
          {error}
        </span>
      )}
    </form>
  );
}

/**
 * U4: a long value previews at two lines; the full text sits in a "Read full text" disclosure.
 * K2 ruling 20: while that disclosure is open the two-line preview is removed and the disclosure body shows the
 * complete value once (with the same content, so the Action link stays); closing restores the preview. The shared
 * Disclosure markup is unchanged: the wrapper listens for the details `toggle` (which does not bubble) in capture.
 */
function LongText({ text, name, legacyCold, children }: { text: string; name: string; legacyCold: boolean; children?: ReactNode }) {
  const long = isLongText(text);
  const [open, setOpen] = useState(false);
  const wrapper = useRef<HTMLDivElement | null>(null);
  useEffect(() => {
    const el = wrapper.current;
    if (!long || el === null) return undefined;
    const onToggle = (event: Event) => {
      const details = event.target;
      if (details instanceof HTMLDetailsElement && details.parentElement === el) setOpen(details.open);
    };
    el.addEventListener("toggle", onToggle, true);
    return () => el.removeEventListener("toggle", onToggle, true);
  }, [long]);
  if (!long) return <span>{children ?? text}</span>;
  return (
    <div className={workClass(legacyCold, "longtext")} ref={wrapper} {...workAttrs(legacyCold, "longtext", open ? "open" : "closed")}>
      {open ? null : (
        <span className="work-cases-clamp" {...workAttrs(legacyCold, "preview", name)}>
          {children ?? text}
        </span>
      )}
      <Disclosure name={name} summary={READ_FULL_TEXT}>
        {open ? (children ?? text) : text}
      </Disclosure>
    </div>
  );
}

const isDomainRow = (row: DomainIndexRow) => row.domain === COLD_DOMAIN || row.domain === EV_DOMAIN;

function DomainRowState({ row, p }: { row: DomainIndexRow; p: DomainWorkPresentation }) {
  if (isDomainRow(row)) {
    return (
      <span className="w1f4-action-badge w1f4-action-badge--amber" {...workAttrs(p.legacyCold, "state", "OPEN")}>
        {p.stateOpen}
      </span>
    );
  }
  // P-K2a-33 / W5-04 pre-flight 28: a W1 row keeps the existing W1 state presenter (its state object); its W1-only
  // step line is omitted, and no W1 state is coerced to the domain `Open`.
  const w1 = { state: row.state as ActionIndexRow["state"] };
  return (
    <span className={`w1f4-action-badge w1f4-action-badge--${stateTone(w1)}`} {...workAttrs(p.legacyCold, "state", w1.state.application)}>
      {stateWords(w1)}
    </span>
  );
}

/** A due date as `YYYY-MM-DD` in UTC, or the presentation's `Not set`. */
function dueText(p: DomainWorkPresentation, due: string | null): string {
  return due === null ? p.dueMissing : coldDueText(due);
}

/** Readiness ruling 67 (re-exported; defined beside the EV switch so the case rows share it, ruling 71). */
export { evActionHref };

function DomainRows({ body, all, p, scope }: { body: DomainIndexBody; all: boolean; p: DomainWorkPresentation; scope: DomainIndexScope }) {
  const lc = p.legacyCold;
  const prefix = namePrefix(lc);
  return (
    <DataTable labelledBy={p.headingId} stickyFirstColumn>
      <thead>
        <tr>
          <th scope="col">Action</th>
          <th scope="col">Source</th>
          <th scope="col">Owner</th>
          <th scope="col">Due</th>
          <th scope="col">State</th>
          <th scope="col">Success criterion</th>
        </tr>
      </thead>
      <tbody>
        {body.rows.map((row, index) => {
          const domain = isDomainRow(row);
          // P-K2a-33: a W1 row shows its stored code only (no battery title); a domain row its stored code and title.
          const label = domain && row.title !== null ? `${row.action_code} · ${row.title}` : row.action_code;
          const owner = row.owner_label ?? p.ownerMissing;
          const content = (
            <>
              <span className={workClass(lc, "code")}>{row.action_code}</span>
              {domain && row.title !== null ? ` · ${row.title}` : null}
            </>
          );
          // Ruling 46 / MOCK DEVIATION (D1) R113: an EV domain Action code stays plain text until V4a mounts its detail
          // route; a W1 row keeps its own W1 address and the cold row its `/verification` href.
          const linked = !domain || p.domainActionLink;
          return (
            <tr
              key={row.action_id}
              hidden={!all && index >= SITE_WORK_VISIBLE_ROWS}
              {...workAttrs(lc, "row", row.action_id)}
              {...workAttrs(lc, "domain", row.domain)}
            >
              <td>
                {/* The server's own Action href: `/verification` for a domain row, the bare W1 address for a W1 row. */}
                <LongText text={label} name={`${prefix}-title-${row.action_id}`} legacyCold={lc}>
                  {linked ? (
                    <Link to={domain ? p.actionHref(row.links.action, scope) : row.links.action} {...workAttrs(lc, "action-link", domain ? "domain" : "w1")}>
                      {content}
                    </Link>
                  ) : (
                    <span {...workAttrs(lc, "action-plain", row.action_id)}>{content}</span>
                  )}
                </LongText>
              </td>
              <td>
                {/* MOCK DEVIATION (D1) R65 (cold) / R74 (EV): the mock's F-118 / F-130 code slot shows `Finding {id8}`;
                    no public Finding code exists. MOCK DEVIATION (D1) R66 (cold) / R75 (EV): plain text, never an
                    anchor, because the domain Finding frame does not read `revision_id`; the selected revision is in
                    the disclosure. */}
                <span className={workClass(lc, "code")} {...workAttrs(lc, "source", row.origin.finding_id)}>
                  {row.origin.label}
                </span>
                <Disclosure name={`${prefix}-source-${row.action_id}`} summary="Finding version" variant="inline">
                  <code data-vocabulary-exempt="source-reference" {...workAttrs(lc, "revision")}>
                    {row.origin.finding_revision_id}
                  </code>
                  {domain && p.sourceUnavailable !== null ? (
                    <>
                      {" "}
                      <span className="muted" {...workAttrs(lc, "source-unavailable")}>
                        {p.sourceUnavailable}
                      </span>
                    </>
                  ) : null}
                </Disclosure>
              </td>
              <td {...workAttrs(lc, "owner")}>
                <LongText text={owner} name={`${prefix}-owner-${row.action_id}`} legacyCold={lc} />
              </td>
              <td className={workClass(lc, "code")} {...workAttrs(lc, "due")}>
                {dueText(p, row.due_at)}
              </td>
              <td>
                <DomainRowState row={row} p={p} />
              </td>
              <td {...workAttrs(lc, "criterion")}>{row.criterion_summary ?? p.criterionMissing}</td>
            </tr>
          );
        })}
      </tbody>
    </DataTable>
  );
}

function DomainLoadedRows({
  body,
  scope,
  links,
  p,
}: {
  body: DomainIndexBody;
  scope: DomainIndexScope;
  links: DomainSiteWorkLinks;
  p: DomainWorkPresentation;
}) {
  const [all, setAll] = useState(false);
  const lc = p.legacyCold;
  const folded = body.rows.length > SITE_WORK_VISIBLE_ROWS;
  const pager = (folded && !all) || scope.cursor !== null || body.next_cursor !== null;
  return (
    <div data-site-work-state="current-rows" {...workAttrs(lc, "state-panel", "rows")}>
      <DomainRows body={body} all={all} p={p} scope={scope} />
      {pager ? (
        <div className="w1f4-work-foot">
          <nav aria-label="Actions pages" {...workAttrs(lc, "pages")} className="w1f4-work-pages">
            {folded && !all ? (
              <button type="button" className="link-button" aria-expanded={false} onClick={() => setAll(true)} {...workAttrs(lc, "show-all")}>
                {p.showAll(body.rows.length)}
              </button>
            ) : null}{" "}
            {scope.cursor !== null ? (
              <Link to={links.page({ ...scope, cursor: null })} {...workAttrs(lc, "first")}>
                First page
              </Link>
            ) : null}{" "}
            {body.next_cursor !== null ? (
              // U3: a cursor page pins the response cutoff in the URL.
              <Link to={links.page({ ...scope, knownAt: body.known_at, cursor: body.next_cursor })} {...workAttrs(lc, "next")}>
                Next page
              </Link>
            ) : null}
          </nav>
        </div>
      ) : null}
    </div>
  );
}

export interface DomainSiteWorkActionsProps {
  siteId: string;
  /** The stored Site display name; the strip uses its W4 short name. */
  siteName: string;
  /** The stored Site type: it selects the fixed network/shape sentences of the read (ruling 44). */
  siteType: string;
  client: DomainActionClient;
  scope: DomainIndexScope;
  links: DomainSiteWorkLinks;
  presentation: DomainWorkPresentation;
  /** U1: a changed basis restarts on page one without the cursor (a navigation). */
  onRestart: (scope: DomainIndexScope) => void;
}

export function DomainSiteWorkActions({ siteId, siteName, siteType, client, scope, links, presentation: p, onRestart }: DomainSiteWorkActionsProps) {
  const [attempt, setAttempt] = useState(0);
  const [read, setRead] = useState<{ key: string; result: DomainIndexResult } | null>(null);
  const { from, to, knownAt, cursor } = scope;
  const lc = p.legacyCold;
  const key = `${siteId}|${from}|${to}|${knownAt ?? ""}|${cursor ?? ""}|${attempt}`;
  useEffect(() => {
    let active = true;
    // The cold read keeps its K2 two-argument call; EV passes its Site type for the ruling-44 sentences.
    const request = lc ? client.getIndex(siteId, { from, to, knownAt, cursor }) : client.getIndex(siteId, { from, to, knownAt, cursor }, siteType);
    void request.then((result) => {
      if (active) setRead({ key, result });
    });
    return () => {
      active = false;
    };
  }, [client, siteId, siteType, lc, from, to, knownAt, cursor, key]);
  const result = read !== null && read.key === key ? read.result : null;
  const body = result !== null && result.status === "loaded" ? result.value : null;
  const notice = body === null ? null : p.notice(body.status, body.known_at);
  const retry = () => {
    if (result !== null && result.status === "basis_changed" && cursor !== null) onRestart({ ...scope, cursor: null });
    else setAttempt((n) => n + 1);
  };
  return (
    <div className={`w1f4-changes-work ${workClass(lc, "actions")}`} data-site-work="actions" {...workAttrs(lc, "", "actions")}>
      <div className="status-strip status-strip--line" aria-label="Actions at this site, scope" {...workAttrs(lc, "strip")}>
        <span className="status-strip__lead" data-site-work-scope>
          {/* K2 ruling 11: loading and refusal show exactly `— actions`, never the mock's zero. */}
          <strong>Scoped to {shortName(siteName)}</strong> · {body === null ? "— actions" : p.count(body.total_count)}
        </span>
        <span className="muted status-strip__item">{p.stripDetail}</span>
        <span className="muted status-strip__item" {...workAttrs(lc, "global-gap")}>
          {p.globalGap}
        </span>
      </div>
      {/* MOCK DEVIATION (D2) R91 (cold; K2 rulings 15, 16) / R80 + R104 (EV): the selected-state notice sits between
          the strip and the panel, blue for Historical/Unknown and amber for Pending recompute/Stale; absent on CURRENT. */}
      {body !== null && notice !== null ? (
        <Notice tone={p.tone(body.status)} data={workAttrs(lc, "currentness", body.status)}>
          <RailIcon name="info" />
          <p>{notice}</p>
        </Notice>
      ) : null}
      <Panel
        heading={p.panelTitle}
        headingId={p.headingId}
        description={body !== null && body.total_count > 0 && body.all_due_dates_unset ? p.dueUnset : undefined}
      >
        {result === null ? (
          <p data-site-work-state="loading" {...workAttrs(lc, "state-panel", "loading")}>
            {p.loading}
          </p>
        ) : body === null ? (
          <div
            className="work-cases-state"
            data-site-work-state="refused"
            {...workAttrs(lc, "state-panel", "refused")}
            {...workAttrs(
              lc,
              "refusal",
              result.status === "loaded" ? "" : (result.code ?? (result.http === null ? "UNREACHABLE" : "UNEXPECTED")),
            )}
          >
            <p>
              <strong>{p.unavailable}</strong>
            </p>
            <p {...workAttrs(lc, "refusal-message")}>{result.status === "loaded" ? "" : result.message}</p>
            <p>
              <button type="button" className="button" onClick={retry} {...workAttrs(lc, "retry")}>
                {p.retry}
              </button>
            </p>
          </div>
        ) : body.total_count === 0 ? (
          <div className="work-cases-empty" {...workAttrs(lc, "empty")} {...workAttrs(lc, "state-panel", "empty")}>
            <span className="work-cases-empty__icon" aria-hidden="true">
              <RailIcon name="evidence" />
            </span>
            <h3>{p.empty[0]}</h3>
            <p>{p.empty[1]}</p>
          </div>
        ) : (
          <DomainLoadedRows key={key} body={body} scope={scope} links={links} p={p} />
        )}
      </Panel>
      {/* MOCK DEVIATION (D1) R01 (cold) / R03 (EV): the mock notice's create-flow sentence is omitted (no create flow). */}
      <Notice tone="blue" data={workAttrs(lc, "notice", "")}>
        <RailIcon name="info" />
        <p>{WORK_CONTEXT_NOTICE_DOMAIN}</p>
      </Notice>
    </div>
  );
}
