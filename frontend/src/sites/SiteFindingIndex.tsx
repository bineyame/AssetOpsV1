/**
 * S4-04 phase 2 (`sitefindings:1`, `I-site-findings-ui`): Site > Findings for
 * an imported Site, over the scoped Finding index read
 * (`GET /api/sites/{site}/finding-index`).
 *
 * The scope (domain, UTC window, page cursor) lives in the URL, owned by the
 * frame; this view reads it, renders one state, and links to other scopes.
 * Only a `CURRENT` read can say anything about how many Findings there are:
 *
 * - `CURRENT`, zero rows: an assessed empty window, with its watermark.
 * - `CURRENT`, rows: persisted canonical Findings in the read's order (episode
 *   start descending, then Finding ID), each linking its exact revision.
 * - Pending, unassessed, stale or failed reads, a closed Performance source,
 *   a continuity limit, a changed basis under an old cursor, and an invalid
 *   scope show no rows and no count, and never say "no Findings".
 *
 * No amount is shown: exact-revision money provenance is not in this read.
 * A Site with no imported record keeps the older summary (`fallback`).
 */
import { useEffect, useState, type FormEvent, type ReactNode } from "react";
import { Link } from "react-router-dom";

import { DataTable, Disclosure, Fact, FactList, Panel } from "../ui";
import type {
  FindingIndexBody,
  FindingIndexClient,
  FindingIndexResult,
  FindingIndexRow,
  FindingIndexScope,
} from "./findingIndexClient";
import { LIFECYCLE_WORDS, transitionWords } from "./findingWords";
import type { Lifecycle } from "./findingClient";

export interface FindingIndexLinks {
  /** The same page at another scope (a new window, page one, or the next page). */
  scope: (scope: FindingIndexScope) => string;
  /** One Finding, optionally at an exact revision. */
  finding: (findingId: string, revisionId?: string | null) => string;
}

export interface SiteFindingIndexProps {
  siteId: string;
  client: FindingIndexClient;
  scope: FindingIndexScope;
  links: FindingIndexLinks;
  /** Apply a new window (a navigation, so reload and back keep it). */
  onScope: (scope: FindingIndexScope) => void;
  /** Rendered for a Site with no imported record (the older summary). */
  fallback: ReactNode;
}

const HEADING_ID = "site-finding-index-heading";

const STATUS_WORDS: Record<string, { label: string; sentence: string }> = {
  PENDING: {
    label: "Not known yet",
    sentence: "The assessment or Finding matching for this window is still in progress.",
  },
  UNASSESSED: {
    label: "Not known",
    sentence: "This window has not been assessed, so nothing can be said about its Findings.",
  },
  STALE_PROJECTION: {
    label: "Not current",
    sentence: "Newer evidence or work for this window is waiting to be assessed.",
  },
  FAILED: {
    label: "Not known",
    sentence: "Assessment work for this window failed.",
  },
};

/** `2026-10-15 08:00 UTC` from an ISO instant (the read's display zone is UTC). */
export function utcText(instant: string | null | undefined): string {
  if (!instant) return "not recorded";
  const date = new Date(instant);
  if (Number.isNaN(date.getTime())) return instant;
  return `${date.toISOString().slice(0, 16).replace("T", " ")} UTC`;
}

const short = (id: string) => id.slice(0, 8);

/** The UTC calendar day of an instant, `YYYY-MM-DD`. */
function dayOf(instant: string): string {
  return new Date(instant).toISOString().slice(0, 10);
}

/** The last UTC day a half-open `[from, to)` window touches. */
function lastDayOf(to: string): string {
  return new Date(new Date(to).getTime() - 1).toISOString().slice(0, 10);
}

