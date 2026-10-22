/**
 * W4-01 commit 5 (`I-incident-ui`, `I-maintenance-ui`): the shared body of the
 * v69 `sitework-incidents` and `sitework-maintenance` screens, over the Site
 * work list read (`workClient.ts`, `site-work-index-1`).
 *
 * The mock's three slots, in order and kept in every state: the status strip,
 * the one "{Incidents|Maintenance} at this site" panel and the context notice
 * (`.agent/W4-01-build-spec.md` "Per-panel copy and layout dry-read", B10,
 * S19-S31 and the Run 7 commit-5 dry-read).
 *
 * - The count comes from the full selected set (`total_count`), never from the
 *   page; a refused read shows no rows and no count, never a zero.
 * - Five rows per page, Previous/Next on the server cursor; the cutoff the
 *   first page was read at (`known_at`) stays bound across pages and reload.
 * - Linked-evidence status (missing, being reassessed) is a link qualification,
 *   never a statement about the case itself or equipment health.
 * - `url: null` rows, absent Assets and absent Finding links are plain text:
 *   no dead link, handler or tab stop.
 * - W4-03 unit 8 (u5, u6): on a mini-grid Site the separate decision-context
 *   overlay reads the current page's case IDs at the list's exact `known_at`
 *   and adds `Decision context:` after the Incident Finding links and as a
 *   secondary Maintenance Activity line. It changes no count, cursor, state,
 *   outcome or case URL; an answer for another page or cutoff is discarded.
 */
import { useEffect, useState, type FormEvent, type ReactNode } from "react";
import { Link } from "react-router-dom";

import { DataTable, Disclosure, Fact, FactList, Panel, ProductStatus, RailIcon, type ProductWords } from "../ui";
import type { DecisionRead, MiniDecisionsClient, WorkContextsBody, WorkDecisionContext } from "./miniDecisionsClient";
import { SOURCE_WORDS, SourceProvenanceRecord, sourceState } from "./sourceProvenance";
import {
  WORK_PAGE_LIMIT,
  type WorkClient,
  type WorkIndexBody,
  type WorkIndexResult,
  type WorkKind,
  type WorkRow,
  type WorkScope,
} from "./workClient";
import "./w1f4-action.css";
import "./w1f4-changes-work.css";
import "./w4-work-cases.css";

/** Earlier pages' cursors (null is page one), newest last; kept in history state so Previous survives reload. */
export type WorkTrail = (string | null)[];

export interface SiteWorkCasesLinks {
  /** One Finding at its pinned revision (`siteFindingHref`). */
  finding: (findingId: string, revisionId: string) => string;
}

export interface SiteWorkCasesProps {
  siteId: string;
  client: WorkClient;
  scope: WorkScope;
  trail: WorkTrail;
  links: SiteWorkCasesLinks;
  /** Go to another window or page (a navigation, so reload and back keep it). */
  onScope: (scope: WorkScope, trail: WorkTrail) => void;
  /** W4-03 unit 8: the decision-context overlay; given only for a mini-grid Site. */
  decisions?: MiniDecisionsClient;
}

/** One case's overlay state: `null` while unread (nothing shown), a list, or `"refused"`. */
type CaseContexts = WorkDecisionContext[] | "refused" | null;

export const DECISION_CONTEXT_UNAVAILABLE = "Decision context unavailable";
export const SCENARIO_DETAIL_UNAVAILABLE = "Scenario detail unavailable";

interface KindCopy {
  kind: WorkKind;
  /** The panel title (v69 rendered panels). */
  title: string;
  /** Plural noun in the status strip (`0 incidents`, `0 maintenance`). */
  noun: string;
  /** The global list the strip names as not available yet. */
  global: string;
  subcopy: string;
  columns: string[];
  /** Column widths at desktop width (spec copy table). */
  widths: string[];
  empty: [string, string];
  /** The window form's start label: Incidents by occurrence, requests by creation (B10). */
  windowStart: string;
  submit: string;
}

