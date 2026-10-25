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
 * W1-F3 (`D-2026-10-17-mockup-layout-spec`): every state renders inside the
 * one v69 panel "Findings at this site": window controls, then the v69 question
 * "Which Findings belong to this site?" with the answer as a big claim, a shared
 * state line with its scope and plain "As of" bound beside the answer, the
 * Findings as rows (or a day strip when no rows can be listed), and a closed
 * exact-reference disclosure last holding the list, page and matching
 * references and the raw recorded state and reasons.
 *
 * No amount is shown: exact-revision money provenance is not in this read.
 * A Site with no imported record keeps the older summary (`fallback`).
 */
import { createContext, useContext, useEffect, useState, type FormEvent, type ReactNode } from "react";
import { Link } from "react-router-dom";

import {
  DataTable,
  Disclosure,
  ExactReferences,
  Fact,
  FactList,
  Notice,
  Panel,
  StatusBar,
  plainTime,
  ProductStatus,
  ShowAll,
  StepStrip,
  currentnessWords,
  readResultWords,
  type ExactReference,
  type ProductWords,
  type Step,
} from "../ui";
import type {
  FindingIndexBody,
  FindingIndexClient,
  FindingIndexDayWatermark,
  FindingIndexResult,
  FindingIndexRow,
  FindingIndexScope,
} from "./findingIndexClient";
import { LIFECYCLE_WORDS, transitionWords } from "./findingWords";
import type { Lifecycle } from "./findingClient";
import "./w1ux02-findings-index.css";
import { UnavailableChip } from "../ui/UnavailableEntry";

/**
 * W1-F5b (D-2026-10-17-f5-subtabs-and-contact): the mock's lens chips and the real window control, at the top
 * of the single Findings panel in every state. Supplied once by the index and read by `View`.
 */
const PanelControls = createContext<ReactNode>(null);
/** post-W6 W1-a Q18 / R196: the lens row (and its helper) sits above the scope strip, as in the mock. */
const LensRow = createContext<ReactNode>(null);
/** post-W6 W1-a Q18: the estate Findings list the scope strip hands off to. */
const ManageHref = createContext<string | null>(null);

/**
 * The mock's `All | Cost | Risks | Opportunities` lens row. `All` is the selected live view; the other lenses
 * have no authoritative classification or Site/window filter yet, so they are "Not available yet" text and
 * cannot change or discard the window selection.
 */
/**
 * W4-03 closure 4 S11: the mini Site's helper in the panel controls. post-W6 W1-b Q20 / R197: "open the renewable
 * evaluation" links to the Site's mounted Performance Renewable view; the index has no Opportunity ID, so no
 * Opportunity address is made up.
 */
export const OPPORTUNITY_INDEX_HELPER =
  "Opportunity index unavailable; open the renewable evaluation for this site's five-day study.";
const OPPORTUNITY_HELPER_LINK = "open the renewable evaluation";

/** A Site-scoped lens address; none exists yet, so every current call leaves these out (Q18 / Q49, D5). */
export type SiteLensHrefs = Partial<Record<"Cost" | "Risks" | "Opportunities", string>>;

function OpportunityHelper({ shown, renewable }: { shown: boolean; renewable?: string }) {
  if (!shown) return null;
  if (renewable === undefined) {
    return (
      <p className="finding-sections__helper" data-opportunity-index-helper>
        {OPPORTUNITY_INDEX_HELPER}
      </p>
    );
  }
  const at = OPPORTUNITY_INDEX_HELPER.indexOf(OPPORTUNITY_HELPER_LINK);
  return (
    <p className="finding-sections__helper" data-opportunity-index-helper>
      {OPPORTUNITY_INDEX_HELPER.slice(0, at)}
      <Link to={renewable} data-opportunity-index-renewable>
        {OPPORTUNITY_HELPER_LINK}
      </Link>
      {OPPORTUNITY_INDEX_HELPER.slice(at + OPPORTUNITY_HELPER_LINK.length)}
    </p>
  );
}

/** A future Site-scoped lens; the unbuilt entries stay literal (navigation-truthfulness inventory). */
function LiveLens({ label, href }: { label: string; href: string }) {
  return (
    <li className="v69-chip" data-lens={label.toLowerCase()}>
      <Link to={href}>{label}</Link>
    </li>
  );
}