function WindowForm({ scope, onScope }: { scope: FindingIndexScope; onScope: (scope: FindingIndexScope) => void }) {
  const valid = !Number.isNaN(new Date(scope.from).getTime()) && !Number.isNaN(new Date(scope.to).getTime());
  const [first, setFirst] = useState(valid ? dayOf(scope.from) : "");
  const [last, setLast] = useState(valid ? lastDayOf(scope.to) : "");
  useEffect(() => {
    if (valid) {
      setFirst(dayOf(scope.from));
      setLast(lastDayOf(scope.to));
    }
  }, [scope.from, scope.to, valid]);
  const submit = (event: FormEvent) => {
    event.preventDefault();
    if (!first || !last) return;
    const to = new Date(`${last}T00:00:00Z`);
    to.setUTCDate(to.getUTCDate() + 1);
    onScope({
      domain: scope.domain,
      from: `${first}T00:00:00Z`,
      to: `${to.toISOString().slice(0, 10)}T00:00:00Z`,
      limit: scope.limit ?? null,
      cursor: null,
    });
  };
  return (
    <form onSubmit={submit} data-finding-index-window aria-label="Findings window">
      <label>
        {"From (UTC day) "}
        <input type="date" value={first} onChange={(event) => setFirst(event.target.value)} />
      </label>{" "}
      <label>
        {"To (UTC day, included) "}
        <input type="date" value={last} onChange={(event) => setLast(event.target.value)} />
      </label>{" "}
      <button type="submit">Show Findings</button>
    </form>
  );
}

function Basis({ body }: { body: FindingIndexBody }) {
  const matcher = body.watermarks.matcher;
  return (
    <Disclosure name="finding-index-basis" summary="What this list is based on">
      <FactList>
        <Fact term="Knowledge as of">{utcText(body.knowledge_at)}</Fact>
        <Fact term="Read built">{utcText(body.built_at)}</Fact>
        <Fact term="Days inspected">{body.discovery.days.join(", ") || "none"}</Fact>
        <Fact term="Finding matching">
          {matcher?.match_pass_id
            ? `pass ${short(String(matcher.match_pass_id))} through selection ${matcher.matched_through_selection_seq ?? "?"}`
            : "no matching pass recorded"}
        </Fact>
        <Fact term="Selection token">
          <code data-finding-index-token>{body.selection_token}</code>
        </Fact>
      </FactList>
      <DataTable labelledBy="finding-index-watermarks-heading">
        <caption id="finding-index-watermarks-heading">Per-day assessment basis</caption>
        <thead>
          <tr>
            <th scope="col">Day (UTC)</th>
            <th scope="col">State</th>
            <th scope="col">Assessment selection</th>
            <th scope="col">Assessment record</th>
            <th scope="col">Findings matched</th>
          </tr>
        </thead>
        <tbody>
          {body.watermarks.days.map((day) => (
            <tr key={day.day} data-finding-index-day={day.day}>
              <td>{day.day}</td>
              <td>{day.status === "CURRENT" ? "Assessed" : (STATUS_WORDS[day.status]?.label ?? day.status)}</td>
              <td>{day.s3.selection_seq ?? "none"}</td>
              <td>{day.s3.run_id ? <code>{short(day.s3.run_id)}</code> : "none"}</td>
              <td>{day.s4.matched ? "Yes" : "No"}</td>
            </tr>
          ))}
        </tbody>
      </DataTable>
      {body.status_reasons.length > 0 && (
        <ul data-finding-index-reasons>
          {body.status_reasons.map((reason) => (
            <li key={reason}>{reason}</li>
          ))}
        </ul>
      )}
    </Disclosure>
  );
}

function Relations({ row, links }: { row: FindingIndexRow; links: FindingIndexLinks }) {
  const items: { label: string; id: string }[] = [
    ...row.relations.merged_from.map((id) => ({ label: "Merged from", id })),
    ...(row.relations.recurs_after ? [{ label: "Recurs after", id: row.relations.recurs_after }] : []),
    ...row.relations.recurred_by.map((id) => ({ label: "Recurred as", id })),
    ...(row.relations.split_from ? [{ label: "Split from", id: row.relations.split_from }] : []),
    ...row.relations.split_parts.map((id) => ({ label: "Split into", id })),
  ];
  if (items.length === 0) return <>None</>;
  return (
    <ul className="finding-index-relations">
      {items.map((item) => (
        <li key={`${item.label}-${item.id}`}>
          {item.label} <Link to={links.finding(item.id)}>{short(item.id)}</Link>
        </li>
      ))}
    </ul>
  );
}

