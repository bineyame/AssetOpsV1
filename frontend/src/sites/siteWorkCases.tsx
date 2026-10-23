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
import { useEffect, useRef, useState, type FormEvent, type ReactNode } from "react";
import { Link } from "react-router-dom";

import { DataTable, Disclosure, Fact, FactList, Notice, Panel, ProductStatus, RailIcon, type ProductWords } from "../ui";
import { globalWorkRequestHref } from "../work/globalWorkClient";
import { READ_FULL_TEXT, coldCurrentnessNotice, coldCurrentnessTone, isLongText } from "./coldWorkPresentation";
import type { DomainStatus } from "./domainActionClient";
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
  /**
   * W5-02 K2 ruling 23: the W4 in-panel window form. On by default (MINIGRID keeps it); a COLDCHAIN Site passes
   * `false` because its page-local `Window` control after the Work subtabs is the one date form.
   */
  windowForm?: boolean;
  /**
   * W5-02 K3a (P-K3a-2): the selected Site's type, IANA timezone and stored code. A COLDCHAIN Site gets the cold case
   * presentation (strip, currentness notice, Site-time Window, plain Findings, WR Overview link); every other type
   * keeps the W4 presentation unchanged.
   */
  site?: SiteWorkCasesSite;
}

export interface SiteWorkCasesSite {
  siteType: string;
  timezone: string;
  /** The stored Site code (`site_id` on the Site read). */
  code: string;
}