export const WORK_KIND_COPY: Record<WorkKind, KindCopy> = {
  incidents: {
    kind: "incidents",
    title: "Incidents at this site",
    noun: "incidents",
    global: "Incidents",
    subcopy: "A case links chronology, findings and work without copying them",
    columns: ["Case", "Window", "What happened", "Linked findings", "State"],
    widths: ["22%", "16%", "29%", "19%", "14%"],
    empty: [
      "No incidents at this site",
      "No operational case was opened in the selected period. A case comes from a linked chain of events, not from a single data gap.",
    ],
    windowStart: "Occurred from",
    submit: "Show incidents",
  },
  maintenance: {
    kind: "maintenance",
    title: "Maintenance at this site",
    noun: "maintenance",
    global: "Maintenance",
    subcopy: "Completed work is activity; the outcome is verified separately",
    columns: ["Work request", "Asset", "Activity", "Outcome", "Next evidence"],
    widths: ["22%", "18%", "23%", "15%", "22%"],
    empty: ["No maintenance work at this site", "No inspection or repair has been raised here in the selected period."],
    windowStart: "Raised from",
    submit: "Show maintenance",
  },
};

export const WORK_CONTEXT_NOTICE =
  "Case history is stored with this site. Incidents and Maintenance can be managed globally. The create flow is not available yet.";

/**
 * W6-01a A2 (spec section 1 "Site Work strip manage links"): the global page for this strip's kind, carrying the
 * Site window and the cutoff (an explicit `scope.knownAt` wins over the loaded list's `known_at`). Never the Site
 * cursor, limit or a Site key: the global page lists every authorized Site. The literal paths stay here because
 * the Site substrate imports nothing from `shell/`.
 */
export function globalWorkManageHref(kind: WorkKind, scope: WorkScope, selectedKnownAt?: string | null): string {
  const path = kind === "incidents" ? "/incidents" : "/maintenance";
  const cutoff = scope.knownAt ?? selectedKnownAt ?? null;
  const known = cutoff ? `&known_at=${encodeURIComponent(cutoff)}` : "";
  return `${path}?from=${encodeURIComponent(scope.from)}&to=${encodeURIComponent(scope.to)}${known}`;
}
export const WORK_COUNT_UNKNOWN = "Count unknown · work source unavailable";
export const WORK_STRIP_DETAIL = "These are work records at this site";
export const WORK_LINK_MISSING = "No selected source for linked evidence";
export const WORK_LINK_PENDING = "Linked evidence is being reassessed";

/** `2026-10-06 16:11 UTC`. */
export function workUtcText(instant: string | null | undefined): string {
  if (!instant) return "not recorded";
  const date = new Date(instant);
  if (Number.isNaN(date.getTime())) return instant;
  return `${date.toISOString().slice(0, 16).replace("T", " ")} UTC`;
}

const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

/** B10: `6 Oct · from 19:11` in East Africa Time (UTC+3, no daylight saving). */
export function eatWindowText(instant: string): string {
  const date = new Date(instant);
  if (Number.isNaN(date.getTime())) return instant;
  const eat = new Date(date.getTime() + 3 * 3600 * 1000);
  const hh = String(eat.getUTCHours()).padStart(2, "0");
  const mm = String(eat.getUTCMinutes()).padStart(2, "0");
  return `${eat.getUTCDate()} ${MONTHS[eat.getUTCMonth()]} · from ${hh}:${mm}`;
}

const STATE_LABEL: Record<string, string> = {
  OPEN: "Open",
  IN_PROGRESS: "In progress",
  CLOSED: "Closed",
  CANCELLED: "Cancelled",
  COMPLETED: "Completed",
  VERIFICATION_WINDOW: "Verification window",
};

/** Chip tones (S21 and the Run 7 dry-read): an open Incident is red; an open request is amber. */
export function stateTone(kind: WorkKind, state: string): "red" | "amber" | "blue" | "neutral" {
  if (state === "OPEN") return kind === "incidents" ? "red" : "amber";
  if (state === "IN_PROGRESS" || state === "COMPLETED" || state === "VERIFICATION_WINDOW") return "blue";
  return "neutral";
}

function StateChip({ kind, state }: { kind: WorkKind; state: string }) {
  const tone = stateTone(kind, state);
  return (
    <span
      className={`w1f4-action-badge${tone === "neutral" ? "" : ` w1f4-action-badge--${tone}`}`}
      data-work-state={state}
      data-work-tone={tone}
    >
      {STATE_LABEL[state] ?? state}
    </span>
  );
}

/** `Kobo` from `Kobo Mini-grid`: the mock's short name, for the status copy only (B10). */
const shortName = (name: string) => name.trim().split(/\s+/)[0] ?? name;

