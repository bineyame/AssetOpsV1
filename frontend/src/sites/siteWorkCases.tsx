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
import { siteDateTimeText, siteLocalDate, siteLocalMidnightUtc, siteLocalParts, siteZoneLabel } from "./siteTime";
import type { DomainStatus } from "./domainActionClient";
import { EV_ACTION_LINK_LIVE, EV_SOURCE_FINDING_UNAVAILABLE, evActionHref } from "./evWorkPresentation";
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

/**
 * The domain case-cell context (COLDCHAIN since W5-02 K3a, EV_CHARGING since W5-04 V3a): the selected Site and the
 * page's explicit cutoff. `legacyCold` is true only on COLDCHAIN, which keeps its K3 `data-cold-work-*` attributes,
 * `cold-work-*` classes and cell rules byte-for-byte; an EV Site gets only `data-domain-work-*` / `domain-work-*`
 * names (W5-04 readiness rulings 18 and 45).
 */
interface DomainCells {
  site: SiteWorkCasesSite;
  knownAt: string | null;
  legacyCold: boolean;
  /** W5-04 V4a (ruling 71): the page's selected window, for the EV case-row Action link. */
  from: string;
  to: string;
}

/**
 * W5-04 V4a (readiness ruling 71, R113 closed): the EV case-row domain Action address keeps the page's selected
 * `from`, `to` and explicit `known_at`; cold (and W4 MINIGRID, which has no domain cells) keep the server href.
 */
function evCaseActionHref(cells: DomainCells): ((href: string) => string) | undefined {
  return cells.legacyCold || !EV_ACTION_LINK_LIVE ? undefined : (href) => evActionHref(href, cells);
}

/** The Site types with the domain case presentation; MINIGRID (and any other type) keeps W4's. */
const DOMAIN_CASE_SITE_TYPES = new Set(["COLDCHAIN", "EV_CHARGING"]);

/** `data-cold-work-{name}` on COLDCHAIN, `data-domain-work-{name}` on EV (ruling 45: EV never gets cold names). */
function caseAttrs(legacyCold: boolean, name: string, value: string): Record<string, string> {
  return { [`data-${legacyCold ? "cold" : "domain"}-work-${name}`]: value };
}

/** `cold-work-{name}` on COLDCHAIN, `domain-work-{name}` on EV. */
const caseClass = (legacyCold: boolean, name: string) => `${legacyCold ? "cold" : "domain"}-work-${name}`;

/** One case's overlay state: `null` while unread (nothing shown), a list, or `"refused"`. */
type CaseContexts = WorkDecisionContext[] | "refused" | null;

export const DECISION_CONTEXT_UNAVAILABLE = "Decision context unavailable";
export const SCENARIO_DETAIL_UNAVAILABLE = "Scenario detail unavailable";