/** MOCK DEVIATION D5 (R394): Cost, Risks and Opportunities stay disabled until Site-scoped lenses exist (Q18/Q49). */
function LensChips({ hrefs = {} }: { hrefs?: SiteLensHrefs }) {
  return (
    <ul className="v69-chips v69-chips--lenses" aria-label="Finding lenses" data-site-findings-lenses>
      <li className="v69-chip" aria-current="true" data-lens="all">
        All
      </li>
      {hrefs.Cost === undefined ? <UnavailableChip label="Cost" /> : <LiveLens label="Cost" href={hrefs.Cost} />}
      {hrefs.Risks === undefined ? <UnavailableChip label="Risks" /> : <LiveLens label="Risks" href={hrefs.Risks} />}
      {hrefs.Opportunities === undefined ? (
        <UnavailableChip label="Opportunities" />
      ) : (
        <LiveLens label="Opportunities" href={hrefs.Opportunities} />
      )}
    </ul>
  );
}

export interface FindingIndexLinks {
  /** The same page at another scope (a new window, page one, or the next page). */
  scope: (scope: FindingIndexScope) => string;
  /** One Finding, optionally at an exact revision. */
  finding: (findingId: string, revisionId?: string | null) => string;
  /** post-W6 W1-a Q18 / R196: the estate Findings list (`Manage in Findings →` on the scope strip). */
  manage?: string;
  /** post-W6 W1-b Q19 / R197: the Site's Performance Dispatch at one UTC day, optionally one interval revision. */
  dispatch?: (day: string, intervalRevisionId: string | null) => string;
  /** post-W6 W1-b Q20 / R197: the Site's mounted Performance Renewable view (the opportunity helper's link). */
  renewable?: string;
}

/**
 * post-W6 W1-b Q19 (pre-flight ruling 2): the Domain cell's Dispatch day is the UTC date of the episode start; the
 * revision is added only when the row's assessment revision is proved to be a 15-minute interval revision by the
 * row's own interval list. A whole-window primary, a missing list or an invalid start never selects a revision, and
 * an invalid start gives no day at all.
 */
export function dispatchTarget(row: FindingIndexRow): { day: string; revisionId: string | null } | null {
  const start = row.episode.start;
  if (typeof start !== "string" || !/^\d{4}-\d{2}-\d{2}T/.test(start) || Number.isNaN(Date.parse(start))) return null;
  const day = new Date(start).toISOString().slice(0, 10);
  const id = row.assessment?.assessment_revision_id;
  const intervals = row.assessment?.interval_assessment_revision_ids;
  const revisionId = typeof id === "string" && id !== "" && Array.isArray(intervals) && intervals.includes(id) ? id : null;
  return { day, revisionId };
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
  /** W4-03 S11: a MINIGRID Site states where its typed five-day opportunity is reached. */
  opportunityHelper?: boolean;
}

const HEADING_ID = "site-finding-index-heading";
/** post-W6 W1-b Q19 / R197: the mock's `Findings at this site` panel description. */
const PANEL_DESCRIPTION = "Domain links back to the Performance view that produced the finding.";
const NOT_A_ZERO =
  "No Findings are listed and no count is given. This is not a statement that the window has no Findings.";

const NOT_CURRENT_CODES = ["PENDING", "UNASSESSED", "STALE_PROJECTION", "FAILED"] as const;

/**
 * The index's non-current states, wrapped onto the shared currentness words
 * (W1-UX-02 wrap-then-replace). Local to this view.
 */
const STATUS_WORDS: Record<string, { label: string; sentence: string }> = Object.fromEntries(
  NOT_CURRENT_CODES.map((code) => {
    const words = currentnessWords(code);
    return [code, { label: words.label, sentence: words.sentence }];
  }),
);

/** A `CURRENT` read that still carries no count: never read as current or empty. */
const NO_COUNT_WORDS: ProductWords = {
  label: "No count was given",
  sentence: "The list came back without a count, so nothing is concluded about this window's Findings.",
  next: "Look again shortly.",
  tone: "limited",
  code: null,
  unrecognised: false,
};

type RefusalKind = "closed" | "continuity_limit" | "basis_changed" | "invalid" | "unauthenticated";