const firstDay = (instant: string) => new Date(instant).toISOString().slice(0, 10);
const lastDay = (to: string) => new Date(new Date(to).getTime() - 1).toISOString().slice(0, 10);

function WindowForm({ copy, scope, onScope }: { copy: KindCopy; scope: WorkScope; onScope: SiteWorkCasesProps["onScope"] }) {
  const valid = !Number.isNaN(new Date(scope.from).getTime()) && !Number.isNaN(new Date(scope.to).getTime());
  const [first, setFirst] = useState(valid ? firstDay(scope.from) : "");
  const [last, setLast] = useState(valid ? lastDay(scope.to) : "");
  useEffect(() => {
    if (valid) {
      setFirst(firstDay(scope.from));
      setLast(lastDay(scope.to));
    }
  }, [scope.from, scope.to, valid]);
  const submit = (event: FormEvent) => {
    event.preventDefault();
    if (!first || !last) return;
    const to = new Date(`${last}T00:00:00Z`);
    to.setUTCDate(to.getUTCDate() + 1);
    // A new window clears the cutoff, the cursor and the earlier pages.
    onScope({ from: `${first}T00:00:00Z`, to: `${to.toISOString().slice(0, 10)}T00:00:00Z`, knownAt: null, cursor: null }, []);
  };
  return (
    <form onSubmit={submit} className="v69-chips w1f4-work-window" data-work-window aria-label={`${copy.global} window`}>
      <label className="w1f4-work-window__field">
        {`${copy.windowStart} `}
        <input className="v69-chip-control" type="date" value={first} onChange={(event) => setFirst(event.target.value)} />
      </label>
      <label className="w1f4-work-window__field">
        {"to (included) "}
        <input className="v69-chip-control" type="date" value={last} onChange={(event) => setLast(event.target.value)} />
      </label>
      <button className="button" type="submit">
        {copy.submit}
      </button>
    </form>
  );
}

/** The list status, as strip words: a link qualification, never a verdict on the cases. */
function statusWords(body: WorkIndexBody): { label: string; tone: "neutral" | "amber" } | null {
  switch (body.status) {
    case "CURRENT":
      return null;
    case "HISTORICAL":
      return { label: `Read as of ${workUtcText(body.known_at)}`, tone: "neutral" };
    case "PENDING_RECOMPUTE":
      return { label: WORK_LINK_PENDING, tone: "amber" };
    case "STALE_SOURCE":
      return { label: "Linked evidence source is out of date", tone: "amber" };
    default:
      return { label: WORK_LINK_MISSING, tone: "neutral" };
  }
}

function WorkStrip({ copy, result, scope }: { copy: KindCopy; result: WorkIndexResult | null; scope: WorkScope }) {
  const loaded = result !== null && result.status === "loaded" ? result.value : null;
  const words = loaded ? statusWords(loaded) : null;
  return (
    <div className="status-strip status-strip--line" aria-label={`${copy.title}, scope`}>
      <span className="status-strip__lead" data-work-scope>
        {loaded ? (
          <>
            <strong>Scoped to {shortName(loaded.site_name)}</strong> · {loaded.total_count} {copy.noun}
          </>
        ) : result === null ? (
          <>Reading work records</>
        ) : (
          <>{WORK_COUNT_UNKNOWN}</>
        )}
      </span>
      <span className="muted status-strip__item">
        {WORK_STRIP_DETAIL}
        {words === null ? null : (
          <>
            {" · "}
            <span data-work-status={loaded?.status} data-work-status-tone={words.tone}>
              {words.label}
            </span>
          </>
        )}
      </span>
      <span className="muted status-strip__item" data-work-manage>
        {/* W6-01b B2: both strips link to their live global root (Incidents since W6-01a, Maintenance since B2). */}
        <Link to={globalWorkManageHref(copy.kind, scope, loaded ? loaded.known_at : null)} data-work-manage-link>
          {`Manage in ${copy.global}`}
        </Link>
      </span>
    </div>
  );
}

