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
 * The default reading is plain; IDs, the selection rule and the list's fence
 * sit in a "What this list is based on" disclosure. Owner, due date, priority,
 * success criterion and any verification verdict are not shown: this read has
 * none of them, and the list derives none.
 */
import { useEffect, useState, type FormEvent } from "react";
import { Link } from "react-router-dom";

import {
  DataTable,
  Disclosure,
  ExactReferences,
  Fact,
  FactList,
  HeadlineVisualCard,
  Panel,
  ProductStatus,
  readResultWords,
  ValueBars,
  type ProductWords,
  type ValueBarItem,
} from "../ui";
import type { ActionIndexBody, ActionIndexClient, ActionIndexResult, ActionIndexRow, ActionIndexScope } from "./actionIndexClient";

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
export function stateWords(row: ActionIndexRow): string {
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
    <form onSubmit={submit} data-site-work-window aria-label="Actions window">
      <label>
        {"Created from "}
        <input type="date" value={first} onChange={(event) => setFirst(event.target.value)} />
      </label>{" "}
      <label>
        {"to (included) "}
        <input type="date" value={last} onChange={(event) => setLast(event.target.value)} />
      </label>{" "}
      <button type="submit">Show Actions</button>
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

function Rows({ body, links }: { body: ActionIndexBody; links: SiteWorkLinks }) {
  return (
    <DataTable labelledBy={HEADING_ID}>
      <thead>
        <tr>
          <th scope="col">Action</th>
          <th scope="col">Source</th>
          <th scope="col">Created</th>
          <th scope="col">State</th>
          <th scope="col">Latest step</th>
        </tr>
      </thead>
      <tbody>
        {body.rows.map((row) => (
          <tr
            key={row.action_id}
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
            <td>{utcText(row.created_at)}</td>
            <td data-site-work-state={row.state.application}>{stateWords(row)}</td>
            <td>
              <Link to={links.history(row.action_id, row.selected_event.id)} data-site-work-event-link>
                {STEP_WORDS[row.selected_event.kind] ?? row.selected_event.kind}
              </Link>
              <br />
              <small>recorded {utcText(row.selected_event.recorded_at)}</small>
            </td>
          </tr>
        ))}
      </tbody>
    </DataTable>
  );
}

function Loaded({ body, scope, links, siteName }: { body: ActionIndexBody; scope: ActionIndexScope; links: SiteWorkLinks; siteName: string }) {
  if (body.total_count === 0) {
    return (
      <>
        <p className="overview-note" data-site-work-scope>
          <strong>Scoped to {siteName}</strong> · 0 Actions created {dayText(body.window.from)} to {dayText(lastDayOf(body.window.to))}
        </p>
        <Panel heading="No Actions created at this site in this window" headingId={HEADING_ID}>
          <div data-site-work-state="current-empty">
            <p>No accepted recommendation was turned into an Action here between these dates.</p>
            <Basis body={body} />
          </div>
        </Panel>
      </>
    );
  }
  return (
    <>
      <p className="overview-note" data-site-work-scope>
        <strong>Scoped to {siteName}</strong> · {body.total_count} {body.total_count === 1 ? "Action" : "Actions"} created{" "}
        {dayText(body.window.from)} to {dayText(lastDayOf(body.window.to))}
      </p>
      <Panel heading="Actions at this site" headingId={HEADING_ID}>
        <div data-site-work-state="current-rows">
          <p>Newest first. Each link opens the Action, the Finding version it came from, or the exact step shown.</p>
          <Rows body={body} links={links} />
          <nav aria-label="Actions pages" data-site-work-pages>
            <span>
              Showing {body.rows.length} of {body.total_count}.
            </span>{" "}
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
          <p className="overview-note">Owners, due dates and success criteria are not recorded for these Actions.</p>
          <Basis body={body} />
        </div>
      </Panel>
    </>
  );
}

function Refused({ result, scope, links }: { result: ActionIndexResult; scope: ActionIndexScope; links: SiteWorkLinks }) {
  switch (result.status) {
    case "basis_changed":
      return (
        <Panel heading="This list changed" headingId={HEADING_ID}>
          <div data-site-work-state="basis-changed" data-site-work-reason={result.reason ?? ""}>
            <p>Actions in this window changed after this page was opened, so the next page cannot continue from it.</p>
            <p>
              <Link to={links.scope({ ...scope, cursor: null })} data-site-work-restart>
                Start again from the first page
              </Link>
            </p>
          </div>
        </Panel>
      );
    case "invalid":
      return (
        <Panel heading="This window cannot be shown" headingId={HEADING_ID}>
          <div data-site-work-state="invalid" data-site-work-code={result.code ?? ""}>
            <p>{result.message ?? "The requested window is not valid."}</p>
            <p>Windows are whole UTC days, at most 31 days long.</p>
          </div>
        </Panel>
      );
    case "unauthenticated":
      return (
        <Panel heading="Sign in to see Actions" headingId={HEADING_ID}>
          <p data-site-work-state="unauthenticated">{result.message ?? "Sign in to read Actions."}</p>
        </Panel>
      );
    case "forbidden":
      return (
        <Panel heading="No access to this site's Actions" headingId={HEADING_ID}>
          <p data-site-work-state="forbidden">{result.message ?? "You do not have access to this site."}</p>
        </Panel>
      );
    case "not_found":
      return (
        <Panel heading="No Actions record for this site" headingId={HEADING_ID}>
          <p data-site-work-state="not-found">
            This site has no imported record, so it has no Action list. This is not a statement that it has no work.
          </p>
        </Panel>
      );
    default:
      return (
        <Panel heading="Actions not known right now" headingId={HEADING_ID}>
          <div data-site-work-state={result.status === "inconsistent" ? "inconsistent" : "unavailable"}>
            <p>The Action list could not be read, so nothing is listed and no count is given.</p>
            <p>This is not a statement that the site has no Actions. Try again shortly.</p>
          </div>
        </Panel>
      );
  }
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
  return (
    <section aria-labelledby={HEADING_ID} data-site-work="actions">
      <WindowForm scope={scope} onScope={onScope} />
      {scope === null ? (
        <Panel heading="Choose a window" headingId={HEADING_ID}>
          <p data-site-work-state="choose-window">
            Pick the days the Actions were created in (at most 31) and select Show Actions. Nothing is listed until a
            window is chosen.
          </p>
        </Panel>
      ) : result === null ? (
        <p data-site-work-state="loading">Loading the site&apos;s Actions.</p>
      ) : null}
      {scope !== null && result !== null ? <SiteWorkCard result={result} siteName={siteName} links={links} /> : null}
      {scope === null || result === null ? null : result.status === "loaded" ? (
        <Loaded body={result.value} scope={scope} links={links} siteName={siteName} />
      ) : (
        <Refused result={result} scope={scope} links={links} />
      )}
      <p className="overview-note" data-site-work-not-included>
        This list holds Actions only. Incidents and maintenance work are not part of it.
      </p>
      <p className="overview-note">Opening an Action moves you to its own page; the breadcrumb keeps this site.</p>
    </section>
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

const STAND_ORDER = [
  ["Accepted, not applied", "pending"],
  ["Applied, result not checked yet", "applied"],
  ["Trial closed", "closed"],
  ["Being checked again", "rechecking"],
] as const;

function standKey(row: ActionIndexRow): string {
  if (row.state.resolution?.state === "RESOLVED") return "closed";
  if (row.state.resolution?.state === "RESOLUTION_WITHDRAWN") return "rechecking";
  if (row.state.application === "APPLIED") return "applied";
  if (row.state.application === "PENDING") return "pending";
  return "unrecognised";
}

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

/**
 * W1-UX-04: the Site Work answer card - what work is open at this site and
 * what is next. A zero is shown only after a successful bounded read, with
 * its read time beside it; a refused or unread list is never a zero. No
 * verification verdict is derived here.
 */
function SiteWorkCard({
  result,
  siteName,
  links,
}: {
  result: ActionIndexResult;
  siteName: string;
  links: SiteWorkLinks;
}) {
  if (result.status !== "loaded") {
    const words = refusedWords(result);
    return (
      <HeadlineVisualCard
        dataName="site-work"
        headingId="site-work-answer-heading"
        question="What work is open at this site, and what is next?"
        headline={<>No Action list can be shown, and no count is given.</>}
        status={<ProductStatus words={words} scope={`${siteName}, Actions`} asOf={null} />}
        meaning={<p>This is not a statement that the site has no Actions.</p>}
        todo={words.next === undefined ? undefined : <p>{words.next}</p>}
      />
    );
  }
  const body = result.value;
  const days = `${dayText(body.window.from)} to ${dayText(lastDayOf(body.window.to))}`;
  const scope = `${siteName}, Actions created ${days}`;
  if (body.total_count === 0) {
    const words = readResultWords("proved-empty");
    return (
      <HeadlineVisualCard
        dataName="site-work"
        headingId="site-work-answer-heading"
        question="What work is open at this site, and what is next?"
        headline={
          <span data-site-work-proved-zero={body.read_at}>No Actions were created at this site in this window.</span>
        }
        status={<ProductStatus words={words} scope={scope} asOf={body.read_at} />}
        meaning={
          <p>
            The full list for this site and window was read and holds no Action. It says nothing about other windows,
            incidents or maintenance work.
          </p>
        }
        todo={<p>Choose a wider window, or open the site&apos;s Findings to see what could be worked on.</p>}
        references={<SiteWorkReferences body={body} />}
      />
    );
  }
  const counts = new Map<string, number>();
  for (const row of body.rows) counts.set(standKey(row), (counts.get(standKey(row)) ?? 0) + 1);
  const items: ValueBarItem[] = STAND_ORDER.map(([label, key]) => ({ label, key, value: counts.get(key) ?? 0, valueText: String(counts.get(key) ?? 0) }));
  const unrecognised = counts.get("unrecognised") ?? 0;
  if (unrecognised > 0) items.push({ label: "State not recognised", key: "unrecognised", value: unrecognised, valueText: String(unrecognised) });
  const newest = body.rows[0];
  return (
    <HeadlineVisualCard
      dataName="site-work"
      headingId="site-work-answer-heading"
      question="What work is open at this site, and what is next?"
      headline={
        <>
          {body.total_count} {body.total_count === 1 ? "Action was" : "Actions were"} created at this site in this window.
        </>
      }
      status={<ProductStatus words={LISTED_WORDS} scope={scope} asOf={body.read_at} />}
      visual={
        <ValueBars
          title={`Where the Actions on this page stand (${body.rows.length} of ${body.total_count})`}
          items={items}
        />
      }
      meaning={
        <p>
          Applied or closed is a recorded step, not proof that a trial worked. Whether a trial met its goal is shown on
          each Action&apos;s Verification.
        </p>
      }
      todo={<p>{LISTED_WORDS.next}</p>}
      destination={
        newest ? (
          <Link to={links.action(newest.action_id)} data-site-work-newest-link>
            Open the newest Action
          </Link>
        ) : undefined
      }
      references={<SiteWorkReferences body={body} />}
    />
  );
}

function SiteWorkReferences({ body }: { body: ActionIndexBody }) {
  return (
    <ExactReferences
      name="site-work-references"
      references={[
        { label: "Window start", value: body.window.from },
        { label: "Window end (not included)", value: body.window.to },
        { label: "List check token", value: body.fence.token },
      ]}
    />
  );
}
