/**
 * W5-02c K4a (`.agent/W5-02c-K4-preflight-rulings.md` rulings 4, 5, 8; build spec "Action panels"): the two loaded
 * panels of the v69 `cold-action` screen (`frontend/mockups/v69/index.html:742-746`), `Declared outcome criteria` and
 * `Related activity`, from one validated domain Action detail read. No fetches; `domainActionClient.ts` owns the read
 * and the shell in `SiteAnalyticsFrames.tsx` owns the breadcrumb, header, strip, currentness and concluding notices.
 *
 * W5-04 V4a (readiness rulings 15, 41): the panels take an explicit per-domain presentation. Cold keeps its K4 literals
 * and both panels byte-for-byte (`COLD_ACTION_PRESENTATION`); EV (`EV_ACTION_PRESENTATION`, v69 `ev-action`,
 * `index.html:710-713`) renders only the `Declared verification plan` panel, with three plain `Pending` results and no
 * Related activity panel, Inspect control or disabled maintenance button (pre-flight 46).
 *
 * Nothing here asserts an observed automatic start or cooling restoration: the result cells are the stored initial
 * results (`Not tested`, `Not tested`, `Not established`, `Pending`) and the completed-inspection sentence states
 * activity only.
 */
import { useNavigate } from "react-router-dom";

import { DataTable, Panel } from "../ui";
import type { DomainActionDetail, DomainStatus } from "./domainActionClient";
import { coldRequestHref } from "./siteWorkCases";

export const COLD_RELATED_TITLE = "Related activity";
/** MOCK DEVIATION (D2) R100: the honest selected state when no completed inspection is linked at the cutoff. */
export const COLD_RELATED_NOT_LINKED = "No completed inspection is linked to this Action.";
/**
 * post-W6 W5-cold R344 (B15-10, K4): exact linked-request states. A linked VERIFICATION_WINDOW request with its performed
 * record, and a linked CANCELLED request, are stated as such; neither establishes a verified outcome.
 */
export const COLD_RELATED_VERIFICATION_WINDOW = "Work was recorded; verification is open and no outcome is established.";
export const COLD_RELATED_CANCELLED = "The linked request was cancelled; no completed work or verified outcome is established.";
export const COLD_INSPECT = "Inspect maintenance evidence";
export const COLD_INSPECT_UNAVAILABLE = "Maintenance detail is unavailable for this record.";
export const COLD_SOURCE_FINDING = "Open source Finding →";
export const COLD_SOURCE_FINDING_UNAVAILABLE = "The selected Finding revision cannot be opened here yet.";

/** W5-04 V4a ruling 41: the loaded panel presentation for one Action domain. */
export interface DomainActionPanelPresentation {
  criteriaTitle: string;
  columns: readonly string[];
  /** The sentence inside the criteria panel when no intent is selected; the table is omitted. */
  intentMissing: string;
  /** Stored result value to its plain label. */
  resultLabels: Record<string, string>;
  /** Whether the cold `Related activity` panel follows (EV has none). */
  related: boolean;
}

/**
 * W5-04 V4a ruling 41: the per-domain Action detail presentation for the shell in `SiteAnalyticsFrames.tsx` (header
 * subtitle, badge, status line, disclosure, currentness, state panel and closing notice) and for these panels.
 * Instances: `COLD_ACTION_PRESENTATION` in `coldWorkPresentation.ts`, `EV_ACTION_PRESENTATION` in
 * `evWorkPresentation.ts`.
 */
export interface DomainActionPresentation {
  subtitle: string;
  stateOpen: string;
  ownerMissing: string;
  /** The status line text after `{owner} · `, from the selected Site's full and derived short name and Finding label. */
  statusTail: (names: { siteName: string; siteShort: string; finding: string }) => string;
  /** Whether the strip carries the selected intent's `Finding version` disclosure. */
  revisionDisclosure: boolean;
  notice: (status: DomainStatus, knownAt: string) => string | null;
  tone: (status: DomainStatus) => "blue" | "amber";
  loading: string;
  notFound: string;
  unavailable: string;
  retry: string;
  closingNotice: string;
  /** Whether the detail's own links keep the selected `from,to` beside `known_at` (EV ruling 14); cold keeps `known_at` only. */
  windowQuery: boolean;
  /**
   * post-W6 W5-cold B15-04 (W4 Q10, W5 rulings 2): the refusal sentence and whether Retry is offered, by exact code.
   * Absent (EV), the shell prints the refusal message with Retry, unchanged.
   */
  refusal?: (refusal: { http: number | null; code: string | null; message: string }) => { message: string; retry: boolean };
  panel: DomainActionPanelPresentation;
}

/** Ruling 5: the completed-inspection sentence, from the selected request title and code only. */
export function coldRelatedCompleted(title: string, code: string): string {
  return `${title} ${code} is complete. A witnessed outcome test remains required.`;
}

/**
 * Ruling 19, MOCK DEVIATION (D2) R102: a selected linked request that is still OPEN or IN_PROGRESS is named with its
 * actual state; the mock's completed wording would claim a completion the record does not hold.
 */
export function coldRelatedOngoing(title: string, code: string, state: "OPEN" | "IN_PROGRESS"): string {
  return `${title} ${code} is ${state === "OPEN" ? "open" : "in progress"}. A witnessed outcome test remains required.`;
}