/** The panel's refusal state: the API table's UI copy, through the shared status line; never a zero. */
const REFUSAL: Record<string, { label: string; sentence: string; tone: ProductWords["tone"] }> = {
  unauthenticated: { label: "Sign in required", sentence: "Sign in to see work at this site.", tone: "problem" },
  forbidden: { label: "No access", sentence: "You do not have access to this site's work.", tone: "problem" },
  not_found: { label: "Site not found", sentence: "This site was not found.", tone: "problem" },
  basis_changed: { label: "This list changed", sentence: "The list changed. Reload the first page.", tone: "waiting" },
  invalid: { label: "This list cannot be shown", sentence: "Reload the work list.", tone: "limited" },
  unavailable: { label: "Work records unavailable", sentence: "Work records are unavailable right now. Try again.", tone: "problem" },
};

function Refused({
  copy,
  result,
  scope,
  onScope,
}: {
  copy: KindCopy;
  result: Exclude<WorkIndexResult, { status: "loaded" }>;
  scope: WorkScope;
  onScope: SiteWorkCasesProps["onScope"];
}) {
  const entry = REFUSAL[result.status] ?? REFUSAL.unavailable;
  // A window refusal keeps the server's own message (the reason is in it); a cursor refusal reads "Reload".
  const sentence =
    result.status === "invalid" && result.code !== "INVALID_CURSOR" && result.message ? result.message : entry.sentence;
  const words: ProductWords = { label: entry.label, sentence, tone: entry.tone, code: result.code, unrecognised: false };
  const restart = result.status === "basis_changed" || (result.status === "invalid" && result.code === "INVALID_CURSOR");
  return (
    <div className="work-cases-state" data-work-refused={result.status} data-work-code={result.code ?? ""}>
      <ProductStatus words={words} scope={`${copy.global} at this site`} asOf={null} inline />
      {restart ? (
        <p>
          <button
            type="button"
            className="link-button"
            data-work-restart
            onClick={() => onScope({ from: scope.from, to: scope.to, knownAt: null, cursor: null }, [])}
          >
            Reload the first page
          </button>
        </p>
      ) : null}
    </div>
  );
}

function Basis({ body }: { body: WorkIndexBody }) {
  const state = sourceState(body.source_provenance);
  return (
    <Disclosure name="work-basis" summary="What this list is based on" variant="tech">
      <FactList>
        <Fact term="Window">
          {workUtcText(body.window.from)} to {workUtcText(body.window.to)} {body.window.bounds}
        </Fact>
        <Fact term="Read as of">{workUtcText(body.known_at)}</Fact>
        <Fact term="Linked evidence">
          <span data-work-coverage={body.coverage.state}>
            {body.coverage.state}
            {body.coverage.reason ? ` (${body.coverage.reason})` : ""}
          </span>
        </Fact>
        <Fact term="Source of cited records">
          <span data-source-provenance={state}>{SOURCE_WORDS[state].label}</span>
        </Fact>
        <Fact term="List fence">
          <code data-work-selection-token data-vocabulary-exempt="source-reference">
            {body.selection_token}
          </code>
        </Fact>
      </FactList>
      {body.source_provenance ? <SourceProvenanceRecord provenance={body.source_provenance} /> : null}
    </Disclosure>
  );
}

/** The exact identities and UTC times behind one row: never truncated, closed by default. */
function RowDetail({ row }: { row: WorkRow }) {
  return (
    <Disclosure name={`work-row-${row.case_id}`} summary="UTC and IDs" variant="inline">
      <FactList>
        <Fact term="Occurred">{workUtcText(row.occurred_at)}</Fact>
        <Fact term="Recorded">{workUtcText(row.recorded_at)}</Fact>
        <Fact term="Case ID">
          <code data-vocabulary-exempt="source-reference">{row.case_id}</code>
        </Fact>
        <Fact term="Version ID">
          <code data-vocabulary-exempt="source-reference">{row.revision_id}</code>
        </Fact>
        {row.record_id ? (
          <Fact term="Activity record ID">
            <code data-vocabulary-exempt="source-reference">{row.record_id}</code>
          </Fact>
        ) : null}
        {row.incident_id ? (
          <Fact term="Incident ID">
            <code data-vocabulary-exempt="source-reference">{row.incident_id}</code>
          </Fact>
        ) : null}
        {row.action_links.length > 0 ? (
          <Fact term="Linked actions">
            {row.action_links.map((a, i) => (
              <span key={`${a.action_id}:${a.action_event_id}`} data-work-action-link={a.action_id}>
                {i > 0 ? ", " : null}
                {a.href ? <Link to={a.href}>{a.label}</Link> : a.label}
              </span>
            ))}
          </Fact>
        ) : null}
        <Fact term="Source of cited records">{SOURCE_WORDS[sourceState(row.source_provenance)].label}</Fact>
      </FactList>
    </Disclosure>
  );
}