function Rows({ body, links }: { body: FindingIndexBody; links: FindingIndexLinks }) {
  return (
    <DataTable labelledBy={HEADING_ID}>
      <thead>
        <tr>
          <th scope="col">Period (UTC)</th>
          <th scope="col">Finding</th>
          <th scope="col">Status</th>
          <th scope="col">Version</th>
          <th scope="col">Related</th>
          <th scope="col">Amount</th>
        </tr>
      </thead>
      <tbody>
        {body.rows.map((row) => (
          <tr
            key={row.finding_id}
            data-finding-index-row={row.finding_id}
            data-finding-revision={row.finding_revision_id}
          >
            <td>
              {utcText(row.episode.start)} to {utcText(row.episode.end)}
            </td>
            <td>
              <Link to={links.finding(row.finding_id, row.finding_revision_id)} data-finding-index-link>
                {LIFECYCLE_WORDS[row.lifecycle as Lifecycle]?.title ?? "Generator support review"}
              </Link>
              <br />
              <small>
                Finding <code>{short(row.finding_id)}</code>
              </small>
            </td>
            <td>
              {LIFECYCLE_WORDS[row.lifecycle as Lifecycle]?.label ?? row.lifecycle}
              {row.transition ? (
                <>
                  <br />
                  <small>{transitionWords(row.transition)}</small>
                </>
              ) : null}
            </td>
            <td>
              Version {row.revision_no}
              <br />
              <small>
                <code>{short(row.finding_revision_id)}</code>
              </small>
            </td>
            <td>
              <Relations row={row} links={links} />
            </td>
            <td data-finding-index-amount={row.amount.state} title={row.amount.reason}>
              No amount shown
            </td>
          </tr>
        ))}
      </tbody>
    </DataTable>
  );
}

function Loaded({ body, scope, links }: { body: FindingIndexBody; scope: FindingIndexScope; links: FindingIndexLinks }) {
  const firstPage = links.scope({ ...scope, cursor: null });
  if (body.status !== "CURRENT" || body.total_count === null) {
    const words = STATUS_WORDS[body.status] ?? { label: "Not known", sentence: "This read is not current." };
    return (
      <Panel heading={words.label} headingId={HEADING_ID}>
        <div data-finding-index-state={body.status}>
          <p>{words.sentence}</p>
          <p>No Findings are listed and no count is given. This is not a statement that the window has no Findings.</p>
          <Basis body={body} />
        </div>
      </Panel>
    );
  }
  if (body.total_count === 0) {
    return (
      <Panel heading="No Findings in this window" headingId={HEADING_ID}>
        <div data-finding-index-state="current-empty">
          <p>
            Every day in this window was assessed and matched for Findings through its latest selection, and no
            Finding overlaps the window.
          </p>
          <Basis body={body} />
        </div>
      </Panel>
    );
  }
  const shown = body.rows.length;
  return (
    <Panel
      heading={`${body.total_count} ${body.total_count === 1 ? "Finding" : "Findings"} in this window`}
      headingId={HEADING_ID}
    >
      <div data-finding-index-state="current-rows">
        <p>
          Newest period first. Each Finding opens at the exact version listed here, which stays the same after
          reload even when a newer version is recorded.
        </p>
        <Rows body={body} links={links} />
        <nav aria-label="Findings pages" data-finding-index-pages>
          <span>
            Showing {shown} of {body.total_count}.
          </span>{" "}
          {scope.cursor ? <Link to={firstPage}>First page</Link> : null}{" "}
          {body.next_cursor ? (
            <Link to={links.scope({ ...scope, cursor: body.next_cursor })} data-finding-index-next>
              Next page
            </Link>
          ) : null}
        </nav>
        <Basis body={body} />
      </div>
    </Panel>
  );
}