/** Refusal states this domain owns (not in the shared map). */
const REFUSAL_WORDS: Record<RefusalKind, Omit<ProductWords, "code" | "unrecognised">> = {
  closed: {
    label: "Not released for this Site",
    sentence: "This Site's assessments are not released, so no Findings list can be shown. It is not empty.",
    tone: "limited",
  },
  continuity_limit: {
    label: "The list cannot be completed",
    sentence:
      "At least one Finding reaches further back than can be followed, so this window's list cannot be completed. It is not empty.",
    next: "Choose a narrower window.",
    tone: "limited",
  },
  basis_changed: {
    label: "The list changed while you were reading it",
    sentence: "The Findings for this window changed since this page was opened, so this page cannot continue.",
    next: "Start again from the first page.",
    tone: "waiting",
  },
  invalid: {
    label: "This window is not valid",
    sentence: "Windows are whole UTC days, at most 31 days long. Nothing is concluded about this request.",
    next: "Choose a window of whole days.",
    tone: "neutral",
  },
  unauthenticated: {
    label: "Sign in needed",
    sentence: "Sign in to read this Site's Findings. Nothing is shown until you do, and nothing is concluded.",
    tone: "neutral",
  },
};

function refusalWords(kind: RefusalKind): ProductWords {
  return { ...REFUSAL_WORDS[kind], code: kind, unrecognised: false };
}

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

/** "25 Oct 2026" for a `YYYY-MM-DD` UTC day; the day itself when unreadable. */
function plainDay(day: string): string {
  const text = plainTime(`${day}T00:00:00Z`);
  return text === null ? day : text.replace(/, \d{2}:\d{2} UTC$/, "");
}

function plainInstant(instant: string | null | undefined): string {
  return plainTime(instant) ?? "time not recorded";
}

/** W1-F3 height phase: a period inside one UTC day names the day once ("15 Oct 2026, 12:00 UTC to 13:30 UTC"). */
function periodText(start: string, end: string): string {
  const a = plainInstant(start);
  const b = plainInstant(end);
  const day = /^(.*), (\d{2}:\d{2} UTC)$/;
  const ma = day.exec(a);
  const mb = day.exec(b);
  return ma && mb && ma[1] === mb[1] ? `${a} to ${mb[2]}` : `${a} to ${b}`;
}

function validWindow(scope: FindingIndexScope): boolean {
  return !Number.isNaN(new Date(scope.from).getTime()) && !Number.isNaN(new Date(scope.to).getTime());
}

/** The plain scope of the state line: the domain and the window's UTC days. */
function windowScope(scope: FindingIndexScope): string {
  if (!validWindow(scope)) return "Mini-grid dispatch Findings · the requested window";
  const first = dayOf(scope.from);
  const last = lastDayOf(scope.to);
  const days = first === last ? plainDay(first) : `${plainDay(first)} to ${plainDay(last)}`;
  return `Mini-grid dispatch Findings at this site · ${days} (UTC)`;
}

function WindowForm({ scope, onScope }: { scope: FindingIndexScope; onScope: (scope: FindingIndexScope) => void }) {
  const valid = validWindow(scope);
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
    <form
      className="v69-chips site-findings-window"
      onSubmit={submit}
      data-finding-index-window
      aria-label="Findings window"
    >
      <label className="v69-chip-field">
        {"From (UTC day)"}
        <input type="date" value={first} onChange={(event) => setFirst(event.target.value)} />
      </label>
      <label className="v69-chip-field">
        {"To (UTC day, included)"}
        <input type="date" value={last} onChange={(event) => setLast(event.target.value)} />
      </label>
      <button className="button" type="submit">
        Show Findings
      </button>
    </form>
  );
}

/**
 * The older basis disclosure. This view no longer renders it (W1-UX-02 moved
 * its values to the exact-reference disclosure and the day strip); it stays
 * exported for `OverviewFindingList` until that view migrates.
 */