/**
 * u5 unit 8 / u6: `Decision context:` and each association (Opportunity first); a typed Opportunity URL links, a
 * Scenario has no detail route, and a refused overlay says so without hiding the row or implying no link.
 */
function DecisionContext({ contexts }: { contexts: CaseContexts }) {
  if (contexts === null || (Array.isArray(contexts) && contexts.length === 0)) return null;
  if (contexts === "refused") {
    return (
      <span className="work-cases-context muted" data-work-decision-context="unavailable">
        {DECISION_CONTEXT_UNAVAILABLE}
      </span>
    );
  }
  return (
    <span className="work-cases-context" data-work-decision-context="loaded">
      Decision context:{" "}
      {contexts.map((c, i) => (
        <span key={`${c.kind}:${c.id}`} data-work-decision={c.kind}>
          {i > 0 ? " · " : null}
          {c.url ? (
            <Link to={c.url}>{c.label}</Link>
          ) : c.kind === "SCENARIO" && c.label !== DECISION_CONTEXT_UNAVAILABLE ? (
            <>
              {c.label} <span className="muted">({SCENARIO_DETAIL_UNAVAILABLE})</span>
            </>
          ) : (
            c.label
          )}
        </span>
      ))}
    </span>
  );
}

function FindingLinks({ row, links }: { row: WorkRow; links: SiteWorkCasesLinks }) {
  if (row.finding_links.length === 0) return <span className="muted">No linked finding</span>;
  return (
    <>
      {row.finding_links.map((f, i) => (
        <span key={`${f.finding_id}:${f.finding_revision_id}`} data-work-finding={f.finding_id}>
          {i > 0 ? " · " : null}
          {f.href ? (
            <Link to={links.finding(f.finding_id, f.finding_revision_id)} data-work-finding-link>
              {`Finding ${f.finding_id.slice(0, 8)}`}
            </Link>
          ) : (
            <span data-work-finding-unlinked>{`Finding ${f.finding_id.slice(0, 8)}`}</span>
          )}
        </span>
      ))}
    </>
  );
}

/** A case title: plain text while `url` is null (no product detail route yet). */
function CaseTitle({ row }: { row: WorkRow }) {
  const label = `${row.code} · ${row.title}`;
  return (
    <span className="work-cases-clamp" data-work-case-title title={label}>
      {row.url ? <Link to={row.url}>{label}</Link> : label}
    </span>
  );
}

function IncidentCells({ row, links, contexts }: { row: WorkRow; links: SiteWorkCasesLinks; contexts: CaseContexts }) {
  return (
    <>
      <td className="work-cases-first">
        <CaseTitle row={row} />
      </td>
      <td>
        <span data-work-window>{eatWindowText(row.occurred_at)}</span>
        <RowDetail row={row} />
      </td>
      <td>
        <span className="work-cases-clamp" title={row.narrative}>
          {row.narrative}
        </span>
      </td>
      <td>
        <FindingLinks row={row} links={links} />
        <DecisionContext contexts={contexts} />
      </td>
      <td>
        <StateChip kind="incidents" state={row.state} />
      </td>
    </>
  );
}

function MaintenanceCells({ row, contexts }: { row: WorkRow; contexts: CaseContexts }) {
  return (
    <>
      <td className="work-cases-first">
        <CaseTitle row={row} />
      </td>
      <td>
        {row.asset_label ? <span data-work-asset>{row.asset_label}</span> : <span className="muted">No asset linked</span>}
        <RowDetail row={row} />
      </td>
      <td>
        <span className="work-cases-clamp">
          <StateChip kind="maintenance" state={row.request_state ?? row.state} />{" "}
          <span data-work-activity>{row.activity ?? "No activity recorded"}</span>
        </span>
        <DecisionContext contexts={contexts} />
      </td>
      <td>
        <span className="work-cases-clamp">
          <span className="w1f4-action-badge w1f4-action-badge--amber" data-work-outcome={row.outcome_state ?? "UNVERIFIED"}>
            Unverified
          </span>{" "}
          <span data-work-outcome-note>{row.outcome_note ?? "No outcome recorded"}</span>
        </span>
      </td>
      <td>
        <span className="work-cases-clamp">{row.next_evidence_copy ?? "No next evidence recorded"}</span>
      </td>
    </>
  );
}