/** The COLDCHAIN case-cell context: the selected Site and the page's explicit cutoff. */
interface ColdCells {
  site: SiteWorkCasesSite;
  knownAt: string | null;
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

// MOCK DEVIATION (D1) R01 (spec M2): the v69 cold Work notice's second sentence promises a global create flow, which
// does not exist (W4 commands are SERVICE-only); the mock notice keeps its form and first sentence only.
/** W5-02 K2a (P-K2a-42): the COLDCHAIN Work context notice; K3a reuses it on the cold case tabs. */
export const WORK_CONTEXT_NOTICE_DOMAIN = "Opening a record moves you to its own area; the breadcrumb keeps this site.";

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
/**
 * W5-02 K3a (K3 pre-flight ruling 6): the COLDCHAIN case strip detail, the v69 `siteWorkScreen` sentence
 * (`index.html:341`), with its `Manage in {kind} →` link to the mounted W6 root. MINIGRID keeps `WORK_STRIP_DETAIL`.
 */
export const WORK_STRIP_DETAIL_DOMAIN: Record<WorkKind, string> = {
  incidents: "Same records and states as the global Incidents list",
  maintenance: "Same records and states as the global Maintenance list",
};
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

/**
 * W5-02 K3a (M5 withdrawn, RESTORE TO MOCK): `6 Oct · from 19:11` in the selected Site's stored IANA timezone. The
 * month is the mock's `Jan`…`Dec` table (`Sep`, never Intl's `Sept`); the UTC instant itself is unchanged.
 */
export function siteWindowText(instant: string, timezone: string): string {
  const date = new Date(instant);
  if (Number.isNaN(date.getTime())) return instant;
  const parts = Object.fromEntries(
    new Intl.DateTimeFormat("en-GB", {
      timeZone: timezone,
      day: "numeric",
      month: "numeric",
      hour: "2-digit",
      minute: "2-digit",
      hourCycle: "h23",
    })
      .formatToParts(date)
      .map((p) => [p.type, p.value]),
  );
  // A numeric month makes en-GB pad the day; the mock shows `6 Oct`, so the day is read as a number.
  return `${Number(parts.day)} ${MONTHS[Number(parts.month) - 1]} · from ${parts.hour}:${parts.minute}`;
}

/**
 * W5-02 K3a (P-K3a-3, R89 D4): the wire has only the composite `asset_label` (`generator-1 · GENERATOR`). Only a
 * final exact `GENERATOR` token reads as `backup generator`; any other label is shown unchanged.
 */
export function coldAssetLabel(label: string): string {
  const suffix = " · GENERATOR";
  return label.endsWith(suffix) ? `${label.slice(0, -suffix.length)} · backup generator` : label;
}

/**
 * W5-02 K3a (P-G-4, MOCK DEVIATION (D1) R68): a cold WR code opens the mounted W6 C2 request Overview for the
 * selected case ID and stored Site code, plus the explicit cutoff when present (the mock's `workverification`
 * destination is not mounted).
 */
export function coldRequestHref(caseId: string, siteCode: string, knownAt: string | null | undefined): string {
  return globalWorkRequestHref(`/maintenance/requests/${encodeURIComponent(caseId)}`, { site_id: siteCode, known_at: knownAt ?? null });
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
export const shortName = (name: string) => name.trim().split(/\s+/)[0] ?? name;

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

function WorkStrip({
  copy,
  result,
  scope,
  cold,
}: {
  copy: KindCopy;
  result: WorkIndexResult | null;
  scope: WorkScope;
  cold: boolean;
}) {
  const loaded = result !== null && result.status === "loaded" ? result.value : null;
  // K3a (P-K3a-7): on COLDCHAIN the currentness notice below the strip carries the status; no duplicate strip label.
  const words = loaded && !cold ? statusWords(loaded) : null;
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
      <span className="muted status-strip__item" data-work-strip-detail>
        {cold ? WORK_STRIP_DETAIL_DOMAIN[copy.kind] : WORK_STRIP_DETAIL}
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
          {cold ? `Manage in ${copy.global} →` : `Manage in ${copy.global}`}
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
function RowDetail({ row, assetId = false }: { row: WorkRow; assetId?: boolean }) {
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
        {/* K3a (K3 pre-flight ruling 2, R89): the selected asset ID, cold Maintenance only; no second disclosure. */}
        {assetId && row.asset_id ? (
          <Fact term="Asset ID">
            <code data-vocabulary-exempt="source-reference" data-work-asset-id>
              {row.asset_id}
            </code>
          </Fact>
        ) : null}
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
              <span key={`${a.kind ?? "ACTION"}:${a.action_id}:${a.action_event_id ?? a.finding_revision_id}`} data-work-action-link={a.action_id}>
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

/**
 * W5-02 K3b (K3 pre-flight ruling 7, MOCK DEVIATION (D2) R94): on COLDCHAIN case cells a long selected value previews
 * at two lines with the full value in a `Read full text` disclosure; while it is open the preview is removed and the
 * body shows the value once, and closing restores it (the K2 ruling 20 behaviour of the cold Actions list).
 */
function CaseLongText({ text, name, children }: { text: string; name: string; children?: ReactNode }) {
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
    <div className="cold-work-longtext" ref={wrapper} data-cold-work-longtext={open ? "open" : "closed"}>
      {open ? null : (
        <span className="work-cases-clamp" data-cold-work-preview={name}>
          {children ?? text}
        </span>
      )}
      <Disclosure name={name} summary={READ_FULL_TEXT}>
        {open ? (children ?? text) : text}
      </Disclosure>
    </div>
  );
}

/**
 * K3a: a cold case title. MOCK DEVIATION (D1) R73: the INC code stays plain (no Incident detail route is mounted).
 * MOCK DEVIATION (D1) R68: the WR code opens the mounted W6 C2 request Overview for the selected case ID (P-G-4).
 */
function ColdCaseTitle({ kind, row, cold }: { kind: WorkKind; row: WorkRow; cold: ColdCells }) {
  const label = `${row.code} · ${row.title}`;
  const href = kind === "maintenance" && row.case_id ? coldRequestHref(row.case_id, cold.site.code, cold.knownAt) : null;
  return (
    <span data-work-case-title>
      <CaseLongText text={label} name={`work-case-title-${row.case_id}`}>
        {href ? (
          <Link to={href} data-work-request-link>
            {label}
          </Link>
        ) : (
          label
        )}
      </CaseLongText>
    </span>
  );
}

/**
 * K3a (K2 ruling 4, K3 pre-flight ruling 2). MOCK DEVIATION (D1) R65: the mock's F-118/F-119 slots show
 * `Finding {id8}`. MOCK DEVIATION (D1) R66: plain text, never an anchor, because the cold Finding frame does not read
 * `revision_id`; each selected revision is in its own `Finding version` disclosure.
 */
function ColdFindingLinks({ row }: { row: WorkRow }) {
  if (row.finding_links.length === 0) return <span className="muted">No linked finding</span>;
  return (
    <>
      {row.finding_links.map((f, i) => (
        <span key={`${f.finding_id}:${f.finding_revision_id}`} data-work-finding={f.finding_id}>
          {i > 0 ? " · " : null}
          <span className="cold-work-code" data-work-finding-unlinked>{`Finding ${f.finding_id.slice(0, 8)}`}</span>
          <Disclosure name={`work-finding-${row.case_id}-${f.finding_revision_id}`} summary="Finding version" variant="inline">
            <code data-vocabulary-exempt="source-reference" data-work-finding-revision>
              {f.finding_revision_id}
            </code>
          </Disclosure>
        </span>
      ))}
    </>
  );
}

function ColdIncidentCells({ row, cold }: { row: WorkRow; cold: ColdCells }) {
  return (
    <>
      <td className="work-cases-first">
        <ColdCaseTitle kind="incidents" row={row} cold={cold} />
      </td>
      <td>
        <span data-work-window>{siteWindowText(row.occurred_at, cold.site.timezone)}</span>
        <RowDetail row={row} />
      </td>
      <td data-work-narrative>
        <CaseLongText text={row.narrative} name={`work-narrative-${row.case_id}`} />
      </td>
      <td>
        <ColdFindingLinks row={row} />
      </td>
      <td>
        <StateChip kind="incidents" state={row.state} />
      </td>
    </>
  );
}

function ColdMaintenanceCells({ row, cold }: { row: WorkRow; cold: ColdCells }) {
  return (
    <>
      <td className="work-cases-first">
        <ColdCaseTitle kind="maintenance" row={row} cold={cold} />
      </td>
      <td>
        {/* MOCK DEVIATION (D4) R89: the selected composite label, `generator-1 · backup generator`. */}
        {row.asset_label ? (
          <span data-work-asset>{coldAssetLabel(row.asset_label)}</span>
        ) : (
          <span className="muted">No asset linked</span>
        )}
        <RowDetail row={row} assetId />
      </td>
      <td data-work-activity-cell>
        {/* K3 pre-flight ruling 3: the selected request-state chip (`Completed` only for COMPLETED).
            MOCK DEVIATION (D2) R70: the stored activity in a same-cell `Activity recorded` disclosure. */}
        <StateChip kind="maintenance" state={row.request_state ?? row.state} />
        {row.activity ? (
          <Disclosure name={`work-activity-${row.case_id}`} summary="Activity recorded" variant="inline">
            <span data-work-activity>
              <CaseLongText text={row.activity} name={`work-activity-text-${row.case_id}`} />
            </span>
          </Disclosure>
        ) : null}
      </td>
      <td data-work-outcome-cell>
        {/* MOCK DEVIATION (D2) R71: the `Unverified` badge, then the selected outcome note in its own disclosure. */}
        <span className="w1f4-action-badge w1f4-action-badge--amber" data-work-outcome={row.outcome_state ?? "UNVERIFIED"}>
          Unverified
        </span>
        {row.outcome_note ? (
          <Disclosure name={`work-outcome-${row.case_id}`} summary="Outcome note" variant="inline">
            <span data-work-outcome-note>
              <CaseLongText text={row.outcome_note} name={`work-outcome-text-${row.case_id}`} />
            </span>
          </Disclosure>
        ) : null}
      </td>
      <td data-work-next-evidence>
        {/* MOCK DEVIATION (D1) R72: the selected next-evidence copy, or the honest gap; never a witnessed test. */}
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
  cold,
}: {
  copy: KindCopy;
  body: WorkIndexBody;
  links: SiteWorkCasesLinks;
  overlay: DecisionRead<WorkContextsBody> | null;
  cold: ColdCells | null;
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
              {cold !== null ? (
                copy.kind === "incidents" ? (
                  <ColdIncidentCells row={row} cold={cold} />
                ) : (
                  <ColdMaintenanceCells row={row} cold={cold} />
                )
              ) : copy.kind === "incidents" ? (
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
  cold,
}: {
  copy: KindCopy;
  body: WorkIndexBody;
  scope: WorkScope;
  trail: WorkTrail;
  links: SiteWorkCasesLinks;
  onScope: SiteWorkCasesProps["onScope"];
  siteId: string;
  decisions?: MiniDecisionsClient;
  cold: ColdCells | null;
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
      {/* K3 pre-flight ruling 4: COLDCHAIN hides the coverage line; its currentness notice sits above the panel. */}
      {cold === null ? <CoverageLine body={body} /> : null}
      <Rows copy={copy} body={body} links={links} overlay={overlay} cold={cold} />
      {/* Cold: MOCK DEVIATION (D2) R93, the W4 Pages block below the table; MOCK DEVIATION (D2) R92, the selected
          `What this list is based on` disclosure at the panel foot (also after the complete-zero empty card). */}
      <div className="w1f4-work-foot">
        <Pages body={body} scope={scope} trail={trail} onScope={onScope} />
        <Basis body={body} />
      </div>
    </div>
  );
}

function Body({ copy, cold, children }: { copy: KindCopy; cold: boolean; children: ReactNode }) {
  return (
    <div className="w1f4-changes-work work-cases" data-site-work={copy.kind} data-cold-cases={cold ? "" : undefined}>
      {children}
    </div>
  );
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
  windowForm = true,
  site,
}: SiteWorkCasesProps & { kind: WorkKind }) {
  const copy = WORK_KIND_COPY[kind];
  const [result, setResult] = useState<WorkIndexResult | null>(null);
  const { from, to, knownAt, cursor } = scope;
  const cold: ColdCells | null = site !== undefined && site.siteType === "COLDCHAIN" ? { site, knownAt: knownAt ?? null } : null;
  const loadedBody = result !== null && result.status === "loaded" ? result.value : null;
  // K3a (P-K3a-7, K3 pre-flight ruling 5): the cold notice comes from the W4 envelope `status`, never `coverage`.
  const currentness =
    cold !== null && loadedBody !== null ? coldCurrentnessNotice(loadedBody.status as DomainStatus, loadedBody.known_at) : null;
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
    <Body copy={copy} cold={cold !== null}>
      <WorkStrip copy={copy} result={result} scope={scope} cold={cold !== null} />
      {/* MOCK DEVIATION (D2) R91 (K3 pre-flight ruling 5): the cold selected-state notice between strip and panel,
          blue for Historical/Unknown and amber for Pending recompute/Stale source; absent on CURRENT. */}
      {loadedBody !== null && currentness !== null ? (
        <Notice tone={coldCurrentnessTone(loadedBody.status as DomainStatus)} data={{ "data-cold-work-currentness": loadedBody.status }}>
          <RailIcon name="info" />
          <p>{currentness}</p>
        </Notice>
      ) : null}
      <Panel
        heading={copy.title}
        headingId={`site-work-${kind}-heading`}
        description={copy.subcopy}
        actions={windowForm ? <WindowForm copy={copy} scope={scope} onScope={onScope} /> : undefined}
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
            cold={cold}
          />
        ) : (
          <Refused copy={copy} result={result} scope={scope} onScope={onScope} />
        )}
      </Panel>
      {cold !== null ? (
        // MOCK DEVIATION (D1) R01: the mock notice's create-flow sentence is omitted (no create flow exists).
        <Notice tone="blue" data={{ "data-work-notice": "", "data-cold-work-notice": "" }}>
          <RailIcon name="info" />
          <p>{WORK_CONTEXT_NOTICE_DOMAIN}</p>
        </Notice>
      ) : (
        <p className="notice notice--info" data-work-notice>
          {WORK_CONTEXT_NOTICE}
        </p>
      )}
    </Body>
  );
}