interface KindCopy {
  kind: WorkKind;
  /** The panel title (v69 rendered panels). */
  title: string;
  /** post-W6 shell R319 (Q20): the strip's count nouns, singular and plural (`1 incident`, `2 maintenance cases`). */
  noun: { one: string; many: string };
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

/** post-W6 shell R319 (Q20): `1 incident`, `0 incidents`, `3 maintenance cases`. */
export function countWords(count: number, noun: { one: string; many: string }): string {
  return `${count} ${count === 1 ? noun.one : noun.many}`;
}

export const WORK_KIND_COPY: Record<WorkKind, KindCopy> = {
  incidents: {
    kind: "incidents",
    title: "Incidents at this site",
    noun: { one: "incident", many: "incidents" },
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
    noun: { one: "maintenance case", many: "maintenance cases" },
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
export function siteWindowText(instant: string, timezone: string | null | undefined, withZone = false): string {
  // post-W6 W4 R320 (Q8, W1 cross-card contract 1): one Site-time formatter, `sites/siteTime.ts`; a missing or invalid
  // zone falls back to UTC. `withZone` appends the zone label (the mini rows' primary Site-local text).
  const p = siteLocalParts(instant, timezone);
  if (p === null) return instant;
  const text = `${p.day} ${MONTHS[p.m - 1]} · from ${p.hh}:${p.mm}`;
  return withZone ? `${text} ${p.zone}` : text;
}

/** post-W6 W4 R320: `2026-10-06 19:11 EAT` in the Site zone (`UTC` when unusable); the stored UTC stays in disclosures. */
export function workSiteText(instant: string | null | undefined, timezone: string | null | undefined): string {
  if (!instant) return "not recorded";
  return siteDateTimeText(instant, timezone) ?? instant;
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

/** post-W6 W4 R320 (Q8): the window's Site-local first and last (included) days; the URL keeps UTC bounds. */
const firstDay = (instant: string, timeZone: string | null) => siteLocalDate(instant, timeZone);
const lastDay = (to: string, timeZone: string | null) => siteLocalDate(new Date(new Date(to).getTime() - 1).toISOString(), timeZone);
const nextDay = (isoDate: string) => {
  const d = new Date(`${isoDate}T00:00:00Z`);
  d.setUTCDate(d.getUTCDate() + 1);
  return d.toISOString().slice(0, 10);
};

function WindowForm({
  copy,
  scope,
  timeZone,
  onScope,
}: {
  copy: KindCopy;
  scope: WorkScope;
  timeZone: string | null;
  onScope: SiteWorkCasesProps["onScope"];
}) {
  const valid = !Number.isNaN(new Date(scope.from).getTime()) && !Number.isNaN(new Date(scope.to).getTime());
  const [first, setFirst] = useState(valid ? firstDay(scope.from, timeZone) : "");
  const [last, setLast] = useState(valid ? lastDay(scope.to, timeZone) : "");
  useEffect(() => {
    if (valid) {
      setFirst(firstDay(scope.from, timeZone));
      setLast(lastDay(scope.to, timeZone));
    }
  }, [scope.from, scope.to, valid, timeZone]);
  const zone = siteZoneLabel(timeZone, scope.from);
  const submit = (event: FormEvent) => {
    event.preventDefault();
    if (!first || !last) return;
    // A new window clears the cutoff, the cursor and the earlier pages; Site-local midnights, sent as UTC.
    onScope({ from: siteLocalMidnightUtc(first, timeZone), to: siteLocalMidnightUtc(nextDay(last), timeZone), knownAt: null, cursor: null }, []);
  };
  return (
    <form onSubmit={submit} className="v69-chips w1f4-work-window" data-work-window aria-label={`${copy.global} window`}>
      <label className="w1f4-work-window__field">
        {`${copy.windowStart} (${zone}) `}
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
function statusWords(body: WorkIndexBody, timeZone: string | null): { label: string; tone: "neutral" | "amber" } | null {
  switch (body.status) {
    case "CURRENT":
      return null;
    case "HISTORICAL":
      return { label: `Read as of ${workSiteText(body.known_at, timeZone)}`, tone: "neutral" };
    case "PENDING_RECOMPUTE":
      return { label: WORK_LINK_PENDING, tone: "amber" };
    case "STALE_SOURCE":
      return { label: "Linked evidence source is out of date", tone: "amber" };
    default:
      return { label: WORK_LINK_MISSING, tone: "neutral" };
  }
}

/** post-W6 W4 R322 (Q9): why the counts are not shown, from the same result classification as the page. */
export const WORK_COUNT_INVALID_WINDOW = "Counts not shown: the selected window is not valid.";
export const WORK_COUNT_EXPIRED_PAGE = "Counts not shown: this page of results expired.";

export function workCountGap(result: WorkIndexResult): string {
  if (result.status === "invalid") return result.code === "INVALID_CURSOR" ? WORK_COUNT_EXPIRED_PAGE : WORK_COUNT_INVALID_WINDOW;
  return WORK_COUNT_UNKNOWN;
}

function WorkStrip({
  copy,
  result,
  scope,
  cold,
  timeZone,
}: {
  copy: KindCopy;
  result: WorkIndexResult | null;
  scope: WorkScope;
  cold: boolean;
  timeZone: string | null;
}) {
  const loaded = result !== null && result.status === "loaded" ? result.value : null;
  // K3a (P-K3a-7): on COLDCHAIN the currentness notice below the strip carries the status; no duplicate strip label.
  const words = loaded && !cold ? statusWords(loaded, timeZone) : null;
  return (
    <div className="status-strip status-strip--line" aria-label={`${copy.title}, scope`}>
      <span className="status-strip__lead" data-work-scope>
        {loaded ? (
          <>
            <strong>Scoped to {shortName(loaded.site_name)}</strong> · {countWords(loaded.total_count, copy.noun)}
          </>
        ) : result === null ? (
          <>Reading work records</>
        ) : (
          <>{workCountGap(result)}</>
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
  invalid: { label: "This list cannot be shown", sentence: "This request cannot be used. Check your entries and try again.", tone: "limited" },
  unavailable: { label: "Work records unavailable", sentence: "Work records are unavailable right now. Try again.", tone: "problem" },
};

const WORK_MAX_DAYS = 31;

/** post-W6 W4 R322: the 422 sentence by code (Q4 wording), with the reversed and over-31-day causes from the bounds. */
export function workInvalidSentence(code: string | null, scope: Pick<WorkScope, "from" | "to">): string {
  if (code === "INVALID_CURSOR") return "This page of results expired. Return to the first page.";
  if (code === "INVALID_KNOWN_AT") return "Choose a valid evidence cutoff.";
  if (code === "INVALID_WINDOW") {
    const from = Date.parse(scope.from);
    const to = Date.parse(scope.to);
    if (!Number.isNaN(from) && !Number.isNaN(to)) {
      if (to <= from) return "The end must be after the start.";
      if (to - from > WORK_MAX_DAYS * 86_400_000) return `Choose a window of ${WORK_MAX_DAYS} days or fewer.`;
    }
    return "Choose a valid Site-local window.";
  }
  return "This request cannot be used. Check your entries and try again.";
}

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
  // post-W6 W4 R322: plain copy keyed on the code; the cause is named only when the requested bounds prove it. The
  // server message never reaches the page.
  const sentence = result.status === "invalid" ? workInvalidSentence(result.code, scope) : entry.sentence;
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

function Basis({ body, timeZone }: { body: WorkIndexBody; timeZone: string | null }) {
  const state = sourceState(body.source_provenance);
  return (
    <Disclosure name="work-basis" summary="What this list is based on" variant="tech">
      <FactList>
        <Fact term="Window">
          {workSiteText(body.window.from, timeZone)} to {workSiteText(body.window.to, timeZone)} {body.window.bounds}
          <span className="muted" data-work-window-utc>
            {` (${workUtcText(body.window.from)} to ${workUtcText(body.window.to)})`}
          </span>
        </Fact>
        <Fact term="Read as of">
          {workSiteText(body.known_at, timeZone)}
          <span className="muted">{` (${workUtcText(body.known_at)})`}</span>
        </Fact>
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
function RowDetail({
  row,
  assetId = false,
  plainDomainActions = false,
  domainActionHref,
}: {
  row: WorkRow;
  assetId?: boolean;
  /** W5-04 V4a (ruling 71): the EV domain Action address with the selected scope; absent keeps the server href. */
  domainActionHref?: (href: string) => string;
  /**
   * W5-04 V3a (MOCK DEVIATION (D1) R113, readiness ruling 46): on an EV Site a linked domain Action stays plain text
   * until V4a mounts the EV detail route (`EV_ACTION_LINK_LIVE`); no interim dead link to the W1 presenter.
   */
  plainDomainActions?: boolean;
}) {
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
                {a.href && !(plainDomainActions && a.kind === "DOMAIN_ACTION") ? (
                  <Link to={domainActionHref && a.kind === "DOMAIN_ACTION" ? domainActionHref(a.href) : a.href}>{a.label}</Link>
                ) : plainDomainActions && a.kind === "DOMAIN_ACTION" ? (
                  <span data-work-action-plain>{a.label}</span>
                ) : (
                  a.label
                )}
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
function DecisionContext({ contexts, caseId = "" }: { contexts: CaseContexts; caseId?: string }) {
  if (contexts === null || (Array.isArray(contexts) && contexts.length === 0)) return null;
  if (contexts === "refused") {
    return (
      <span className="work-cases-context muted" data-work-decision-context="unavailable">
        {DECISION_CONTEXT_UNAVAILABLE}
      </span>
    );
  }
  // post-W6 W4 R324 (Q12): a long context keeps its preview and gains `Read full text`; links stay in the open body.
  const full = `Decision context: ${contexts.map((c) => c.label).join(" · ")}`;
  return (
    <span className="work-cases-context-wrap" data-work-decision-context="loaded" title={full}>
      <CaseLongText text={full} name={`work-mini-context-${caseId}`} legacyCold={false}>
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
      </CaseLongText>
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

/**
 * post-W6 W4 R324 (Q12): a long mini value keeps its two-line preview and gains the cold/EV `Read full text`
 * disclosure (a keyboard-focusable summary; the complete text is in the DOM once opened). `title` stays supplemental.
 */
function MiniLongText({ text, name, children }: { text: string; name: string; children?: ReactNode }) {
  return (
    <span className="work-cases-mini-long" data-work-mini-long={name} title={text}>
      <CaseLongText text={text} name={name} legacyCold={false}>
        {children}
      </CaseLongText>
    </span>
  );
}

/** A case title: plain text while `url` is null (no product detail route yet). */
function CaseTitle({ row }: { row: WorkRow }) {
  const label = `${row.code} · ${row.title}`;
  return (
    <span data-work-case-title>
      <MiniLongText text={label} name={`work-mini-title-${row.case_id}`}>
        {row.url ? <Link to={row.url}>{label}</Link> : label}
      </MiniLongText>
    </span>
  );
}

function IncidentCells({
  row,
  links,
  contexts,
  timeZone,
}: {
  row: WorkRow;
  links: SiteWorkCasesLinks;
  contexts: CaseContexts;
  timeZone: string | null;
}) {
  return (
    <>
      <td className="work-cases-first">
        <CaseTitle row={row} />
      </td>
      <td>
        <span data-work-window>{siteWindowText(row.occurred_at, timeZone, true)}</span>
        <RowDetail row={row} />
      </td>
      <td>
        <MiniLongText text={row.narrative} name={`work-mini-narrative-${row.case_id}`} />
      </td>
      <td>
        <FindingLinks row={row} links={links} />
        <DecisionContext contexts={contexts} caseId={row.case_id} />
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
        <MiniLongText text={row.activity ?? "No activity recorded"} name={`work-mini-activity-${row.case_id}`}>
          <StateChip kind="maintenance" state={row.request_state ?? row.state} />{" "}
          <span data-work-activity>{row.activity ?? "No activity recorded"}</span>
        </MiniLongText>
        <DecisionContext contexts={contexts} caseId={row.case_id} />
      </td>
      <td>
        <MiniLongText text={row.outcome_note ?? "No outcome recorded"} name={`work-mini-outcome-${row.case_id}`}>
          <span className="w1f4-action-badge w1f4-action-badge--amber" data-work-outcome={row.outcome_state ?? "UNVERIFIED"}>
            Unverified
          </span>{" "}
          <span data-work-outcome-note>{row.outcome_note ?? "No outcome recorded"}</span>
        </MiniLongText>
      </td>
      <td>
        <MiniLongText text={row.next_evidence_copy ?? "No next evidence recorded"} name={`work-mini-next-${row.case_id}`} />
      </td>
    </>
  );
}

/**
 * W5-02 K3b (K3 pre-flight ruling 7, MOCK DEVIATION (D2) R94): on COLDCHAIN case cells a long selected value previews
 * at two lines with the full value in a `Read full text` disclosure; while it is open the preview is removed and the
 * body shows the value once, and closing restores it (the K2 ruling 20 behaviour of the cold Actions list).
 */
function CaseLongText({
  text,
  name,
  legacyCold,
  children,
}: {
  text: string;
  name: string;
  legacyCold: boolean;
  children?: ReactNode;
}) {
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
    <div className={caseClass(legacyCold, "longtext")} ref={wrapper} {...caseAttrs(legacyCold, "longtext", open ? "open" : "closed")}>
      {open ? null : (
        <span className="work-cases-clamp" {...caseAttrs(legacyCold, "preview", name)}>
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
 * K3a: a domain case title. MOCK DEVIATION (D1) R73 (cold) / R85 (EV): the INC code stays plain (no Incident detail
 * route is mounted). MOCK DEVIATION (D1) R68 (cold) / R83 (EV): the WR code opens the mounted W6 C2 request Overview
 * for the selected case ID, stored Site code and explicit cutoff (P-G-4). R94 (cold) / R107 (EV): long titles preview.
 */
function DomainCaseTitle({ kind, row, cells }: { kind: WorkKind; row: WorkRow; cells: DomainCells }) {
  const label = `${row.code} · ${row.title}`;
  const href = kind === "maintenance" && row.case_id ? coldRequestHref(row.case_id, cells.site.code, cells.knownAt) : null;
  return (
    <span data-work-case-title>
      <CaseLongText text={label} name={`work-case-title-${row.case_id}`} legacyCold={cells.legacyCold}>
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
 * K3a (K2 ruling 4, K3 pre-flight ruling 2). MOCK DEVIATION (D1) R65 (cold) / R74 (EV): the mock's F-118/F-119 or
 * F-130 slots show `Finding {id8}`. MOCK DEVIATION (D1) R66 (cold) / R75 (EV): plain text, never an anchor, because
 * the domain Finding frame does not read `revision_id`; each selected revision is in its own `Finding version`
 * disclosure, which on EV also carries the R75 sentence (as the EV Actions Source cell).
 */
function DomainFindingLinks({ row, legacyCold }: { row: WorkRow; legacyCold: boolean }) {
  if (row.finding_links.length === 0) return <span className="muted">No linked finding</span>;
  return (
    <>
      {row.finding_links.map((f, i) => (
        <span key={`${f.finding_id}:${f.finding_revision_id}`} data-work-finding={f.finding_id}>
          {i > 0 ? " · " : null}
          <span className={caseClass(legacyCold, "code")} data-work-finding-unlinked>{`Finding ${f.finding_id.slice(0, 8)}`}</span>
          <Disclosure name={`work-finding-${row.case_id}-${f.finding_revision_id}`} summary="Finding version" variant="inline">
            <code data-vocabulary-exempt="source-reference" data-work-finding-revision>
              {f.finding_revision_id}
            </code>
            {legacyCold ? null : (
              <>
                {" "}
                <span className="muted" data-domain-work-source-unavailable="">
                  {EV_SOURCE_FINDING_UNAVAILABLE}
                </span>
              </>
            )}
          </Disclosure>
        </span>
      ))}
    </>
  );
}

function DomainIncidentCells({ row, cells }: { row: WorkRow; cells: DomainCells }) {
  return (
    <>
      <td className="work-cases-first">
        <DomainCaseTitle kind="incidents" row={row} cells={cells} />
      </td>
      <td>
        {/* W5-02 K3a; W5-04 build spec E5 withdrawn (R-10): the occurrence time in the stored Site IANA zone. */}
        <span data-work-window>{siteWindowText(row.occurred_at, cells.site.timezone)}</span>
        <RowDetail row={row} plainDomainActions={!cells.legacyCold && !EV_ACTION_LINK_LIVE} domainActionHref={evCaseActionHref(cells)} />
      </td>
      <td data-work-narrative>
        <CaseLongText text={row.narrative} name={`work-narrative-${row.case_id}`} legacyCold={cells.legacyCold} />
      </td>
      <td>
        <DomainFindingLinks row={row} legacyCold={cells.legacyCold} />
      </td>
      <td>
        <StateChip kind="incidents" state={row.state} />
      </td>
    </>
  );
}

function DomainMaintenanceCells({ row, cells }: { row: WorkRow; cells: DomainCells }) {
  const lc = cells.legacyCold;
  return (
    <>
      <td className="work-cases-first">
        <DomainCaseTitle kind="maintenance" row={row} cells={cells} />
      </td>
      <td>
        {/* Cold: MOCK DEVIATION (D4) R89, the selected composite label, `generator-1 · backup generator`, with its ID
            in `UTC and IDs`. EV (readiness ruling 13): the selected W4 `asset_label` unchanged, else the gap. */}
        {row.asset_label ? (
          <span data-work-asset>{lc ? coldAssetLabel(row.asset_label) : row.asset_label}</span>
        ) : (
          <span className="muted">No asset linked</span>
        )}
        <RowDetail row={row} assetId={lc} plainDomainActions={!lc && !EV_ACTION_LINK_LIVE} domainActionHref={evCaseActionHref(cells)} />
      </td>
      <td data-work-activity-cell>
        {/* K3 pre-flight ruling 3: the selected request-state chip (`Completed` only for COMPLETED).
            MOCK DEVIATION (D2) R70 (cold) / R81 (EV): the stored activity in a same-cell `Activity recorded`
            disclosure. */}
        <StateChip kind="maintenance" state={row.request_state ?? row.state} />
        {row.activity ? (
          <Disclosure name={`work-activity-${row.case_id}`} summary="Activity recorded" variant="inline">
            <span data-work-activity>
              <CaseLongText text={row.activity} name={`work-activity-text-${row.case_id}`} legacyCold={lc} />
            </span>
          </Disclosure>
        ) : null}
      </td>
      <td data-work-outcome-cell>
        {/* MOCK DEVIATION (D2) R71 (cold) / R82 (EV): the `Unverified` badge, then the selected outcome note in its own
            disclosure. */}
        <span className="w1f4-action-badge w1f4-action-badge--amber" data-work-outcome={row.outcome_state ?? "UNVERIFIED"}>
          Unverified
        </span>
        {row.outcome_note ? (
          <Disclosure name={`work-outcome-${row.case_id}`} summary="Outcome note" variant="inline">
            <span data-work-outcome-note>
              <CaseLongText text={row.outcome_note} name={`work-outcome-text-${row.case_id}`} legacyCold={lc} />
            </span>
          </Disclosure>
        ) : null}
      </td>
      <td data-work-next-evidence>
        {/* MOCK DEVIATION (D1) R72 (cold) / R84 (EV): the selected next-evidence copy, or the honest gap; never a
            witnessed test. */}
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
  cells,
  timeZone,
}: {
  copy: KindCopy;
  body: WorkIndexBody;
  links: SiteWorkCasesLinks;
  overlay: DecisionRead<WorkContextsBody> | null;
  cells: DomainCells | null;
  timeZone: string | null;
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
              {cells !== null ? (
                copy.kind === "incidents" ? (
                  <DomainIncidentCells row={row} cells={cells} />
                ) : (
                  <DomainMaintenanceCells row={row} cells={cells} />
                )
              ) : copy.kind === "incidents" ? (
                <IncidentCells row={row} links={links} contexts={contextsOf(row.case_id)} timeZone={timeZone} />
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
  cells,
  timeZone,
}: {
  copy: KindCopy;
  body: WorkIndexBody;
  scope: WorkScope;
  trail: WorkTrail;
  links: SiteWorkCasesLinks;
  onScope: SiteWorkCasesProps["onScope"];
  siteId: string;
  decisions?: MiniDecisionsClient;
  cells: DomainCells | null;
  timeZone: string | null;
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
          <Basis body={body} timeZone={timeZone} />
        </div>
      </>
    );
  }
  return (
    <div data-work-loaded>
      {/* K3 pre-flight ruling 4: COLDCHAIN and EV hide the coverage line; the currentness notice sits above the panel. */}
      {cells === null ? <CoverageLine body={body} /> : null}
      <Rows copy={copy} body={body} links={links} overlay={overlay} cells={cells} timeZone={timeZone} />
      {/* MOCK DEVIATION (D2) R93 (cold) / R106 (EV): the W4 Pages block below the table; MOCK DEVIATION (D2) R92
          (cold) / R105 (EV): the selected `What this list is based on` disclosure at the panel foot (also after the
          complete-zero empty card). */}
      <div className="w1f4-work-foot">
        <Pages body={body} scope={scope} trail={trail} onScope={onScope} />
        <Basis body={body} timeZone={timeZone} />
      </div>
    </div>
  );
}

/**
 * W5-04 readiness ruling 18: `data-domain-cases` (the Site type) on both domain Site types, `data-cold-cases` on
 * COLDCHAIN only (the K5 cold cell rules and regression keep it); MINIGRID gets neither.
 */
function Body({ copy, cells, children }: { copy: KindCopy; cells: DomainCells | null; children: ReactNode }) {
  return (
    <div
      className="w1f4-changes-work work-cases"
      data-site-work={copy.kind}
      data-cold-cases={cells !== null && cells.legacyCold ? "" : undefined}
      data-domain-cases={cells !== null ? cells.site.siteType : undefined}
    >
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
  // W5-02 K3a (COLDCHAIN) and W5-04 V3a (EV_CHARGING): the domain case presentation; MINIGRID keeps W4's.
  const cells: DomainCells | null =
    site !== undefined && DOMAIN_CASE_SITE_TYPES.has(site.siteType)
      ? { site, knownAt: knownAt ?? null, legacyCold: site.siteType === "COLDCHAIN", from, to }
      : null;
  const legacyCold = cells !== null && cells.legacyCold;
  // post-W6 W4 R320 (Q8): the Site's stored timezone for every type (MINIGRID included); null reads as UTC.
  const timeZone = site?.timezone ?? null;
  const loadedBody = result !== null && result.status === "loaded" ? result.value : null;
  // K3a (P-K3a-7, K3 pre-flight ruling 5): the domain notice comes from the W4 envelope `status`, never `coverage`.
  const currentness =
    cells !== null && loadedBody !== null ? coldCurrentnessNotice(loadedBody.status as DomainStatus, loadedBody.known_at) : null;
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
    <Body copy={copy} cells={cells}>
      {/* Cold K3 pre-flight ruling 6 / EV pre-flight 35: the mock strip sentence and `Manage in {kind} →` to the
          mounted W6 root; MOCK DEVIATION (D4) R111 (EV): the stored Site display name's short form. */}
      <WorkStrip copy={copy} result={result} scope={scope} cold={cells !== null} timeZone={timeZone} />
      {/* MOCK DEVIATION (D2) R91 (cold, K3 pre-flight ruling 5) / R80 + R104 (EV): the selected-state notice between
          strip and panel, blue for Historical/Unknown and amber for Pending recompute/Stale source; absent on CURRENT. */}
      {loadedBody !== null && currentness !== null ? (
        <Notice tone={coldCurrentnessTone(loadedBody.status as DomainStatus)} data={caseAttrs(legacyCold, "currentness", loadedBody.status)}>
          <RailIcon name="info" />
          <p>{currentness}</p>
        </Notice>
      ) : null}
      <Panel
        heading={copy.title}
        headingId={`site-work-${kind}-heading`}
        description={copy.subcopy}
        actions={windowForm ? <WindowForm copy={copy} scope={scope} timeZone={timeZone} onScope={onScope} /> : undefined}
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
            cells={cells}
            timeZone={timeZone}
          />
        ) : (
          <Refused copy={copy} result={result} scope={scope} onScope={onScope} />
        )}
      </Panel>
      {cells !== null ? (
        // MOCK DEVIATION (D1) R01 (cold) / R03 (EV): the mock notice's create-flow sentence is omitted (no create
        // flow exists).
        <Notice tone="blue" data={{ "data-work-notice": "", ...caseAttrs(legacyCold, "notice", "") }}>
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