function Rows({
  copy,
  body,
  links,
  overlay,
}: {
  copy: KindCopy;
  body: WorkIndexBody;
  links: SiteWorkCasesLinks;
  overlay: DecisionRead<WorkContextsBody> | null;
}) {
  // PR-12.3: a refused Incident overlay is one line beside the table for the displayed rows, not one per row; the
  // rows keep their canonical Finding links and show no context. Maintenance keeps its row-level copy.
  const panelRefused = copy.kind === "incidents" && overlay !== null && overlay.status !== "loaded";
  const contextsOf = (caseId: string): CaseContexts =>
    overlay === null || panelRefused
      ? null
      : overlay.status === "loaded"
        ? (overlay.value.contexts[caseId] ?? "refused")
        : "refused";
  return (
    <div className="work-cases-table" data-work-table={copy.kind}>
      {panelRefused ? (
        <p
          className="work-cases-context work-cases-context--panel muted"
          data-work-decision-context="unavailable"
          data-work-decision-context-scope={body.rows.map((r) => r.case_id).join(" ")}
        >
          {DECISION_CONTEXT_UNAVAILABLE}
        </p>
      ) : null}
      <DataTable labelledBy={`site-work-${copy.kind}-heading`}>
        <colgroup>
          {copy.widths.map((width, i) => (
            <col key={i} style={{ width }} />
          ))}
        </colgroup>
        <thead>
          <tr>
            {copy.columns.map((c) => (
              <th scope="col" key={c}>
                {c}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {body.rows.map((row) => (
            <tr key={row.case_id} data-work-row={row.case_id} data-work-revision={row.revision_id}>
              {copy.kind === "incidents" ? (
                <IncidentCells row={row} links={links} contexts={contextsOf(row.case_id)} />
              ) : (
                <MaintenanceCells row={row} contexts={contextsOf(row.case_id)} />
              )}
            </tr>
          ))}
        </tbody>
      </DataTable>
    </div>
  );
}

function Pages({
  body,
  scope,
  trail,
  onScope,
}: {
  body: WorkIndexBody;
  scope: WorkScope;
  trail: WorkTrail;
  onScope: SiteWorkCasesProps["onScope"];
}) {
  // The page number is known when the earlier cursors are (first page, or pages reached in this tab).
  const known = !scope.cursor || trail.length > 0;
  const first = trail.length * WORK_PAGE_LIMIT + 1;
  const last = first + body.rows.length - 1;
  const bound = { from: scope.from, to: scope.to, knownAt: body.known_at };
  return (
    <nav aria-label="Work list pages" className="w1f4-work-pages" data-work-pages>
      <span data-work-showing>
        {known ? `Showing ${first}–${last} of ${body.total_count}` : `Showing ${body.rows.length} of ${body.total_count}`}
      </span>
      <span className="work-cases-scroll-hint" aria-hidden="true">
        Scroll the table for more columns →
      </span>
      {scope.cursor ? (
        <button
          type="button"
          className="link-button"
          data-work-previous
          onClick={() => onScope({ ...bound, cursor: trail.length > 0 ? trail[trail.length - 1] : null }, trail.slice(0, -1))}
        >
          Previous
        </button>
      ) : null}
      {body.next_cursor ? (
        <button
          type="button"
          className="link-button"
          data-work-next
          onClick={() => onScope({ ...bound, cursor: body.next_cursor }, [...trail, scope.cursor ?? null])}
        >
          Next
        </button>
      ) : null}
    </nav>
  );
}

function CoverageLine({ body }: { body: WorkIndexBody }) {
  if (body.coverage.state === "COMPLETE") return null;
  const pending = body.coverage.reason === "LINK_WORK_PENDING" || body.coverage.reason === "LINK_SOURCE_STALE";
  const words: ProductWords = pending
    ? { label: WORK_LINK_PENDING, sentence: "Linked evidence is being reassessed.", tone: "waiting", code: body.coverage.reason, unrecognised: false }
    : { label: WORK_LINK_MISSING, sentence: "A linked record has no selected source.", tone: "neutral", code: body.coverage.reason, unrecognised: false };
  return (
    <p className="work-cases-coverage" data-work-coverage-line={body.coverage.reason ?? body.coverage.state}>
      <ProductStatus words={words} scope="Linked evidence" asOf={body.known_at} inline />
    </p>
  );
}

/**
 * The overlay for exactly this page: its case IDs at its `known_at`. An answer keyed to another page, cutoff or
 * selection token is never shown (closure 1 work overlay: discard responses from a prior list token).
 */
function useDecisionOverlay(
  decisions: MiniDecisionsClient | undefined,
  siteId: string,
  body: WorkIndexBody,
): DecisionRead<WorkContextsBody> | null {
  const caseIds = body.rows.map((r) => r.case_id);
  const key = [siteId, body.known_at, body.selection_token, ...caseIds].join("|");
  const [state, setState] = useState<{ key: string; read: DecisionRead<WorkContextsBody> } | null>(null);
  useEffect(() => {
    if (decisions === undefined || caseIds.length === 0) return undefined;
    let active = true;
    void decisions.getWorkContexts(siteId, caseIds, body.known_at).then((read) => {
      if (active) setState({ key, read });
    });
    return () => {
      active = false;
    };
    // `key` carries the Site, cutoff, token and the page's case IDs.
  }, [decisions, key]);
  return state !== null && state.key === key ? state.read : null;
}

function Loaded({
  copy,
  body,
  scope,
  trail,
  links,
  onScope,
  siteId,
  decisions,
}: {
  copy: KindCopy;
  body: WorkIndexBody;
  scope: WorkScope;
  trail: WorkTrail;
  links: SiteWorkCasesLinks;
  onScope: SiteWorkCasesProps["onScope"];
  siteId: string;
  decisions?: MiniDecisionsClient;
}) {
  const overlay = useDecisionOverlay(decisions, siteId, body);
  if (body.total_count === 0) {
    return (
      <>
        <div className="work-cases-empty" data-work-empty>
          <span className="work-cases-empty__icon" data-work-empty-icon aria-hidden="true">
            <RailIcon name="evidence" />
          </span>
          <h3>{copy.empty[0]}</h3>
          <p>{copy.empty[1]}</p>
        </div>
        <div className="w1f4-work-foot">
          <Basis body={body} />
        </div>
      </>
    );
  }
  return (
    <div data-work-loaded>
      <CoverageLine body={body} />
      <Rows copy={copy} body={body} links={links} overlay={overlay} />
      <div className="w1f4-work-foot">
        <Pages body={body} scope={scope} trail={trail} onScope={onScope} />
        <Basis body={body} />
      </div>
    </div>
  );
}

function Body({ copy, children }: { copy: KindCopy; children: ReactNode }) {
  return <div className="w1f4-changes-work work-cases" data-site-work={copy.kind}>{children}</div>;
}

export function SiteWorkCases({
  kind,
  siteId,
  client,
  scope,
  trail,
  links,
  onScope,
  decisions,
}: SiteWorkCasesProps & { kind: WorkKind }) {
  const copy = WORK_KIND_COPY[kind];
  const [result, setResult] = useState<WorkIndexResult | null>(null);
  const { from, to, knownAt, cursor } = scope;
  useEffect(() => {
    let active = true;
    setResult(null);
    void client.getWorkIndex(siteId, kind, { from, to, knownAt, cursor }).then((loaded) => {
      if (active) setResult(loaded);
    });
    return () => {
      active = false;
    };
  }, [client, siteId, kind, from, to, knownAt, cursor]);
  return (
    <Body copy={copy}>
      <WorkStrip copy={copy} result={result} scope={scope} />
      <Panel
        heading={copy.title}
        headingId={`site-work-${kind}-heading`}
        description={copy.subcopy}
        actions={<WindowForm copy={copy} scope={scope} onScope={onScope} />}
      >
        {result === null ? (
          <p data-work-loading>Loading the site&apos;s work records.</p>
        ) : result.status === "loaded" ? (
          <Loaded
            copy={copy}
            body={result.value}
            scope={scope}
            trail={trail}
            links={links}
            onScope={onScope}
            siteId={siteId}
            decisions={decisions}
          />
        ) : (
          <Refused copy={copy} result={result} scope={scope} onScope={onScope} />
        )}
      </Panel>
      <p className="notice notice--info" data-work-notice>
        {WORK_CONTEXT_NOTICE}
      </p>
    </Body>
  );
}