function Refused({ result, scope, links }: { result: FindingIndexResult; scope: FindingIndexScope; links: FindingIndexLinks }) {
  const firstPage = links.scope({ ...scope, cursor: null });
  switch (result.status) {
    case "closed":
      return (
        <Panel heading="Findings list closed for this Site" headingId={HEADING_ID}>
          <div data-finding-index-state="closed">
            <p>{result.message ?? "This Site's assessments are not released."}</p>
            <p>
              No Findings are listed and no count is given. A link to an exact Finding version still opens it as
              audit material.
            </p>
          </div>
        </Panel>
      );
    case "continuity_limit":
      return (
        <Panel heading="Not known for this window" headingId={HEADING_ID}>
          <div data-finding-index-state="continuity-limit">
            <p>{result.message}</p>
            <p>
              No Findings are listed and no count is given. Choose a narrower window.
              {result.inspectedFrom && result.inspectedTo
                ? ` Days reached: ${result.inspectedFrom} to ${result.inspectedTo}.`
                : ""}
            </p>
          </div>
        </Panel>
      );
    case "basis_changed":
      return (
        <Panel heading="This list changed" headingId={HEADING_ID}>
          <div data-finding-index-state="basis-changed" data-finding-index-reason={result.reason ?? ""}>
            <p>The Findings for this window changed since this page was opened, so this page cannot continue.</p>
            <p>
              <Link to={firstPage} data-finding-index-restart>
                Start again from the first page
              </Link>
            </p>
          </div>
        </Panel>
      );
    case "invalid":
      return (
        <Panel heading="This window cannot be shown" headingId={HEADING_ID}>
          <div data-finding-index-state="invalid" data-finding-index-code={result.code ?? ""}>
            <p>{result.message ?? "The requested window is not valid."}</p>
            <p>Windows are whole UTC days, at most 31 days long.</p>
          </div>
        </Panel>
      );
    case "unauthenticated":
      return (
        <Panel heading="Sign in to see Findings" headingId={HEADING_ID}>
          <p data-finding-index-state="unauthenticated">{result.message ?? "Sign in to read Findings."}</p>
        </Panel>
      );
    case "forbidden":
      return (
        <Panel heading="No access to this Site's Findings" headingId={HEADING_ID}>
          <p data-finding-index-state="forbidden">{result.message ?? "You do not have access to this Site."}</p>
        </Panel>
      );
    default:
      return (
        <Panel heading="Findings unavailable" headingId={HEADING_ID}>
          <p data-finding-index-state="unavailable">
            {result.status === "unavailable" && result.message ? result.message : "The Findings could not be read."}
          </p>
        </Panel>
      );
  }
}

export function SiteFindingIndex({ siteId, client, scope, links, onScope, fallback }: SiteFindingIndexProps) {
  const [result, setResult] = useState<FindingIndexResult | null>(null);
  const { domain, from, to, limit, cursor } = scope;
  useEffect(() => {
    let active = true;
    setResult(null);
    void client.getFindingIndex(siteId, { domain, from, to, limit, cursor }).then((loaded) => {
      if (active) setResult(loaded);
    });
    return () => {
      active = false;
    };
  }, [client, siteId, domain, from, to, limit, cursor]);
  if (result === null) {
    return <p>Loading the site&apos;s findings.</p>;
  }
  if (result.status === "not_imported") {
    return <>{fallback}</>;
  }
  return (
    <section aria-labelledby={HEADING_ID} data-findings-index="site-window">
      <p className="overview-note">
        Mini-grid dispatch Findings that overlap {utcText(from)} to {utcText(to)} (the end is not included).
      </p>
      <WindowForm scope={scope} onScope={onScope} />
      {result.status === "loaded" ? (
        <Loaded body={result.value} scope={scope} links={links} />
      ) : (
        <Refused result={result} scope={scope} links={links} />
      )}
    </section>
  );
}