export function Basis({ body }: { body: FindingIndexBody }) {
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

/** One day of the window as a step: checked and matched, waiting, failed or not known. */
function dayStep(day: FindingIndexDayWatermark): Step {
  const label = plainDay(day.day);
  if (day.status === "CURRENT") {
    return day.s4.matched
      ? { label, state: "done", detail: "Checked, and Findings matched" }
      : { label, state: "waiting", detail: "Checked; Findings not matched yet" };
  }
  const words = currentnessWords(day.status);
  if (words.unrecognised) return { label, state: "not-known", detail: words.label };
  if (day.status === "FAILED") return { label, state: "problem", detail: words.label };
  if (words.tone === "waiting" || words.tone === "limited") return { label, state: "waiting", detail: words.label };
  return { label, state: "not-known", detail: words.label };
}

function DayStrip({ body, rows = false }: { body: FindingIndexBody; rows?: boolean }) {
  if (body.watermarks.days.length === 0) return null;
  // W1-F3 review M4: beside rows, a one-day window is already named by every row's Period cell.
  if (rows && body.watermarks.days.length === 1) return null;
  // W1-F3 height phase: the days read as one compact line of marks; a day that is not done keeps its detail.
  return (
    <div className="v69-step-line">
      <StepStrip title="Days in this window" steps={body.watermarks.days.map(dayStep)} />
    </div>
  );
}

/** The labelled exact values behind a loaded list: references, raw state and reasons. */
function bodyReferences(body: FindingIndexBody, scope: FindingIndexScope): ExactReference[] {
  const matcher = body.watermarks.matcher;
  const through = matcher?.matched_through_selection_seq;
  const references: ExactReference[] = [
    { label: "Recorded list state", value: body.status },
    { label: "List as of (exact time)", value: body.knowledge_at },
    { label: "List prepared at (exact time)", value: body.built_at },
    { label: "List reference", value: body.selection_token },
    { label: "Matching pass reference", value: matcher?.match_pass_id ? String(matcher.match_pass_id) : null },
    { label: "Matched through check number", value: through === null || through === undefined ? null : String(through) },
  ];
  if (scope.cursor) references.push({ label: "This page reference", value: scope.cursor });
  if (body.next_cursor) references.push({ label: "Next page reference", value: body.next_cursor });
  for (const day of body.watermarks.days) {
    references.push({ label: `Assessment record, ${plainDay(day.day)}`, value: day.s3.run_id });
  }
  body.status_reasons.forEach((reason, index) => {
    references.push({ label: `Reason recorded ${index + 1}`, value: reason });
  });
  return references;
}

const RELATION_TEXT = {
  merged_from: "Merged from another Finding",
  recurs_after: "Recurs after an earlier Finding",
  recurred_by: "Recurred as a later Finding",
  split_from: "Split from another Finding",
  split_parts: "Split into another Finding",
} as const;

function Relations({ row, links }: { row: FindingIndexRow; links: FindingIndexLinks }) {
  const items: { text: string; id: string }[] = [
    ...row.relations.merged_from.map((id) => ({ text: RELATION_TEXT.merged_from, id })),
    ...(row.relations.recurs_after ? [{ text: RELATION_TEXT.recurs_after, id: row.relations.recurs_after }] : []),
    ...row.relations.recurred_by.map((id) => ({ text: RELATION_TEXT.recurred_by, id })),
    ...(row.relations.split_from ? [{ text: RELATION_TEXT.split_from, id: row.relations.split_from }] : []),
    ...row.relations.split_parts.map((id) => ({ text: RELATION_TEXT.split_parts, id })),
  ];
  if (items.length === 0) return null;
  const seen: Record<string, number> = {};
  return (
    <ul className="finding-index-relations">
      {items.map((item) => {
        seen[item.text] = (seen[item.text] ?? 0) + 1;
        const text = seen[item.text] > 1 ? `${item.text} (${seen[item.text]})` : item.text;
        return (
          <li key={`${item.text}-${item.id}`}>
            <Link to={links.finding(item.id)} data-finding-index-related={item.id}>
              {text}
            </Link>
          </li>
        );
      })}
    </ul>
  );
}

/** W1-F3 height phase: the mock shows three rows; the rest of the page stays behind "Show all N". */
const ROWS_SHOWN = 3;

function Rows({ body, links }: { body: FindingIndexBody; links: FindingIndexLinks }) {
  const first = body.rows.slice(0, ROWS_SHOWN);
  const rest = body.rows.slice(ROWS_SHOWN);
  return (
    <>
      <RowTable rows={first} links={links} />
      {rest.length === 0 ? null : (
        <ShowAll name="finding-index-rows" summary={`Show all ${body.rows.length} Findings on this page`}>
          <RowTable rows={rest} links={links} />
        </ShowAll>
      )}
    </>
  );
}

function DomainCell({ row, links }: { row: FindingIndexRow; links: FindingIndexLinks }) {
  const target = links.dispatch === undefined ? null : dispatchTarget(row);
  if (target === null || links.dispatch === undefined) return <>Dispatch</>;
  return (
    <Link
      to={links.dispatch(target.day, target.revisionId)}
      data-finding-index-dispatch={target.day}
      data-finding-index-dispatch-revision={target.revisionId ?? undefined}
    >
      Dispatch
    </Link>
  );
}

function RowTable({ rows, links }: { rows: FindingIndexBody["rows"]; links: FindingIndexLinks }) {
  return (
    <DataTable labelledBy={HEADING_ID}>
      <thead>
        <tr>
          <th scope="col">Finding</th>
          <th scope="col">Domain</th>
          <th scope="col">Priority</th>
          <th scope="col">Confidence</th>
          <th scope="col">State</th>
          <th scope="col">Main consequence</th>
          <th scope="col">Lens</th>
          <th scope="col">Period</th>
        </tr>
      </thead>
      <tbody>
        {rows.map((row) => {
          const lifecycle = LIFECYCLE_WORDS[row.lifecycle as Lifecycle];
          return (
            <tr
              key={row.finding_id}
              className="finding-index-row"
              data-finding-index-row={row.finding_id}
              data-finding-revision={row.finding_revision_id}
            >
              <td>
                <Link to={links.finding(row.finding_id, row.finding_revision_id)} data-finding-index-link>
                  {lifecycle?.title ?? "Generator support review"}
                </Link>{" "}
                <small className="finding-index-version">· Version {row.revision_no}</small>
                {/* W1-F3 review H2/M9: related Findings sit under the title instead of a wrapping column. */}
                <Relations row={row} links={links} />
              </td>
              <td data-finding-index-domain>
                <DomainCell row={row} links={links} />
              </td>
              <td>
                <span className="badge badge--not-assessed" data-finding-index-priority data-not-assessed>
                  Not assessed
                </span>
              </td>
              <td>
                <span className="badge badge--not-assessed" data-finding-index-confidence data-not-assessed>
                  Not assessed
                </span>
              </td>
              <td className="finding-index-state-cell">
                <span
                  className="finding-index-state"
                  data-finding-index-lifecycle={lifecycle ? "known" : "unrecognised"}
                >
                  {lifecycle?.label ?? "State not recognised"}
                </span>
                {row.transition ? <small> {transitionWords(row.transition)}</small> : null}
              </td>
              <td data-finding-index-amount={row.amount.state}>
                Not in this list
              </td>
              <td>
                <span className="badge badge--not-assessed" data-finding-index-lens data-not-assessed>
                  Not assessed
                </span>
              </td>
              <td className="finding-index-period">{periodText(row.episode.start, row.episode.end)}</td>
            </tr>
          );
        })}
      </tbody>
    </DataTable>
  );
}

/**
 * One state of the screen in the v69 form (W1-F3, mock `siteFindingsScreen`):
 * a one-line statusbar (the claim and the shared state line), then the single
 * panel "Findings at this site" holding the table, pages and day strip, or
 * the in-panel gap where no rows can be listed, with the closed exact
 * references last; then the mock's blue notice when there is one.
 */
function View({
  state,
  claim,
  status,
  body,
  action,
  notice,
  references,
  attributes = {},
}: {
  state: string;
  claim: string;
  status: ReactNode;
  body: ReactNode;
  action?: ReactNode;
  notice?: ReactNode;
  references?: ReactNode;
  attributes?: Record<string, string>;
}) {
  const controls = useContext(PanelControls);
  const lenses = useContext(LensRow);
  const manage = useContext(ManageHref);
  return (
    <div className="site-findings-view" data-finding-index-state={state} {...attributes}>
      {lenses}
      <StatusBar items label="Findings state" data={{ "data-site-findings-status": "" }}>
        <strong data-site-findings-claim>{claim}</strong>
        {status}
        {manage === null ? null : (
          <>
            <span className="status-strip__spacer" />
            <Link to={manage} data-site-findings-manage>
              Manage in Findings →
            </Link>
          </>
        )}
      </StatusBar>
      <Panel heading="Findings at this site" headingId={HEADING_ID} description={PANEL_DESCRIPTION} actions={action}>
        {controls}
        {body}
        {references ?? null}
      </Panel>
      {notice === undefined ? null : (
        <Notice tone="blue" data={{ "data-site-findings-notice": "" }}>
          {notice}
        </Notice>
      )}
    </div>
  );
}

/** The in-panel gap where no rows can be listed: short muted lines, as the mock's muted table row. */
function Gap({ children }: { children: ReactNode }) {
  return (
    <div className="site-findings-gap" data-site-findings-gap>
      {children}
    </div>
  );
}

function Loaded({ body, scope, links }: { body: FindingIndexBody; scope: FindingIndexScope; links: FindingIndexLinks }) {
  const firstPage = links.scope({ ...scope, cursor: null });
  const scopeText = windowScope(scope);
  const references = <ExactReferences name="finding-index-references" references={bodyReferences(body, scope)} />;
  if (body.status !== "CURRENT" || body.total_count === null) {
    const words = body.status === "CURRENT" ? NO_COUNT_WORDS : currentnessWords(body.status);
    return (
      <View
        state={body.status}
        claim="The Findings for this window are not known"
        status={<ProductStatus inline words={words} scope={scopeText} asOf={body.knowledge_at} />}
        body={
          <>
            <Gap>
              <p>{NOT_A_ZERO}</p>
              {words.next === undefined ? <p>Look again after every day in this window has been checked.</p> : null}
            </Gap>
            <DayStrip body={body} />
          </>
        }
        references={references}
      />
    );
  }
  if (body.total_count === 0) {
    return (
      <View
        state="current-empty"
        claim="No Findings in this window"
        status={<ProductStatus inline words={readResultWords("proved-empty")} scope={scopeText} asOf={body.knowledge_at} />}
        body={
          <>
            <Gap>
              <p>
                Every day in this window was assessed and matched for Findings through its latest check, and no
                Finding overlaps the window. This holds for the time shown; later readings can change it. Choose
                another window to look at other days.
              </p>
            </Gap>
            <DayStrip body={body} />
          </>
        }
        references={references}
      />
    );
  }
  const shown = body.rows.length;
  const newest = body.rows[0];
  return (
    <View
      state="current-rows"
      claim={`${body.total_count} ${body.total_count === 1 ? "Finding" : "Findings"} in this window`}
      status={<ProductStatus inline words={currentnessWords("CURRENT")} scope={scopeText} asOf={body.knowledge_at} />}
      body={
        <>
          <Rows body={body} links={links} />
          <nav aria-label="Findings pages" data-finding-index-pages>
            {/* W1-F3 review M4: the count is said only when this page does not hold every Finding. */}
            {shown < body.total_count ? (
              <span>
                Showing {shown} of {body.total_count}.
              </span>
            ) : null}{" "}
            {scope.cursor ? <Link to={firstPage}>First page</Link> : null}{" "}
            {body.next_cursor ? (
              <Link to={links.scope({ ...scope, cursor: body.next_cursor })} data-finding-index-next>
                Next page
              </Link>
            ) : null}
          </nav>
          <DayStrip body={body} rows />
        </>
      }
      notice={
        <p>
          Each row is a bounded conclusion about part of this window, newest period first. Each Finding opens at the
          exact version listed here, which stays the same after reload even when a newer version is recorded. No
          amount is shown in this list.
        </p>
      }
      action={
        newest === undefined ? undefined : (
          <Link to={links.finding(newest.finding_id, newest.finding_revision_id)} data-finding-index-destination>
            Open the newest Finding
          </Link>
        )
      }
      references={references}
    />
  );
}

function RefusedCard({
  state,
  headline,
  words,
  scope,
  meaning,
  todo,
  references = [],
  attributes = {},
}: {
  state: string;
  headline: string;
  words: ProductWords;
  scope: string;
  meaning: ReactNode;
  todo?: ReactNode;
  references?: ExactReference[];
  attributes?: Record<string, string>;
}) {
  return (
    <View
      state={state}
      attributes={attributes}
      claim={headline}
      status={<ProductStatus inline words={words} scope={scope} asOf={null} />}
      body={
        <Gap>
          {meaning}
          {todo ?? null}
        </Gap>
      }
      references={
        references.length === 0 ? undefined : (
          <ExactReferences name="finding-index-references" references={references} />
        )
      }
    />
  );
}

function Refused({ result, scope, links }: { result: FindingIndexResult; scope: FindingIndexScope; links: FindingIndexLinks }) {
  const firstPage = links.scope({ ...scope, cursor: null });
  const scopeText = windowScope(scope);
  switch (result.status) {
    case "closed":
      return (
        <RefusedCard
          state="closed"
          headline="Findings list closed for this Site"
          words={refusalWords("closed")}
          scope={scopeText}
          meaning={
            <>
              <p>{result.message ?? "This Site's assessments are not released."}</p>
              <p>
                No Findings are listed and no count is given. A link to an exact Finding version still opens it as
                audit material.
              </p>
            </>
          }
        />
      );
    case "continuity_limit":
      return (
        <RefusedCard
          state="continuity-limit"
          headline="Not known for this window"
          words={refusalWords("continuity_limit")}
          scope={scopeText}
          meaning={
            <>
              {result.message ? <p>{result.message}</p> : null}
              <p>
                No Findings are listed and no count is given.
                {result.inspectedFrom && result.inspectedTo
                  ? ` Days reached: ${plainDay(result.inspectedFrom)} to ${plainDay(result.inspectedTo)}.`
                  : ""}
              </p>
            </>
          }
          todo={<p>Choose a narrower window.</p>}
        />
      );
    case "basis_changed":
      return (
        <RefusedCard
          state="basis-changed"
          headline="This list changed"
          words={refusalWords("basis_changed")}
          scope={scopeText}
          attributes={{ "data-finding-index-reason": result.reason ?? "" }}
          meaning={<p>No Findings are listed from the old page, and no count is given.</p>}
          todo={
            <p>
              <Link to={firstPage} data-finding-index-restart>
                Start again from the first page
              </Link>
            </p>
          }
          references={[
            { label: "Recorded reason", value: result.reason ?? null },
            ...(scope.cursor ? [{ label: "Old page reference", value: scope.cursor }] : []),
          ]}
        />
      );
    case "invalid":
      return (
        <RefusedCard
          state="invalid"
          headline="This window cannot be shown"
          words={refusalWords("invalid")}
          scope={scopeText}
          attributes={{ "data-finding-index-code": result.code ?? "" }}
          meaning={
            <>
              <p>{result.message ?? "The requested window is not valid."}</p>
              <p>No Findings are listed and no count is given.</p>
            </>
          }
          todo={<p>Choose whole UTC days, at most 31 days long, above.</p>}
          references={[
            { label: "Recorded reason", value: result.code ?? null },
            { label: "Field named", value: result.field ?? null },
          ]}
        />
      );
    case "unauthenticated":
      return (
        <RefusedCard
          state="unauthenticated"
          headline="Sign in to see Findings"
          words={refusalWords("unauthenticated")}
          scope={scopeText}
          meaning={<p>{result.message ?? "Sign in to read Findings."}</p>}
        />
      );
    case "forbidden":
      return (
        <RefusedCard
          state="forbidden"
          headline="No access to this Site's Findings"
          words={readResultWords("refused")}
          scope={scopeText}
          meaning={<p>{result.message ?? "You do not have access to this Site."}</p>}
        />
      );
    default:
      return (
        <RefusedCard
          state="unavailable"
          headline="Findings unavailable"
          words={readResultWords("unavailable")}
          scope={scopeText}
          meaning={
            <>
              <p>
                {result.status === "unavailable" && result.message ? result.message : "The Findings could not be read."}
              </p>
              <p>No Findings are listed and no count is given.</p>
            </>
          }
        />
      );
  }
}

export function SiteFindingIndex({ siteId, client, scope, links, onScope, fallback, opportunityHelper = false }: SiteFindingIndexProps) {
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
    <div className="finding-index" data-findings-index="site-window">
      <ManageHref.Provider value={links.manage ?? null}>
      <LensRow.Provider value={<LensChips />}>
      <PanelControls.Provider
        value={
          <div className="site-findings-controls" data-site-findings-controls>
            {/* The opportunity helper stays in the panel, the noninteractive line it was before the lenses moved. */}
            <OpportunityHelper shown={opportunityHelper} renewable={links.renewable} />
            <WindowForm scope={scope} onScope={onScope} />
          </div>
        }
      >
        {result.status === "loaded" ? (
          <Loaded body={result.value} scope={scope} links={links} />
        ) : (
          <Refused result={result} scope={scope} links={links} />
        )}
      </PanelControls.Provider>
      </LensRow.Provider>
      </ManageHref.Provider>
    </div>
  );
}