const CRITERIA_HEADING_ID = "domain-action-criteria-heading";
const RELATED_HEADING_ID = "domain-action-related-heading";
const INSPECT_NOTE_ID = "domain-action-inspect-unavailable";

/**
 * Rulings 5 and 19: the Related activity sentence for the selected request. COMPLETED with its performed record is a
 * completed inspection; a linked OPEN or IN_PROGRESS request is named with its state; post-W6 R344 adds linked
 * VERIFICATION_WINDOW with its record and linked CANCELLED; anything else (no case, COMPLETED or VERIFICATION_WINDOW
 * without its performed record) is the no-completed-inspection sentence.
 */
function relatedSentence(work: DomainActionDetail["links"]["work"]): { kind: string; text: string } {
  if (work.case_id !== null && work.case_title !== null && work.case_code !== null) {
    if (work.request_state === "COMPLETED" && work.record_id !== null) {
      return { kind: "completed", text: coldRelatedCompleted(work.case_title, work.case_code) };
    }
    if (work.request_state === "OPEN" || work.request_state === "IN_PROGRESS") {
      return { kind: work.request_state === "OPEN" ? "open" : "in-progress", text: coldRelatedOngoing(work.case_title, work.case_code, work.request_state) };
    }
    if (work.request_state === "VERIFICATION_WINDOW" && work.record_id !== null) {
      return { kind: "verification-window", text: COLD_RELATED_VERIFICATION_WINDOW };
    }
    if (work.request_state === "CANCELLED") {
      return { kind: "cancelled", text: COLD_RELATED_CANCELLED };
    }
  }
  return { kind: "not-linked", text: COLD_RELATED_NOT_LINKED };
}

export function DomainActionVerification({
  detail,
  siteCode,
  knownAt,
  presentation,
}: {
  detail: DomainActionDetail;
  /** Ruling 41: the selected Action domain's panel words and panel set. */
  presentation: DomainActionPanelPresentation;
  /** The stored Site code, for the selected W6 request Overview address. */
  siteCode: string;
  /** The explicit URL cutoff only (P-G-4); null omits `known_at` from the Overview address. */
  knownAt: string | null;
}) {
  const navigate = useNavigate();
  const work = detail.links.work;
  const related = relatedSentence(work);
  // Ruling 8, MOCK DEVIATION (D1) R68: Inspect opens the selected W6 request Overview (the mock's `workverification`
  // target is unavailable) whenever a case ID is selected.
  const inspectHref = work.case_id === null ? null : coldRequestHref(work.case_id, siteCode, knownAt);
  const intent = detail.intent;
  return (
    <>
      <Panel heading={presentation.criteriaTitle} headingId={CRITERIA_HEADING_ID}>
        {intent === null ? (
          <p data-domain-action-intent-missing>{presentation.intentMissing}</p>
        ) : (
          <div data-domain-action-criteria>
            <DataTable labelledBy={CRITERIA_HEADING_ID}>
              <thead>
                <tr>
                  {presentation.columns.map((column) => (
                    <th key={column} scope="col">
                      {column}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {intent.criteria.map((criterion) => {
                  const result = detail.results?.find((r) => r.key === criterion.key)?.result ?? null;
                  return (
                    <tr key={criterion.key} data-domain-action-criterion={criterion.key}>
                      <td>{criterion.label}</td>
                      <td>{criterion.required_evidence}</td>
                      <td data-domain-action-result={result ?? ""}>{result === null ? "" : presentation.resultLabels[result]}</td>
                    </tr>
                  );
                })}
              </tbody>
            </DataTable>
          </div>
        )}
      </Panel>
      {presentation.related ? (
        <Panel heading={COLD_RELATED_TITLE} headingId={RELATED_HEADING_ID}>
          <div className="domain-action-related" data-domain-action-related={related.kind}>
            <p className="prose" data-domain-action-related-sentence>
              {related.text}
            </p>
            <p className="domain-action-related__controls">
              {inspectHref === null ? (
                <>
                  <button
                    type="button"
                    className="button"
                    disabled
                    aria-describedby={INSPECT_NOTE_ID}
                    data-domain-action-inspect="unavailable"
                  >
                    {COLD_INSPECT}
                  </button>{" "}
                  <span className="muted" id={INSPECT_NOTE_ID} data-domain-action-inspect-note>
                    {COLD_INSPECT_UNAVAILABLE}
                  </span>
                </>
              ) : (
                <button
                  type="button"
                  className="button"
                  onClick={() => navigate(inspectHref)}
                  data-domain-action-inspect="live"
                  data-domain-action-inspect-target={inspectHref}
                >
                  {COLD_INSPECT}
                </button>
              )}{" "}
              {/* MOCK DEVIATION (D1) R66: the mock's `Open source Finding →` link is muted noninteractive text until an
                  exact-revision cold Finding destination exists (ruling 8). */}
              <span className="muted" data-domain-action-finding-control>
                {COLD_SOURCE_FINDING}
              </span>{" "}
              <span className="muted" data-domain-action-finding-note>
                {COLD_SOURCE_FINDING_UNAVAILABLE}
              </span>
            </p>
          </div>
        </Panel>
      ) : null}
    </>
  );
}
